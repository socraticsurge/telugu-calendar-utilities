# Weekday -> set of nakshatras forming Sarvartha Siddhi Yoga.
_SARVARTHA_SIDDHI: dict[str, set[str]] = {
    'Adivaram':    {'Hasta', 'Mula', 'Pushya', 'Ashvini', 'Punarvasu', 'Anuradha', 'Shravana', 'Revati'},
    'Somavaram':   {'Shravana', 'Rohini', 'Mrigashira', 'Pushya', 'Anuradha'},
    'Mangalavaram': {'Ashvini', 'Krittika', 'Ashlesha', 'Uttara Ashadha', 'Uttara Phalguni', 'Uttara Bhadrapada'},
    'Budhavaram':  {'Krittika', 'Rohini', 'Hasta', 'Anuradha', 'Mrigashira'},
    'Guruvaram':   {'Ashvini', 'Punarvasu', 'Anuradha', 'Revati', 'Pushya', 'Swati'},
    'Shukravaram': {'Revati', 'Anuradha', 'Ashvini', 'Pushya', 'Shravana', 'Punarvasu'},
    'Shanivaram':  {'Swati', 'Rohini', 'Shravana'},
}

# Weekday -> single nakshatra forming Amrita Siddhi Yoga.
_AMRITA_SIDDHI: dict[str, str] = {
    'Adivaram':    'Hasta',
    'Somavaram':   'Mrigashira',
    'Mangalavaram': 'Ashvini',
    'Budhavaram':  'Anuradha',
    'Guruvaram':   'Pushya',
    'Shukravaram': 'Revati',
    'Shanivaram':  'Rohini',
}

# Weekday -> tithi number (1-15 within either paksha) forming Visha Yoga.
_VISHA_YOGA: dict[str, int] = {
    'Adivaram': 5, 'Somavaram': 6, 'Mangalavaram': 7, 'Budhavaram': 8,
    'Guruvaram': 9, 'Shukravaram': 10, 'Shanivaram': 11,
}

# Weekday -> tithi number(s) (1-15 within either paksha) forming Dagdha Yoga.
_DAGDHA_YOGA: dict[str, set[int]] = {
    'Adivaram': {12}, 'Somavaram': {11}, 'Mangalavaram': {5}, 'Budhavaram': {2, 3},
    'Guruvaram': {6}, 'Shukravaram': {8}, 'Shanivaram': {9},
}

_PUSHKARA_VARAS: set[str] = {'Adivaram', 'Mangalavaram', 'Shanivaram'}

_DVIPUSHKARA_TITHIS: set[int] = {2, 7, 12}
_DVIPUSHKARA_NAKSHATRAS: set[str] = {'Mrigashira', 'Chitra', 'Dhanishtha'}

_TRIPUSHKARA_TITHIS: set[int] = {2, 7, 12}
_TRIPUSHKARA_NAKSHATRAS: set[str] = {
    'Krittika', 'Punarvasu', 'Uttara Phalguni',
    'Vishakha', 'Uttara Ashadha', 'Purva Bhadrapada',
}


def _tithi_number(tithi_name: str) -> int:
    """1-15 tithi number within either paksha (Pratipat=1 ... Pournami/Amavasya=15)."""
    from telugu_panchangam.panchangam_names import TITHI_NAMES
    return (TITHI_NAMES.index(tithi_name) % 15) + 1


def get_special_yogas(vaaram: str, tithi_name: str, nakshatra_name: str) -> list[str]:
    """Return the list of special yogas (possibly empty) for the given day."""
    yogas: list[str] = []

    if nakshatra_name in _SARVARTHA_SIDDHI.get(vaaram, set()):
        yogas.append('Sarvartha Siddhi Yoga')

    if nakshatra_name == _AMRITA_SIDDHI.get(vaaram):
        yogas.append('Amrita Siddhi Yoga')

    tithi_number = _tithi_number(tithi_name)

    if tithi_number == _VISHA_YOGA.get(vaaram):
        yogas.append('Visha Yoga')

    if tithi_number in _DAGDHA_YOGA.get(vaaram, set()):
        yogas.append('Dagdha Yoga')

    if vaaram in _PUSHKARA_VARAS:
        if tithi_number in _DVIPUSHKARA_TITHIS and nakshatra_name in _DVIPUSHKARA_NAKSHATRAS:
            yogas.append('Dvipushkara Yoga')
        if tithi_number in _TRIPUSHKARA_TITHIS and nakshatra_name in _TRIPUSHKARA_NAKSHATRAS:
            yogas.append('Tripushkara Yoga')

    return yogas


# ---------------------------------------------------------------------------
# Anandadi 28 muhurta yogas (Muhurta Chintamani)
# ---------------------------------------------------------------------------

ANANDADI_YOGAS = [
    'Ananda', 'Kalidanda', 'Dhumra', 'Dhata', 'Saumya', 'Dhwanksha',
    'Dhwaja', 'Shrivatsa', 'Vajra', 'Mudgara', 'Chhatra', 'Maitra',
    'Manasa', 'Padma', 'Lumba', 'Utpat', 'Mrityu', 'Kaana',
    'Siddhi', 'Subha', 'Amrita', 'Musala', 'Gada', 'Matanga',
    'Raksha', 'Chara', 'Sthira', 'Vardhamana',
]

# Starting nakshatra offset (0-indexed into the 27 nakshatras) per weekday.
# Standard table from Muhurta Chintamani.
_VAARA_OFFSET = {
    'Adivaram':     0,    # Sunday   starts from Ashvini
    'Somavaram':    4,    # Monday   starts from Mrigashira (Mrigashira = index 4)
    'Mangalavaram': 8,    # Tuesday  starts from Ashlesha
    'Budhavaram':  12,    # Wednesday starts from Hasta
    'Guruvaram':   16,    # Thursday starts from Anuradha
    'Shukravaram': 19,    # Friday   starts from Purva Ashadha
    'Shanivaram':  23,    # Saturday starts from Shatabhisha
}

_NAKSHATRA_ORDER = [
    'Ashvini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha',
    'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
    'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada',
    'Revati',
]

ANANDADI_AUSPICIOUS = frozenset({
    'Ananda', 'Dhata', 'Saumya', 'Dhwaja', 'Shrivatsa', 'Chhatra', 'Maitra',
    'Manasa', 'Padma', 'Siddhi', 'Subha', 'Amrita', 'Matanga', 'Raksha',
    'Sthira', 'Vardhamana',
})

ANANDADI_INAUSPICIOUS = frozenset({
    'Kalidanda', 'Dhumra', 'Dhwanksha', 'Vajra', 'Mudgara', 'Lumba', 'Utpat',
    'Mrityu', 'Kaana', 'Musala', 'Gada', 'Chara',
})


def compute_anandadi_yoga(vaaram: str, nakshatra: str) -> str | None:
    """Return the Anandadi muhurta yoga for the given vaaram + nakshatra."""
    offset = _VAARA_OFFSET.get(vaaram)
    if offset is None or nakshatra not in _NAKSHATRA_ORDER:
        return None
    nak_idx = _NAKSHATRA_ORDER.index(nakshatra)
    return ANANDADI_YOGAS[(nak_idx - offset) % 28]
