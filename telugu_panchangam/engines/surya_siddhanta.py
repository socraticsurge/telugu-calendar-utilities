# src/engines/surya_siddhanta.py
import math
from datetime import date

import pytz

from telugu_panchangam.engines.base import (
    PanchangamEngine, RASHI_NAMES, RITUVU_NAMES,
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES,
    VAARAM_NAMES, MAASAM_NAMES, SAMVATSARA_NAMES,
    KARANA_REPEATING, KARANA_FIXED,
)
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    get_sunrise, get_sunset, get_moonrise, get_moonset,
)
from telugu_panchangam.models.panchangam_day import Location, Span, Window, PanchangamDay
from telugu_panchangam.eclipses import get_eclipse_for_date
from telugu_panchangam.special_yogas import get_special_yogas

_KALI_EPOCH_JD    = 588465.5
_CIVIL_DAYS       = 1_577_917_828
_SUN_REVS         = 4_320_000
_MOON_REVS        = 57_753_336
_MOON_APOGEE_REVS = 488_219
_SUN_APOGEE_DEG   = 77.333
_SUN_MANDA_R      = 13.5
_MOON_MANDA_R     = 31.5

_RAHU_PART   = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 3, 6: 4}
_GULIKA_PART = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}
_YAMAG_PART  = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
_DURMUHURTHA_PARTS = {
    0: (5, 12), 1: (7, 15), 2: (5, 9),
    3: (2, 8),  4: (10, 16), 5: (4, 11), 6: (6, 14),
}
_DAY_CHOGHADIYA = {
    0: ['Udveg','Char','Labh','Amrit','Kaal','Shubh','Rog','Udveg'],
    1: ['Amrit','Kaal','Shubh','Rog','Udveg','Char','Labh','Amrit'],
    2: ['Rog','Udveg','Char','Labh','Amrit','Kaal','Shubh','Rog'],
    3: ['Labh','Amrit','Kaal','Shubh','Rog','Udveg','Char','Labh'],
    4: ['Shubh','Rog','Udveg','Char','Labh','Amrit','Kaal','Shubh'],
    5: ['Char','Labh','Amrit','Kaal','Shubh','Rog','Udveg','Char'],
    6: ['Kaal','Shubh','Rog','Udveg','Char','Labh','Amrit','Kaal'],
}
_AMRITA_OFFSET_GHATIKAS = [
    55, 4, 26, 22, 49, 17, 45, 13, 37, 55,
    4, 12, 41, 16, 45, 17, 35, 10, 20, 52,
    30, 35, 54, 22, 4, 36, 14,
]
_VARJYAM_OFFSET_GHATIKAS = [
    30, 12, 50, 47, 24, 43, 21, 56, 12, 30,
    38, 47, 16, 50, 20, 52, 10, 44, 55, 27,
    5, 10, 28, 57, 38, 11, 48,
]


def _mean_longitude(ka: float, revs: int) -> float:
    return (ka * revs / _CIVIL_DAYS * 360.0) % 360.0


def ss_sun_longitude(jd: float) -> float:
    ka = jd - _KALI_EPOCH_JD
    mean_sun = _mean_longitude(ka, _SUN_REVS)
    anomaly = (mean_sun - _SUN_APOGEE_DEG) % 360.0
    correction = _SUN_MANDA_R * math.sin(math.radians(anomaly))
    return (mean_sun + correction) % 360.0


def ss_moon_longitude(jd: float) -> float:
    ka = jd - _KALI_EPOCH_JD
    mean_moon = _mean_longitude(ka, _MOON_REVS)
    moon_apogee = _mean_longitude(ka, _MOON_APOGEE_REVS)
    anomaly = (mean_moon - moon_apogee) % 360.0
    correction = _MOON_MANDA_R * math.sin(math.radians(anomaly))
    return (mean_moon + correction) % 360.0


def ss_elongation(jd: float) -> float:
    return (ss_moon_longitude(jd) - ss_sun_longitude(jd)) % 360.0


