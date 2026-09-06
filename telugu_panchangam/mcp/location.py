from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from telugu_panchangam.cities import CITIES

_TF = TimezoneFinder()
_GEOCODER = Nominatim(user_agent='mcp-server-panchangam', timeout=10)


def timezone_for_coordinates(lat: float, lon: float) -> str:
    """Return the IANA timezone for a lat/lon pair, or raise ValueError."""
    tz = _TF.timezone_at(lat=lat, lng=lon)
    if tz is None:
        raise ValueError(f'Could not determine timezone for ({lat}, {lon}). Pass timezone explicitly.')
    return tz


def resolve_location(city: str) -> tuple[float, float, str]:
    """Return (latitude, longitude, timezone) for a city name.

    Checks the 22 pre-configured cities first (case-insensitive, no network).
    Falls back to Nominatim geocoding + timezonefinder for any other city.
    Raises ValueError if the city cannot be resolved.
    """
    for c in CITIES:
        if c.name.lower() == city.lower():
            return c.lat, c.lon, c.timezone

    location = _GEOCODER.geocode(city)
    if location is None:
        raise ValueError(
            f"Unknown city: '{city}'. Call list_supported_cities() for pre-configured cities, "
            "or pass latitude/longitude/timezone directly."
        )

    tz = _TF.timezone_at(lat=location.latitude, lng=location.longitude)
    if tz is None:
        raise ValueError(f"Could not determine timezone for '{city}'.")

    return location.latitude, location.longitude, tz
