from datetime import date, datetime

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.surya_siddhanta import ss_moon_longitude
from telugu_panchangam.engines.vakya import VakyaEngine, vakya_moon_longitude

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
    from telugu_panchangam.panchangam_names import TITHI_NAMES
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.name in TITHI_NAMES

def test_tithi_start_end():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.tithi.start < result.tithi.end

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

def test_paksham_shukla_on_ref():
    # REF_DATE (Holi 2024) is Pournami day — Shukla paksha at sunrise.
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.paksham == 'Shukla'

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

def test_vakya_moon_differs_from_ss():
    from telugu_panchangam.engines.utils import local_midnight_jd
    jd = local_midnight_jd(REF_DATE, 'Asia/Kolkata')
    ss  = ss_moon_longitude(jd)
    vak = vakya_moon_longitude(jd)
    diff = abs((vak - ss + 180) % 360 - 180)
    assert diff <= 1.5

def test_all_22_cities_vakya():
    from telugu_panchangam.cities import CITIES
    from telugu_panchangam.generators.ics import ICSGenerator
    gen = ICSGenerator()
    for loc in CITIES:
        days = [ENGINE.calculate(REF_DATE, loc)]
        raw = gen.generate(days, 'vakya')
        assert len(raw) > 0, f'Empty for {loc.name}'

def test_eclipse_and_special_yogas_fields_present():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.eclipse is None or hasattr(result.eclipse, 'kind')
    assert isinstance(result.special_yogas, list)


def test_rituvu_june_2026_is_grishma():
    from datetime import date
    result = ENGINE.calculate(date(2026, 6, 11), HYD)
    assert result.rituvu == 'Grishma'
