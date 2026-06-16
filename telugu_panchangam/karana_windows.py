"""Karana-related sub-windows (Vishaghati, Bhadra Mukha/Puchha).

Vishaghati ("poison ghatika") — a short window inside each nakshatra's
transit classically considered inauspicious for muhurta. Offsets per
Muhurta Chintamani; width 4 vighatis.

Bhadra Mukha / Puchha — sub-windows of Vishti karana (Bhadra). The
classical 5:8:3 split across the full Vishti span:
  Mukha  (first 5/16)  — most inauspicious; hard-cut from muhurta slots
  Body   (middle 8/16) — ordinary avoidance (already handled by Vishti karana)
  Puchha (last 3/16)   — auspicious for warfare, lawsuits, contests
Sources: Muhurta Chintamani, Dharma Sindhu.
"""
from datetime import timedelta
from telugu_panchangam.models.panchangam_day import Span, GhatiWindow, GhatiClock
from telugu_panchangam.ghati import civil_to_ghati


VISHAGHATI_OFFSETS_GHATI = {
    'Ashvini': 50, 'Bharani': 24, 'Krittika': 30, 'Rohini': 40,
    'Mrigashira': 14, 'Ardra': 21, 'Punarvasu': 30, 'Pushya': 20,
    'Ashlesha': 32, 'Magha': 30, 'Purva Phalguni': 20, 'Uttara Phalguni': 18,
    'Hasta': 21, 'Chitra': 20, 'Swati': 14, 'Vishakha': 14,
    'Anuradha': 10, 'Jyeshtha': 14, 'Mula': 20, 'Purva Ashadha': 24,
    'Uttara Ashadha': 20, 'Shravana': 10, 'Dhanishtha': 10,
    'Shatabhisha': 18, 'Purva Bhadrapada': 16, 'Uttara Bhadrapada': 24,
    'Revati': 30,
}

VISHAGHATI_WIDTH_VIGHATIS = 4


def compute_vishaghati(
    nakshatra_spans: list[Span], clk: GhatiClock,
) -> list[GhatiWindow]:
    """Return Vishaghati windows overlapping the panchangam day.

    A day may contain one nakshatra (typical) or two (when transit happens
    during the day). For each nakshatra span, compute the poison-ghatika
    window at its classical offset and clip to the sunrise->next-sunrise
    interval.
    """
    windows: list[GhatiWindow] = []
    for span in nakshatra_spans:
        offset_g = VISHAGHATI_OFFSETS_GHATI.get(span.name)
        if offset_g is None:
            continue
        span_duration_s = (span.end - span.start).total_seconds()
        if span_duration_s <= 0:
            continue
        # Offset is in ghatis-from-nakshatra-start, scaled to the
        # nakshatra's full 60-ghati transit. Width uses the day's ghati clock.
        start = span.start + timedelta(seconds=span_duration_s * offset_g / 60.0)
        width_s = VISHAGHATI_WIDTH_VIGHATIS * (clk.seconds_per_ghati / 60.0)
        end = start + timedelta(seconds=width_s)
        # Clip to the panchangam day.
        if end <= clk.sunrise or start >= clk.next_sunrise:
            continue
        if start < clk.sunrise:
            start = clk.sunrise
        if end > clk.next_sunrise:
            end = clk.next_sunrise
        windows.append(GhatiWindow(
            name='Vishaghati',
            start=start, end=end,
            start_ghati=civil_to_ghati(clk, start),
            end_ghati=civil_to_ghati(clk, end),
        ))
    return windows


def compute_bhadra_windows(
    karana_spans: list[Span], clk: GhatiClock,
) -> tuple[GhatiWindow | None, GhatiWindow | None]:
    """Locate Vishti karana in the day's karana list; split into Mukha
    (first 5/16, hard-avoid) and Puchha (last 3/16, auspicious for
    contests/litigation). The middle 8/16 is the "body" with no special status.
    Returns (mukha, puchha) — either can be None when the corresponding
    sub-window is fully outside the panchangam day.
    """
    vishti = next((k for k in karana_spans if k.name == 'Vishti'), None)
    if vishti is None:
        return (None, None)
    total_s = (vishti.end - vishti.start).total_seconds()
    if total_s <= 0:
        return (None, None)
    # 5:8:3 split across the full Vishti span.
    mukha_start = vishti.start
    mukha_end = vishti.start + timedelta(seconds=total_s * 5 / 16)
    puchha_start = vishti.start + timedelta(seconds=total_s * 13 / 16)
    puchha_end = vishti.end

    def _clip(name: str, s, e) -> GhatiWindow | None:
        if e <= clk.sunrise or s >= clk.next_sunrise:
            return None
        if s < clk.sunrise:
            s = clk.sunrise
        if e > clk.next_sunrise:
            e = clk.next_sunrise
        return GhatiWindow(
            name=name, start=s, end=e,
            start_ghati=civil_to_ghati(clk, s),
            end_ghati=civil_to_ghati(clk, e),
        )

    return (_clip('Bhadra Mukha', mukha_start, mukha_end),
            _clip('Bhadra Puchha', puchha_start, puchha_end))
