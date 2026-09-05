"""Guru/Shukra Maudhya (combustion / heliacal setting).

Per Brihat Samhita / Muhurta Chintamani:
- Jupiter: 11° elongation threshold
- Venus: 10° elongation threshold

When combust, classical samskara rules (especially marriage and
upanayana) require the day be skipped.
"""
from telugu_panchangam.models.panchangam_day import MaudhyaInfo

COMBUSTION_THRESHOLDS = {
    'Guru': 11.0,
    'Shukra': 10.0,
}


def compute_maudhya(graha: str, sun_long: float, planet_long: float) -> MaudhyaInfo:
    threshold = COMBUSTION_THRESHOLDS[graha]
    # Signed shortest-arc elongation in [0, 180]
    diff = abs((planet_long - sun_long + 180.0) % 360.0 - 180.0)
    return MaudhyaInfo(
        graha=graha,
        elongation_deg=diff,
        combust=diff < threshold,
        threshold_deg=threshold,
    )
