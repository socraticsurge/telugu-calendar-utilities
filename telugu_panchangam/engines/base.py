from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from telugu_panchangam.models.panchangam_day import (
    Location, PanchangamDay, SlotFacts, Span, Window,
)
from telugu_panchangam.panchangam_names import (
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES, RASHI_NAMES,
    MAASAM_NAMES, SAMVATSARA_NAMES, RITUVU_NAMES, VAARAM_NAMES,
    KARANA_REPEATING, KARANA_FIXED, EKADASHI_NAMES, GANDA_MOOLA_NAKSHATRAS,
)


def rituvu_name(jd: float) -> str:
    """Drik ritu at instant `jd`, from the tropical sun sign."""
    from telugu_panchangam.engines.utils import tropical_sun_longitude
    return RITUVU_NAMES[int(tropical_sun_longitude(jd) / 30.0) % 12]


# Uttarayanam runs Makara through Mithuna (sidereal signs 9..2),
# Dakshinayanam Karkataka through Dhanu (3..8).
_UTTARAYANAM_SIGNS = frozenset({9, 10, 11, 0, 1, 2})


def ayanam_name(sun_sign_idx: int) -> str:
    return 'Uttarayanam' if sun_sign_idx in _UTTARAYANAM_SIGNS else 'Dakshinayanam'


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

# --- Specialty rule tables (previously inline-cased in _festivals) ---
#
# These four rule patterns were special cases inside the _festivals body
# until Phase 6. Lifting them into named tables makes the dispatcher
# uniform: every festival is now described by a row in a table, not by
# a block of inline conditionals.
#
# Adding new festivals of these shapes is now an "append a row" change
# — the routine modification CLAUDE.md explicitly permits.

# Pattern: every <weekday> of <maasam>. No tithi condition.
# Example: Karthika Somavaram = every Monday in Kartika maasam.
# Weekday convention: 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat
# (matches the `weekday` int passed into _festivals).
_WEEKDAY_IN_MAASAM_FESTIVALS: list[tuple[str, int, str]] = [
    ('Kartika',  1, 'Karthika Somavaram'),
]

# Pattern: the LAST <weekday> in <paksham> of <maasam>. "Last" means
# the next <weekday> falls in the other paksham (i.e., crossed
# Pournami if paksha=Shukla, or crossed Amavasya if paksha=Krishna).
# Example: Varalakshmi Vratam = the last Shukla Friday in Shravana
# (the next Friday falls in Krishna paksha, after Shravana Pournami).
_LAST_WEEKDAY_IN_PAKSHAM_FESTIVALS: list[tuple[str, int, str, str]] = [
    # (maasam, weekday_idx, paksham, festival_name)
    ('Shravana', 5, 'Shukla', 'Varalakshmi Vratam'),
]

# Pattern: every month, the tithi at moonrise equals <tithi_idx>
# (with the prev-day moonrise tithi check to dedupe a tithi that
# spans two moonrises). Observed in Adhika months too.
# Example: Sankashti Chaturthi = Krishna Chaturthi (tithi 18) at moonrise.
_MOONRISE_MONTHLY_FESTIVALS: list[tuple[int, str]] = [
    # (tithi_idx, festival_name)
    (18, 'Sankashti Chaturthi'),
]

# Pattern: every month, the tithi at nishita equals <tithi_idx>
# (with the prev-day nishita tithi check). Suppressed when the
# annual variant fires the same day (e.g. Masa Shivaratri yields
# to Maha Shivaratri in Magha).
# Example: Masa Shivaratri = Krishna Chaturdashi (tithi 28) at nishita,
# except when Maha Shivaratri (annual, also tithi 28) fires.
_NISHITA_MONTHLY_FESTIVALS: list[tuple[int, str, str | None]] = [
    # (tithi_idx, festival_name, suppress_if_present)
    (28, 'Masa Shivaratri', 'Maha Shivaratri'),
]


