"""Measure a fixed committed implementation snapshot without modifying its checkout."""
import argparse
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from frbench.common import write_json  # noqa: E402


def portable_report(report):
    # Preserve timings, verification/routing and accepted-result evidence while
    # leaving duplicated effective options, scratch paths and raw diagnostics local.
    for attempt in report['attempts']:
        for packer in attempt.get('packer_results', []):
            details = packer.pop('details', {})
            if details.get('resources'):
                packer['resources'] = details['resources']
            evidence = details.get('evidence', [])
            for item in evidence:
                if item.get('executable'):
                    item['executable'] = Path(item['executable']).name
            if evidence:
                packer['evidence'] = evidence
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--filerepack', type=Path, required=True)
    parser.add_argument('--revision', required=True, help='Explicit immutable commit/ref to snapshot')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--publish', type=Path, help='Optional portable JSON evidence destination')
    parser.add_argument('--timeout', type=int, default=90)
    args = parser.parse_args()
    commit = subprocess.check_output(['git', '-C', str(args.filerepack), 'rev-parse',
                                      args.revision + '^{commit}'], text=True).strip()
    archive = subprocess.check_output(['git', '-C', str(args.filerepack), 'archive', commit])
    with tempfile.TemporaryDirectory(prefix='frbench-source-') as temp:
        source = Path(temp)
        with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
            if any(Path(m.name).is_absolute() or '..' in Path(m.name).parts or m.issym()
                   or m.islnk() for m in stream.getmembers()):
                raise ValueError('Unsafe implementation archive')
            if sys.version_info >= (3, 12):
                stream.extractall(source, filter='data')
            else:
                stream.extractall(source)
        write_json(source / '.frbench-source.json', {'commit': commit, 'dirty': False,
                   'snapshot': 'git archive; working changes and ignored build artifacts excluded'})
        process = subprocess.run([sys.executable, '-m', 'frbench', 'run', '--root', str(ROOT),
                                  '--filerepack', str(source), '--repeat', '3', '--warmup', '1',
                                  '--strict-verifiers', '--require-outcomes', '--timeout', str(args.timeout),
                                  '--min-verified', str(len(__import__('frbench.common', fromlist=['read_manifest']).read_manifest(ROOT)['cases'])),
                                  '--output', str(args.output)], cwd=ROOT)
    report_path = args.output / 'report.json'
    if args.publish and report_path.is_file():
        report = json.loads(report_path.read_text(encoding='utf-8'))
        report['execution_exit_code'] = process.returncode
        report['evidence_notes'] = ['All measurements use fresh copies, 3 measured attempts and 1 discarded warmup.',
                                  'Native optimizer absence can result in unchanged files; tool identities are recorded.',
                                  'Configured CI platforms are not evidence of executed platform qualification.']
        write_json(args.publish, portable_report(report))
    raise SystemExit(process.returncode)


if __name__ == '__main__':
    main()
