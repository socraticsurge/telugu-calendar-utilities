# Muhurta finder: slots derive from already-verified engine windows.
from datetime import date

import pytest

from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES
from telugu_panchangam.personal.muhurta import (
    day_slots, GOOD_CHOGHADIYA, relative_tier,
)

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(y, m, d, include_eclipse=False):
    return ENGINE.calculate(date(y, m, d), HYD, include_eclipse=include_eclipse)


def _expected_tier(slots, score, personal_dosha, day_dosha):
    """Recompute the relative tier the same way assign_tiers() does."""
    all_scores = [s['score'] for s in slots]
    ceiling, floor = max(all_scores), min(all_scores)
    tier = relative_tier(score, ceiling, floor)
    if tier == 'Excellent' and (personal_dosha is not None or day_dosha is not None):
        tier = 'Good'
    return tier


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
    assert slots and all(slots[i]['score'] >= slots[i+1]['score'] for i in range(len(slots)-1))
    assert all(s['reasons'] for s in slots)


def test_travel_avoids_vishti():
    # 2026-06-10: Vishti karana runs 13:52 to past midnight (daytime overlap)
    day = _day(2026, 6, 10)
    vishti = [k for k in day.karana if k.name == 'Vishti']
    assert vishti, 'fixture assumption: Vishti present this day'
    for s in day_slots(day, activity='travel'):
        for k in vishti:
            assert not (s['start'] < k.end and k.start < s['end'])


# --- Tarabalam: graded per-person (no longer hard-skip) ---

def test_tarabalam_favourable_adds_per_person_bonus():
    # 2026-06-17 (Punarvasu): Parama Mitra for Uttara Bhadrapada -> +1
    slots = day_slots(_day(2026, 6, 17), janma_nakshatras=['Uttara Bhadrapada'])
    assert slots, 'favourable day should produce slots'
    reasons = slots[0]['reasons']
    assert any('tarabalam favourable' in r and '(+1)' in r for r in reasons), \
        f'expected +1 tarabalam reason; got {reasons}'


def test_tarabalam_unfavourable_keeps_day_but_penalises():
    # 2026-06-18 (Pushya): Janma tara for Uttara Bhadrapada.
    # Old behavior was to hard-skip; new graded behavior keeps the slot at -1.
    slots = day_slots(_day(2026, 6, 18), janma_nakshatras=['Uttara Bhadrapada'])
    assert slots, 'graded scoring should not hard-skip a Janma day'
    assert any('tarabalam avoid' in r and '(-1)' in r for s in slots for r in s['reasons'])


def test_tarabalam_mixed_group_nets_correctly():
    # 2026-06-17 (Punarvasu).
    # Uttara Bhadrapada -> Parama Mitra (favourable, +1)
    # Vishakha -> Janma (unfavourable, -1)  (Vishakha sits 9 stars before Punarvasu)
    # Net tarabalam: 0
    slots = day_slots(_day(2026, 6, 17),
                      janma_nakshatras=['Uttara Bhadrapada', 'Vishakha'])
    assert slots
    rs = slots[0]['reasons']
    assert any('tarabalam favourable' in r and '(+1)' in r for r in rs)
    assert any('tarabalam avoid' in r and '(-1)' in r for r in rs)


# --- Chandrabalam: graded per-person, mode filters not scores ---

def test_chandrabalam_good_adds_bonus_in_default_mode():
    # 2026-06-17: Moon is in Mithuna. Janma rashi Mesha -> position 3 (good).
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Krittika'],
                      janma_rasis=['Mesha'])
    assert slots
    assert any('chandrabalam favourable' in r and '(+1)' in r for r in slots[0]['reasons'])


def test_chandrabalam_remedial_annotates_no_score():
    # 2026-06-17 Moon in Mithuna. Vrishabha -> position 2 (remedial).
    # Rohini (Kshema on Punarvasu, favourable tarabalam) sits in Vrishabha.
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Rohini'],
                      janma_rasis=['Vrishabha'])
    assert slots
    rs = slots[0]['reasons']
    # remedial gives no bonus and no penalty — just an annotation line
    assert any('chandrabalam remedial' in r for r in rs)
    assert not any('chandrabalam favourable' in r for r in rs)


def test_chandrabalam_avoid_subtracts():
    # 2026-06-17 Moon in Mithuna. Karka -> position 12 (avoid).
    # Pushya (Parama Mitra on Punarvasu, favourable tarabalam) sits in Karka.
    day = _day(2026, 6, 17)
    slots = day_slots(day,
                      janma_nakshatras=['Pushya'],
                      janma_rasis=['Karka'])
    assert slots, 'default stars mode does not filter avoid days'
    rs = slots[0]['reasons']
    assert any('chandrabalam avoid' in r and '(-1)' in r for r in rs)


def test_chandra_mode_strict_filters_remedial_and_avoid_days():
    day = _day(2026, 6, 17)
    # Rohini + Vrishabha -> Moon@2 = remedial; strict mode filters out
    assert day_slots(day, janma_nakshatras=['Rohini'], janma_rasis=['Vrishabha'],
                    chandra_mode='strict') == []
    # Pushya + Karka -> Moon@12 = avoid; strict and puja_ok both filter
    assert day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'],
                    chandra_mode='strict') == []
    assert day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'],
                    chandra_mode='puja_ok') == []
    # But puja_ok keeps remedial days (Rohini + Vrishabha)
    assert day_slots(day, janma_nakshatras=['Rohini'], janma_rasis=['Vrishabha'],
                    chandra_mode='puja_ok'), \
        'puja_ok should keep remedial days'


