"""Decoded-content checks independent of filerepack's implementation.

Checks match declared corpus profiles. They are deliberately stronger than file-open
or magic-byte checks; they do not claim full application/render equivalence.
"""
import bz2
import gzip
import hashlib
import io
import json
import lzma
import shutil
import sqlite3
import struct
import subprocess
import tempfile
import zipfile
import zlib
from pathlib import Path
from xml.dom import minidom


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(argv, **kwargs):
    alternatives = {'magick': 'convert', '7zz': '7z'}
    if argv[0] in alternatives and not shutil.which(argv[0]):
        argv = [alternatives[argv[0]], *argv[1:]]
    return subprocess.run(argv, check=True, capture_output=True, timeout=90, **kwargs).stdout


def json_tokens(data):
    """Ignore only whitespace outside strings, preserving duplicate keys and numeric spelling."""
    text = data.decode('utf-8')
    json.loads(text, parse_int=str, parse_float=str,
               parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    result = []
    quoted = escaped = False
    for char in text:
        if quoted or char not in ' \t\r\n':
            result.append(char)
        if escaped:
            escaped = False
        elif quoted and char == '\\':
            escaped = True
        elif char == '"':
            quoted = not quoted
    return ''.join(result)


def xml_tree(data):
    """Keep text, comments, processing instructions, namespaces and doctype; sort attributes."""
    dom = minidom.parseString(data)

    def node(n):
        attrs = sorted((a.name, a.value) for a in n.attributes.values()) if n.attributes else []
        return (n.nodeType, n.nodeName, n.nodeValue, attrs,
                getattr(n, 'publicId', None), getattr(n, 'systemId', None),
                [node(c) for c in n.childNodes])
    return node(dom)


def decode_stream(data, codec):
    if codec == 'gz':
        return gzip.decompress(data)
    if codec == 'bz2':
        return bz2.decompress(data)
    if codec in ('xz', 'lzma'):
        return lzma.decompress(data, format=lzma.FORMAT_AUTO)
    if codec == 'zst':
        import zstandard
        with zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data)) as stream:
            return stream.read()
    if codec == 'br':
        import brotli
        return brotli.decompress(data)
    if codec == 'lz4':
        import lz4.frame
        return lz4.frame.decompress(data)
    exe = {'lz': 'lzip', 'lzo': 'lzop', 'z': 'gzip'}[codec]
    return command([exe, '-d', '-c'], input=data)


def array_bits(array):
    import numpy as np
    array = np.asarray(array)
    if array.dtype.kind in 'OUS':
        values = array.tolist()
    else:
        # Normalize endian only, retaining floating NaN payloads and signed zero.
        values = digest(array.astype(array.dtype.newbyteorder('<')).tobytes())
    return (str(array.dtype.newbyteorder('<')), array.shape, values)


def arrow_array_state(array):
    import pyarrow as pa
    if isinstance(array, pa.ChunkedArray):
        array = array.combine_chunks()
    valid = array.is_valid().to_pylist()
    if pa.types.is_dictionary(array.type):
        return arrow_array_state(array.dictionary_decode())
    if pa.types.is_floating(array.type):
        values = array.to_numpy(zero_copy_only=False)
        return str(array.type), valid, array_bits(values[valid])
    if pa.types.is_struct(array.type):
        values = [arrow_array_state(array.field(i).filter(pa.array(valid)))
                  for i in range(array.type.num_fields)]
    elif (pa.types.is_list(array.type) or pa.types.is_large_list(array.type) or
          pa.types.is_fixed_size_list(array.type) or pa.types.is_map(array.type)):
        values = [arrow_array_state(value.values) if value.is_valid else None for value in array]
    else:
        values = array.to_pylist()
    return str(array.type), valid, values


def sqlite_state(path):
    uri = Path(path).resolve().as_uri() + '?mode=ro&immutable=1'
    with sqlite3.connect(uri, uri=True) as db:
        schema = db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master "
                            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
        tables = {}
        for kind, name, _, sql in schema:
            if kind == 'table':
                quoted = '"' + name.replace('"', '""') + '"'
                prefix = '' if 'WITHOUT ROWID' in sql.upper() else 'rowid,'
                rows = db.execute('SELECT ' + prefix + '* FROM ' + quoted).fetchall()
                tables[name] = sorted(rows, key=repr)
        return (schema, tables, db.execute('PRAGMA application_id').fetchone(),
                db.execute('PRAGMA user_version').fetchone())


