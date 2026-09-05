from datetime import date, timedelta

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.gochara.combustion import COMBUSTION_THRESHOLDS, compute_maudhya


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


def test_thresholds_known():
    assert COMBUSTION_THRESHOLDS['Guru'] == 11.0
    assert COMBUSTION_THRESHOLDS['Shukra'] == 10.0


def test_compute_maudhya_combust():
    info = compute_maudhya('Guru', sun_long=100.0, planet_long=105.0)
    assert info.graha == 'Guru'
    assert info.threshold_deg == 11.0
    assert abs(info.elongation_deg - 5.0) < 1e-9
    assert info.combust is True


def test_compute_maudhya_not_combust():
    info = compute_maudhya('Shukra', sun_long=100.0, planet_long=140.0)
    assert info.combust is False
    assert abs(info.elongation_deg - 40.0) < 1e-9


def test_compute_maudhya_wraparound():
    # Sun at 355°, planet at 5° → 10° elongation
    info = compute_maudhya('Guru', sun_long=355.0, planet_long=5.0)
    assert abs(info.elongation_deg - 10.0) < 1e-9
    assert info.combust is True  # 10 < 11


def test_drik_populates_both_maudhya():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.guru_maudhya is not None
    assert day.shukra_maudhya is not None
    assert day.guru_maudhya.graha == 'Guru'
    assert day.shukra_maudhya.graha == 'Shukra'
    assert 0.0 <= day.guru_maudhya.elongation_deg <= 180.0


def test_ss_vakya_maudhya_none():
    """SS/Vakya don't model outer planets; both fields remain None."""
    eng = SuryaSiddhantaEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.guru_maudhya is None
    assert day.shukra_maudhya is None


def test_maudhya_in_all_mcp_tool_responses():
    import json

    from telugu_panchangam.mcp.tools import (
        tool_get_muhurta,
        tool_get_panchangam,
        tool_get_panchangam_range,
    )
    out1 = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'guru_maudhya' in out1
    assert 'shukra_maudhya' in out1

    out2 = json.loads(tool_get_muhurta('2026-06-11', city='Hyderabad'))
    assert 'guru_maudhya' in out2

    out3 = json.loads(tool_get_panchangam_range('2026-06-11', '2026-06-12', city='Hyderabad'))
    assert 'guru_maudhya' in out3['days'][0]


def test_wedding_skips_combust_guru():
    """When Guru is combust, the wedding activity drops the day."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikEngine()
    city = _hyderabad()
    for d in range(0, 365):
        target = date(2026, 6, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.guru_maudhya is None or not day.guru_maudhya.combust:
            continue
        slots = day_slots(day, activity='wedding')
        assert len(slots) == 0
        return
    pytest.skip('No Guru-combust day in 365-day scan')


def test_wedding_skips_combust_shukra():
    """When Shukra is combust, the wedding activity drops the day."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikEngine()
    city = _hyderabad()
    for d in range(0, 365):
        target = date(2026, 6, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.shukra_maudhya is None or not day.shukra_maudhya.combust:
            continue
        slots = day_slots(day, activity='wedding')
        assert len(slots) == 0
        return
    pytest.skip('No Shukra-combust day in 365-day scan')
