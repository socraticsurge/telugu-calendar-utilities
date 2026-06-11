from mcp.server.fastmcp import FastMCP

from telugu_panchangam.mcp.tools import (
    tool_list_supported_cities,
    tool_get_panchangam,
    tool_get_muhurta,
    tool_get_special_days,
    tool_get_panchangam_range,
    tool_find_tarabalam_days,
    tool_get_graha_positions,
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
    """Returns full Panchangam JSON for a date and city: Pancha Anga (Tithi, Nakshatra, Yoga, Karana), sky events (Sunrise, Sunset, Moonrise, Moonset), auspicious windows (Brahma Muhurta, Abhijit, Amrita Kalam), inauspicious windows (Rahu Kalam, Gulika, Yamagandam, Varjyam, Durmuhurtham), Choghadiya, and special day flags. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude for a custom location; timezone is derived if omitted), system=drik|surya_siddhanta|vakya (default: drik)."""
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
    """Returns auspicious and inauspicious time windows for a date and city as JSON. Lighter than get_panchangam — use for quick 'is this a good time?' queries. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude; timezone is derived if omitted), system=drik|surya_siddhanta|vakya (default: drik)."""
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
    """Returns a JSON list of special days in a given month: Ekadashi (fasting days), Amavasya (new moon), Pournami (full moon), Pradosham, Sankranti, and Eclipses. Args: year=e.g. 2026, month=1-12, city=city name (or pass latitude+longitude; timezone is derived if omitted), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_special_days(year, month, city, system, latitude, longitude, timezone)


@mcp.tool()
def get_panchangam_range(
    start_date: str,
    end_date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns a compact Panchangam summary for each day in a date range (max 31 days). Each day includes: Tithi, Nakshatra, Yoga, Sunrise/Sunset, all auspicious and inauspicious windows, eclipse (if any), special yogas, and special day flags. Useful for planning muhurtas over a week or comparing multiple days. Args: start_date=YYYY-MM-DD, end_date=YYYY-MM-DD, city=city name, system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_panchangam_range(start_date, end_date, city, system, latitude, longitude, timezone)


def main() -> None:
    mcp.run()


@mcp.tool()
def find_tarabalam_days(
    janma_nakshatras: list[str],
    start_date: str,
    days: int = 14,
    city: str = 'Hyderabad',
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
    janma_rasis: list[str | None] | None = None,
    chandra_mode: str = 'stars',
) -> str:
    """Find which upcoming days are auspicious for one or more people based on their janma (birth) nakshatras — Tarabalam, optionally combined with Chandrabalam. Returns per-day taras (Janma/Sampat/Vipat/Kshema/Pratyak/Sadhana/Naidhana/Mitra/Parama Mitra) for each person plus good_for_all_dates listing days auspicious for everyone. Pass janma_rasis (aligned with janma_nakshatras, null entries allowed) to also check Chandrabalam — each person then gets a chandra position/verdict (good | puja | bad) and good_for_all requires both checks to pass. Args: janma_nakshatras=1-4 birth stars (canonical spellings, e.g. 'Ashvini', 'Uttara Bhadrapada'), start_date=YYYY-MM-DD, days=1-60 (default 14), city=city name (or latitude+longitude), system=drik|surya_siddhanta|vakya, janma_rasis=optional birth rashis (e.g. 'Meena'), chandra_mode=how the Moon affects good_for_all: 'stars' (annotate only, matches classic tarabalam tables — default), 'puja_ok' (drop Moon-avoid days), 'strict' (Moon must be good)."""
    return tool_find_tarabalam_days(janma_nakshatras, start_date, days, city, system, latitude, longitude, timezone, janma_rasis, chandra_mode)


@mcp.tool()
def get_graha_positions(
    date: str,
    city: str = 'Hyderabad',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Sidereal (Lahiri) positions of all nine grahas — Surya, Chandra, Kuja, Budha, Guru, Shukra, Shani, Rahu, Ketu — at sunrise of the given date: longitude, rasi, nakshatra, pada, retrograde flag, and when each graha enters its next rasi (rasi_until + next_rasi; transit/gochara groundwork). Args: date=YYYY-MM-DD, city=city name (or latitude+longitude; timezone derived if omitted)."""
    return tool_get_graha_positions(date, city, latitude, longitude, timezone)