def raster_state(path, config=None):
    from .semantic import image_metadata
    from PIL import Image
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    with Image.open(path) as image:
        frames = []
        # Palette indices and disposal/blend instructions describe storage/compositing.
        # Compare the background color and rendered frames, rather than the index or
        # instructions used to produce the same frames. Strict instruction identity
        # is an explicit optional profile constraint.
        palette = image.getpalette()
        background = image.info.get('background')
        background_color = (tuple(palette[background * 3:background * 3 + 3])
                            if palette and isinstance(background, int) else None)
        controls = (config or {}).get('preserve_frame_controls', False)
        for i in range(getattr(image, 'n_frames', 1)):
            image.seek(i)
            high_depth = ((image.mode, digest(image.tobytes()))
                          if image.mode in ('I', 'F') or image.mode.startswith('I;16') else None)
            frames.append((image.size, digest(image.convert('RGBA').tobytes()), high_depth,
                           image.info.get('duration'),
                           getattr(image, 'disposal_method', image.info.get('disposal')) if controls else None,
                           image.info.get('blend') if controls else None,
                           image_metadata(image, background_color)))
        exact = None
        if (config or {}).get('exact_png_bits'):
            import imagecodecs
            exact = array_bits(imagecodecs.png_decode(Path(path).read_bytes()))
        return (frames, image.info.get('loop'), exact)


def media_state(path, video=False):
    from .semantic import media_metadata
    info = json.loads(command(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                              '-of', 'json', str(path)]))
    streams = []
    for stream in info['streams']:
        kind = stream['codec_type']
        index = str(stream['index'])
        if kind == 'video':
            pixel_format = ('rgba64le' if any(bit in stream.get('pix_fmt', '')
                                           for bit in ('10', '12', '14', '16', 'f32')) else 'rgba')
            raw = command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:' + index,
                           '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', pixel_format, '-'])
            # Keep frame count/order plus stream timing. Container time bases can change.
            streams.append((kind, stream['width'], stream['height'],
                            stream.get('avg_frame_rate'), digest(raw)))
        elif kind == 'audio':
            raw = command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:' + index,
                           '-f', 's32le', '-acodec', 'pcm_s32le', '-'])
            streams.append((kind, stream['sample_rate'], stream['channels'], digest(raw)))
        else:
            streams.append((kind, stream.get('codec_name'), stream.get('tags')))
    return streams, media_metadata(info, command, path)


def archive_state(path, config):
    from .semantic import check_usdz, zip_metadata
    children = config.get('children', {})
    entries = []
    if config['kind'] == 'zip':
        with zipfile.ZipFile(path) as archive:
            if config.get('package') == 'usdz':
                check_usdz(Path(path), archive.infolist())
            if archive.testzip() is not None:
                raise ValueError('Bad ZIP CRC')
            for info in archive.infolist():
                data = archive.read(info)
                verifier = children.get(info.filename, {'kind': 'bytes'})
                value = bytes_state(data, verifier, info.filename)
                entries.append((info.filename, info.is_dir(), value, zip_metadata(info, config)))
            for name in config.get('stored_first', []):
                info = archive.getinfo(name)
                if archive.infolist()[0].filename != name or info.compress_type != 0:
                    raise ValueError(name + ' must be first and STORED')
        preserve_order = (config.get('preserve_order') or config.get('package') == 'usdz' or
                          len({entry[0] for entry in entries}) != len(entries))
        return (entries if preserve_order else sorted(entries, key=repr), archive.comment)
    import tarfile
    if config.get('codec'):
        source = io.BytesIO(decode_stream(Path(path).read_bytes(), config['codec']))
        archive = tarfile.open(fileobj=source)
    else:
        archive = tarfile.open(path)
    with archive:
        for info in archive:
            stream = archive.extractfile(info) if info.isfile() else None
            value = bytes_state(stream.read(), children.get(info.name, {'kind': 'bytes'}),
                                info.name) if stream else None
            entries.append((info.name, info.type, info.linkname, info.mode, info.uid, info.gid,
                            info.uname, info.gname, info.mtime, info.pax_headers, value))
    return sorted(entries, key=repr)


def npz_state(path):
    """Load a trusted numeric NPZ fixture with NumPy, never enabling pickle."""
    import numpy as np

    arrays = np.load(path, allow_pickle=False)
    if not isinstance(arrays, np.lib.npyio.NpzFile):
        raise ValueError('Expected a NumPy NPZ archive')
    try:
        return [(name, array_bits(arrays[name])) for name in arrays.files]
    finally:
        arrays.close()