def test_chandrabalam_scores_identical_across_modes():
    """The same slot has the same score regardless of mode — mode only filters."""
    day = _day(2026, 6, 17)
    # Mesha -> Moon@3 = good. Visible in all three modes; score must match.
    args = dict(janma_nakshatras=['Krittika'], janma_rasis=['Mesha'])
    s_stars = day_slots(day, **args, chandra_mode='stars')
    s_puja = day_slots(day, **args, chandra_mode='puja_ok')
    s_strict = day_slots(day, **args, chandra_mode='strict')
    assert s_stars and s_puja and s_strict
    assert [s['score'] for s in s_stars] == [s['score'] for s in s_puja]
    assert [s['score'] for s in s_stars] == [s['score'] for s in s_strict]


# --- Eclipse hard-skip ---

def test_eclipse_day_returns_no_slots():
    # 2027-08-02: total solar eclipse, visible from Hyderabad.
    day = _day(2027, 8, 2, include_eclipse=True)
    assert day.eclipse is not None, 'fixture assumption: eclipse present this day'
    assert day_slots(day) == [], 'eclipse days are deferred for auspicious activities'


# --- Validation ---

def test_invalid_activity_raises():
    with pytest.raises(ValueError):
        day_slots(_day(2026, 6, 17), activity='not-a-real-activity')


# --- Activity taxonomy (Batch D) ---

def test_all_36_activities_callable():
    from telugu_panchangam.personal.muhurta import ACTIVITIES, ACTIVITY_RULES
    from telugu_panchangam.personal.activity_rules import ACTIVITY_ALIASES
    assert len(ACTIVITIES) == 36
    # backward-compat: every old key must still be accepted
    for old in ('any', 'travel', 'purchase', 'ceremony', 'beginning'):
        assert old in ACTIVITY_RULES
    # spot check existing keys
    for new in ('wedding', 'gruhapravesha', 'naming', 'annaprasana',
                'karnavedha', 'mundana', 'upanayana', 'vidyarambha',
                'engagement', 'vehicle', 'property', 'gold', 'bhumi_puja',
                'business', 'job', 'yajna', 'pilgrimage', 'court', 'surgery'):
        assert new in ACTIVITY_RULES
    assert ACTIVITY_ALIASES['litigation'] == 'court'
    assert 'litigation' in ACTIVITIES
    # Task 15: Nakshatra Mukha activities
    for mukha_act in ('well_digging', 'coronation'):
        assert mukha_act in ACTIVITY_RULES
    # Panchaka-restricted activities
    for panchaka in ('cremation', 'construction_roof', 'wood_cutting'):
        assert panchaka in ACTIVITY_RULES
    # every row has a label
    for k, row in ACTIVITY_RULES.items():
        assert row.get('label'), f'activity {k!r} missing label'


def test_wedding_skips_dagdha_day():
    # 2026-06-17 carries Dagdha Yoga — samskara activities are deferred.
    day = _day(2026, 6, 17)
    assert 'Dagdha Yoga' in day.special_yogas, 'fixture assumption'
    assert day_slots(day, activity='wedding') == []
    # And the other samskaras that ride the same rule:
    for samskara in ('gruhapravesha', 'upanayana', 'naming',
                     'annaprasana', 'karnavedha', 'mundana',
                     'engagement', 'bhumi_puja', 'yajna', 'vidyarambha'):
        assert day_slots(day, activity=samskara) == [], \
            f'{samskara} should defer on Dagdha day'


def test_vehicle_applies_labh_bonus():
    # Vehicle prefers the Labh choghadiya. A muhurta whose dominant
    # choghadiya is Labh should carry the "Labh favoured for Vehicle" bonus.
    day = _day(2026, 6, 17)
    slots = day_slots(day, activity='vehicle')
    labh_slots = [s for s in slots
                  if any(r.startswith('Labh choghadiya') for r in s['reasons'])]
    assert labh_slots, 'expected at least one muhurta in the Labh choghadiya'
    assert any('Labh favoured for Vehicle purchase' in r
               for r in labh_slots[0]['reasons'])


def test_surgery_avoids_vishti():
    # 2026-06-10 has Vishti karana in the daytime window.
    day = _day(2026, 6, 10)
    vishti = [k for k in day.karana if k.name == 'Vishti']
    assert vishti
    for s in day_slots(day, activity='surgery'):
        for k in vishti:
            assert not (s['start'] < k.end and k.start < s['end'])


def test_pilgrimage_avoids_vishti():
    day = _day(2026, 6, 10)
    vishti = [k for k in day.karana if k.name == 'Vishti']
    assert vishti
    for s in day_slots(day, activity='pilgrimage'):
        for k in vishti:
            assert not (s['start'] < k.end and k.start < s['end'])


def test_naming_uses_shubh_bonus():
    # Naming has prefer_choghadiya=('Shubh', 1) — verify the reason appears.
    day = _day(2026, 6, 17)
    slots = day_slots(day, activity='naming')
    shubh = [s for s in slots if s['reasons'][0].startswith('Shubh ')]
    if shubh:  # at least one Shubh block clear of bad windows
        assert any('Shubh favoured for Naming' in r for r in shubh[0]['reasons'])


