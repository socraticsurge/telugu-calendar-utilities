"""Every supported candidate minute consumes the selected engine's public facts."""
from datetime import datetime, timedelta, timezone
from random import Random

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.generate import ENGINES
from telugu_panchangam.generators.slot_facts import build_slot_fact_table
from telugu_panchangam.personal.homa import solar_nakshatra_at

FIELDS = ['nakshatra', 'tithi', 'yoga', 'karana', 'lunar_sign', 'solar_nakshatra']
# Stable random days span the supported deployment horizon as well as known boundaries.
START = datetime(2026, 6, 1, tzinfo=timezone.utc)
SAMPLED_DATES = [(START + timedelta(days=offset)).isoformat()
                 for offset in Random(182).sample(range(550), 3)]


@pytest.mark.parametrize('system', list(ENGINES))
@pytest.mark.parametrize('city', ['Hyderabad', 'New York'])
@pytest.mark.parametrize('iso', ['2026-06-17T00:00:00+00:00', '2026-07-16T00:00:00+00:00', *SAMPLED_DATES])
def test_every_minute_matches_selected_public_engine(system, city, iso):
    engine = ENGINES[system]()
    location = next(c for c in CITIES if c.name == city)
    start = datetime.fromisoformat(iso)
    table = build_slot_fact_table(engine, system, start, start + timedelta(days=1))
    assert table['fields'] == FIELDS
    assert table['system'] == system
    assert table['stepSeconds'] == 60
    assert table['rows'][0][0] == 0
    row_index = 0
    for minute in range(1440):
        while row_index + 1 < len(table['rows']) and table['rows'][row_index + 1][0] <= minute:
            row_index += 1
        instant = start + timedelta(minutes=minute)
        facts = engine.facts_at(instant, location, vaaram='Somavaram')
        assert table['rows'][row_index][1:] == [
            *(getattr(facts, field) for field in FIELDS[:-1]),
            solar_nakshatra_at(instant, engine),
        ]


@pytest.mark.parametrize('seconds', [1, 30, 59])
def test_non_minute_generation_bounds_are_rejected(seconds):
    start = datetime(2026, 6, 17, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match='whole UTC minute'):
        build_slot_fact_table(ENGINES['drik'](), 'drik', start + timedelta(seconds=seconds), start + timedelta(days=1))


def test_vakya_discontinuity_day_is_evaluated_without_interpolation():
    # The frozen model's 3031-day correction changes at 2027-08-05 18:56:55 UTC.
    # Both candidate minutes are queried independently, never interpolated.
    engine = ENGINES['vakya']()
    start = datetime(2027, 8, 5, 18, 55, tzinfo=timezone.utc)
    location = CITIES[0]
    table = build_slot_fact_table(engine, 'vakya', start, start + timedelta(minutes=5))
    for offset in range(5):
        row = next(row for row in reversed(table['rows']) if row[0] <= offset)
        instant = start + timedelta(minutes=offset)
        facts = engine.facts_at(instant, location, vaaram='Somavaram')
        assert row[1:] == [
            *(getattr(facts, field) for field in FIELDS[:-1]),
            solar_nakshatra_at(instant, engine),
        ]


def test_feed_generation_stages_one_global_table_per_selected_system(tmp_path):
    import json
    from datetime import date

    from telugu_panchangam.generate import generate_feeds

    generate_feeds(str(tmp_path), date(2026, 6, 17), date(2026, 6, 17),
                   systems=['drik'], city_names=['Hyderabad', 'New York'])
    files = list(tmp_path.glob('*.slot-facts-v1.json'))
    assert [path.name for path in files] == ['drik.slot-facts-v1.json']
    payload = json.loads(files[0].read_text())
    assert payload['system'] == 'drik'
    assert payload['endMinute'] - payload['startMinute'] == 3 * 1440


@pytest.mark.parametrize('iso', ['2026-03-08T01:55:00', '2026-11-01T01:55:00'])
def test_aware_non_utc_bounds_are_evaluated_on_utc_minutes_across_dst(iso):
    from zoneinfo import ZoneInfo

    start = datetime.fromisoformat(iso).replace(tzinfo=ZoneInfo('America/New_York'))
    end = start + timedelta(hours=3)
    engine = ENGINES['drik']()
    assert build_slot_fact_table(engine, 'drik', start, end) == build_slot_fact_table(
        engine, 'drik', start.astimezone(timezone.utc), end.astimezone(timezone.utc),
    )
