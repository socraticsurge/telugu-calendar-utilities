# Muhurta finder: slots derive from already-verified engine windows.
from datetime import date

import pytest

from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES
from telugu_panchangam.personal.muhurta import day_slots, GOOD_CHOGHADIYA

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(y, m, d, include_eclipse=False):
    return ENGINE.calculate(date(y, m, d), HYD, include_eclipse=include_eclipse)


def test_slots_never_overlap_inauspicious_windows():
    day = _day(2026, 6, 17)
    bad = [day.rahu_kalam, day.gulika_kalam, day.yamagandam] + day.varjyam + day.durmuhurtham
    for s in day_slots(day):
        for w in bad:
            assert not (s['start'] < w.end and w.start < s['end']), \
                f"slot {s['start']}-{s['end']} overlaps {w.name}"


def test_slots_come_from_good_choghadiya_only():
    day = _day(2026, 6, 17)
    for s in day_slots(day):
        assert s['reasons'][0].split(' ')[0] in GOOD_CHOGHADIYA


def test_ranked_by_score_and_carries_reasons():
    slots = day_slots(_day(2026, 6, 17))
    assert slots and all(slots[i]['score'] >= slots[i+1]['score'] for i in range(len(slots)-1))
    assert all(s['reasons'] for s in slots)


def test_travel_avoids_vishti():
    # 2026-06-10: Vishti karana runs 13:52 to past midnight (daytime overlap)
    day = _day(2026, 6, 10)
    vishti = [k for k in day.karana if k.name == 'Vishti']
    assert vishti, 'fixture assumption: Vishti present this day'
    for s in day_slots(day, activity='travel'):
        for k in vishti:
            assert not (s['start'] < k.end and k.start < s['end'])


# --- Tarabalam: graded per-person (no longer hard-skip) ---

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


# --- Chandrabalam: graded per-person, mode filters not scores ---

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
    assert s_stars and s_puja and s_strict
    assert [s['score'] for s in s_stars] == [s['score'] for s in s_puja]
    assert [s['score'] for s in s_stars] == [s['score'] for s in s_strict]


# --- Eclipse hard-skip ---

def test_eclipse_day_returns_no_slots():
    # 2027-08-02: total solar eclipse, visible from Hyderabad.
    day = _day(2027, 8, 2, include_eclipse=True)
    assert day.eclipse is not None, 'fixture assumption: eclipse present this day'
    assert day_slots(day) == [], 'eclipse days are deferred for auspicious activities'


# --- Validation ---

def test_invalid_activity_raises():
    with pytest.raises(ValueError):
        day_slots(_day(2026, 6, 17), activity='wedding')


def test_invalid_chandra_mode_raises():
    with pytest.raises(ValueError):
        day_slots(_day(2026, 6, 17), chandra_mode='bogus')


def test_misaligned_rasis_raise():
    with pytest.raises(ValueError):
        day_slots(_day(2026, 6, 17),
                  janma_nakshatras=['Pushya'],
                  janma_rasis=['Karka', 'Mesha'])


# --- MCP ---

def test_mcp_find_muhurta():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta('2026-06-15', 5, 'any', 'Hyderabad'))
    assert result['slots'], 'expected at least one slot in 5 days'
    top = result['slots'][0]
    assert {'date', 'vaaram', 'start', 'end', 'score', 'reasons'} <= set(top)
    scores = [s['score'] for s in result['slots']]
    assert scores == sorted(scores, reverse=True)
    assert 'disclaimer' in result
    assert result['chandra_mode'] == 'stars'


def test_mcp_find_muhurta_with_chandra_mode():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta(
        '2026-06-15', 5, 'any', 'Hyderabad',
        janma_nakshatras=['Pushya'], janma_rasis=['Karka'],
        chandra_mode='strict'))
    # Karka has Moon at 12 from Karka on Mithuna days — should drop those.
    # We don't assert empty (depends on the whole window), but result must
    # be a list and chandra_mode must round-trip.
    assert result['chandra_mode'] == 'strict'
    assert isinstance(result['slots'], list)


def test_mcp_find_muhurta_validates():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    assert 'error' in json.loads(tool_find_muhurta('2026-06-15', 20, 'any', 'Hyderabad'))
    assert 'error' in json.loads(tool_find_muhurta('2026-06-15', 5, 'wedding', 'Hyderabad'))
    assert 'error' in json.loads(tool_find_muhurta(
        '2026-06-15', 5, 'any', 'Hyderabad', chandra_mode='bogus'))
    # rashis without aligned nakshatras
    assert 'error' in json.loads(tool_find_muhurta(
        '2026-06-15', 5, 'any', 'Hyderabad', janma_rasis=['Karka']))
