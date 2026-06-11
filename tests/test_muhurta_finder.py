# Muhurta finder: slots derive from already-verified engine windows.
from datetime import date, timedelta

import pytest

from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES
from telugu_panchangam.personal.muhurta import day_slots, GOOD_CHOGHADIYA

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(y, m, d):
    return ENGINE.calculate(date(y, m, d), HYD, include_eclipse=False)


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


def test_group_screening_skips_unfavourable_days():
    # 2026-06-18 is a Pushya day: Janma tara for Uttara Bhadrapada -> skipped
    assert day_slots(_day(2026, 6, 18), janma_nakshatras=['Uttara Bhadrapada']) == []
    # 2026-06-17 (Punarvasu): Parama Mitra -> included, with the group reason
    slots = day_slots(_day(2026, 6, 17), janma_nakshatras=['Uttara Bhadrapada'])
    assert slots and any('tarabalam favourable' in r for r in slots[0]['reasons'])


def test_invalid_activity_raises():
    with pytest.raises(ValueError):
        day_slots(_day(2026, 6, 17), activity='wedding')


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


def test_mcp_find_muhurta_validates():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    assert 'error' in json.loads(tool_find_muhurta('2026-06-15', 20, 'any', 'Hyderabad'))
    assert 'error' in json.loads(tool_find_muhurta('2026-06-15', 5, 'wedding', 'Hyderabad'))
