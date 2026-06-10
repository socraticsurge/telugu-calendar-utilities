from telugu_panchangam.cities import CITIES
from telugu_panchangam.models.panchangam_day import Location

def test_cities_count():
    assert len(CITIES) == 22

def test_each_city_is_location():
    for c in CITIES:
        assert isinstance(c, Location)
        assert c.lat != 0.0
        assert c.lon != 0.0
        assert c.timezone != ''

def test_hyderabad_present():
    names = [c.name for c in CITIES]
    assert 'Hyderabad' in names

def test_london_present():
    names = [c.name for c in CITIES]
    assert 'London' in names
