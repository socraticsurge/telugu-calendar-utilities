import json

import pytest


def test_list_supported_cities_count():
    from telugu_panchangam.mcp.tools import tool_list_supported_cities
    result = json.loads(tool_list_supported_cities())
    assert len(result) == 22


def test_list_supported_cities_fields():
    from telugu_panchangam.mcp.tools import tool_list_supported_cities
    cities = json.loads(tool_list_supported_cities())
    for c in cities:
        assert 'name' in c
        assert 'latitude' in c
        assert 'longitude' in c
        assert 'timezone' in c
        assert 'country' in c


def test_get_panchangam_top_level_keys():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    for key in ('date', 'city', 'system', 'metadata', 'pancha_anga',
                'sky', 'auspicious', 'inauspicious', 'choghadiya',
                'special_days', 'is_special'):
        assert key in result, f"Missing key: {key}"


def test_get_panchangam_times_are_hhmm():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    sunrise = result['sky']['sunrise']
    assert len(sunrise) == 5
    assert sunrise[2] == ':'


def test_get_panchangam_metadata_fields():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    meta = result['metadata']
    for field in ('samvatsara', 'ayanam', 'rituvu', 'maasam', 'paksham', 'vaaram', 'solar_sign', 'lunar_sign'):
        assert field in meta, f"Missing metadata field: {field}"


def test_get_panchangam_all_three_systems():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    for system in ('drik', 'surya_siddhanta', 'vakya'):
        result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', system))
        assert 'error' not in result
        assert result['system'] == system


def test_get_muhurta_has_only_windows():
    from telugu_panchangam.mcp.tools import tool_get_muhurta
    result = json.loads(tool_get_muhurta('2026-06-10', 'Hyderabad', 'drik'))
    assert 'auspicious' in result
    assert 'inauspicious' in result
    assert 'pancha_anga' not in result
    assert 'metadata' not in result
    assert 'choghadiya' not in result


def test_get_muhurta_auspicious_keys():
    from telugu_panchangam.mcp.tools import tool_get_muhurta
    result = json.loads(tool_get_muhurta('2026-06-10', 'Hyderabad', 'drik'))
    assert 'brahma_muhurta' in result['auspicious']
    assert 'amrita_kalam' in result['auspicious']
    assert 'rahu_kalam' in result['inauspicious']
    assert 'gulika_kalam' in result['inauspicious']


def test_get_special_days_structure():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2026, 6, 'Hyderabad', 'drik'))
    assert 'special_days' in result
    assert isinstance(result['special_days'], list)
    assert len(result['special_days']) > 0


def test_get_special_days_entry_fields():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2026, 6, 'Hyderabad', 'drik'))
    for day in result['special_days']:
        assert 'date' in day
        assert 'tithi' in day
        assert 'events' in day
        assert isinstance(day['events'], list)


def test_get_panchangam_invalid_date():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('not-a-date', 'Hyderabad', 'drik'))
    assert 'error' in result
    assert 'YYYY-MM-DD' in result['error']


def test_get_panchangam_invalid_system():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'bad_system'))
    assert 'error' in result
    assert 'drik' in result['error']


def test_get_special_days_invalid_month():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2026, 13, 'Hyderabad', 'drik'))
    assert 'error' in result
    assert 'Invalid month' in result['error']


def test_get_panchangam_has_eclipse_and_special_yogas_keys():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    assert 'eclipse' in result
    assert 'special_yogas' in result
    assert isinstance(result['special_yogas'], list)


def test_get_panchangam_eclipse_populated_on_eclipse_date():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2025-09-07', 'Hyderabad', 'drik'))
    assert result['eclipse'] is not None
    assert result['eclipse']['kind'] == 'Lunar'
    assert result['eclipse']['subtype'] == 'Total'
    assert result['eclipse']['visible'] is True
    assert result['eclipse']['sutak'] is not None
    assert 'start' in result['eclipse']['sutak']


def test_get_panchangam_eclipse_none_on_non_eclipse_date():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    assert result['eclipse'] is None


def test_get_special_days_eclipse_event_listed():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2025, 9, 'Hyderabad', 'drik'))
    sep7 = next(d for d in result['special_days'] if d['date'] == '2025-09-07')
    assert any('Eclipse' in e for e in sep7['events'])


def test_get_special_days_special_yogas_key_present():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2026, 6, 'Hyderabad', 'drik'))
    assert len(result['special_days']) > 0
    for day in result['special_days']:
        assert 'special_yogas' in day
        assert isinstance(day['special_yogas'], list)