def cpio_state(data):
    """Check newc records and compare names, metadata and typed member contents."""
    offset = 0
    records = []
    while offset + 110 <= len(data):
        header = data[offset:offset + 110]
        magic = header[:6]
        if magic not in (b'070701', b'070702'):
            raise ValueError('Invalid newc CPIO magic')
        try:
            fields = [int(header[6 + i * 8:14 + i * 8], 16) for i in range(13)]
        except ValueError as exc:
            raise ValueError('Invalid newc CPIO header field') from exc
        file_size, name_size, checksum = fields[6], fields[11], fields[12]
        if name_size < 1:
            raise ValueError('Empty newc CPIO filename')
        name_start = offset + 110
        name_end = name_start + name_size
        if name_end > len(data):
            raise ValueError('Truncated newc CPIO filename')
        name = data[name_start:name_end]
        if not name.endswith(b'\0'):
            raise ValueError('Unterminated newc CPIO filename')
        try:
            decoded_name = name[:-1].decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError('Invalid newc CPIO filename encoding') from exc
        data_start = (name_end + 3) & ~3
        data_end = data_start + file_size
        if data_end > len(data):
            raise ValueError('Truncated newc CPIO member data')
        payload = data[data_start:data_end]
        if magic == b'070702' and sum(payload) & 0xffffffff != checksum:
            raise ValueError('newc CPIO checksum mismatch')
        offset = (data_end + 3) & ~3
        if decoded_name == 'TRAILER!!!':
            if file_size or any(data[offset:]):
                raise ValueError('Invalid newc CPIO trailer or non-padding suffix')
            if not records:
                raise ValueError('Empty newc CPIO archive')
            trailer_identity = tuple(value for i, value in enumerate(fields) if i not in (6, 12))
            return (records, trailer_identity)
        if not decoded_name or decoded_name.startswith('/') or '..' in decoded_name.split('/'):
            raise ValueError('Unsafe newc CPIO path in fixture')
        if decoded_name.endswith('.json'):
            content = json_tokens(payload)
        elif decoded_name.endswith('.xml'):
            content = xml_tree(payload)
        else:
            content = digest(payload)
        metadata = tuple(value for i, value in enumerate(fields) if i not in (6, 12))
        records.append((decoded_name, metadata, content))
    raise ValueError('Missing or truncated newc CPIO trailer')


def _read_varint(data, offset):
    value = shift = 0
    while offset < len(data) and shift <= 63:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
    raise ValueError('Invalid CRX protobuf varint')


def _protobuf_fields(data):
    fields = []
    offset = 0
    while offset < len(data):
        key, offset = _read_varint(data, offset)
        number, wire = key >> 3, key & 7
        if number == 0:
            raise ValueError('Invalid CRX protobuf field number')
        if wire == 0:
            value, offset = _read_varint(data, offset)
        elif wire == 2:
            length, offset = _read_varint(data, offset)
            end = offset + length
            if end > len(data):
                raise ValueError('Truncated CRX protobuf field')
            value, offset = data[offset:end], end
        elif wire == 1:
            end = offset + 8
            if end > len(data):
                raise ValueError('Truncated CRX protobuf fixed64 field')
            value, offset = data[offset:end], end
        elif wire == 5:
            end = offset + 4
            if end > len(data):
                raise ValueError('Truncated CRX protobuf fixed32 field')
            value, offset = data[offset:end], end
        else:
            raise ValueError('Unsupported CRX protobuf wire type')
        fields.append((number, wire, value))
    return fields


def _crx3_parts(data):
    if len(data) < 12 or data[:4] != b'Cr24':
        raise ValueError('Missing CRX magic')
    version, header_length = struct.unpack_from('<II', data, 4)
    if version != 3 or not header_length or 12 + header_length >= len(data):
        raise ValueError('Invalid CRX3 header')
    header = _protobuf_fields(data[12:12 + header_length])
    zip_payload = data[12 + header_length:]
    signed_values = [value for number, wire, value in header if number == 10000 and wire == 2]
    proofs = [value for number, wire, value in header if number == 2 and wire == 2]
    if len(signed_values) != 1 or len(proofs) != 1:
        raise ValueError('CRX3 must have exactly one signed header and RSA proof')
    signed_header_data = signed_values[0]
    proof = _protobuf_fields(proofs[0])
    public_values = [value for number, wire, value in proof if number == 1 and wire == 2]
    signature_values = [value for number, wire, value in proof if number == 2 and wire == 2]
    if len(public_values) != 1 or len(signature_values) != 1:
        raise ValueError('Malformed CRX3 RSA proof')
    ids = [value for number, wire, value in _protobuf_fields(signed_header_data)
           if number == 1 and wire == 2]
    public_key = public_values[0]
    if len(ids) != 1 or ids[0] != hashlib.sha256(public_key).digest()[:16]:
        raise ValueError('CRX3 signed extension ID does not match its public key')
    signing_input = (b'CRX3 SignedData\0' + struct.pack('<I', len(signed_header_data))
                     + signed_header_data + zip_payload)
    return public_key, signature_values[0], signing_input, zip_payload


