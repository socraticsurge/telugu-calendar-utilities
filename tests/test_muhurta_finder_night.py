"""Muhurta night contracts; assertions preserved from the original suite."""

from tests.muhurta_finder_support import ENGINE, _two_days


def test_night_slots_timing_between_sunset_and_next_sunrise():
    from telugu_panchangam.personal.muhurta import night_slots
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    assert slots, 'expected night slots on a clean day'
    for s in slots:
        assert s['start'] >= day.sunset, 'slot must start at or after sunset'
        assert s['end'] <= next_day.sunrise, 'slot must end at or before next sunrise'


def test_night_slots_are_named_night_muhurtas():
    from telugu_panchangam.muhurtas import NIGHT_MUHURTAS
    from telugu_panchangam.personal.muhurta import night_slots
    night_names = {n for n, _, _ in NIGHT_MUHURTAS}
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    assert slots
    for s in slots:
        lead = s['reasons'][0]
        assert ' muhurta' in lead, f'night slot lead is not a muhurta identity: {lead!r}'
        name = lead.split(' muhurta')[0].split(' (')[0]
        assert name in night_names, f'unknown night muhurta {name!r}'


def test_night_slots_do_not_overlap_varjyam():
    from telugu_panchangam.personal.muhurta import night_slots
    # 2026-06-11: Amrita Kalam 23:49–01:17 — confirms night windows exist.
    # Check that any varjyam window never overlaps night slots.
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    for s in slots:
        for w in day.varjyam:
            assert not (s['start'] < w.end and w.start < s['end']), \
                f"night slot {s['start']}-{s['end']} overlaps varjyam {w.start}-{w.end}"


def test_night_slots_exclude_rahu_gulika_yamagandam():
    from telugu_panchangam.personal.muhurta import night_slots
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    # Rahu/Gulika/Yamagandam are daytime-only; night slots must never overlap them.
    for s in slots:
        for w in [day.rahu_kalam, day.gulika_kalam, day.yamagandam]:
            assert not (s['start'] < w.end and w.start < s['end']), \
                f"night slot overlaps daytime window {w.name}"


def test_night_slots_brahma_muhurta_bonus():
    # Brahma is now the 14th night muhurta, scored +2 via its nature
    # (it leads the slot's reasons as "Brahma muhurta ... (+2)").
    from telugu_panchangam.personal.muhurta import night_slots
    day, next_day = _two_days(2026, 6, 1)
    slots = night_slots(day, next_day, engine=ENGINE)
    brahma_slots = [s for s in slots if s['reasons'][0].startswith('Brahma muhurta')]
    assert brahma_slots, 'expected the Brahma (14th night) muhurta to surface on 2026-06-01'
    for s in brahma_slots:
        assert '(+2)' in s['reasons'][0], \
            f'Brahma muhurta should carry +2 nature; got {s["reasons"][0]!r}'


def test_night_slots_nishita_kala_bonus():
    from telugu_panchangam.personal.muhurta import night_slots
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    nishita_slots = [s for s in slots
                     if any('Nishita Kala' in r for r in s['reasons'])]
    assert nishita_slots, 'expected at least one slot overlapping Nishita Kala'
    for s in nishita_slots:
        bonus_reasons = [r for r in s['reasons'] if 'Nishita Kala' in r]
        assert any('+2' in r for r in bonus_reasons), \
            f'Nishita Kala should carry +2 bonus; got {bonus_reasons}'


def test_night_slots_no_abhijit_bonus():
    from telugu_panchangam.personal.muhurta import night_slots
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    for s in slots:
        assert not any('Abhijit' in r for r in s['reasons']), \
            'Abhijit Muhurta must not appear in night slot reasons'


def test_night_slots_amrita_kalam_bonus_if_present():
    from telugu_panchangam.personal.muhurta import night_slots
    # 2026-06-11 (Ashvini): second Amrita Kalam at 23:49–01:17 IST falls in the night.
    day, next_day = _two_days(2026, 6, 11)
    slots = night_slots(day, next_day, engine=ENGINE)
    amrita_slots = [s for s in slots
                    if any('Amrita Kalam' in r for r in s['reasons'])]
    # If Amrita Kalam is present in night it must carry +2.
    for s in amrita_slots:
        bonus = [r for r in s['reasons'] if 'Amrita Kalam' in r]
        assert any('+2' in r for r in bonus), f'expected +2; got {bonus}'


def test_night_slots_reason_groups_have_slot_quality():
    from telugu_panchangam.personal.muhurta import night_slots
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    assert slots
    for s in slots:
        rg = s['reason_groups']
        assert 'slot_quality' in rg
        assert 'day_quality' in rg
        assert 'group_fit' in rg
        assert 'activity_match' in rg
        assert rg['slot_quality'], 'slot_quality should have at least the choghadiya chip'


def test_night_slots_sorted_by_tier_then_score():
    from telugu_panchangam.personal.muhurta import TIER_NAMES, night_slots
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    assert slots
    for i in range(len(slots) - 1):
        a, b = slots[i], slots[i + 1]
        rank_a = TIER_NAMES.index(a['tier'])
        rank_b = TIER_NAMES.index(b['tier'])
        assert rank_a > rank_b or (rank_a == rank_b and a['score'] >= b['score'])


def test_night_slots_eclipse_returns_empty():
    from telugu_panchangam.models.panchangam_day import EclipseInfo
    from telugu_panchangam.personal.muhurta import night_slots
    day, next_day = _two_days(2026, 6, 16)
    from dataclasses import replace
    day_with_eclipse = replace(day, eclipse=EclipseInfo(
        kind='Solar', subtype='Total', start=day.sunrise,
        end=day.sunset, visible=False, sutak_start=day.sunrise, sutak_end=day.sunset))
    assert night_slots(day_with_eclipse, next_day) == []


def test_night_slots_are_at_most_48_minutes():
    """Night slot windows are also ≤ 48 minutes."""
    from datetime import timedelta

    from telugu_panchangam.personal.muhurta import MUHURTA_MINUTES, night_slots
    limit = timedelta(minutes=MUHURTA_MINUTES)
    for date_args in [(2026, 6, 16), (2026, 6, 25)]:
        day, next_day = _two_days(*date_args)
        for s in night_slots(day, next_day, engine=ENGINE):
            duration = s['end'] - s['start']
            assert duration <= limit, (
                f"{date_args}: night slot {s['start']}–{s['end']} is {duration}"
            )
