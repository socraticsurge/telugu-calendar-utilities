"""Daily-horoscope authority layers must not inherit one another's status."""
import json
from pathlib import Path

from telugu_panchangam.gochara.rules import GOCHARA_PROVENANCE
from telugu_panchangam.personal.llm_phalalu import LLM_PHALALU_PROVENANCE


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


def test_vedha_has_exact_primary_text_locators():
    claim = _claims()[GOCHARA_PROVENANCE['vedha']]
    assert claim['surface'] == 'daily_horoscope'
    assert claim['evidence_class'] == 'textual'
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['PD-SASTRI-1942', 'JP-SASTRI-1932-V3']
    assert 'Adhyaya XXVI, slokas 3-8' in claim['locator']
    assert 'printed pp. 833-834' in claim['locator']


def test_node_house_conflict_is_explicit_and_scoped():
    claim = _claims()[GOCHARA_PROVENANCE['nodes']]
    assert claim['surface'] == 'daily_horoscope'
    assert claim['evidence_class'] == 'textual'
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['PD-SASTRI-1942']
    assert 'Adhyaya XXVI, sloka 2' in claim['locator']
    assert '10th' in claim['scope']
    assert 'no-Vedha policy remains unverified' in claim['scope']


def test_named_conditions_separate_house_evidence_from_product_labels():
    claim = _claims()[GOCHARA_PROVENANCE['named_conditions']]
    assert claim['surface'] == 'daily_horoscope'
    assert claim['verification_state'] == 'partially_verified'
    assert claim['source_ids'] == ['PD-SASTRI-1942']
    assert 'sloka 1' in claim['locator']
    assert 'slokas 22-23' in claim['locator']
    assert 'natal Moon' in claim['scope']
    assert 'rising, peak and setting phase labels' in claim['scope']


def test_user_copy_does_not_launder_brihat_samhita_authority():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    pypi = (ROOT / 'README_PYPI.md').read_text(encoding='utf-8')
    assert 'Verdicts follow the classical Brihat Samhita gochara tables' not in html
    assert 'per classical Brihat Samhita tables' not in pypi
    assert 'Phaladeepika 26.3–8 supplies' in html
    assert 'Known source conflict:' in html
    assert 'Phaladeepika 26.2 treats both like Surya' in html
    assert 'never calculated from lagna' in html
    assert 'conventional product presentation' in pypi


def test_browser_named_shani_conditions_use_only_the_moon_reference():
    frontend = (ROOT / 'src/panels/gochara.ts').read_text(encoding='utf-8')
    assert 'shaniConditionFromMoonHouse(houseFrom(shaniIdx, jr))' in frontend
    assert 'shaniConditionFromMoonHouse(houseFromRef(shaniIdx, jr))' in frontend
    assert 'shaniConditionFromMoonHouse(houseFrom(shaniIdx, jl))' not in frontend
    assert 'shaniConditionFromMoonHouse(houseFromRef(shaniIdx, jl))' not in frontend


def test_llm_prose_cannot_inherit_transit_authority():
    claim = _claims()[LLM_PHALALU_PROVENANCE]
    assert claim['surface'] == 'daily_horoscope'
    assert claim['evidence_class'] == 'project_heuristic'
    assert claim['verification_state'] == 'heuristic'
    assert claim['source_ids'] == []
    assert claim['locator'] is None
    assert 'not semantically or scripturally verified' in claim['scope']

    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    frontend = (ROOT / 'src/panels/gochara.ts').read_text(encoding='utf-8')
    assert 'do not inherit the scriptural authority' in html
    assert 'prose and guidance are interpretive' in frontend