def crx_state(path, config):
    public_key, signature, signing_input, zip_payload = _crx3_parts(Path(path).read_bytes())
    with tempfile.TemporaryDirectory(prefix='frbench-crx-verify-') as temp:
        temp = Path(temp)
        public_der = temp / 'public.der'
        public_pem = temp / 'public.pem'
        signature_path = temp / 'signature.bin'
        signed_path = temp / 'signed.bin'
        zip_path = temp / 'payload.zip'
        public_der.write_bytes(public_key)
        signature_path.write_bytes(signature)
        signed_path.write_bytes(signing_input)
        zip_path.write_bytes(zip_payload)
        command(['openssl', 'pkey', '-pubin', '-inform', 'DER', '-in', str(public_der),
                 '-out', str(public_pem)])
        command(['openssl', 'dgst', '-sha256', '-verify', str(public_pem), '-signature',
                 str(signature_path), '-sigopt', 'rsa_padding_mode:pkcs1', str(signed_path)])
        contents = archive_state(zip_path, {'kind': 'zip',
                                           'children': config.get('children', {})})
    return (hashlib.sha256(public_key).hexdigest(), digest(zip_payload), contents)


def car_state(path):
    """Read the corpus's BOMStore/one-rendition profile without filerepack code."""
    data = Path(path).read_bytes()
    if len(data) < 512 or data[:8] != b'BOMStore' or any(data[32:512]):
        raise ValueError('Invalid corpus CAR BOMStore header')
    version, block_count, index_offset, index_size, vars_offset, vars_size = struct.unpack_from(
        '>6I', data, 8)
    if version != 1:
        raise ValueError('Unsupported corpus CAR BOMStore version')
    if (index_offset < 512 or index_offset + index_size > len(data)
            or vars_offset < 512 or vars_offset + vars_size > len(data)):
        raise ValueError('CAR index or variable table is outside the file')
    table = data[index_offset:index_offset + index_size]
    if len(table) < 8:
        raise ValueError('Truncated CAR block index')
    capacity = struct.unpack_from('>I', table)[0]
    if 4 + capacity * 8 + 4 > len(table):
        raise ValueError('Truncated CAR block pointers')
    pointers = [struct.unpack_from('>2I', table, 4 + i * 8) for i in range(capacity)]
    free_count = struct.unpack_from('>I', table, 4 + capacity * 8)[0]
    if free_count:
        raise ValueError('This generated CAR profile has no free pointer table')
    if any(table[8 + capacity * 8:]):
        raise ValueError('Unexpected CAR block-index suffix')
    blocks = {}
    occupied = [(0, 512), (index_offset, index_offset + index_size),
                (vars_offset, vars_offset + vars_size)]
    for block_id, (address, size) in enumerate(pointers):
        if not address and not size:
            continue
        if block_id == 0 or not address or not size or address + size > len(data):
            raise ValueError('Invalid CAR block pointer')
        blocks[block_id] = data[address:address + size]
        occupied.append((address, address + size))
    if len(blocks) != block_count:
        raise ValueError('CAR allocated-block count differs from its index')
    end = 0
    for start, stop in sorted(occupied):
        if start < end or any(data[end:start]):
            raise ValueError('CAR blocks overlap or contain unclassified bytes')
        end = stop
    if any(data[end:]):
        raise ValueError('Unexpected CAR trailing bytes')

    variable_data = data[vars_offset:vars_offset + vars_size]
    if len(variable_data) < 4:
        raise ValueError('Truncated CAR variable table')
    variable_count = struct.unpack_from('>I', variable_data)[0]
    variables, offset = {}, 4
    for _ in range(variable_count):
        if offset + 5 > len(variable_data):
            raise ValueError('Truncated CAR variable')
        block_id, size = struct.unpack_from('>IB', variable_data, offset)
        end = offset + 5 + size
        name = variable_data[offset + 5:end]
        if not name or end > len(variable_data) or name in variables or block_id not in blocks:
            raise ValueError('Invalid CAR named variable')
        variables[name] = block_id
        offset = end
    if offset != len(variable_data) or not {b'CARHEADER', b'RENDITIONS', b'KEYFORMAT'} <= variables.keys():
        raise ValueError('Invalid CAR catalog variables')

    renditions_tree = blocks[variables[b'RENDITIONS']]
    if len(renditions_tree) != 21 or renditions_tree[:4] != b'tree':
        raise ValueError('Unsupported CAR rendition-tree profile')
    tree_version, root_id, page_size, entry_count = struct.unpack_from('>4I', renditions_tree, 4)
    if tree_version != 1 or page_size < 12 or root_id not in blocks:
        raise ValueError('Invalid CAR rendition-tree header')
    page = blocks[root_id]
    if len(page) < page_size:
        raise ValueError('Truncated CAR rendition-tree page')
    leaf, count, forward, backward = struct.unpack_from('>HHII', page)
    if leaf != 1 or count != entry_count or forward or backward or 12 + count * 8 > len(page):
        raise ValueError('Invalid CAR rendition-tree leaf')
    rendition_entries = [struct.unpack_from('>2I', page, 12 + i * 8) for i in range(count)]
    rendition_ids = set()
    for value_id, key_id in rendition_entries:
        if value_id not in blocks or key_id not in blocks:
            raise ValueError('CAR rendition tree references a missing block')
        key = blocks[key_id]
        rendition = blocks[value_id]
        if len(key) != 2 or len(rendition) < 184 or rendition[:4] != b'ISTC':
            raise ValueError('Invalid generated CAR rendition/key')
        tlv_size = struct.unpack_from('>I', rendition, 168)[0]
        body_size = struct.unpack_from('>I', rendition, 180)[0]
        body_start = 184 + tlv_size
        if body_start + body_size != len(rendition):
            raise ValueError('CAR rendition sizes do not match')
        body = rendition[body_start:]
        if body[:4] in (b'MLEC', b'CELM') and len(body) >= 16:
            body_version, codec, compressed_size = struct.unpack_from('<3I', body, 4)
            if body_version != 0 or codec != 2 or compressed_size != len(body) - 16:
                raise ValueError('Unsupported generated CAR rendition compression')
            raw = zlib.decompress(body[16:])
            normalized = (rendition[:180], rendition[184:body_start], body[:12], raw)
        else:
            normalized = (digest(rendition),)
        rendition_ids.add(value_id)
        blocks[value_id] = ('rendition', normalized)
    if len(rendition_ids) != entry_count:
        raise ValueError('Duplicate CAR rendition block')
    if len(rendition_ids) != 1:
        raise ValueError('Generated CAR profile expects one rendition')
    return (data[:16], data[32:512], variable_data,
            [(block_id, blocks[block_id]) for block_id in sorted(blocks)])


