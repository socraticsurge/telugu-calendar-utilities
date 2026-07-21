"""The 30 named muhurtas of the ahoratra.

A muhurta is 1/30 of the day-and-night: 15 daytime muhurtas tiling
sunrise->sunset, 15 night muhurtas tiling sunset->next sunrise. Each is
~48 minutes (2 ghati) at the equinox but is computed proportionally
(daytime/15, night/15), so it expands and contracts with the season.
This matches how the engine already defines Abhijit and Durmuhurtham:
the 8th daytime muhurta computed here coincides exactly with the engine's
Abhijit Muhurta (see tests/test_named_muhurtas.py).

This module only *consumes* engine output (a PanchangamDay's sunrise /
sunset, plus the next day's sunrise for the night set); it does not touch
the engines. Names, deities and natures are the owner-verified reference
in docs/reference/07-muhurta-table.md — the single source of record.
"""
from __future__ import annotations

# (name, presiding deity or None for concept-names, nature)
# Nature is 'auspicious' or 'inauspicious'. Order is 1..15 from sunrise.
DAY_MUHURTAS = [
    ('Rudra',       'Rudra (fierce Shiva)',      'inauspicious'),
    ('Ahi',         'Sarpa (the Serpent)',       'inauspicious'),
    ('Mitra',       'Mitra (Aditya)',            'auspicious'),
    ('Pitri',       'the Pitrs (ancestors)',     'inauspicious'),
    ('Vasu',        'the Vasus',                 'auspicious'),
    ('Vara',        'Varaha (Vishnu)',           'auspicious'),
    ('Vishvedeva',  'the Vishvedevas',           'auspicious'),
    ('Vidhi',       'Brahma',                    'auspicious'),   # 8th = Abhijit
    ('Sathamukhi',  None,                        'auspicious'),
    ('Puruhuta',    'Indra',                     'inauspicious'),
    ('Vahini',      None,                        'inauspicious'),
    ('Naktanchara', None,                        'inauspicious'),
    ('Varuna',      'Varuna',                    'auspicious'),
    ('Aryama',      'Aryaman (Aditya)',          'auspicious'),
    ('Bhaga',       'Bhaga (Aditya)',            'inauspicious'),
]

# Order is 1..15 from sunset.
NIGHT_MUHURTAS = [
    ('Girisha',      'Shiva (Girisha)',          'inauspicious'),
    ('Ajapada',      'Aja-Ekapada (a Rudra)',    'inauspicious'),
    ('Ahirbudhnya',  'Ahirbudhnya (a Rudra)',    'auspicious'),
    ('Pusha',        'Pushan (Aditya)',          'auspicious'),
    ('Aswi',         'the Ashvins',              'auspicious'),
    ('Yama',         'Yama',                     'inauspicious'),
    ('Agni',         'Agni',                     'inauspicious'),
    ('Vidhatru',     'Vidhatr (the ordainer)',   'auspicious'),
    ('Chanda',       'Chandra (Moon)',           'auspicious'),
    ('Aditi',        'Aditi',                    'auspicious'),
    ('Jeeva',        'Brihaspati (Jupiter)',     'auspicious'),
    ('Vishnu',       'Vishnu',                   'auspicious'),
    ('Yumigadyuti',  None,                       'auspicious'),
    ('Brahma',       'Brahma',                   'auspicious'),   # 14th = Brahma Muhurta
    ('Samudra',      None,                       'auspicious'),
]

ABHIJIT_INDEX = 8   # 8th daytime muhurta (straddles solar noon; none on Wednesday)
BRAHMA_INDEX = 14   # 14th night muhurta (pre-dawn)


def _entry(index, period, table_row, start, end):
    name, deity, nature = table_row
    return {
        'index': index,           # 1..15 within the period
        'period': period,         # 'day' | 'night'
        'name': name,
        'deity': deity,
        'nature': nature,
        'start': start,
        'end': end,
        'is_abhijit': period == 'day' and index == ABHIJIT_INDEX,
        'is_brahma': period == 'night' and index == BRAHMA_INDEX,
    }


def named_muhurtas(day, next_day=None) -> list[dict]:
    """The named muhurtas for `day`.

    Returns the 15 daytime muhurtas (sunrise->sunset). If `next_day` is
    given, also appends the 15 night muhurtas (sunset->next sunrise).
    Each muhurta is a dict; see _entry. Times are whatever tz the day's
    sunrise/sunset carry (engine emits UTC).
    """
    out = []
    day_len = (day.sunset - day.sunrise) / 15
    for i, row in enumerate(DAY_MUHURTAS):
        start = day.sunrise + i * day_len
        end = day.sunrise + (i + 1) * day_len
        out.append(_entry(i + 1, 'day', row, start, end))

    if next_day is not None:
        night_len = (next_day.sunrise - day.sunset) / 15
        for i, row in enumerate(NIGHT_MUHURTAS):
            start = day.sunset + i * night_len
            end = day.sunset + (i + 1) * night_len
            out.append(_entry(i + 1, 'night', row, start, end))

    return out
