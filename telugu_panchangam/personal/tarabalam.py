# Tarabalam: personal day-strength from one's janma (birth) nakshatra.
#
# Count from the janma nakshatra to the day's moon nakshatra, inclusive,
# then reduce modulo 9. The nine taras repeat in fixed order; taras
# 2, 4, 6, 8, 9 are auspicious and 1, 3, 5, 7 are to be avoided
# (Janma is treated as avoid, per the common Telugu convention).
from telugu_panchangam.panchangam_names import NAKSHATRA_NAMES

TARA_NAMES: list[str] = [
    'Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak',
    'Sadhana', 'Naidhana', 'Mitra', 'Parama Mitra',
]

AUSPICIOUS_TARAS: frozenset[int] = frozenset({2, 4, 6, 8, 9})


def _nak_index(name: str) -> int:
    try:
        return NAKSHATRA_NAMES.index(name)
    except ValueError:
        raise ValueError(
            f'Unknown nakshatra {name!r} — expected one of {NAKSHATRA_NAMES}'
        ) from None


def tara_number(janma_nakshatra: str, day_nakshatra: str) -> int:
    """Tara 1..9 for a person of `janma_nakshatra` on a `day_nakshatra` day."""
    count = (_nak_index(day_nakshatra) - _nak_index(janma_nakshatra)) % 27 + 1
    return (count - 1) % 9 + 1


def tara_name(n: int) -> str:
    return TARA_NAMES[n - 1]


def is_auspicious_tara(n: int) -> bool:
    return n in AUSPICIOUS_TARAS


def taras_for_day(day_nakshatra: str, janma_nakshatras: list[str]) -> list[dict]:
    """Tara of each group member on a `day_nakshatra` day."""
    out = []
    for janma in janma_nakshatras:
        n = tara_number(janma, day_nakshatra)
        out.append({
            'janma_nakshatra': janma,
            'tara': n,
            'name': tara_name(n),
            'auspicious': is_auspicious_tara(n),
        })
    return out


def good_for_all(day_nakshatra: str, janma_nakshatras: list[str]) -> bool:
    """True when the day is auspicious for every member of the group."""
    return all(t['auspicious'] for t in taras_for_day(day_nakshatra, janma_nakshatras))
