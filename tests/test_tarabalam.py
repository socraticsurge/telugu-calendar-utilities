# Tarabalam counting verified against a reference tarabala table
# (June 2026, four janma nakshatras; see feature/tarabalam PR).
from telugu_panchangam.personal.tarabalam import (
    tara_number, tara_name, is_auspicious_tara, taras_for_day, TARA_NAMES,
)


# --- Counting rule: janma -> day nakshatra, inclusive, mod 9 ---
# Reference rows for an Ashvini day:

def test_uttara_bhadrapada_on_ashvini_day_is_vipat():
    assert tara_number('Uttara Bhadrapada', 'Ashvini') == 3
    assert tara_name(3) == 'Vipat'

def test_purva_ashadha_on_ashvini_day_is_parama_mitra():
    assert tara_number('Purva Ashadha', 'Ashvini') == 9
    assert tara_name(9) == 'Parama Mitra'

def test_shravana_on_ashvini_day_is_naidhana():
    assert tara_number('Shravana', 'Ashvini') == 7
    assert tara_name(7) == 'Naidhana'

def test_purva_phalguni_on_ashvini_day_is_parama_mitra():
    assert tara_number('Purva Phalguni', 'Ashvini') == 9

# Reference rows for a Pushya day:

def test_uttara_bhadrapada_on_pushya_day_is_janma():
    assert tara_number('Uttara Bhadrapada', 'Pushya') == 1
    assert tara_name(1) == 'Janma'

def test_shravana_on_pushya_day_is_pratyak():
    assert tara_number('Shravana', 'Pushya') == 5

def test_same_nakshatra_is_janma():
    assert tara_number('Rohini', 'Rohini') == 1


# --- Auspiciousness convention: 2,4,6,8,9 good; 1,3,5,7 avoid ---

def test_auspicious_taras():
    assert [n for n in range(1, 10) if is_auspicious_tara(n)] == [2, 4, 6, 8, 9]


def test_tara_names_complete():
    assert TARA_NAMES == ['Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak',
                          'Sadhana', 'Naidhana', 'Mitra', 'Parama Mitra']


# --- Group day view ---

def test_taras_for_day_group():
    out = taras_for_day('Ashvini', ['Uttara Bhadrapada', 'Purva Ashadha'])
    assert out[0] == {'janma_nakshatra': 'Uttara Bhadrapada', 'tara': 3,
                      'name': 'Vipat', 'auspicious': False}
    assert out[1]['name'] == 'Parama Mitra' and out[1]['auspicious'] is True

def test_good_for_all_requires_every_tara_auspicious():
    from telugu_panchangam.personal.tarabalam import good_for_all
    group = ['Uttara Bhadrapada', 'Purva Ashadha', 'Shravana', 'Purva Phalguni']
    # Punarvasu day (reference: marked good-for-all): 9/6/4/6 — all auspicious
    assert good_for_all('Punarvasu', group) is True
    # Ashvini day: Vipat for U.Bhadrapada and Naidhana for Shravana
    assert good_for_all('Ashvini', group) is False
    # Bharani day: Janma for Purva Ashadha and Purva Phalguni
    assert good_for_all('Bharani', group) is False


def test_invalid_nakshatra_raises():
    import pytest
    with pytest.raises(ValueError):
        tara_number('Ashwini', 'Pushya')  # misspelling: must match canonical list


# --- MCP tool ---

def test_mcp_find_tarabalam_days():
    import json
    from telugu_panchangam.mcp.tools import tool_find_tarabalam_days
    result = json.loads(tool_find_tarabalam_days(
        ['Uttara Bhadrapada', 'Purva Ashadha', 'Shravana', 'Purva Phalguni'],
        '2026-06-11', 14, 'Hyderabad', 'drik'))
    assert len(result['days']) == 14
    d0 = result['days'][0]
    assert d0['date'] == '2026-06-11'
    assert d0['nakshatra'] == 'Revati'
    # Revati(26): U.Bh -> 2 Sampat
    assert d0['taras'][0]['name'] == 'Sampat'
    assert isinstance(d0['good_for_all'], bool)
    assert 'good_for_all_dates' in result


def test_mcp_find_tarabalam_days_validates():
    import json
    from telugu_panchangam.mcp.tools import tool_find_tarabalam_days
    # Error convention matches the other MCP tools: {'error': ...} JSON
    assert 'error' in json.loads(tool_find_tarabalam_days(
        [], '2026-06-11', 7, 'Hyderabad', 'drik'))
    assert 'error' in json.loads(tool_find_tarabalam_days(
        ['Revati'] * 5, '2026-06-11', 7, 'Hyderabad', 'drik'))
    assert 'error' in json.loads(tool_find_tarabalam_days(
        ['Revati'], '2026-06-11', 61, 'Hyderabad', 'drik'))
    assert 'error' in json.loads(tool_find_tarabalam_days(
        ['Ashwini'], '2026-06-11', 7, 'Hyderabad', 'drik'))  # misspelling
