from abc import ABC, abstractmethod
from datetime import date
from telugu_panchangam.models.panchangam_day import Location, PanchangamDay, Span, Window

TITHI_NAMES: list[str] = [
    # Shukla Paksha (0-14)
    'Shukla Pratipat', 'Shukla Dwitiya', 'Shukla Tritiya', 'Shukla Chaturthi',
    'Shukla Panchami', 'Shukla Shashthi', 'Shukla Saptami', 'Shukla Ashtami',
    'Shukla Navami', 'Shukla Dashami', 'Shukla Ekadashi', 'Shukla Dwadashi',
    'Shukla Trayodashi', 'Shukla Chaturdashi', 'Pournami',
    # Krishna Paksha (15-29)
    'Krishna Pratipat', 'Krishna Dwitiya', 'Krishna Tritiya', 'Krishna Chaturthi',
    'Krishna Panchami', 'Krishna Shashthi', 'Krishna Saptami', 'Krishna Ashtami',
    'Krishna Navami', 'Krishna Dashami', 'Krishna Ekadashi', 'Krishna Dwadashi',
    'Krishna Trayodashi', 'Krishna Chaturdashi', 'Amavasya',
]

NAKSHATRA_NAMES: list[str] = [
    'Ashvini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha',
    'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha',
    'Shravana', 'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada',
    'Uttara Bhadrapada', 'Revati',
]

YOGA_NAMES: list[str] = [
    'Vishkambha', 'Preeti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda',
    'Sukarma', 'Dhriti', 'Shoola', 'Ganda', 'Vriddhi', 'Dhruva',
    'Vyaghata', 'Harshana', 'Vajra', 'Siddhi', 'Vyatipata', 'Variyan',
    'Parigha', 'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla',
    'Brahma', 'Indra', 'Vaidhriti',
]

RASHI_NAMES: list[str] = [
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
    'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
]

MAASAM_NAMES: list[str] = [
    'Chaitra', 'Vaishakha', 'Jyeshtha', 'Ashadha',
    'Shravana', 'Bhadrapada', 'Ashvina', 'Kartika',
    'Margashira', 'Pushya', 'Magha', 'Phalguna',
]

SAMVATSARA_NAMES: list[str] = [
    'Prabhava', 'Vibhava', 'Shukla', 'Pramoduta', 'Prajapati',
    'Angirasa', 'Shrimukha', 'Bhava', 'Yuva', 'Dhata',
    'Ishvara', 'Bahudhanya', 'Pramadi', 'Vikrama', 'Vrisha',
    'Chitrabhanu', 'Subhanu', 'Tarana', 'Parthiva', 'Vyaya',
    'Sarvajit', 'Sarvadharin', 'Virodhi', 'Vikrita', 'Khara',
    'Nandana', 'Vijaya', 'Jaya', 'Manmatha', 'Durmukhi',
    'Hevilambi', 'Vilambi', 'Vikari', 'Sharvari', 'Plava',
    'Shubhakrit', 'Shobhakrit', 'Krodhi', 'Vishvavasu', 'Parabhava',
    'Plavanga', 'Kilaka', 'Saumya', 'Sadharana', 'Virodhikrit',
    'Paridhavi', 'Pramadicha', 'Ananda', 'Rakshasa', 'Nala',
    'Pingala', 'Kalayukti', 'Siddharthi', 'Raudra', 'Durmati',
    'Dundubhi', 'Rudhirodgari', 'Raktakshi', 'Krodhana', 'Kshaya',
]

# Drik ritu: seasons are tropical (sayana), anchored to the solstices —
# Shishira starts at Uttarayana (winter solstice), each ritu spans two
# tropical signs. Indexed by tropical sun sign (0 = Aries .. 11 = Pisces).
# Verified against drikpanchang.com "Drik Ritu" (e.g. Grishma 2026 runs
# Apr 20 - Jun 21, the tropical Taurus + Gemini stretch).
RITUVU_NAMES: list[str] = [
    'Vasanta',                 # Aries
    'Grishma', 'Grishma',      # Taurus, Gemini
    'Varsha', 'Varsha',        # Cancer, Leo
    'Sharad', 'Sharad',        # Virgo, Libra
    'Hemanta', 'Hemanta',      # Scorpio, Sagittarius
    'Shishira', 'Shishira',    # Capricorn, Aquarius
    'Vasanta',                 # Pisces
]


