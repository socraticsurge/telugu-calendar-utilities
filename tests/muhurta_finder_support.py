# Muhurta finder: slots derive from already-verified engine windows.
from datetime import date

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.muhurta import (
    relative_tier,
)

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(y, m, d, include_eclipse=False):
    return ENGINE.calculate(date(y, m, d), HYD, include_eclipse=include_eclipse)


def _expected_tier(slots, score, personal_dosha, day_dosha):
    """Recompute the relative tier the same way assign_tiers() does."""
    all_scores = [s['score'] for s in slots]
    ceiling, floor = max(all_scores), min(all_scores)
    tier = relative_tier(score, ceiling, floor)
    if tier != 'Excellent':
        return tier
    if personal_dosha is not None:
        return 'Good'
    if day_dosha is not None:
        return 'Good'
    return tier


def _two_days(y, m, d):
    """Return (day, next_day) PanchangamDay pair for night_slots()."""
    from datetime import timedelta
    d0 = date(y, m, d)
    return ENGINE.calculate(d0, HYD), ENGINE.calculate(d0 + timedelta(days=1), HYD)
