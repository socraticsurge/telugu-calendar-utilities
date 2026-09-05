# Chandrabalam verified against drikpanchang.com chandrabalam-timings
# (Hyderabad, 11/06/2026): moon in Meena, then Mesha after 08:16 —
# both 12-rasi verdict columns pinned below.
import pytest

from telugu_panchangam.personal.chandrabalam import (
    chandra_position,
    chandra_verdict,
    is_favourable_chandra,
)

# DP verdicts with moon in Meena: (janma rasi, verdict)
MEENA_DAY = [
    ('Mesha', 'bad'), ('Vrishabha', 'good'), ('Mithuna', 'good'),
    ('Karka', 'puja'), ('Simha', 'bad'), ('Kanya', 'good'),
    ('Tula', 'good'), ('Vrischika', 'puja'), ('Dhanu', 'bad'),
    ('Makara', 'good'), ('Kumbha', 'puja'), ('Meena', 'good'),
]

# DP verdicts with moon in Mesha
MESHA_DAY = [
    ('Mesha', 'good'), ('Vrishabha', 'bad'), ('Mithuna', 'good'),
    ('Karka', 'good'), ('Simha', 'puja'), ('Kanya', 'bad'),
    ('Tula', 'good'), ('Vrischika', 'good'), ('Dhanu', 'puja'),
    ('Makara', 'bad'), ('Kumbha', 'good'), ('Meena', 'puja'),
]


@pytest.mark.parametrize('janma,expected', MEENA_DAY)
def test_chandrabalam_moon_in_meena(janma, expected):
    assert chandra_verdict(chandra_position(janma, 'Meena')) == expected


@pytest.mark.parametrize('janma,expected', MESHA_DAY)
def test_chandrabalam_moon_in_mesha(janma, expected):
    assert chandra_verdict(chandra_position(janma, 'Mesha')) == expected


def test_position_is_one_indexed_from_janma():
    assert chandra_position('Mesha', 'Mesha') == 1
    assert chandra_position('Mesha', 'Vrishabha') == 2
    assert chandra_position('Meena', 'Mesha') == 2

def test_favourable_positions():
    assert [n for n in range(1, 13) if is_favourable_chandra(n)] == [1, 3, 6, 7, 10, 11]

def test_invalid_rasi_raises():
    with pytest.raises(ValueError):
        chandra_position('Aries', 'Meena')


# --- MCP integration: optional janma_rasis on find_tarabalam_days ---

def test_mcp_tarabalam_with_rasis():
    import json

    from telugu_panchangam.mcp.tools import tool_find_tarabalam_days
    result = json.loads(tool_find_tarabalam_days(
        ['Uttara Bhadrapada', 'Purva Ashadha'], '2026-06-11', 7, 'Hyderabad', 'drik',
        janma_rasis=['Meena', None]))
    d0 = result['days'][0]
    # 2026-06-11 sunrise: moon in Meena -> position 1 from Meena -> good
    assert d0['taras'][0]['chandra'] == {'position': 1, 'verdict': 'good'}
    # No rasi given for the second person -> no chandra key
    assert 'chandra' not in d0['taras'][1]
    # default chandra_mode='stars': chandra annotates but never blocks
    for day in result['days']:
        assert day['good_for_all'] == all(t['auspicious'] for t in day['taras'])


def test_mcp_chandra_mode_strict_and_puja_ok():
    import json

    from telugu_panchangam.mcp.tools import tool_find_tarabalam_days
    args = (['Uttara Bhadrapada', 'Purva Ashadha'], '2026-06-11', 14, 'Hyderabad', 'drik')
    kw = dict(janma_rasis=['Meena', 'Dhanu'])
    stars  = json.loads(tool_find_tarabalam_days(*args, **kw, chandra_mode='stars'))
    pujaok = json.loads(tool_find_tarabalam_days(*args, **kw, chandra_mode='puja_ok'))
    strict = json.loads(tool_find_tarabalam_days(*args, **kw, chandra_mode='strict'))
    # this pair aligns on stars but never clears the moon (verified by cycle analysis)
    assert len(stars['good_for_all_dates']) > 0
    assert pujaok['good_for_all_dates'] == []
    assert strict['good_for_all_dates'] == []
    assert 'error' in json.loads(tool_find_tarabalam_days(*args, **kw, chandra_mode='loose'))


def test_mcp_tarabalam_rasis_validation():
    import json

    from telugu_panchangam.mcp.tools import tool_find_tarabalam_days
    assert 'error' in json.loads(tool_find_tarabalam_days(
        ['Revati'], '2026-06-11', 7, 'Hyderabad', 'drik', janma_rasis=['Aries']))
    assert 'error' in json.loads(tool_find_tarabalam_days(
        ['Revati'], '2026-06-11', 7, 'Hyderabad', 'drik', janma_rasis=['Meena', 'Mesha']))


# --- Rashi derivation from nakshatra + padam ---

def test_rasi_derivation():
    from telugu_panchangam.personal.chandrabalam import rasi_from_nakshatra
    # 18 stars sit wholly in one rashi — padam irrelevant
    assert rasi_from_nakshatra('Ashvini') == 'Mesha'
    assert rasi_from_nakshatra('Uttara Bhadrapada') == 'Meena'
    assert rasi_from_nakshatra('Rohini', 3) == 'Vrishabha'
    # straddling stars need the padam
    assert rasi_from_nakshatra('Krittika') is None
    assert rasi_from_nakshatra('Krittika', 1) == 'Mesha'
    assert rasi_from_nakshatra('Krittika', 2) == 'Vrishabha'
    assert rasi_from_nakshatra('Uttara Phalguni', 1) == 'Simha'
    assert rasi_from_nakshatra('Uttara Phalguni', 4) == 'Kanya'
    assert rasi_from_nakshatra('Purva Bhadrapada', 4) == 'Meena'

def test_exactly_nine_stars_straddle():
    from telugu_panchangam.panchangam_names import NAKSHATRA_NAMES
    from telugu_panchangam.personal.chandrabalam import rasi_from_nakshatra
    straddlers = [n for n in NAKSHATRA_NAMES if rasi_from_nakshatra(n) is None]
    assert straddlers == ['Krittika', 'Mrigashira', 'Punarvasu', 'Uttara Phalguni',
                          'Chitra', 'Vishakha', 'Uttara Ashadha', 'Dhanishtha',
                          'Purva Bhadrapada']
