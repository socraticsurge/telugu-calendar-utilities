"""Daily-horoscope authority layers must not inherit one another's status."""
import json
from pathlib import Path

from telugu_panchangam.gochara.rules import GOCHARA_PROVENANCE


ROOT = Path(__file__).parents[1]


def _claims():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return {claim['id']: claim for claim in ledger['claims']}


def test_favourable_houses_have_exact_primary_text_locator():
    claim = _claims()[GOCHARA_PROVENANCE['favourable_houses']]
    assert claim['surface'] == 'daily_horoscope'
    assert claim['evidence_class'] == 'textual'
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['BS-IYER-1884']
    assert 'Chapter CIV (104), stanza 4' in claim['locator']


def test_adjacent_gochara_layers_remain_explicit_evidence_debt():
    claims = _claims()
    for layer in ('vedha', 'nodes', 'named_conditions'):
        claim = claims[GOCHARA_PROVENANCE[layer]]
        assert claim['surface'] == 'daily_horoscope'
        assert claim['verification_state'] == 'needs_locator'
        assert claim['locator'] is None


def test_user_copy_does_not_launder_brihat_samhita_authority():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    pypi = (ROOT / 'README_PYPI.md').read_text(encoding='utf-8')
    assert 'Verdicts follow the classical Brihat Samhita gochara tables' not in html
    assert 'per classical Brihat Samhita tables' not in pypi
    assert 'exact source locators remain under review' in html
    assert 'open locator debt' in pypi
