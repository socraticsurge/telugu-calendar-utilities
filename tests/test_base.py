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


def test_next_nakshatra_span():
    from datetime import datetime, timezone
    from unittest.mock import patch, MagicMock
    from telugu_panchangam.models.panchangam_day import Span
    from telugu_panchangam.engines.base import next_nakshatra_span

    span_end = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    # Test typical transition: Ashvini (0) -> Bharani (1)
    span = Span(name='Ashvini', start=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc), end=span_end)

    mock_moon_func = MagicMock()

    with patch('telugu_panchangam.engines.utils.find_crossing', return_value=2459947.5) as mock_find, \
         patch('telugu_panchangam.engines.utils.jd_to_utc', return_value=datetime(2023, 1, 2, 12, 0, tzinfo=timezone.utc)) as mock_jd_to_utc, \
         patch('telugu_panchangam.engines.utils.datetime_to_jd', return_value=2459946.5) as mock_dt_to_jd:

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
