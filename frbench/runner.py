"""Isolated measurements, checkpoints, machine-readable results and Markdown reports."""
import csv
import importlib.metadata
import json
import os
import platform
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .common import ROOT, check_manifest, corpus_root, read_manifest, sha256, write_json

PROFILES = {
    'lossless': {'keep_meta': True, 'wmv_lossless': True},
    'ultra': {'keep_meta': True, 'wmv_lossless': True, 'ultra': True},
    'experimental': {'keep_meta': True, 'wmv_lossless': True, 'experimental_formats': True},
    'checkpoint-load-only': {'keep_meta': True, 'wmv_lossless': True,
                             'checkpoint_compatibility': 'load-only'},
    'dryrun': {'keep_meta': True, 'wmv_lossless': True, 'dryrun': True},
}
TOOLS = ['7zz', '7z', 'zip', 'rar', 'unrar', 'gzip', 'pigz', 'xz', 'bzip2', 'zstd',
         'brotli', 'lz4', 'lzip', 'lzop', 'compress', 'qpdf', 'gs', 'pdftoppm', 'pdftotext',
         'ffmpeg', 'ffprobe', 'flac', 'jpegoptim', 'jpegtran', 'optipng', 'pngcrush',
         'gifsicle', 'cwebp', 'dwebp', 'magick', 'convert', 'openssl', 'avifenc', 'avifdec', 'cjxl',
         'djxl', 'h5repack', 'nccopy', 'Rscript', 'filerepack-ole', 'mp3packer', 'optivorbis']


def git_info(path):
    def run(*args):
        out = subprocess.run(['git', '-C', str(path), *args], capture_output=True, text=True)
        return out.stdout.strip() if out.returncode == 0 else None
    return {'commit': run('rev-parse', 'HEAD'), 'dirty': bool(run('status', '--porcelain'))}


def source_identity(path):
    if not path:
        return None
    path = Path(path).resolve()
    source = path / 'filerepack'
    origin = path / '.frbench-source.json'
    pinned = json.loads(origin.read_text(encoding='utf-8')) if origin.is_file() else {}
    return {**git_info(path), **pinned, 'python_source_sha256': __import__('hashlib').sha256(
        json.dumps({str(p.relative_to(source)): sha256(p) for p in sorted(source.rglob('*.py'))}, sort_keys=True).encode()).hexdigest()}


def harness_identity():
    source = Path(__file__).resolve().parent
    files = {p.name: sha256(p) for p in sorted(source.glob('*.py'))}
    return {**git_info(ROOT), 'python_source_sha256': __import__('hashlib').sha256(
        json.dumps(files, sort_keys=True).encode()).hexdigest()}


def environment():
    packages = {}
    for package in ['filerepack', 'Pillow', 'pikepdf', 'numpy', 'pyarrow', 'h5py', 'netCDF4',
                    'tifffile', 'imagecodecs', 'astropy', 'duckdb', 'fonttools', 'olefile',
                    'torch', 'pyreadstat', 'zarr', 'zstandard', 'psutil', 'pypdf', 'onnx',
                    'lz4', 'brotli', 'fastavro', 'pydicom', 'pillow-heif']:
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    versions = {}
    for name in TOOLS:
        exe = shutil.which(name)
        versions[name] = {'available': bool(exe)}
        if exe:
            versions[name]['sha256'] = sha256(exe)
            flag = '-version' if name in ('ffmpeg', 'ffprobe') else '--version'
            try:
                process = subprocess.run([exe, flag], capture_output=True, text=True, errors='replace', stdin=subprocess.DEVNULL, timeout=4)
                lines = (process.stdout + process.stderr).splitlines()
                versions[name]['version'] = next((line.strip() for line in lines if line.strip()), '')[:250]
            except (OSError, subprocess.TimeoutExpired):
                versions[name]['version'] = 'unavailable'
    return {'platform': platform.system(), 'platform_release': platform.release(),
            'machine': platform.machine(), 'python': platform.python_version(),
            'cpu_count': os.cpu_count(), 'packages': packages, 'tools': versions,
            'tool_overrides': {key: {'name': Path(value).name, 'available': Path(value).is_file(),
                                    'sha256': sha256(value) if Path(value).is_file() else None}
                               for key, value in os.environ.items() if key.startswith('FILEREPACK_')}}


