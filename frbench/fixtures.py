"""Additional audit fixtures; generators use public formats and independent readers."""
import io
import json
import struct


def trace_chunk(tag, body, subtag=0):
    data = struct.pack('<IIQ', tag, subtag, len(body)) + body
    return data + bytes(-len(data) % 8)


def current_formats(builder):
    from .generate import compress
    supported = set(builder.catalog['supported_extensions'])
    # Inspection-only model inputs preserve every byte while exercising native readers.
    raw = struct.pack('<4I', 0, 0x80000000, 0x7FC01234, 0x3F800000)
    header = json.dumps({'__metadata__': {'source': 'synthetic'},
                         'weights': {'dtype': 'F32', 'shape': [4], 'data_offsets': [0, 16]}},
                        separators=(',', ':')).encode()
    header += b' ' * (-len(header) % 8)
    safetensors = struct.pack('<Q', len(header)) + header + raw
    def ggstring(value):
        data = value.encode()
        return struct.pack('<Q', len(data)) + data
    gguf = (b'GGUF' + struct.pack('<IQQ', 3, 1, 1) + ggstring('general.alignment') +
            struct.pack('<II', 4, 32) + ggstring('weights') + struct.pack('<IQIQ', 1, 4, 0, 0))
    gguf += bytes(-len(gguf) % 32) + raw
    for ext, data in [('safetensors', safetensors), ('gguf', gguf)]:
        builder.add('scientific/inspection.' + ext, data, ext, 'scientific',
                    {'kind': 'model', 'format': ext},
                    note='Bounded inspection-only profile; tensor payloads are never instantiated')
        builder.cases[-1]['qualification'] = {'statuses': ['unchanged'], 'routing': {'packer': ext}}
        builder.add('controls/truncated.' + ext, data[:12], ext, 'scientific', {'kind': 'bytes'},
                    tier='control', expectation='unchanged')
    def onnx_case():
        import onnx
        helper = onnx.helper
        graph = helper.make_graph([helper.make_node('Identity', ['X'], ['Y'])], 'synthetic',
                                  [helper.make_tensor_value_info('X', onnx.TensorProto.FLOAT, [4])],
                                  [helper.make_tensor_value_info('Y', onnx.TensorProto.FLOAT, [4])])
        model = helper.make_model(graph, producer_name='frbench',
                                  opset_imports=[helper.make_opsetid('', 13)], ir_version=8)
        builder.add('scientific/inspection.onnx', model.SerializeToString(), 'onnx',
                    'scientific', {'kind': 'model', 'format': 'onnx'})
        builder.cases[-1]['qualification'] = {'statuses': ['unchanged'], 'routing': {'packer': 'onnx'}}
        builder.add('controls/truncated.onnx', b'\x08\x08\x3a\xff', 'onnx', 'scientific',
                    {'kind': 'bytes'}, tier='control', expectation='unchanged')
    builder.optional('onnx', onnx_case)
    def trace_case():
        import lz4.block
        raw = b'Synthetic archived log record\0' * 1024
        encoded = lz4.block.compress(raw, store_size=False, dict=raw[-65536:])
        blocks = (b'bv4-' + struct.pack('<I', len(raw)) + raw + b'bv41' +
                  struct.pack('<II', len(raw), len(encoded)) + encoded + b'bv4$')
        prefix = trace_chunk(0x1000, bytes(208), 0x11) + trace_chunk(0x600b, b'synthetic catalog')
        data = prefix + trace_chunk(0x600d, blocks, 7) + trace_chunk(0x1111, b'opaque trailer')
        builder.add('native/archived.tracev3', data, 'tracev3', 'native', {'kind': 'tracev3'})
        builder.cases[-1]['qualification'] = {'routing': {'packer': 'tracev3'}}
        builder.add('controls/truncated.tracev3', prefix + trace_chunk(0x600d, b'bv41\xff'),
                    'tracev3', 'native', {'kind': 'bytes'}, tier='control', expectation='unchanged')
    builder.optional('tracev3', trace_case)
    builder.add('streams/weak.gzip', compress(builder.payload, 'gz'), 'gzip', 'streams',
                {'kind': 'stream', 'codec': 'gz'})
    tar = builder.directory / 'archives/container.tar.gz'
    if tar.is_file():
        builder.add('archives/container.tar.gzip', tar.read_bytes(), 'tar.gzip', 'archives',
                    {'kind': 'tar', 'codec': 'gz', 'children': builder.children})
        builder.cases[-1]['qualification'] = {'routing': {'family': 'tar.gz'}}
        builder.add('archives/detected-tar.gzip', tar.read_bytes(), 'gzip', 'archives',
                    {'kind': 'tar', 'codec': 'gz', 'children': builder.children})
        builder.cases[-1]['qualification'] = {'routing': {'family': 'tar.gz'}}
    warcs = sorted((builder.directory / 'native').glob('*.warc.gz'))
    if warcs:
        raw = warcs[0].read_bytes()
        for name, ext in [('native/alias.warc.gzip', 'warc'),
                          ('native/detected-warc.gz', 'gz'), ('native/detected-warc.gzip', 'gzip')]:
            builder.add(name, raw, ext, 'native', {'kind': 'warc'})
            builder.cases[-1]['qualification'] = {'routing': {'packer': 'warc'}}
    for ext in ('rds', 'rda', 'rdata'):
        path = builder.directory / ('scientific/arrays.' + ext)
        if path.is_file():
            builder.add('scientific/arrays.' + ext + '.gzip', compress(path.read_bytes(), 'gz'),
                        ext, 'scientific', {'kind': 'r'})
            builder.cases[-1]['qualification'] = {'routing': {'packer': 'r-serialization'}}
    def rtf_case():
        from PIL import Image, PngImagePlugin
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('Author', 'Synthetic fixture')
        stream = io.BytesIO()
        Image.new('RGBA', (64, 32), (12, 34, 56, 255)).save(stream, 'PNG',
                                                         compress_level=0, pnginfo=metadata)
        image = stream.getvalue()
        host = (br'{\rtf1\ansi\uc1{\fonttbl{\f0 Arial;}}'
                br'{\info{\title Synthetic document}{\author Frbench}}'
                br'\pard Keep  two spaces, \{braces\}, \\, \'e9 and \u1040?\par ')
        picture = br'{\pict\pngblip\picw64\pich32\picwgoal960\pichgoal480 '
        for name, payload in [('hex', image.hex().encode()),
                              ('binary', b'\\bin' + str(len(image)).encode() + b' ' + image)]:
            data = host + picture + payload + br'}\par End.}' + b'\r\n'
            builder.add('documents/picture-' + name + '.rtf', data, 'rtf', 'documents',
                        {'kind': 'rtf'})
            if 'rtf' in supported:
                builder.cases[-1]['qualification'] = {'routing': {'packer': 'rtf'},
                                                      'requires_extension': 'rtf'}
        builder.add('controls/truncated.rtf', host + picture + b'00', 'rtf', 'documents',
                    {'kind': 'bytes'}, tier='control', expectation='unchanged')
    builder.optional('rtf', rtf_case)


