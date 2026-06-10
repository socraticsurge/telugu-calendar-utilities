from datetime import date, datetime, timezone
from src.models.panchangam_day import Location, Span, Window, PanchangamDay

def test_location_fields():
    loc = Location(name='Hyderabad', lat=17.385, lon=78.4867, timezone='Asia/Kolkata')
    assert loc.name == 'Hyderabad'
    assert loc.lat == 17.385

def test_span_fields():
    start = datetime(2024, 3, 15, 6, 0, tzinfo=timezone.utc)
    end = datetime(2024, 3, 15, 18, 0, tzinfo=timezone.utc)
    span = Span(name='Hasta', start=start, end=end)
    assert span.name == 'Hasta'

def test_panchangam_day_requires_fields():
    import pytest
    with pytest.raises(TypeError):
        PanchangamDay()
