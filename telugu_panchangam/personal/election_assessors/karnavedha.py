"""Day-level Karnavedha predicates under the named Raman policy.

These predicates deliberately consume the Panchangam day's exact transition
spans.  They are not sampled at offered Muhurta windows and do not use the
remote election-chart service.  The governing interval is half-open so a
transition exactly at sunset belongs to the following interval and does not
create two daylight rulers.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

KARNAVEDHA_DAYLIGHT_POLICY_ID = 'raman-karnavedha-daylight-v1'
KARNAVEDHA_DAYLIGHT_POLICY_CLAIM = (
    'election_day.karnavedha_daylight_policy_v1')
KARNAVEDHA_TITHI_RULE_ID = 'karnavedha.daylight-tithi-single'
KARNAVEDHA_NAKSHATRA_RULE_ID = 'karnavedha.daylight-nakshatra-single'
KARNAVEDHA_SOURCE_CLAIM = 'muhurta.karnavedha'
KARNAVEDHA_SOURCE_LOCATOR = (
    "B. V. Raman, Chapter VIII, 'Ear boring (Karnavedha),' inspected in "
    'the 2020 Chistabo derivative at internal printed p. 23 '
    '(physical PDF p. 26)')

_RULES = (
    {
        'id': KARNAVEDHA_TITHI_RULE_ID,
        'label': 'One Tithi rules throughout local daylight',
        'limb': 'Tithi',
        'attribute': 'tithi',
    },
    {
        'id': KARNAVEDHA_NAKSHATRA_RULE_ID,
        'label': 'One Nakshatra rules throughout local daylight',
        'limb': 'Nakshatra',
        'attribute': 'nakshatra',
    },
)


def _aware(value: Any) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _local_timezone(day: Any) -> ZoneInfo | None:
    location = getattr(day, 'location', None)
    timezone = getattr(location, 'timezone', None)
    if not isinstance(timezone, str) or not timezone:
        return None
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return None


def _base_outcome(rule: Mapping[str, str]) -> dict[str, Any]:
    return {
        'rule_id': rule['id'],
        'label': rule['label'],
        'effect': 'reject',
        'source_claim': KARNAVEDHA_SOURCE_CLAIM,
        'source_locator': KARNAVEDHA_SOURCE_LOCATOR,
        'policy_id': KARNAVEDHA_DAYLIGHT_POLICY_ID,
        'decision_policy_claim': KARNAVEDHA_DAYLIGHT_POLICY_CLAIM,
        'interval': '[local sunrise, local sunset)',
    }


def _unknown(rule: Mapping[str, str], detail: str) -> dict[str, Any]:
    return {
        **_base_outcome(rule),
        'status': 'unknown',
        'evidence': [detail],
    }


def _evaluate_limb(
    day: Any,
    rule: Mapping[str, str],
    sunrise: datetime,
    sunset: datetime,
    timezone: ZoneInfo,
) -> dict[str, Any]:
    span = getattr(day, rule['attribute'], None)
    if span is None:
        return _unknown(
            rule, f'{rule["limb"]} transition span is unavailable.')
    name = getattr(span, 'name', None)
    start = getattr(span, 'start', None)
    end = getattr(span, 'end', None)
    if not isinstance(name, str) or not name.strip():
        return _unknown(rule, f'{rule["limb"]} name is unavailable.')
    if not _aware(start) or not _aware(end):
        return _unknown(
            rule,
            f'{rule["limb"]} boundaries must be timezone-aware.',
        )
    if start >= end:
        return _unknown(
            rule, f'{rule["limb"]} transition span is not ordered.')
    if start > sunrise or end <= sunrise:
        return _unknown(
            rule,
            f'{name} does not contain local sunrise, so the active '
            f'{rule["limb"]} boundary is uncertain.',
        )

    local_end = end.astimezone(timezone).isoformat(timespec='seconds')
    local_sunrise = sunrise.astimezone(timezone).isoformat(timespec='seconds')
    local_sunset = sunset.astimezone(timezone).isoformat(timespec='seconds')
    if end < sunset:
        status = 'fail'
        evidence = (
            (
                f'{name} ends at {local_end}, inside daylight '
                f'[{local_sunrise}, {local_sunset}).'
            ),
        )
    else:
        status = 'pass'
        evidence = (
            (
                f'{name} remains active throughout daylight; its next transition '
                f'is {local_end}.'
            ),
        )
    return {
        **_base_outcome(rule),
        'status': status,
        'evidence': list(evidence),
        'active_name': name,
        'transition': local_end,
    }


def evaluate_karnavedha_daylight(day: Any) -> dict[str, Any]:
    """Evaluate both Raman daylight-limb predicates exactly once for a day.

    A result is admitted only when both outcomes are conclusively ``pass``.
    Missing, naive, inconsistent, or otherwise uncertain temporal evidence is
    ``unknown`` and therefore fails closed.
    """
    sunrise = getattr(day, 'sunrise', None)
    sunset = getattr(day, 'sunset', None)
    timezone = _local_timezone(day)
    if (
        not _aware(sunrise)
        or not _aware(sunset)
        or sunrise >= sunset
        or timezone is None
    ):
        outcomes = [
            _unknown(
                rule,
                'Local daylight boundaries are missing, unordered, '
                'timezone-naive, or use an unknown IANA timezone.',
            )
            for rule in _RULES
        ]
    else:
        outcomes = [
            _evaluate_limb(day, rule, sunrise, sunset, timezone)
            for rule in _RULES
        ]
    rejected = any(item['status'] == 'fail' for item in outcomes)
    needs_review = any(item['status'] == 'unknown' for item in outcomes)
    return {
        'policy_id': KARNAVEDHA_DAYLIGHT_POLICY_ID,
        'policy_claim': KARNAVEDHA_DAYLIGHT_POLICY_CLAIM,
        'interval': '[local sunrise, local sunset)',
        'outcomes': outcomes,
        'rejected': rejected,
        'needs_review': needs_review,
        'admissible': all(item['status'] == 'pass' for item in outcomes),
    }


def karnavedha_daylight_drop_reason(assessment: Mapping[str, Any]) -> str:
    """Return one stable diagnosis for a failed-closed daylight assessment."""
    details = []
    for outcome in assessment.get('outcomes', ()):
        status = outcome.get('status')
        if status == 'pass':
            continue
        limb = (
            'Tithi' if outcome.get('rule_id') == KARNAVEDHA_TITHI_RULE_ID
            else 'Nakshatra'
        )
        transition = outcome.get('transition')
        if status == 'fail' and isinstance(transition, str):
            details.append(
                f'{limb} changes at {transition} inside local daylight')
        else:
            details.append(f'{limb} boundary could not be verified')
    return (
        'Karnavedha daylight rule · ' + '; '.join(details)
        if details
        else 'Karnavedha daylight rule admitted'
    )


__all__ = [
    'KARNAVEDHA_DAYLIGHT_POLICY_CLAIM',
    'KARNAVEDHA_DAYLIGHT_POLICY_ID',
    'KARNAVEDHA_NAKSHATRA_RULE_ID',
    'KARNAVEDHA_SOURCE_LOCATOR',
    'KARNAVEDHA_TITHI_RULE_ID',
    'evaluate_karnavedha_daylight',
    'karnavedha_daylight_drop_reason',
]
