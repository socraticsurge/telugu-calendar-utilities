from mcp.server.fastmcp import FastMCP

from telugu_panchangam.mcp.tools import (
    tool_list_supported_cities,
    tool_get_panchangam,
    tool_get_muhurta,
    tool_get_special_days,
    tool_get_panchangam_range,
    tool_find_tarabalam_days,
    tool_get_graha_positions,
    tool_get_gochara,
    tool_get_rasi_phalalu,
    tool_find_muhurta,
    tool_get_daily_horas,
    tool_get_lagna_transitions,
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
    ayanamsa: str = 'lahiri',
) -> str:
    """Returns full Panchangam JSON for a date and city: Pancha Anga (Tithi, Nakshatra, Yoga, Karana), sky events (Sunrise, Sunset, Moonrise, Moonset), auspicious windows (Brahma Muhurta, Abhijit, Amrita Kalam), inauspicious windows (Rahu Kalam, Gulika, Yamagandam, Varjyam, Durmuhurtham), Choghadiya, and special day flags. New in 1.9.0: ghati_clock (sunrise-anchored ghati/vighati clock), nakshatra_pada (Moon's pada 1-4), vishaghati windows, bhadra_mukha/bhadra_puchha (Vishti split), sankramana_avoidance, in_panchaka_nakshatra, nakshatra_mukha (Adho/Urdhva/Tiryak), anandadi_yoga, is_khar_maasa/khar_maasa_name, is_pitru_paksha, simha_stha_guru/simha_stha_shukra (Drik only), guru_maudhya/shukra_maudhya (Drik only), disha_shoola_direction, panchaka_rahita. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude for a custom location; timezone is derived if omitted), system=drik|surya_siddhanta|vakya (default: drik), ayanamsa=lahiri|raman|krishnamurti|true_chitrapaksha (default: lahiri; SS and Vakya accept the param for API symmetry but always use their own mean-motion model)."""
    return tool_get_panchangam(date, city, system, latitude, longitude, timezone, ayanamsa)


@mcp.tool()
def get_muhurta(
    date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns auspicious and inauspicious time windows for a date and city as JSON. Lighter than get_panchangam — use for quick 'is this a good time?' queries. Includes all 1.9.0 timing fields: vishaghati, bhadra_mukha/bhadra_puchha, sankramana_avoidance, ghati_clock, in_panchaka_nakshatra, nakshatra_mukha, anandadi_yoga, is_khar_maasa, is_pitru_paksha, simha_stha_guru/shukra, guru_maudhya/shukra_maudhya, disha_shoola_direction, panchaka_rahita. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude; timezone is derived if omitted), system=drik|surya_siddhanta|vakya (default: drik)."""
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
def get_daily_horas(
    date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns 24 planetary hours (horas) for a date and city as JSON. The 12 daytime horas start at sunrise and the 12 nighttime horas start at sunset. The first hora is ruled by the weekday lord. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude; timezone is derived if omitted), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_daily_horas(date, city, system, latitude, longitude, timezone)


@mcp.tool()
def get_lagna_transitions(
    date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns Ascendant (Lagna) sign boundaries for a date and city as JSON, tracking the rising sign on the eastern horizon from sunrise to next sunrise. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude; timezone is derived if omitted), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_lagna_transitions(date, city, system, latitude, longitude, timezone)


@mcp.tool()
def get_panchangam_range(
    start_date: str,
    end_date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
    ayanamsa: str = 'lahiri',
) -> str:
    """Returns a compact Panchangam summary for each day in a date range (max 31 days). Each day includes: Tithi, Nakshatra, Yoga, Sunrise/Sunset, all auspicious and inauspicious windows, eclipse (if any), special yogas, and special day flags. New in 1.9.0: each day also carries all timing-computation fields — ghati_clock, nakshatra_pada, vishaghati, bhadra_mukha/bhadra_puchha, sankramana_avoidance, in_panchaka_nakshatra, nakshatra_mukha, anandadi_yoga, is_khar_maasa/khar_maasa_name, is_pitru_paksha, simha_stha_guru/shukra, guru_maudhya/shukra_maudhya, disha_shoola_direction, panchaka_rahita. Useful for planning muhurtas over a week or comparing multiple days. Args: start_date=YYYY-MM-DD, end_date=YYYY-MM-DD, city=city name, system=drik|surya_siddhanta|vakya (default: drik), ayanamsa=lahiri|raman|krishnamurti|true_chitrapaksha (default: lahiri)."""
    return tool_get_panchangam_range(start_date, end_date, city, system, latitude, longitude, timezone, ayanamsa)


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
    ayanamsa: str = 'lahiri',
) -> str:
    """Sidereal positions of all nine grahas — Surya, Chandra, Kuja, Budha, Guru, Shukra, Shani, Rahu, Ketu — at sunrise of the given date: longitude, rasi, nakshatra, pada, retrograde flag, and when each graha enters its next rasi (rasi_until + next_rasi; transit/gochara groundwork). Args: date=YYYY-MM-DD, city=city name (or latitude+longitude; timezone derived if omitted), ayanamsa=lahiri|raman|krishnamurti|true_chitrapaksha (default: lahiri; note: gochara/positions module uses Lahiri internally, alternate ayanamsa is accepted but not yet applied to graha position calculations)."""
    return tool_get_graha_positions(date, city, latitude, longitude, timezone, ayanamsa)


@mcp.tool()
def get_gochara(
    date: str,
    janma_rasi: str,
    city: str = 'Hyderabad',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Gochara (transit) verdicts for a janma rasi (natal Moon sign): each of the nine grahas with its house position counted from the janma rasi, a verdict (favourable | blocked by vedha | adverse) per the classical Brihat Samhita tables, plus named conditions — Sade Sati with phase, Ashtama Shani, Ardhastama Shani. Positions at sunrise of the date. Args: date=YYYY-MM-DD, janma_rasi=e.g. 'Mesha' (canonical rashi spellings), city=city name (or latitude+longitude)."""
    return tool_get_gochara(date, janma_rasi, city, latitude, longitude, timezone)


