"""Ordered reason groups and disclosed dosha annotations."""

from telugu_panchangam.personal.nitya_yoga import NITYA_HARD_AVOID
from telugu_panchangam.personal.slot_scorers import YOGA_PENALTY, _DayContext


def _personal_dosha(
    chandra_avoid_names,
    lagna_ashtama_names,
    chandra_puja_names,
    tara_unfav_names,
    special_yogas,
) -> str | None:
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


def _initial_reason_buckets(
    yoga_reasons,
    nitya_reasons,
    ctx: _DayContext,
    anandadi_reason,
    tithi_day_reason,
    election_reasons,
    tithi_activity_reason,
    preferred_number_tithi_reason,
) -> tuple[list[str], list[str]]:
    day_quality = list(yoga_reasons) + list(nitya_reasons)
    if ctx.simha_stha_shukra_penalty:
        day_quality.append(
            f'Simha-Stha Shukra (Venus in Simha) ({ctx.simha_stha_shukra_penalty})'
        )
    if anandadi_reason:
        day_quality.append(anandadi_reason)
    if tithi_day_reason:
        day_quality.append(tithi_day_reason)
    activity_match = list(election_reasons)
    if tithi_activity_reason:
        activity_match.append(tithi_activity_reason)
    if preferred_number_tithi_reason:
        activity_match.append(preferred_number_tithi_reason)
    if ctx.vara_reason:
        activity_match.append(ctx.vara_reason)
    return day_quality, activity_match
