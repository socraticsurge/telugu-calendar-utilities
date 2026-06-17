"""Pitru Paksha — Bhadrapada Krishna paksha 15-day window.

From Bhadrapada Shukla Pournami onward through Krishna paksha to
Mahalaya Amavasya. Samskaras (especially marriage, upanayana, naming
ceremonies) are restricted; only pitru-rites (shraddha, tarpana) are
appropriate.

For purposes of this flag we mark the 15-day Krishna paksha portion
of Bhadrapada. The terminal Amavasya is included.
"""


def is_pitru_paksha_day(maasam: str | None, paksham: str | None) -> bool:
    """True iff this day falls in Bhadrapada Krishna paksha."""
    if maasam is None or paksham is None:
        return False
    base = maasam.removeprefix('Adhika ').removeprefix('Nija ')
    return base == 'Bhadrapada' and paksham == 'Krishna'
