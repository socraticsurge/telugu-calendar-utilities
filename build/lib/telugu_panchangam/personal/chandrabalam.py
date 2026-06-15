# Chandrabalam: daily strength from the Moon's rashi relative to one's
# janma rashi. Count from the janma rashi to the day's moon rashi,
# inclusive (1..12). Verified against drikpanchang.com chandrabalam
# timings: positions 1, 3, 6, 7, 10, 11 are good; 2, 5, 9 are workable
# with remedial puja; 4, 8, 12 are avoided (8 is Ashtama Chandra).
from telugu_panchangam.engines.base import RASHI_NAMES

CHANDRA_GOOD: frozenset[int] = frozenset({1, 3, 6, 7, 10, 11})
CHANDRA_PUJA: frozenset[int] = frozenset({2, 5, 9})


def _rasi_index(name: str) -> int:
    try:
        return RASHI_NAMES.index(name)
    except ValueError:
        raise ValueError(
            f'Unknown rashi {name!r} — expected one of {RASHI_NAMES}'
        ) from None


def chandra_position(janma_rasi: str, day_rasi: str) -> int:
    """Moon's position 1..12 counted from the janma rashi."""
    return (_rasi_index(day_rasi) - _rasi_index(janma_rasi)) % 12 + 1


def chandra_verdict(position: int) -> str:
    """'good' | 'puja' (workable with remedy) | 'bad'."""
    if position in CHANDRA_GOOD:
        return 'good'
    if position in CHANDRA_PUJA:
        return 'puja'
    return 'bad'


def is_favourable_chandra(position: int) -> bool:
    return position in CHANDRA_GOOD


def rasi_from_nakshatra(nakshatra: str, pada: int | None = None) -> str | None:
    """Janma rashi derived from the birth star (and padam where needed).

    Each rashi spans nine padas (2 1/4 nakshatras): 18 stars sit wholly in
    one rashi, nine straddle two. For a straddler with no padam, returns
    None — the rashi genuinely cannot be known from the star alone.
    """
    from telugu_panchangam.engines.base import NAKSHATRA_NAMES
    try:
        k = NAKSHATRA_NAMES.index(nakshatra)
    except ValueError:
        raise ValueError(
            f'Unknown nakshatra {nakshatra!r} — expected one of {NAKSHATRA_NAMES}'
        ) from None
    if pada is not None:
        if not 1 <= pada <= 4:
            raise ValueError('pada must be 1..4')
        return RASHI_NAMES[(k * 4 + pada - 1) // 9]
    first, last = (k * 4) // 9, (k * 4 + 3) // 9
    return RASHI_NAMES[first] if first == last else None
