from datetime import date, datetime, timezone
from src.engines.drik import DrikGanitaEngine
from src.cities import CITIES

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
    from src.engines.base import RASHI_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.solar_sign in RASHI_NAMES

def test_lunar_sign_is_rashi():
    from src.engines.base import RASHI_NAMES
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
