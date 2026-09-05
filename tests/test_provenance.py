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


def test_contradicted_claims_require_inspected_evidence():
    ledger = _load(LEDGER_PATH)
    for claim in ledger['claims']:
        if claim['verification_state'] != 'contradicted':
            continue
        assert claim['evidence_class'] == 'textual'
        assert claim['source_ids']
        assert claim['locator'] and claim['locator'].strip()
        assert claim.get('last_reviewed')


def test_abhijit_method_has_a_direct_scoped_published_reference():
    ledger = _load(LEDGER_PATH)
    sources = {source['id']: source for source in ledger['sources']}
    claims = {claim['id']: claim for claim in ledger['claims']}

    claim = claims['panchangam.abhijit_muhurta_method']
    assert claim['evidence_class'] == 'published_panchangam'
    assert claim['verification_state'] == 'partially_verified'
    assert claim['source_ids'] == ['DP-ABHIJIT-MUHURAT']
    assert '15 equal sunrise-to-sunset parts' in claim['locator']
    assert 'Wednesday exclusion' in claim['locator']
    assert sources['DP-ABHIJIT-MUHURAT']['url'].endswith(
        '/muhurat/daily/abhijit-muhurat.html')


def test_forward_festival_fixture_discloses_verification_per_cell():
    fixture = _load(FESTIVAL_FIXTURE)
    statuses = [cell['verification']['status'] for cell in fixture['cells']]

    assert len(statuses) == 30
    assert statuses.count('DP_VERIFIED') == 1
    assert statuses.count('ENGINE_PINNED') == 29
    assert 'DP-verified festival regression' not in fixture['purpose']
