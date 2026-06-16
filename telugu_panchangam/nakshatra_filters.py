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


# ---- Nakshatra mouth-direction classification (Mukha) ----
# Used as an activity-conditioned filter in muhurta:
#   Adho   → foundations, digging, mining
#   Urdhva → coronation, roofing, ceremony tops
#   Tiryan → travel, journey, horizontal works

NAKSHATRA_MUKHA: dict[str, str] = {
    'Mrigashira': 'Urdhva', 'Ardra': 'Urdhva', 'Punarvasu': 'Urdhva',
    'Pushya': 'Urdhva', 'Shravana': 'Urdhva', 'Dhanishtha': 'Urdhva',
    'Shatabhisha': 'Urdhva', 'Purva Phalguni': 'Urdhva',
    'Purva Ashadha': 'Urdhva', 'Purva Bhadrapada': 'Urdhva',

    'Krittika': 'Adho', 'Bharani': 'Adho', 'Magha': 'Adho',
    'Vishakha': 'Adho', 'Mula': 'Adho', 'Ashlesha': 'Adho',
    'Jyeshtha': 'Adho',

    'Ashvini': 'Tiryan', 'Hasta': 'Tiryan', 'Swati': 'Tiryan',
    'Anuradha': 'Tiryan', 'Chitra': 'Tiryan', 'Revati': 'Tiryan',
    'Uttara Phalguni': 'Tiryan', 'Uttara Ashadha': 'Tiryan',
    'Uttara Bhadrapada': 'Tiryan', 'Rohini': 'Tiryan',
}


def nakshatra_mukha(name: str | None) -> str | None:
    """Return the Mukha (mouth direction) for a nakshatra name.

    Returns 'Adho', 'Urdhva', or 'Tiryan', or None when name is None
    or not in the table (e.g. an unrecognised nakshatra spelling).
    """
    if name is None:
        return None
    return NAKSHATRA_MUKHA.get(name)
