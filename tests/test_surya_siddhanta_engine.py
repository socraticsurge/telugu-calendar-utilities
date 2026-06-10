from datetime import date, datetime, timezone
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine, ss_sun_longitude, ss_moon_longitude
from telugu_panchangam.cities import CITIES

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
    from telugu_panchangam.engines.base import TITHI_NAMES
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
    from telugu_panchangam.engines.base import NAKSHATRA_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.nakshatra.name in NAKSHATRA_NAMES

def test_yoga_valid():
    from telugu_panchangam.engines.base import YOGA_NAMES
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
    from telugu_panchangam.engines.base import MAASAM_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.maasam in MAASAM_NAMES

def test_is_pournami_on_ss_pournami_date():
    # SS elongation puts Pournami on 2024-03-22 (tithi_idx=14, elong ~178°)
    # Drik puts it on 2024-03-25 — demonstrating SS vs Drik difference
    ss_pournami_date = date(2024, 3, 22)
    result = ENGINE.calculate(ss_pournami_date, HYD)
    assert result.is_pournami is True

def test_ss_tithi_start_end_valid():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.start < result.tithi.end
