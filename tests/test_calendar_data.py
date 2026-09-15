"""Structured data comes from engine objects, never from description parsing."""

from datetime import date, timedelta

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.generators.calendar_data import calendar_feed


@pytest.mark.parametrize(
    "engine_class", [DrikGanitaEngine, SuryaSiddhantaEngine, VakyaEngine]
)
@pytest.mark.parametrize("city_name", ["Hyderabad", "New York"])
def test_calendar_data_keeps_identity_and_real_facts(engine_class, city_name):
    location = next(c for c in CITIES if c.name == city_name)
    engine = engine_class()
    days = [
        engine.calculate(date(2026, 7, 18) + timedelta(days=i), location)
        for i in range(2)
    ]
    result = calendar_feed(days, days[0].system)
    assert result["schemaVersion"] == 1
    assert result["city"] == city_name
    assert result["timezone"] == location.timezone
    first = result["days"]["20260718"]["day"]
    assert first["nakshatra"]["name"] == days[0].nakshatra.name
    assert len(first["nightChoghadiya"]) == 8
    assert result["days"]["20260719"]["day"]["nightChoghadiya"] == []


def test_empty_calendar_data_is_rejected():
    with pytest.raises(ValueError, match="at least one day"):
        calendar_feed([], "drik")


def test_cross_runtime_calendar_corpus_is_current():
    import json

    from tools.export_calendar_contract_fixture import ROOT, build_fixture

    actual = json.loads(
        (ROOT / "tests/fixtures/calendar-data-contract.json").read_text()
    )
    assert actual == build_fixture()
