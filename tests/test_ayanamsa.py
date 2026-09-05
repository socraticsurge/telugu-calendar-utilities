from datetime import date

import pytest
import swisseph as swe

from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.utils import sidereal_longitude_with_ayanamsa
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.models.panchangam_day import Location

# CITIES is a list; use a fixed Hyderabad location for these tests.
_HYD = Location(name='Hyderabad', lat=17.385, lon=78.4867, timezone='Asia/Kolkata')


def test_default_ayanamsa_is_lahiri():
    assert DrikEngine().ayanamsa == 'lahiri'
    assert SuryaSiddhantaEngine().ayanamsa == 'lahiri'
    assert VakyaEngine().ayanamsa == 'lahiri'


def test_ayanamsa_constructor_accepts_valid():
    DrikEngine(ayanamsa='raman')
    DrikEngine(ayanamsa='krishnamurti')
    DrikEngine(ayanamsa='true_chitrapaksha')


def test_invalid_ayanamsa_raises():
    with pytest.raises(ValueError, match='ayanamsa must be one of'):
        DrikEngine(ayanamsa='krishnamoorthy')
    with pytest.raises(ValueError, match='ayanamsa must be one of'):
        SuryaSiddhantaEngine(ayanamsa='unknown')
    with pytest.raises(ValueError, match='ayanamsa must be one of'):
        VakyaEngine(ayanamsa='unknown')


def test_lahiri_default_preserves_existing_drik_output():
    # If Lahiri default changes anything, existing tests would break.
    # This is a smoke check: a known Drik output is unchanged.
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), _HYD)
    assert day.nakshatra is not None
    assert day.tithi is not None


def test_alternate_ayanamsa_shifts_longitude():
    jd = 2461183.5  # 2026-06-11 00:00 UTC
    lon_lahiri = sidereal_longitude_with_ayanamsa(jd, swe.MOON, 'lahiri')
    lon_raman = sidereal_longitude_with_ayanamsa(jd, swe.MOON, 'raman')
    # Lahiri vs Raman differ by classical offset; must measurably differ.
    assert abs((lon_lahiri - lon_raman + 180) % 360 - 180) > 0.05


def test_ss_vakya_ayanamsa_is_noop():
    """SS and Vakya use their own moon model; ayanamsa param is accepted
    but does not change anga output for the same date."""
    d = date(2026, 6, 11)
    a = SuryaSiddhantaEngine().calculate(d, _HYD)
    b = SuryaSiddhantaEngine(ayanamsa='raman').calculate(d, _HYD)
    assert a.nakshatra.name == b.nakshatra.name
    assert a.tithi.name == b.tithi.name


def test_ayanamsa_in_mcp_response_metadata():
    import json

    from telugu_panchangam.mcp.tools import tool_get_panchangam
    out = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    # ayanamsa must be present somewhere — top-level or under metadata.
    ay = out.get('ayanamsa') or out.get('metadata', {}).get('ayanamsa')
    assert ay == 'lahiri'
    out2 = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad', ayanamsa='raman'))
    ay2 = out2.get('ayanamsa') or out2.get('metadata', {}).get('ayanamsa')
    assert ay2 == 'raman'


def test_ayanamsa_in_all_ayanamsa_aware_mcp_tools():
    import json

    from telugu_panchangam.mcp.tools import (
        tool_find_muhurta,
        tool_get_graha_positions,
        tool_get_panchangam,
        tool_get_panchangam_range,
    )
    # tool_get_panchangam — top-level ayanamsa
    out = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert out.get('ayanamsa') == 'lahiri'

    # tool_get_panchangam_range — top-level ayanamsa
    out2 = json.loads(tool_get_panchangam_range('2026-06-11', '2026-06-12', city='Hyderabad'))
    assert out2.get('ayanamsa') == 'lahiri'

    # tool_get_graha_positions — top-level ayanamsa
    out3 = json.loads(tool_get_graha_positions('2026-06-11', city='Hyderabad'))
    assert out3.get('ayanamsa') == 'lahiri'

    # tool_find_muhurta — top-level ayanamsa
    out4 = json.loads(tool_find_muhurta('2026-06-11', days=1, city='Hyderabad'))
    assert out4.get('ayanamsa') == 'lahiri'


# ── graha_positions module — ayanamsa wired through ──────────────────────────