def bytes_state(data, config, name='blob'):
    kind = config['kind']
    if kind == 'bytes':
        return digest(data)
    if kind == 'json':
        return json_tokens(data)
    if kind == 'jsonl':
        # splitlines(keepends=True) retains CRLF versus LF and final newline.
        return [(json_tokens(line.rstrip(b'\r\n')),
                 line[len(line.rstrip(b'\r\n')):]) for line in data.splitlines(keepends=True)]
    if kind == 'xml':
        return xml_tree(data)
    if kind == 'stream':
        return digest(decode_stream(data, config['codec']))
    if kind == 'swf':
        import zlib
        if data[:3] not in (b'CWS', b'FWS'):
            raise ValueError('Unsupported SWF')
        raw = zlib.decompress(data[8:]) if data[:3] == b'CWS' else data[8:]
        if len(raw) + 8 != struct.unpack_from('<I', data, 4)[0]:
            raise ValueError('SWF length')
        return (data[3:8], digest(raw))
    if kind == 'tgs':
        return json_tokens(gzip.decompress(data))
    if kind == 'nrrd':
        header, raw = data.split(b'\n\n', 1)
        lines = header.splitlines()
        encoding = next(line.split(b':', 1)[1].strip() for line in lines
                        if line.startswith(b'encoding:'))
        if encoding in (b'gzip', b'gz'):
            raw = gzip.decompress(raw)
        elif encoding in (b'bzip2', b'bz2'):
            raw = bz2.decompress(raw)
        return ([line for line in lines if not line.startswith(b'encoding:')], digest(raw))
    if kind == 'blend':
        if data[:2] == b'\x1f\x8b':
            data = gzip.decompress(data)
        elif data[:4] == b'\x28\xb5\x2f\xfd':
            data = decode_stream(data, 'zst')
        if not data.startswith(b'BLENDER'):
            raise ValueError('Blender header')
        return digest(data)
    if kind == 'psb':
        # Generated composite-only profile: exact header/resources, decoded channels.
        import zlib
        color_len = struct.unpack_from('>I', data, 26)[0]
        offset = 30 + color_len
        resources = struct.unpack_from('>I', data, offset)[0]
        offset += 4 + resources
        layer_len = struct.unpack_from('>Q', data, offset)[0]
        offset += 8 + layer_len
        codec = struct.unpack_from('>H', data, offset)[0]
        raw = data[offset + 2:]
        if codec == 2:
            raw = zlib.decompress(raw)
        elif codec != 0:
            raise ValueError('PSB oracle only handles raw/ZIP composite')
        return (data[:offset], digest(raw))
    if kind == 'aseprite':
        import zlib
        result = [data[:128]]
        header = bytearray(data[:128])
        header[:4] = b'\0' * 4
        result[0] = bytes(header)
        offset = 128
        while offset < len(data):
            length, magic, count, duration = struct.unpack_from('<IHHH', data, offset)
            if magic != 0xF1FA:
                raise ValueError('Aseprite frame magic')
            chunks = []
            start = offset + 16
            for _ in range(count):
                size, tag = struct.unpack_from('<IH', data, start)
                content = data[start + 6:start + size]
                if tag == 0x2005 and struct.unpack_from('<H', content, 7)[0] == 2:
                    content = content[:20] + zlib.decompress(content[20:])
                chunks.append((tag, content))
                start += size
            result.append((duration, chunks))
            offset += length
        return result
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / Path(name).name
        path.write_bytes(data)
        return fingerprint(path, config)


