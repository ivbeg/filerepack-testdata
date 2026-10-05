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
import sqlite3
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.dom import minidom


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(argv, **kwargs):
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


def raster_state(path):
    from PIL import Image
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    with Image.open(path) as image:
        frames = []
        for i in range(getattr(image, 'n_frames', 1)):
            image.seek(i)
            frames.append((image.size, digest(image.convert('RGBA').tobytes()),
                           image.info.get('duration'), image.info.get('disposal'),
                           image.info.get('blend')))
        return (frames, image.info.get('loop'))


def media_state(path, video=False):
    info = json.loads(command(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                              '-of', 'json', str(path)]))
    streams = []
    for stream in info['streams']:
        kind = stream['codec_type']
        index = str(stream['index'])
        if kind == 'video' and not stream.get('disposition', {}).get('attached_pic'):
            raw = command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:' + index,
                           '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'])
            # Keep frame count/order plus stream timing. Container time bases can change.
            streams.append((kind, stream['width'], stream['height'],
                            stream.get('avg_frame_rate'), digest(raw)))
        elif kind == 'audio':
            raw = command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:' + index,
                           '-f', 's32le', '-acodec', 'pcm_s32le', '-'])
            streams.append((kind, stream['sample_rate'], stream['channels'], digest(raw)))
        else:
            streams.append((kind, stream.get('codec_name'), stream.get('tags')))
    return streams


def archive_state(path, config):
    children = config.get('children', {})
    entries = []
    if config['kind'] == 'zip':
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError('Bad ZIP CRC')
            for info in archive.infolist():
                data = archive.read(info)
                verifier = children.get(info.filename, {'kind': 'bytes'})
                value = bytes_state(data, verifier, info.filename)
                entries.append((info.filename, info.is_dir(), value))
            for name in config.get('stored_first', []):
                info = archive.getinfo(name)
                if archive.infolist()[0].filename != name or info.compress_type != 0:
                    raise ValueError(name + ' must be first and STORED')
        return (sorted(entries, key=repr), archive.comment)
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
    if kind in ('zip', 'tar'):
        return archive_state(path, config)
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
        return raster_state(path)
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
                tuple((f.name, f.metadata) for f in table.schema), table.to_pydict())
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
        import h5py
        objects = []
        with h5py.File(path, 'r') as file:
            def visit(name, obj):
                attrs = sorted((k, repr(v)) for k, v in obj.attrs.items())
                objects.append((name, attrs, array_bits(obj[()]) if isinstance(obj, h5py.Dataset)
                                else None))
            visit('/', file)
            file.visititems(visit)
        return objects
    if kind == 'netcdf':
        import netCDF4
        with netCDF4.Dataset(path) as file:
            file.set_auto_maskandscale(False)
            return ([(k, repr(file.getncattr(k))) for k in sorted(file.ncattrs())],
                    [(k, len(d), d.isunlimited()) for k, d in file.dimensions.items()],
                    [(k, v.dimensions, [(a, repr(v.getncattr(a))) for a in sorted(v.ncattrs())],
                      array_bits(v[:])) for k, v in file.variables.items()])
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
        with pikepdf.open(path) as pdf:
            meta = sorted((str(k), str(v)) for k, v in pdf.docinfo.items())
            boxes = [(str(p.obj.get('/MediaBox')), str(p.obj.get('/CropBox')),
                      str(p.obj.get('/Rotate'))) for p in pdf.pages]
            attachments = sorted((k, digest(v.get_file().read_bytes()))
                                 for k, v in pdf.attachments.items())
        text = b''  # This corpus contains shape-only pages; no text-equivalence claim.
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / 'page'
            command(['gs', '-q', '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=png16m',
                     '-r72', '-sOutputFile=' + str(prefix) + '-%03d.png', str(path)])
            pages = [raster_state(p) for p in sorted(Path(temp).glob('page-*.png'))]
        return boxes, meta, attachments, text, pages
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
        'pdf': ['pikepdf', 'PIL'],
    }.get(config['kind'], [])
    commands = {'audio': ['ffmpeg', 'ffprobe'], 'video': ['ffmpeg', 'ffprobe'],
                'pdf': ['gs'], '7z': ['7zz'], 'rar': ['unrar'],
                'imagemagick': ['magick'], 'svg-render': ['magick']}.get(config['kind'], [])
    codec = config.get('codec')
    if codec in ('br', 'zst', 'lz4'):
        modules += [{'br': 'brotli', 'zst': 'zstandard', 'lz4': 'lz4'}[codec]]
    if codec in ('lz', 'lzo', 'z'):
        commands += [{'lz': 'lzip', 'lzo': 'lzop', 'z': 'gzip'}[codec]]
    missing = [m for m in modules if not importlib.util.find_spec(m)]
    missing += [c for c in commands if not shutil.which(c)]
    for child in config.get('children', {}).values():
        missing.extend(require(child))
    return sorted(set(missing))
