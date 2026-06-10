# src/engines/drik.py
from datetime import date, datetime, timezone
import swisseph as swe
import pytz

from src.engines.base import (
    PanchangamEngine, RASHI_NAMES, RITUVU_NAMES,
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES,
    VAARAM_NAMES, MAASAM_NAMES, SAMVATSARA_NAMES,
    KARANA_REPEATING, KARANA_FIXED,
)
from src.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    sun_longitude, moon_longitude, moon_sun_elongation,
    get_sunrise, get_sunset, get_moonrise, get_moonset,
)
from src.models.panchangam_day import Location, Span, Window, PanchangamDay

# Rahu Kalam, Gulika, Yamagandam: 1-indexed part of day (1=first, 8=last)
# Weekday: 0=Sunday, 1=Monday, ..., 6=Saturday
_RAHU_PART   = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 3, 6: 4}
_GULIKA_PART = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}
_YAMAG_PART  = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}

# Durmuhurtham: 2 muhurta indices (1-indexed out of 30 solar muhurtas per day) per weekday
_DURMUHURTHA_PARTS = {
    0: (5, 12),   # Sunday
    1: (7, 15),   # Monday
    2: (5, 9),    # Tuesday
    3: (2, 8),    # Wednesday
    4: (10, 16),  # Thursday
    5: (4, 11),   # Friday
    6: (6, 14),   # Saturday
}

# Day Choghadiya sequence (8 per day from sunrise), weekday 0=Sunday
_DAY_CHOGHADIYA = {
    0: ['Udveg','Char','Labh','Amrit','Kaal','Shubh','Rog','Udveg'],
    1: ['Amrit','Kaal','Shubh','Rog','Udveg','Char','Labh','Amrit'],
    2: ['Rog','Udveg','Char','Labh','Amrit','Kaal','Shubh','Rog'],
    3: ['Labh','Amrit','Kaal','Shubh','Rog','Udveg','Char','Labh'],
    4: ['Shubh','Rog','Udveg','Char','Labh','Amrit','Kaal','Shubh'],
    5: ['Char','Labh','Amrit','Kaal','Shubh','Rog','Udveg','Char'],
    6: ['Kaal','Shubh','Rog','Udveg','Char','Labh','Amrit','Kaal'],
}

# Amrita Kalam offset from Nakshatra start, in ghatikas (1 ghatika = 24 min)
_AMRITA_OFFSET_GHATIKAS = [
    55, 4, 26, 22, 49, 17, 45, 13, 37, 55,
    4, 12, 41, 16, 45, 17, 35, 10, 20, 52,
    30, 35, 54, 22, 4, 36, 14,
]

# Varjyam offset from Nakshatra start, in ghatikas
_VARJYAM_OFFSET_GHATIKAS = [
    30, 12, 50, 47, 24, 43, 21, 56, 12, 30,
    38, 47, 16, 50, 20, 52, 10, 44, 55, 27,
    5, 10, 28, 57, 38, 11, 48,
]


class DrikGanitaEngine(PanchangamEngine):

    def calculate(self, d: date, location: Location) -> PanchangamDay:
        geopos = [location.lon, location.lat, 0.0]
        jd_midnight = local_midnight_jd(d, location.timezone)

        # --- Solar & lunar rise/set ---
        jd_sunrise = get_sunrise(jd_midnight, geopos)
        jd_sunset = get_sunset(jd_sunrise, geopos)
        jd_moonrise = get_moonrise(jd_midnight, geopos)
        jd_moonset = get_moonset(jd_midnight, geopos)

        sunrise = jd_to_utc(jd_sunrise)
        sunset = jd_to_utc(jd_sunset)
        moonrise = jd_to_utc(jd_moonrise)
        moonset = jd_to_utc(jd_moonset)

        # --- Signs ---
        sun_lon_sr = sun_longitude(jd_sunrise)
        moon_lon_sr = moon_longitude(jd_sunrise)
        solar_sign = RASHI_NAMES[int(sun_lon_sr / 30) % 12]
        lunar_sign = RASHI_NAMES[int(moon_lon_sr / 30) % 12]

        # --- Ayanam ---
        sun_sign_idx = int(sun_lon_sr / 30) % 12
        uttarayanam_signs = {9, 10, 11, 0, 1, 2, 3, 4, 5}
        ayanam = 'Uttarayanam' if sun_sign_idx in uttarayanam_signs else 'Dakshinayanam'

        # --- Rituvu ---
        rituvu = RITUVU_NAMES[sun_sign_idx]

        # weekday: 0=Sunday ... 6=Saturday
        weekday = int((jd_sunrise + 1.5)) % 7

        # Stubs for fields implemented in Tasks 7-9
        _stub_span = Span('', sunrise, sunrise)
        _stub_window = Window('', sunrise, sunrise)

        return PanchangamDay(
            date=d,
            location=location,
            system='drik',
            samvatsara='',
            ayanam=ayanam,
            rituvu=rituvu,
            maasam='',
            paksham='',
            tithi=_stub_span,
            vaaram='',
            nakshatra=_stub_span,
            yoga=_stub_span,
            karana=[],
            sunrise=sunrise,
            sunset=sunset,
            moonrise=moonrise,
            moonset=moonset,
            solar_sign=solar_sign,
            lunar_sign=lunar_sign,
            brahma_muhurta=_stub_window,
            abhijit_muhurta=None,
            amrita_kalam=[],
            rahu_kalam=_stub_window,
            gulika_kalam=_stub_window,
            yamagandam=_stub_window,
            varjyam=[],
            durmuhurtham=[],
            choghadiya=[],
            is_ekadashi=False,
            is_amavasya=False,
            is_pournami=False,
            is_pradosham=False,
            is_shani_pradosham=False,
            is_soma_pradosham=False,
            is_sankranti=False,
        )
