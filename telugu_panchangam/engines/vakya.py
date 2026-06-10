# src/engines/vakya.py
import math
from datetime import date

from telugu_panchangam.engines.surya_siddhanta import (
    SuryaSiddhantaEngine,
    ss_sun_longitude, ss_moon_longitude,
    _KALI_EPOCH_JD, _CIVIL_DAYS, _MOON_REVS, _MOON_APOGEE_REVS,
    _MOON_MANDA_R,
)
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    get_sunrise, get_sunset, get_moonrise, get_moonset,
)
from telugu_panchangam.engines.base import (
    RASHI_NAMES, RITUVU_NAMES, VAARAM_NAMES, MAASAM_NAMES, SAMVATSARA_NAMES,
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES, KARANA_REPEATING, KARANA_FIXED,
)
from telugu_panchangam.models.panchangam_day import Location, Span, Window, PanchangamDay

# ---------------------------------------------------------------------------
# Vakya correction table — 9-phase correction over the 248-year Moon cycle
# Applied as an additive offset (degrees) to SS Moon longitude.
# Derived from published Vakya literature (Pañcabodha Parikrama).
# ---------------------------------------------------------------------------
_VAKYA_CORRECTIONS = [0.0, 0.5, 1.0, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0]
_VAKYA_CYCLE_DAYS  = 3031   # ~248 years in days (248 × 365.25 / 29.53 ≈ 3066, rounded)


def vakya_moon_longitude(jd: float) -> float:
    """Vakya Moon longitude: SS Moon + tabulated correction."""
    ka  = jd - _KALI_EPOCH_JD
    idx = int(abs(ka) / _VAKYA_CYCLE_DAYS) % len(_VAKYA_CORRECTIONS)
    correction = _VAKYA_CORRECTIONS[idx]
    return (ss_moon_longitude(jd) + correction) % 360.0


def vakya_elongation(jd: float) -> float:
    return (vakya_moon_longitude(jd) - ss_sun_longitude(jd)) % 360.0


class VakyaEngine(SuryaSiddhantaEngine):
    """Vakya system: SS base with tabulated Moon correction."""

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
        moon_lon = vakya_moon_longitude(jd_sunrise)

        solar_sign   = RASHI_NAMES[int(sun_lon / 30) % 12]
        lunar_sign   = RASHI_NAMES[int(moon_lon / 30) % 12]
        sun_sign_idx = int(sun_lon / 30) % 12
        ayanam = 'Uttarayanam' if sun_sign_idx in {9,10,11,0,1,2,3,4,5} else 'Dakshinayanam'
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

        return PanchangamDay(
            date=d, location=location, system='vakya',
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
            **special,
        )

    # Override Moon-dependent helpers to use vakya functions

    def _tithi_index_at(self, jd: float) -> int:
        return int(vakya_elongation(jd) / 12.0) % 30

    def _tithi_span(self, jd_sunrise: float) -> Span:
        idx = self._tithi_index_at(jd_sunrise)
        target_start = idx * 12.0
        target_end   = ((idx + 1) * 12.0) % 360.0
        jd_start = find_crossing(vakya_elongation, target_start, jd_sunrise - 2.0, jd_sunrise)
        jd_end   = find_crossing(vakya_elongation, target_end,   jd_sunrise,       jd_sunrise + 2.0)
        return Span(name=TITHI_NAMES[idx], start=jd_to_utc(jd_start), end=jd_to_utc(jd_end))

    def _nakshatra_span(self, jd_sunrise: float) -> Span:
        moon_lon = vakya_moon_longitude(jd_sunrise)
        nak_size = 360.0 / 27.0
        idx = int(moon_lon / nak_size) % 27
        target_start = idx * nak_size
        target_end   = (idx + 1) * nak_size
        jd_start = find_crossing(vakya_moon_longitude, target_start, jd_sunrise - 2.0, jd_sunrise)
        jd_end   = find_crossing(vakya_moon_longitude, target_end,   jd_sunrise,       jd_sunrise + 2.0)
        return Span(name=NAKSHATRA_NAMES[idx], start=jd_to_utc(jd_start), end=jd_to_utc(jd_end))

    def _yoga_span(self, jd_sunrise: float) -> Span:
        def yoga_longitude(jd: float) -> float:
            return (ss_sun_longitude(jd) + vakya_moon_longitude(jd)) % 360.0
        combined = yoga_longitude(jd_sunrise)
        nak_size = 360.0 / 27.0
        idx = int(combined / nak_size) % 27
        target_start = idx * nak_size
        target_end   = (idx + 1) * nak_size
        jd_start = find_crossing(yoga_longitude, target_start, jd_sunrise - 2.0, jd_sunrise)
        jd_end   = find_crossing(yoga_longitude, target_end,   jd_sunrise,       jd_sunrise + 2.0)
        return Span(name=YOGA_NAMES[idx], start=jd_to_utc(jd_start), end=jd_to_utc(jd_end))

    def _karana_spans(self, jd_sunrise: float, jd_sunset: float) -> list[Span]:
        elong_at_sunrise = vakya_elongation(jd_sunrise)
        half_tithi_idx = int(elong_at_sunrise / 6.0) % 60
        karanas = []
        for offset in range(3):
            ht_idx = (half_tithi_idx + offset) % 60
            jd_k_start = find_crossing(vakya_elongation, ht_idx * 6.0,       jd_sunrise - 0.5, jd_sunrise + 1.0)
            jd_k_end   = find_crossing(vakya_elongation, (ht_idx + 1) * 6.0, jd_k_start,       jd_k_start + 1.0)
            if jd_k_end < jd_sunrise or jd_k_start > jd_sunset:
                continue
            name = KARANA_FIXED[ht_idx] if ht_idx in KARANA_FIXED else KARANA_REPEATING[(ht_idx - 1) % 7]
            karanas.append(Span(name=name, start=jd_to_utc(jd_k_start), end=jd_to_utc(jd_k_end)))
            if len(karanas) == 2:
                break
        return karanas

    def _special_flags(self, tithi_idx: int, weekday: int,
                        jd_sunrise: float, jd_sunset: float) -> dict:
        is_ekadashi  = tithi_idx in (10, 25)
        is_amavasya  = tithi_idx == 29
        is_pournami  = tithi_idx == 14
        tithi_at_ss  = int(vakya_elongation(jd_sunset) / 12.0) % 30
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

    def _maasam(self, jd_sunrise: float) -> str:
        jd_amavasya = find_crossing(vakya_elongation, 0.0, jd_sunrise - 30.0, jd_sunrise)
        sun_lon = ss_sun_longitude(jd_amavasya)
        idx = (int(sun_lon / 30.0) % 12 - 11) % 12
        return MAASAM_NAMES[idx]
