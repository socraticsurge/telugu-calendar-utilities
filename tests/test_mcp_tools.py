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
