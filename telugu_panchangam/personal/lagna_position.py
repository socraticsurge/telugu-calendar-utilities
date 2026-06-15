# Lagna position from janma rashi — the lagna (rising sign) analog of
# chandrabalam. Counts the same way: from the janma rashi to the rashi
# currently rising, inclusive (1..12). Classical Jyotisha treats certain
# positions as structurally strong (Kendra), prosperous (Trikona), or
# inauspicious (Ashtama / 8th from janma).
#
# Sources: Brihat Parashara Hora Shastra (ch. on Bhava-vichara, kendra
# and trikona doctrines); modern commentaries on muhurta selection
# (Muhurta Chintamani, ch. on Lagna-shuddhi); drikpanchang.com lagna
# muhurta tables.
from telugu_panchangam.engines.base import RASHI_NAMES

# Kendra (angular houses) — 1, 4, 7, 10 from janma rashi. Structural
# strength; favoured for any new beginning.
LAGNA_KENDRA: frozenset[int] = frozenset({1, 4, 7, 10})

# Trikona (trinal houses) — 1, 5, 9 from janma rashi. Auspicious /
# dharmic; favoured for ceremonies, prosperity-seeking activity.
LAGNA_TRIKONA: frozenset[int] = frozenset({1, 5, 9})

# Position 1 is in both sets — own rashi rising. Strongest single
# position; some traditions add an extra bonus when slot lagna == janma.
LAGNA_OWN: int = 1

# Ashtama (8th from janma) — classical "danger" position. Same logic
# as Ashtama Chandra: cap the slot's tier, don't merely subtract score.
LAGNA_ASHTAMA: int = 8


def _rasi_index(name: str) -> int:
    try:
        return RASHI_NAMES.index(name)
    except ValueError:
        raise ValueError(
            f'Unknown rashi {name!r} — expected one of {RASHI_NAMES}'
        ) from None


def lagna_position(janma_rasi: str, lagna_rasi: str) -> int:
    """Lagna's position 1..12 counted from the janma rashi."""
    return (_rasi_index(lagna_rasi) - _rasi_index(janma_rasi)) % 12 + 1


def lagna_verdict(position: int) -> str:
    """'own' | 'kendra' | 'trikona' | 'ashtama' | 'neutral'.

    ``own`` is returned for position 1 (kendra + trikona + own rashi).
    Otherwise kendra and trikona are reported distinctly even though
    a single slot will only ever match one of them at a time.
    """
    if position == LAGNA_OWN:
        return 'own'
    if position == LAGNA_ASHTAMA:
        return 'ashtama'
    if position in LAGNA_TRIKONA:
        return 'trikona'
    if position in LAGNA_KENDRA:
        return 'kendra'
    return 'neutral'


def is_favourable_lagna(position: int) -> bool:
    """True iff the position is kendra OR trikona (the union)."""
    return position in LAGNA_KENDRA or position in LAGNA_TRIKONA


def is_ashtama_lagna(position: int) -> bool:
    return position == LAGNA_ASHTAMA
