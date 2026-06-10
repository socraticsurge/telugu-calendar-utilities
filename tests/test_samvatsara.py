from datetime import date

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.base import SAMVATSARA_NAMES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.generate import default_feed_window

HYD = next(c for c in CITIES if c.name == 'Hyderabad')

# (date, expected samvatsara) — well-known anchor years
KNOWN_YEARS = [
    (date(2014, 6, 10), 'Jaya'),
    (date(2024, 6, 10), 'Krodhi'),
    (date(2025, 6, 10), 'Vishvavasu'),
    (date(2026, 6, 10), 'Parabhava'),
    (date(1987, 6, 10), 'Prabhava'),
    # year flips at Ugadi, not at the Gregorian new year
    (date(2026, 1, 10), 'Vishvavasu'),
]


def test_samvatsara_names_are_unique():
    assert len(SAMVATSARA_NAMES) == 60
    assert len(set(SAMVATSARA_NAMES)) == 60


@pytest.mark.parametrize('engine', [DrikGanitaEngine(), SuryaSiddhantaEngine(), VakyaEngine()],
                         ids=['drik', 'surya_siddhanta', 'vakya'])
@pytest.mark.parametrize('d,expected', KNOWN_YEARS, ids=lambda v: str(v))
def test_samvatsara_known_years(engine, d, expected):
    result = engine.calculate(d, HYD, include_eclipse=False)
    assert result.samvatsara == expected


def test_samvatsara_flips_at_ugadi_2026():
    """Ugadi 2026 is March 19: Vishvavasu before, Parabhava after."""
    engine = DrikGanitaEngine()
    before = engine.calculate(date(2026, 3, 15), HYD, include_eclipse=False)
    after = engine.calculate(date(2026, 3, 25), HYD, include_eclipse=False)
    assert before.samvatsara == 'Vishvavasu'
    assert after.samvatsara == 'Parabhava'


@pytest.mark.parametrize('today,expected_end', [
    (date(2026, 1, 15), date(2027, 6, 30)),
    (date(2026, 6, 15), date(2027, 11, 30)),
    (date(2026, 7, 15), date(2027, 12, 31)),   # was off by a year for July
    (date(2026, 8, 15), date(2028, 1, 31)),
    (date(2026, 12, 15), date(2028, 5, 31)),
])
def test_default_feed_window(today, expected_end):
    start, end = default_feed_window(today)
    assert start == date(today.year, today.month, 1)
    assert end == expected_end
