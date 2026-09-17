"""Muhurta mcp contracts; assertions preserved from the original suite."""



def test_mcp_find_muhurta_emits_dropped_days():
    import json

    from telugu_panchangam.mcp.tools import tool_find_muhurta
    # Wedding over 2026-06-16 to 2026-06-20 — should drop 06-17 (Dagdha)
    # and 06-18 (Dagdha is gone, but Rikta + Sarvartha Siddhi might mix);
    # let's just verify dropped_days exists and at least the Dagdha day
    # appears for wedding activity.
    result = json.loads(tool_find_muhurta('2026-06-16', 5, 'wedding', 'Hyderabad'))
    assert 'dropped_days' in result
    # The 17th has Dagdha Yoga — must show up in dropped_days for wedding
    dropped_dates = {dd['date'] for dd in result['dropped_days']}
    assert '2026-06-17' in dropped_dates, f'expected Dagdha day in dropped_days; got {result["dropped_days"]}'
    # Each dropped entry has a date and a reason
    for dd in result['dropped_days']:
        assert 'date' in dd
        assert 'reason' in dd
        assert isinstance(dd['reason'], str)
        assert dd['reason']


def test_mcp_find_muhurta_emits_tier_on_each_slot():
    import json

    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta('2026-06-15', 5, 'any', 'Hyderabad'))
    assert result['slots']
    for s in result['slots']:
        assert s['tier'] in ('Excellent', 'Good', 'Fair', 'Avoid')


def test_mcp_find_muhurta_exposes_janma_rasis_janma_lagnas_chandra_mode():
    """The MCP-exposed find_muhurta (server.py) must thread all per-person
    inputs that the underlying tool_find_muhurta (tools.py) accepts.

    Regression guard: until this fix, MCP clients could pass only
    janma_nakshatras — the Chandrabalam (janma_rasis), Lagna Shuddhi
    (janma_lagnas), and chandra_mode parameters that tool_find_muhurta
    already supported were unreachable from any MCP client.
    """
    import json

    from telugu_panchangam.mcp.server import find_muhurta
    # FastMCP @mcp.tool() wraps the function — original is on .fn
    fn = getattr(find_muhurta, 'fn', find_muhurta)
    result = json.loads(fn(
        '2026-06-15',
        days=3,
        activity='any',
        city='Hyderabad',
        janma_nakshatras=['Ashvini', 'Bharani'],
        janma_rasis=['Mesha', None],         # second person's rashi unknown
        janma_lagnas=[None, 'Karka'],        # first person's lagna unknown
        chandra_mode='puja_ok',
    ))
    assert 'error' not in result, f'unexpected error: {result.get("error")}'
    assert 'slots' in result
    assert result.get('chandra_mode') == 'puja_ok'


def test_find_muhurta_python_and_mcp_signatures_are_stable():
    """The complexity refactor must not change either public call contract."""
    from inspect import signature

    from telugu_panchangam.mcp.server import find_muhurta
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    tool_parameters = signature(tool_find_muhurta).parameters
    assert tuple(tool_parameters) == (
        'start_date',
        'days',
        'activity',
        'city',
        'system',
        'janma_nakshatras',
        'janma_rasis',
        'janma_lagnas',
        'chandra_mode',
        'latitude',
        'longitude',
        'timezone',
        'ayanamsa',
        'travel_direction',
        'include_night',
    )
    assert tool_parameters['days'].default == 7
    assert tool_parameters['include_night'].default is False

    mcp_parameters = signature(find_muhurta).parameters
    assert tuple(mcp_parameters) == tuple(tool_parameters)[:13] + ('include_night',)
    assert mcp_parameters['days'].default == 7
    assert mcp_parameters['include_night'].default is False


def test_engine_kwarg_does_not_break_mcp_path():
    """Through the MCP tool — verify it still produces results."""
    import json

    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta('2026-06-15', 5, 'any', 'Hyderabad'))
    assert result['slots']
    # Score is the sum of its (+n)/(-n) reasons
    for s in result['slots']:
        bonuses = []
        for r in s['reasons']:
            # Match trailing (+N) or (-N)
            import re
            m = re.search(r'\(([+-]\d+)\)\s*$', r)
            if m:
                bonuses.append(int(m.group(1)))
        # Reasons may include the constant 'clear of all inauspicious windows'
        # and karana-avoided lines that don't have a number — those are fine.
        # We just verify the sum matches the score.
        assert sum(bonuses) == s['score'], \
            f'reasons {bonuses} should sum to {s["score"]} but got {sum(bonuses)}'


def test_mcp_find_muhurta():
    import json

    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta('2026-06-15', 5, 'any', 'Hyderabad'))
    assert result['slots'], 'expected at least one slot in 5 days'
    top = result['slots'][0]
    assert {'date', 'vaaram', 'start', 'end', 'score', 'reasons'} <= set(top)
    # Sorted by (tier desc, score desc) — tier takes priority, so a lower-score
    # slot in a higher tier may appear before a higher-score slot capped to a
    # lower tier by day_dosha.  Check the actual sort key, not score alone.
    from telugu_panchangam.personal.muhurta import TIER_NAMES
    def sort_key(slot):
        return -TIER_NAMES.index(slot['tier']), -slot['score']

    assert result['slots'] == sorted(result['slots'], key=sort_key)
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
    assert 'error' in json.loads(tool_find_muhurta('2026-06-15', 5, 'not-a-real-activity', 'Hyderabad'))
    assert 'error' in json.loads(tool_find_muhurta(
        '2026-06-15', 5, 'any', 'Hyderabad', chandra_mode='bogus'))
    # rashis without aligned nakshatras
    assert 'error' in json.loads(tool_find_muhurta(
        '2026-06-15', 5, 'any', 'Hyderabad', janma_rasis=['Karka']))


def test_mcp_find_muhurta_include_night():
    import json

    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta(
        '2026-06-15', 3, 'any', 'Hyderabad', include_night=True))
    assert 'slots' in result
    assert result['slots'], 'expected at least one slot over 3 days with night included'
    # Verify some night slots exist (start time after ~18:00 local)
    # We just check that all slots have the required keys.
    for s in result['slots']:
        assert {'date', 'vaaram', 'start', 'end', 'score', 'reasons'} <= set(s)
