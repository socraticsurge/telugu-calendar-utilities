"""Disha Shoola — weekday direction-of-blocked-travel.

Classical rule: travel toward the indicated direction on the given
weekday is inauspicious. Used as an activity-conditioned filter for
travel muhurta (caller supplies their intended travel direction).
"""

DISHA_SHOOLA = {
    'Adivaram':     'West',
    'Somavaram':    'East',
    'Mangalavaram': 'North',
    'Budhavaram':   'North',
    'Guruvaram':    'South',
    'Shukravaram':  'West',
    'Shanivaram':   'East',
}


def disha_shoola(vaaram: str | None) -> str | None:
    """Return the blocked direction for the given weekday, or None."""
    return DISHA_SHOOLA.get(vaaram) if vaaram else None
