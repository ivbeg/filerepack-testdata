"""One fresh filerepack operation and independent verification per process."""
import dataclasses
import json
import os
import sys
import time
from pathlib import Path

from .common import file_inventory, write_json
from .oracles import fingerprint, require


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    response = Path(sys.argv[2])
    case, source = request['case'], Path(request['source'])
    result = {'status': 'error', 'reason': '', 'seconds': 0.0,
              'input_bytes': file_inventory(source)['bytes'], 'output_bytes': file_inventory(source)['bytes']}
    phase = 'input-verification'
    try:
        missing = require(case['oracle'])
        if missing and case['expectation'] != 'unchanged':
            result.update(status='skipped-verifier', reason='Missing oracle: ' + ', '.join(missing))
            write_json(response, result)
            return
        before_bytes = file_inventory(source)
        expected = (before_bytes if case['expectation'] == 'unchanged'
                    else fingerprint(source, case['oracle']))
        if request.get('filerepack'):
            sys.path.insert(0, request['filerepack'])
            # Native format workers inherit this module search path.
            os.environ['PYTHONPATH'] = request['filerepack'] + os.pathsep + os.environ.get('PYTHONPATH', '')
        from filerepack import FileRepacker, RepackOptions, __version__
        from filerepack.formats import identify_filename
        result['filerepack_version'] = __version__
        options = RepackOptions(**request['options'])
        phase = 'repack'
        start = time.perf_counter()
        if source.is_dir():
            from filerepack import repack_store
            output_dir = source.parent / 'optimized'
            operation = repack_store(str(source), str(output_dir), options=options)
            output = output_dir / source.name
            if not output.exists():
                output = source
        else:
            kind = identify_filename(source.name, peek_path=str(source))
            result['detected'] = dataclasses.asdict(kind) if kind else None
            operation = FileRepacker().repack(str(source), options=options)
            output = Path(operation.filepath)
            if not output.exists():
                raise ValueError('Reported output does not exist: ' + output.name)
        result['seconds'] = time.perf_counter() - start
        result['output_bytes'] = file_inventory(output)['bytes']
        if hasattr(operation, 'results'):
            result['packer_results'] = [
                {'replaced': r.replaced, 'reason': r.reason, 'details': r.details}
                for r in operation.results]
        else:
            result['packer_results'] = [{'replaced': operation.replaced,
                                         'reason': operation.reason, 'details': operation.details}]
        phase = 'output-verification'
        actual = (file_inventory(output) if case['expectation'] == 'unchanged'
                  else fingerprint(output, case['oracle']))
        if expected != actual:
            result.update(status='preservation-failure', reason='Independent decoded-content comparison differs')
        elif result['output_bytes'] > result['input_bytes']:
            result.update(status='growth-failure', reason='Output grew under no-growth policy')
        elif request['options'].get('dryrun') and file_inventory(source) != before_bytes:
            result.update(status='preservation-failure', reason='Dry run changed source')
        elif case['expectation'] == 'unchanged' and file_inventory(source) != before_bytes:
            result.update(status='preservation-failure', reason='Rejection control was modified')
        elif result['output_bytes'] < result['input_bytes']:
            result.update(status='improved', reason='Verified smaller output')
        else:
            reasons = [r['reason'] for r in result['packer_results'] if r['reason']]
            result.update(status='unchanged', reason='; '.join(reasons) or
                          'No accepted candidate (inspect log/tool inventory for cause)')
        result['verification'] = 'byte-identity' if case['expectation'] == 'unchanged' else case['oracle']['kind']
    except Exception as exc:
        result.update(status='error', phase=phase, reason=type(exc).__name__ + ': ' + str(exc))
    write_json(response, result)


if __name__ == '__main__':
    main()
