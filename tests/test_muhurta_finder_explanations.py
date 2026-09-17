"""Muhurta explanations contracts; assertions preserved from the original suite."""

from telugu_panchangam.personal.muhurta import day_slots
from tests.muhurta_finder_support import _day


def test_reason_groups_present_with_expected_keys():
    """Every slot carries a 'reason_groups' dict with the five categories."""
    day = _day(2026, 6, 17)
    slots = day_slots(day, janma_nakshatras=['Krittika'])
    assert slots
    for s in slots:
        rg = s['reason_groups']
        assert set(rg.keys()) == {'slot_quality', 'day_quality',
                                  'group_fit', 'activity_match', 'notes'}
        # slot_quality always has at least the choghadiya line
        assert any('choghadiya' in r for r in rg['slot_quality'])


def _inventory_reason_groups():
    """A slot with Siddha Yoga + tarabalam mixed + tithi-class match
    routes each reason to its category."""
    # 2026-02-12 (Thu) — Siddha Yoga, Krishna Dashami.
    # Inventory purchase explicitly favours Dashami + Guruvaram.
    day = _day(2026, 2, 12)
    slots = day_slots(day, activity='business_inventory_purchase',
                      janma_nakshatras=['Krittika'])
    assert slots
    rg = slots[0]['reason_groups']
    return slots, rg


def test_reason_groups_categorise_correctly():
    _, rg = _inventory_reason_groups()
    # Slot quality leads with the named-muhurta identity, then choghadiya.
    # It must NOT claim "clear of all inauspicious windows" — a slot is only
    # kept when it clears the hard windows, so the line was a tautology that
    # also contradicted any muhurta of inauspicious nature.
    assert any('muhurta' in r for r in rg['slot_quality'])
    assert any('choghadiya' in r for r in rg['slot_quality'])
    assert not any('clear of all inauspicious windows' in r for r in rg['slot_quality'])


def test_reason_groups_separate_day_group_and_activity_evidence():
    slots, rg = _inventory_reason_groups()
    # Day quality contains the Siddha Yoga reason.
    assert any('Siddha Yoga' in r for r in rg['day_quality']) or \
           any('Siddha Yoga' in r for s in slots for r in s['reason_groups']['day_quality'])
    # Group fit contains tarabalam line (favourable or avoid)
    assert any('tarabalam' in r for r in rg['group_fit'])
    # Activity match contains exact Dashami + Guruvaram bonuses.
    assert any('Dashami specifically favoured' in r for r in rg['activity_match'])
    assert any('Guruvaram favoured' in r for r in rg['activity_match'])


def test_doctrinal_note_sarvartha_rectifies_tara():
    """When Sarvartha Siddhi is present AND someone has unfavourable tara,
    a classical-doctrine note appears in reason_groups['notes']."""
    # 2026-06-25 Sarvartha Siddhi day. Krittika on Swati = ?
    # Punarvasu has Krittika at tara=5 (Pratyak — avoid). But 2026-06-25
    # nakshatra is Swati (idx 14). Krittika idx 2. (14-2)%27+1 = 13.
    # (12)%9+1 = 4 (Kshema, favourable). Not unfav.
    # Need someone with unfav tara on Swati: tara=1 (Janma) → Swati itself,
    # so use 'Swati' as janma. (14-14)%27+1 = 1, Janma — avoid.
    day = _day(2026, 6, 25)
    slots = day_slots(day, janma_nakshatras=['Swati'])
    assert slots
    notes = slots[0]['reason_groups']['notes']
    assert any('rectifies tara dosha' in n for n in notes), \
        f'expected Sarvartha rectification note; got {notes}'


def test_doctrinal_note_chandra_dosha_not_rectified():
    """Sarvartha doesn't rectify chandra dosha — that caution surfaces
    when a Siddhi yoga is present AND someone has Moon@4/8/12."""
    day = _day(2026, 6, 25)
    # Krittika padam 1 → Mesha rashi. On 2026-06-25 Moon's rashi
    # is Tula (Swati nakshatra spans Tula). From Mesha to Tula = position
    # 7 (good). Need a rashi with Moon-avoid from Tula.
    # Moon=Tula (idx 6). Avoid positions are {4,8,12}. From rashi r:
    #   pos = (6 - r) % 12 + 1
    # pos=4 → r=3 (Karka). pos=8 → r=11 (Meena). pos=12 → r=7 (Vrischika).
    # Use Pushya (Karka rashi) → Moon@4
    slots = day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'])
    assert slots
    notes = slots[0]['reason_groups']['notes']
    assert any('not rectified' in n and 'chandra' in n.lower() for n in notes), \
        f'expected chandra-not-rectified note; got {notes}'


def test_no_notes_on_clean_day():
    """A day with no Siddhi yoga and clean fits — no doctrinal notes."""
    day = _day(2026, 6, 16)  # no special yogas
    slots = day_slots(day, janma_nakshatras=['Krittika'])
    assert slots
    for s in slots:
        assert s['reason_groups']['notes'] == []


def _reason_group_total(rg):
    """Sum the original signed reason suffixes without calling the scorer."""
    import re
    total = 0
    for cat in ('slot_quality', 'day_quality', 'group_fit', 'activity_match'):
        for r in rg[cat]:
            m = re.search(r'\(([+-]\d+)\)\s*$', r)
            if m:
                total += int(m.group(1))
    return total


def test_reason_groups_score_consistency():
    """The sum of (+N)/(-N) across all groups equals the slot's score."""
    day = _day(2026, 4, 20)
    slots = day_slots(day, activity='wedding',
                      janma_nakshatras=['Krittika'], janma_rasis=['Mesha'])
    assert slots
    for s in slots:
        rg = s['reason_groups']
        total = _reason_group_total(rg)
        assert total == s['score'], \
            f'groups sum {total} != score {s["score"]} ({rg})'


def test_diagnose_day_eclipse():
    from telugu_panchangam.personal.muhurta import diagnose_day
    # 2027-08-02: total solar eclipse, Hyderabad
    day = _day(2027, 8, 2, include_eclipse=True)
    reason = diagnose_day(day)
    assert reason
    assert 'eclipse' in reason.lower()


def test_diagnose_day_samskara_skip_on_dagdha():
    from telugu_panchangam.personal.muhurta import diagnose_day
    # 2026-06-17 has Dagdha Yoga — wedding defers
    day = _day(2026, 6, 17)
    reason = diagnose_day(day, activity='wedding')
    assert reason
    assert 'Dagdha' in reason


def test_diagnose_day_samskara_skip_on_vaidhriti():
    from telugu_panchangam.personal.muhurta import diagnose_day
    # 2026-07-02 has Vaidhriti at sunrise
    day = _day(2026, 7, 2)
    reason = diagnose_day(day, activity='wedding')
    assert reason
    assert 'Vaidhriti' in reason


def test_diagnose_day_returns_none_when_clear():
    from telugu_panchangam.personal.muhurta import diagnose_day
    # 2026-06-16 — clean day (Bhadra tithi, no special yogas)
    day = _day(2026, 6, 16)
    assert diagnose_day(day, activity='any') is None
