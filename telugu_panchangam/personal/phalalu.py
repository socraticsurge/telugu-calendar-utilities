# Daily Rasi Phalalu: a deterministic daily reading composed from
# computed facts — chandrabalam (Moon's house), gochara verdicts with
# vedha, named Shani conditions and optionally the day's tarabalam.
# Every sentence is traceable to a calculation; nothing is invented.
from telugu_panchangam.gochara.rules import gochara_for, named_conditions
from telugu_panchangam.personal.chandrabalam import chandra_position, chandra_verdict
from telugu_panchangam.personal.tarabalam import (
    is_auspicious_tara,
    tara_name,
    tara_number,
)

HOUSE_MEANINGS: dict[int, str] = {
    1: 'self and health',
    2: 'wealth and family',
    3: 'courage and effort',
    4: 'home and comfort',
    5: 'children and learning',
    6: 'health and rivals',
    7: 'partnerships',
    8: 'obstacles',
    9: 'fortune and dharma',
    10: 'career and standing',
    11: 'gains and income',
    12: 'expenses and rest',
}

_GOOD_OPENERS = {
    'good': 'The Moon stands well for your rashi today — a day that supports initiative.',
    'puja': "The Moon's position asks for a small remedial prayer; proceed gently after it.",
    'bad': 'The Moon sits heavily for your rashi today — keep the day light and routine.',
}

# slow grahas first: they set the backdrop; fast ones colour the day
_GRAHA_ORDER = ['Shani', 'Guru', 'Rahu', 'Ketu', 'Kuja', 'Surya', 'Shukra', 'Budha']


def _graha_line(v: dict) -> str:
    g, pos, meaning = v['graha'], v['position'], HOUSE_MEANINGS[v['position']]
    if v['verdict'] == 'favourable':
        return f'{g} in your {_ord(pos)} house favours {meaning}.'
    if v['verdict'] == 'blocked':
        return (
            f"{g}'s good {_ord(pos)}-house transit is under vedha by {v['vedha_by']} — "
            f'gains in {meaning} may arrive with friction.'
        )
    return f'{g} in the {_ord(pos)} house tests {meaning}; avoid forcing matters there.'


def _ord(n: int) -> str:
    return f'{n}{["st", "nd", "rd"][n - 1] if n <= 3 else "th"}'


def _day_quality(moon_verdict: str, favourable_count: int) -> str:
    if moon_verdict == 'good' and favourable_count >= 4:
        return 'good'
    if moon_verdict == 'bad' and favourable_count <= 2:
        return 'difficult'
    return 'mixed'


def _tara_line(janma_nakshatra: str, day_nakshatra: str) -> str:
    number = tara_number(janma_nakshatra, day_nakshatra)
    guidance = (
        'a supportive day for beginnings.'
        if is_auspicious_tara(number)
        else 'better suited to routine than to new starts.'
    )
    return f"From your star, today's tara is {number} {tara_name(number)} — {guidance}"


def _condition_line(condition: str) -> str:
    if condition.startswith('Sade Sati'):
        return f'{condition} is running — Shani asks for patience, discipline and steady work.'
    if condition == 'Ashtama Shani':
        return 'Ashtama Shani is running — avoid risks and keep commitments minimal.'
    return f'{condition} is running — go slower than usual on big steps.'


def _summary_line(favourable_count: int, blocked_count: int) -> str:
    blocked = f', {blocked_count} under vedha' if blocked_count else ''
    return f'{favourable_count} of 9 grahas favour you today{blocked}.'


def rasi_phalalu(
    janma_rasi: str,
    sky: dict[str, str],
    janma_nakshatra: str | None = None,
    day_nakshatra: str | None = None,
) -> dict:
    verdicts = {v['graha']: v for v in gochara_for(janma_rasi, sky)}
    conditions = named_conditions(janma_rasi, sky)

    moon_pos = chandra_position(janma_rasi, sky['Chandra'])
    moon_verdict = chandra_verdict(moon_pos)

    fav = sum(1 for v in verdicts.values() if v['verdict'] == 'favourable')
    blocked = sum(1 for v in verdicts.values() if v['verdict'] == 'blocked')
    adverse = 9 - fav - blocked

    lines = [_GOOD_OPENERS[moon_verdict]]
    if janma_nakshatra and day_nakshatra:
        lines.append(_tara_line(janma_nakshatra, day_nakshatra))
    lines.extend(_condition_line(condition) for condition in conditions)
    lines.extend(_graha_line(verdicts[graha]) for graha in _GRAHA_ORDER)
    lines.append(_summary_line(fav, blocked))

    return {
        'janma_rasi': janma_rasi,
        'day_quality': _day_quality(moon_verdict, fav),
        'moon_house': moon_pos,
        'favourable_count': fav,
        'blocked_count': blocked,
        'adverse_count': adverse,
        'conditions': conditions,
        'lines': lines,
    }
