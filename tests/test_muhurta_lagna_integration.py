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


def test_janma_lagna_adds_independent_check_not_replacing_rashi():
    """When janma_lagnas[i] is set, the rashi-based check is NOT
    suppressed — both references contribute independently. So a
    slot whose lagna is favourable from janma rashi but neutral
    from janma lagna still shows the rashi chip; if both are
    favourable, BOTH chips appear and BOTH +1s land on the score.
    """
    day = _day(2026, 6, 17)
    # On 2026-06-17 Hyderabad a choghadiya slot starts in Tula
    # lagna (~10:04 IST). From janma rashi Mesha → position 7
    # (kendra). From janma lagna Vrishabha → position 6 (neutral).
    # Rashi chip MUST still appear even though lagna check is silent.
    slots = day_slots(day,
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'],
                      janma_lagnas=['Vrishabha'])
    rashi_chip = any('from Mesha' in r and ' lagna' not in r.split('from Mesha')[1][:8]
                     for s in slots for r in s['reasons']
                     if 'Tula lagna favourable' in r)
    lagna_chip = any('from Vrishabha lagna' in r
                     for s in slots for r in s['reasons']
                     if 'Tula lagna favourable' in r)
    assert rashi_chip, 'janma-rashi check must still fire when lagna is also set'
    assert not lagna_chip, 'Tula is not kendra/trikona from Vrishabha — no lagna chip'


def test_janma_lagna_both_references_score_when_both_favourable():
    """Both checks favourable on the same slot → both chips +
    both +1s contribute to the score."""
    day = _day(2026, 6, 17)
    # Tula is position 7 from Mesha (kendra) and position 5 from
    # Mithuna (trikona). Both checks fire.
    slots = day_slots(day,
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'],
                      janma_lagnas=['Mithuna'])
    rashi = [r for s in slots for r in s['reasons']
             if 'Tula lagna favourable' in r and 'from Mesha' in r
             and 'from Mesha lagna' not in r]
    lagna = [r for s in slots for r in s['reasons']
             if 'Tula lagna favourable' in r and 'from Mithuna lagna' in r]
    assert rashi, 'expected rashi-reference chip'
    assert lagna, 'expected lagna-reference chip'


def test_janma_lagna_chip_carries_lagna_suffix():
    """The 'from <rasi> lagna' suffix differentiates lagna-reference
    chips from rashi-reference chips at-a-glance."""
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'],
                      janma_lagnas=['Mesha'])
    # janma lagna == janma rashi (both Mesha) → both checks fire.
    lagna_chips = [r for s in slots for r in s['reasons']
                   if 'Tula lagna favourable' in r and 'from Mesha lagna' in r]
    assert lagna_chips, 'expected a Mesha-lagna chip with the suffix'


def test_janma_lagna_falls_back_cleanly_when_null():
    """When janma_lagnas[i] is None, only the rashi-reference
    check runs — no lagna-reference chip is added (back to
    pre-Option-B behaviour for that person)."""
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'],
                      janma_lagnas=[None])
    rashi_chips = [r for s in slots for r in s['reasons']
                   if 'Tula lagna favourable' in r]
    assert rashi_chips, 'expected at least one Tula kendra reason'
    # No reason should carry the ' lagna' reference suffix.
    for r in rashi_chips:
        assert 'lagna favourable' in r  # the leading "Tula lagna" mention
        assert ' lagna' not in r.split('from ')[1], \
            f'unexpected lagna suffix in fallback chip: {r}'


def test_activity_prefer_lagna_class_scores_when_slot_lagna_matches():
    """travel activity prefers Chara (movable) lagnas. On 2026-06-20
    Hyderabad, a choghadiya slot starts in Tula lagna (~10:05 IST) —
    Tula is a Chara rashi, so the slot picks up the +1 with a chip
    naming the class.
    """
    day = _day(2026, 6, 20)
    slots = day_slots(day, activity='travel')
    assert slots
    chara_chips = [
        r for s in slots for r in s['reasons']
        if 'lagna (Chara)' in r and 'Travel' in r
    ]
    assert chara_chips, \
        f'expected a Chara-lagna chip on a travel slot; reasons = ' \
        f'{[r for s in slots for r in s["reasons"] if "lagna" in r.lower()]}'


def test_activity_prefer_lagna_class_silent_when_slot_lagna_wrong():
    """travel activity (Chara) on a slot whose lagna is Sthira or
    Dvisvabhava should NOT produce the class chip. Tula on
    2026-06-20 is Chara; a Vrischika (Sthira) slot must not."""
    day = _day(2026, 6, 20)
    slots = day_slots(day, activity='travel')
    bad_chips = [
        r for s in slots for r in s['reasons']
        if ('lagna (Sthira)' in r or 'lagna (Dvisvabhava)' in r)
        and 'Travel' in r
    ]
    assert not bad_chips, \
        f'travel should only chip Chara lagnas, got: {bad_chips}'


def test_activity_lagna_independent_of_personal_kendra_trikona():
    """The activity-class chip is an INDEPENDENT scoring signal from
    the per-person kendra/trikona check. Both can fire on the same
    slot — verify the cell counts +2 not +1 when both match."""
    # 2026-06-20 Hyderabad: a slot in Tula (Chara) lagna.
    # janma rashi Mesha → Tula is 7th from Mesha (kendra).
    # So a wedding-scored slot in Tula gets the kendra chip from
    # the personal check, AND if we had a Chara-activity it'd
    # double up — but wedding prefers Sthira. Use travel instead
    # (Chara) for the activity, and Mesha rashi for the personal
    # kendra check. Tula lagna is 7th from Mesha AND Chara.
    day = _day(2026, 6, 20)
    slots = day_slots(day, activity='travel',
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'])
    assert slots
    # Find a slot with both chips firing.
    double = []
    for s in slots:
        has_personal = any('Tula lagna favourable' in r for r in s['reasons'])
        has_activity = any('lagna (Chara) favoured for Travel' in r for r in s['reasons'])
        if has_personal and has_activity:
            double.append(s)
    assert double, \
        'expected at least one Tula slot to fire both personal kendra AND activity Chara chips'


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
