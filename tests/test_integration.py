# tests/test_integration.py
"""Full pipeline: engine → ICS → parse. Runs for 3 days, 2 cities."""
from datetime import date, timedelta
from icalendar import Calendar
from src.cities import CITIES
from src.engines.drik import DrikGanitaEngine
from src.generators.ics import ICSGenerator

ENGINE = DrikGanitaEngine()
GEN = ICSGenerator()
START = date(2024, 3, 24)

def days_for(city_name: str, n: int = 5):
    loc = next(c for c in CITIES if c.name == city_name)
    return [ENGINE.calculate(START + timedelta(days=i), loc) for i in range(n)]

def test_hyderabad_drik_feed():
    days = days_for('Hyderabad')
    raw = GEN.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert len(events) == 5
    for e in events:
        desc = str(e.get('description'))
        assert 'Rahu Kalam' in desc
        assert 'Sunrise' in desc

def test_london_drik_feed():
    days = days_for('London')
    raw = GEN.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert len(events) == 5

def test_all_22_cities_generate_without_error():
    for loc in CITIES:
        days = [ENGINE.calculate(START, loc)]
        raw = GEN.generate(days, 'drik')
        assert len(raw) > 0, f'Empty output for {loc.name}'
