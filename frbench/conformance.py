"""Executable, independently decoded oracle profile qualification.

All inventory profiles have an acceptance and bounded destructive-corruption check.
Selected envelope formats additionally have nonidentical equivalent re-encodings.
Deep metadata/value mutations are covered by the named regression tests.
"""
import bz2
import gzip
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from .common import corpus_root, read_manifest
from .oracles import fingerprint, require


def profile_key(config):
    return ':'.join(str(config.get(key, '')) for key in ('kind', 'format', 'codec'))


def inventory(root=None):
    root = corpus_root(root)
    return json.loads((root / 'docs/oracle-conformance.json').read_text(encoding='utf-8'))


def equivalent(source, destination, config):
    kind = config['kind']
    if kind in ('zip', 'npz', 'checkpoint') and not config.get('package'):
        with zipfile.ZipFile(source) as old, zipfile.ZipFile(destination, 'w') as new:
            new.comment = old.comment
            for original in old.infolist():
                info = __import__('copy').copy(original)
                info.compress_type = 0 if info.filename in config.get('stored_first', []) else zipfile.ZIP_DEFLATED
                new.writestr(info, old.read(original), compresslevel=9)
        return 'zip-recompression'
    if kind == 'json':
        from .oracles import json_tokens
        destination.write_bytes(json_tokens(source.read_bytes()).encode())
        return 'json-whitespace'
    if kind == 'jsonl':
        from .oracles import bytes_state
        destination.write_bytes(b''.join(value.encode() + ending for value, ending in
                                        bytes_state(source.read_bytes(), config)))
        return 'jsonl-whitespace'
    if kind == 'xml':
        from xml.dom import minidom
        destination.write_bytes(minidom.parseString(source.read_bytes()).toxml(encoding='utf-8'))
        return 'xml-serialization'
    if kind == 'stream':
        from .generate import compress
        from .oracles import decode_stream
        destination.write_bytes(compress(decode_stream(source.read_bytes(), config['codec']),
                                         config['codec'], 9))
        return 'stream-recompression'
    if kind in ('tgs', 'blend', 'warc', 'r') and source.read_bytes()[:2] == b'\x1f\x8b':
        destination.write_bytes(gzip.compress(gzip.decompress(source.read_bytes()), compresslevel=9, mtime=0))
        return 'gzip-recompression'
    if kind == 'cpbz2':
        destination.write_bytes(bz2.compress(bz2.decompress(source.read_bytes()), compresslevel=9))
        return 'bzip2-recompression'
    if kind == 'pdf':
        import pikepdf
        with pikepdf.open(source) as pdf:
            pdf.save(destination, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        return 'pdf-recompression'
    if kind == 'arrow':
        import pyarrow as pa
        import pyarrow.feather as feather
        import pyarrow.orc as orc
        import pyarrow.parquet as pq
        form = config['format']
        if form == 'parquet':
            pq.write_table(pq.read_table(source), destination, compression='zstd')
        elif form == 'feather':
            feather.write_feather(feather.read_table(source), destination, compression='zstd')
        elif form == 'orc':
            orc.write_table(orc.read_table(source), destination, compression='zlib')
        else:
            with pa.memory_map(str(source)) as file:
                try:
                    table = pa.ipc.open_file(file).read_all()
                except pa.ArrowInvalid:
                    file.seek(0)
                    table = pa.ipc.open_stream(file).read_all()
            with pa.OSFile(str(destination), 'wb') as file:
                with pa.ipc.new_file(file, table.schema, options=pa.ipc.IpcWriteOptions(compression='zstd')) as writer:
                    writer.write_table(table)
        return 'arrow-recompression'
    if kind == 'mat':
        import scipy.io
        scipy.io.savemat(destination, {k: v for k, v in scipy.io.loadmat(source).items()
                                      if not k.startswith('__')}, do_compression=True)
        return 'mat-recompression'
    if kind == 'font':
        from fontTools.ttLib import TTFont
        with TTFont(source, recalcTimestamp=False) as font:
            font.save(destination)
        return 'font-serialization'
    if kind == 'ole':
        destination.write_bytes(source.read_bytes() + bytes(512))
        return 'unused-ole-sector'
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copyfile(source, destination)
    return 'byte-identity'


def qualify(entry, case, root):
    missing = require(case['oracle'])
    if missing:
        return {'profile': entry['profile'], 'status': 'skipped', 'missing': missing}
    source = root / case['path']
    with tempfile.TemporaryDirectory(prefix='frbench-conformance-') as temp:
        candidate = Path(temp) / source.name
        expected = fingerprint(source, case['oracle'])
        strategy = equivalent(source, candidate, case['oracle'])
        if expected != fingerprint(candidate, case['oracle']):
            raise ValueError(entry['profile'] + ': equivalent candidate differs')
        if candidate.is_dir():
            import zarr
            group = zarr.open_group(str(candidate), mode='r+')
            arrays = []
            group.visititems(lambda name, obj: arrays.append(obj) if isinstance(obj, zarr.Array) else None)
            data = next(obj for obj in arrays if obj.size)
            index = (0,) * data.ndim
            data[index] = data[index] + 1
        elif case['oracle']['kind'] == 'tar' and not case['oracle'].get('codec'):
            import tarfile
            with tarfile.open(source) as old, tarfile.open(candidate, 'w') as new:
                mutated = False
                for info in old:
                    stream = old.extractfile(info) if info.isfile() else None
                    payload = stream.read() if stream else None
                    if payload and not mutated:
                        payload = bytes([payload[0] ^ 1]) + payload[1:]
                        mutated = True
                    new.addfile(info, __import__('io').BytesIO(payload) if payload is not None else None)
                if not mutated:
                    raise ValueError('No TAR member payload for mutation')
        else:
            data = source.read_bytes()
            candidate.write_bytes(data[:max(1, len(data) // 2)])
        try:
            corrupted = fingerprint(candidate, case['oracle'])
        except Exception:
            detected = True
        else:
            detected = expected != corrupted
        if not detected:
            raise ValueError(entry['profile'] + ': destructive payload truncation was accepted')
        return {'profile': entry['profile'], 'status': 'passed', 'equivalence': strategy,
                'corruption': 'array-value' if source.is_dir() else
                              ('tar-member-payload' if case['oracle']['kind'] == 'tar' and
                               not case['oracle'].get('codec') else 'payload-truncation')}


def run(root=None, strict=False):
    root = corpus_root(root)
    cases = {case['id']: case for case in read_manifest(root)['cases']}
    entries = inventory(root)['profiles']
    expected = {profile_key(c['oracle']) for c in cases.values() if c['expectation'] == 'observe'}
    actual = {entry['profile'] for entry in entries}
    if expected != actual or len(entries) != len(actual):
        raise ValueError('Oracle conformance inventory is incomplete or duplicated')
    results = []
    for entry in entries:
        try:
            result = qualify(entry, cases[entry['case']], root)
        except Exception as exc:
            result = {'profile': entry['profile'], 'status': 'failed',
                      'reason': type(exc).__name__ + ': ' + str(exc)}
        results.append(result)
        print(entry['profile'], result['status'], result.get('reason', ''), flush=True)
    return {'profiles': results, 'strict': strict,
            'passed': sum(r['status'] == 'passed' for r in results),
            'skipped': sum(r['status'] == 'skipped' for r in results),
            'failed': sum(r['status'] == 'failed' for r in results)}