def fingerprint(path, config):
    path = Path(path)
    kind = config['kind']
    if kind == 'npz':
        return npz_state(path)
    if kind in ('tracev3', 'rtf', 'model'):
        from .new_formats import model_state, rtf_state, tracev3_state
        if kind == 'tracev3':
            return tracev3_state(path.read_bytes())
        if kind == 'rtf':
            return rtf_state(path.read_bytes(), lambda data: bytes_state(data, {'kind': 'raster'}))
        return model_state(path.read_bytes(), config['format'])
    if kind in ('zip', 'tar'):
        return archive_state(path, config)
    if kind == 'cpbz2':
        return cpio_state(bz2.decompress(path.read_bytes()))
    if kind == 'cpio':
        return cpio_state(path.read_bytes())
    if kind == 'crx':
        return crx_state(path, config)
    if kind == 'car':
        return car_state(path)
    if kind in ('bytes', 'json', 'jsonl', 'xml', 'stream', 'swf', 'tgs', 'blend',
                'nrrd', 'psb', 'aseprite'):
        return bytes_state(path.read_bytes(), config)
    if kind == 'warc':
        data = path.read_bytes()
        if data.startswith(b'\x1f\x8b'):
            data = gzip.decompress(data)
        return digest(data)
    if kind == 'nib':
        data = path.read_bytes()
        version, coder, count, obj_start, key_count, key_start, value_count, val_start, cls_count, cls_start = struct.unpack_from('<10I', data, 10)
        def read_integer(offset):
            value, shift = 0, 0
            while True:
                byte = data[offset]
                value |= (byte & 127) << shift
                offset += 1
                if byte & 128:
                    return value, offset
                shift += 7
        objects, offset = [], obj_start
        for _ in range(count):
            obj = []
            for _ in range(3):
                value, offset = read_integer(offset)
                obj.append(value)
            objects.append(obj)
        values, offset = [], val_start
        for _ in range(value_count):
            key, offset = read_integer(offset)
            tag, offset = data[offset], offset + 1
            if tag != 8:
                raise ValueError('NIB corpus oracle expects opaque data values')
            size, offset = read_integer(offset)
            values.append((key, tag, data[offset:offset + size]))
            offset += size
        return (version, coder, data[key_start:val_start], data[cls_start:],
                [(cls, values[start:start + length]) for cls, start, length in objects])
    if kind == 'duckdb':
        import duckdb
        with duckdb.connect(str(path), read_only=True) as db:
            tables = db.execute("SELECT table_schema,table_name FROM information_schema.tables "
                                "WHERE table_schema NOT IN ('information_schema','pg_catalog') "
                                "ORDER BY table_schema,table_name").fetchall()
            records = []
            for schema, table in tables:
                def quote(x):
                    return '"' + x.replace('"', '""') + '"'
                records.append((schema, table, db.execute('DESCRIBE ' + quote(schema) + '.' + quote(table)).fetchall(),
                                sorted(db.execute('SELECT * FROM ' + quote(schema) + '.' + quote(table)).fetchall(), key=repr)))
            return records
    if kind == 'dicom':
        import pydicom
        data = pydicom.dcmread(path)
        pixels = array_bits(data.pixel_array)
        def attrs(ds):
            return [(str(e.tag), e.VR, [attrs(x) for x in e.value] if e.VR == 'SQ' else repr(e.value))
                    for e in ds if e.tag not in (0x7FE00010, 0x7FE00001, 0x7FE00002)]
        return attrs(data), pixels
    if kind == 'svg-render':
        data = path.read_bytes()
        if data.startswith(b'\x1f\x8b'):
            data = gzip.decompress(data)
        with tempfile.TemporaryDirectory() as temp:
            svg = Path(temp) / 'input.svg'
            svg.write_bytes(data)
            return command(['magick', str(svg), '-depth', '16', 'rgba:-'])
    if kind == 'sqlite':
        return sqlite_state(path)
    if kind == 'raster':
        return raster_state(path, config)
    if kind in ('audio', 'video'):
        return media_state(path, kind == 'video')
    if kind == 'arrow':
        import pyarrow as pa
        import pyarrow.feather as feather
        import pyarrow.orc as orc
        import pyarrow.parquet as pq
        form = config['format']
        if form == 'parquet':
            table = pq.read_table(path)
        elif form == 'orc':
            table = orc.read_table(path)
        elif form == 'feather':
            table = feather.read_table(path)
        else:
            with pa.memory_map(str(path)) as source:
                try:
                    reader = pa.ipc.open_file(source)
                except pa.ArrowInvalid:
                    source.seek(0)
                    reader = pa.ipc.open_stream(source)
                table = reader.read_all()
        return (str(table.schema), table.schema.metadata,
                tuple((f.name, f.metadata) for f in table.schema),
                tuple(arrow_array_state(column) for column in table.columns))
    if kind == 'avro':
        import fastavro
        with path.open('rb') as stream:
            reader = fastavro.reader(stream)
            return reader.writer_schema, list(reader)
    if kind == 'ole':
        import olefile
        with olefile.OleFileIO(path) as ole:
            streams = {tuple(name): digest(ole.openstream(name).read()) for name in ole.listdir()}
            directory = sorted((e.name, e.entry_type, e.clsid, e.dwUserFlags,
                                e.createTime, e.modifyTime)
                               for e in ole.direntries if e and e.entry_type != 0)
            return streams, directory
    if kind == 'hdf5':
        from .semantic import hdf5_state
        return hdf5_state(path, array_bits)
    if kind == 'netcdf':
        from .semantic import netcdf_state
        return netcdf_state(path, array_bits)
    if kind == 'tiff':
        import tifffile
        with tifffile.TiffFile(path) as file:
            return [(array_bits(p.asarray()), [(t.name, repr(t.value)) for t in p.tags.values()
                     if t.name not in {'Compression', 'StripOffsets', 'StripByteCounts',
                                       'TileOffsets', 'TileByteCounts', 'RowsPerStrip',
                                       'Predictor', 'Software'}]) for p in file.pages]
    if kind == 'fits':
        from astropy.io import fits
        with fits.open(path, do_not_scale_image_data=True, uint=False) as hdus:
            result = []
            for hdu in hdus:
                if hdu.data is None:
                    continue  # empty primary added by tiled compression
                attrs = [(c.keyword, c.value, c.comment) for c in hdu.header.cards
                         if c.keyword not in {'SIMPLE', 'XTENSION', 'BITPIX', 'PCOUNT', 'GCOUNT',
                                              'CHECKSUM', 'DATASUM', 'EXTEND'}
                         and not c.keyword.startswith(('NAXIS', 'Z'))]
                result.append((attrs, array_bits(hdu.data)))
            return result
    if kind == 'mat':
        import scipy.io
        return {k: array_bits(v) for k, v in scipy.io.loadmat(path).items()
                if not k.startswith('__')}
    if kind == 'spss':
        import pyreadstat
        data, meta = pyreadstat.read_sav(path, output_format='dict', user_missing=True)
        return (data, meta.column_names, meta.column_labels, meta.variable_value_labels,
                meta.missing_ranges, meta.file_label)
    if kind == 'font':
        from fontTools.ttLib import TTFont
        with TTFont(path, recalcTimestamp=False) as font:
            font.flavor = None
            # XML is independent of compressed font-table envelope/checksums.
            output = io.BytesIO()
            font.saveXML(output, tables=[tag for tag in font.keys() if tag != 'GlyphOrder'])
            xml = minidom.parseString(output.getvalue())
            for node in list(xml.getElementsByTagName('checkSumAdjustment')):
                node.parentNode.removeChild(node)
            return xml_tree(xml.toxml().encode())
    if kind == 'checkpoint':
        # Passive ZIP comparison, never unpickle corpus checkpoint objects.
        with zipfile.ZipFile(path) as file:
            return [(i.filename, digest(file.read(i))) for i in file.infolist()]
    if kind == 'r':
        codec = path.read_bytes()[:6]
        data = path.read_bytes()
        if codec[:2] == b'\x1f\x8b':
            data = gzip.decompress(data)
        elif codec[:3] == b'BZh':
            data = bz2.decompress(data)
        elif codec == b'\xfd7zXZ\0':
            data = lzma.decompress(data)
        return digest(data)  # serialized graph and every XDR record remain byte-identical
    if kind == 'zarr':
        import zarr
        root = zarr.open_group(str(path), mode='r')
        result = [('/', dict(root.attrs))]
        def visit(name, obj):
            result.append((name, dict(obj.attrs), array_bits(obj[:]) if isinstance(obj, zarr.Array)
                           else None))
        root.visititems(visit)
        return result
    if kind == 'pdf':
        # Compare rendering, page geometry, metadata and attachments for shape-only pages.
        import pikepdf
        from pypdf import PdfReader
        from .semantic import pdf_semantics
        with pikepdf.open(path) as pdf:
            meta = sorted((str(k), str(v)) for k, v in pdf.docinfo.items())
            boxes = [(str(p.obj.get('/MediaBox')), str(p.obj.get('/CropBox')),
                      str(p.obj.get('/Rotate'))) for p in pdf.pages]
            attachments = sorted((k, digest(v.get_file().read_bytes()))
                                 for k, v in pdf.attachments.items())
            semantic = pdf_semantics(pdf)
        text = tuple(page.extract_text() for page in PdfReader(path).pages)
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / 'page'
            command(['gs', '-q', '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=png16m',
                     '-r72', '-sOutputFile=' + str(prefix) + '-%03d.png', str(path)])
            pages = [raster_state(p) for p in sorted(Path(temp).glob('page-*.png'))]
        return boxes, meta, attachments, text, pages, semantic
    if kind in ('7z', 'rar'):
        # List/test/extract trusted repository fixtures into a disposable directory.
        # No externally supplied archives are accepted by this verifier.
        with tempfile.TemporaryDirectory() as temp:
            if kind == 'rar':
                command(['unrar', 't', '-idq', str(path)])
                command(['unrar', 'x', '-idq', '-o+', str(path), temp + '/'])
            else:
                command(['7zz', 't', str(path)])
                command(['7zz', 'x', '-y', '-o' + temp, str(path)])
            return {str(p.relative_to(temp)): bytes_state(p.read_bytes(),
                    config.get('children', {}).get(str(p.relative_to(temp)), {'kind': 'bytes'}),
                    p.name) for p in sorted(Path(temp).rglob('*')) if p.is_file()}
    if kind == 'imagemagick':
        return command(['magick', str(path), '-depth', '16', 'rgba:-'])
    raise ValueError('Unknown oracle: ' + kind)


