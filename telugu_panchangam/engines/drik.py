# src/engines/drik.py
from datetime import date, datetime, timezone

from telugu_panchangam.engines.base import (
    PanchangamEngine, RASHI_NAMES, rituvu_name, ayanam_name,
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES,
    VAARAM_NAMES,
    KARANA_REPEATING, KARANA_FIXED, samvatsara_name, maasam_name,
    RAHU_PART, GULIKA_PART, YAMAG_PART,
    DURMUHURTA_DAY_MUHURTAS, DURMUHURTA_NIGHT_MUHURTAS,
    VARJYAM_GHATIS, AMRITA_GHATIS,
    nakshatra_day_windows, next_nakshatra_span,
)
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    sun_longitude, moon_longitude, moon_sun_elongation, previous_new_moon,
    get_sunrise, get_sunset, get_moonrise, get_moonset,
)
from telugu_panchangam.models.panchangam_day import Location, Span, Window, PanchangamDay
from telugu_panchangam.eclipses import get_eclipse_for_date
from telugu_panchangam.special_yogas import get_special_yogas

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

class DrikGanitaEngine(PanchangamEngine):

    def __init__(self, ayanamsa: str = 'lahiri'):
        from telugu_panchangam.engines.utils import _validate_ayanamsa
        _validate_ayanamsa(ayanamsa)
        self.ayanamsa = ayanamsa
        super().__init__()

    # --- Ayanamsa-aware longitude helpers ------------------------------------
    # When ayanamsa == 'lahiri' (default), the cached hot-path helpers are used
    # (byte-identical to existing behavior). For other ayanamsas we bypass the
    # lru_cache and call sidereal_longitude_with_ayanamsa directly.

    def _moon_lon(self, jd: float) -> float:
        if self.ayanamsa == 'lahiri':
            return moon_longitude(jd)
        from telugu_panchangam.engines.utils import sidereal_longitude_with_ayanamsa
        import swisseph as swe
        return sidereal_longitude_with_ayanamsa(jd, swe.MOON, self.ayanamsa)

    def _sun_lon(self, jd: float) -> float:
        if self.ayanamsa == 'lahiri':
            return sun_longitude(jd)
        from telugu_panchangam.engines.utils import sidereal_longitude_with_ayanamsa
        import swisseph as swe
        return sidereal_longitude_with_ayanamsa(jd, swe.SUN, self.ayanamsa)

    def _elongation(self, jd: float) -> float:
        if self.ayanamsa == 'lahiri':
            return moon_sun_elongation(jd)
        return (self._moon_lon(jd) - self._sun_lon(jd)) % 360.0

    def _elongation_func(self):
        """Return an elongation callable suitable for find_crossing."""
        if self.ayanamsa == 'lahiri':
            return moon_sun_elongation
        return self._elongation

    def _tithi_index_at(self, jd: float) -> int:
        """Tithi index 0-29 (0=Shukla Pratipat, 14=Pournami, 29=Amavasya)."""
        return int(self._elongation(jd) / 12.0) % 30

    def _tithi_span(self, jd_sunrise: float) -> Span:
        """Tithi active at sunrise, with start/end times."""
        elong_func = self._elongation_func()
        idx = self._tithi_index_at(jd_sunrise)
        target_start = idx * 12.0
        target_end = ((idx + 1) * 12.0) % 360.0

        jd_tithi_start = find_crossing(elong_func, target_start,
                                        jd_sunrise - 2.0, jd_sunrise)
        jd_tithi_end = find_crossing(elong_func, target_end,
                                      jd_sunrise, jd_sunrise + 2.0)

        return Span(
            name=TITHI_NAMES[idx],
            start=jd_to_utc(jd_tithi_start),
            end=jd_to_utc(jd_tithi_end),
        )

    def _nakshatra_span(self, jd_sunrise: float) -> Span:
        """Nakshatra active at sunrise, with start/end times."""
        moon_lon = self._moon_lon(jd_sunrise)
        moon_lon_func = self._moon_longitude_func()
        nak_size = 360.0 / 27.0
        idx = int(moon_lon / nak_size) % 27

        target_start = idx * nak_size
        target_end = (idx + 1) * nak_size

        jd_nak_start = find_crossing(moon_lon_func, target_start,
                                      jd_sunrise - 2.0, jd_sunrise)
        jd_nak_end = find_crossing(moon_lon_func, target_end,
                                    jd_sunrise, jd_sunrise + 2.0)

        return Span(
            name=NAKSHATRA_NAMES[idx],
            start=jd_to_utc(jd_nak_start),
            end=jd_to_utc(jd_nak_end),
        )

    def _yoga_span(self, jd_sunrise: float) -> Span:
        """Yoga at sunrise (Sun+Moon combined longitude)."""
        def yoga_longitude(jd: float) -> float:
            return (self._sun_lon(jd) + self._moon_lon(jd)) % 360.0

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
        return self._day_part_window(RAHU_PART[weekday], jd_sr, jd_ss, 'Rahu Kalam')

    def _gulika_kalam(self, weekday: int, jd_sr: float, jd_ss: float) -> Window:
        return self._day_part_window(GULIKA_PART[weekday], jd_sr, jd_ss, 'Gulika Kalam')

    def _yamagandam(self, weekday: int, jd_sr: float, jd_ss: float) -> Window:
        return self._day_part_window(YAMAG_PART[weekday], jd_sr, jd_ss, 'Yamagandam')

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
        half_muhurta = (jd_sunset - jd_sunrise) / 30.0  # half of a day/15 muhurta
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

    def _durmuhurtham(self, weekday: int, jd_sr: float, jd_ss: float,
                       jd_next_sr: float) -> list[Window]:
        results = []
        day_muhurta = (jd_ss - jd_sr) / 15.0
        for p in DURMUHURTA_DAY_MUHURTAS[weekday]:
            start = jd_sr + (p - 1) * day_muhurta
            results.append(Window(name='Durmuhurtham',
                                  start=jd_to_utc(start),
                                  end=jd_to_utc(start + day_muhurta)))
        night_muhurta = (jd_next_sr - jd_ss) / 15.0
        for p in DURMUHURTA_NIGHT_MUHURTAS.get(weekday, ()):
            start = jd_ss + (p - 1) * night_muhurta
            results.append(Window(name='Durmuhurtham',
                                  start=jd_to_utc(start),
                                  end=jd_to_utc(start + night_muhurta)))
        return results

    def _samvatsara(self, jd_sunrise: float, maasam: str) -> str:
        """60-year Samvatsara cycle (Telugu solar reckoning, flips at Ugadi)."""
        return samvatsara_name(jd_sunrise, maasam)

    def _maasam(self, jd_sunrise: float) -> str:
        """Amanta lunar month name, with Adhika/Nija prefix when applicable."""
        return maasam_name(self._elongation_func(), self._sun_longitude_func(), jd_sunrise)

    def _special_flags(self, tithi_idx: int, weekday: int,
                        jd_sunrise: float, jd_sunset: float) -> dict:
        is_ekadashi = tithi_idx in (10, 25)
        is_amavasya = tithi_idx == 29
        is_pournami = tithi_idx == 14
        tithi_at_sunset = int(self._elongation(jd_sunset) / 12.0) % 30
        is_pradosham = tithi_idx in (12, 27) or tithi_at_sunset in (12, 27)
        is_shani = is_pradosham and weekday == 6
        is_soma = is_pradosham and weekday == 1
        sun_sign_sr = int(self._sun_lon(jd_sunrise) / 30.0) % 12
        # Check if a sign change occurred in the 24h window: prev midnight to next sunrise
        sun_sign_prev_sr = int(self._sun_lon(jd_sunrise - 1.0) / 30.0) % 12
        sun_sign_next_sr = int(self._sun_lon(jd_sunrise + 1.0) / 30.0) % 12
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
        elong_func = self._elongation_func()
        elong_at_sunrise = self._elongation(jd_sunrise)
        half_tithi_idx = int(elong_at_sunrise / 6.0) % 60

        karanas = []
        for offset in range(3):
            ht_idx = (half_tithi_idx + offset) % 60
            ht_start_deg = ht_idx * 6.0
            ht_end_deg = (ht_idx + 1) * 6.0

            jd_k_start = find_crossing(elong_func, ht_start_deg,
                                        jd_sunrise - 0.5, jd_sunrise + 1.0)
            jd_k_end = find_crossing(elong_func, ht_end_deg,
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

    def calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:
        geopos = [location.lon, location.lat, 0.0]
        jd_midnight = local_midnight_jd(d, location.timezone)

        # --- Solar & lunar rise/set ---
        jd_sunrise = get_sunrise(jd_midnight, geopos)
        jd_sunset = get_sunset(jd_sunrise, geopos)
        jd_next_sunrise = get_sunrise(jd_midnight + 1.0, geopos)
        jd_moonrise = get_moonrise(jd_midnight, geopos)
        jd_moonset = get_moonset(jd_midnight, geopos)

        sunrise = jd_to_utc(jd_sunrise)
        sunset = jd_to_utc(jd_sunset)
        moonrise = jd_to_utc(jd_moonrise)
        moonset = jd_to_utc(jd_moonset)

        # --- Signs ---
        sun_lon_sr = self._sun_lon(jd_sunrise)
        moon_lon_sr = self._moon_lon(jd_sunrise)
        solar_sign = RASHI_NAMES[int(sun_lon_sr / 30) % 12]
        lunar_sign = RASHI_NAMES[int(moon_lon_sr / 30) % 12]

        # --- Ayanam ---
        sun_sign_idx = int(sun_lon_sr / 30) % 12
        ayanam = ayanam_name(sun_sign_idx)

        # --- Rituvu ---
        rituvu = rituvu_name(jd_sunrise)

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
        maasam = self._maasam(jd_sunrise)
        samvatsara = self._samvatsara(jd_sunrise, maasam)

        eclipse = get_eclipse_for_date(d, location) if include_eclipse else None
        special_yogas = get_special_yogas(vaaram, tithi_span.name, nakshatra_span.name)

        # Varjyam / Amrita Kalam: windows of the sunrise nakshatra and the one
        # following it that begin within this panchangam day.
        nak_spans = [nakshatra_span, next_nakshatra_span(nakshatra_span, self._moon_longitude_func())]
        day_start = jd_to_utc(jd_sunrise)
        day_end = jd_to_utc(jd_next_sunrise)

        day = PanchangamDay(
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
            amrita_kalam=nakshatra_day_windows(nak_spans, AMRITA_GHATIS, 'Amrita Kalam', day_start, day_end),
            rahu_kalam=self._rahu_kalam(weekday, jd_sunrise, jd_sunset),
            gulika_kalam=self._gulika_kalam(weekday, jd_sunrise, jd_sunset),
            yamagandam=self._yamagandam(weekday, jd_sunrise, jd_sunset),
            varjyam=nakshatra_day_windows(nak_spans, VARJYAM_GHATIS, 'Varjyam', day_start, day_end),
            durmuhurtham=self._durmuhurtham(weekday, jd_sunrise, jd_sunset, jd_next_sunrise),
            choghadiya=self._choghadiya(weekday, jd_sunrise, jd_sunset),
            is_ekadashi=special['is_ekadashi'],
            is_amavasya=special['is_amavasya'],
            is_pournami=special['is_pournami'],
            is_pradosham=special['is_pradosham'],
            is_shani_pradosham=special['is_shani_pradosham'],
            is_soma_pradosham=special['is_soma_pradosham'],
            is_sankranti=special['is_sankranti'],
            eclipse=eclipse,
            special_yogas=special_yogas,
            festivals=self._festivals(maasam, weekday, jd_sunrise, jd_sunset,
                                      jd_next_sunrise, jd_moonrise),
            sankramanam=self._sankramanam_name(jd_sunrise, jd_sunset),
        )
        day.ghati_clock = self._build_ghati_clock(sunrise, jd_to_utc(jd_next_sunrise))
        nak_arc = 360.0 / 27.0
        nak_pos = moon_lon_sr / nak_arc
        day.nakshatra_pada = int(nak_pos * 4) % 4 + 1
        from telugu_panchangam.karana_windows import compute_vishaghati, compute_bhadra_windows
        day.vishaghati = compute_vishaghati(nak_spans, day.ghati_clock)
        day.bhadra_mukha, day.bhadra_puchha = compute_bhadra_windows(day.karana, day.ghati_clock)
        return day

    def _sun_sign_idx_at(self, jd: float) -> int:
        return int(self._sun_lon(jd) / 30.0) % 12

    def _sun_longitude_func(self):
        if self.ayanamsa == 'lahiri':
            return sun_longitude
        return self._sun_lon

    def _moon_longitude_func(self):
        if self.ayanamsa == 'lahiri':
            return moon_longitude
        return self._moon_lon


# Alias so tests and callers can import either name.
DrikEngine = DrikGanitaEngine
