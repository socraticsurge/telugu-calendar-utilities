from datetime import datetime, timedelta
from telugu_panchangam.models.panchangam_day import GhatiClock, GhatiWindow


def make_clock(sunrise: datetime, next_sunrise: datetime) -> GhatiClock:
    seconds_per_ghati = (next_sunrise - sunrise).total_seconds() / 60.0
    return GhatiClock(sunrise=sunrise, next_sunrise=next_sunrise,
                      seconds_per_ghati=seconds_per_ghati)


def civil_to_ghati(clk: GhatiClock, t: datetime) -> float:
    return (t - clk.sunrise).total_seconds() / clk.seconds_per_ghati


def ghati_to_civil(clk: GhatiClock, g: float) -> datetime:
    return clk.sunrise + timedelta(seconds=g * clk.seconds_per_ghati)


def ghati_window(
    clk: GhatiClock, name: str, start_ghati: float, end_ghati: float,
) -> GhatiWindow:
    return GhatiWindow(
        name=name,
        start=ghati_to_civil(clk, start_ghati),
        end=ghati_to_civil(clk, end_ghati),
        start_ghati=start_ghati,
        end_ghati=end_ghati,
    )