def test_get_panchangam_range_basic():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-06-10', '2026-06-12', 'Hyderabad'))
    assert 'days' in result
    assert len(result['days']) == 3
    day = result['days'][0]
    for key in ('date', 'vaaram', 'tithi', 'nakshatra', 'sunrise', 'sunset',
                'auspicious', 'inauspicious', 'special_days', 'special_yogas',
                'yoga', 'eclipse', 'is_special'):
        assert key in day, f"Missing key in range day: {key}"


def test_get_panchangam_range_exceeds_limit():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-01-01', '2026-06-01', 'Hyderabad'))
    assert 'error' in result


def test_get_panchangam_range_exactly_31_days_allowed():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-06-01', '2026-07-01', 'Hyderabad'))
    assert 'days' in result
    assert len(result['days']) == 31


def test_get_panchangam_range_32_days_rejected():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-06-01', '2026-07-02', 'Hyderabad'))
    assert 'error' in result


def test_get_panchangam_range_invalid_dates():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-06-12', '2026-06-10', 'Hyderabad'))
    assert 'error' in result


def test_get_panchangam_range_auspicious_keys():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-06-10', '2026-06-10', 'Hyderabad'))
    day = result['days'][0]
    assert 'brahma_muhurta' in day['auspicious']
    assert 'rahu_kalam' in day['inauspicious']


@pytest.mark.parametrize('system', ['drik', 'surya_siddhanta', 'vakya'])
def test_choghadiya_has_end_time(system):
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', system))
    assert 'choghadiya' in result
    chog = result['choghadiya']
    assert len(chog) == 8
    for entry in chog:
        assert 'end' in entry
        assert len(entry['end']) == 5
        assert entry['end'][2] == ':'


def test_get_panchangam_includes_festivals():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-11-08', 'Hyderabad', 'drik'))
    assert 'Deepavali' in result['special_days']
    assert 'Naraka Chaturdashi' in result['special_days']


def test_special_days_use_named_sankramanam():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-15', 'Hyderabad', 'drik'))
    assert 'Mithuna Sankramanam' in result['special_days']
    assert 'Sankranti' not in result['special_days']


# --- tool_get_daily_horas (Phase 7 PR 2 — was zero-direct-coverage) ----------

PLANET_HORA_NAMES = {
    'Sun Hora', 'Moon Hora', 'Mars Hora', 'Mercury Hora',
    'Jupiter Hora', 'Venus Hora', 'Saturn Hora',
}
# Hora rulers indexed by weekday-Sun=0 (planetary-hour rule): the first
# hora of the day is the day's lord — Sun on Sunday, Moon on Monday,
# Mars on Tuesday, Mercury on Wednesday, Jupiter on Thursday, Venus on
# Friday, Saturn on Saturday.
WEEKDAY_FIRST_HORA = [
    'Sun Hora', 'Moon Hora', 'Mars Hora', 'Mercury Hora',
    'Jupiter Hora', 'Venus Hora', 'Saturn Hora',
]


def test_get_daily_horas_top_level_shape():
    """Golden-day shape: 2027-09-04 Hyderabad — same Saturday as the
    DP-verified pilot cell in tests/fixtures/forward_year_festivals.json.
    """
    from telugu_panchangam.mcp.tools import tool_get_daily_horas
    result = json.loads(tool_get_daily_horas('2027-09-04', 'Hyderabad'))
    assert 'error' not in result, f'unexpected error: {result.get("error")}'
    for key in ('date', 'city', 'system', 'horas'):
        assert key in result, f'missing key {key!r} in {result.keys()}'
    assert result['date'] == '2027-09-04'
    assert result['city'] == 'Hyderabad'
    assert result['system'] == 'drik'


def test_get_daily_horas_entries_have_valid_planet_names():
    from telugu_panchangam.mcp.tools import tool_get_daily_horas
    result = json.loads(tool_get_daily_horas('2027-09-04', 'Hyderabad'))
    horas = result['horas']
    assert horas, 'horas list is empty'
    for h in horas:
        assert h['name'] in PLANET_HORA_NAMES, f"unknown hora ruler {h['name']!r}"
        assert 'start' in h
        assert 'end' in h
        assert h['start'] != h['end'], f'zero-length hora: {h}'