def rituvu_name(jd: float) -> str:
    """Drik ritu at instant `jd`, from the tropical sun sign."""
    from telugu_panchangam.engines.utils import tropical_sun_longitude
    return RITUVU_NAMES[int(tropical_sun_longitude(jd) / 30.0) % 12]


# Uttarayanam runs Makara through Mithuna (sidereal signs 9..2),
# Dakshinayanam Karkataka through Dhanu (3..8).
_UTTARAYANAM_SIGNS = frozenset({9, 10, 11, 0, 1, 2})


def ayanam_name(sun_sign_idx: int) -> str:
    return 'Uttarayanam' if sun_sign_idx in _UTTARAYANAM_SIGNS else 'Dakshinayanam'

VAARAM_NAMES: list[str] = [
    'Adivaram', 'Somavaram', 'Mangalavaram', 'Budhavaram',
    'Guruvaram', 'Shukravaram', 'Shanivaram',
]

KARANA_REPEATING: list[str] = [
    'Bava', 'Balava', 'Kaulava', 'Taitila', 'Garaja', 'Vanija', 'Vishti',
]
KARANA_FIXED: dict[int, str] = {
    0: 'Kinstughna',
    57: 'Shakuni',
    58: 'Chatushpada',
    59: 'Naga',
}


_KALI_EPOCH_JD = 588465.5
_SIDEREAL_YEAR_DAYS = 365.25636


def samvatsara_name(jd: float, maasam: str) -> str:
    """Telugu (southern, Chaitradi) 60-year Samvatsara name at instant `jd`.

    Counts solar years elapsed since the Kali epoch. The ahargana is shifted
    by the current lunar month so the year flips at Chaitra (Ugadi) rather
    than at the mean solar boundary. Offset +12 anchors the cycle so that
    Kali 5128 (2026-27 CE) is Parabhava.
    """
    base = maasam.removeprefix('Adhika ').removeprefix('Nija ')
    maasa_num = MAASAM_NAMES.index(base) + 1
    ahargana = jd - _KALI_EPOCH_JD
    kali_elapsed = int((ahargana + (4 - maasa_num) * 30) / _SIDEREAL_YEAR_DAYS)
    return SAMVATSARA_NAMES[(kali_elapsed + 12) % 60]


def maasam_name(elongation_func, sun_longitude_func, jd_sunrise: float) -> str:
    """Amanta lunar month name at jd_sunrise, with Adhika/Nija prefix.

    The month is named from the sun's sign at its starting new moon. When the
    sun occupies the same sign at both bounding new moons, the month contains
    no sankranti and is Adhika; the following month repeats the name as Nija.
    """
    from telugu_panchangam.engines.utils import next_new_moon, previous_new_moon

    nm_start = previous_new_moon(elongation_func, jd_sunrise)
    sign_start = int(sun_longitude_func(nm_start) / 30.0) % 12
    name = MAASAM_NAMES[(sign_start - 11) % 12]

    nm_end = next_new_moon(elongation_func, nm_start + 1.0)
    if sign_start == int(sun_longitude_func(nm_end) / 30.0) % 12:
        return f'Adhika {name}'

    nm_prev = previous_new_moon(elongation_func, nm_start - 1.0)
    if sign_start == int(sun_longitude_func(nm_prev) / 30.0) % 12:
        return f'Nija {name}'

    return name


