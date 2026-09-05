# Festival dates verified against drikpanchang.com day pages
# (Hyderabad, geoname 1269843) "Day Festivals and Events" for 2026.
from datetime import date
from functools import lru_cache

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


@lru_cache(maxsize=None)
def fests(y, m, d):
    return ENGINE.calculate(date(y, m, d), HYD, include_eclipse=False).festivals


# --- Solar (Sankranti cluster) ---

def test_bhogi():
    assert 'Bhogi' in fests(2026, 1, 13)

def test_makara_sankranti():
    assert 'Makara Sankranti' in fests(2026, 1, 14)
    assert 'Makara Sankranti' not in fests(2026, 1, 15)

def test_kanuma():
    assert 'Kanuma' in fests(2026, 1, 15)


# --- Sunrise-tithi festivals ---

def test_vasanta_panchami():
    assert 'Vasanta Panchami' in fests(2026, 1, 23)

def test_ratha_saptami():
    assert 'Ratha Saptami' in fests(2026, 1, 25)

def test_ugadi():
    assert 'Ugadi' in fests(2026, 3, 19)

def test_hanuman_jayanti_telugu():
    assert 'Hanuman Jayanti' in fests(2026, 5, 12)

def test_guru_pournami():
    assert 'Guru Pournami' in fests(2026, 7, 29)

def test_raksha_bandhan():
    assert 'Raksha Bandhan' in fests(2026, 8, 28)

def test_mahalaya_amavasya():
    assert 'Mahalaya Amavasya' in fests(2026, 10, 10)

def test_navaratri_begins():
    assert 'Sharad Navaratri begins' in fests(2026, 10, 11)

def test_durgashtami():
    assert 'Durgashtami' in fests(2026, 10, 19)

def test_atla_taddi():
    assert 'Atla Taddi' in fests(2026, 10, 28)

def test_naraka_chaturdashi():
    assert 'Naraka Chaturdashi' in fests(2026, 11, 8)

def test_nagula_chavithi():
    assert 'Nagula Chavithi' in fests(2026, 11, 13)

def test_karthika_pournami():
    assert 'Karthika Pournami' in fests(2026, 11, 24)

def test_naga_panchami_telugu():
    assert 'Naga Panchami' in fests(2026, 12, 14)

def test_subrahmanya_shashti():
    assert 'Subrahmanya Shashti' in fests(2026, 12, 15)

def test_holi():
    assert 'Holi' in fests(2026, 3, 4)


# --- Weekday-dependent ---

def test_varalakshmi_vratam():
    assert 'Varalakshmi Vratam' in fests(2026, 8, 28)
    # The earlier Shravana Friday is too far from Pournami
    assert 'Varalakshmi Vratam' not in fests(2026, 8, 21)

def test_karthika_somavaram():
    assert 'Karthika Somavaram' in fests(2026, 11, 16)
    assert 'Karthika Somavaram' in fests(2026, 11, 23)
    assert 'Karthika Somavaram' not in fests(2026, 11, 17)


# --- Madhyahna-decided (tithi at midday, not sunrise) ---

def test_sri_rama_navami_smarta():
    assert 'Sri Rama Navami' in fests(2026, 3, 26)
    assert 'Sri Rama Navami' not in fests(2026, 3, 27)

def test_akshaya_tritiya():
    assert 'Akshaya Tritiya' in fests(2026, 4, 19)
    assert 'Akshaya Tritiya' not in fests(2026, 4, 20)

def test_vinayaka_chavithi():
    assert 'Vinayaka Chavithi' in fests(2026, 9, 14)
    assert 'Vinayaka Chavithi' not in fests(2026, 9, 15)


# --- Aparahna-decided ---

def test_maharnavami():
    assert 'Maharnavami' in fests(2026, 10, 19)

def test_vijayadashami():
    assert 'Vijayadashami (Dasara)' in fests(2026, 10, 20)
    assert 'Vijayadashami (Dasara)' not in fests(2026, 10, 21)


# --- Nishita / pradosha-decided ---

def test_maha_shivaratri():
    assert 'Maha Shivaratri' in fests(2026, 2, 15)

def test_krishna_janmashtami():
    assert 'Krishna Janmashtami' in fests(2026, 9, 4)

def test_deepavali():
    assert 'Deepavali' in fests(2026, 11, 8)
    assert 'Deepavali' not in fests(2026, 11, 9)

def test_holika_dahan():
    assert 'Holika Dahan' in fests(2026, 3, 3)


# --- Monthly vrats ---

def test_sankashti_chaturthi():
    assert 'Sankashti Chaturthi' in fests(2026, 10, 29)

def test_masa_shivaratri():
    assert 'Masa Shivaratri' in fests(2026, 11, 7)
    # On Maha Shivaratri day only the major name is shown
    assert 'Masa Shivaratri' not in fests(2026, 2, 15)


# --- Adhika maasam: lunar festivals skip the intercalary month ---

def test_no_lunar_festivals_in_adhika_maasam():
    # 2026-06-01 falls in Adhika Jyeshtha
    day = ENGINE.calculate(date(2026, 6, 1), HYD, include_eclipse=False)
    assert day.maasam.startswith('Adhika')
    monthly = {'Sankashti Chaturthi', 'Masa Shivaratri'}
    assert all(f in monthly for f in day.festivals)
