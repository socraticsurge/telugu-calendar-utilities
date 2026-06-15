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