# Traditional Ekadashi names by Amanta maasam and paksham. Both Ekadashis of
# an Adhika maasam have their own names (Padmini/Parama) regardless of month.
EKADASHI_NAMES: dict[str, dict[str, str]] = {
    'Chaitra':    {'Shukla': 'Kamada',      'Krishna': 'Varuthini'},
    'Vaishakha':  {'Shukla': 'Mohini',      'Krishna': 'Apara'},
    'Jyeshtha':   {'Shukla': 'Nirjala',     'Krishna': 'Yogini'},
    'Ashadha':    {'Shukla': 'Shayani',     'Krishna': 'Kamika'},
    'Shravana':   {'Shukla': 'Putrada',     'Krishna': 'Aja'},
    'Bhadrapada': {'Shukla': 'Parivartini', 'Krishna': 'Indira'},
    'Ashvina':    {'Shukla': 'Papankusha',  'Krishna': 'Rama'},
    'Kartika':    {'Shukla': 'Prabodhini',  'Krishna': 'Utpanna'},
    'Margashira': {'Shukla': 'Mokshada',    'Krishna': 'Saphala'},
    'Pushya':     {'Shukla': 'Putrada',     'Krishna': 'Shattila'},
    'Magha':      {'Shukla': 'Jaya',        'Krishna': 'Vijaya'},
    'Phalguna':   {'Shukla': 'Amalaki',     'Krishna': 'Papamochani'},
}


# ---------------------------------------------------------------------------
# Muhurta window tables — verified against Drik Panchang (Hyderabad, Jun–Aug
# 2026 day panchang pages). Weekday convention throughout: 0=Sunday.
# ---------------------------------------------------------------------------

# Rahu Kalam / Gulika Kalam / Yamagandam: 1-indexed part of the 8-part day.
RAHU_PART   = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}
GULIKA_PART = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}
YAMAG_PART  = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}

# Durmuhurtham: 1-indexed muhurtas of the 15-muhurta day; Tuesday has a
# second window at night (1-indexed muhurta of the 15-muhurta night).
DURMUHURTA_DAY_MUHURTAS = {0: (14,), 1: (9, 12), 2: (4,), 3: (8,), 4: (6, 12), 5: (4, 9), 6: (1, 2)}
DURMUHURTA_NIGHT_MUHURTAS = {2: (7,)}

# Varjyam (Tyajya) and Amrita Kalam: classical start ghatis per nakshatra on
# the 60-ghati scale of the nakshatra's actual span; both last 4 such ghatis.
# Order matches NAKSHATRA_NAMES (Ashvini … Revati).
VARJYAM_GHATIS: list[int] = [
    50, 24, 30, 40, 14, 21, 30, 20, 32,
    30, 20, 18, 21, 20, 14, 14, 10, 14,
    56, 24, 20, 10, 10, 18, 16, 24, 30,
]
AMRITA_GHATIS: list[int] = [
    42, 48, 54, 52, 38, 35, 54, 44, 56,
    54, 44, 42, 45, 44, 38, 38, 34, 38,
    44, 48, 44, 34, 34, 42, 40, 48, 54,
]


def nakshatra_ghati_window(span: Span, ghatis: list[int], label: str) -> Window:
    """The window starting `ghatis[nak]`/60 into the span, lasting 4/60 of it."""
    idx = NAKSHATRA_NAMES.index(span.name)
    dur = span.end - span.start
    start = span.start + dur * (ghatis[idx] / 60.0)
    return Window(name=label, start=start, end=start + dur * (4.0 / 60.0))


def nakshatra_day_windows(spans: list[Span], ghatis: list[int], label: str,
                          day_start, day_end) -> list[Window]:
    """Windows from `spans` that begin within the panchangam day
    [day_start, day_end) — the convention printed panchangams follow."""
    out = []
    for span in spans:
        w = nakshatra_ghati_window(span, ghatis, label)
        if day_start <= w.start < day_end:
            out.append(w)
    return out


def next_nakshatra_span(span: Span, moon_longitude_func) -> Span:
    """The nakshatra span immediately following `span`, using the engine's
    own moon-longitude model."""
    from telugu_panchangam.engines.utils import datetime_to_jd, jd_to_utc, find_crossing
    idx = (NAKSHATRA_NAMES.index(span.name) + 1) % 27
    nak_size = 360.0 / 27.0
    jd_start = datetime_to_jd(span.end)
    jd_end = find_crossing(moon_longitude_func, (idx + 1) * nak_size,
                           jd_start, jd_start + 2.0)
    return Span(name=NAKSHATRA_NAMES[idx], start=span.end, end=jd_to_utc(jd_end))


