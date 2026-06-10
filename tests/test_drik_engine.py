from datetime import date, datetime, timezone
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()

# 2024-03-25 is Holi (Pournami in Phalguna maasam)
REF_DATE = date(2024, 3, 25)

def test_sunrise_is_datetime():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert isinstance(result.sunrise, datetime)
    assert result.sunrise.tzinfo is not None

def test_sunrise_hour_hyderabad():
    # Hyderabad sunrise on 2024-03-25 should be ~06:15 IST = ~00:45 UTC
    result = ENGINE.calculate(REF_DATE, HYD)
    utc_hour = result.sunrise.astimezone(timezone.utc).hour
    assert utc_hour in (0, 1)  # 00:xx or 01:xx UTC

def test_solar_sign_is_rashi():
    from telugu_panchangam.engines.base import RASHI_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.solar_sign in RASHI_NAMES

def test_lunar_sign_is_rashi():
    from telugu_panchangam.engines.base import RASHI_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.lunar_sign in RASHI_NAMES

def test_solar_sign_march25_is_meena():
    # Sun in Meena (Pisces sidereal) in late March
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.solar_sign == 'Meena'

def test_ayanam_march_is_uttarayanam():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.ayanam == 'Uttarayanam'

def test_rituvu_meena_is_shishira():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.rituvu == 'Shishira'

def test_tithi_name_is_valid():
    from telugu_panchangam.engines.base import TITHI_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.name in TITHI_NAMES

def test_pournami_on_ref_date():
    # 2024-03-25 is Holi (Pournami)
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.name == 'Pournami'

def test_tithi_has_start_end():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.start < result.tithi.end

def test_nakshatra_name_is_valid():
    from telugu_panchangam.engines.base import NAKSHATRA_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.nakshatra.name in NAKSHATRA_NAMES

def test_yoga_name_is_valid():
    from telugu_panchangam.engines.base import YOGA_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.yoga.name in YOGA_NAMES

def test_karana_count_is_one_or_two():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert 1 <= len(result.karana) <= 2

def test_paksham_is_shukla_on_ref_date():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.paksham == 'Shukla'

def test_rahu_kalam_is_window():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.rahu_kalam.start < result.rahu_kalam.end

def test_rahu_kalam_within_day():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.sunrise <= result.rahu_kalam.start
    assert result.rahu_kalam.end <= result.sunset

def test_brahma_muhurta_before_sunrise():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.brahma_muhurta.end <= result.sunrise

def test_choghadiya_count_is_eight():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert len(result.choghadiya) == 8

def test_vaaram_is_valid():
    from telugu_panchangam.engines.base import VAARAM_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.vaaram in VAARAM_NAMES

def test_durmuhurtham_count_is_two():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert len(result.durmuhurtham) == 2

def test_samvatsara_is_string():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert isinstance(result.samvatsara, str) and result.samvatsara != ''

def test_maasam_is_valid():
    from telugu_panchangam.engines.base import MAASAM_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.maasam in MAASAM_NAMES

def test_is_pournami_on_ref_date():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.is_pournami is True

EKADASHI_DATE = date(2024, 3, 20)  # Shukla Ekadashi before Holi

def test_is_ekadashi():
    result = ENGINE.calculate(EKADASHI_DATE, HYD)
    assert result.is_ekadashi is True

def test_sankranti_on_mesha_sankranti():
    # Mesha Sankranti 2024: ~April 14
    result = ENGINE.calculate(date(2024, 4, 14), HYD)
    assert result.is_sankranti is True

def test_eclipse_field_present_and_none_on_non_eclipse_day():
    # Use a date with no eclipse
    result = ENGINE.calculate(date(2024, 3, 26), HYD)
    assert result.eclipse is None

def test_eclipse_populated_on_known_eclipse_date():
    result = ENGINE.calculate(date(2025, 9, 7), HYD)
    assert result.eclipse is not None
    assert result.eclipse.kind == 'Lunar'

def test_special_yogas_field_is_list():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert isinstance(result.special_yogas, list)
