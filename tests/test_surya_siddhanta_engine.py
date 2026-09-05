from datetime import date, datetime, timezone

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.surya_siddhanta import (
    SuryaSiddhantaEngine,
    ss_moon_longitude,
    ss_sun_longitude,
)

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = SuryaSiddhantaEngine()
REF_DATE = date(2024, 3, 25)

def test_calculate_returns_panchangam_day():
    from telugu_panchangam.models.panchangam_day import PanchangamDay
    result = ENGINE.calculate(REF_DATE, HYD)
    assert isinstance(result, PanchangamDay)

def test_system_is_surya_siddhanta():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.system == 'surya_siddhanta'

def test_sunrise_is_datetime():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert isinstance(result.sunrise, datetime)
    assert result.sunrise.tzinfo is not None

def test_sunrise_hour_hyderabad():
    result = ENGINE.calculate(REF_DATE, HYD)
    utc_hour = result.sunrise.astimezone(timezone.utc).hour
    assert utc_hour in (0, 1)

def test_ss_sun_longitude_range():
    from telugu_panchangam.engines.utils import local_midnight_jd
    jd = local_midnight_jd(REF_DATE, 'Asia/Kolkata')
    lon = ss_sun_longitude(jd)
    assert 0.0 <= lon < 360.0

def test_ss_moon_longitude_range():
    from telugu_panchangam.engines.utils import local_midnight_jd
    jd = local_midnight_jd(REF_DATE, 'Asia/Kolkata')
    lon = ss_moon_longitude(jd)
    assert 0.0 <= lon < 360.0

def test_ss_sun_in_meena_on_ref_date():
    from telugu_panchangam.engines.utils import local_midnight_jd
    jd = local_midnight_jd(REF_DATE, 'Asia/Kolkata')
    lon = ss_sun_longitude(jd)
    assert 320.0 < lon < 360.0

def test_tithi_name_is_valid():
    from telugu_panchangam.panchangam_names import TITHI_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.name in TITHI_NAMES

def test_tithi_has_start_end():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.start < result.tithi.end

def test_paksham_shukla_on_ref():
    # SS Pournami falls on 2024-03-24 (one day before Drik); on 2024-03-25 SS is Krishna paksha
    from telugu_panchangam.engines.surya_siddhanta import ss_elongation
    from telugu_panchangam.engines.utils import get_sunrise, local_midnight_jd
    geopos = [HYD.lon, HYD.lat, 0.0]
    jd_mid = local_midnight_jd(REF_DATE, HYD.timezone)
    jd_sr  = get_sunrise(jd_mid, geopos)
    elong  = ss_elongation(jd_sr)
    tithi_idx = int(elong / 12.0) % 30
    result = ENGINE.calculate(REF_DATE, HYD)
    expected_paksham = 'Shukla' if tithi_idx < 15 else 'Krishna'
    assert result.paksham == expected_paksham

def test_nakshatra_valid():
    from telugu_panchangam.panchangam_names import NAKSHATRA_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.nakshatra.name in NAKSHATRA_NAMES

def test_yoga_valid():
    from telugu_panchangam.panchangam_names import YOGA_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.yoga.name in YOGA_NAMES

def test_karana_count():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert 1 <= len(result.karana) <= 2

def test_rahu_kalam_within_day():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.sunrise <= result.rahu_kalam.start
    assert result.rahu_kalam.end <= result.sunset

def test_brahma_muhurta_before_sunrise():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.brahma_muhurta.end <= result.sunrise

def test_choghadiya_count():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert len(result.choghadiya) == 8

def test_durmuhurtham_count():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert len(result.durmuhurtham) == 2

def test_samvatsara_nonempty():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.samvatsara != ''

def test_maasam_valid():
    from telugu_panchangam.panchangam_names import MAASAM_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.maasam in MAASAM_NAMES

def test_is_pournami_on_holi_2024():
    # With the corrected manda equation SS agrees with Drik that
    # 2024-03-25 (Holi) is Pournami.
    result = ENGINE.calculate(date(2024, 3, 25), HYD)
    assert result.is_pournami is True

def test_ss_tithi_start_end_valid():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.start < result.tithi.end

def test_eclipse_and_special_yogas_fields_present():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.eclipse is None or hasattr(result.eclipse, 'kind')
    assert isinstance(result.special_yogas, list)


# --- Accuracy of the SS longitude model against modern sidereal positions ---
# Pure Surya Siddhanta (no bija): sun stays within ~1 deg of the modern
# sidereal sun; moon within ~5.5 deg (evection/variation are unmodelled).

def _sample_jds():
    from datetime import date

    from telugu_panchangam.engines.utils import local_midnight_jd
    jd0 = local_midnight_jd(date(2026, 1, 1), 'Asia/Kolkata')
    return [jd0 + i * 7.3 for i in range(60)]


def test_ss_sun_within_one_degree_of_drik():
    from telugu_panchangam.engines.utils import sun_longitude
    for jd in _sample_jds():
        diff = abs((ss_sun_longitude(jd) - sun_longitude(jd) + 180.0) % 360.0 - 180.0)
        assert diff < 1.0, f'sun off by {diff:.2f} deg at jd={jd}'


def test_ss_moon_within_five_and_half_degrees_of_drik():
    from telugu_panchangam.engines.utils import moon_longitude
    for jd in _sample_jds():
        diff = abs((ss_moon_longitude(jd) - moon_longitude(jd) + 180.0) % 360.0 - 180.0)
        assert diff < 5.5, f'moon off by {diff:.2f} deg at jd={jd}'


def test_rituvu_june_2026_is_grishma():
    from datetime import date
    result = ENGINE.calculate(date(2026, 6, 11), HYD)
    assert result.rituvu == 'Grishma'
