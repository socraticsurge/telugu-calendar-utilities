"""Tests for Khar-Maasa flag (Sun in Dhanu or Meena).

Sidereal (Lahiri) solar sign boundaries verified with drikpanchang.com:
  - Dhanur Maasa 2026: Sun enters Dhanu ~17 Dec 2026
  - Meena Maasa 2027: Sun enters Meena ~16 Mar 2027
"""
import json
from datetime import date

import pytest

from telugu_panchangam.maasa_filters import KHAR_MAASA_SIGNS, khar_maasa_name
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.cities import CITIES


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


# ---------------------------------------------------------------------------
# Unit tests for maasa_filters.py
# ---------------------------------------------------------------------------

def test_khar_maasa_signs_set():
    assert KHAR_MAASA_SIGNS == {'Dhanu', 'Meena'}


def test_khar_maasa_name_dhanu():
    assert khar_maasa_name('Dhanu') == 'Dhanur'


def test_khar_maasa_name_meena():
    assert khar_maasa_name('Meena') == 'Meena'


def test_khar_maasa_name_other():
    for sign in ('Mesha', 'Vrishabha', 'Mithuna', 'Karka',
                 'Simha', 'Kanya', 'Tula', 'Vrischika',
                 'Makara', 'Kumbha'):
        assert khar_maasa_name(sign) is None, f'Expected None for {sign}'


def test_khar_maasa_name_none():
    assert khar_maasa_name(None) is None


# ---------------------------------------------------------------------------
# Engine flag tests (Drik)
# ---------------------------------------------------------------------------

def test_dhanur_maasa_december_2026():
    """Mid-Dhanur-Maasa: 2026-12-20 is in Dhanu (sidereal)."""
    eng = DrikEngine()
    city = _hyderabad()
    day = eng.calculate(date(2026, 12, 20), city)
    assert day.solar_sign == 'Dhanu'
    assert day.is_khar_maasa is True
    assert day.khar_maasa_name == 'Dhanur'


def test_meena_maasa_march_2027():
    """Mid-Meena-Maasa: 2027-03-20 is in Meena (sidereal)."""
    eng = DrikEngine()
    city = _hyderabad()
    day = eng.calculate(date(2027, 3, 20), city)
    assert day.solar_sign == 'Meena'
    assert day.is_khar_maasa is True
    assert day.khar_maasa_name == 'Meena'


def test_non_khar_maasa_october_2026():
    """October 2026 is not Khar-Maasa (Sun in Kanya/Tula)."""
    eng = DrikEngine()
    city = _hyderabad()
    day = eng.calculate(date(2026, 10, 15), city)
    assert day.is_khar_maasa is False
    assert day.khar_maasa_name is None


# ---------------------------------------------------------------------------
# All 3 engines set the flag consistently
# ---------------------------------------------------------------------------

def test_flag_in_all_three_engines():
    """SS and Vakya engines also populate is_khar_maasa and khar_maasa_name."""
    from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
    from telugu_panchangam.engines.vakya import VakyaEngine
    city = _hyderabad()
    # Dhanur Maasa date that all three engines should agree on
    test_date = date(2026, 12, 20)
    for EngClass in (SuryaSiddhantaEngine, VakyaEngine):
        eng = EngClass()
        day = eng.calculate(test_date, city)
        # All sidereal engines use the same RASHI_NAMES; Sun in Dhanu on this date.
        assert day.is_khar_maasa is True, (
            f'{EngClass.__name__}: expected is_khar_maasa=True on {test_date}, '
            f'solar_sign={day.solar_sign}'
        )
        assert day.khar_maasa_name == 'Dhanur', (
            f'{EngClass.__name__}: expected khar_maasa_name=Dhanur, '
            f'got {day.khar_maasa_name!r}'
        )


# ---------------------------------------------------------------------------
# MCP serialization
# ---------------------------------------------------------------------------

