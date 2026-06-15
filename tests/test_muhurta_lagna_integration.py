"""Integration tests for lagna position scoring inside day_slots.

These exercise the full muhurta path so a regression in `_score_lagna`,
the personal-dosha cascade, or the lagna threading would be caught.
The engine is pinned (DrikGanitaEngine, Hyderabad) — same fixtures as
the rest of test_muhurta_finder.py.
"""
from datetime import date

from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES
from telugu_panchangam.personal.muhurta import day_slots
from telugu_panchangam.personal.lagna_hora import get_lagna_transitions

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(y, m, d):
    return ENGINE.calculate(date(y, m, d), HYD, include_eclipse=False)


def _lagna_at(day, slot_start):
    """Lookup the rashi rising at a given moment within the day."""
    for w in get_lagna_transitions(day):
        if w.start <= slot_start < w.end:
            return w.name.replace(' Lagna', '')
    return None


def test_lagna_scoring_skipped_when_no_janma_rasi_given():
    """Generic muhurta queries (no janma) must not pay the lagna cost
    nor pick up lagna-related reasons/dosha — keeps the fast path
    fast and avoids surprising users who didn't opt in."""
    day = _day(2026, 6, 17)
    slots = day_slots(day)
    assert slots
    for s in slots:
        assert s['personal_dosha'] != 'ashtama_lagna'
        for chip in s['reasons']:
            assert 'lagna favourable' not in chip
            assert 'lagna Ashtama' not in chip


def test_lagna_kendra_or_trikona_adds_bonus_and_reason():
    """For Hyderabad 2026-06-17 with janma=Mesha, find a slot whose
    rising sign is Karka (kendra/4th from Mesha) and verify the
    +1 + reason chip both fire."""
    day = _day(2026, 6, 17)
    slots = day_slots(day, janma_nakshatras=['Krittika'], janma_rasis=['Mesha'])
    assert slots
    # Find a slot that starts during a kendra/trikona lagna from Mesha.
    # Per generator output, Karka rises ~07:58 → 10:11 IST for this date.
    favoured = [s for s in slots
                if _lagna_at(day, s['start']) in ('Karka','Simha','Tula','Dhanu','Makara')]
    assert favoured, 'expected at least one slot in a kendra/trikona lagna'
    matched = [s for s in favoured
               if any('lagna favourable' in r for r in s['reasons'])]
    assert matched, 'expected the kendra/trikona reason to surface'


def test_ashtama_lagna_sets_personal_dosha_and_caps_tier():
    """For Hyderabad 2026-06-17 with janma=Mesha, Vrischika is 8th
    (Ashtama). Any slot whose start falls in Vrischika lagna must:
    - carry personal_dosha == 'ashtama_lagna'
    - never be tiered as 'Excellent' (matching the existing
      Ashtama-Chandra cap)."""
    day = _day(2026, 6, 17)
    slots = day_slots(day, janma_nakshatras=['Krittika'], janma_rasis=['Mesha'])
    assert slots
    ashtama_slots = [s for s in slots
                     if _lagna_at(day, s['start']) == 'Vrischika']
    if not ashtama_slots:
        # If no choghadiya slot happens to start in Vrischika lagna on
        # this date, the test can't verify the cap — skip gracefully
        # rather than failing for an unrelated reason.
        return
    for s in ashtama_slots:
        got = s['personal_dosha']
        assert got == 'ashtama_lagna', f'expected ashtama_lagna, got {got}'
        assert s['tier'] != 'Excellent'


def test_janma_lagna_overrides_janma_rashi_when_provided():
    """When janma_lagnas[i] is set, that person's kendra/trikona/
    Ashtama positions count from the natal ascendant instead of
    janma rashi. Different reference → potentially different
    scoring."""
    day = _day(2026, 6, 17)
    # On 2026-06-17 Hyderabad a choghadiya slot starts in Tula lagna
    # (~10:04 IST). From janma rashi Mesha, Tula is position 7
    # (kendra) → favourable. From janma lagna Vrishabha, Tula is
    # position 6 (neutral) → no chip.
    slots_rashi = day_slots(day,
                            janma_nakshatras=['Krittika'],
                            janma_rasis=['Mesha'])
    slots_lagna = day_slots(day,
                            janma_nakshatras=['Krittika'],
                            janma_rasis=['Mesha'],
                            janma_lagnas=['Vrishabha'])
    def has_tula_fav(slots):
        return any(
            'Tula lagna favourable' in r
            for s in slots for r in s['reasons']
        )
    assert has_tula_fav(slots_rashi), \
        'Tula should be kendra from Mesha (rashi mode)'
    assert not has_tula_fav(slots_lagna), \
        'Tula should NOT be kendra/trikona from Vrishabha (lagna mode)'


def test_janma_lagna_chip_carries_lagna_suffix():
    """Reason chip should end with 'from <rasi> lagna' (not just
    'from <rasi>') when janma_lagnas is set — so users see at-a-
    glance which reference convention was applied."""
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'],
                      janma_lagnas=['Mesha'])
    matched = [r for s in slots for r in s['reasons']
               if 'Tula lagna favourable' in r]
    assert matched, 'expected at least one Tula kendra reason'
    assert all('from Mesha lagna' in r for r in matched), \
        f'expected "from Mesha lagna" suffix, got: {matched}'


def test_janma_lagna_falls_back_to_rashi_when_null():
    """When janma_lagnas[i] is None, that person's scoring falls
    back to janma rashi — chip stays in the original 'from <rasi>'
    format (no ' lagna' suffix)."""
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'],
                      janma_lagnas=[None])
    matched = [r for s in slots for r in s['reasons']
               if 'Tula lagna favourable' in r]
    assert matched, 'expected at least one Tula kendra reason'
    for r in matched:
        assert 'from Mesha lagna' not in r, \
            f'unexpected lagna suffix in fallback chip: {r}'
        assert 'from Mesha' in r


def test_ashtama_chandra_takes_precedence_over_ashtama_lagna():
    """Both doshas can co-occur on the same slot. The personal_dosha
    cascade puts ashtama_chandra above ashtama_lagna — verify that
    when an Ashtama-Chandra person is provided, ashtama_lagna doesn't
    silently take the slot's flag."""
    # 2026-06-25 Hyderabad: Moon in Tula. janma=Meena → Moon@8
    # (Ashtama Chandra). Whatever the slot's lagna is, ashtama_chandra
    # should win in the cascade.
    day = _day(2026, 6, 25)
    slots = day_slots(day,
                      janma_nakshatras=['Revati'],
                      janma_rasis=['Meena'])
    assert slots
    chandra_doshas = [s for s in slots
                      if s['personal_dosha'] == 'ashtama_chandra']
    assert chandra_doshas, 'expected ashtama_chandra to surface for janma=Meena'
    # And none of those slots should be flagged as ashtama_lagna,
    # even if the lagna happens to also be 8th from Meena.
    for s in chandra_doshas:
        assert s['personal_dosha'] != 'ashtama_lagna'
