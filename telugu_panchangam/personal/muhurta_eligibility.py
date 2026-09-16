"""Day and slot admission policies, independent of transport and ranking."""

from telugu_panchangam.personal.activity_rules import canonical_activity_nakshatras
from telugu_panchangam.personal.election_assessors.karnavedha import (
    karnavedha_daylight_drop_reason,
)
from telugu_panchangam.personal.lagna_position import lagna_class_of
from telugu_panchangam.personal.nitya_yoga import NITYA_HARD_AVOID
from telugu_panchangam.personal.slot_scorers import _DayContext
from telugu_panchangam.personal.tithi_class import tithi_number

_ADHIKA_PREFIX = 'Adhika '
_DISALLOWED_TITHI = object()


def _overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1


def _month_admitted(day, rules) -> bool:
    allowed_maasams = rules.get('allowed_maasams')
    allowed_pairs = {tuple(pair) for pair in rules.get('allowed_maasa_solar_pairs', ())}
    maasam = day.maasam.removeprefix('Nija ').removeprefix(_ADHIKA_PREFIX)
    if not allowed_maasams and not allowed_pairs:
        return True
    return (
        maasam in (allowed_maasams or ()) or (maasam, day.solar_sign) in allowed_pairs
    )


def _calendar_profile_skip_reason(day, rules) -> str | None:
    if not _month_admitted(day, rules):
        return (
            f'{day.maasam} Maasa · {rules["label"]} source profile '
            'does not admit this lunar month'
        )
    allowed_varas = rules.get('allowed_varas')
    if allowed_varas and day.vaaram not in allowed_varas:
        return (
            f'{day.vaaram} · {rules["label"]} source profile '
            'does not admit this weekday'
        )
    allowed_pakshams = rules.get('allowed_pakshams')
    if allowed_pakshams and day.paksham not in allowed_pakshams:
        return (
            f'{day.paksham} Paksha · {rules["label"]} source profile '
            'does not admit this lunar fortnight'
        )
    avoided = map(tuple, rules.get('avoid_vara_paksha', ()))
    if (day.vaaram, day.paksham) in avoided:
        return (
            f'{day.vaaram} during {day.paksham} Paksha · '
            f'{rules["label"]} source profile rejects this combination'
        )
    return _solar_profile_skip_reason(day, rules)


def _solar_profile_skip_reason(day, rules) -> str | None:
    allowed_classes = rules.get('allowed_solar_classes')
    solar_class = lagna_class_of(day.solar_sign)
    if allowed_classes and solar_class not in allowed_classes:
        return (
            f'Surya in {day.solar_sign} ({solar_class}) · '
            f'{rules["label"]} source profile does not admit this Rasi class'
        )
    allowed_signs = rules.get('allowed_solar_signs')
    if allowed_signs and day.solar_sign not in allowed_signs:
        return (
            f'Surya in {day.solar_sign} · {rules["label"]} source profile '
            'does not admit this solar Rasi'
        )
    return None


def _chandra_skip_reason(day, janma_rasis, chandra_mode) -> str | None:
    if janma_rasis is None or chandra_mode == 'stars':
        return None
    from telugu_panchangam.personal.chandrabalam import chandra_position

    positions = [
        chandra_position(rashi, day.lunar_sign)
        for rashi in janma_rasis
        if rashi is not None
    ]
    return _chandra_position_rejection(positions, chandra_mode)


def _chandra_position_rejection(positions, chandra_mode) -> str | None:
    from telugu_panchangam.personal.chandrabalam import CHANDRA_GOOD, CHANDRA_PUJA

    admitted_positions = {
        'strict': CHANDRA_GOOD,
        'puja_ok': CHANDRA_GOOD | CHANDRA_PUJA,
    }.get(chandra_mode)
    if admitted_positions is None:
        return None
    if any(position not in admitted_positions for position in positions):
        return {
            'strict': 'chandra_mode=strict · Moon at sunrise fails for at least one person',
            'puja_ok': 'chandra_mode=puja_ok · someone has Moon-avoid (4/8/12)',
        }[chandra_mode]
    return None


def _traditional_calendar_skip_reason(day, rules) -> str | None:
    if rules.get('skip_on_panchaka_nakshatra') and day.in_panchaka_nakshatra:
        return (
            f'Panchaka Nakshatra ({day.nakshatra.name}) · '
            f'{rules["label"]} traditionally avoided'
        )
    if rules.get('skip_on_khar_maasa') and day.is_khar_maasa:
        return (
            f'Khar-Maasa ({day.khar_maasa_name} Maasa) · '
            f'{rules["label"]} traditionally avoided'
        )
    return _traditional_month_skip_reason(day, rules)


