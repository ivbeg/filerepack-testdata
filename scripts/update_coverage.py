"""Refresh the JSON and Markdown coverage snapshots from a local filerepack checkout."""

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from frbench.common import read_manifest, write_json  # noqa: E402
from frbench.runner import coverage  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--filerepack', required=True, help='Local source checkout')
    args = parser.parse_args()
    data = coverage(ROOT, args.filerepack)
    manifest = read_manifest(ROOT)
    write_json(ROOT / 'docs/coverage.json', data)

    tier_counts = Counter(case['tier'] for case in manifest['cases'])
    scope_counts = Counter(case['scope'] for case in manifest['cases'])
    original_count = sum(case['scope'] == 'original' for case in manifest['cases'])
    native_original = data['native_or_original']
    lines = [
        '# Coverage snapshot',
        '',
        "Catalog: local filerepack source; regenerate with `python scripts/update_coverage.py --filerepack ../filerepack`.",
        '',
        f"- {len(manifest['cases'])} cases: {tier_counts['smoke']} smoke, "
        f"{tier_counts['extended']} extended, {tier_counts['control']} rejection controls, "
        f"{tier_counts['stress']} separate stress fixtures.",
        f"- {data['covered']}/{data['supported']} registered extension routes have non-control fixtures.",
        f"- {native_original} extensions have native or original fixtures.",
        f"- {data['handlers_covered']}/{data['handler_count']} handler groups have fixtures.",
        f"- {original_count} upstream originals; remaining fixtures are generated or routing derivatives.",
        f"- {data['filename_routes_covered']}/{len(data['filename_routes'])} compound/content-detected filename routes have fixtures.",
        '- Directory Zarr v2 is an additional store fixture outside the flat extension denominator.',
        '',
        'Handler and extension coverage means an input exists for that path. It does not guarantee '
        'that every sample is accepted for rewriting or becomes smaller.',
        '',
        '## Fixture scopes',
        '',
        '| Scope | Cases | Meaning |',
        '|---|---:|---|',
        '| alias | %d | Existing bitstream under another supported routing suffix. |' % scope_counts['alias'],
        '| container-only | %d | Generic ZIP/TAR/SQLite payload without an application-format claim. |' % scope_counts['container-only'],
        '| native | %d | Generated format-shaped profile checked by the listed oracle. |' % scope_counts['native'],
        '| original | %d | Unmodified, license-reviewed upstream regression sample. |' % scope_counts['original'],
        '| syntax | %d | Valid generic structure without application/render qualification. |' % scope_counts['syntax'],
        '',
        '## Handler groups',
        '',
        '| Handler/family | Cases | Native/original/syntax case |',
        '|---|---:|---|',
    ]
    for row in data['handlers']:
        evidence = 'yes' if row['native_original_or_syntax'] else 'transport/alias only'
        lines.append(f"| `{row['handler']}` | {row['cases']} | {evidence} |")
    lines.extend(['', '## Extension routes', '', '| Extension | Cases | Scopes |', '|---|---:|---|'])
    for row in data['extensions']:
        scopes = ', '.join(row['scopes']) if row['scopes'] else 'missing'
        lines.append(f"| .{row['extension']} | {row['cases']} | {scopes} |")
    lines.extend(['', '## Filename routes', '', '| Filename suffix or detected type | Cases |', '|---|---:|'])
    for row in data['filename_routes']:
        lines.append(f"| `{row['route']}` | {', '.join(row['cases']) if row['cases'] else 'missing'} |")
    lines.extend([
        '',
        'The ODF packages use the registered media-type/extension pairs from the '
        '[OASIS OpenDocument 1.3 MIME type table](https://docs.oasis-open.org/office/OpenDocument/v1.3/os/part3-schema/OpenDocument-v1.3-os-part3-schema.pdf). '
        'The `.otf` sample is an ODF formula template selected by ZIP content, because `.otf` is not a flat registry extension.',
        '',
        '## Remaining depth gaps',
        '',
        'More real user-created office, video and scientific files, application rendering, larger '
        'heterogeneous archives and opt-in OLE content transforms would improve representativeness. '
        'Bounded nesting, archive links/controls, HDF5 graphs/references, nested NetCDF groups, '
        'high-bit-depth pixels, image metadata, rich PDF and multi-stream media are included. '
        'The current synthetic corpus '
        'deliberately includes favorable compression opportunities.',
        '',
        'CRX3 is included as a correctly signed ZIP package and the independent oracle checks the '
        'signature. The current local filerepack run safely leaves it unchanged because the archive '
        'reader rejects the CRX prefix. This fixture records input coverage, not a claim of successful '
        'CRX recompression.',
        '',
        'Original licensed samples and generated files must be analyzed separately for empirical claims.',
        'The catalog is a snapshot of the local registry, including optional RTF. The committed '
        '95827f3 implementation has 311 flat extensions and 101 handlers. Extra corpus routes '
        'are reported as removed registry entries when comparing an older implementation; '
        'strict coverage gates uncovered live routes, unresolved handler mappings and filename paths.',
        '',
    ])
    (ROOT / 'docs/COVERAGE.md').write_text('\n'.join(lines))
    print(f"Updated docs/coverage.json and docs/COVERAGE.md: "
          f"{data['covered']}/{data['supported']} extensions, "
          f"{data['handlers_covered']}/{data['handler_count']} handler groups.")


if __name__ == '__main__':
    main()
