"""Muhurta activity rules contracts; assertions preserved from the original suite."""


import pytest

from telugu_panchangam.personal.muhurta import day_slots
from tests.muhurta_finder_support import ENGINE, _day


def test_all_36_activities_callable():
    from telugu_panchangam.personal.activity_rules import ACTIVITY_ALIASES
    from telugu_panchangam.personal.muhurta import ACTIVITIES, ACTIVITY_RULES
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
                     'engagement', 'bhumi_puja', 'vidyarambha'):
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


def test_tithi_family_classification():
    from telugu_panchangam.personal.tithi_class import (
        FAMILIES,
        tithi_family,
        tithi_number,
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
    from collections import Counter

    from telugu_panchangam.personal.tithi_class import TITHI_NUMBER_FAMILY
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


@pytest.fixture
def vyaghata_windows():
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
    return in_window, out_window


def test_partial_avoid_nitya_dosha_window(vyaghata_windows):
    in_window, _ = vyaghata_windows
    if in_window:
        assert any('Vyaghata yoga dosha-window' in r
                   for s in in_window for r in s['reasons'])


def test_outside_nitya_dosha_window_has_no_penalty(vyaghata_windows):
    _, out_window = vyaghata_windows
    if out_window:
        # Outside the dosha-window — no penalty reason
        for s in out_window:
            assert not any('Vyaghata yoga dosha-window' in r for r in s['reasons'])


def test_neutral_nitya_yoga_no_score():
    """Vajra and Variyan are explicitly neutral — no bonus, no penalty."""
    from telugu_panchangam.personal.nitya_yoga import nitya_disposition
    assert nitya_disposition('Vajra') == 'neutral'
    assert nitya_disposition('Variyan') == 'neutral'


def test_unknown_tithi_name_does_not_explode():
    # Robustness: tithi_family is wrapped in try/except inside day_slots,
    # so an unknown tithi name silently skips tithi-class scoring.
    from telugu_panchangam.personal.tithi_class import is_rikta, tithi_family
    with pytest.raises(ValueError):
        tithi_family('Unknown Mystery Tithi')

    # is_rikta swallows the ValueError and returns False
    assert is_rikta('Unknown Mystery Tithi') is False


def test_is_rikta_unknown_tithi_returns_false():
    from telugu_panchangam.personal.tithi_class import is_rikta
    assert is_rikta('InvalidTithi') is False


def test_score_tithi_class_avoid_gives_minus_one():
    from telugu_panchangam.personal.slot_scorers import score_tithi_class
    # A hypothetical activity may still avoid a whole Tithi family.
    bonus, day_r, act_r, fam = score_tithi_class(
        'Shukla Tritiya', 'Purna', 'Wedding (Vivaha)',
        avoid_tithi_class=['Jaya'])
    assert bonus == -1
    assert day_r is None
    assert act_r is not None
    assert 'inauspicious' in act_r
    assert 'Jaya' in act_r
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
    assert act_r is not None
    assert 'favoured' in act_r


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
    assert act_r is not None
    assert 'favoured' in act_r
