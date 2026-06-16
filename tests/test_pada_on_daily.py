from datetime import date
from telugu_panchangam.engines.drik import DrikGanitaEngine as DrikEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.cities import CITIES


def _hyderabad():
    return next(c for c in CITIES if c.name == 'Hyderabad')


def test_pada_is_1_to_4_drik():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.nakshatra_pada in (1, 2, 3, 4)


def test_pada_is_1_to_4_surya_siddhanta():
    eng = SuryaSiddhantaEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.nakshatra_pada in (1, 2, 3, 4)


def test_pada_is_1_to_4_vakya():
    eng = VakyaEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.nakshatra_pada in (1, 2, 3, 4)


def test_pada_consistent_with_graha_positions_moon():
    # Cross-check Drik's daily pada against gochara/positions Moon pada
    # — same astronomical computation, same sunrise.
    from telugu_panchangam.gochara.positions import graha_positions
    from telugu_panchangam.engines.utils import get_sunrise, local_midnight_jd

    loc = _hyderabad()
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), loc)
    jd_sr = get_sunrise(local_midnight_jd(date(2026, 6, 11), loc.timezone),
                        [loc.lon, loc.lat, 0.0])
    grahas = graha_positions(jd_sr)
    moon = next(g for g in grahas if g['graha'] == 'Chandra')
    assert day.nakshatra_pada == moon['pada']


def test_pada_in_mcp_output():
    # tool_get_panchangam returns a flat dict — no 'day' wrapper.
    import json
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    out = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    # nakshatra_pada surfaces alongside the existing nakshatra serialization;
    # exact placement is implementation choice (top-level or under
    # pancha_anga) — but it MUST be present and in range 1..4.
    pada = out.get('nakshatra_pada') or out.get('pancha_anga', {}).get('nakshatra_pada')
    assert pada in (1, 2, 3, 4), f"nakshatra_pada missing or invalid: {pada}"