class SuryaSiddhantaEngine(PanchangamEngine):

    def calculate(self, d: date, location: Location) -> PanchangamDay:
        geopos = [location.lon, location.lat, 0.0]
        jd_midnight = local_midnight_jd(d, location.timezone)

        jd_sunrise  = get_sunrise(jd_midnight, geopos)
        jd_sunset   = get_sunset(jd_sunrise, geopos)
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
        uttarayanam_signs = {9, 10, 11, 0, 1, 2, 3, 4, 5}
        ayanam = 'Uttarayanam' if sun_sign_idx in uttarayanam_signs else 'Dakshinayanam'
        rituvu = RITUVU_NAMES[sun_sign_idx]

        weekday = int((jd_sunrise + 1.5)) % 7
        vaaram  = VAARAM_NAMES[weekday]

        tithi_span   = self._tithi_span(jd_sunrise)
        tithi_idx    = self._tithi_index_at(jd_sunrise)
        paksham      = 'Shukla' if tithi_idx < 15 else 'Krishna'
        nak_span     = self._nakshatra_span(jd_sunrise)
        yoga_span    = self._yoga_span(jd_sunrise)
        karana_spans = self._karana_spans(jd_sunrise, jd_sunset)

        samvatsara = self._samvatsara(jd_sunrise)
        maasam     = self._maasam(jd_sunrise)
        special    = self._special_flags(tithi_idx, weekday, jd_sunrise, jd_sunset)

        eclipse    = get_eclipse_for_date(d, location)
        special_yogas = get_special_yogas(vaaram, tithi_span.name, nak_span.name)

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
            amrita_kalam=self._amrita_kalam(jd_sunrise, nak_span),
            rahu_kalam=self._rahu_kalam(weekday, jd_sunrise, jd_sunset),
            gulika_kalam=self._gulika_kalam(weekday, jd_sunrise, jd_sunset),
            yamagandam=self._yamagandam(weekday, jd_sunrise, jd_sunset),
            varjyam=self._varjyam(nak_span),
            durmuhurtham=self._durmuhurtham(weekday, jd_sunrise, jd_sunset),
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

    def _samvatsara(self, jd_sunrise: float) -> str:
        ka = jd_sunrise - _KALI_EPOCH_JD
        return SAMVATSARA_NAMES[int(ka / 361.02) % 60]

    def _maasam(self, jd_sunrise: float) -> str:
        jd_amavasya = find_crossing(ss_elongation, 0.0, jd_sunrise - 30.0, jd_sunrise)
        sun_lon = ss_sun_longitude(jd_amavasya)
        idx = (int(sun_lon / 30.0) % 12 - 11) % 12
        return MAASAM_NAMES[idx]

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
        return self._day_part_window(_RAHU_PART[wd], jd_sr, jd_ss, 'Rahu Kalam')

    def _gulika_kalam(self, wd, jd_sr, jd_ss):
        return self._day_part_window(_GULIKA_PART[wd], jd_sr, jd_ss, 'Gulika Kalam')

    def _yamagandam(self, wd, jd_sr, jd_ss):
        return self._day_part_window(_YAMAG_PART[wd], jd_sr, jd_ss, 'Yamagandam')

    def _brahma_muhurta(self, jd_sunrise):
        m = 1.0 / 30.0
        return Window('Brahma Muhurta', start=jd_to_utc(jd_sunrise - 2*m), end=jd_to_utc(jd_sunrise - m))

    def _abhijit_muhurta(self, jd_sr, jd_ss, wd):
        if wd == 3:
            return None
        mid = (jd_sr + jd_ss) / 2.0
        hm  = (jd_ss - jd_sr) / 60.0
        return Window('Abhijit Muhurta', start=jd_to_utc(mid - hm), end=jd_to_utc(mid + hm))

    def _choghadiya(self, wd, jd_sr, jd_ss):
        names = _DAY_CHOGHADIYA[wd]
        blk   = (jd_ss - jd_sr) / 8.0
        return [Window(names[i], jd_to_utc(jd_sr + i*blk), jd_to_utc(jd_sr + (i+1)*blk)) for i in range(8)]

    def _durmuhurtham(self, wd, jd_sr, jd_ss):
        m = (jd_ss - jd_sr) / 30.0
        return [Window('Durmuhurtham', jd_to_utc(jd_sr + (p-1)*m), jd_to_utc(jd_sr + p*m))
                for p in _DURMUHURTHA_PARTS[wd]]

    def _amrita_kalam(self, jd_sunrise, nak_span):
        idx    = NAKSHATRA_NAMES.index(nak_span.name)
        offset = _AMRITA_OFFSET_GHATIKAS[idx] * (24.0 / 60.0) / 24.0
        s      = datetime_to_jd(nak_span.start) + offset
        return [Window('Amrita Kalam', jd_to_utc(s), jd_to_utc(s + (4.0/60.0)/24.0))]

    def _varjyam(self, nak_span):
        idx    = NAKSHATRA_NAMES.index(nak_span.name)
        offset = _VARJYAM_OFFSET_GHATIKAS[idx] * (24.0 / 60.0) / 24.0
        s      = datetime_to_jd(nak_span.start) + offset
        return [Window('Varjyam', jd_to_utc(s), jd_to_utc(s + (4.0/60.0)/24.0))]