def test_court_uses_exact_source_gates_not_tithi_family_bonus():
    # 2026-04-20 is an admitted Monday, Shukla Tritiya (Jaya), Rohini day.
    # The corrected filing profile admits it without a Jaya-family proxy.
    day = _day(2026, 4, 20)
    slots = day_slots(day, activity='court')
    assert slots
    assert not any('Jaya' in r and 'favoured' in r
                   for s in slots for r in s['reasons'])


# --- Tithi family + Vara (Batch B) ---
#
# Calendar pins (verified against the Drik engine for Hyderabad):
#   2026-06-16  Tue  Shukla Dwitiya       Bhadra   (no special yogas)
#   2026-06-17  Wed  Shukla Tritiya       Jaya     (Dagdha Yoga)
#   2026-06-18  Thu  Shukla Chaturthi     Rikta    (Sarvartha + Amrita Siddhi)
#   2026-06-19  Fri  Shukla Panchami      Purna    (no yogas)
#   2026-06-21  Sun  Shukla Saptami       Bhadra   (no yogas)
#   2026-06-23  Tue  Shukla Navami        Rikta    (no yogas)
#   2026-06-26  Fri  Shukla Dwadashi      Bhadra   (no yogas)
#   2026-06-29  Mon  Pournami             Purna    (no yogas)
#   2026-07-02  Thu  Krishna Dwitiya      Bhadra   (no yogas)

def test_tithi_family_classification():
    from telugu_panchangam.personal.tithi_class import (
        tithi_number, tithi_family, FAMILIES,
    )
    # Engine-canonical names (Pratipat, Shashthi) and the two terminus
    # aliases (Pournami / Amavasya) all map correctly.
    assert tithi_family('Shukla Pratipat') == 'Nanda'        # 1
    assert tithi_family('Shukla Shashthi') == 'Nanda'        # 6
    assert tithi_family('Parama Ekadashi') == 'Nanda'        # 11 — named Ekadashi
    assert tithi_family('Shukla Dwitiya') == 'Bhadra'        # 2
    assert tithi_family('Krishna Trayodashi') == 'Jaya'      # 13
    assert tithi_family('Krishna Chaturdashi') == 'Rikta'    # 14
    assert tithi_family('Pournami') == 'Purna'               # Shukla terminus
    assert tithi_family('Amavasya') == 'Purna'               # Krishna terminus
    # Common spelling alternates still parse.
    assert tithi_family('Shukla Pratipada') == 'Nanda'       # alias for Pratipat
    assert tithi_family('Krishna Shashti') == 'Nanda'        # alias for Shashthi
    # tithi_number returns 1..15
    assert tithi_number('Krishna Dwadashi') == 12
    # every family has 3 tithis
    from telugu_panchangam.personal.tithi_class import TITHI_NUMBER_FAMILY
    from collections import Counter
    counts = Counter(TITHI_NUMBER_FAMILY.values())
    for fam in FAMILIES:
        assert counts[fam] == 3, f'{fam} should have 3 tithis, got {counts[fam]}'


def test_rikta_tithi_universal_penalty():
    # 2026-06-23 — Shukla Navami (9, Rikta), no special yogas. Pure Rikta.
    day = _day(2026, 6, 23)
    slots = day_slots(day, activity='any')
    assert slots
    assert any('Rikta tithi' in r and '(-2)' in r
               for s in slots for r in s['reasons'])


def test_rikta_penalty_applies_to_generic_activity():
    # Same Rikta day, with the generic explorer — penalty still appears.
    day = _day(2026, 6, 23)
    slots = day_slots(day, activity='any')
    assert any('Rikta tithi' in r and '(-2)' in r
               for s in slots for r in s['reasons'])


def test_pournami_rejected_for_wedding_instead_of_purna_bonus():
    assert day_slots(_day(2026, 6, 29), activity='wedding') == []


def test_court_does_not_inherit_jaya_tithi_bonus():
    slots = day_slots(_day(2026, 4, 20), activity='court')
    assert slots
    assert not any('Jaya' in r and 'favoured' in r
                   for s in slots for r in s['reasons'])


def test_gruhapravesha_uses_exact_source_gates_not_tithi_family_bonus():
    # The corrected profile rejects Sunday outright and admits the source's
    # Jaya-family Shukla Tritiya/Trayodashi instead of penalizing the family.
    assert day_slots(_day(2026, 6, 21), activity='gruhapravesha') == []
    slots = day_slots(_day(2026, 4, 20), activity='gruhapravesha')
    assert slots
    assert not any('Bhadra' in r or 'Jaya' in r
                   for slot in slots for r in slot['reasons'])


def test_vara_bonus_thursday_wedding():
    day = _day(2026, 2, 26)  # Thu, Shukla Dashami, Mrigashira
    slots = day_slots(day, activity='wedding')
    assert slots
    reasons = [r for s in slots for r in s['reasons']]
    assert any('Guruvaram favoured for Wedding' in r for r in reasons)
    assert not any('Purna' in r or 'Jaya' in r for r in reasons)


def test_vara_bonus_friday_vehicle():
    # 2026-06-19 (Fri) = Shukla Panchami (Purna). Vehicle prefers Bhadra
    # tithi (not Purna) and Shukravaram vara — only vara fires.
    day = _day(2026, 6, 19)
    slots = day_slots(day, activity='vehicle')
    assert slots
    reasons = [r for s in slots for r in s['reasons']]
    assert any('Shukravaram favoured for Vehicle' in r for r in reasons)


