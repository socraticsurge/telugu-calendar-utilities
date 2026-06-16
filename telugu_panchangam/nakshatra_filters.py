"""Nakshatra-based muhurta filters.

5 Panchaka Nakshatras (Dhanishtha 2nd half -> Revati) — universal
cremation/roofing/wood-cutting/south-travel restriction. We treat
the whole of Dhanishtha as Panchaka (most published panchangams do
the same; the 2nd-half precision can be added later if a devotee
asks).

Designed for extension: Task 15 will append Mukha nakshatra direction
mappings to this module.
"""

PANCHAKA_NAKSHATRAS = frozenset({
    'Dhanishtha',
    'Shatabhisha',
    'Purva Bhadrapada',
    'Uttara Bhadrapada',
    'Revati',
})


def is_panchaka_nakshatra(name: str) -> bool:
    """Return True if *name* is one of the 5 Panchaka Nakshatras."""
    return name in PANCHAKA_NAKSHATRAS
