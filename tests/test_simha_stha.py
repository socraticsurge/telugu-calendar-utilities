"""Tests for Simha-Stha Guru / Shukra flags.

Jupiter (Guru) enters Simha rasi (sidereal Lahiri) around August 2026
and remains until approximately August 2027. Venus (Shukra) transits
Simha for roughly a month every ~19 months.

All flag correctness is checked via type assertions; value assertions
are made only where the ephemeris date is known-good.
"""
import json
from datetime import date, timedelta

import pytest

from telugu_panchangam.gochara.simha_stha import is_simha_stha
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.cities import CITIES


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


# ---------------------------------------------------------------------------
# Unit tests for simha_stha.py
# ---------------------------------------------------------------------------

def test_is_simha_stha():
    assert is_simha_stha('Simha') is True
    assert is_simha_stha('Mesha') is False
    assert is_simha_stha(None) is False


def test_is_simha_stha_all_other_rasis():
    other = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka',
             'Kanya', 'Tula', 'Vrischika', 'Dhanu',
             'Makara', 'Kumbha', 'Meena']
    for rasi in other:
        assert is_simha_stha(rasi) is False, f'Expected False for {rasi}'


# ---------------------------------------------------------------------------
# Drik engine populates both flags as booleans
# ---------------------------------------------------------------------------

def test_drik_populates_both_flags():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert isinstance(day.simha_stha_guru, bool)
    assert isinstance(day.simha_stha_shukra, bool)


# ---------------------------------------------------------------------------
# SS and Vakya leave flags as False (no outer-planet modelling)
# ---------------------------------------------------------------------------

def test_ss_defaults_false():
    """SS engine doesn't model outer planets; flags remain False."""
    eng = SuryaSiddhantaEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.simha_stha_guru is False
    assert day.simha_stha_shukra is False


def test_vakya_defaults_false():
    """Vakya engine doesn't model outer planets; flags remain False."""
    from telugu_panchangam.engines.vakya import VakyaEngine
    eng = VakyaEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.simha_stha_guru is False
    assert day.simha_stha_shukra is False


# ---------------------------------------------------------------------------
# MCP tool serialization
# ---------------------------------------------------------------------------

def test_flags_in_all_mcp_tool_responses():
    from telugu_panchangam.mcp.tools import (
        tool_get_panchangam, tool_get_muhurta, tool_get_panchangam_range,
    )
    test_date = '2026-06-11'

    out1 = json.loads(tool_get_panchangam(test_date, city='Hyderabad'))
    assert 'simha_stha_guru' in out1, 'tool_get_panchangam missing simha_stha_guru'
    assert 'simha_stha_shukra' in out1, 'tool_get_panchangam missing simha_stha_shukra'

    out2 = json.loads(tool_get_muhurta(test_date, city='Hyderabad'))
    assert 'simha_stha_guru' in out2, 'tool_get_muhurta missing simha_stha_guru'
    assert 'simha_stha_shukra' in out2, 'tool_get_muhurta missing simha_stha_shukra'

    out3 = json.loads(tool_get_panchangam_range(test_date, test_date, city='Hyderabad'))
    day0 = out3['days'][0]
    assert 'simha_stha_guru' in day0, 'tool_get_panchangam_range day missing simha_stha_guru'
    assert 'simha_stha_shukra' in day0, 'tool_get_panchangam_range day missing simha_stha_shukra'


# ---------------------------------------------------------------------------
# Jupiter-in-Simha period: Dec 2026 should be Simha-Stha Guru
# (sidereal Lahiri: Jupiter enters Simha ~Aug 2026, exits ~Aug 2027)
# ---------------------------------------------------------------------------

def test_jupiter_in_simha_dec_2026():
    """Jupiter is in Simha rasi on 2026-12-01 (sidereal Lahiri)."""
    eng = DrikEngine()
    day = eng.calculate(date(2026, 12, 1), _hyderabad())
    assert isinstance(day.simha_stha_guru, bool)
    # Jupiter is known to be in Simha in this period.
    assert day.simha_stha_guru is True, (
        'Expected simha_stha_guru=True on 2026-12-01; '
        'got False — verify Jupiter rasi in ephemeris'
    )


