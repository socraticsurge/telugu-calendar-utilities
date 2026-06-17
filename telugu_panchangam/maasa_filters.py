"""Solar-month-based muhurta filters.

Khar-Maasa — Sun in Dhanur (Sagittarius) or Meena (Pisces). Samskara
restriction. Pure check on solar rasi at sunrise.

The engine stores the sidereal rasi using RASHI_NAMES from engines/base.py:
  index 8 → 'Dhanu'  (Sagittarius / Dhanur Maasa)
  index 11 → 'Meena' (Pisces / Meena Maasa)
"""

KHAR_MAASA_SIGNS = {'Dhanu', 'Meena'}


def khar_maasa_name(solar_sign: str | None) -> str | None:
    """Return 'Dhanur' for Dhanu rasi, 'Meena' for Meena, else None.

    The classical month name is 'Dhanur Maasa'; the rasi stored by the
    engine is 'Dhanu', so we map it to the traditional human-readable form.
    """
    if solar_sign == 'Dhanu':
        return 'Dhanur'
    if solar_sign == 'Meena':
        return 'Meena'
    return None
