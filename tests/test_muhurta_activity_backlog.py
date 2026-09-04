"""The Muhurtam expansion backlog must remain source-resolvable and explicit."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]


def _load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def test_activity_backlog_has_unique_keys_and_resolvable_sources():
    backlog = _load('docs/reference/muhurta-activity-backlog.json')
    ledger = _load('docs/reference/provenance.json')
    source_ids = {source['id'] for source in ledger['sources']}
    items = backlog['items']
    keys = [item['key'] for item in items]

    assert backlog['schema_version'] == 1
    assert len(keys) == len(set(keys))
    assert {'priority', 'disposition', 'reason', 'boundary'} <= set(items[0])
    for item in items:
        assert item['source_candidates']
        for candidate in item['source_candidates']:
            assert candidate['source_id'] in source_ids
            assert candidate['locator'].strip()


def test_pdf_locators_name_an_inspected_artifact_not_the_uninspected_work():
    backlog = _load('docs/reference/muhurta-activity-backlog.json')
    ledger = _load('docs/reference/provenance.json')
    sources = {source['id']: source for source in ledger['sources']}

    for item in backlog['items']:
        for candidate in item['source_candidates']:
            locator = candidate['locator']
            if 'physical PDF p' not in locator:
                continue
            source = sources[candidate['source_id']]
            assert source.get('inspected_directly') is True
            assert candidate['source_id'] == 'BVR-MUHURTHA-CHISTABO-2020'


def test_backlog_distinguishes_existing_remediation_from_new_keys():
    backlog = _load('docs/reference/muhurta-activity-backlog.json')
    by_key = {item['key']: item for item in backlog['items']}

    assert by_key['gruhapravesha']['disposition'] == 'implemented_verified'
    assert 'gruhapravesha' in ACTIVITY_RULES
    for key, item in by_key.items():
        if item['disposition'] in {'existing_conflict', 'implemented_verified'}:
            assert key in ACTIVITY_RULES
            continue
        assert key not in ACTIVITY_RULES


def test_priority_zero_backlog_matches_documented_first_wave():
    backlog = _load('docs/reference/muhurta-activity-backlog.json')
    p0 = [item['key'] for item in backlog['items'] if item['priority'] == 'P0']
    assert p0 == ['gruhapravesha', 'seemantha', 'house_purchase', 'home_repair']
