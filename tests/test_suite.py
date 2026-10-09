import json
import zipfile

import pytest

from frbench.common import check_manifest, file_inventory, read_manifest, write_json
from frbench.generate import Builder, compress, zip_bytes
from frbench.oracles import bytes_state, fingerprint, json_tokens, sqlite_state, xml_tree
from frbench.runner import measure, summarize


def test_json_oracle_retains_duplicate_keys_numeric_tokens_and_escapes():
    before = b' { "n": 1E+99999, "n": -0, "s": "keep  \\u0061" } '
    after = b'{"n":1E+99999,"n":-0,"s":"keep  \\u0061"}'
    assert json_tokens(before) == json_tokens(after)
    assert json_tokens(before) != json_tokens(after.replace(b'-0', b'0'))
    assert json_tokens(before) != json_tokens(after.replace(b'\\u0061', b'a'))


def test_jsonl_oracle_preserves_record_boundaries_and_line_endings():
    oracle = {'kind': 'jsonl'}
    assert bytes_state(b' {"a": 1} \r\n2', oracle) == bytes_state(b'{"a":1}\r\n2', oracle)
    assert bytes_state(b'1\r\n2', oracle) != bytes_state(b'1\n2', oracle)


def test_xml_oracle_keeps_text_comments_namespaces_and_doctype():
    assert xml_tree(b'<a  x = "1"><b>  keep </b><!-- comment --></a>') == xml_tree(
        b'<a x="1"><b>  keep </b><!-- comment --></a>')
    assert xml_tree(b'<a> x </a>') != xml_tree(b'<a>x</a>')
    assert xml_tree(b'<a><!--x--></a>') != xml_tree(b'<a/>')
    assert xml_tree(b'<a xmlns="one"/>') != xml_tree(b'<a xmlns="two"/>')


@pytest.mark.parametrize('codec', ['gz', 'bz2', 'xz', 'lzma'])
def test_stream_decoding_independent_of_compression_level(codec):
    content = b'synthetic-data' * 1000
    oracle = {'kind': 'stream', 'codec': codec}
    assert bytes_state(compress(content, codec, 1), oracle) == bytes_state(compress(content, codec, 9), oracle)


def test_archive_detects_member_removal_and_nested_content_corruption(tmp_path):
    config = {'kind': 'zip', 'children': {'data.json': {'kind': 'json'}}}
    a, b = tmp_path / 'a.zip', tmp_path / 'b.zip'
    a.write_bytes(zip_bytes({'data.json': b' { "n": 1 } ', 'empty/': b'', 'raw.bin': b'exact'}))
    b.write_bytes(zip_bytes({'data.json': b'{"n":1}', 'empty/': b'', 'raw.bin': b'exact'}, level=9))
    assert fingerprint(a, config) == fingerprint(b, config)
    b.write_bytes(zip_bytes({'data.json': b'{"n":2}', 'raw.bin': b'exact'}))
    assert fingerprint(a, config) != fingerprint(b, config)


def test_npz_oracle_uses_numpy_reader_without_unpickling(tmp_path):
    np = pytest.importorskip('numpy')
    source, candidate, corrupted = (tmp_path / name for name in
                                    ('source.npz', 'candidate.npz', 'corrupted.npz'))
    values = np.array([0.0, -0.0, np.nan, 2.5], dtype='<f8')
    labels = np.arange(4, dtype='<i2')
    np.savez(source, values=values, labels=labels)

    with zipfile.ZipFile(source) as archive:
        entries = {info.filename: archive.read(info) for info in archive.infolist()}
    candidate.write_bytes(zip_bytes(entries, level=9))

    oracle = {'kind': 'npz'}
    expected = fingerprint(source, oracle)
    assert expected == fingerprint(candidate, oracle)

    changed = values.copy()
    changed[-1] = 3.5
    np.savez(corrupted, values=changed, labels=labels)
    assert expected != fingerprint(corrupted, oracle)

    objects = tmp_path / 'objects.npz'
    np.savez(objects, values=np.array([{'safe': 'not loaded'}], dtype=object))
    with pytest.raises(ValueError, match='Object arrays'):
        fingerprint(objects, oracle)


def test_epub_oracle_enforces_stored_first_mimetype(tmp_path):
    path = tmp_path / 'book.epub'
    path.write_bytes(zip_bytes({'other': b'1', 'mimetype': b'application/epub+zip'}))
    with pytest.raises(ValueError, match='first'):
        fingerprint(path, {'kind': 'zip', 'stored_first': ['mimetype']})


def test_sqlite_oracle_includes_implicit_rowids_and_application_metadata(tmp_path):
    import sqlite3
    path = tmp_path / 'db.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE data(value TEXT)')
        db.execute("INSERT INTO data(rowid,value) VALUES (99,'same')")
    before = sqlite_state(path)
    with sqlite3.connect(path) as db:
        db.execute('UPDATE data SET rowid=1')
    assert sqlite_state(path) != before


def manifest_for(tmp_path):
    path = tmp_path / 'corpus/data.json'
    path.parent.mkdir()
    path.write_bytes(b' { "x": 1 } ')
    case = {'id': 'json', 'path': 'corpus/data.json', 'extension': 'json', 'family': 'text',
            'scope': 'native', 'tier': 'smoke', 'expectation': 'observe', 'oracle': {'kind': 'json'},
            'license': 'BSD-3-Clause', 'provenance': {'type': 'generated'},
            'inventory': file_inventory(path)}
    write_json(tmp_path / 'corpus/manifest.json', {'schema_version': 1, 'cases': [case],
                                               'supported_extensions': ['json']})
    return case


