from telugu_panchangam.engines.base import PanchangamEngine
from telugu_panchangam.panchangam_names import (
    NAKSHATRA_NAMES,
    RASHI_NAMES,
    TITHI_NAMES,
    YOGA_NAMES,
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


def test_next_nakshatra_span():
    from datetime import datetime, timezone
    from unittest.mock import MagicMock, patch

    from telugu_panchangam.engines.base import next_nakshatra_span
    from telugu_panchangam.models.panchangam_day import Span

    span_end = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    # Test typical transition: Ashvini (0) -> Bharani (1)
    span = Span(name='Ashvini', start=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc), end=span_end)

    mock_moon_func = MagicMock()

    with patch('telugu_panchangam.engines.utils.find_crossing', return_value=2459947.5) as mock_find, \
         patch('telugu_panchangam.engines.utils.jd_to_utc', return_value=datetime(2023, 1, 2, 12, 0, tzinfo=timezone.utc)), \
         patch('telugu_panchangam.engines.utils.datetime_to_jd', return_value=2459946.5):

        result = next_nakshatra_span(span, mock_moon_func)

        assert result.name == 'Bharani'
        assert result.start == span_end
        assert result.end == datetime(2023, 1, 2, 12, 0, tzinfo=timezone.utc)

        # Verify find_crossing was called with correct target longitude
        # Ashvini is index 0. Next is Bharani, index 1. Target should be (1 + 1) * 360/27 = 2 * 13.333 = 26.666
        args, _ = mock_find.call_args
        assert abs(args[1] - 26.666666666666668) < 1e-9

    # Test wrap-around transition: Revati (26) -> Ashvini (0)
    span_wrap = Span(name='Revati', start=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc), end=span_end)

    with patch('telugu_panchangam.engines.utils.find_crossing', return_value=2459947.5) as mock_find, \
         patch('telugu_panchangam.engines.utils.jd_to_utc', return_value=datetime(2023, 1, 2, 12, 0, tzinfo=timezone.utc)), \
         patch('telugu_panchangam.engines.utils.datetime_to_jd', return_value=2459946.5):

        result_wrap = next_nakshatra_span(span_wrap, mock_moon_func)

        assert result_wrap.name == 'Ashvini'

        # Target for next nakshatra after Revati (index 26) is Ashvini (index 0).
        # Internal idx calculation gives idx = 0. Target is (0 + 1) * 360/27 = 13.333
        args, _ = mock_find.call_args
        assert abs(args[1] - 13.333333333333334) < 1e-9


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

    from telugu_panchangam.engines.base import nakshatra_day_windows
    from telugu_panchangam.models.panchangam_day import Span

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


# --- Nakshatra Ghati Window ---

def test_nakshatra_ghati_window_happy_path():
    from datetime import datetime, timedelta, timezone

    from telugu_panchangam.engines.base import nakshatra_ghati_window
    from telugu_panchangam.models.panchangam_day import Span

    start_time = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    end_time = start_time + timedelta(hours=1)
    span = Span(name='Ashvini', start=start_time, end=end_time)

    ghatis = [30] + [0] * 26

    window = nakshatra_ghati_window(span, ghatis, 'Test Window')

    assert window.name == 'Test Window'
    assert window.start == start_time + timedelta(minutes=30)
    assert window.end == window.start + timedelta(minutes=4)


def test_nakshatra_ghati_window_zero_duration():
    from datetime import datetime, timezone

    from telugu_panchangam.engines.base import nakshatra_ghati_window
    from telugu_panchangam.models.panchangam_day import Span

    time = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    span = Span(name='Bharani', start=time, end=time)

    ghatis = [0, 24] + [0] * 25

    window = nakshatra_ghati_window(span, ghatis, 'Zero Duration')

    assert window.name == 'Zero Duration'
    assert window.start == time
    assert window.end == time


