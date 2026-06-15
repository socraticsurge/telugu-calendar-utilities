# Tithi family classification — the 15 tithis grouped into 5 families
# of 3 each. The same families apply to both Shukla and Krishna pakshams.
#
#   Nanda  (1, 6, 11)   — joyful, prosperous, fame-bringing
#   Bhadra (2, 7, 12)   — permanence, stability
#   Jaya   (3, 8, 13)   — victory, conquest
#   Rikta  (4, 9, 14)   — empty, depleting (least auspicious)
#   Purna  (5, 10, 15)  — full, completion (Pournami / Amavasya)
#
# The classifier reads the *last word* of the tithi name so it works
# uniformly for engine output ('Krishna Trayodashi'), named Ekadashis
# ('Parama Ekadashi', 'Padmini Ekadashi'), and the two terminal aliases
# (Pournami and Amavasya — both tithi 15 in their paksham).

# Canonical last-word lookup. The engine emits 'Pratipat' and 'Shashthi'
# (matching base.TITHI_NAMES); we also accept the common alternates
# 'Pratipada' and 'Shashti' that appear in published panchangams.
TITHI_NAMES: list[str] = [
    'Pratipat',  'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
    'Shashthi',  'Saptami', 'Ashtami', 'Navami',    'Dashami',
    'Ekadashi',  'Dwadashi','Trayodashi','Chaturdashi','Pournami',
]

# Alternate spellings we may see in feeds / external sources.
_ALIASES = {
    'Pratipada': 1,   # common spelling for Pratipat
    'Prathama':  1,   # rarer alias for Pratipat
    'Shashti':   6,   # alternate spelling for Shashthi
    'Amavasya': 15,   # Krishna paksha terminal — same family as Pournami
}

TITHI_NUMBER_FAMILY: dict[int, str] = {
    1: 'Nanda',  6: 'Nanda', 11: 'Nanda',
    2: 'Bhadra', 7: 'Bhadra', 12: 'Bhadra',
    3: 'Jaya',   8: 'Jaya',  13: 'Jaya',
    4: 'Rikta',  9: 'Rikta', 14: 'Rikta',
    5: 'Purna', 10: 'Purna', 15: 'Purna',
}

FAMILIES = ('Nanda', 'Bhadra', 'Jaya', 'Rikta', 'Purna')


def tithi_number(name: str) -> int:
    """Tithi 1..15 from any of the names emitted by our engines/feeds.

    Accepts: 'Krishna Trayodashi', 'Shukla Panchami', 'Pournami',
    'Amavasya', 'Parama Ekadashi', 'Padmini Ekadashi', etc. The last
    word carries the canonical tithi name (or an alias).
    """
    if not name:
        raise ValueError('Empty tithi name')
    last = name.strip().split()[-1]
    if last in _ALIASES:
        return _ALIASES[last]
    if last in TITHI_NAMES:
        return TITHI_NAMES.index(last) + 1
    raise ValueError(f'Unknown tithi name: {name!r}')


def tithi_family(name: str) -> str:
    """Family for a tithi name. One of Nanda | Bhadra | Jaya | Rikta | Purna."""
    return TITHI_NUMBER_FAMILY[tithi_number(name)]


def is_rikta(name: str) -> bool:
    """True when the tithi is Rikta (4, 9, 14) — universally avoided."""
    try:
        return tithi_family(name) == 'Rikta'
    except ValueError:
        return False
