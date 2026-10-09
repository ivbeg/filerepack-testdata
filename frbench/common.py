import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def corpus_root(value=None):
    if value is not None:
        return Path(value).expanduser().resolve()
    configured = os.environ.get('FILEREPACK_TESTDATA_ROOT')
    if configured:
        return Path(configured).expanduser().resolve()
    for candidate in (Path.cwd(), ROOT):
        if (candidate / 'corpus/manifest.json').is_file():
            return candidate.resolve()
    raise ValueError('Corpus assets are not included in runtime wheels. Clone '
                     'https://github.com/ivbeg/filerepack-testdata and pass --root PATH '
                     'or set FILEREPACK_TESTDATA_ROOT=PATH.')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def file_inventory(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Symlinks are not allowed in corpus inventories: ' + str(path))
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_file():
        return {'bytes': path.stat().st_size, 'sha256': sha256(path)}
    if any(p.is_symlink() for p in path.rglob('*')):
        raise ValueError('Symlink inside corpus directory: ' + str(path))
    items = {str(p.relative_to(path)): file_inventory(p)
             for p in sorted(path.rglob('*')) if p.is_file()}
    raw = json.dumps(items, sort_keys=True, separators=(',', ':')).encode()
    return {'bytes': sum(i['bytes'] for i in items.values()),
            'sha256': hashlib.sha256(raw).hexdigest(), 'files': items}


def read_manifest(root=None):
    root = corpus_root(root)
    path = root / 'corpus/manifest.json'
    if not path.is_file():
        raise ValueError('Corpus manifest missing: ' + str(path) +
                         '. Pass --root to a filerepack-testdata checkout.')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported manifest version')
    seen = set()
    for case in manifest['cases']:
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', case['id']):
            raise ValueError('Unsafe case ID: ' + case['id'])
        if case['id'] in seen:
            raise ValueError('Duplicate case ID: ' + case['id'])
        seen.add(case['id'])
        path = root / case['path']
        if path.is_symlink() or not path.resolve().is_relative_to(root / 'corpus'):
            raise ValueError('Corpus path escapes root: ' + case['path'])
        if not case.get('license') or not case.get('provenance'):
            raise ValueError('Missing provenance: ' + case['id'])
        if case.get('scope') not in ('native', 'original', 'syntax', 'alias', 'container-only'):
            raise ValueError('Invalid scope: ' + case['id'])
        if case.get('tier') not in ('smoke', 'extended', 'control', 'stress'):
            raise ValueError('Invalid tier: ' + case['id'])
        if case.get('expectation') not in ('observe', 'unchanged'):
            raise ValueError('Invalid expectation: ' + case['id'])
        if not isinstance(case.get('oracle'), dict) or not case['oracle'].get('kind'):
            raise ValueError('Missing oracle: ' + case['id'])
    return manifest


def check_manifest(root=None):
    root = corpus_root(root)
    manifest = read_manifest(root)
    failures = []
    for case in manifest['cases']:
        path = Path(root) / case['path']
        try:
            actual = file_inventory(path)
            if actual != case['inventory']:
                failures.append(case['id'] + ': checksum/size differs')
        except (OSError, ValueError) as exc:
            failures.append(case['id'] + ': ' + str(exc))
        for name in case.get('provenance', {}).get('license_files', []):
            legal = root / name
            if not legal.resolve().is_relative_to(root / 'licenses') or not legal.is_file():
                failures.append(case['id'] + ': missing/invalid legal notice: ' + name)
    originals = {case['id']: case for case in manifest['cases'] if case['scope'] == 'original'}
    index_path = root / 'corpus/originals/index.json'
    if originals or index_path.is_file():
        if not index_path.is_file():
            failures.append('Original index missing')
        else:
            indexed = json.loads(index_path.read_text(encoding='utf-8'))['cases']
            records = {case['id']: case for case in indexed}
            if len(records) != len(indexed) or records.keys() != originals.keys():
                failures.append('Original index IDs differ from manifest')
            for case_id in records.keys() & originals.keys():
                if records[case_id] != originals[case_id]:
                    failures.append(case_id + ': original index differs from manifest')
    return failures


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
