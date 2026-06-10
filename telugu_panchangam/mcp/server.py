from mcp.server.fastmcp import FastMCP

from telugu_panchangam.mcp.tools import (
    tool_list_supported_cities,
    tool_get_panchangam,
    tool_get_muhurta,
    tool_get_special_days,
)

mcp = FastMCP('mcp-server-panchangam')


@mcp.tool()
def list_supported_cities() -> str:
    """Returns a JSON list of 22 pre-configured cities with name, latitude, longitude, timezone, and country. Call this first to discover valid city names."""
    return tool_list_supported_cities()


@mcp.tool()
def get_panchangam(
    date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns full Panchangam JSON for a date and city: Pancha Anga (Tithi, Nakshatra, Yoga, Karana), sky events (Sunrise, Sunset, Moonrise, Moonset), auspicious windows (Brahma Muhurta, Abhijit, Amrita Kalam), inauspicious windows (Rahu Kalam, Gulika, Yamagandam, Varjyam, Durmuhurtham), Choghadiya, and special day flags. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude+timezone for a custom location), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_panchangam(date, city, system, latitude, longitude, timezone)


@mcp.tool()
def get_muhurta(
    date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns auspicious and inauspicious time windows for a date and city as JSON. Lighter than get_panchangam — use for quick 'is this a good time?' queries. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude+timezone), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_muhurta(date, city, system, latitude, longitude, timezone)


@mcp.tool()
def get_special_days(
    year: int,
    month: int,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns a JSON list of special days in a given month: Ekadashi (fasting days), Amavasya (new moon), Pournami (full moon), Pradosham, and Sankranti. Args: year=e.g. 2026, month=1-12, city=city name (or pass latitude+longitude+timezone), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_special_days(year, month, city, system, latitude, longitude, timezone)


def main() -> None:
    mcp.run()