def test_vara_and_tithi_class_stack():
    # 2026-06-26 (Fri) = Shukla Dwadashi (Bhadra). Vehicle prefers both
    # Bhadra tithi AND Shukravaram vara — both bonuses should appear.
    day = _day(2026, 6, 26)
    slots = day_slots(day, activity='vehicle')
    assert slots
    reasons = [r for s in slots for r in s['reasons']]
    assert any('Bhadra' in r and 'favoured for Vehicle' in r for r in reasons)
    assert any('Shukravaram favoured for Vehicle' in r for r in reasons)


def test_tuesday_is_rejected_for_court_filing():
    day = _day(2026, 6, 16)
    assert day_slots(day, activity='court') == []


def test_no_vara_match_no_bonus():
    # 2026-06-16 (Tue) with activity='any' — 'any' has no prefer_vara.
    day = _day(2026, 6, 16)
    slots = day_slots(day, activity='any')
    assert slots
    for s in slots:
        for r in s['reasons']:
            assert 'Mangalavaram favoured' not in r
            assert 'favoured for Anything auspicious' not in r


# --- Nitya Yoga scoring (Batch B-2) ---

def test_vaidhriti_defers_wedding():
    """2026-07-02 (Thu) carries Vaidhriti yoga at sunrise. Vaidhriti is a
    hard-avoid Nitya yoga — samskara activities (wedding, gruhapravesha,
    etc.) defer outright."""
    day = _day(2026, 7, 2)
    assert day.yoga.name == 'Vaidhriti', 'fixture: 2026-07-02 should be Vaidhriti'
    assert day_slots(day, activity='wedding') == []
    assert day_slots(day, activity='gruhapravesha') == []
    assert day_slots(day, activity='upanayana') == []


def test_vaidhriti_penalises_non_samskara():
    """For non-samskara activities, Vaidhriti is -2 day_bonus + reason
    but does not defer the day."""
    day = _day(2026, 7, 2)
    # Slots before yoga ends are under Vaidhriti — they get -2
    eng_slots = day_slots(day, activity='any', engine=ENGINE)
    # Check at least one early slot carries the Vaidhriti penalty
    early = [s for s in eng_slots if s['start'] <= day.yoga.end]
    assert early
    assert any('Vaidhriti yoga (-2)' in r for s in early for r in s['reasons'])


def test_auspicious_nitya_yoga_bonus():
    """2026-07-16 (Thu) = Siddhi yoga (auspicious). Slots under Siddhi
    pick up the +1 bonus."""
    day = _day(2026, 7, 16)
    assert day.yoga.name == 'Siddhi'
    eng_slots = day_slots(day, activity='any', engine=ENGINE)
    assert eng_slots
    early = [s for s in eng_slots if s['start'] <= day.yoga.end]
    assert any('Siddhi yoga (+1)' in r for s in early for r in s['reasons'])


def test_partial_avoid_nitya_dosha_window():
    """2026-06-18 sunrise yoga = Vyaghata (partial-avoid). Slots inside
    the 9-ghati dosha-window get -1; slots outside don't."""
    from datetime import timedelta
    day = _day(2026, 6, 18)
    assert day.yoga.name == 'Vyaghata'
    window_end = day.yoga.start + timedelta(minutes=9 * 24)  # 216 min
    eng_slots = day_slots(day, activity='any', engine=ENGINE)
    in_window = [s for s in eng_slots if s['start'] < window_end]
    out_window = [s for s in eng_slots if s['start'] >= window_end
                                       and s['start'] < day.yoga.end]
    if in_window:
        assert any('Vyaghata yoga dosha-window' in r
                   for s in in_window for r in s['reasons'])
    if out_window:
        # Outside the dosha-window — no penalty reason
        for s in out_window:
            assert not any('Vyaghata yoga dosha-window' in r for r in s['reasons'])


def test_neutral_nitya_yoga_no_score():
    """Vajra and Variyan are explicitly neutral — no bonus, no penalty."""
    from telugu_panchangam.personal.nitya_yoga import nitya_disposition
    assert nitya_disposition('Vajra') == 'neutral'
    assert nitya_disposition('Variyan') == 'neutral'


# --- Reason grouping + doctrinal notes (Batch C #16) ---

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


def test_reason_groups_categorise_correctly():
    """A slot with Sarvartha Siddhi + tarabalam mixed + tithi-class match
    routes each reason to its category."""
    # 2026-06-25 (Thu) — Sarvartha Siddhi at sunrise, Shukla Ekadashi (Nanda).
    # Legacy Job profile prefers Nanda + Guruvaram, so all categories fire.
    day = _day(2026, 6, 25)
    slots = day_slots(day, activity='job',
                      janma_nakshatras=['Krittika'])
    assert slots
    rg = slots[0]['reason_groups']
    # Slot quality leads with the named-muhurta identity, then choghadiya.
    # It must NOT claim "clear of all inauspicious windows" — a slot is only
    # kept when it clears the hard windows, so the line was a tautology that
    # also contradicted any muhurta of inauspicious nature.
    assert any('muhurta' in r for r in rg['slot_quality'])
    assert any('choghadiya' in r for r in rg['slot_quality'])
    assert not any('clear of all inauspicious windows' in r for r in rg['slot_quality'])
    # Day quality contains the Sarvartha yoga reason
    assert any('Sarvartha Siddhi' in r for r in rg['day_quality']) or \
           any('Sarvartha Siddhi' in r for s in slots for r in s['reason_groups']['day_quality'])
    # Group fit contains tarabalam line (favourable or avoid)
    assert any('tarabalam' in r for r in rg['group_fit'])
    # Activity match contains Nanda + Guruvaram bonuses
    assert any('Nanda' in r and 'favoured for Job' in r for r in rg['activity_match'])
    assert any('Guruvaram favoured for Job' in r for r in rg['activity_match'])


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