def require(config):
    """Return missing oracle dependencies without importing filerepack."""
    import importlib.util
    import shutil
    modules = {
        'raster': ['PIL'], 'arrow': ['pyarrow'], 'avro': ['fastavro'], 'ole': ['olefile'],
        'hdf5': ['h5py', 'numpy'], 'netcdf': ['netCDF4', 'numpy'],
        'tiff': ['tifffile', 'numpy'], 'fits': ['astropy', 'numpy'], 'mat': ['scipy', 'numpy'],
        'duckdb': ['duckdb'], 'dicom': ['pydicom', 'numpy'], 'spss': ['pyreadstat'], 'font': ['fontTools'], 'zarr': ['zarr', 'numpy'],
        'npz': ['numpy'],
        'pdf': ['pikepdf', 'pypdf', 'PIL'], 'tracev3': ['lz4'], 'rtf': ['PIL'],
    }.get(config['kind'], [])
    if config['kind'] == 'model' and config.get('format') == 'onnx':
        modules.append('onnx')
    if config.get('exact_png_bits'):
        modules += ['imagecodecs', 'numpy']
    commands = {'audio': ['ffmpeg', 'ffprobe'], 'video': ['ffmpeg', 'ffprobe'],
                'pdf': ['gs'], '7z': ['7zz'], 'rar': ['unrar'],
                'imagemagick': ['magick'], 'svg-render': ['magick'],
                'crx': ['openssl']}.get(config['kind'], [])
    codec = config.get('codec')
    if codec in ('br', 'zst', 'lz4'):
        modules += [{'br': 'brotli', 'zst': 'zstandard', 'lz4': 'lz4'}[codec]]
    if codec in ('lz', 'lzo', 'z'):
        commands += [{'lz': 'lzip', 'lzo': 'lzop', 'z': 'gzip'}[codec]]
    missing = [m for m in modules if not importlib.util.find_spec(m)]
    alternatives = {'magick': 'convert', '7zz': '7z'}
    missing += [c for c in commands if not shutil.which(c) and
                not shutil.which(alternatives.get(c, c))]
    for child in config.get('children', {}).values():
        missing.extend(require(child))
    return sorted(set(missing))
