# src/engines/surya_siddhanta.py
import math
from datetime import date

import pytz

from telugu_panchangam.engines.base import (
    PanchangamEngine, RASHI_NAMES, rituvu_name, ayanam_name,
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES,
    VAARAM_NAMES, MAASAM_NAMES,
    KARANA_REPEATING, KARANA_FIXED, samvatsara_name, maasam_name,
    RAHU_PART, GULIKA_PART, YAMAG_PART,
    DURMUHURTA_DAY_MUHURTAS, DURMUHURTA_NIGHT_MUHURTAS,
    VARJYAM_GHATIS, AMRITA_GHATIS,
    nakshatra_day_windows, next_nakshatra_span,
)
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    get_sunrise, get_sunset, get_moonrise, get_moonset, previous_new_moon,
)
from telugu_panchangam.models.panchangam_day import Location, Span, Window, PanchangamDay
from telugu_panchangam.eclipses import get_eclipse_for_date
from telugu_panchangam.special_yogas import get_special_yogas

# Kali epoch: midnight of Feb 17/18, 3102 BCE at Ujjain (75.7683 E local time).
_KALI_EPOCH_JD    = 588465.5 - 75.7683 / 360.0
_CIVIL_DAYS       = 1_577_917_828
_SUN_REVS         = 4_320_000
_MOON_REVS        = 57_753_336
_MOON_APOGEE_REVS = 488_219
_MOON_APOGEE_AT_EPOCH = 90.0   # SS places the moon's mandocca at 90 deg at Kali epoch
_SUN_APOGEE_DEG   = 77.333
# Manda epicycle circumferences in degrees; the equation-of-centre amplitude
# is circumference / 2*pi, subtracted when the anomaly (from apogee) is 0-180.
_SUN_MANDA_R      = 13.5
_MOON_MANDA_R     = 31.5

_DAY_CHOGHADIYA = {
    0: ['Udveg','Char','Labh','Amrit','Kaal','Shubh','Rog','Udveg'],
    1: ['Amrit','Kaal','Shubh','Rog','Udveg','Char','Labh','Amrit'],
    2: ['Rog','Udveg','Char','Labh','Amrit','Kaal','Shubh','Rog'],
    3: ['Labh','Amrit','Kaal','Shubh','Rog','Udveg','Char','Labh'],
    4: ['Shubh','Rog','Udveg','Char','Labh','Amrit','Kaal','Shubh'],
    5: ['Char','Labh','Amrit','Kaal','Shubh','Rog','Udveg','Char'],
    6: ['Kaal','Shubh','Rog','Udveg','Char','Labh','Amrit','Kaal'],
}


def _mean_longitude(ka: float, revs: int) -> float:
    return (ka * revs / _CIVIL_DAYS * 360.0) % 360.0


def ss_sun_longitude(jd: float) -> float:
    ka = jd - _KALI_EPOCH_JD
    mean_sun = _mean_longitude(ka, _SUN_REVS)
    anomaly = (mean_sun - _SUN_APOGEE_DEG) % 360.0
    correction = _SUN_MANDA_R / (2.0 * math.pi) * math.sin(math.radians(anomaly))
    return (mean_sun - correction) % 360.0


def ss_moon_longitude(jd: float) -> float:
    ka = jd - _KALI_EPOCH_JD
    mean_moon = _mean_longitude(ka, _MOON_REVS)
    moon_apogee = (_mean_longitude(ka, _MOON_APOGEE_REVS) + _MOON_APOGEE_AT_EPOCH) % 360.0
    anomaly = (mean_moon - moon_apogee) % 360.0
    correction = _MOON_MANDA_R / (2.0 * math.pi) * math.sin(math.radians(anomaly))
    return (mean_moon - correction) % 360.0


def ss_elongation(jd: float) -> float:
    return (ss_moon_longitude(jd) - ss_sun_longitude(jd)) % 360.0


