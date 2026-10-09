"""Registry facts from a trusted implementation checkout, isolated from the harness."""
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SPECIAL_FAMILY = {
    '7z': '7z', 'cb7': '7z', 'rar': 'rar', 'cbr': 'rar', 'tar': 'tar', 'cbt': 'tar',
    'cpio': 'cpio', 'cpbz2': 'cpio.bz2',
    'tgz': 'tar.gz', 'taz': 'tar.z', 'gem': 'tar', 'crate': 'tar.gz', 'unitypackage': 'tar.gz',
    'tbz': 'tar.bz2', 'tbz2': 'tar.bz2', 'txz': 'tar.xz', 'tzst': 'tar.zst',
    'tlz': 'tar.lz', 'tzo': 'tar.lzo', 'cab': 'cab', 'wim': 'wim',
}


def discover_catalog(path):
    source = Path(path).resolve()
    if not (source / 'filerepack/consts.py').is_file():
        raise ValueError('Not a filerepack checkout: ' + str(source))
    script = '''
import json
from filerepack import consts, formats
try:
    from filerepack import format_registry as registry
except ImportError:
    registry = formats
print('FRBENCH_CATALOG=' + json.dumps({
    'archive_extensions': list(consts.ARCHIVE_EXTS),
    'standalone_extensions': list(consts.STANDALONE_EXTS),
    'aliases': getattr(registry, 'STANDALONE_ALIASES', {}),
    'families': getattr(registry, 'SPECIAL_FAMILY', {}),
    'compound_families': getattr(registry, 'COMPOUND_FAMILY', {}),
    'inspection_only': [k for k, v in getattr(registry, 'FORMAT_REGISTRY', {}).items()
                        if getattr(v, 'inspection_only', False)],
}))
'''
    env = dict(os.environ, PYTHONPATH=str(source))
    process = subprocess.run([sys.executable, '-c', script], cwd=source, env=env,
                             capture_output=True, text=True, timeout=30)
    if process.returncode:
        raise ValueError('Registry discovery failed: ' + process.stderr.strip()[-2000:])
    payload = next((line.removeprefix('FRBENCH_CATALOG=')
                    for line in process.stdout.splitlines()
                    if line.startswith('FRBENCH_CATALOG=')), None)
    if payload is None:
        raise ValueError('Registry discovery returned no metadata')
    facts = json.loads(payload)
    packers = {}
    for node in ast.walk(ast.parse((source / 'filerepack/dispatch.py').read_text())):
        target = (node.target if isinstance(node, ast.AnnAssign) else
                  node.targets[0] if isinstance(node, ast.Assign) and node.targets else None)
        if isinstance(target, ast.Name) and target.id == '_PACKERS':
            if not isinstance(node.value, ast.Dict):
                raise ValueError('Unsupported dispatcher metadata layout')
            for key, value in zip(node.value.keys, node.value.values):
                function = value.args[0] if isinstance(value, ast.Call) and value.args else value
                if isinstance(function, ast.Name):
                    packers[ast.literal_eval(key)] = function.id
    families = {**SPECIAL_FAMILY, **facts['families']}
    mapping = {ext: 'archive:' + families.get(ext, 'zip')
               for ext in facts['archive_extensions']}
    mapping.update({ext: packers.get(facts['aliases'].get(ext, ext), 'unmapped:' + ext)
                    for ext in facts['standalone_extensions']})
    routes = set(facts['compound_families'])
    routes.update('tar.' + codec for codec in
                  ('gz', 'xz', 'bz2', 'zst', 'br', 'lz4', 'lz', 'lzma', 'lzo', 'z'))
    routes.update(ext + '.' + codec for ext in ('rds', 'rda', 'rdata')
                  for codec in ('gz', 'gzip', 'bz2', 'xz'))
    routes.update(('warc.gz', 'warc.gzip', 'cpio', 'cpio.bz2', 'otf'))
    commit = subprocess.run(['git', '-C', str(source), 'rev-parse', 'HEAD'],
                            capture_output=True, text=True).stdout.strip() or None
    registry_hash = hashlib.sha256()
    for name in ('format_registry.py', 'formats.py', 'consts.py', 'dispatch.py'):
        file = source / 'filerepack' / name
        if file.is_file():
            registry_hash.update(name.encode() + b'\0' + file.read_bytes())
    return {'schema_version': 2, **facts,
            'supported_extensions': sorted(set(facts['archive_extensions'] +
                                               facts['standalone_extensions'])),
            'handler_by_extension': mapping, 'filename_suffixes': sorted(routes),
            'implementation': {'commit': commit, 'registry_sha256': registry_hash.hexdigest()}}
