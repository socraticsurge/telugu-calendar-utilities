# Nitya Yoga classification — the 27 sun-moon longitudinal yogas and
# their muhurta-shastra disposition.
#
# Spellings match telugu_panchangam.engines.base.YOGA_NAMES exactly
# (e.g. 'Preeti' not 'Priti', 'Shoola' not 'Shula', 'Variyan' not
# 'Variyana') — these are the strings the engine actually emits via
# SlotFacts.yoga.
#
# Hard-avoid (universal): Vyatipata (17), Vaidhriti (27). Muhurta texts
# universally treat these as no-go for samskaras and major beginnings.
# They get -2 day_bonus and a samskara skip rule.
#
# Partial-avoid: Vishkambha, Atiganda, Shoola, Ganda, Vyaghata, Parigha.
# Only the dosha-window of the yoga (first N ghatis after the yoga
# begins) is treated as inauspicious. -1 to the day bonus when the
# slot is inside the window.
#
# Auspicious: Preeti, Ayushman, Saubhagya, Shobhana, Sukarma, Dhriti,
# Vriddhi, Dhruva, Harshana, Siddhi, Shiva, Siddha, Sadhya, Shubha,
# Shukla, Brahma, Indra. +1 day bonus.
#
# Neutral (no score): Vajra, Variyan — mixed in classical texts;
# leaving at zero to avoid contested classifications.
#
# A ghati = 24 minutes (1/30 of a day).
from datetime import timedelta

# Hard-avoid yogas — samskara skip + -2 day bonus
NITYA_HARD_AVOID: frozenset[str] = frozenset({'Vyatipata', 'Vaidhriti'})
NITYA_HARD_PENALTY: int = -2

# Partial-avoid yogas — -1 only during the first N ghatis (dosha-window)
# from when the yoga begins.
_GHATI_MIN = 24
NITYA_PARTIAL_DOSHA_WINDOW: dict[str, timedelta] = {
    'Vishkambha': timedelta(minutes=3 * _GHATI_MIN),   # 72 min
    'Atiganda':   timedelta(minutes=6 * _GHATI_MIN),   # 144 min
    'Shoola':     timedelta(minutes=5 * _GHATI_MIN),   # 120 min
    'Ganda':      timedelta(minutes=6 * _GHATI_MIN),   # 144 min
    'Vyaghata':   timedelta(minutes=9 * _GHATI_MIN),   # 216 min
    'Parigha':    timedelta(minutes=5 * _GHATI_MIN),   # 120 min
}
NITYA_PARTIAL_PENALTY: int = -1

# Auspicious yogas — +1 day bonus
NITYA_AUSPICIOUS: frozenset[str] = frozenset({
    'Preeti', 'Ayushman', 'Saubhagya', 'Shobhana',
    'Sukarma', 'Dhriti', 'Vriddhi', 'Dhruva',
    'Harshana', 'Siddhi', 'Shiva', 'Siddha',
    'Sadhya', 'Shubha', 'Shukla', 'Brahma', 'Indra',
})
NITYA_AUSPICIOUS_BONUS: int = 1


def nitya_disposition(yoga_name: str) -> str:
    """One of 'hard-avoid' | 'partial-avoid' | 'auspicious' | 'neutral'."""
    if yoga_name in NITYA_HARD_AVOID:
        return 'hard-avoid'
    if yoga_name in NITYA_PARTIAL_DOSHA_WINDOW:
        return 'partial-avoid'
    if yoga_name in NITYA_AUSPICIOUS:
        return 'auspicious'
    return 'neutral'
