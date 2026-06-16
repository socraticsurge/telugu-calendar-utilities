"""Forward-year DP-verified festival regression (2027-2028).

Pins the Drik engine's festival output for 5 anchor festivals × 3 cities
against drikpanchang.com day-page values. Locks current behaviour so any
future engine change must justify any diff against DP.

Per project memory `verify-against-drikpanchang.md`:
  - Every cell records a DP day-page URL + screenshot date.
  - Tolerances: sunrise/sunset < 60 seconds, anga-end < 120 seconds.
  - A failure is a signal to investigate, not necessarily a bug — DP may
    update its own algorithms; engine changes may also be intentional.

**Fixture contract (all fields REQUIRED on every cell):**
  expected.{date, weekday, maasam, paksham,
            tithi_name, tithi_ends_ist,
            nakshatra_name, nakshatra_ends_ist,
            yoga_ends_ist,
            sunrise_ist, sunset_ist,
            deciding_moment}
  dp_source.{festival_page, day_page, screenshot_dated, screenshot_notes}

If a future cell can't supply one of these from DP, that cell isn't ready
to land — fix the data, don't soften the test.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest
import pytz

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'forward_year_festivals.json'
IST = pytz.timezone('Asia/Kolkata')

with FIXTURE_PATH.open() as f:
    FIXTURE = json.load(f)

CELLS = FIXTURE['cells']
TOL_SUN = FIXTURE['tolerances']['sunrise_sunset_seconds']
TOL_ANGA = FIXTURE['tolerances']['anga_end_seconds']
CITIES_BY_NAME = {c.name: c for c in CITIES}


def _ist(s: str) -> datetime:
    """Parse 'YYYY-MM-DDTHH:MM' (or '...HH:MM:SS') as IST tz-aware datetime."""
    return IST.localize(datetime.fromisoformat(s))


def _cell_id(cell: dict) -> str:
    return f"{cell['festival'].replace(' ', '_')}-{cell['city']}-{cell['year']}"


@pytest.fixture(params=CELLS, ids=_cell_id)
def cell(request):
    return request.param


@pytest.fixture
def panchangam_day(cell):
    """Compute the engine's PanchangamDay for this cell's date+city.
    Shared across all per-cell tests so we only call calculate() once per cell."""
    engine = DrikGanitaEngine()
    location = CITIES_BY_NAME[cell['city']]
    target_date = date.fromisoformat(cell['expected']['date'])
    return engine.calculate(target_date, location)


def test_festival_present(cell, panchangam_day):
    """The engine's festivals list must include this festival on the expected date."""
    assert cell['festival'] in panchangam_day.festivals, (
        f"Expected {cell['festival']!r} in engine festivals {panchangam_day.festivals} "
        f"for {cell['expected']['date']} {cell['city']}. "
        f"DP source: {cell['dp_source']['day_page']}"
    )


def test_weekday_match(cell, panchangam_day):
    assert panchangam_day.vaaram == cell['expected']['weekday'], (
        f"Vaaram {panchangam_day.vaaram!r} != expected {cell['expected']['weekday']!r}. "
        f"DP source: {cell['dp_source']['day_page']}"
    )


def test_maasam_match(cell, panchangam_day):
    assert panchangam_day.maasam == cell['expected']['maasam']
    assert panchangam_day.paksham == cell['expected']['paksham']


def test_tithi_name_match(cell, panchangam_day):
    assert panchangam_day.tithi.name == cell['expected']['tithi_name'], (
        f"Tithi {panchangam_day.tithi.name!r} != expected {cell['expected']['tithi_name']!r}. "
        f"DP source: {cell['dp_source']['day_page']}"
    )


def test_sunrise_within_tolerance(cell, panchangam_day):
    expected = _ist(cell['expected']['sunrise_ist'])
    actual = panchangam_day.sunrise.astimezone(IST)
    delta = abs((actual - expected).total_seconds())
    assert delta <= TOL_SUN, (
        f"Sunrise {actual.strftime('%H:%M:%S')} IST differs from DP "
        f"{expected.strftime('%H:%M:%S')} IST by {delta:.0f}s (tolerance {TOL_SUN}s). "
        f"Source: {cell['dp_source']['day_page']}"
    )


def test_sunset_within_tolerance(cell, panchangam_day):
    expected = _ist(cell['expected']['sunset_ist'])
    actual = panchangam_day.sunset.astimezone(IST)
    delta = abs((actual - expected).total_seconds())
    assert delta <= TOL_SUN, (
        f"Sunset {actual.strftime('%H:%M:%S')} IST differs from DP "
        f"{expected.strftime('%H:%M:%S')} IST by {delta:.0f}s (tolerance {TOL_SUN}s). "
        f"Source: {cell['dp_source']['day_page']}"
    )


def test_tithi_end_within_tolerance(cell, panchangam_day):
    expected = _ist(cell['expected']['tithi_ends_ist'])
    actual = panchangam_day.tithi.end.astimezone(IST)
    delta = abs((actual - expected).total_seconds())
    assert delta <= TOL_ANGA, (
        f"Tithi end {actual.strftime('%H:%M:%S')} IST differs from DP "
        f"{expected.strftime('%H:%M:%S')} IST by {delta:.0f}s (tolerance {TOL_ANGA}s). "
        f"Source: {cell['dp_source']['day_page']}"
    )


def test_nakshatra_name_match(cell, panchangam_day):
    assert panchangam_day.nakshatra.name == cell['expected']['nakshatra_name'], (
        f"Nakshatra {panchangam_day.nakshatra.name!r} != expected "
        f"{cell['expected']['nakshatra_name']!r}. "
        f"DP source: {cell['dp_source']['day_page']}"
    )


def test_nakshatra_end_within_tolerance(cell, panchangam_day):
    expected = _ist(cell['expected']['nakshatra_ends_ist'])
    actual = panchangam_day.nakshatra.end.astimezone(IST)
    delta = abs((actual - expected).total_seconds())
    assert delta <= TOL_ANGA, (
        f"Nakshatra end {actual.strftime('%H:%M:%S')} IST differs from DP "
        f"{expected.strftime('%H:%M:%S')} IST by {delta:.0f}s (tolerance {TOL_ANGA}s). "
        f"Source: {cell['dp_source']['day_page']}"
    )


def test_yoga_end_within_tolerance(cell, panchangam_day):
    expected = _ist(cell['expected']['yoga_ends_ist'])
    actual = panchangam_day.yoga.end.astimezone(IST)
    delta = abs((actual - expected).total_seconds())
    assert delta <= TOL_ANGA, (
        f"Yoga end {actual.strftime('%H:%M:%S')} IST differs from DP "
        f"{expected.strftime('%H:%M:%S')} IST by {delta:.0f}s (tolerance {TOL_ANGA}s). "
        f"Source: {cell['dp_source']['day_page']}"
    )