def terminate(process):
    if os.name == 'posix':
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=3)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    else:
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
    process.wait()


def measure(case, root, filerepack, options, timeout, log, keep_work=False,
            enforce_outcomes=False):
    with tempfile.TemporaryDirectory(prefix='frbench-') as temp:
        work = Path(temp)
        original = Path(root) / case['path']
        source = work / original.name
        if original.is_dir():
            shutil.copytree(original, source)
        else:
            shutil.copy2(original, source)
        request = work / 'request.json'
        response = work / 'response.json'
        write_json(request, {'case': case, 'source': str(source), 'filerepack': filerepack,
                             'options': options, 'enforce_outcomes': enforce_outcomes})
        env = dict(os.environ)
        env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
        env['PYTHONHASHSEED'] = '0'
        start = time.perf_counter()
        peak = None
        timed_out = False
        try:
            import psutil
        except ImportError:
            psutil = None
        with log.open('wb') as output:
            process = subprocess.Popen([sys.executable, '-m', 'frbench.worker', str(request),
                                        str(response)], stdout=output, stderr=subprocess.STDOUT,
                                       env=env, start_new_session=os.name == 'posix')
            while process.poll() is None:
                elapsed = time.perf_counter() - start
                if elapsed > timeout:
                    timed_out = True
                    terminate(process)
                    break
                if psutil:
                    try:
                        proc = psutil.Process(process.pid)
                        rss = proc.memory_info().rss
                        for child in proc.children(recursive=True):
                            try:
                                rss += child.memory_info().rss
                            except psutil.Error:
                                pass
                        peak = max(peak or 0, rss)
                    except psutil.Error:
                        pass
                time.sleep(0.05)
        wall = time.perf_counter() - start
        if timed_out or not response.exists():
            result = {'status': 'timeout' if timed_out else 'worker-failure',
                      'reason': 'Worker exceeded timeout' if timed_out else
                                'Worker exited without response; see log',
                      'seconds': None, 'input_bytes': case['inventory']['bytes'],
                      'output_bytes': case['inventory']['bytes']}
        else:
            result = json.loads(response.read_text())
        result.update(wall_seconds=wall, peak_tree_rss_bytes=peak,
                      log=str(log.relative_to(log.parents[1])))
        if keep_work and result['status'] in FAILURES:
            retained = log.parent.parent / 'failed-work' / log.stem
            shutil.copytree(work, retained)
        return result


FAILURES = {'preservation-failure', 'growth-failure', 'error', 'timeout', 'worker-failure',
            'corpus-failure', 'qualification-failure'}


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['id']].append(row)
    cases = []
    for case_id, attempts in groups.items():
        first = attempts[0]
        status_counts = Counter(r['status'] for r in attempts)
        status = next((r['status'] for r in attempts if r['status'] in FAILURES),
                      'improved' if 'improved' in status_counts else first['status'])
        sizes = [r['output_bytes'] for r in attempts]
        seconds = [r['seconds'] for r in attempts if r['seconds'] is not None]
        item = {k: first[k] for k in ('id', 'extension', 'family', 'scope', 'tier', 'input_bytes')}
        item.update(status=status, attempts=len(attempts), statuses=dict(status_counts),
                    output_bytes=int(statistics.median(sizes)),
                    savings_bytes=first['input_bytes'] - int(statistics.median(sizes)),
                    seconds_median=statistics.median(seconds) if seconds else None,
                    seconds_min=min(seconds) if seconds else None,
                    seconds_max=max(seconds) if seconds else None,
                    reason=next(r['reason'] for r in attempts if r['status'] == status))
        item['savings_pct'] = item['savings_bytes'] * 100 / item['input_bytes'] if item['input_bytes'] else 0
        cases.append(item)
    # Totals count one median observation per case, not all repeated copies.
    valid = [c for c in cases if c['status'] in ('improved', 'unchanged') and c['tier'] not in ('control', 'stress')]
    meaningful = [c for c in valid if c['scope'] not in ('container-only', 'alias')]
    def totals(items):
        before = sum(c['input_bytes'] for c in items)
        after = sum(c['output_bytes'] for c in items)
        return {'cases': len(items), 'input_bytes': before, 'output_bytes': after,
                'savings_pct': (before - after) * 100 / before if before else 0,
                'seconds': sum(c['seconds_median'] or 0 for c in items)}
    return {'cases': cases, 'status_counts': dict(Counter(c['status'] for c in cases)),
            'verified_totals': totals(valid), 'native_totals': totals(meaningful),
            'original_totals': totals([c for c in valid if c['scope'] == 'original']),
            'generated_totals': totals([c for c in meaningful if c['scope'] != 'original']),
            'stress_totals': totals([c for c in cases if c['tier'] == 'stress' and
                                    c['status'] in ('improved', 'unchanged')])}


