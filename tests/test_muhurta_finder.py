"""Muhurta timing contracts; assertions preserved from the original suite."""


import pytest

from telugu_panchangam.personal.muhurta import day_slots
from tests.muhurta_finder_support import ENGINE, _day


def test_slots_never_overlap_inauspicious_windows():
    day = _day(2026, 6, 17)
    bad = [day.rahu_kalam, day.gulika_kalam, day.yamagandam] + day.varjyam + day.durmuhurtham
    for s in day_slots(day):
        for w in bad:
            assert not (s['start'] < w.end and w.start < s['end']), \
                f"slot {s['start']}-{s['end']} overlaps {w.name}"


def test_every_slot_is_a_named_muhurta():
    # Slots are the named 48-min muhurtas now; the identity leads the
    # reasons. Choghadiya is a scoring attribute, not a gate, so a slot
    # may sit in any choghadiya (bad ones just score 0).
    from telugu_panchangam.muhurtas import DAY_MUHURTAS
    day_names = {n for n, _, _ in DAY_MUHURTAS}
    day = _day(2026, 6, 17)
    slots = day_slots(day)
    assert slots
    for s in slots:
        lead = s['reasons'][0]
        assert ' muhurta' in lead, f'slot lead is not a muhurta identity: {lead!r}'
        name = lead.split(' muhurta')[0].split(' (')[0]  # strip '(Abhijit)' tag
        assert name in day_names, f'unknown day muhurta {name!r}'


def test_ranked_by_score_and_carries_reasons():
    slots = day_slots(_day(2026, 6, 17))
    assert slots
    assert all(slots[i]['score'] >= slots[i+1]['score'] for i in range(len(slots)-1))
    assert all(s['reasons'] for s in slots)


def test_travel_avoids_vishti():
    # 2026-06-10: Vishti karana runs 13:52 to past midnight (daytime overlap)
    day = _day(2026, 6, 10)
    vishti = [k for k in day.karana if k.name == 'Vishti']
    assert vishti, 'fixture assumption: Vishti present this day'
    for s in day_slots(day, activity='travel'):
        for k in vishti:
            assert not (s['start'] < k.end and k.start < s['end'])


def test_eclipse_day_returns_no_slots():
    # 2027-08-02: total solar eclipse, visible from Hyderabad.
    day = _day(2027, 8, 2, include_eclipse=True)
    assert day.eclipse is not None, 'fixture assumption: eclipse present this day'
    assert day_slots(day) == [], 'eclipse days are deferred for auspicious activities'


def test_invalid_activity_raises():
    day = _day(2026, 6, 17)
    with pytest.raises(ValueError):
        day_slots(day, activity='not-a-real-activity')


def test_engine_kwarg_changes_late_slot_nakshatra():
    """On 2026-06-17 with engine passed, a slot starting after
    day.nakshatra.end uses the new nakshatra for tarabalam — the score
    can differ from the same slot computed in snapshot mode."""
    day = _day(2026, 6, 17)
    # Snapshot mode (no engine): all slots score using sunrise Punarvasu
    day_slots(day, janma_nakshatras=['Pushya'])
    # Engine mode: slots after Punarvasu's end use the next nakshatra
    eng_slots = day_slots(day, janma_nakshatras=['Pushya'], engine=ENGINE)
    # Pushya's tara on Punarvasu (sunrise) = Parama Mitra (favourable, +1)
    # Pushya's tara on Pushya (post-transition) = Janma (-1)
    # So a late-day slot in engine mode should carry the avoid reason.
    late_eng_reasons = [r for s in eng_slots
                        if s['start'] >= day.nakshatra.end
                        for r in s['reasons']]
    if late_eng_reasons:
        # We have at least one late slot — verify nakshatra-driven swing
        assert any('tarabalam avoid' in r and 'Janma' in r for r in late_eng_reasons), \
            f'late slot should show Janma when nakshatra transitions: {late_eng_reasons}'