def test_nakshatra_ghati_window_different_nakshatra():
    from datetime import datetime, timedelta, timezone

    from telugu_panchangam.engines.base import nakshatra_ghati_window
    from telugu_panchangam.models.panchangam_day import Span

    start_time = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    end_time = start_time + timedelta(hours=2)
    span = Span(name='Krittika', start=start_time, end=end_time)

    ghatis = [0, 0, 45] + [0] * 24

    window = nakshatra_ghati_window(span, ghatis, 'Krittika Window')

    assert window.name == 'Krittika Window'
    assert window.start == start_time + timedelta(minutes=90)
    assert window.end == window.start + timedelta(minutes=8)


# --- Maasam naming ---

from unittest.mock import patch

from telugu_panchangam.engines.base import maasam_name


def _mock_prev_new_moon(elong_func, jd):
    if jd == 100.0: return 90.0
    if jd == 89.0: return 60.0
    return 0.0

def _mock_next_new_moon(elong_func, jd):
    if jd == 91.0: return 120.0
    return 0.0

@patch('telugu_panchangam.engines.utils.previous_new_moon', _mock_prev_new_moon)
@patch('telugu_panchangam.engines.utils.next_new_moon', _mock_next_new_moon)
def test_maasam_name_regular():
    def mock_sun_lon(jd):
        if jd == 90.0: return 11 * 30.0 + 15.0 # sign 11 -> Chaitra
        if jd == 120.0: return 0 * 30.0 + 15.0 # sign 0
        if jd == 60.0: return 10 * 30.0 + 15.0 # sign 10
        return 0.0

    name = maasam_name(None, mock_sun_lon, 100.0)
    assert name == 'Chaitra'

@patch('telugu_panchangam.engines.utils.previous_new_moon', _mock_prev_new_moon)
@patch('telugu_panchangam.engines.utils.next_new_moon', _mock_next_new_moon)
def test_maasam_name_adhika():
    def mock_sun_lon(jd):
        if jd == 90.0: return 11 * 30.0 + 5.0 # sign 11 -> Chaitra
        if jd == 120.0: return 11 * 30.0 + 25.0 # sign 11
        if jd == 60.0: return 10 * 30.0 + 15.0 # sign 10
        return 0.0

    name = maasam_name(None, mock_sun_lon, 100.0)
    assert name == 'Adhika Chaitra'

@patch('telugu_panchangam.engines.utils.previous_new_moon', _mock_prev_new_moon)
@patch('telugu_panchangam.engines.utils.next_new_moon', _mock_next_new_moon)
def test_maasam_name_nija():
    def mock_sun_lon(jd):
        if jd == 90.0: return 11 * 30.0 + 25.0 # sign 11 -> Chaitra
        if jd == 120.0: return 0 * 30.0 + 15.0 # sign 0
        if jd == 60.0: return 11 * 30.0 + 5.0 # sign 11
        return 0.0

    name = maasam_name(None, mock_sun_lon, 100.0)
    assert name == 'Nija Chaitra'


def test_nakshatra_ghati_window_calculation():
    from datetime import datetime, timedelta, timezone

    from telugu_panchangam.engines.base import nakshatra_ghati_window
    from telugu_panchangam.models.panchangam_day import Span

    # Create a 60-hour span to make calculations straightforward (1 hour = 1 ghati proportion)
    start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=60)

    # Ashvini is at index 0 in NAKSHATRA_NAMES
    span = Span(name='Ashvini', start=start, end=end)

    # Create a mock ghatis list.
    # The length must be at least up to the index. Let's make it 27, all 0s, except index 0 which we test.
    # Let's say the window starts at 30 ghatis.
    ghatis = [0] * 27
    ghatis[0] = 30

    # Run function
    window = nakshatra_ghati_window(span, ghatis, 'Test Window')

    # Calculations:
    # duration = 60 hours
    # start_offset = 60 * (30/60) = 30 hours
    # window duration = 60 * (4/60) = 4 hours
    expected_start = start + timedelta(hours=30)
    expected_end = expected_start + timedelta(hours=4)

    assert window.name == 'Test Window'
    assert window.start == expected_start
    assert window.end == expected_end