def test_checksum_mismatch_is_detected(tmp_path):
    manifest_for(tmp_path)
    assert not check_manifest(tmp_path)
    (tmp_path / 'corpus/data.json').write_bytes(b'changed')
    assert check_manifest(tmp_path)


def test_manifest_rejects_traversal_and_duplicate_ids(tmp_path):
    case = manifest_for(tmp_path)
    doc = json.loads((tmp_path / 'corpus/manifest.json').read_text())
    doc['cases'][0]['path'] = '../escaped'
    write_json(tmp_path / 'corpus/manifest.json', doc)
    with pytest.raises(ValueError, match='escapes'):
        read_manifest(tmp_path)
    doc['cases'] = [case, case]
    write_json(tmp_path / 'corpus/manifest.json', doc)
    with pytest.raises(ValueError, match='Duplicate'):
        read_manifest(tmp_path)


def test_summaries_exclude_controls_aliases_failed_and_skipped_from_native_savings():
    def row(name, status, scope='native', tier='extended', output=50, seconds=1):
        return {'id': name, 'status': status, 'extension': 'json', 'family': 'text',
                'scope': scope, 'tier': tier, 'input_bytes': 100, 'output_bytes': output,
                'seconds': seconds, 'reason': status}
    rows = [row('a', 'improved', seconds=1), row('a', 'improved', seconds=3),
            row('b', 'improved', scope='container-only'), row('c', 'unchanged', tier='control', output=100),
            row('d', 'error', output=0), row('e', 'skipped-verifier')]
    result = summarize(rows)
    assert result['native_totals']['cases'] == 1
    assert result['native_totals']['savings_pct'] == 50
    assert result['native_totals']['seconds'] == 2
    assert result['verified_totals']['cases'] == 2


def fake_repacker(tmp_path, expression):
    package = tmp_path / 'implementation/filerepack'
    package.mkdir(parents=True)
    (package / '__init__.py').write_text('''
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
__version__ = 'test'
class RepackOptions:
    def __init__(self, **kwargs): pass
class FileRepacker:
    def repack(self, filename, **kwargs):
        path = Path(filename)
''' + '        ' + expression + '\n' + '''        return SimpleNamespace(filepath=filename, results=[])
''')
    (package / 'formats.py').write_text('def identify_filename(*a, **k): return None\n')
    return str(package.parent)


@pytest.mark.parametrize(('action', 'expected'), [
    ("path.write_bytes(b'{\"x\":1}')", 'improved'),
    ("path.write_bytes(b'{\"x\":2}')", 'preservation-failure'),
    ('pass', 'unchanged'),
])
def test_isolation_and_real_worker_failure_detection(tmp_path, action, expected):
    case = manifest_for(tmp_path)
    original = (tmp_path / case['path']).read_bytes()
    implementation = fake_repacker(tmp_path, action)
    logs = tmp_path / 'results/logs'
    logs.mkdir(parents=True)
    result = measure(case, tmp_path, implementation, {}, 20, logs / 'case.log')
    assert result['status'] == expected
    assert (tmp_path / case['path']).read_bytes() == original


def test_timeout_terminates_worker(tmp_path):
    case = manifest_for(tmp_path)
    implementation = fake_repacker(tmp_path, '__import__("time").sleep(10)')
    logs = tmp_path / 'results/logs'
    logs.mkdir(parents=True)
    result = measure(case, tmp_path, implementation, {}, 1, logs / 'case.log')
    assert result['status'] == 'timeout'
    assert result['wall_seconds'] < 5


def test_builder_records_failed_optional_generators_without_partial_cases(tmp_path):
    builder = Builder(tmp_path, {})
    def failing():
        builder.add('partial.json', b'{}', 'json', 'text', {'kind': 'json'})
        raise RuntimeError('missing backend')
    builder.optional('fixture', failing)
    assert not builder.cases
    assert builder.gaps[0]['generator'] == 'fixture'


def test_inventory_rejects_missing_paths_and_symlinks(tmp_path):
    with pytest.raises(FileNotFoundError):
        file_inventory(tmp_path / 'missing')
    data = tmp_path / 'file'
    data.write_bytes(b'kept')
    link = tmp_path / 'symlink'
    try:
        link.symlink_to(data)
    except OSError:
        pytest.skip('Creating symlinks unavailable on this platform')
    with pytest.raises(ValueError, match='Symlink'):
        file_inventory(tmp_path)


def test_manifest_rejects_case_id_path_traversal(tmp_path):
    manifest_for(tmp_path)
    path = tmp_path / 'corpus/manifest.json'
    data = json.loads(path.read_text())
    data['cases'][0]['id'] = '../bad'
    write_json(path, data)
    with pytest.raises(ValueError, match='Unsafe case ID'):
        read_manifest(tmp_path)


def test_report_comparison_leaves_unmeasured_time_unknown(tmp_path):
    from frbench.runner import compare
    before = {'corpus_manifest_sha256': 'a', 'options': {}, 'environment': {},
              'summary': {'cases': [{'id': 'a', 'status': 'error', 'output_bytes': 1,
                                    'seconds_median': None}]}}
    after = json.loads(json.dumps(before))
    after['summary']['cases'][0].update(status='improved', seconds_median=0.5)
    write_json(tmp_path / 'a.json', before)
    write_json(tmp_path / 'b.json', after)
    assert compare(tmp_path / 'a.json', tmp_path / 'b.json')['changes'][0]['seconds_delta'] is None