def test_engine_kwarg_preserves_early_slot_tara():
    """An early slot (before nakshatra.end) scores identically with or
    without engine — the slot-time nakshatra equals sunrise nakshatra."""
    day = _day(2026, 6, 17)
    snap = day_slots(day, janma_nakshatras=['Pushya'])
    eng_slots = day_slots(day, janma_nakshatras=['Pushya'], engine=ENGINE)
    if not snap or not eng_slots:
        return
    # Find the first slot whose end is before day.nakshatra.end
    early_eng = next((s for s in eng_slots if s['end'] <= day.nakshatra.end), None)
    early_snap = next((s for s in snap if s['end'] <= day.nakshatra.end and
                       s['start'] == early_eng['start']), None) if early_eng else None
    if early_eng and early_snap:
        assert early_eng['score'] == early_snap['score'], \
            f'early slot should score the same in both modes; ' \
            f'eng={early_eng["score"]} snap={early_snap["score"]}'


def test_sarvartha_lapses_for_late_slot():
    """2026-06-25: Sarvartha Siddhi at sunrise via Swati. After Swati ends,
    new nakshatra (Vishakha for Drik) is not in Guruvaram's Sarvartha set
    — late slots in engine mode should NOT carry the Sarvartha bonus."""
    day = _day(2026, 6, 25)
    assert 'Sarvartha Siddhi Yoga' in day.special_yogas
    eng_slots = day_slots(day, engine=ENGINE)
    # Slots after Swati's end (Drik: 10:59 UTC) should not have Sarvartha
    for s in eng_slots:
        if s['start'] >= day.nakshatra.end:
            for r in s['reasons']:
                assert 'Sarvartha Siddhi Yoga' not in r, \
                    f'late slot at {s["start"]} should not credit Sarvartha; got {r}'


def test_sarvartha_active_for_early_slot():
    """The same 2026-06-25 should still credit Sarvartha for slots ending
    before Swati's end."""
    day = _day(2026, 6, 25)
    eng_slots = day_slots(day, engine=ENGINE)
    early = [s for s in eng_slots if s['end'] <= day.nakshatra.end]
    assert early, 'fixture: expected at least one slot before nakshatra transition'
    assert any('Sarvartha Siddhi Yoga' in r for s in early for r in s['reasons'])


def test_invalid_chandra_mode_raises():
    day = _day(2026, 6, 17)
    with pytest.raises(ValueError):
        day_slots(day, chandra_mode='bogus')


def test_misaligned_rasis_raise():
    day = _day(2026, 6, 17)
    with pytest.raises(ValueError):
        day_slots(day, janma_nakshatras=['Pushya'],
                  janma_rasis=['Karka', 'Mesha'])


def test_day_slots_are_muhurtas_of_equal_length():
    """Each day slot is one named muhurta = (sunset-sunrise)/15 — ~48 min,
    breathing with the season (so it can exceed 48 min in summer). All
    day slots on a given day share that exact length.
    """
    for date_args in [(2026, 6, 16), (2026, 6, 17), (2026, 6, 25)]:
        day = _day(*date_args)
        mu_len = (day.sunset - day.sunrise) / 15
        for s in day_slots(day, engine=ENGINE):
            assert abs((s['end'] - s['start'] - mu_len).total_seconds()) < 1, (
                f"{date_args}: slot {s['start']}–{s['end']} is not one muhurta "
                f"({mu_len})")


def test_day_slot_starts_align_to_muhurta_grid():
    """Every slot starts exactly on a muhurta boundary: sunrise + k*(day/15)
    for some k in 0..14. Muhurtas are indivisible now — a bad-window overlap
    excludes the whole muhurta rather than shifting its start.
    """
    day = _day(2026, 6, 17)
    mu_len = (day.sunset - day.sunrise) / 15
    grid = {round((day.sunrise + k * mu_len).timestamp()) for k in range(15)}
    for s in day_slots(day, engine=ENGINE):
        assert round(s['start'].timestamp()) in grid, (
            f"slot start {s['start']} is not on the muhurta grid")


def test_day_produces_at_most_fifteen_distinct_muhurtas():
    """There are 15 daytime muhurtas; the finder returns a subset of them
    (those clear of hard windows), never more, never duplicated."""
    day = _day(2026, 6, 25)
    slots = day_slots(day, engine=ENGINE)
    assert 0 < len(slots) <= 15
    starts = [s['start'] for s in slots]
    assert len(starts) == len(set(starts)), 'a muhurta was emitted twice'
