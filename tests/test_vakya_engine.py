from datetime import date, datetime, timezone
from src.engines.vakya import VakyaEngine, vakya_moon_longitude, vakya_elongation
from src.engines.surya_siddhanta import ss_moon_longitude
from src.cities import CITIES

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = VakyaEngine()
REF_DATE = date(2024, 3, 25)

def test_system_is_vakya():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.system == 'vakya'

def test_sunrise_is_datetime():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert isinstance(result.sunrise, datetime)
    assert result.sunrise.tzinfo is not None

def test_tithi_valid():
    from src.engines.base import TITHI_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.name in TITHI_NAMES

def test_tithi_start_end():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.start < result.tithi.end

def test_nakshatra_valid():
    from src.engines.base import NAKSHATRA_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.nakshatra.name in NAKSHATRA_NAMES

def test_yoga_valid():
    from src.engines.base import YOGA_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.yoga.name in YOGA_NAMES

def test_karana_count():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert 1 <= len(result.karana) <= 2

def test_paksham_krishna_on_ref():
    # Vakya engine places REF_DATE in Krishna paksha (elongation ~222°, tithi 18)
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.paksham == 'Krishna'

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
    from src.engines.base import MAASAM_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.maasam in MAASAM_NAMES

def test_vakya_moon_differs_from_ss():
    from src.engines.utils import local_midnight_jd
    jd = local_midnight_jd(REF_DATE, 'Asia/Kolkata')
    ss  = ss_moon_longitude(jd)
    vak = vakya_moon_longitude(jd)
    diff = abs((vak - ss + 180) % 360 - 180)
    assert diff <= 1.5

def test_all_22_cities_vakya():
    from src.cities import CITIES
    from src.generators.ics import ICSGenerator
    from icalendar import Calendar
    gen = ICSGenerator()
    for loc in CITIES:
        days = [ENGINE.calculate(REF_DATE, loc)]
        raw = gen.generate(days, 'vakya')
        assert len(raw) > 0, f'Empty for {loc.name}'