class PanchangamEngine(ABC):
    @abstractmethod
    def calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:
        """Calculate full Panchangam for a single date and location."""
        ...

    def calculate_bulk(self, start_date: date, days: int, location: Location, include_eclipse: bool = True) -> list[PanchangamDay]:
        """Calculate full Panchangam for a consecutive range of days and location.
        Default implementation calls `calculate` sequentially.
        """
        from datetime import timedelta
        return [self.calculate(start_date + timedelta(days=i), location, include_eclipse) for i in range(days)]

    # --- Per-instant fact computation (slot-time precision) --------------
    #
    # Subclasses expose the two longitude functions they use; the base
    # class derives every other anga name from them. Each engine keeps its
    # own astronomical model (Drik = Swiss Ephemeris; SS = mean motion +
    # manda correction; Vakya = tables + Moon correction).

    def _sun_longitude_func(self):
        """Function f(jd) -> sidereal Sun longitude in degrees [0, 360)."""
        raise NotImplementedError

    def _moon_longitude_func(self):
        """Function f(jd) -> sidereal Moon longitude in degrees [0, 360)."""
        raise NotImplementedError

    def facts_at(self, dt: datetime, location: Location,
                 vaaram: str | None = None) -> SlotFacts:
        """Return the panchangam facts active at `dt` for this engine.

        The vaaram of the panchangam day (one constant per civil-day-at-
        sunrise) is supplied by the caller, since vaaram is decided by
        the sunrise weekday and does not flip during the day. If omitted,
        we derive it from the UTC weekday of `dt` — which is an
        approximation suitable for slot-time scoring within a single day.
        """
        # Local import to avoid circular dependency: special_yogas
        # imports TITHI_NAMES from this module.
        from telugu_panchangam.special_yogas import get_special_yogas
        from telugu_panchangam.engines.utils import datetime_to_jd

        # Anchor dt in UTC
        dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        jd = datetime_to_jd(dt_utc)

        sun_long_fn = self._sun_longitude_func()
        moon_long_fn = self._moon_longitude_func()
        sun_long = sun_long_fn(jd) % 360.0
        moon_long = moon_long_fn(jd) % 360.0
        elongation = (moon_long - sun_long) % 360.0

        # Nakshatra: Moon longitude / (360/27)
        nak_size = 360.0 / 27.0
        nak_idx = int(moon_long / nak_size) % 27
        nakshatra_name = NAKSHATRA_NAMES[nak_idx]

        # Tithi: elongation / 12
        tithi_idx = int(elongation / 12.0) % 30
        tithi_name = TITHI_NAMES[tithi_idx]

        # Nitya Yoga: (Sun + Moon) longitude / (360/27)
        yoga_combined = (sun_long + moon_long) % 360.0
        yoga_idx = int(yoga_combined / nak_size) % 27
        yoga_name = YOGA_NAMES[yoga_idx]

        # Karana: half-tithi
        ht_idx = int(elongation / 6.0) % 60
        if ht_idx in KARANA_FIXED:
            karana_name = KARANA_FIXED[ht_idx]
        else:
            karana_name = KARANA_REPEATING[(ht_idx - 1) % 7]

        # Moon's rashi (12 signs, 30 degrees each)
        rashi_idx = int(moon_long / 30.0) % 12
        lunar_sign_name = RASHI_NAMES[rashi_idx]

        # Vaaram: passed in (sunrise-decided). Fallback to UTC weekday — but
        # callers from day_slots will always pass the day's vaaram.
        if vaaram is None:
            # Map Python weekday (Mon=0..Sun=6) to our Adivaram(Sun=0)..
            vaaram = VAARAM_NAMES[(dt_utc.weekday() + 1) % 7]

        special_yogas = get_special_yogas(vaaram, tithi_name, nakshatra_name)

        return SlotFacts(
            nakshatra=nakshatra_name,
            tithi=tithi_name,
            yoga=yoga_name,
            karana=karana_name,
            lunar_sign=lunar_sign_name,
            vaaram=vaaram,
            special_yogas=special_yogas,
        )

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
        name, _ = self._sankramanam_name_and_jd(jd_sr, jd_ss)
        return name

    def _sankramanam_name_and_jd(
        self, jd_sr: float, jd_ss: float
    ) -> tuple[str | None, float | None]:
        """Name + exact JD of the Sun's rasi-ingress this day, or (None, None).

        Bisects for the crossing using this engine's sun-longitude model when
        a sign change is detected. The bisection window is chosen to span the
        crossing safely:
          - Intra-day crossing (between jd_sr and jd_ss): bisect in that range.
          - After-previous-sunset crossing (entry after yesterday's sunset counts
            today): bisect in [jd_sr - 1.0, jd_sr].
        """
        from telugu_panchangam.engines.utils import find_crossing
        sr = self._sun_sign_idx_at(jd_sr)
        ss = self._sun_sign_idx_at(jd_ss)
        if sr != ss:
            # Crossing happened between sunrise and sunset today
            target_deg = ss * 30.0
            jd_cross = find_crossing(
                self._sun_longitude_func(), target_deg, jd_sr, jd_ss
            )
            return RASHI_NAMES[ss], jd_cross
        prev_sr = self._sun_sign_idx_at(jd_sr - 1.0)
        prev_ss = self._sun_sign_idx_at(jd_ss - 1.0)
        if sr != prev_ss and prev_ss == prev_sr:
            # Crossing happened after yesterday's sunset (observed today)
            target_deg = sr * 30.0
            jd_cross = find_crossing(
                self._sun_longitude_func(), target_deg, jd_ss - 1.0, jd_sr
            )
            return RASHI_NAMES[sr], jd_cross
        return None, None

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
            # Weekday-in-maasam: e.g. Karthika Somavaram (every Monday in Kartika)
            for m, wd, name in _WEEKDAY_IN_MAASAM_FESTIVALS:
                if base_m == m and weekday == wd:
                    fests.append(name)
            # Last-weekday-in-paksham: e.g. Varalakshmi Vratam (last Shukla
            # Friday in Shravana, identified by "today is in this paksham
            # AND the same weekday a week from now has crossed into the
            # other paksham")
            for m, wd, paksha, name in _LAST_WEEKDAY_IN_PAKSHAM_FESTIVALS:
                if base_m != m or weekday != wd:
                    continue
                today_shukla = t_sr <= 14
                next_week_shukla = self._tithi_index_at(jd_sr + 7.0) <= 14
                this_paksha_now = today_shukla if paksha == 'Shukla' else (not today_shukla)
                crosses_paksha_in_week = (this_paksha_now != (next_week_shukla if paksha == 'Shukla' else (not next_week_shukla)))
                if this_paksha_now and crosses_paksha_in_week:
                    fests.append(name)

        # --- Monthly vrats (observed in Adhika months too) ---
        if jd_ss < jd_moonrise < jd_next_sr:
            jd_moonrise_eff = jd_moonrise
        else:
            jd_moonrise_eff = jd_ss + 0.1
        # Moonrise-monthly: e.g. Sankashti Chaturthi
        for tithi_idx, name in _MOONRISE_MONTHLY_FESTIVALS:
            if self._tithi_index_at(jd_moonrise_eff) == tithi_idx \
                    and self._tithi_index_at(jd_moonrise_eff - 1.0) != tithi_idx:
                fests.append(name)
        # Nishita-monthly with annual-variant suppression: e.g. Masa Shivaratri
        # (suppressed when Maha Shivaratri already fired today)
        for tithi_idx, name, suppress_if in _NISHITA_MONTHLY_FESTIVALS:
            if suppress_if and suppress_if in fests:
                continue
            if self._tithi_index_at(nishita) == tithi_idx \
                    and self._tithi_index_at(nishita - 1.0) != tithi_idx:
                fests.append(name)

        return fests

    def _build_ghati_clock(self, sunrise_dt, next_sunrise_dt):
        from telugu_panchangam.ghati import make_clock
        return make_clock(sunrise_dt, next_sunrise_dt)
