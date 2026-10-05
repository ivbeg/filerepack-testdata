#!/usr/bin/env python3
"""Restore only pinned original bytes; never accept a changed upstream download."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    index = json.loads((root / 'corpus/originals/index.json').read_text())
    for case in index['cases']:
        path = (root / case['path']).resolve()
        if not path.is_relative_to(root / 'corpus/originals'):
            raise ValueError('Invalid original path')
        expected = case['inventory']['sha256']
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('Existing bytes do not match pin: ' + path.name)
            continue
        url = case['provenance']['source']
        if not url.startswith('https://raw.githubusercontent.com/'):
            raise ValueError('Unexpected upstream URL')
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(case['inventory']['bytes'] + 1)
        if len(data) != case['inventory']['bytes'] or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Upstream checksum mismatch: ' + path.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print('Restored', path.name)


if __name__ == '__main__':
    main()
