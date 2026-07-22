"""Regression tests for the LLM Rasi Phalalu verifier's graha-name
tolerance.

The 2026-07-20 daily run failed with:
    Verification failed: Mesha: unknown graha 'Sun' in transits_cited
The model had labelled Surya in English. That's a naming drift, not an
astronomy error, so _verify normalizes the label before the membership
check while still verifying position and verdict exactly.
"""
import pytest

from telugu_panchangam.personal.llm_phalalu import (
    LLM_PHALALU_PROVENANCE, _canonical_graha, _verify, _compute_all_rashis,
    VerificationError,
)
from telugu_panchangam.panchangam_names import RASHI_NAMES


def test_canonical_graha_maps_english_and_synonyms():
    assert _canonical_graha('Sun') == 'Surya'
    assert _canonical_graha('moon') == 'Chandra'
    assert _canonical_graha('MARS') == 'Kuja'
    assert _canonical_graha('Jupiter') == 'Guru'
    assert _canonical_graha('Saturn') == 'Shani'
    # Already-canonical names pass through.
    assert _canonical_graha('Surya') == 'Surya'
    assert _canonical_graha('Rahu') == 'Rahu'
    # Genuinely unknown names pass through unchanged (still caught by _verify).
    assert _canonical_graha('Nibiru') == 'Nibiru'


# A plausible sky: every graha placed in some rasi. Values need only be
# internally consistent for _compute_all_rashis to produce verdicts.
_SKY = {
    'Surya': 'Karka', 'Chandra': 'Simha', 'Kuja': 'Vrishabha',
    'Budha': 'Mithuna', 'Guru': 'Karka', 'Shukra': 'Simha',
    'Shani': 'Meena', 'Rahu': 'Kumbha', 'Ketu': 'Simha',
}


def _all_rashis():
    return _compute_all_rashis(_SKY)


def _base_items(all_rashis=None):
    """Minimal valid response with one engine-verifiable claim per rasi."""
    all_rashis = all_rashis or _all_rashis()
    items = []
    for rasi in RASHI_NAMES:
        surya = all_rashis[rasi]['verdicts']['Surya']
        items.append({
            'rasi': rasi,
            'text': 'Surya provides the principal transit theme.',
            'advice': 'Review the day calmly and keep expectations flexible.',
            'transits_cited': [{
                'graha': 'Surya',
                'position': surya['position'],
                'verdict': surya['verdict'],
            }],
        })
    return items


def test_verify_accepts_english_graha_label():
    all_rashis = _all_rashis()
    surya = all_rashis['Mesha']['verdicts']['Surya']
    items = _base_items(all_rashis)
    # Cite Surya under its English name, with the correct position/verdict.
    for it in items:
        if it['rasi'] == 'Mesha':
            it['transits_cited'] = [{
                'graha': 'Sun',
                'position': surya['position'],
                'verdict': surya['verdict'],
            }]
    _verify(items, all_rashis)  # must not raise


def test_verify_still_rejects_invented_graha():
    all_rashis = _all_rashis()
    items = _base_items(all_rashis)
    for it in items:
        if it['rasi'] == 'Mesha':
            it['transits_cited'] = [{'graha': 'Nibiru', 'position': 1, 'verdict': 'good'}]
    with pytest.raises(VerificationError, match="unknown graha 'Nibiru'"):
        _verify(items, all_rashis)


def test_verify_still_catches_position_mismatch_under_alias():
    all_rashis = _all_rashis()
    surya = all_rashis['Mesha']['verdicts']['Surya']
    wrong = (surya['position'] % 12) + 1
    items = _base_items(all_rashis)
    for it in items:
        if it['rasi'] == 'Mesha':
            it['transits_cited'] = [{
                'graha': 'Sun', 'position': wrong, 'verdict': surya['verdict'],
            }]
    with pytest.raises(VerificationError, match="position mismatch"):
        _verify(items, all_rashis)


def test_verify_rejects_duplicate_rasi_entries():
    all_rashis = _all_rashis()
    items = _base_items(all_rashis)
    items[-1] = dict(items[0])
    with pytest.raises(VerificationError, match='Duplicate rasi'):
        _verify(items, all_rashis)


def test_verify_rejects_empty_citation_laundering():
    all_rashis = _all_rashis()
    items = _base_items(all_rashis)
    items[0]['transits_cited'] = []
    with pytest.raises(VerificationError, match='no engine-verifiable transit'):
        _verify(items, all_rashis)


@pytest.mark.parametrize('value', [
    'Sign the contract before the afternoon.',
    'Postpone the decision for 48 hours.',
    'Seek medication based on this transit.',
    'Plan important work for the morning hours.',
    'Make a major investment while the transit is supportive.',
])
def test_verify_rejects_precise_or_high_stakes_guidance(value):
    all_rashis = _all_rashis()
    items = _base_items(all_rashis)
    items[0]['advice'] = value
    with pytest.raises(VerificationError, match='unsupported precise or high-stakes'):
        _verify(items, all_rashis)


def test_verify_requires_citations_to_be_named_in_the_prose():
    all_rashis = _all_rashis()
    items = _base_items(all_rashis)
    items[0]['text'] = 'A quiet and reflective day may unfold.'
    with pytest.raises(VerificationError, match='is not named in text'):
        _verify(items, all_rashis)


def test_llm_interpretation_has_a_distinct_provenance_claim():
    assert LLM_PHALALU_PROVENANCE == 'daily_horoscope.llm_interpretation'
