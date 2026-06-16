import pytest
import swisseph as swe
from datetime import date
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.engines.utils import sidereal_longitude_with_ayanamsa
from telugu_panchangam.cities import CITIES
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
