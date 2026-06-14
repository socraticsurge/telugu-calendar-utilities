from telugu_panchangam.engines.base import (
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES, RASHI_NAMES,
    SAMVATSARA_NAMES, MAASAM_NAMES, RITUVU_NAMES, VAARAM_NAMES,
    PanchangamEngine,
)

def test_tithi_names_count():
    assert len(TITHI_NAMES) == 30

def test_nakshatra_names_count():
    assert len(NAKSHATRA_NAMES) == 27

def test_yoga_names_count():
    assert len(YOGA_NAMES) == 27

def test_rashi_names_count():
    assert len(RASHI_NAMES) == 12

def test_engine_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        PanchangamEngine()


# --- Ekadashi naming ---

def test_ekadashi_name_regular_months():
    from telugu_panchangam.engines.base import ekadashi_name
    assert ekadashi_name('Jyeshtha', 'Krishna', 'Vrishabha') == 'Yogini'
    assert ekadashi_name('Jyeshtha', 'Shukla', 'Vrishabha') == 'Nirjala'
    assert ekadashi_name('Magha', 'Shukla', 'Makara') == 'Jaya'


def test_ekadashi_name_nija_prefix_stripped():
    from telugu_panchangam.engines.base import ekadashi_name
    assert ekadashi_name('Nija Jyeshtha', 'Shukla', 'Vrishabha') == 'Nirjala'


def test_ekadashi_name_adhika_maasam():
    from telugu_panchangam.engines.base import ekadashi_name
    assert ekadashi_name('Adhika Jyeshtha', 'Shukla', 'Vrishabha') == 'Padmini'
    assert ekadashi_name('Adhika Jyeshtha', 'Krishna', 'Vrishabha') == 'Parama'


def test_ekadashi_name_vaikunta_in_dhanurmasa():
    from telugu_panchangam.engines.base import ekadashi_name
    assert ekadashi_name('Margashira', 'Shukla', 'Dhanu') == 'Mokshada (Vaikunta)'
    assert ekadashi_name('Margashira', 'Krishna', 'Dhanu') == 'Saphala'


# --- Rituvu (Drik ritu: tropical, solstice-anchored) ---
# Reference values verified against drikpanchang.com day pages (Hyderabad):
# 19/04/2026 Vasanta, 21/04/2026 Grishma, 11/06/2026 Grishma, 22/12/2026 Shishira

def _noon_jd(y, m, d):
    from datetime import date
    from telugu_panchangam.engines.utils import local_midnight_jd
    return local_midnight_jd(date(y, m, d), 'Asia/Kolkata') + 0.5


def test_rituvu_april_19_is_vasanta():
    from telugu_panchangam.engines.base import rituvu_name
    assert rituvu_name(_noon_jd(2026, 4, 19)) == 'Vasanta'


def test_rituvu_april_21_is_grishma():
    from telugu_panchangam.engines.base import rituvu_name
    assert rituvu_name(_noon_jd(2026, 4, 21)) == 'Grishma'


def test_rituvu_june_11_is_grishma():
    from telugu_panchangam.engines.base import rituvu_name
    assert rituvu_name(_noon_jd(2026, 6, 11)) == 'Grishma'


def test_rituvu_december_22_is_shishira():
    from telugu_panchangam.engines.base import rituvu_name
    assert rituvu_name(_noon_jd(2026, 12, 22)) == 'Shishira'


# --- Ayanam (sidereal: Uttarayanam = Makara through Mithuna) ---

def test_ayanam_uttarayanam_signs():
    from telugu_panchangam.engines.base import ayanam_name
    assert ayanam_name(9) == 'Uttarayanam'   # Makara
    assert ayanam_name(2) == 'Uttarayanam'   # Mithuna
    assert ayanam_name(3) == 'Dakshinayanam' # Karkataka
    assert ayanam_name(4) == 'Dakshinayanam' # Simha
    assert ayanam_name(8) == 'Dakshinayanam' # Dhanu


# --- Nakshatra Ghati Window ---

def test_nakshatra_ghati_window_happy_path():
    from telugu_panchangam.engines.base import nakshatra_ghati_window
    from telugu_panchangam.models.panchangam_day import Span
    from datetime import datetime, timezone, timedelta

    start_time = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    # Span of 1 hour (3600 seconds)
    end_time = start_time + timedelta(hours=1)
    span = Span(name='Ashvini', start=start_time, end=end_time)

    # Fake ghatis list where Ashvini (index 0) has a start of 30 ghatis
    ghatis = [30] + [0] * 26

    window = nakshatra_ghati_window(span, ghatis, 'Test Window')

    assert window.name == 'Test Window'
    # 30/60 is exactly halfway, so start is 12:30
    assert window.start == start_time + timedelta(minutes=30)
    # Duration is always 4/60 of the span, which is 1 hour * (4/60) = 4 minutes
    assert window.end == window.start + timedelta(minutes=4)


def test_nakshatra_ghati_window_zero_duration():
    from telugu_panchangam.engines.base import nakshatra_ghati_window
    from telugu_panchangam.models.panchangam_day import Span
    from datetime import datetime, timezone

    time = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    span = Span(name='Bharani', start=time, end=time)

    # Bharani is index 1
    ghatis = [0, 24] + [0] * 25

    window = nakshatra_ghati_window(span, ghatis, 'Zero Duration')

    assert window.name == 'Zero Duration'
    assert window.start == time
    assert window.end == time


def test_nakshatra_ghati_window_different_nakshatra():
    from telugu_panchangam.engines.base import nakshatra_ghati_window
    from telugu_panchangam.models.panchangam_day import Span
    from datetime import datetime, timezone, timedelta

    start_time = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    end_time = start_time + timedelta(hours=2)
    span = Span(name='Krittika', start=start_time, end=end_time)

    # Krittika is index 2
    ghatis = [0, 0, 45] + [0] * 24

    window = nakshatra_ghati_window(span, ghatis, 'Krittika Window')

    assert window.name == 'Krittika Window'
    # 45/60 is 3/4. 3/4 of 2 hours is 1.5 hours (90 minutes)
    assert window.start == start_time + timedelta(minutes=90)
    # Duration is 4/60. 4/60 of 2 hours is 120 * 4 / 60 = 8 minutes
    assert window.end == window.start + timedelta(minutes=8)
