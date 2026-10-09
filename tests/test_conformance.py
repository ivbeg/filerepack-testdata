import pytest

from frbench.common import ROOT, read_manifest
from frbench.conformance import inventory, profile_key, qualify
from frbench.oracles import require


ENTRIES = inventory(ROOT)['profiles']
CASES = {case['id']: case for case in read_manifest(ROOT)['cases']}


def test_every_used_oracle_profile_has_a_conformance_entry():
    expected = {profile_key(case['oracle']) for case in CASES.values()
                if case['expectation'] == 'observe'}
    keys = [entry['profile'] for entry in ENTRIES]
    assert len(keys) == len(set(keys))
    assert set(keys) == expected
    assert all(profile_key(CASES[entry['case']]['oracle']) == entry['profile'] for entry in ENTRIES)


@pytest.mark.parametrize('entry', ENTRIES, ids=lambda e: e['profile'])
def test_corpus_profile_conformance(entry):
    case = CASES[entry['case']]
    missing = require(case['oracle'])
    if missing:
        pytest.skip('Missing independent verifier: ' + ', '.join(missing))
    result = qualify(entry, case, ROOT)
    assert result['status'] == 'passed'