def test_reason_groups_score_consistency():
    """The sum of (+N)/(-N) across all groups equals the slot's score."""
    import re
    day = _day(2026, 4, 20)
    slots = day_slots(day, activity='wedding',
                      janma_nakshatras=['Krittika'], janma_rasis=['Mesha'])
    assert slots
    for s in slots:
        rg = s['reason_groups']
        total = 0
        for cat in ('slot_quality', 'day_quality', 'group_fit', 'activity_match'):
            for r in rg[cat]:
                m = re.search(r'\(([+-]\d+)\)\s*$', r)
                if m:
                    total += int(m.group(1))
        assert total == s['score'], \
            f'groups sum {total} != score {s["score"]} ({rg})'


# --- Tier mapping (Batch C #15) ---

def test_score_tier_thresholds():
    from telugu_panchangam.personal.muhurta import score_tier
    # Excellent: ≥ 7
    assert score_tier(7) == 'Excellent'
    assert score_tier(15) == 'Excellent'
    # Good: 4..6
    assert score_tier(6) == 'Good'
    assert score_tier(4) == 'Good'
    # Fair: 1..3
    assert score_tier(3) == 'Fair'
    assert score_tier(1) == 'Fair'
    # Avoid: ≤ 0
    assert score_tier(0) == 'Avoid'
    assert score_tier(-5) == 'Avoid'


def test_each_slot_carries_a_tier():
    """Every slot has a `tier` field matching its relative score band."""
    day = _day(2026, 6, 17)
    slots = day_slots(day)
    assert slots
    for s in slots:
        assert s['tier'] == _expected_tier(slots, s['score'], s['personal_dosha'], s['day_dosha'])
        assert s['tier'] in ('Excellent', 'Good', 'Fair', 'Avoid')


# --- Personal (chandra) dosha: tier cap + sort tiebreaker ---

def test_personal_dosha_none_when_chandra_and_tara_clean():
    # 2026-06-17: Mesha -> Moon@3 (good) — no chandra caution.
    # janma=Krittika may still set tara_dosha for the day's nakshatras;
    # what we're asserting here is the chandra branch stays clean.
    day = _day(2026, 6, 17)
    slots = day_slots(day, janma_nakshatras=['Krittika'], janma_rasis=['Mesha'])
    assert slots
    assert all(s['personal_dosha'] not in ('chandra_avoid', 'chandra_remedial')
               for s in slots)


def test_personal_dosha_tara_dosha_caps_tier():
    # 2026-06-20: janma Ashvini sees an unfavourable tara on this day's
    # nakshatra, and no Sarvartha/Amrita Siddhi Yoga rectifies it. The
    # top slot should be flagged 'tara_dosha' and capped below Excellent.
    day = _day(2026, 6, 20)
    slots = day_slots(day, janma_nakshatras=['Ashvini'])
    assert slots
    top = slots[0]
    assert top['personal_dosha'] == 'tara_dosha'
    assert top['tier'] != 'Excellent'


def test_personal_dosha_chandra_avoid_caps_tier():
    # 2026-06-25: Pushya + Karka -> Moon@4 (avoid, non-Ashtama). The top
    # slot scores 8 (Excellent by raw score — now including the +1 for the
    # muhurta's auspicious nature) but the unrectified chandra_avoid dosha
    # caps its tier at Good.
    from telugu_panchangam.personal.muhurta import score_tier
    day = _day(2026, 6, 25)
    slots = day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'])
    assert slots
    top = slots[0]
    assert top['score'] == 8
    assert score_tier(top['score']) == 'Excellent'
    assert top['personal_dosha'] == 'chandra_avoid'
    assert top['tier'] == 'Good'


def test_personal_dosha_chandra_remedial_caps_tier_when_excellent():
    # 2026-06-17: Rohini + Vrishabha -> Moon@2 (remedial/puja position).
    day = _day(2026, 6, 17)
    slots = day_slots(day, janma_nakshatras=['Rohini'], janma_rasis=['Vrishabha'])
    assert slots
    for s in slots:
        assert s['personal_dosha'] == 'chandra_remedial'
        assert s['tier'] == _expected_tier(slots, s['score'], s['personal_dosha'], s['day_dosha'])


def test_sort_tiebreaker_prefers_personally_clean_slot():
    """Among equal-score slots, the one without a personal dosha sorts first."""
    day = _day(2026, 6, 25)
    slots = day_slots(day, janma_nakshatras=['Pushya'], janma_rasis=['Karka'])
    assert slots
    # The sort key (-score, has_personal_dosha, start) must be honoured —
    # for any pair of equal-score slots, a clean one (if present) cannot
    # follow a dosha-bearing one.
    for i in range(len(slots) - 1):
        a, b = slots[i], slots[i + 1]
        if a['score'] == b['score']:
            assert (a['personal_dosha'] is not None) <= (b['personal_dosha'] is not None)


