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

    def _tithi_index_at(self, jd: float) -> int:
        """Tithi index 0-29 (0=Shukla Pratipat, 14=Pournami, 29=Amavasya)."""
        return int(moon_sun_elongation(jd) / 12.0) % 30

    def _tithi_span(self, jd_sunrise: float) -> Span:
        """Tithi active at sunrise, with start/end times."""
        idx = self._tithi_index_at(jd_sunrise)
        target_start = idx * 12.0
        target_end = ((idx + 1) * 12.0) % 360.0

        jd_tithi_start = find_crossing(moon_sun_elongation, target_start,
                                        jd_sunrise - 2.0, jd_sunrise)
        jd_tithi_end = find_crossing(moon_sun_elongation, target_end,
                                      jd_sunrise, jd_sunrise + 2.0)

        return Span(
            name=TITHI_NAMES[idx],
            start=jd_to_utc(jd_tithi_start),
            end=jd_to_utc(jd_tithi_end),
        )

    def _nakshatra_span(self, jd_sunrise: float) -> Span:
        """Nakshatra active at sunrise, with start/end times."""
        moon_lon = moon_longitude(jd_sunrise)
        nak_size = 360.0 / 27.0
        idx = int(moon_lon / nak_size) % 27

        target_start = idx * nak_size
        target_end = (idx + 1) * nak_size

        jd_nak_start = find_crossing(moon_longitude, target_start,
                                      jd_sunrise - 2.0, jd_sunrise)
        jd_nak_end = find_crossing(moon_longitude, target_end,
                                    jd_sunrise, jd_sunrise + 2.0)

        return Span(
            name=NAKSHATRA_NAMES[idx],
            start=jd_to_utc(jd_nak_start),
            end=jd_to_utc(jd_nak_end),
        )

    def _yoga_span(self, jd_sunrise: float) -> Span:
        """Yoga at sunrise (Sun+Moon combined longitude)."""
        def yoga_longitude(jd: float) -> float:
            return (sun_longitude(jd) + moon_longitude(jd)) % 360.0

        combined = yoga_longitude(jd_sunrise)
        nak_size = 360.0 / 27.0
        idx = int(combined / nak_size) % 27

        target_start = idx * nak_size
        target_end = (idx + 1) * nak_size

        jd_yoga_start = find_crossing(yoga_longitude, target_start,
                                       jd_sunrise - 2.0, jd_sunrise)
        jd_yoga_end = find_crossing(yoga_longitude, target_end,
                                     jd_sunrise, jd_sunrise + 2.0)

        return Span(
            name=YOGA_NAMES[idx],
            start=jd_to_utc(jd_yoga_start),
            end=jd_to_utc(jd_yoga_end),
        )

    def _day_part_window(self, part: int, jd_sunrise: float,
                          jd_sunset: float, name: str) -> Window:
        """Return Window for the Nth 1-indexed equal part of the day (8 parts)."""
        day_duration = jd_sunset - jd_sunrise
        part_size = day_duration / 8.0
        start = jd_sunrise + (part - 1) * part_size
        end = start + part_size
        return Window(name=name, start=jd_to_utc(start), end=jd_to_utc(end))

    def _rahu_kalam(self, weekday: int, jd_sr: float, jd_ss: float) -> Window:
        return self._day_part_window(_RAHU_PART[weekday], jd_sr, jd_ss, 'Rahu Kalam')

    def _gulika_kalam(self, weekday: int, jd_sr: float, jd_ss: float) -> Window:
        return self._day_part_window(_GULIKA_PART[weekday], jd_sr, jd_ss, 'Gulika Kalam')

    def _yamagandam(self, weekday: int, jd_sr: float, jd_ss: float) -> Window:
        return self._day_part_window(_YAMAG_PART[weekday], jd_sr, jd_ss, 'Yamagandam')

    def _brahma_muhurta(self, jd_sunrise: float) -> Window:
        # 2 muhurtas (96 min) before sunrise; 1 muhurta = 48 min = 1/30 day
        muhurta = 1.0 / 30.0
        start = jd_sunrise - 2 * muhurta
        end = jd_sunrise - muhurta
        return Window(name='Brahma Muhurta', start=jd_to_utc(start), end=jd_to_utc(end))

    def _abhijit_muhurta(self, jd_sunrise: float, jd_sunset: float,
                          weekday: int) -> Window | None:
        if weekday == 3:  # Wednesday — no Abhijit
            return None
        midday = (jd_sunrise + jd_sunset) / 2.0
        half_muhurta = (jd_sunset - jd_sunrise) / 60.0
        return Window(name='Abhijit Muhurta',
                      start=jd_to_utc(midday - half_muhurta),
                      end=jd_to_utc(midday + half_muhurta))

    def _choghadiya(self, weekday: int, jd_sr: float, jd_ss: float) -> list[Window]:
        names = _DAY_CHOGHADIYA[weekday]
        block = (jd_ss - jd_sr) / 8.0
        return [
            Window(name=names[i],
                   start=jd_to_utc(jd_sr + i * block),
                   end=jd_to_utc(jd_sr + (i + 1) * block))
            for i in range(8)
        ]

    def _durmuhurtham(self, weekday: int, jd_sr: float, jd_ss: float) -> list[Window]:
        muhurta = (jd_ss - jd_sr) / 30.0
        parts = _DURMUHURTHA_PARTS[weekday]
        results = []
        for p in parts:
            start = jd_sr + (p - 1) * muhurta
            results.append(Window(name='Durmuhurtham',
                                  start=jd_to_utc(start),
                                  end=jd_to_utc(start + muhurta)))
        return results

    def _amrita_kalam(self, jd_sunrise: float, nak_span: Span) -> list[Window]:
        nak_idx = NAKSHATRA_NAMES.index(nak_span.name)
        offset_ghatikas = _AMRITA_OFFSET_GHATIKAS[nak_idx]
        offset_jd = offset_ghatikas * (24.0 / 60.0) / 24.0  # ghatikas to days
        nak_start_jd = datetime_to_jd(nak_span.start)
        start_jd = nak_start_jd + offset_jd
        end_jd = start_jd + (4.0 / 60.0) / 24.0  # 4 ghatikas duration
        return [Window(name='Amrita Kalam', start=jd_to_utc(start_jd), end=jd_to_utc(end_jd))]

    def _varjyam(self, nak_span: Span) -> list[Window]:
        nak_idx = NAKSHATRA_NAMES.index(nak_span.name)
        offset_ghatikas = _VARJYAM_OFFSET_GHATIKAS[nak_idx]
        offset_jd = offset_ghatikas * (24.0 / 60.0) / 24.0
        nak_start_jd = datetime_to_jd(nak_span.start)
        start_jd = nak_start_jd + offset_jd
        end_jd = start_jd + (4.0 / 60.0) / 24.0
        return [Window(name='Varjyam', start=jd_to_utc(start_jd), end=jd_to_utc(end_jd))]

    def _samvatsara(self, jd_sunrise: float) -> str:
        """60-year Samvatsara cycle based on Kali Ahargana."""
        jd_kali_epoch = 588465.5
        ahargana = jd_sunrise - jd_kali_epoch
        idx = int(ahargana / 361.02) % 60
        return SAMVATSARA_NAMES[idx]

    def _maasam(self, jd_sunrise: float) -> str:
        """Lunar month name based on Sun's sign at the most recent Amavasya."""
        jd_amavasya = find_crossing(moon_sun_elongation, 0.0,
                                     jd_sunrise - 30.0, jd_sunrise)
        sun_lon_at_nm = sun_longitude(jd_amavasya)
        solar_sign_idx = int(sun_lon_at_nm / 30.0) % 12
        maasam_idx = (solar_sign_idx - 11) % 12
        return MAASAM_NAMES[maasam_idx]

    def _special_flags(self, tithi_idx: int, weekday: int,
                        jd_sunrise: float, jd_sunset: float) -> dict:
        is_ekadashi = tithi_idx in (10, 25)
        is_amavasya = tithi_idx == 29
        is_pournami = tithi_idx == 14
        tithi_at_sunset = int(moon_sun_elongation(jd_sunset) / 12.0) % 30
        is_pradosham = tithi_idx in (12, 27) or tithi_at_sunset in (12, 27)
        is_shani = is_pradosham and weekday == 6
        is_soma = is_pradosham and weekday == 1
        sun_sign_sr = int(sun_longitude(jd_sunrise) / 30.0) % 12
        # Check if a sign change occurred in the 24h window: prev midnight to next sunrise
        sun_sign_prev_sr = int(sun_longitude(jd_sunrise - 1.0) / 30.0) % 12
        sun_sign_next_sr = int(sun_longitude(jd_sunrise + 1.0) / 30.0) % 12
        is_sankranti = (sun_sign_sr != sun_sign_next_sr) or (sun_sign_prev_sr != sun_sign_sr)
        return {
            'is_ekadashi': is_ekadashi,
            'is_amavasya': is_amavasya,
            'is_pournami': is_pournami,
            'is_pradosham': is_pradosham,
            'is_shani_pradosham': is_shani,
            'is_soma_pradosham': is_soma,
            'is_sankranti': is_sankranti,
        }

    def _karana_spans(self, jd_sunrise: float, jd_sunset: float) -> list[Span]:
        """Karanas active between sunrise and sunset."""
        elong_at_sunrise = moon_sun_elongation(jd_sunrise)
        half_tithi_idx = int(elong_at_sunrise / 6.0) % 60

        karanas = []
        for offset in range(3):
            ht_idx = (half_tithi_idx + offset) % 60
            ht_start_deg = ht_idx * 6.0
            ht_end_deg = (ht_idx + 1) * 6.0

            jd_k_start = find_crossing(moon_sun_elongation, ht_start_deg,
                                        jd_sunrise - 0.5, jd_sunrise + 1.0)
            jd_k_end = find_crossing(moon_sun_elongation, ht_end_deg,
                                      jd_k_start, jd_k_start + 1.0)

            if jd_k_end < jd_sunrise or jd_k_start > jd_sunset:
                continue

            if ht_idx in KARANA_FIXED:
                name = KARANA_FIXED[ht_idx]
            else:
                name = KARANA_REPEATING[(ht_idx - 1) % 7]

            karanas.append(Span(
                name=name,
                start=jd_to_utc(jd_k_start),
                end=jd_to_utc(jd_k_end),
            ))
            if len(karanas) == 2:
                break

        return karanas

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
        vaaram = VAARAM_NAMES[weekday]

        # --- Pancha Anga ---
        tithi_span = self._tithi_span(jd_sunrise)
        tithi_idx = self._tithi_index_at(jd_sunrise)
        paksham = 'Shukla' if tithi_idx < 15 else 'Krishna'

        nakshatra_span = self._nakshatra_span(jd_sunrise)
        yoga_span = self._yoga_span(jd_sunrise)
        karana_spans = self._karana_spans(jd_sunrise, jd_sunset)

        # --- Metadata & Special Flags ---
        special = self._special_flags(tithi_idx, weekday, jd_sunrise, jd_sunset)
        samvatsara = self._samvatsara(jd_sunrise)
        maasam = self._maasam(jd_sunrise)

        return PanchangamDay(
            date=d,
            location=location,
            system='drik',
            samvatsara=samvatsara,
            ayanam=ayanam,
            rituvu=rituvu,
            maasam=maasam,
            paksham=paksham,
            tithi=tithi_span,
            vaaram=vaaram,
            nakshatra=nakshatra_span,
            yoga=yoga_span,
            karana=karana_spans,
            sunrise=sunrise,
            sunset=sunset,
            moonrise=moonrise,
            moonset=moonset,
            solar_sign=solar_sign,
            lunar_sign=lunar_sign,
            brahma_muhurta=self._brahma_muhurta(jd_sunrise),
            abhijit_muhurta=self._abhijit_muhurta(jd_sunrise, jd_sunset, weekday),
            amrita_kalam=self._amrita_kalam(jd_sunrise, nakshatra_span),
            rahu_kalam=self._rahu_kalam(weekday, jd_sunrise, jd_sunset),
            gulika_kalam=self._gulika_kalam(weekday, jd_sunrise, jd_sunset),
            yamagandam=self._yamagandam(weekday, jd_sunrise, jd_sunset),
            varjyam=self._varjyam(nakshatra_span),
            durmuhurtham=self._durmuhurtham(weekday, jd_sunrise, jd_sunset),
            choghadiya=self._choghadiya(weekday, jd_sunrise, jd_sunset),
            is_ekadashi=special['is_ekadashi'],
            is_amavasya=special['is_amavasya'],
            is_pournami=special['is_pournami'],
            is_pradosham=special['is_pradosham'],
            is_shani_pradosham=special['is_shani_pradosham'],
            is_soma_pradosham=special['is_soma_pradosham'],
            is_sankranti=special['is_sankranti'],
        )
