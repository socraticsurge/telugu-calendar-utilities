# Muhurta finder: ranks daytime slots by intersecting what the engines
# already compute — good choghadiya blocks minus every inauspicious
# window, with bonuses for Abhijit/Amrita overlap and the day's special
# yogas, light activity rules, and optional tarabalam screening for a
# group. Deterministic and explainable: each slot carries its reasons.
from datetime import datetime, timedelta

from telugu_panchangam.models.panchangam_day import PanchangamDay
from telugu_panchangam.personal.tarabalam import tara_number, is_auspicious_tara

GOOD_CHOGHADIYA = {'Amrit': 3, 'Shubh': 2, 'Labh': 2, 'Char': 1}
MIN_SLOT_MINUTES = 24  # one ghati

ACTIVITIES = ('any', 'travel', 'purchase', 'ceremony', 'beginning')

_YOGA_BONUS = {'Sarvartha Siddhi Yoga': 2, 'Amrita Siddhi Yoga': 2,
               'Dvipushkara Yoga': 1, 'Tripushkara Yoga': 1}
_YOGA_PENALTY = {'Visha Yoga': -2, 'Dagdha Yoga': -2}


def _subtract(start: datetime, end: datetime, blocks: list[tuple[datetime, datetime]]):
    """Pieces of [start, end) not covered by any block."""
    pieces = [(start, end)]
    for b0, b1 in blocks:
        nxt = []
        for p0, p1 in pieces:
            if b1 <= p0 or b0 >= p1:
                nxt.append((p0, p1))
                continue
            if p0 < b0:
                nxt.append((p0, b0))
            if b1 < p1:
                nxt.append((b1, p1))
        pieces = nxt
    return pieces


def _overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1


def day_slots(day: PanchangamDay, activity: str = 'any',
              janma_nakshatras: list[str] | None = None) -> list[dict]:
    """Ranked auspicious slots for one day (daytime, sunrise to sunset)."""
    if activity not in ACTIVITIES:
        raise ValueError(f'activity must be one of {ACTIVITIES}')

    day_reasons: list[str] = []
    day_bonus = 0

    # group screening: every person's tara must be auspicious (classic standard)
    if janma_nakshatras:
        taras = [tara_number(j, day.nakshatra.name) for j in janma_nakshatras]
        if not all(is_auspicious_tara(t) for t in taras):
            return []
        day_bonus += 2
        day_reasons.append('tarabalam favourable for everyone (+2)')

    for y in day.special_yogas:
        if y in _YOGA_BONUS:
            day_bonus += _YOGA_BONUS[y]
            day_reasons.append(f'{y} day (+{_YOGA_BONUS[y]})')
        if y in _YOGA_PENALTY:
            if activity == 'ceremony':
                return []          # ceremonies avoid Visha/Dagdha days outright
            day_bonus += _YOGA_PENALTY[y]
            day_reasons.append(f'{y} day ({_YOGA_PENALTY[y]})')

    bad = [(w.start, w.end) for w in
           [day.rahu_kalam, day.gulika_kalam, day.yamagandam]
           + list(day.varjyam) + list(day.durmuhurtham)]

    if activity == 'travel':
        bad += [(k.start, k.end) for k in day.karana if k.name == 'Vishti']

    abhijit = day.abhijit_muhurta
    amrita = list(day.amrita_kalam)

    slots = []
    for block in day.choghadiya:
        base = GOOD_CHOGHADIYA.get(block.name)
        if base is None:
            continue
        for s, e in _subtract(block.start, block.end, bad):
            if (e - s) < timedelta(minutes=MIN_SLOT_MINUTES):
                continue
            score = base + day_bonus
            reasons = [f'{block.name} choghadiya (+{base})', 'clear of all inauspicious windows'] + day_reasons
            if abhijit and _overlaps(s, e, abhijit.start, abhijit.end):
                score += 2
                reasons.append('overlaps Abhijit Muhurta (+2)')
            if any(_overlaps(s, e, a.start, a.end) for a in amrita):
                score += 2
                reasons.append('overlaps Amrita Kalam (+2)')
            if activity == 'purchase' and block.name == 'Labh':
                score += 1
                reasons.append('Labh favoured for purchases (+1)')
            if activity == 'beginning' and block.name == 'Amrit':
                score += 1
                reasons.append('Amrit favoured for beginnings (+1)')
            if activity == 'travel':
                reasons.append('Vishti karana avoided')
            slots.append({'date': day.date.isoformat(), 'vaaram': day.vaaram,
                          'start': s, 'end': e, 'score': score, 'reasons': reasons})
    slots.sort(key=lambda x: (-x['score'], x['start']))
    return slots
