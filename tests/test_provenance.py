"""Trust-contract tests for the astrological provenance ledger."""
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
LEDGER_PATH = ROOT / 'docs' / 'reference' / 'provenance.json'
FESTIVAL_FIXTURE = ROOT / 'tests' / 'fixtures' / 'forward_year_festivals.json'


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def test_provenance_claims_have_valid_unique_ids_and_sources():
    ledger = _load(LEDGER_PATH)
    source_ids = {source['id'] for source in ledger['sources']}
    claim_ids = [claim['id'] for claim in ledger['claims']]

    assert len(source_ids) == len(ledger['sources'])
    assert len(claim_ids) == len(set(claim_ids))
    for claim in ledger['claims']:
        assert claim['evidence_class'] in ledger['evidence_classes']
        assert claim['verification_state'] in ledger['verification_states']
        assert set(claim['source_ids']) <= source_ids
        assert (ROOT / claim['implementation']).exists()
        assert claim['scope'].strip()


def test_verified_textual_claims_require_precise_locators():
    ledger = _load(LEDGER_PATH)
    for claim in ledger['claims']:
        if (claim['evidence_class'] == 'textual'
                and claim['verification_state'] == 'verified'):
            assert claim['source_ids']
            assert claim['locator'] and claim['locator'].strip()


def test_forward_festival_fixture_discloses_verification_per_cell():
    fixture = _load(FESTIVAL_FIXTURE)
    statuses = [cell['verification']['status'] for cell in fixture['cells']]

    assert len(statuses) == 30
    assert statuses.count('DP_VERIFIED') == 1
    assert statuses.count('ENGINE_PINNED') == 29
    assert 'DP-verified festival regression' not in fixture['purpose']