@mcp.tool()
def get_rasi_phalalu(
    date: str,
    janma_rasi: str,
    city: str = 'Hyderabad',
    janma_nakshatra: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Daily Rasi Phalalu — a deterministic daily reading for a janma rasi, rendered entirely from computed facts: the Moon's chandrabalam house sets the day quality, each graha's gochara verdict (with vedha) becomes one traceable sentence, Sade Sati/Ashtama Shani are stated when running, and passing janma_nakshatra adds the day's tarabalam line. Not fiction: every line maps to a calculation. Args: date=YYYY-MM-DD, janma_rasi=e.g. 'Mesha', janma_nakshatra=optional birth star for the tara line, city=city name (or latitude+longitude)."""
    return tool_get_rasi_phalalu(date, janma_rasi, city, janma_nakshatra, latitude, longitude, timezone)


@mcp.tool()
def find_muhurta(
    start_date: str,
    days: int = 7,
    activity: str = 'any',
    city: str = 'Hyderabad',
    system: str = 'drik',
    janma_nakshatras: list[str] | None = None,
    janma_rasis: list[str | None] | None = None,
    janma_lagnas: list[str | None] | None = None,
    chandra_mode: str = 'stars',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
    ayanamsa: str = 'lahiri',
) -> str:
    """Find ranked auspicious time slots over the coming days. Slots are good choghadiya blocks (Amrit/Shubh/Labh/Char) with every inauspicious window subtracted (Rahu Kalam, Gulika, Yamagandam, Varjyam, Durmuhurtham), scored with Abhijit Muhurta / Amrita Kalam overlap and special-yoga bonuses. activity tunes the rules: travel additionally avoids Vishti karana, ceremony skips Visha/Dagdha days, purchase favours Labh, beginning favours Amrit. New in 1.9.0: Bhadra Mukha is a hard-avoid cut; Bhadra Puchha is a bonus for litigation; Simha-Stha Guru/Shukra, Guru/Shukra Maudhya (combustion), Khar-Maasa, Adhika Maasa, and Pitru Paksha are all skipped for samskara activities; Panchaka Rahita (Mrityu/Agni/Raja/Chora/Roga) is checked at both day-level (sunrise lagna) and slot-level; optional travel_direction parameter activates Disha Shoola filtering. New activities: litigation, cremation, construction_roof, wood_cutting, well_digging, coronation. Pass janma_nakshatras (1-4 birth stars) to keep only days whose tarabalam favours everyone. Optionally pass janma_rasis (aligned with janma_nakshatras, null entries allowed) to add Chandrabalam scoring — each person then gets the Moon's position from their rashi with a verdict (good / needs remedial puja / avoid), and chandra_mode selects how this affects the day filter: 'stars' (annotate only, default), 'puja_ok' (drop Moon-avoid days), 'strict' (Moon must be good). Optionally pass janma_lagnas (aligned, null entries allowed) to use strict Lagna Shuddhi for that person — kendra/trikona/Ashtama count from the natal ascendant; otherwise we fall back to counting from janma_rasis (Chandra-Rashi-as-lagna tradition). Args: start_date=YYYY-MM-DD, days=1-14, activity=any|travel|purchase|ceremony|beginning|litigation|cremation|construction_roof|wood_cutting|well_digging|coronation, city=city name (or latitude+longitude), system=drik|surya_siddhanta|vakya, janma_rasis=optional birth rashis (e.g. ['Meena', 'Simha']), janma_lagnas=optional birth lagnas (e.g. ['Vrishabha', None]), chandra_mode=stars|puja_ok|strict, ayanamsa=lahiri|raman|krishnamurti|true_chitrapaksha (default: lahiri), travel_direction=optional compass direction (N/S/E/W/NE/NW/SE/SW) to activate Disha Shoola filtering for travel activity."""
    return tool_find_muhurta(start_date, days, activity, city, system,
                             janma_nakshatras, janma_rasis, janma_lagnas,
                             chandra_mode, latitude, longitude, timezone, ayanamsa)