def _traditional_month_skip_reason(day, rules) -> str | None:
    if rules.get('skip_on_adhika') and day.maasam.startswith(_ADHIKA_PREFIX):
        return f'Adhika Maasa · {rules["label"]} traditionally avoided'
    if rules.get('skip_on_pitru_paksha') and day.is_pitru_paksha:
        return (
            'Pitru Paksha (Bhadrapada Krishna paksha) · '
            f'{rules["label"]} traditionally avoided'
        )
    if rules.get('skip_on_simha_stha_guru') and day.simha_stha_guru:
        return (
            'Simha-Stha Guru · '
            f'{rules["label"]} traditionally avoided while Jupiter is in Simha'
        )
    return None


def _traditional_skip_reason(day, rules) -> str | None:
    if reason := _traditional_calendar_skip_reason(day, rules):
        return reason
    if reason := _combustion_skip_reason(day, rules):
        return reason
    return _yoga_skip_reason(day, rules)


def _combustion_skip_reason(day, rules) -> str | None:
    for graha in rules.get('skip_on_combust', []):
        info = getattr(day, f'{graha.lower()}_maudhya', None)
        if info is not None and info.combust:
            return (
                f'{graha} Maudhya ({info.elongation_deg:.1f}° < '
                f'{info.threshold_deg}°) · {rules["label"]} '
                f'traditionally avoided when {graha} is combust'
            )
    return None


def _yoga_skip_reason(day, rules) -> str | None:
    skip_yogas = set(rules.get('skip_on_yoga', ()))
    if not skip_yogas:
        return None
    for yoga in day.special_yogas:
        if yoga in skip_yogas:
            return f'{yoga} · {rules["label"]} traditionally avoids this day'
    if day.yoga.name in NITYA_HARD_AVOID:
        return f'{day.yoga.name} yoga · samskaras traditionally defer'
    return None


def _travel_skip_reason(day, activity, travel_direction) -> str | None:
    if activity != 'travel' or travel_direction is None:
        return None
    blocked = getattr(day, 'disha_shoola_direction', None)
    if blocked is not None and travel_direction == blocked:
        return (
            f'Disha Shoola ({day.vaaram}) · travel toward {blocked} '
            'is inauspicious on this weekday'
        )
    return None


def _day_skip_reason(
    day,
    rules,
    activity,
    travel_direction,
    janma_rasis,
    chandra_mode,
    daylight_assessment=None,
) -> str | None:
    """Return a reason string if the day should be skipped, else None.

    Covers eclipse, disha shoola, all rule-driven skips (khar maasa,
    adhika, pitru paksha, simha-stha guru, combustion, skip-on-yoga),
    and chandra_mode day-level filtering.
    """
    if day.eclipse is not None:
        kind = f'{day.eclipse.kind} eclipse'
        return f'{kind} · auspicious activities deferred'

    if daylight_assessment is not None and not daylight_assessment['admissible']:
        return karnavedha_daylight_drop_reason(daylight_assessment)

    if reason := _calendar_profile_skip_reason(day, rules):
        return reason

    if reason := _travel_skip_reason(day, activity, travel_direction):
        return reason

    if reason := _traditional_skip_reason(day, rules):
        return reason

    return _chandra_skip_reason(day, janma_rasis, chandra_mode)


def _nakshatra_admitted(nakshatra, ctx: _DayContext) -> bool:
    janma_nakshatras = canonical_activity_nakshatras(ctx.janma_nakshatras or [])
    if ctx.avoid_janma_nakshatra and nakshatra in janma_nakshatras:
        return False
    if ctx.allowed_nakshatras and nakshatra not in ctx.allowed_nakshatras:
        return False
    return nakshatra not in ctx.avoid_nakshatras


def _tithi_admitted(tithi, number, ctx: _DayContext) -> bool:
    if ctx.allowed_tithi_numbers and number not in ctx.allowed_tithi_numbers:
        return False
    if ctx.allowed_tithi_names and tithi not in ctx.allowed_tithi_names:
        return False
    return number not in ctx.avoid_tithi_numbers


def _allowed_tithi_number(day, facts, ctx: _DayContext):
    if not _nakshatra_admitted(facts.nakshatra, ctx):
        return _DISALLOWED_TITHI
    try:
        number = tithi_number(facts.tithi)
    except ValueError:
        number = None
    if not _tithi_admitted(facts.tithi, number, ctx):
        return _DISALLOWED_TITHI
    if (day.vaaram, facts.tithi) in ctx.avoid_vara_tithi_names:
        return _DISALLOWED_TITHI
    if facts.yoga in ctx.avoid_nitya_yogas:
        return _DISALLOWED_TITHI
    return number


def _night_traditional_skip(day, rules) -> bool:
    if _traditional_calendar_skip_reason(day, rules) is not None:
        return True
    return _combustion_skip_reason(day, rules) is not None


def _night_unavailable(day, rules, activity, travel_direction) -> bool:
    if day.eclipse is not None:
        return True
    if _travel_skip_reason(day, activity, travel_direction) is not None:
        return True
    if rules.get('daytime_only') or rules.get('forenoon_only'):
        return True
    if _calendar_profile_skip_reason(day, rules) is not None:
        return True
    return _night_traditional_skip(day, rules)
