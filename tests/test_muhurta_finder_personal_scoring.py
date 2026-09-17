"""Muhurta personal scoring contracts; assertions preserved from the original suite."""


import pytest

from telugu_panchangam.personal.muhurta import day_slots
from tests.muhurta_finder_support import _day, _expected_tier


def test_tarabalam_favourable_adds_per_person_bonus():
    # 2026-06-17 (Punarvasu): Parama Mitra for Uttara Bhadrapada -> +1
    slots = day_slots(_day(2026, 6, 17), janma_nakshatras=['Uttara Bhadrapada'])
    assert slots, 'favourable day should produce slots'
    reasons = slots[0]['reasons']
    assert any('tarabalam favourable' in r and '(+1)' in r for r in reasons), \
        f'expected +1 tarabalam reason; got {reasons}'


def test_tarabalam_unfavourable_keeps_day_but_penalises():
    # 2026-06-18 (Pushya): Janma tara for Uttara Bhadrapada.
    # Old behavior was to hard-skip; new graded behavior keeps the slot at -1.
    slots = day_slots(_day(2026, 6, 18), janma_nakshatras=['Uttara Bhadrapada'])
    assert slots, 'graded scoring should not hard-skip a Janma day'
    assert any('tarabalam avoid' in r and '(-1)' in r for s in slots for r in s['reasons'])


def test_tarabalam_mixed_group_nets_correctly():
    # 2026-06-17 (Punarvasu).
    # Uttara Bhadrapada -> Parama Mitra (favourable, +1)
    # Vishakha -> Janma (unfavourable, -1)  (Vishakha sits 9 stars before Punarvasu)
    # Net tarabalam: 0
    slots = day_slots(_day(2026, 6, 17),
                      janma_nakshatras=['Uttara Bhadrapada', 'Vishakha'])
    assert slots
    rs = slots[0]['reasons']
    assert any('tarabalam favourable' in r and '(+1)' in r for r in rs)
    assert any('tarabalam avoid' in r and '(-1)' in r for r in rs)


def test_chandrabalam_good_adds_bonus_in_default_mode():
    # 2026-06-17: Moon is in Mithuna. Janma rashi Mesha -> position 3 (good).
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'])
    assert slots
    assert any('chandrabalam favourable' in r and '(+1)' in r for r in slots[0]['reasons'])


def test_chandrabalam_remedial_annotates_no_score():
    # 2026-06-17 Moon in Mithuna. Vrishabha -> position 2 (remedial).
    # Rohini (Kshema on Punarvasu, favourable tarabalam) sits in Vrishabha.
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Rohini'],
                      janma_rasis=['Vrishabha'])
    assert slots
    rs = slots[0]['reasons']
    # remedial gives no bonus and no penalty — just an annotation line
    assert any('chandrabalam remedial' in r for r in rs)
    assert not any('chandrabalam favourable' in r for r in rs)


def test_chandrabalam_avoid_subtracts():
    # 2026-06-17 Moon in Mithuna. Karka -> position 12 (avoid).
    # Pushya (Parama Mitra on Punarvasu, favourable tarabalam) sits in Karka.
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Pushya'],
                      janma_rasis=['Karka'])
    assert slots, 'default stars mode does not filter avoid days'
    rs = slots[0]['reasons']
    assert any('chandrabalam avoid' in r and '(-1)' in r for r in rs)


def test_chandra_mode_strict_filters_remedial_and_avoid_days():
    day = _day(2026, 6, 17)
    # Rohini + Vrishabha -> Moon@2 = remedial; strict mode filters out
    assert day_slots(day, janma_nakshatras=['Rohini'], janma_rasis=['Vrishabha'],
                    chandra_mode='strict') == []
    # Pushya + Karka -> Moon@12 = avoid; strict and puja_ok both filter
    assert day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'],
                    chandra_mode='strict') == []
    assert day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'],
                    chandra_mode='puja_ok') == []
    # But puja_ok keeps remedial days (Rohini + Vrishabha)
    assert day_slots(day, janma_nakshatras=['Rohini'], janma_rasis=['Vrishabha'],
                    chandra_mode='puja_ok'), \
        'puja_ok should keep remedial days'


def test_chandrabalam_scores_identical_across_modes():
    """The same slot has the same score regardless of mode — mode only filters."""
    day = _day(2026, 6, 17)
    # Mesha -> Moon@3 = good. Visible in all three modes; score must match.
    args = dict(janma_nakshatras=['Krittika'], janma_rasis=['Mesha'])
    s_stars = day_slots(day, **args, chandra_mode='stars')
    s_puja = day_slots(day, **args, chandra_mode='puja_ok')
    s_strict = day_slots(day, **args, chandra_mode='strict')
    assert s_stars
    assert s_puja
    assert s_strict
    assert [s['score'] for s in s_stars] == [s['score'] for s in s_puja]
    assert [s['score'] for s in s_stars] == [s['score'] for s in s_strict]


def test_score_tier_thresholds():
    from telugu_panchangam.personal.muhurta import score_tier
    # Excellent: ≥ 7
    assert score_tier(7) == 'Excellent'
    assert score_tier(15) == 'Excellent'
    # Good: 4..6
    assert score_tier(6) == 'Good'
    assert score_tier(4) == 'Good'
    # Fair: 1..3
    assert score_tier(3) == 'Fair'
    assert score_tier(1) == 'Fair'
    # Avoid: ≤ 0
    assert score_tier(0) == 'Avoid'
    assert score_tier(-5) == 'Avoid'


def test_each_slot_carries_a_tier():
    """Every slot has a `tier` field matching its relative score band."""
    day = _day(2026, 6, 17)
    slots = day_slots(day)
    assert slots
    for s in slots:
        assert s['tier'] == _expected_tier(slots, s['score'], s['personal_dosha'], s['day_dosha'])
        assert s['tier'] in ('Excellent', 'Good', 'Fair', 'Avoid')