def markdown(report):
    summary = report['summary']
    totals = summary['native_totals']
    lines = ['# filerepack benchmark', '',
             'Generated: ' + report['created_utc'], '',
             f"Profile: `{report['profile']}` · repeat: {report['repeat']} · selected cases: {len(summary['cases'])}", '',
             ('WARNING: filerepack source changed during this run; timings/outcomes do not describe one immutable implementation.'
              if report.get('source_changed_during_run') else 'Source snapshot remained stable during the run.'), '',
             'Status counts: ' + ', '.join(f'{k}={v}' for k, v in summary['status_counts'].items()), '',
             f"Native/syntax/original verified cases: {totals['cases']}; byte-weighted savings: "
             f"{totals['savings_pct']:.2f}% ({totals['input_bytes']:,} → {totals['output_bytes']:,} bytes).", '',
             'Container-only and alias fixtures are excluded from this aggregate. Controls and '
             'verification skips are excluded from savings. Unchanged is observable behavior, '
             'not evidence of a successful optimizer. Synthetic results are not workload-wide estimates.', '',
             '| Case | Scope | Status | Input | Output | Savings | Median seconds |',
             '|---|---|---|---:|---:|---:|---:|']
    for c in summary['cases']:
        seconds = f"{c['seconds_median']:.4f}" if c['seconds_median'] is not None else '—'
        lines.append(f"| {c['id']} | {c['scope']} | {c['status']} | {c['input_bytes']} | "
                     f"{c['output_bytes']} | {c['savings_pct']:.2f}% | {seconds} |")
    issues = [c for c in summary['cases'] if c['status'] not in ('improved', 'unchanged')]
    if issues:
        lines += ['', '## Failures and skips', '']
        lines += [f"- `{c['id']}`: {c['reason']}" for c in issues]
    lines += ['', 'See `report.json` for environment/tool versions, source identity, options, '
              'per-attempt times, sampled process-tree RSS, and logs. RSS sums can double-count '
              'shared pages and the 50 ms sampling can miss short peaks.', '']
    return '\n'.join(lines)


