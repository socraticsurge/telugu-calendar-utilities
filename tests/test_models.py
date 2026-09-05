from datetime import datetime, timezone

from telugu_panchangam.models.panchangam_day import Location, PanchangamDay, Span


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

def test_eclipse_info_fields():
    from telugu_panchangam.models.panchangam_day import EclipseInfo
    start = datetime(2025, 9, 7, 16, 27, tzinfo=timezone.utc)
    end = datetime(2025, 9, 7, 19, 56, tzinfo=timezone.utc)
    eclipse = EclipseInfo(
        kind='Lunar', subtype='Total', visible=True,
        start=start, end=end,
        sutak_start=start, sutak_end=end,
    )
    assert eclipse.kind == 'Lunar'
    assert eclipse.subtype == 'Total'
    assert eclipse.visible is True
    assert eclipse.start == start
    assert eclipse.sutak_end == end