def ekadashi_name(maasam: str, paksham: str, solar_sign: str) -> str | None:
    """Traditional name of the Ekadashi falling in `maasam`/`paksham`.

    Vaikunta (Mukkoti) Ekadashi is tied to Dhanurmasa — the Shukla Ekadashi
    while the sun is in Dhanu — not to a fixed lunar month.
    """
    if maasam.startswith('Adhika'):
        return 'Padmini' if paksham == 'Shukla' else 'Parama'
    name = EKADASHI_NAMES.get(maasam.removeprefix('Nija '), {}).get(paksham)
    if name and paksham == 'Shukla' and solar_sign == 'Dhanu':
        return f'{name} (Vaikunta)'
    return name


# ---------------------------------------------------------------------------
# Festivals (Telugu / amanta conventions). Each entry: (maasam, tithi index,
# name) with tithi indices 0=Shukla Pratipat .. 14=Pournami .. 29=Amavasya.
# Which moment decides the day varies by festival; all 2026 dates verified
# against drikpanchang.com "Day Festivals and Events" (Hyderabad).
# ---------------------------------------------------------------------------

GANDA_MOOLA_NAKSHATRAS: frozenset[str] = frozenset(
    {'Ashvini', 'Ashlesha', 'Magha', 'Jyeshtha', 'Mula', 'Revati'})

_SUNRISE_FESTIVALS: list[tuple[str, int, str]] = [
    ('Vaishakha',  24, 'Hanuman Jayanti'),          # Telugu: Vaishakha Krishna Dashami
    ('Ashadha',    14, 'Guru Pournami'),
    ('Shravana',   14, 'Raksha Bandhan'),
    ('Shravana',   22, 'Krishna Janmashtami'),
    ('Bhadrapada', 29, 'Mahalaya Amavasya'),
    ('Ashvina',    0,  'Sharad Navaratri begins'),
    ('Ashvina',    7,  'Durgashtami'),
    ('Ashvina',    17, 'Atla Taddi'),
    ('Ashvina',    28, 'Naraka Chaturdashi'),
    ('Kartika',    3,  'Nagula Chavithi'),
    ('Kartika',    14, 'Karthika Pournami'),
    ('Margashira', 4,  'Naga Panchami'),            # Telugu convention
    ('Margashira', 5,  'Subrahmanya Shashti'),
    ('Magha',      4,  'Vasanta Panchami'),
    ('Magha',      6,  'Ratha Saptami'),
    ('Phalguna',   14, 'Holika Dahan'),
    ('Phalguna',   15, 'Holi'),                     # day after Holika Dahan
]

_MADHYAHNA_FESTIVALS: list[tuple[str, int, str]] = [
    ('Chaitra',    0, 'Ugadi'),    # pratipada can be kshaya: decided at midday
    ('Chaitra',    8, 'Sri Rama Navami'),
    ('Vaishakha',  2, 'Akshaya Tritiya'),
    ('Bhadrapada', 3, 'Vinayaka Chavithi'),
]

_APARAHNA_FESTIVALS: list[tuple[str, int, str]] = [
    ('Ashvina', 8, 'Maharnavami'),
    ('Ashvina', 9, 'Vijayadashami (Dasara)'),
]

_PRADOSHA_FESTIVALS: list[tuple[str, int, str]] = [
    ('Ashvina',  29, 'Deepavali'),
]

_NISHITA_FESTIVALS: list[tuple[str, int, str]] = [
    ('Magha',    28, 'Maha Shivaratri'),
]