class SuryaSiddhantaEngine(PanchangamEngine):

    def calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:
        geopos = [location.lon, location.lat, 0.0]
        jd_midnight = local_midnight_jd(d, location.timezone)

        jd_sunrise  = get_sunrise(jd_midnight, geopos)
        jd_sunset   = get_sunset(jd_sunrise, geopos)
        jd_next_sunrise = get_sunrise(jd_midnight + 1.0, geopos)
        jd_moonrise = get_moonrise(jd_midnight, geopos)
        jd_moonset  = get_moonset(jd_midnight, geopos)

        sunrise  = jd_to_utc(jd_sunrise)
        sunset   = jd_to_utc(jd_sunset)
        moonrise = jd_to_utc(jd_moonrise)
        moonset  = jd_to_utc(jd_moonset)

        sun_lon  = ss_sun_longitude(jd_sunrise)
        moon_lon = ss_moon_longitude(jd_sunrise)

        solar_sign   = RASHI_NAMES[int(sun_lon / 30) % 12]
        lunar_sign   = RASHI_NAMES[int(moon_lon / 30) % 12]
        sun_sign_idx = int(sun_lon / 30) % 12
        ayanam = ayanam_name(sun_sign_idx)
        rituvu = rituvu_name(jd_sunrise)

        weekday = int((jd_sunrise + 1.5)) % 7
        vaaram  = VAARAM_NAMES[weekday]

        tithi_span   = self._tithi_span(jd_sunrise)
        tithi_idx    = self._tithi_index_at(jd_sunrise)
        paksham      = 'Shukla' if tithi_idx < 15 else 'Krishna'
        nak_span     = self._nakshatra_span(jd_sunrise)
        yoga_span    = self._yoga_span(jd_sunrise)
        karana_spans = self._karana_spans(jd_sunrise, jd_sunset)

        maasam     = self._maasam(jd_sunrise)
        samvatsara = self._samvatsara(jd_sunrise, maasam)
        special    = self._special_flags(tithi_idx, weekday, jd_sunrise, jd_sunset)

        eclipse    = get_eclipse_for_date(d, location) if include_eclipse else None
        special_yogas = get_special_yogas(vaaram, tithi_span.name, nak_span.name)

        # Varjyam / Amrita Kalam: windows of the sunrise nakshatra and the one
        # following it that begin within this panchangam day.
        nak_spans = [nak_span, next_nakshatra_span(nak_span, self._moon_longitude_func())]
        day_start = jd_to_utc(jd_sunrise)
        day_end   = jd_to_utc(jd_next_sunrise)

        return PanchangamDay(
            date=d, location=location, system='surya_siddhanta',
            samvatsara=samvatsara, ayanam=ayanam, rituvu=rituvu,
            maasam=maasam, paksham=paksham,
            tithi=tithi_span, vaaram=vaaram,
            nakshatra=nak_span, yoga=yoga_span, karana=karana_spans,
            sunrise=sunrise, sunset=sunset, moonrise=moonrise, moonset=moonset,
            solar_sign=solar_sign, lunar_sign=lunar_sign,
            brahma_muhurta=self._brahma_muhurta(jd_sunrise),
            abhijit_muhurta=self._abhijit_muhurta(jd_sunrise, jd_sunset, weekday),
            amrita_kalam=nakshatra_day_windows(nak_spans, AMRITA_GHATIS, 'Amrita Kalam', day_start, day_end),
            rahu_kalam=self._rahu_kalam(weekday, jd_sunrise, jd_sunset),
            gulika_kalam=self._gulika_kalam(weekday, jd_sunrise, jd_sunset),
            yamagandam=self._yamagandam(weekday, jd_sunrise, jd_sunset),
            varjyam=nakshatra_day_windows(nak_spans, VARJYAM_GHATIS, 'Varjyam', day_start, day_end),
            durmuhurtham=self._durmuhurtham(weekday, jd_sunrise, jd_sunset, jd_next_sunrise),
            choghadiya=self._choghadiya(weekday, jd_sunrise, jd_sunset),
            eclipse=eclipse,
            special_yogas=special_yogas,
            **special,
        )

    def _tithi_index_at(self, jd: float) -> int:
        return int(ss_elongation(jd) / 12.0) % 30

    def _tithi_span(self, jd_sunrise: float) -> Span:
        idx = self._tithi_index_at(jd_sunrise)
        target_start = idx * 12.0
        target_end   = ((idx + 1) * 12.0) % 360.0
        jd_start = find_crossing(ss_elongation, target_start, jd_sunrise - 2.0, jd_sunrise)
        jd_end   = find_crossing(ss_elongation, target_end,   jd_sunrise,       jd_sunrise + 2.0)
        return Span(name=TITHI_NAMES[idx], start=jd_to_utc(jd_start), end=jd_to_utc(jd_end))

    def _nakshatra_span(self, jd_sunrise: float) -> Span:
        moon_lon = ss_moon_longitude(jd_sunrise)
        nak_size = 360.0 / 27.0
        idx = int(moon_lon / nak_size) % 27
        target_start = idx * nak_size
        target_end   = (idx + 1) * nak_size
        jd_start = find_crossing(ss_moon_longitude, target_start, jd_sunrise - 2.0, jd_sunrise)
        jd_end   = find_crossing(ss_moon_longitude, target_end,   jd_sunrise,       jd_sunrise + 2.0)
        return Span(name=NAKSHATRA_NAMES[idx], start=jd_to_utc(jd_start), end=jd_to_utc(jd_end))

    def _yoga_span(self, jd_sunrise: float) -> Span:
        def yoga_longitude(jd: float) -> float:
            return (ss_sun_longitude(jd) + ss_moon_longitude(jd)) % 360.0
        combined = yoga_longitude(jd_sunrise)
        nak_size = 360.0 / 27.0
        idx = int(combined / nak_size) % 27
        target_start = idx * nak_size
        target_end   = (idx + 1) * nak_size
        jd_start = find_crossing(yoga_longitude, target_start, jd_sunrise - 2.0, jd_sunrise)
        jd_end   = find_crossing(yoga_longitude, target_end,   jd_sunrise,       jd_sunrise + 2.0)
        return Span(name=YOGA_NAMES[idx], start=jd_to_utc(jd_start), end=jd_to_utc(jd_end))

    def _karana_spans(self, jd_sunrise: float, jd_sunset: float) -> list[Span]:
        elong_at_sunrise = ss_elongation(jd_sunrise)
        half_tithi_idx = int(elong_at_sunrise / 6.0) % 60
        karanas = []
        for offset in range(3):
            ht_idx = (half_tithi_idx + offset) % 60
            jd_k_start = find_crossing(ss_elongation, ht_idx * 6.0,       jd_sunrise - 0.5, jd_sunrise + 1.0)
            jd_k_end   = find_crossing(ss_elongation, (ht_idx + 1) * 6.0, jd_k_start,       jd_k_start + 1.0)
            if jd_k_end < jd_sunrise or jd_k_start > jd_sunset:
                continue
            name = KARANA_FIXED[ht_idx] if ht_idx in KARANA_FIXED else KARANA_REPEATING[(ht_idx - 1) % 7]
            karanas.append(Span(name=name, start=jd_to_utc(jd_k_start), end=jd_to_utc(jd_k_end)))
            if len(karanas) == 2:
                break
        return karanas

    def _samvatsara(self, jd_sunrise: float, maasam: str) -> str:
        return samvatsara_name(jd_sunrise, maasam)

    def _maasam(self, jd_sunrise: float) -> str:
        return maasam_name(ss_elongation, ss_sun_longitude, jd_sunrise)

    def _special_flags(self, tithi_idx: int, weekday: int,
                        jd_sunrise: float, jd_sunset: float) -> dict:
        is_ekadashi  = tithi_idx in (10, 25)
        is_amavasya  = tithi_idx == 29
        is_pournami  = tithi_idx == 14
        tithi_at_ss  = int(ss_elongation(jd_sunset) / 12.0) % 30
        is_pradosham = tithi_idx in (12, 27) or tithi_at_ss in (12, 27)
        sun_sr = int(ss_sun_longitude(jd_sunrise) / 30.0) % 12
        sun_ss = int(ss_sun_longitude(jd_sunset)  / 30.0) % 12
        prev   = int(ss_sun_longitude(jd_sunrise - 1.0) / 30.0) % 12
        return {
            'is_ekadashi': is_ekadashi, 'is_amavasya': is_amavasya,
            'is_pournami': is_pournami, 'is_pradosham': is_pradosham,
            'is_shani_pradosham': is_pradosham and weekday == 6,
            'is_soma_pradosham':  is_pradosham and weekday == 1,
            'is_sankranti': sun_sr != sun_ss or sun_sr != prev,
        }

    def _day_part_window(self, part, jd_sr, jd_ss, name):
        sz = (jd_ss - jd_sr) / 8.0
        s  = jd_sr + (part - 1) * sz
        return Window(name=name, start=jd_to_utc(s), end=jd_to_utc(s + sz))

    def _rahu_kalam(self, wd, jd_sr, jd_ss):
        return self._day_part_window(RAHU_PART[wd], jd_sr, jd_ss, 'Rahu Kalam')

    def _gulika_kalam(self, wd, jd_sr, jd_ss):
        return self._day_part_window(GULIKA_PART[wd], jd_sr, jd_ss, 'Gulika Kalam')

    def _yamagandam(self, wd, jd_sr, jd_ss):
        return self._day_part_window(YAMAG_PART[wd], jd_sr, jd_ss, 'Yamagandam')

    def _brahma_muhurta(self, jd_sunrise):
        m = 1.0 / 30.0
        return Window('Brahma Muhurta', start=jd_to_utc(jd_sunrise - 2*m), end=jd_to_utc(jd_sunrise - m))

    def _abhijit_muhurta(self, jd_sr, jd_ss, wd):
        if wd == 3:
            return None
        mid = (jd_sr + jd_ss) / 2.0
        hm  = (jd_ss - jd_sr) / 30.0  # half of a day/15 muhurta
        return Window('Abhijit Muhurta', start=jd_to_utc(mid - hm), end=jd_to_utc(mid + hm))

    def _choghadiya(self, wd, jd_sr, jd_ss):
        names = _DAY_CHOGHADIYA[wd]
        blk   = (jd_ss - jd_sr) / 8.0
        return [Window(names[i], jd_to_utc(jd_sr + i*blk), jd_to_utc(jd_sr + (i+1)*blk)) for i in range(8)]

    def _durmuhurtham(self, wd, jd_sr, jd_ss, jd_next_sr):
        out = []
        m = (jd_ss - jd_sr) / 15.0
        out += [Window('Durmuhurtham', jd_to_utc(jd_sr + (p-1)*m), jd_to_utc(jd_sr + p*m))
                for p in DURMUHURTA_DAY_MUHURTAS[wd]]
        nm = (jd_next_sr - jd_ss) / 15.0
        out += [Window('Durmuhurtham', jd_to_utc(jd_ss + (p-1)*nm), jd_to_utc(jd_ss + p*nm))
                for p in DURMUHURTA_NIGHT_MUHURTAS.get(wd, ())]
        return out

    def _moon_longitude_func(self):
        """Moon-longitude model used for nakshatra boundaries (vakya overrides)."""
        return ss_moon_longitude