def depth_profiles(builder):
    import tempfile
    from pathlib import Path
    from .generate import command, zip_bytes
    def arrow_edges():
        import numpy as np
        import pyarrow as pa
        import pyarrow.parquet as pq
        values = np.array([0, 0x80000000, 0x7FC01234, 0x3F800000], dtype='<u4').view('<f4')
        field = pa.field('value', pa.float32(), metadata={b'unit': b'synthetic'})
        table = pa.Table.from_arrays([pa.array(values)], schema=pa.schema([field]))
        stream = io.BytesIO()
        pq.write_table(table, stream, compression='NONE')
        builder.add('scientific/float-edge.parquet', stream.getvalue(), 'parquet',
                    'scientific', {'kind': 'arrow', 'format': 'parquet'})
        stream = io.BytesIO()
        with pa.ipc.new_file(stream, table.schema) as writer:
            writer.write_table(table)
        builder.add('scientific/float-edge.arrow', stream.getvalue(), 'arrow',
                    'scientific', {'kind': 'arrow', 'format': 'ipc'})
    builder.optional('arrow numeric edges', arrow_edges)
    # Bounded archive controls never contain user paths or downloaded executables.
    for name, members in [('parent-path', {'../frbench-synthetic-escape.txt': b'synthetic'}),
                          ('signature-marker', {'_xmlsignatures/sig1.xml': b'<Signature/>',
                                                'document.xml': b'<document/>'})]:
        ext = 'docx' if name == 'signature-marker' else 'zip'
        builder.add('controls/archive-' + name + '.' + ext, zip_bytes(members), ext,
                    'archives', {'kind': 'bytes'}, scope='container-only',
                    tier='control', expectation='unchanged')
    buffer = io.BytesIO()
    import zipfile
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('same.txt', b'first')
        archive.writestr('same.txt', b'second')
    builder.add('controls/duplicate-members.zip', buffer.getvalue(), 'zip', 'archives',
                {'kind': 'bytes'}, tier='control', expectation='unchanged')
    bad_crc = bytearray(zip_bytes({'member.txt': b'synthetic payload'}))
    offset = 30 + len('member.txt')
    bad_crc[offset] ^= 1
    builder.add('controls/bad-crc.zip', bytes(bad_crc), 'zip', 'archives',
                {'kind': 'bytes'}, tier='control', expectation='unchanged')
    builder.add('archives/empty.zip', zip_bytes({}), 'zip', 'archives', {'kind': 'zip'})
    builder.add('archives/unicode.zip', zip_bytes({'данные/測定.json': b' { "value": 1 } '}),
                'zip', 'archives', {'kind': 'zip', 'children': {'данные/測定.json': {'kind': 'json'}}})
    nested = zip_bytes({'payload.json': b' { "n": 1 } '})
    builder.add('archives/nested.zip', zip_bytes({'inner.zip': nested, 'notes.txt': b'keep'}),
                'zip', 'archives', {'kind': 'zip', 'children': {
                    'inner.zip': {'kind': 'zip', 'children': {'payload.json': {'kind': 'json'}}}}})
    def encrypted_zip():
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            (temp / 'synthetic.txt').write_bytes(b'synthetic protected payload')
            command(['zip', '-q', '-P', 'synthetic-only-password', str(temp / 'encrypted.zip'),
                     'synthetic.txt'], cwd=temp)
            builder.add('controls/encrypted.zip', (temp / 'encrypted.zip').read_bytes(),
                        'zip', 'archives', {'kind': 'bytes'}, tier='control', expectation='unchanged')
    builder.optional('encrypted-zip', encrypted_zip)
    # Linked TAR exercises metadata and links without an external target.
    import tarfile
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w', format=tarfile.PAX_FORMAT) as archive:
        members = [('data.txt', tarfile.REGTYPE, ''), ('hard.txt', tarfile.LNKTYPE, 'data.txt'),
                   ('soft.txt', tarfile.SYMTYPE, 'data.txt')]
        for name, kind, target in members:
            info = tarfile.TarInfo(name)
            info.type, info.linkname, info.mode, info.mtime = kind, target, 0o640, 1577934246
            info.uid, info.gid, info.uname, info.gname = 1000, 1000, 'synthetic', 'synthetic'
            raw = b'synthetic linked payload\n' * 128 if kind == tarfile.REGTYPE else b''
            info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw) if raw else None)
    builder.add('archives/linked.tar', buffer.getvalue(), 'tar', 'archives', {'kind': 'tar'})

    def rich_images():
        import numpy as np
        from PIL import Image, ImageCms
        import tifffile
        high = np.arange(128 * 128, dtype='<u2').reshape(128, 128)
        stream = io.BytesIO()
        Image.fromarray(high).save(stream, 'PNG', compress_level=0)
        builder.add('images/high-depth.png', stream.getvalue(), 'png', 'images', {'kind': 'raster'})
        stream = io.BytesIO()
        exif = Image.Exif()
        exif[0x010E], exif[0x0112], exif[0x013B] = 'Synthetic metadata profile', 1, 'Frbench'
        icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        Image.new('RGB', (128, 128), 'red').save(stream, 'JPEG', quality=95, exif=exif, icc_profile=icc)
        builder.add('images/metadata.jpg', stream.getvalue(), 'jpg', 'images', {'kind': 'raster'})
        values = np.array([0, 0x80000000, 0x7FC01234, 0x3F800000], dtype='<u4').view('<f4')
        path = builder.directory / 'scientific/float-edge.tiff'
        path.parent.mkdir(parents=True, exist_ok=True)
        tifffile.imwrite(path, values.reshape(2, 2), metadata=None, description='Exact float edge bits')
        builder.add('scientific/float-edge.tiff', None, 'tiff', 'scientific', {'kind': 'tiff'})
    builder.optional('rich-images', rich_images)

    def rich_pdf():
        import pikepdf
        pdf = pikepdf.Pdf.new()
        page = pdf.add_blank_page(page_size=(300, 300))
        font = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name.Font,
                                                  Subtype=pikepdf.Name.Type1,
                                                  BaseFont=pikepdf.Name.Helvetica))
        page.Resources = pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font))
        page.Contents = pdf.make_stream(b'BT /F1 12 Tf 20 250 Td (Synthetic searchable text) Tj ET\n' * 40)
        link = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name.Annot,
            Subtype=pikepdf.Name.Link, Rect=pikepdf.Array([20, 245, 200, 265]),
            A=pikepdf.Dictionary(S=pikepdf.Name.URI, URI=pikepdf.String('https://example.org/synthetic'))))
        widget = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name.Annot,
            Subtype=pikepdf.Name.Widget, FT=pikepdf.Name.Tx, T=pikepdf.String('answer'),
            V=pikepdf.String('Synthetic response'), Rect=pikepdf.Array([20, 100, 200, 125]),
            DA=pikepdf.String('/F1 12 Tf 0 g'), P=page.obj))
        page.Annots = pikepdf.Array([link, widget])
        pdf.Root.AcroForm = pikepdf.Dictionary(Fields=pikepdf.Array([widget]),
            DR=pikepdf.Dictionary(Font=pikepdf.Dictionary(F1=font)),
            DA=pikepdf.String('/F1 12 Tf 0 g'))
        pdf.docinfo['/Title'] = 'Synthetic text, link and form profile'
        pdf.attachments['synthetic.txt'] = b'Exact attachment bytes'
        stream = io.BytesIO()
        pdf.save(stream, compress_streams=False)
        builder.add('documents/text-form-link.pdf', stream.getvalue(), 'pdf', 'documents', {'kind': 'pdf'})
    builder.optional('rich-pdf', rich_pdf)

    def scientific_graphs():
        import h5py
        import netCDF4
        import numpy as np
        edge = np.array([0, 0x8000000000000000, 0x7FF8000000001234, 0x3FF0000000000000],
                        dtype='<u8').view('<f8')
        path = builder.directory / 'scientific/linked-graph.h5'
        path.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(path, 'w') as file:
            data = file.create_dataset('values', data=edge)
            group = file.create_group('nested')
            group['cycle'] = file
            file['alias'] = data
            file['soft'] = h5py.SoftLink('/values')
            file['external'] = h5py.ExternalLink('not-opened.h5', '/synthetic')
            file.attrs['reference'] = data.ref
            file.attrs['edge'] = edge
        builder.add('scientific/linked-graph.h5', None, 'h5', 'scientific', {'kind': 'hdf5'})
        path = builder.directory / 'scientific/nested-groups.nc4'
        with netCDF4.Dataset(path, 'w', format='NETCDF4') as file:
            file.createDimension('x', 4)
            group = file.createGroup('measurements')
            values = group.createVariable('edge', 'f8', ('x',))
            values[:] = edge
            values.units = 'synthetic units'
            group.setncattr('edge_metadata', edge)
        builder.add('scientific/nested-groups.nc4', None, 'nc4', 'scientific', {'kind': 'netcdf'})
    builder.optional('scientific-graphs', scientific_graphs)

    def multi_stream():
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'multi.mkv'
            command(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=64x64:rate=10:duration=1',
                     '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
                     '-f', 'lavfi', '-i', 'sine=frequency=660:duration=1',
                     '-map', '0:v', '-map', '1:a', '-map', '2:a',
                     '-vf', 'select=eq(n\\,0)+eq(n\\,1)+eq(n\\,3)+eq(n\\,6)+eq(n\\,9)',
                     '-vsync', 'vfr', '-c:v', 'ffv1', '-c:a', 'pcm_s16le',
                     '-metadata', 'title=Synthetic multiple streams',
                     '-metadata:s:a:0', 'language=eng', '-metadata:s:a:1', 'language=rus',
                     str(output)])
            builder.add('video/multiple-streams.mkv', output.read_bytes(), 'mkv', 'video', {'kind': 'video'})
    builder.optional('multi-stream-media', multi_stream)

    # Stress is an explicit tier; ordinary smoke/extended measurements remain identifiable.
    scale = builder.scale
    seed = b'Synthetic stress payload; no private data.\n'
    size = 16 * 1024 * 1024 * scale
    payload = (seed * (size // len(seed)) + seed[:size % len(seed)])
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        info = tarfile.TarInfo('large.txt')
        info.size, info.mode, info.mtime = len(payload), 0o644, 1577934246
        archive.addfile(info, io.BytesIO(payload))
    builder.add('stress/large.tar', buffer.getvalue(), 'tar', 'archives', {'kind': 'tar'},
                tier='stress', note='16 MiB per --scale unit; report separately from ordinary cases')