# --- Day-level dosha (Rikta tithi / Visha-Dagdha / Vyatipata-Vaidhriti): tier cap ---

def test_day_dosha_rikta_tithi_caps_tier_when_excellent():
    # 2026-06-14: Krishna Chaturdashi (Rikta tithi). A slot here should
    # never show as "Excellent" even if its raw score is the batch ceiling.
    day = _day(2026, 6, 14)
    slots = day_slots(day)
    assert slots
    rikta_slots = [s for s in slots if s['day_dosha'] == 'rikta_tithi']
    assert rikta_slots
    for s in rikta_slots:
        assert s['tier'] == _expected_tier(slots, s['score'], s['personal_dosha'], s['day_dosha'])
        assert s['tier'] != 'Excellent'


def test_day_dosha_amavasya_caps_tier_when_excellent():
    # 2026-06-15: Amavasya. Treated same as Rikta tithi for tier-cap.
    day = _day(2026, 6, 15)
    slots = day_slots(day)
    assert slots
    amavasya_slots = [s for s in slots if s['day_dosha'] == 'amavasya']
    assert amavasya_slots
    for s in amavasya_slots:
        assert s['tier'] == _expected_tier(slots, s['score'], s['personal_dosha'], s['day_dosha'])
        assert s['tier'] != 'Excellent'


def test_day_dosha_none_on_clean_day():
    day = _day(2026, 6, 16)
    slots = day_slots(day)
    assert slots
    assert all(s['day_dosha'] is None for s in slots)


# --- dropped_days transparency (Batch C #17) ---

def test_diagnose_day_eclipse():
    from telugu_panchangam.personal.muhurta import diagnose_day
    # 2027-08-02: total solar eclipse, Hyderabad
    day = _day(2027, 8, 2, include_eclipse=True)
    reason = diagnose_day(day)
    assert reason and 'eclipse' in reason.lower()


def test_diagnose_day_samskara_skip_on_dagdha():
    from telugu_panchangam.personal.muhurta import diagnose_day
    # 2026-06-17 has Dagdha Yoga — wedding defers
    day = _day(2026, 6, 17)
    reason = diagnose_day(day, activity='wedding')
    assert reason and 'Dagdha' in reason


def test_diagnose_day_samskara_skip_on_vaidhriti():
    from telugu_panchangam.personal.muhurta import diagnose_day
    # 2026-07-02 has Vaidhriti at sunrise
    day = _day(2026, 7, 2)
    reason = diagnose_day(day, activity='wedding')
    assert reason and 'Vaidhriti' in reason


def test_diagnose_day_returns_none_when_clear():
    from telugu_panchangam.personal.muhurta import diagnose_day
    # 2026-06-16 — clean day (Bhadra tithi, no special yogas)
    day = _day(2026, 6, 16)
    assert diagnose_day(day, activity='any') is None


def test_mcp_find_muhurta_emits_dropped_days():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    # Wedding over 2026-06-16 to 2026-06-20 — should drop 06-17 (Dagdha)
    # and 06-18 (Dagdha is gone, but Rikta + Sarvartha Siddhi might mix);
    # let's just verify dropped_days exists and at least the Dagdha day
    # appears for wedding activity.
    result = json.loads(tool_find_muhurta('2026-06-16', 5, 'wedding', 'Hyderabad'))
    assert 'dropped_days' in result
    # The 17th has Dagdha Yoga — must show up in dropped_days for wedding
    dropped_dates = {dd['date'] for dd in result['dropped_days']}
    assert '2026-06-17' in dropped_dates, f'expected Dagdha day in dropped_days; got {result["dropped_days"]}'
    # Each dropped entry has a date and a reason
    for dd in result['dropped_days']:
        assert 'date' in dd and 'reason' in dd
        assert isinstance(dd['reason'], str) and dd['reason']


def test_mcp_find_muhurta_emits_tier_on_each_slot():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta('2026-06-15', 5, 'any', 'Hyderabad'))
    assert result['slots']
    for s in result['slots']:
        assert s['tier'] in ('Excellent', 'Good', 'Fair', 'Avoid')


def test_mcp_find_muhurta_exposes_janma_rasis_janma_lagnas_chandra_mode():
    """The MCP-exposed find_muhurta (server.py) must thread all per-person
    inputs that the underlying tool_find_muhurta (tools.py) accepts.

    Regression guard: until this fix, MCP clients could pass only
    janma_nakshatras — the Chandrabalam (janma_rasis), Lagna Shuddhi
    (janma_lagnas), and chandra_mode parameters that tool_find_muhurta
    already supported were unreachable from any MCP client.
    """
    import json
    from telugu_panchangam.mcp.server import find_muhurta
    # FastMCP @mcp.tool() wraps the function — original is on .fn
    fn = getattr(find_muhurta, 'fn', find_muhurta)
    result = json.loads(fn(
        '2026-06-15',
        days=3,
        activity='any',
        city='Hyderabad',
        janma_nakshatras=['Ashvini', 'Bharani'],
        janma_rasis=['Mesha', None],         # second person's rashi unknown
        janma_lagnas=[None, 'Karka'],        # first person's lagna unknown
        chandra_mode='puja_ok',
    ))
    assert 'error' not in result, f'unexpected error: {result.get("error")}'
    assert 'slots' in result
    assert result.get('chandra_mode') == 'puja_ok'