# ---------------------------------------------------------------------------
# Muhurta: wedding hard-skips on Simha-Stha Guru days
# ---------------------------------------------------------------------------

def test_wedding_activity_skips_simha_stha_guru():
    """When simha_stha_guru is True, wedding activity returns no slots."""
    from telugu_panchangam.personal.muhurta import day_slots, diagnose_day
    eng = DrikEngine()
    city = _hyderabad()
    found = False
    for delta in range(0, 365):
        target = date(2026, 6, 1) + timedelta(days=delta)
        day = eng.calculate(target, city)
        if not day.simha_stha_guru:
            continue
        found = True
        slots = day_slots(day, activity='wedding')
        assert len(slots) == 0, (
            f'Expected 0 wedding slots on Simha-Stha Guru day {target}; '
            f'got {len(slots)}'
        )
        reason = diagnose_day(day, activity='wedding')
        assert reason is not None
        assert 'Simha-Stha Guru' in reason
        break
    if not found:
        pytest.skip('No Simha-Stha Guru day found in scan range; skipping scoring path test')


def test_wedding_diagnose_simha_stha_guru():
    """diagnose_day explains the Simha-Stha Guru skip for weddings."""
    from telugu_panchangam.personal.muhurta import diagnose_day
    # Use a known Simha-Stha Guru date
    eng = DrikEngine()
    day = eng.calculate(date(2026, 12, 1), _hyderabad())
    if not day.simha_stha_guru:
        pytest.skip('2026-12-01 is not Simha-Stha Guru; verify ephemeris')
    reason = diagnose_day(day, activity='wedding')
    assert reason is not None
    assert 'Simha-Stha Guru' in reason


# ---------------------------------------------------------------------------
# Muhurta: Simha-Stha Shukra applies -2 penalty (not a hard skip)
# ---------------------------------------------------------------------------

def test_simha_stha_shukra_penalty_in_reasons():
    """When simha_stha_shukra is True for wedding, penalty appears in reasons."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikEngine()
    city = _hyderabad()
    found = False
    # Scan for a Shukra-in-Simha day (Venus transits ~1 month each cycle)
    for delta in range(0, 730):
        target = date(2026, 1, 1) + timedelta(days=delta)
        day = eng.calculate(target, city)
        if not day.simha_stha_shukra:
            continue
        # Must not also be Guru Simha-Stha (that would hard-skip)
        if day.simha_stha_guru:
            continue
        # Must not be eclipse / khar-maasa / etc. that would drop the day
        found = True
        slots = day_slots(day, activity='wedding')
        if slots:
            # At least one slot should mention the Shukra penalty
            all_reasons = [r for s in slots for r in s.get('reasons', [])]
            shukra_mentions = [r for r in all_reasons if 'Simha-Stha Shukra' in r]
            assert shukra_mentions, (
                f'Expected Shukra penalty reason on {target}; '
                f'reasons were: {all_reasons[:5]}'
            )
        break
    if not found:
        pytest.skip('No Shukra-in-Simha day (without Guru conflict) found in scan; skipping')


# ---------------------------------------------------------------------------
# Non-wedding activities are NOT skipped by Simha-Stha Guru
# ---------------------------------------------------------------------------

def test_non_wedding_not_blocked_by_simha_stha_guru():
    """The Simha-Stha Guru hard-skip only applies to wedding, not generic activities."""
    from telugu_panchangam.personal.muhurta import diagnose_day
    eng = DrikEngine()
    day = eng.calculate(date(2026, 12, 1), _hyderabad())
    if not day.simha_stha_guru:
        pytest.skip('2026-12-01 is not Simha-Stha Guru; verify ephemeris')
    reason_any = diagnose_day(day, activity='any')
    assert reason_any is None or 'Simha-Stha Guru' not in reason_any

    reason_travel = diagnose_day(day, activity='travel')
    assert reason_travel is None or 'Simha-Stha Guru' not in reason_travel
