import argparse
import json
from pathlib import Path

from .common import check_manifest, corpus_root, read_manifest
from .runner import PROFILES, compare, coverage, environment, run


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return value


def main():
    parser = argparse.ArgumentParser(description='Preservation-aware filerepack corpus benchmark')
    sub = parser.add_subparsers(dest='command', required=True)
    generate = sub.add_parser('generate', help='Regenerate synthetic fixtures; originals remain pinned')
    generate.add_argument('--root', help='Corpus checkout; defaults to configured root/current checkout')
    generate.add_argument('--filerepack', help='Local checkout for extension catalog (required on first generation)')
    generate.add_argument('--scale', type=positive, default=1, help='Synthetic record count multiplier')
    generate.add_argument('--minimal', action='store_true', help='Stdlib corpus only; optional gaps explicit')
    generate.add_argument('--strict', action='store_true', help='Fail if any generator fails')
    generate.add_argument('--extend', action='store_true',
                          help='Add new coverage without rebuilding existing generated files')
    bench = sub.add_parser('run', help='Run each case in a fresh copy/process')
    bench.add_argument('--root', help='Corpus checkout; or FILEREPACK_TESTDATA_ROOT')
    bench.add_argument('--filerepack', help='Source checkout; otherwise use installed filerepack')
    bench.add_argument('--profile', choices=PROFILES, default='lossless')
    bench.add_argument('--repeat', type=positive, default=1)
    bench.add_argument('--warmup', type=int, choices=range(0, 11), default=0)
    bench.add_argument('--timeout', type=positive, default=120)
    bench.add_argument('--output', required=True, help='New result directory; never overwrites')
    bench.add_argument('--family', help='Comma-separated family names')
    bench.add_argument('--ext', help='Comma-separated extensions')
    bench.add_argument('--case', help='Comma-separated ID substrings')
    bench.add_argument('--tier', choices=['smoke', 'extended', 'control', 'stress', 'all'], default='all')
    bench.add_argument('--native-only', action='store_true')
    bench.add_argument('--keep-work', action='store_true', help='Retain failed disposable work for diagnosis')
    bench.add_argument('--options', default='{}', help='RepackOptions JSON overrides; exact lossless only')
    bench.add_argument('--strict-verifiers', action='store_true',
                       help='Fail on any missing independent verifier')
    bench.add_argument('--min-verified', type=positive, default=1,
                       help='Required verified selected cases, including rejection controls')
    bench.add_argument('--require-outcomes', action='store_true',
                       help='Enforce case-specific qualification outcome contracts')
    check = sub.add_parser('check', help='Verify every corpus checksum and provenance record')
    check.add_argument('--root', help='Corpus checkout; or FILEREPACK_TESTDATA_ROOT')
    check.add_argument('--decode', action='store_true', help='Also open every positive fixture with its independent oracle')
    check.add_argument('--strict-verifiers', action='store_true',
                       help='Decode fixtures and fail on missing dependencies')
    cov = sub.add_parser('coverage', help='Show coverage and live format registry drift')
    cov.add_argument('--root', help='Corpus checkout; or FILEREPACK_TESTDATA_ROOT')
    cov.add_argument('--filerepack')
    cov.add_argument('--json', action='store_true')
    cov.add_argument('--strict', action='store_true', help='Fail on missing live extension/handler/filename coverage')
    sub.add_parser('doctor', help='Inventory runtime and tools')
    diff = sub.add_parser('compare', help='Compare two reports by case ID')
    diff.add_argument('before')
    diff.add_argument('after')
    args = parser.parse_args()
    try:
        if args.command in ('generate', 'run', 'check', 'coverage'):
            args.root = str(corpus_root(args.root))
        if args.command == 'generate':
            from .generate import generate
            code = generate(args)
        elif args.command == 'run':
            code = run(args)
        elif args.command == 'check':
            failures = check_manifest(Path(args.root))
            print('\n'.join(failures) if failures else 'All corpus checksums and provenance records match.')
            if (args.decode or args.strict_verifiers) and not failures:
                from .oracles import fingerprint, require
                checked = skipped = 0
                for case in read_manifest(args.root)['cases']:
                    if case['expectation'] == 'unchanged':
                        continue
                    missing = require(case['oracle'])
                    if missing:
                        skipped += 1
                        print('SKIP', case['id'], ', '.join(missing))
                        if args.strict_verifiers:
                            failures.append(case['id'] + ': missing verifier: ' + ', '.join(missing))
                        continue
                    try:
                        fingerprint(Path(args.root) / case['path'], case['oracle'])
                        checked += 1
                    except Exception as exc:
                        message = case['id'] + ': ' + type(exc).__name__ + ': ' + str(exc)
                        failures.append(message)
                        print('FAIL', message)
                print(f'{checked} fixtures decoded; {skipped} missing-dependency skips; {len(failures)} failures.')
            code = bool(failures)
        elif args.command == 'coverage':
            result = coverage(args.root, args.filerepack)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"{result['covered']}/{result['supported']} extensions have positive fixtures; "
                      f"{result['native_or_original']} have native/original fixtures.")
                print(f"{result['handlers_covered']}/{result['handler_count']} distinct handler groups have fixtures.")
                print('Missing: ' + ', '.join(result['missing']))
                print(f"Special filename routes: {result['filename_routes_covered']}/"
                      f"{len(result['filename_routes'])} covered.")
                if result['drift']:
                    print('Registry drift: ' + json.dumps(result['drift']))
                for gap in result['generation_gaps']:
                    print('Generator gap: ' + gap['generator'] + ': ' + gap['reason'])
            incomplete = (result['missing'] or result['missing_handlers'] or
                          result['unmapped_extensions'] or
                          any(not route['covered'] for route in result['filename_routes']) or
                          result['generation_gaps'])
            code = bool(args.strict and incomplete)
        elif args.command == 'compare':
            print(json.dumps(compare(args.before, args.after), indent=2))
            code = 0
        else:
            print(json.dumps(environment(), indent=2))
            code = 0
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    raise SystemExit(code)