def test_unknown_tithi_name_does_not_explode():
    # Robustness: tithi_family is wrapped in try/except inside day_slots,
    # so an unknown tithi name silently skips tithi-class scoring.
    from telugu_panchangam.personal.tithi_class import tithi_family, is_rikta
    with pytest.raises(ValueError):
        tithi_family('Unknown Mystery Tithi')

    # is_rikta swallows the ValueError and returns False
    assert is_rikta('Unknown Mystery Tithi') is False


def test_is_rikta_unknown_tithi_returns_false():
    from telugu_panchangam.personal.tithi_class import is_rikta
    assert is_rikta('InvalidTithi') is False


# --- B1-Heavy: per-slot precision via engine.facts_at() ---

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


# ---------------------------------------------------------------------------
# Tithi avoid scoring (score_tithi_class — avoid_tithi_class param)
# ---------------------------------------------------------------------------

def test_score_tithi_class_avoid_gives_minus_one():
    from telugu_panchangam.personal.slot_scorers import score_tithi_class
    # A hypothetical activity may still avoid a whole Tithi family.
    bonus, day_r, act_r, fam = score_tithi_class(
        'Shukla Tritiya', 'Purna', 'Wedding (Vivaha)',
        avoid_tithi_class=['Jaya'])
    assert bonus == -1
    assert day_r is None
    assert act_r is not None and 'inauspicious' in act_r and 'Jaya' in act_r
    assert fam == 'Jaya'


def test_score_tithi_class_avoid_no_effect_on_non_matching():
    from telugu_panchangam.personal.slot_scorers import score_tithi_class
    # Bhadra tithi not in avoid list → neutral
    bonus, _, act_r, _ = score_tithi_class(
        'Shukla Dwitiya', 'Purna', 'Wedding (Vivaha)',
        avoid_tithi_class=['Jaya'])
    assert bonus == 0
    assert act_r is None


def test_score_tithi_class_prefer_wins_over_neutral_avoid_list():
    from telugu_panchangam.personal.slot_scorers import score_tithi_class
    # Purna tithi matches prefer_tithi_class — +1 even if avoid list is empty
    bonus, _, act_r, fam = score_tithi_class(
        'Shukla Panchami', 'Purna', 'Wedding (Vivaha)',
        avoid_tithi_class=['Jaya'])
    assert bonus == 1
    assert act_r is not None and 'favoured' in act_r


def test_score_tithi_class_rikta_unaffected_by_avoid():
    from telugu_panchangam.personal.slot_scorers import score_tithi_class
    # Rikta path still returns -2 regardless of avoid list contents
    bonus, day_r, _, fam = score_tithi_class(
        'Shukla Chaturthi', 'Purna', 'Wedding (Vivaha)',
        avoid_tithi_class=['Jaya', 'Rikta'])
    assert bonus == -2
    assert fam == 'Rikta'


def test_shukla_tritiya_admitted_for_wedding_without_jaya_penalty():
    from telugu_panchangam.personal.tithi_class import tithi_family
    day = _day(2026, 4, 20)
    assert tithi_family(day.tithi.name) == 'Jaya', f'fixture: expected Jaya tithi, got {day.tithi.name}'
    slots = day_slots(day, activity='wedding')
    assert slots
    for s in slots:
        act_reasons = s['reason_groups']['activity_match']
        assert not any('Jaya' in r for r in act_reasons)


def test_litigation_alias_matches_court_results():
    day = _day(2026, 4, 20)
    assert day_slots(day, activity='litigation') == \
        day_slots(day, activity='court')


def test_tithi_class_scorer_still_supports_preferred_class():
    from telugu_panchangam.personal.slot_scorers import score_tithi_class
    bonus, _, act_r, _ = score_tithi_class(
        'Shukla Tritiya', 'Jaya', 'Example activity',
        avoid_tithi_class=['Purna'])
    assert bonus == 1
    assert act_r is not None and 'favoured' in act_r


def test_engine_kwarg_does_not_break_mcp_path():
    """Through the MCP tool — verify it still produces results."""
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta('2026-06-15', 5, 'any', 'Hyderabad'))
    assert result['slots']
    # Score is the sum of its (+n)/(-n) reasons
    for s in result['slots']:
        bonuses = []
        for r in s['reasons']:
            # Match trailing (+N) or (-N)
            import re
            m = re.search(r'\(([+-]\d+)\)\s*$', r)
            if m:
                bonuses.append(int(m.group(1)))
        # Reasons may include the constant 'clear of all inauspicious windows'
        # and karana-avoided lines that don't have a number — those are fine.
        # We just verify the sum matches the score.
        assert sum(bonuses) == s['score'], \
            f'reasons {bonuses} should sum to {s["score"]} but got {sum(bonuses)}'


def test_invalid_chandra_mode_raises():
    with pytest.raises(ValueError):
        day_slots(_day(2026, 6, 17), chandra_mode='bogus')


def test_misaligned_rasis_raise():
    with pytest.raises(ValueError):
        day_slots(_day(2026, 6, 17),
                  janma_nakshatras=['Pushya'],
                  janma_rasis=['Karka', 'Mesha'])


# --- MCP ---