def test_get_daily_horas_first_hora_is_weekday_lord_each_weekday():
    """Planetary-hour rule: the first hora of every day is the weekday's
    own ruler (Sun on Sunday, Moon on Monday, … Saturn on Saturday).
    Sweeps a full week (2027-08-29 Sunday → 2027-09-04 Saturday).
    """
    from datetime import date, timedelta

    from telugu_panchangam.mcp.tools import tool_get_daily_horas
    start = date(2027, 8, 29)  # Sunday
    for offset in range(7):
        d = start + timedelta(days=offset)
        result = json.loads(tool_get_daily_horas(d.isoformat(), 'Hyderabad'))
        # Python weekday(): Mon=0..Sun=6; remap to Sun=0..Sat=6 (planetary-hour convention)
        wd_sun_first = (d.weekday() + 1) % 7
        expected = WEEKDAY_FIRST_HORA[wd_sun_first]
        actual = result['horas'][0]['name']
        assert actual == expected, (
            f'{d} ({d.strftime("%A")}): first hora {actual!r} != expected {expected!r}'
        )


def test_get_daily_horas_invalid_system_returns_error():
    from telugu_panchangam.mcp.tools import tool_get_daily_horas
    result = json.loads(tool_get_daily_horas('2026-06-15', 'Hyderabad', system='nonsense'))
    assert 'error' in result


# --- tool_get_lagna_transitions (Phase 7 PR 2 — was zero-direct-coverage) -----

RASHI_LAGNA_ORDER = [
    'Mesha Lagna', 'Vrishabha Lagna', 'Mithuna Lagna', 'Karka Lagna',
    'Simha Lagna', 'Kanya Lagna', 'Tula Lagna', 'Vrischika Lagna',
    'Dhanu Lagna', 'Makara Lagna', 'Kumbha Lagna', 'Meena Lagna',
]


def test_get_lagna_transitions_top_level_shape():
    """Golden-day shape: 2027-09-04 Hyderabad."""
    from telugu_panchangam.mcp.tools import tool_get_lagna_transitions
    result = json.loads(tool_get_lagna_transitions('2027-09-04', 'Hyderabad'))
    assert 'error' not in result, f'unexpected error: {result.get("error")}'
    for key in ('date', 'city', 'system', 'lagnas'):
        assert key in result, f'missing key {key!r} in {result.keys()}'
    assert result['date'] == '2027-09-04'


def test_get_lagna_transitions_entries_have_valid_rashi_names():
    from telugu_panchangam.mcp.tools import tool_get_lagna_transitions
    result = json.loads(tool_get_lagna_transitions('2027-09-04', 'Hyderabad'))
    lagnas = result['lagnas']
    assert lagnas, 'lagnas list is empty'
    for L in lagnas:
        assert L['name'] in RASHI_LAGNA_ORDER, f"unknown lagna {L['name']!r}"
        assert 'start' in L
        assert 'end' in L
        assert L['start'] != L['end'], f'zero-length lagna: {L}'


def test_get_lagna_transitions_count_in_expected_range():
    """A full sunrise-to-sunrise sky cycle yields 12–16 lagna windows.
    The Earth rotates ~13 rashis through 24 h; declination + latitude
    add ±2. Hyderabad's ~17.4°N typically gives 13–14.
    """
    from telugu_panchangam.mcp.tools import tool_get_lagna_transitions
    result = json.loads(tool_get_lagna_transitions('2027-09-04', 'Hyderabad'))
    n = len(result['lagnas'])
    assert 12 <= n <= 16, f'expected 12-16 lagna windows; got {n}'


def test_get_lagna_transitions_cyclic_order():
    """Consecutive lagnas advance one rashi at a time around the zodiac:
    Mesha → Vrishabha → … → Meena → Mesha. Any non-adjacent step is a
    regression in the bisection / transition logic.
    """
    from telugu_panchangam.mcp.tools import tool_get_lagna_transitions
    result = json.loads(tool_get_lagna_transitions('2027-09-04', 'Hyderabad'))
    lagnas = result['lagnas']
    idx = [RASHI_LAGNA_ORDER.index(L['name']) for L in lagnas]
    for i in range(len(idx) - 1):
        nxt_expected = (idx[i] + 1) % 12
        assert idx[i + 1] == nxt_expected, (
            f'lagna {i} ({lagnas[i]["name"]}) → {i+1} ({lagnas[i+1]["name"]}) '
            f'broke cyclic order (expected {RASHI_LAGNA_ORDER[nxt_expected]})'
        )


def test_get_lagna_transitions_invalid_date_returns_error():
    from telugu_panchangam.mcp.tools import tool_get_lagna_transitions
    result = json.loads(tool_get_lagna_transitions('not-a-date', 'Hyderabad'))
    assert 'error' in result