def test_personal_dosha_none_when_chandra_and_tara_clean():
    # 2026-06-17: Mesha -> Moon@3 (good) — no chandra caution.
    # janma=Krittika may still set tara_dosha for the day's nakshatras;
    # what we're asserting here is the chandra branch stays clean.
    day = _day(2026, 6, 17)
    slots = day_slots(day, janma_nakshatras=['Krittika'], janma_rasis=['Mesha'])
    assert slots
    assert all(s['personal_dosha'] not in ('chandra_avoid', 'chandra_remedial')
               for s in slots)


def test_personal_dosha_tara_dosha_caps_tier():
    # 2026-06-20: janma Ashvini sees an unfavourable tara on this day's
    # nakshatra, and no Sarvartha/Amrita Siddhi Yoga rectifies it. The
    # top slot should be flagged 'tara_dosha' and capped below Excellent.
    day = _day(2026, 6, 20)
    slots = day_slots(day, janma_nakshatras=['Ashvini'])
    assert slots
    top = slots[0]
    assert top['personal_dosha'] == 'tara_dosha'
    assert top['tier'] != 'Excellent'


def test_personal_dosha_chandra_avoid_caps_tier():
    # 2026-06-25: Pushya + Karka -> Moon@4 (avoid, non-Ashtama). The top
    # slot scores 8 (Excellent by raw score — now including the +1 for the
    # muhurta's auspicious nature) but the unrectified chandra_avoid dosha
    # caps its tier at Good.
    from telugu_panchangam.personal.muhurta import score_tier
    day = _day(2026, 6, 25)
    slots = day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'])
    assert slots
    top = slots[0]
    assert top['score'] == 8
    assert score_tier(top['score']) == 'Excellent'
    assert top['personal_dosha'] == 'chandra_avoid'
    assert top['tier'] == 'Good'


def test_personal_dosha_chandra_remedial_caps_tier_when_excellent():
    # 2026-06-17: Rohini + Vrishabha -> Moon@2 (remedial/puja position).
    day = _day(2026, 6, 17)
    slots = day_slots(day, janma_nakshatras=['Rohini'], janma_rasis=['Vrishabha'])
    assert slots
    for s in slots:
        assert s['personal_dosha'] == 'chandra_remedial'
        assert s['tier'] == _expected_tier(slots, s['score'], s['personal_dosha'], s['day_dosha'])


def test_sort_tiebreaker_prefers_personally_clean_slot():
    """Among equal-score slots, the one without a personal dosha sorts first."""
    day = _day(2026, 6, 25)
    slots = day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'])
    assert slots
    # The sort key (-score, has_personal_dosha, start) must be honoured —
    # for any pair of equal-score slots, a clean one (if present) cannot
    # follow a dosha-bearing one.
    for i in range(len(slots) - 1):
        a, b = slots[i], slots[i + 1]
        if a['score'] == b['score']:
            assert (a['personal_dosha'] is not None) <= (b['personal_dosha'] is not None)


def test_day_dosha_rikta_tithi_caps_tier_when_excellent():
    # 2026-06-14: Krishna Chaturdashi (Rikta tithi). A slot here should
    # never show as "Excellent" even if its raw score is the batch ceiling.
    day = _day(2026, 6, 14)
    slots = day_slots(day)
    assert slots
    rikta_slots = [s for s in slots if s['day_dosha'] == 'rikta_tithi']
    assert rikta_slots
    for s in rikta_slots:
        assert s['tier'] == _expected_tier(slots, s['score'], s['personal_dosha'], s['day_dosha'])
        assert s['tier'] != 'Excellent'


def test_day_dosha_amavasya_caps_tier_when_excellent():
    # 2026-06-15: Amavasya. Treated same as Rikta tithi for tier-cap.
    day = _day(2026, 6, 15)
    slots = day_slots(day)
    assert slots
    amavasya_slots = [s for s in slots if s['day_dosha'] == 'amavasya']
    assert amavasya_slots
    for s in amavasya_slots:
        assert s['tier'] == _expected_tier(slots, s['score'], s['personal_dosha'], s['day_dosha'])
        assert s['tier'] != 'Excellent'


def test_day_dosha_none_on_clean_day():
    day = _day(2026, 6, 16)
    slots = day_slots(day)
    assert slots
    assert all(s['day_dosha'] is None for s in slots)


@pytest.mark.parametrize(
    ("chandra_mode", "expected_dropped"),
    (("stars", False), ("puja_ok", True), ("strict", True)),
)
def test_score_chandra_preserves_per_person_results(
    chandra_mode, expected_dropped
):
    from telugu_panchangam.personal.slot_scorers import score_chandra

    result = score_chandra(
        ["Ashvini", "Bharani", "Krittika", "Rohini"],
        ["Mesha", "Meena", "Kanya", None],
        "Mesha",
        chandra_mode,
    )

    assert result == (
        0,
        [
            "chandrabalam favourable for #1 (Ashvini) (+1)",
            "chandrabalam remedial for #2 (Bharani) Moon@2 (puja recommended)",
            "chandrabalam avoid for #3 (Krittika) Ashtama Moon@8 (-1)",
        ],
        expected_dropped,
        ["#3 (Krittika) Ashtama"],
        ["#2 (Bharani)"],
    )


def test_score_chandra_ignores_unknown_rashis():
    from telugu_panchangam.personal.slot_scorers import score_chandra

    assert score_chandra(["Ashvini"], [None], "Mesha", "strict") == (
        0,
        [],
        False,
        [],
        [],
    )
