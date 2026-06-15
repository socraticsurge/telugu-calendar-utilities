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


# --- Nakshatra Day Windows ---

def test_nakshatra_day_windows_boundaries():
    from datetime import datetime, timedelta
    from telugu_panchangam.models.panchangam_day import Span
    from telugu_panchangam.engines.base import nakshatra_day_windows, NAKSHATRA_NAMES

    day_start = datetime(2024, 1, 1, 6, 0)
    day_end = datetime(2024, 1, 2, 6, 0)

    # Use first nakshatra for simplicity
    nak_name = NAKSHATRA_NAMES[0]
    idx = 0

    # Dummy ghatis list, all 0 except we modify the first one for each case
    ghatis = [0] * 27

    # Helper to test a single span and ghati
    def check_window(span_start: datetime, span_end: datetime, ghati: int) -> int:
        ghatis[idx] = ghati
        span = Span(name=nak_name, start=span_start, end=span_end)
        res = nakshatra_day_windows([span], ghatis, "Test", day_start, day_end)
        return len(res)

    # Test 1: Window starts exactly at day_start (included)
    # span is 60 hours long, ghati is 30 -> window start = span.start + 30/60 * 60 = span.start + 30
    # Let's use simpler math: 60 minutes span.
    # span_start = day_start - 30 mins
    # dur = 60 mins. ghati = 30 -> start + 30/60 * 60 mins = start + 30 mins = day_start
    assert check_window(day_start - timedelta(minutes=30), day_start + timedelta(minutes=30), 30) == 1

    # Test 2: Window starts slightly before day_start (excluded)
    # window start = day_start - 1 minute
    assert check_window(day_start - timedelta(minutes=31), day_start + timedelta(minutes=29), 30) == 0

    # Test 3: Window starts strictly inside [day_start, day_end) (included)
    # window start = day_start + 1 minute
    assert check_window(day_start - timedelta(minutes=29), day_start + timedelta(minutes=31), 30) == 1

    # Test 4: Window starts exactly at day_end (excluded)
    assert check_window(day_end - timedelta(minutes=30), day_end + timedelta(minutes=30), 30) == 0

    # Test 5: Window starts slightly after day_end (excluded)
    assert check_window(day_end - timedelta(minutes=29), day_end + timedelta(minutes=31), 30) == 0