class PanchangamEngine(ABC):
    @abstractmethod
    def calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:
        """Calculate full Panchangam for a single date and location."""
        ...

    def _sun_sign_idx_at(self, jd: float) -> int:
        """Sidereal sun sign index (0=Mesha) at jd, per this engine's model."""
        raise NotImplementedError

    def _is_makara_day(self, jd_sr: float, jd_ss: float) -> bool:
        """Makara Sankranti is observed the day the sun enters Makara, unless
        the entry falls after sunset — then the following day."""
        sr, ss = self._sun_sign_idx_at(jd_sr), self._sun_sign_idx_at(jd_ss)
        if sr != 9 and ss == 9:
            return True   # entry between today's sunrise and sunset
        if sr == 9 and self._sun_sign_idx_at(jd_ss - 1.0) != 9 \
                   and self._sun_sign_idx_at(jd_sr - 1.0) != 9:
            return True   # entry after yesterday's sunset
        return False

    def _sankramanam_name(self, jd_sr: float, jd_ss: float) -> str | None:
        """Name of the rashi the sun enters this day, or None. Uses the same
        convention as Makara Sankranti: entry after sunset belongs to the
        next day."""
        sr, ss = self._sun_sign_idx_at(jd_sr), self._sun_sign_idx_at(jd_ss)
        if sr != ss:
            return RASHI_NAMES[ss]
        prev_sr = self._sun_sign_idx_at(jd_sr - 1.0)
        prev_ss = self._sun_sign_idx_at(jd_ss - 1.0)
        if sr != prev_ss and prev_ss == prev_sr:
            return RASHI_NAMES[sr]
        return None

    def _festivals(self, maasam: str, weekday: int,
                   jd_sr: float, jd_ss: float, jd_next_sr: float,
                   jd_moonrise: float) -> list[str]:
        fests: list[str] = []

        # --- Solar: Sankranti cluster ---
        if self._is_makara_day(jd_sr, jd_ss):
            fests.append('Makara Sankranti')
        if self._is_makara_day(jd_next_sr, jd_ss + 1.0):
            fests.append('Bhogi')
        if self._is_makara_day(jd_sr - 1.0, jd_ss - 1.0):
            fests.append('Kanuma')

        t_sr = self._tithi_index_at(jd_sr)
        nishita = (jd_ss + jd_next_sr) / 2.0

        # --- Lunar festivals (skip the intercalary Adhika month) ---
        if not maasam.startswith('Adhika'):
            base_m = maasam.removeprefix('Nija ')
            for m, idx, name in _SUNRISE_FESTIVALS:
                if base_m == m and t_sr == idx:
                    fests.append(name)
            moments = [
                (_MADHYAHNA_FESTIVALS, jd_sr + 0.5 * (jd_ss - jd_sr)),
                (_APARAHNA_FESTIVALS,  jd_sr + 0.7 * (jd_ss - jd_sr)),
                (_PRADOSHA_FESTIVALS,  jd_ss + 0.05),
                (_NISHITA_FESTIVALS,   nishita),
            ]
            for rules, jd_moment in moments:
                t_now = self._tithi_index_at(jd_moment)
                # the same tithi can prevail at this moment two days running;
                # the festival belongs to the first
                t_prev = self._tithi_index_at(jd_moment - 1.0)
                # when sunrise was Amavasya and pratipada has begun, the
                # amanta month has rolled over by this moment
                if t_sr == 29 and t_now == 0:
                    m_moment = MAASAM_NAMES[(MAASAM_NAMES.index(base_m) + 1) % 12]
                else:
                    m_moment = base_m
                for m, idx, name in rules:
                    if m_moment == m and t_now == idx and t_prev != idx:
                        fests.append(name)
            if base_m == 'Kartika' and weekday == 1:
                fests.append('Karthika Somavaram')
            # Varalakshmi Vratam: the last Shukla-paksha Friday on or before
            # Shravana Pournami (the next Friday falls in Krishna paksha)
            if base_m == 'Shravana' and weekday == 5 and t_sr <= 14 \
                    and self._tithi_index_at(jd_sr + 7.0) >= 15:
                fests.append('Varalakshmi Vratam')

        # --- Monthly vrats (observed in Adhika months too) ---
        if jd_ss < jd_moonrise < jd_next_sr:
            jd_sankashti = jd_moonrise
        else:
            jd_sankashti = jd_ss + 0.1
        if self._tithi_index_at(jd_sankashti) == 18 \
                and self._tithi_index_at(jd_sankashti - 1.0) != 18:
            fests.append('Sankashti Chaturthi')
        if 'Maha Shivaratri' not in fests \
                and self._tithi_index_at(nishita) == 28 \
                and self._tithi_index_at(nishita - 1.0) != 28:
            fests.append('Masa Shivaratri')

        return fests