def run(args):
    root = Path(args.root).resolve()
    failures = check_manifest(root)
    if failures:
        raise ValueError('Corpus integrity failed: ' + '; '.join(failures[:10]))
    manifest = read_manifest(root)
    selected = [c for c in manifest['cases']
                if (not args.family or c['family'] in args.family.split(','))
                and (not args.ext or c['extension'] in args.ext.split(','))
                and (not args.case or any(x in c['id'] for x in args.case.split(',')))
                and (args.tier == 'all' or c['tier'] == args.tier)
                and (not args.native_only or c['scope'] not in ('container-only', 'alias'))]
    if not selected:
        raise ValueError('No cases selected')
    destination = Path(args.output).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    logs = destination / 'logs'
    logs.mkdir()
    options = {'quiet': True, 'debug': True, 'keep_if_larger': True,
               **PROFILES[args.profile]}
    options.update(json.loads(args.options))
    if options.get('lossy') or options.get('jpeg_quality') or options.get('png_quality') or options.get('pdf_profile'):
        raise ValueError('This suite uses exact lossless oracles; lossy options need quality oracles')
    rows = []
    source = str(Path(args.filerepack).resolve()) if args.filerepack else None
    metadata = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
                'profile': args.profile, 'repeat': args.repeat, 'warmup': args.warmup,
                'timeout': args.timeout, 'options': options, 'environment': environment(),
                'filerepack_source': source_identity(source), 'harness': harness_identity(),
                'corpus_manifest_sha256': sha256(root / 'corpus/manifest.json')}
    with (destination / 'attempts.jsonl').open('w') as journal:
        for index, case in enumerate(selected, 1):
            for attempt in range(-args.warmup, args.repeat):
                log = logs / f"{case['id']}-{attempt}.log"
                result = measure(case, root, source, options, args.timeout, log, args.keep_work,
                                 getattr(args, 'require_outcomes', False))
                row = {**{k: case[k] for k in ('id', 'extension', 'family', 'scope', 'tier')},
                       'attempt': attempt, **result}
                print(f"[{index}/{len(selected)}] {case['id']} #{attempt}: {result['status']}", flush=True)
                if attempt >= 0:
                    rows.append(row)
                    journal.write(json.dumps(row, ensure_ascii=False) + '\n')
                    journal.flush()
                write_json(destination / 'progress.json', {'completed_attempts': len(rows),
                                                           'selected_cases': len(selected)})
    after = check_manifest(root)
    if sha256(root / 'corpus/manifest.json') != metadata['corpus_manifest_sha256']:
        after.append('Corpus manifest changed during benchmark')
    if after:
        rows.append({'id': 'corpus-integrity', 'extension': '', 'family': 'suite',
                     'scope': 'control', 'tier': 'control', 'status': 'corpus-failure',
                     'reason': '; '.join(after), 'seconds': None, 'input_bytes': 0, 'output_bytes': 0})
    source_end = source_identity(source)
    harness_end = harness_identity()
    report = {**metadata, 'filerepack_source_end': source_end, 'harness_end': harness_end,
              'harness_changed_during_run': harness_end != metadata['harness'],
              'source_changed_during_run': source_end != metadata['filerepack_source'],
              'attempts': rows, 'summary': summarize(rows)}
    verified = sum(c['status'] in ('improved', 'unchanged')
                   for c in report['summary']['cases'])
    issues = []
    minimum = getattr(args, 'min_verified', 1)
    if report['harness_changed_during_run']:
        issues.append('Harness changed during benchmark')
    if verified < minimum:
        issues.append(f'Only {verified} cases independently verified; required {minimum}')
    if getattr(args, 'strict_verifiers', False):
        skipped = sorted({row['id'] for row in rows if row['status'] == 'skipped-verifier'})
        if skipped:
            issues.append('Missing verifiers: ' + ', '.join(skipped))
    report['qualification'] = {'verified_cases': verified, 'minimum_verified_cases': minimum,
                               'strict_verifiers': getattr(args, 'strict_verifiers', False),
                               'issues': issues}
    write_json(destination / 'report.json', report)
    (destination / 'report.md').write_text(markdown(report))
    cases = report['summary']['cases']
    with (destination / 'cases.csv').open('w', newline='') as stream:
        fields = ['id', 'extension', 'family', 'scope', 'tier', 'status', 'input_bytes',
                  'output_bytes', 'savings_bytes', 'savings_pct', 'seconds_median', 'reason']
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(cases)
    write_json(destination / 'coverage.json', coverage(root, source, cases))
    print('\n' + str(destination / 'report.md'))
    return 1 if issues or report['source_changed_during_run'] or any(c['status'] in FAILURES for c in cases) else 0


