"""Ordered reason groups and disclosed dosha annotations."""

from dataclasses import dataclass

from telugu_panchangam.personal.nitya_yoga import NITYA_HARD_AVOID
from telugu_panchangam.personal.slot_scorers import YOGA_PENALTY, _DayContext


@dataclass
class _CalendarReasons:
    yoga: list[str]
    nitya: list[str]
    anandadi: str | None
    tithi_day: str | None
    election: tuple[str, ...]
    tithi_activity: str | None
    preferred_tithi: str | None


def _personal_dosha(
    chandra_names, lagna_ashtama_names, tara_unfav_names, special_yogas
):
    chandra_avoid_names, chandra_puja_names = chandra_names
    if chandra_avoid_names:
        return (
            'ashtama_chandra'
            if any('Ashtama' in name for name in chandra_avoid_names)
            else 'chandra_avoid'
        )
    if lagna_ashtama_names:
        return 'ashtama_lagna'
    if chandra_puja_names:
        return 'chandra_remedial'
    rectified = any(
        yoga in ('Sarvartha Siddhi Yoga', 'Amrita Siddhi Yoga')
        for yoga in special_yogas
    )
    if tara_unfav_names and not rectified:
        return 'tara_dosha'
    return None


def _day_dosha(facts, tithi_fam, manual_prerequisites) -> str | None:
    if tithi_fam == 'Rikta':
        return 'rikta_tithi'
    if 'Amavasya' in facts.tithi:
        return 'amavasya'
    if any(yoga in YOGA_PENALTY for yoga in facts.special_yogas):
        return 'visha_dagdha_yoga'
    if facts.yoga in NITYA_HARD_AVOID:
        return 'vyatipata_vaidhriti'
    return 'practitioner_review' if manual_prerequisites else None


def _append_manual_notes(notes, day, ctx: _DayContext, cur_lagna) -> None:
    english_weekdays = {
        'Adivaram': 'Sunday',
        'Somavaram': 'Monday',
        'Mangalavaram': 'Tuesday',
        'Budhavaram': 'Wednesday',
        'Guruvaram': 'Thursday',
        'Shukravaram': 'Friday',
        'Shanivaram': 'Saturday',
    }
    current_weekday = english_weekdays.get(day.vaaram)
    for item in ctx.manual_checks:
        named_weekdays = [name for name in english_weekdays.values() if name in item]
        if not named_weekdays or current_weekday in named_weekdays:
            notes.append(f'Manual check required · {item}')
    if ctx.caution_lagna_solar and cur_lagna == day.solar_sign:
        notes.append(
            f'Source caution · {cur_lagna} Lagna is occupied by Surya; '
            'Raman associates this with delay from hard rock.'
        )


def _slot_quality_reasons(mu, block, base, nature_bonus) -> list[str]:
    mu_label = mu['name']
    if mu['is_abhijit']:
        mu_label += ' (Abhijit)'
    mu_deity = f' · {mu["deity"]}' if mu['deity'] else ''
    chog_desc = f'{block.name} choghadiya'
    if mu.get('chog_straddle'):
        chog_desc += f' (spans {mu["chog_straddle"]})'
    chog_line = f'{chog_desc} (+{base})' if base else chog_desc
    return [
        f'{mu_label} muhurta{mu_deity} · {mu["nature"]} ({nature_bonus:+d})',
        chog_line,
    ]


def _initial_reason_buckets(ctx: _DayContext, reasons: _CalendarReasons):
    day_quality = list(reasons.yoga) + list(reasons.nitya)
    if ctx.simha_stha_shukra_penalty:
        day_quality.append(
            f'Simha-Stha Shukra (Venus in Simha) ({ctx.simha_stha_shukra_penalty})'
        )
    if reasons.anandadi:
        day_quality.append(reasons.anandadi)
    if reasons.tithi_day:
        day_quality.append(reasons.tithi_day)
    activity_match = list(reasons.election)
    if reasons.tithi_activity:
        activity_match.append(reasons.tithi_activity)
    if reasons.preferred_tithi:
        activity_match.append(reasons.preferred_tithi)
    if ctx.vara_reason:
        activity_match.append(ctx.vara_reason)
    return day_quality, activity_match
