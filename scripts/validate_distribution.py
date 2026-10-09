#!/usr/bin/env python3
"""Build and exercise wheel/sdist outside the checkout, with explicit corpus discovery."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def execute(argv, *, cwd, env=None, expected=0):
    process = subprocess.run([str(arg) for arg in argv], cwd=cwd, env=env,
                             capture_output=True, text=True, timeout=300)
    if process.returncode != expected:
        raise RuntimeError('Artifact check failed: ' + ' '.join(str(v) for v in argv) +
                           '\n' + process.stdout[-2000:] + process.stderr[-4000:])
    return process


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Optional portable JSON result')
    args = parser.parse_args()
    results = []
    with tempfile.TemporaryDirectory(prefix='frbench-distribution-') as temp:
        temp = Path(temp)
        source = temp / 'source'
        source.mkdir()
        paths = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '--cached',
                                         '--others', '--exclude-standard', '-z']).decode().split('\0')
        for name in set(paths):
            if name and (ROOT / name).is_file():
                destination = source / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, destination)
        artifacts = temp / 'artifacts'
        execute([sys.executable, '-m', 'build', '--no-isolation', '--outdir', artifacts], cwd=source)
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env.pop('FILEREPACK_TESTDATA_ROOT', None)
        for artifact in sorted(artifacts.iterdir()):
            environment = temp / ('env-' + ('wheel' if artifact.suffix == '.whl' else 'sdist'))
            venv.EnvBuilder(with_pip=False, symlinks=os.name != 'nt').create(environment)
            python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            execute([sys.executable, '-m', 'pip', '--python', python, 'install', '--no-deps', artifact], cwd=temp, env=env)
            location = execute([python, '-c', 'import frbench; print(frbench.__file__)'], cwd=temp, env=env).stdout.strip()
            if not Path(location).resolve().is_relative_to(environment.resolve()):
                raise RuntimeError('Artifact imported checkout code: ' + location)
            execute([python, '-m', 'frbench', 'check', '--root', ROOT], cwd=temp, env=env)
            missing = execute([python, '-m', 'frbench', 'check'], cwd=temp, env=env, expected=2)
            if '--root' not in missing.stderr:
                raise RuntimeError('Missing corpus diagnostic is not actionable')
            if artifact.suffix != '.whl':
                extracted = temp / 'extracted'
                extracted.mkdir()
                with tarfile.open(artifact) as archive:
                    for member in archive.getmembers():
                        path = Path(member.name)
                        if path.is_absolute() or '..' in path.parts or member.issym() or member.islnk():
                            raise RuntimeError('Unsafe distribution path')
                    if sys.version_info >= (3, 12):
                        archive.extractall(extracted, filter='data')
                    else:
                        archive.extractall(extracted)
                dataset = next(extracted.iterdir())
                execute([python, '-m', 'frbench', 'check', '--root', dataset], cwd=temp, env=env)
            results.append({'artifact': artifact.name, 'installed_import': 'isolated environment',
                            'explicit_corpus_check': 'passed', 'missing_corpus_diagnostic': 'passed'})
    report = {'python': sys.version.split()[0], 'checks': results}
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
