"""Sankramana avoidance window.

When the Sun crosses into a new rasi, classical samskara rules forbid
ceremonies for 16 ghatikas before and after the exact ingress moment.
Total span = 32 ghatis (~12h48m). Different sources cite 16 vs 30 ghatis
for Karkata/Makara (solstitial); we use the conservative 16 for all signs.
"""
from datetime import datetime, timedelta

from telugu_panchangam.models.panchangam_day import GhatiClock, Window


def compute_sankramana_window(
    sankranti_moment: datetime | None, clk: GhatiClock,
) -> Window | None:
    """Return the 16-ghati-before + 16-ghati-after avoidance window around
    the Sun's sign-ingress moment. None when no Sankranti occurs on this
    panchangam day.
    """
    if sankranti_moment is None:
        return None
    half_width_s = 16 * clk.seconds_per_ghati
    return Window(
        name='Sankramana Avoidance',
        start=sankranti_moment - timedelta(seconds=half_width_s),
        end=sankranti_moment + timedelta(seconds=half_width_s),
    )
