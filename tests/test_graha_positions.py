# Graha positions verified against drikpanchang.com sidereal planetary
# positions (11/06/2026, Hyderabad). The Moon is pinned via the day page's
# sunrise nakshatra (Revati) since DP's positions page is time-of-fetch.
from datetime import date

from telugu_panchangam.engines.utils import get_sunrise, local_midnight_jd
from telugu_panchangam.gochara.positions import GRAHA_NAMES, graha_positions

HYD_GEO = [78.4744, 17.3850, 0.0]


def _sunrise_jd(d):
    return get_sunrise(local_midnight_jd(d, 'Asia/Kolkata'), HYD_GEO)


def _positions():
    return {g['graha']: g for g in graha_positions(_sunrise_jd(date(2026, 6, 11)))}


def test_all_nine_grahas_present():
    assert GRAHA_NAMES == ['Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
                           'Shukra', 'Shani', 'Rahu', 'Ketu']
    assert list(_positions().keys()) == GRAHA_NAMES


def test_rasis_match_dp_2026_06_11():
    p = _positions()
    assert p['Surya']['rasi'] == 'Vrishabha'
    assert p['Chandra']['rasi'] == 'Meena'      # Revati at sunrise
    assert p['Kuja']['rasi'] == 'Mesha'
    assert p['Budha']['rasi'] == 'Mithuna'
    assert p['Guru']['rasi'] == 'Karka'
    assert p['Shukra']['rasi'] == 'Karka'
    assert p['Shani']['rasi'] == 'Meena'
    assert p['Rahu']['rasi'] == 'Kumbha'
    assert p['Ketu']['rasi'] == 'Simha'


def test_nakshatras_match_dp():
    p = _positions()
    assert p['Surya']['nakshatra'] == 'Mrigashira'
    assert p['Chandra']['nakshatra'] == 'Revati'
    assert p['Kuja']['nakshatra'] == 'Bharani'
    assert p['Shani']['nakshatra'] == 'Revati'
    assert p['Rahu']['nakshatra'] == 'Shatabhisha'


def test_retrograde_flags():
    p = _positions()
    # nodes are perpetually retrograde; no major graha was retro that day
    assert p['Rahu']['retrograde'] is True
    assert p['Ketu']['retrograde'] is True
    for g in ('Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani'):
        assert p[g]['retrograde'] is False


def test_next_ingress_sun_matches_sankramanam():
    p = _positions()
    # The drik engine puts Mithuna sankramanam on 2026-06-15 (DP-verified)
    assert p['Surya']['next_rasi'] == 'Mithuna'
    assert p['Surya']['rasi_until'] == '2026-06-15'


def test_next_ingress_moon_within_three_days():
    p = _positions()
    until = date.fromisoformat(p['Chandra']['rasi_until'])
    assert date(2026, 6, 11) <= until <= date(2026, 6, 14)
    assert p['Chandra']['next_rasi'] == 'Mesha'


def test_next_ingress_respects_retrograde_direction():
    p = _positions()
    # Rahu moves backwards: from Kumbha it enters Makara next
    assert p['Rahu']['next_rasi'] == 'Makara'


def test_longitudes_in_range_and_ketu_opposite():
    p = _positions()
    for g in p.values():
        assert 0.0 <= g['longitude'] < 360.0
    diff = abs((p['Rahu']['longitude'] - p['Ketu']['longitude']) % 360.0 - 180.0)
    assert diff < 1e-6


# --- MCP tool ---

def test_mcp_get_graha_positions():
    import json

    from telugu_panchangam.mcp.tools import tool_get_graha_positions
    result = json.loads(tool_get_graha_positions('2026-06-11', 'Hyderabad'))
    assert result['date'] == '2026-06-11'
    assert len(result['grahas']) == 9
    shani = next(g for g in result['grahas'] if g['graha'] == 'Shani')
    assert shani['rasi'] == 'Meena'
    assert shani['nakshatra'] == 'Revati'
    assert 'rasi_until' in shani
    assert 'retrograde' in shani


def test_mcp_get_graha_positions_validates():
    import json

    from telugu_panchangam.mcp.tools import tool_get_graha_positions
    assert 'error' in json.loads(tool_get_graha_positions('11-06-2026', 'Hyderabad'))