def test_mcp_find_muhurta():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta('2026-06-15', 5, 'any', 'Hyderabad'))
    assert result['slots'], 'expected at least one slot in 5 days'
    top = result['slots'][0]
    assert {'date', 'vaaram', 'start', 'end', 'score', 'reasons'} <= set(top)
    # Sorted by (tier desc, score desc) — tier takes priority, so a lower-score
    # slot in a higher tier may appear before a higher-score slot capped to a
    # lower tier by day_dosha.  Check the actual sort key, not score alone.
    from telugu_panchangam.personal.muhurta import TIER_NAMES
    sort_key = lambda s: (-TIER_NAMES.index(s['tier']), -s['score'])
    assert result['slots'] == sorted(result['slots'], key=sort_key)
    assert 'disclaimer' in result
    assert result['chandra_mode'] == 'stars'


def test_mcp_find_muhurta_with_chandra_mode():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta(
        '2026-06-15', 5, 'any', 'Hyderabad',
        janma_nakshatras=['Pushya'], janma_rasis=['Karka'],
        chandra_mode='strict'))
    # Karka has Moon at 12 from Karka on Mithuna days — should drop those.
    # We don't assert empty (depends on the whole window), but result must
    # be a list and chandra_mode must round-trip.
    assert result['chandra_mode'] == 'strict'
    assert isinstance(result['slots'], list)


def test_mcp_find_muhurta_validates():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    assert 'error' in json.loads(tool_find_muhurta('2026-06-15', 20, 'any', 'Hyderabad'))
    assert 'error' in json.loads(tool_find_muhurta('2026-06-15', 5, 'not-a-real-activity', 'Hyderabad'))
    assert 'error' in json.loads(tool_find_muhurta(
        '2026-06-15', 5, 'any', 'Hyderabad', chandra_mode='bogus'))
    # rashis without aligned nakshatras
    assert 'error' in json.loads(tool_find_muhurta(
        '2026-06-15', 5, 'any', 'Hyderabad', janma_rasis=['Karka']))


# ---------------------------------------------------------------------------
# Night slots
# ---------------------------------------------------------------------------

def _two_days(y, m, d):
    """Return (day, next_day) PanchangamDay pair for night_slots()."""
    from datetime import timedelta
    d0 = date(y, m, d)
    return ENGINE.calculate(d0, HYD), ENGINE.calculate(d0 + timedelta(days=1), HYD)


def test_night_slots_timing_between_sunset_and_next_sunrise():
    from telugu_panchangam.personal.muhurta import night_slots
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    assert slots, 'expected night slots on a clean day'
    for s in slots:
        assert s['start'] >= day.sunset, 'slot must start at or after sunset'
        assert s['end'] <= next_day.sunrise, 'slot must end at or before next sunrise'


def test_night_slots_are_named_night_muhurtas():
    from telugu_panchangam.personal.muhurta import night_slots
    from telugu_panchangam.muhurtas import NIGHT_MUHURTAS
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
    from telugu_panchangam.personal.muhurta import night_slots, TIER_NAMES
    day, next_day = _two_days(2026, 6, 16)
    slots = night_slots(day, next_day, engine=ENGINE)
    assert slots
    for i in range(len(slots) - 1):
        a, b = slots[i], slots[i + 1]
        rank_a = TIER_NAMES.index(a['tier'])
        rank_b = TIER_NAMES.index(b['tier'])
        assert rank_a > rank_b or (rank_a == rank_b and a['score'] >= b['score'])


def test_night_slots_eclipse_returns_empty():
    from datetime import timedelta
    from telugu_panchangam.personal.muhurta import night_slots
    from telugu_panchangam.models.panchangam_day import EclipseInfo
    day, next_day = _two_days(2026, 6, 16)
    from dataclasses import replace
    day_with_eclipse = replace(day, eclipse=EclipseInfo(
        kind='Solar', subtype='Total', start=day.sunrise,
        end=day.sunset, visible=False, sutak_start=day.sunrise, sutak_end=day.sunset))
    assert night_slots(day_with_eclipse, next_day) == []


def test_mcp_find_muhurta_include_night():
    import json
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    result = json.loads(tool_find_muhurta(
        '2026-06-15', 3, 'any', 'Hyderabad', include_night=True))
    assert 'slots' in result
    assert result['slots'], 'expected at least one slot over 3 days with night included'
    # Verify some night slots exist (start time after ~18:00 local)
    # We just check that all slots have the required keys.
    for s in result['slots']:
        assert {'date', 'vaaram', 'start', 'end', 'score', 'reasons'} <= set(s)


# ---------------------------------------------------------------------------
# Phase 2 — 48-minute classical muhurta windows
# ---------------------------------------------------------------------------

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


def test_night_slots_are_at_most_48_minutes():
    """Night slot windows are also ≤ 48 minutes."""
    from datetime import timedelta
    from telugu_panchangam.personal.muhurta import night_slots, MUHURTA_MINUTES
    limit = timedelta(minutes=MUHURTA_MINUTES)
    for date_args in [(2026, 6, 16), (2026, 6, 25)]:
        day, next_day = _two_days(*date_args)
        for s in night_slots(day, next_day, engine=ENGINE):
            duration = s['end'] - s['start']
            assert duration <= limit, (
                f"{date_args}: night slot {s['start']}–{s['end']} is {duration}"
            )


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