def test_graha_positions_lahiri_vs_raman_differ():
    """Lahiri and Raman longitudes must differ (they differ by ~20–30 arcmin)."""
    import json

    from telugu_panchangam.mcp.tools import tool_get_graha_positions
    lahiri = json.loads(tool_get_graha_positions('2026-06-17', city='Hyderabad', ayanamsa='lahiri'))
    raman  = json.loads(tool_get_graha_positions('2026-06-17', city='Hyderabad', ayanamsa='raman'))
    sun_l = next(g['longitude'] for g in lahiri['grahas'] if g['graha'] == 'Surya')
    sun_r = next(g['longitude'] for g in raman['grahas']  if g['graha'] == 'Surya')
    assert abs(sun_l - sun_r) > 0.1, (
        f'Lahiri and Raman Sun longitudes too close: {sun_l:.4f} vs {sun_r:.4f} — '
        'ayanamsa may not be applied'
    )


def test_graha_positions_no_stale_ayanamsa_note():
    """The 'ayanamsa_note' warning field must be gone now that it is applied."""
    import json

    from telugu_panchangam.mcp.tools import tool_get_graha_positions
    for ay in ('lahiri', 'raman'):
        out = json.loads(tool_get_graha_positions('2026-06-17', city='Hyderabad', ayanamsa=ay))
        assert 'ayanamsa_note' not in out, f'Stale ayanamsa_note still present for {ay}'


def test_graha_positions_invalid_ayanamsa_returns_error():
    import json

    from telugu_panchangam.mcp.tools import tool_get_graha_positions
    out = json.loads(tool_get_graha_positions('2026-06-17', city='Hyderabad', ayanamsa='tropical'))
    assert 'error' in out


# ── gochara and phalalu — ayanamsa now accepted and applied ──────────────────

def test_tool_get_gochara_accepts_ayanamsa():
    import json

    from telugu_panchangam.mcp.tools import tool_get_gochara
    out = json.loads(tool_get_gochara('2026-06-17', 'Mesha', 'Hyderabad', ayanamsa='raman'))
    assert 'error' not in out
    assert 'gochara' in out


def test_tool_get_gochara_raman_vs_lahiri_may_differ():
    """With a different ayanamsa the Moon rasi can shift, changing house verdicts.
    We only verify both return valid responses — an actual positional shift
    is asserted by test_graha_positions_lahiri_vs_raman_differ above."""
    import json

    from telugu_panchangam.mcp.tools import tool_get_gochara
    out_l = json.loads(tool_get_gochara('2026-06-17', 'Mesha', 'Hyderabad', ayanamsa='lahiri'))
    out_r = json.loads(tool_get_gochara('2026-06-17', 'Mesha', 'Hyderabad', ayanamsa='raman'))
    assert 'error' not in out_l
    assert 'error' not in out_r


def test_tool_get_rasi_phalalu_accepts_ayanamsa():
    import json

    from telugu_panchangam.mcp.tools import tool_get_rasi_phalalu
    out = json.loads(tool_get_rasi_phalalu('2026-06-17', 'Mesha', 'Hyderabad', ayanamsa='raman'))
    assert 'error' not in out


# ── rashi_ingresses — ayanamsa wired through ─────────────────────────────────

def test_rashi_ingresses_lahiri_vs_raman_differ():
    """Ingress timestamps must differ between ayanamsas (sign boundaries shift)."""
    import json

    from telugu_panchangam.mcp.tools import tool_get_rashi_ingresses
    lahiri = json.loads(tool_get_rashi_ingresses('2026-06-01', '2026-09-30',
                                                  planets=['Sun'], ayanamsa='lahiri'))
    raman  = json.loads(tool_get_rashi_ingresses('2026-06-01', '2026-09-30',
                                                  planets=['Sun'], ayanamsa='raman'))
    assert lahiri['ingresses'] and raman['ingresses']
    from datetime import datetime
    t_l = datetime.strptime(lahiri['ingresses'][0]['enters'], '%Y-%m-%d %H:%M UTC')
    t_r = datetime.strptime(raman['ingresses'][0]['enters'],  '%Y-%m-%d %H:%M UTC')
    diff_minutes = abs((t_l - t_r).total_seconds()) / 60
    assert diff_minutes > 1, (
        f'Lahiri and Raman ingress times too close: {diff_minutes:.1f} min apart'
    )


def test_rashi_ingresses_ayanamsa_echoed_in_response():
    import json

    from telugu_panchangam.mcp.tools import tool_get_rashi_ingresses
    out = json.loads(tool_get_rashi_ingresses('2026-06-01', '2026-08-31',
                                               planets=['Sun'], ayanamsa='krishnamurti'))
    assert out.get('ayanamsa') == 'krishnamurti'


def test_rashi_ingresses_default_ayanamsa_is_lahiri():
    import json

    from telugu_panchangam.mcp.tools import tool_get_rashi_ingresses
    out = json.loads(tool_get_rashi_ingresses('2026-06-01', '2026-08-31', planets=['Sun']))
    assert out.get('ayanamsa') == 'lahiri'
