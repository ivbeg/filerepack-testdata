import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def read_manifest(root=ROOT):
    root = Path(root).resolve()
    manifest = json.loads((root / 'corpus/manifest.json').read_text())
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
    return manifest


def check_manifest(root=ROOT):
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
    return failures


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
