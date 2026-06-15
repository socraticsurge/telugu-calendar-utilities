import pytest
from unittest.mock import patch, MagicMock


def test_predefined_city_resolves_without_network():
    from telugu_panchangam.mcp.location import resolve_location
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc:
        lat, lon, tz = resolve_location('Hyderabad')
        mock_gc.geocode.assert_not_called()
    assert abs(lat - 17.385) < 0.01
    assert abs(lon - 78.487) < 0.01
    assert tz == 'Asia/Kolkata'


def test_predefined_city_case_insensitive():
    from telugu_panchangam.mcp.location import resolve_location
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc:
        lat, lon, tz = resolve_location('hyderabad')
        mock_gc.geocode.assert_not_called()
    assert tz == 'Asia/Kolkata'


def test_predefined_city_london():
    from telugu_panchangam.mcp.location import resolve_location
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc:
        lat, lon, tz = resolve_location('London')
        mock_gc.geocode.assert_not_called()
    assert abs(lat - 51.507) < 0.01
    assert tz == 'Europe/London'


def test_unknown_city_uses_nominatim():
    from telugu_panchangam.mcp.location import resolve_location
    mock_loc = MagicMock()
    mock_loc.latitude = 51.5074
    mock_loc.longitude = -0.1278
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc, \
         patch('telugu_panchangam.mcp.location._TF') as mock_tf:
        mock_gc.geocode.return_value = mock_loc
        mock_tf.timezone_at.return_value = 'Europe/London'
        lat, lon, tz = resolve_location('Some Unknown City')
    assert lat == 51.5074
    assert lon == -0.1278
    assert tz == 'Europe/London'


def test_unresolvable_city_raises_value_error():
    from telugu_panchangam.mcp.location import resolve_location
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc:
        mock_gc.geocode.return_value = None
        with pytest.raises(ValueError, match=r"Unknown city.*list_supported_cities\(\)"):
            resolve_location('xyznotacity123abc')


def test_timezone_not_found_raises_value_error():
    from telugu_panchangam.mcp.location import resolve_location
    mock_loc = MagicMock()
    mock_loc.latitude = 0.0
    mock_loc.longitude = 0.0
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc, \
         patch('telugu_panchangam.mcp.location._TF') as mock_tf:
        mock_gc.geocode.return_value = mock_loc
        mock_tf.timezone_at.return_value = None
        with pytest.raises(ValueError, match="Could not determine timezone"):
            resolve_location('Some Ocean Point')

def test_timezone_for_coordinates_success():
    from telugu_panchangam.mcp.location import timezone_for_coordinates
    with patch('telugu_panchangam.mcp.location._TF') as mock_tf:
        mock_tf.timezone_at.return_value = 'Asia/Kolkata'
        tz = timezone_for_coordinates(17.385, 78.487)

        mock_tf.timezone_at.assert_called_once_with(lat=17.385, lng=78.487)
        assert tz == 'Asia/Kolkata'

def test_timezone_for_coordinates_not_found():
    from telugu_panchangam.mcp.location import timezone_for_coordinates
    with patch('telugu_panchangam.mcp.location._TF') as mock_tf:
        mock_tf.timezone_at.return_value = None
        with pytest.raises(ValueError, match=r"Could not determine timezone for.*"):
            timezone_for_coordinates(0.0, 0.0)
