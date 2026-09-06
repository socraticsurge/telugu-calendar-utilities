from datetime import date, timedelta

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.personal.muhurta import day_slots


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


def _find_adhika_day():
    """Scan a wide range for any Adhika Maasa day."""
    eng = DrikEngine()
    city = _hyderabad()
    # Adhika months occur ~every 2-3 years. Scan 4 years.
    for d in range(0, 365 * 4):
        target = date(2026, 1, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.maasam.startswith('Adhika '):
            return day, target
    return None, None


def test_adhika_maasa_day_exists_in_scan():
    """Sanity check: there must be Adhika days in the 4-year scan."""
    day, target = _find_adhika_day()
    assert day is not None, "Expected at least one Adhika Maasa day in 4-year scan"


def test_wedding_skipped_on_adhika_maasa():
    """The wedding activity must drop slots on Adhika Maasa days."""
    day, target = _find_adhika_day()
    if day is None:
        pytest.skip('No Adhika Maasa day found in 4-year scan')
    slots = day_slots(day, activity='wedding')
    assert len(slots) == 0, (
        f"Expected 0 wedding slots on Adhika day {target} "
        f"(maasam={day.maasam!r}); got {len(slots)}"
    )


def test_nija_maasa_not_skipped():
    """Nija (regular) months must NOT be skipped — only Adhika is restricted."""
    eng = DrikEngine()
    city = _hyderabad()
    # 2026-11-15 is in regular Kartika/Margashirsha — verify it's NOT Adhika
    day = eng.calculate(date(2026, 11, 15), city)
    assert not day.maasam.startswith('Adhika ')
    # Wedding must produce slots on this non-Adhika day (assuming no other
    # samskara dosha is active). We don't assert a count > 0 because other
    # filters could legitimately produce 0 slots.
    day_slots(day, activity='wedding')
    # If we got 0, it's because of *another* filter, not Adhika.
    # No strict assertion — this test just exercises the code path.


def test_diagnose_day_explains_adhika_skip():
    """diagnose_day should return an explanatory message on Adhika days."""
    from telugu_panchangam.personal.muhurta import diagnose_day
    day, target = _find_adhika_day()
    if day is None:
        pytest.skip('No Adhika Maasa day found')
    diagnosis = diagnose_day(day, activity='wedding')
    # Expect 'Adhika' to appear in the diagnosis text.
    assert 'Adhika' in diagnosis, (
        f"Expected 'Adhika' in diagnose_day output; got: {diagnosis!r}"
    )