def coverage(root=None, source=None, results=None):
    from .catalog import discover_catalog
    root = corpus_root(root)
    manifest = read_manifest(root)
    catalog = json.loads((Path(root) / 'corpus/catalog.json').read_text())
    expected = set(manifest['supported_extensions'])
    drift = None
    if source:
        catalog = discover_catalog(source)
        live = set(catalog['supported_extensions'])
        drift = {'added': sorted(live - expected), 'removed': sorted(expected - live)}
        expected = live
    rows = []
    for ext in sorted(expected):
        cases = [c for c in manifest['cases'] if c['extension'] == ext and c['tier'] != 'control']
        measured = [c for c in (results or []) if c['extension'] == ext]
        scopes = sorted(set(c['scope'] for c in cases))
        rows.append({'extension': ext, 'cases': len(cases), 'scopes': scopes,
                     'native_or_original': any(s in ('native', 'original') for s in scopes),
                     'measured_statuses': dict(Counter(c['status'] for c in measured))})
    missing = [r['extension'] for r in rows if not r['cases']]
    mapping = catalog.get('handler_by_extension', {})
    handler_rows = []
    for handler in sorted(set(mapping.values())):
        extensions = sorted(ext for ext, value in mapping.items() if value == handler)
        fixtures = [c for c in manifest['cases'] if c['extension'] in extensions and c['tier'] != 'control']
        handler_rows.append({'handler': handler, 'extensions': extensions,
                             'cases': len(fixtures),
                             'native_original_or_syntax': any(c['scope'] in ('native', 'original', 'syntax') for c in fixtures)})
    positive = [case for case in manifest['cases'] if case['tier'] != 'control']
    route_suffixes = catalog.get('filename_suffixes') or [
        *(('tar.' + codec) for codec in
          ['gz', 'xz', 'bz2', 'zst', 'br', 'lz4', 'lz', 'lzma', 'lzo', 'z']),
        'warc.gz',
        *(f'{ext}.{codec}' for ext in ['rds', 'rda', 'rdata']
          for codec in ['gz', 'bz2', 'xz']),
        'cpio',
        'cpio.bz2',
        'otf',
    ]
    filename_routes = []
    for suffix in route_suffixes:
        if suffix == 'otf':
            matching = [case for case in positive if case['extension'] == 'otf']
            route = '.otf (ODF package detected by ZIP content)'
        else:
            matching = [case for case in positive
                        if Path(case['path']).name.lower().endswith('.' + suffix)]
            route = '.' + suffix
        filename_routes.append({'route': route, 'cases': [case['id'] for case in matching],
                                'covered': bool(matching)})
    missing_handlers = [h['handler'] for h in handler_rows if not h['cases']]
    unmapped = [ext for ext, handler in mapping.items() if handler.startswith('unmapped:')]
    return {'handlers': handler_rows, 'handler_count': len(handler_rows),
            'handlers_covered': sum(bool(h['cases']) for h in handler_rows),
            'missing_handlers': missing_handlers, 'unmapped_extensions': sorted(unmapped),
            'registry_identity': catalog.get('implementation'),
            'supported': len(expected), 'covered': len(expected) - len(missing),
            'native_or_original': sum(r['native_or_original'] for r in rows),
            'missing': missing, 'drift': drift, 'extensions': rows,
            'filename_routes': filename_routes,
            'filename_routes_covered': sum(route['covered'] for route in filename_routes),
            'generation_gaps': manifest.get('generation_gaps', []),
            'stores': [c['id'] for c in manifest['cases'] if c['extension'] == 'zarr']}


def compare(before, after):
    a = json.loads(Path(before).read_text())
    b = json.loads(Path(after).read_text())
    comparable = (a['corpus_manifest_sha256'] == b['corpus_manifest_sha256'] and
                  a['options'] == b['options'])
    left = {c['id']: c for c in a['summary']['cases']}
    right = {c['id']: c for c in b['summary']['cases']}
    changes = []
    for name in sorted(left.keys() & right.keys()):
        x, y = left[name], right[name]
        changes.append({'id': name, 'status_before': x['status'], 'status_after': y['status'],
                        'output_delta_bytes': y['output_bytes'] - x['output_bytes'],
                        'seconds_delta': (y['seconds_median'] - x['seconds_median']
                                          if y['seconds_median'] is not None and x['seconds_median'] is not None
                                          else None)})
    incompatibilities = []
    for field in ('corpus_manifest_sha256', 'options', 'environment', 'harness', 'profile',
                  'repeat', 'warmup', 'timeout'):
        if a.get(field) is None or b.get(field) is None:
            incompatibilities.append(field + ': identity unavailable')
        elif (a[field].get('python_source_sha256') != b[field].get('python_source_sha256')
              if field == 'harness' else a[field] != b[field]):
            incompatibilities.append(field + ': differs')
    if left.keys() != right.keys():
        incompatibilities.append('selected cases: differ')
    if any(report.get('source_changed_during_run') or report.get('harness_changed_during_run')
           for report in (a, b)):
        incompatibilities.append('source or harness changed during a run')
    return {'comparable': not incompatibilities, 'incompatibilities': incompatibilities,
            'comparable_corpus_and_options': comparable,
            'same_environment': a['environment'] == b['environment'],
            'added_cases': sorted(right.keys() - left.keys()),
            'removed_cases': sorted(left.keys() - right.keys()), 'changes': changes}
