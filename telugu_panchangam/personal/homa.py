"""Classical Homahuti and Agnivasa election tests.

Muhurta Chintamani, Nakshatra-prakarana 35-36, gives two conjunctive
conditions for a Homa offering: the offering must fall in a benefic Graha's
three-Nakshatra group counted from Surya, and Agni must reside on earth.
"""
from __future__ import annotations

from datetime import datetime

from telugu_panchangam.engines.utils import datetime_to_jd
from telugu_panchangam.panchangam_names import NAKSHATRA_NAMES, VAARAM_NAMES


HOMAHUTI_GROUP_LORDS = (
    'Surya', 'Budha', 'Shukra', 'Shani', 'Chandra',
    'Mangala', 'Guru', 'Rahu', 'Ketu',
)
HOMAHUTI_BENEFIC_LORDS = frozenset({'Budha', 'Shukra', 'Chandra', 'Guru'})


def homahuti_group(solar_nakshatra: str, lunar_nakshatra: str) -> tuple[str, int]:
    """Return (Graha lord, 1-based group) for the inclusive Surya count."""
    sun = NAKSHATRA_NAMES.index(solar_nakshatra)
    moon = NAKSHATRA_NAMES.index(lunar_nakshatra)
    group = ((moon - sun) % 27) // 3
    return HOMAHUTI_GROUP_LORDS[group], group + 1


def agnivasa_remainder(tithi_name: str, vaaram: str) -> int:
    """Return the verse-36 modulo-four result (0, 1, 2, or 3)."""
    from telugu_panchangam.panchangam_names import TITHI_NAMES

    tithi_ordinal = TITHI_NAMES.index(tithi_name) + 1
    vara_ordinal = VAARAM_NAMES.index(vaaram) + 1  # Sunday is one.
    return (tithi_ordinal + 1 + vara_ordinal) % 4


def solar_nakshatra_at(dt: datetime, engine) -> str:
    """Compute Surya's Nakshatra through the selected Panchangam engine."""
    jd = datetime_to_jd(dt)
    longitude = engine._sun_longitude_func()(jd) % 360.0
    return NAKSHATRA_NAMES[int(longitude / (360.0 / 27.0)) % 27]


def homa_election(tithi_name: str, vaaram: str, lunar_nakshatra: str,
                  solar_nakshatra: str) -> tuple[bool, list[str]]:
    """Apply both hard gates and return transparent pass reasons."""
    lord, group = homahuti_group(solar_nakshatra, lunar_nakshatra)
    remainder = agnivasa_remainder(tithi_name, vaaram)
    admitted = lord in HOMAHUTI_BENEFIC_LORDS and remainder in {0, 3}
    reasons = [
        f'Homahuti group {group}: {solar_nakshatra} to {lunar_nakshatra} '
        f'falls to {lord}',
        f'Agnivasa remainder {remainder}: Agni resides on earth',
    ]
    return admitted, reasons