def test_khar_maasa_fields_in_all_mcp_paths():
    """Both is_khar_maasa and khar_maasa_name are present in all 3 MCP tools."""
    from telugu_panchangam.mcp.tools import (
        tool_get_panchangam,
        tool_get_muhurta,
        tool_get_panchangam_range,
    )
    # Use a Khar-Maasa date so both fields have non-trivial values
    khar_date = '2026-12-20'

    out1 = json.loads(tool_get_panchangam(khar_date, city='Hyderabad'))
    assert 'is_khar_maasa' in out1, 'tool_get_panchangam missing is_khar_maasa'
    assert 'khar_maasa_name' in out1, 'tool_get_panchangam missing khar_maasa_name'
    assert out1['is_khar_maasa'] is True
    assert out1['khar_maasa_name'] == 'Dhanur'

    out2 = json.loads(tool_get_muhurta(khar_date, city='Hyderabad'))
    assert 'is_khar_maasa' in out2, 'tool_get_muhurta missing is_khar_maasa'
    assert 'khar_maasa_name' in out2, 'tool_get_muhurta missing khar_maasa_name'
    assert out2['is_khar_maasa'] is True
    assert out2['khar_maasa_name'] == 'Dhanur'

    out3 = json.loads(tool_get_panchangam_range(khar_date, khar_date, city='Hyderabad'))
    day0 = out3['days'][0]
    assert 'is_khar_maasa' in day0, 'tool_get_panchangam_range missing is_khar_maasa'
    assert 'khar_maasa_name' in day0, 'tool_get_panchangam_range missing khar_maasa_name'
    assert day0['is_khar_maasa'] is True
    assert day0['khar_maasa_name'] == 'Dhanur'


def test_mcp_non_khar_maasa_fields_are_false_and_none():
    """On a non-Khar-Maasa date, is_khar_maasa=False and khar_maasa_name=null."""
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    out = json.loads(tool_get_panchangam('2026-10-15', city='Hyderabad'))
    assert out['is_khar_maasa'] is False
    assert out['khar_maasa_name'] is None


# ---------------------------------------------------------------------------
# Muhurta consumption: samskara activities skip Khar-Maasa days
# ---------------------------------------------------------------------------

def test_wedding_skipped_during_khar_maasa():
    """Wedding activity returns [] on a Khar-Maasa day."""
    from telugu_panchangam.personal.muhurta import day_slots, diagnose_day
    eng = DrikEngine()
    city = _hyderabad()
    day = eng.calculate(date(2026, 12, 20), city)
    assert day.is_khar_maasa

    slots = day_slots(day, activity='wedding')
    assert slots == [], (
        f'Expected no wedding slots during Khar-Maasa; got {len(slots)}'
    )

    reason = diagnose_day(day, activity='wedding')
    assert reason is not None
    assert 'Khar-Maasa' in reason


def test_samskara_activities_skip_khar_maasa():
    """All samskara activities with skip_on_khar_maasa=True return [] on Khar-Maasa."""
    from telugu_panchangam.personal.muhurta import ACTIVITY_RULES, day_slots
    eng = DrikEngine()
    city = _hyderabad()
    day = eng.calculate(date(2026, 12, 20), city)
    assert day.is_khar_maasa

    khar_skip_activities = [
        act for act, rules in ACTIVITY_RULES.items()
        if rules.get('skip_on_khar_maasa')
    ]
    assert len(khar_skip_activities) > 0, 'No activities found with skip_on_khar_maasa'

    for activity in khar_skip_activities:
        slots = day_slots(day, activity=activity)
        assert slots == [], (
            f'Activity {activity!r}: expected 0 slots on Khar-Maasa day; '
            f'got {len(slots)}'
        )


def test_non_samskara_not_skipped_during_khar_maasa():
    """Generic/travel activities are NOT blocked by Khar-Maasa."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikEngine()
    city = _hyderabad()
    day = eng.calculate(date(2026, 12, 20), city)
    assert day.is_khar_maasa

    # 'any' and 'travel' have no skip_on_khar_maasa — should still produce slots
    # (eclipse or all-bad-choghadiya could theoretically give 0, but Dec 2026
    # is an ordinary day; we just assert the Khar-Maasa rule is NOT the cause).
    from telugu_panchangam.personal.muhurta import diagnose_day
    reason = diagnose_day(day, activity='any')
    assert reason is None or 'Khar-Maasa' not in reason

    reason_travel = diagnose_day(day, activity='travel')
    assert reason_travel is None or 'Khar-Maasa' not in reason_travel
