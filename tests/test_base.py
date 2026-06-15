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

# --- Window boundary testing ---

def test_nakshatra_day_windows_boundaries():
    from datetime import datetime, timedelta
    from telugu_panchangam.models.panchangam_day import Span
    from telugu_panchangam.engines.base import nakshatra_day_windows

    day_start = datetime(2023, 1, 1, 6, 0)
    day_end = datetime(2023, 1, 2, 6, 0)

    # Use Ashvini (index 0) with a custom ghatis list where ghatis[0] = 0.
    # This means the window starts exactly at the span's start time.
    ghatis = [0] * 27

    span_exact_start = Span(name='Ashvini', start=day_start, end=day_start + timedelta(hours=1))
    span_before_start = Span(name='Ashvini', start=day_start - timedelta(microseconds=1), end=day_start + timedelta(hours=1))
    span_before_end = Span(name='Ashvini', start=day_end - timedelta(microseconds=1), end=day_end + timedelta(hours=1))
    span_exact_end = Span(name='Ashvini', start=day_end, end=day_end + timedelta(hours=1))

    spans = [span_exact_start, span_before_start, span_before_end, span_exact_end]

    windows = nakshatra_day_windows(spans, ghatis, "Test", day_start, day_end)

    assert len(windows) == 2
    # Included: starting exactly at day_start
    assert windows[0].start == span_exact_start.start
    # Included: starting just before day_end
    assert windows[1].start == span_before_end.start
