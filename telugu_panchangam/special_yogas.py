from telugu_panchangam.engines.base import TITHI_NAMES

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


def _tithi_number(tithi_name: str) -> int:
    """1-15 tithi number within either paksha (Pratipat=1 ... Pournami/Amavasya=15)."""
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

    return yogas
