"""Coverage and freshness tests for the browser activity-check contract."""

import json
from pathlib import Path

from telugu_panchangam.personal.activity_catalog import BROWSER_ACTIVITIES
from telugu_panchangam.personal.activity_check_contract import (
    ACTIVITY_CHECK_SPECS,
    CANONICAL_VARAS,
    DETERMINISTIC_PANCHANGAM_FIELDS,
    MANUAL_CHECK_CLASS,
    MANUAL_CHECK_DISPLAY_SECTIONS,
    build_activity_check_contract,
)
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.election_chart_rules import (
    ELECTION_CHART_RULES,
)
from telugu_panchangam.personal.personal_election import (
    PERSONAL_ELECTION_RULES,
)

ROOT = Path(__file__).parents[1]
GENERATED = ROOT / 'src' / 'data' / 'activity-rules.generated.json'


def _rule_ids(rules):
    return tuple(
        rule['id'] if isinstance(rule, dict) else rule[0]
        for rule in rules
    )


def test_every_browser_activity_and_check_has_explicit_classification():
    contract = build_activity_check_contract()
    assert tuple(ACTIVITY_CHECK_SPECS) == BROWSER_ACTIVITIES
    assert tuple(contract['activities']) == BROWSER_ACTIVITIES

    seen_ids = set()
    for activity in BROWSER_ACTIVITIES:
        entry = contract['activities'][activity]
        source_checks = ACTIVITY_RULES[activity].get('manual_checks', ())
        rows_by_source = {index: [] for index in range(len(source_checks))}
        for row in entry['manual_checks']:
            assert row['id'] not in seen_ids
            seen_ids.add(row['id'])
            assert row['class'] == MANUAL_CHECK_CLASS
            assert row['display_section'] in MANUAL_CHECK_DISPLAY_SECTIONS
            assert row['text'].strip()
            rows_by_source[row['source_index']].append(row)

        assert all(rows_by_source.values())
        for index, source_text in enumerate(source_checks):
            assert {
                row['source_text'] for row in rows_by_source[index]
            } == {source_text}


def test_rule_inventories_cover_the_python_sources_exactly():
    contract = build_activity_check_contract()['activities']
    for activity in BROWSER_ACTIVITIES:
        expected_fields = [
            field for field in DETERMINISTIC_PANCHANGAM_FIELDS
            if field in ACTIVITY_RULES[activity]
        ]
        assert contract[activity][
            'deterministic_panchangam_fields'] == expected_fields
        assert tuple(contract[activity]['personal_rule_ids']) == _rule_ids(
            PERSONAL_ELECTION_RULES.get(activity, ()))
        assert tuple(
            contract[activity]['election_chart_rule_ids']) == _rule_ids(
                ELECTION_CHART_RULES.get(activity, ()))


def test_generated_check_contract_is_fresh():
    generated = json.loads(GENERATED.read_text(encoding='utf-8'))
    assert generated['check_contract'] == build_activity_check_contract()


def test_mixed_and_regex_ambiguous_checks_have_intentional_sections():
    activities = build_activity_check_contract()['activities']

    owner_ritual = [
        row for row in activities['gruhapravesha']['manual_checks']
        if row['source_index'] == 3
    ]
    assert [row['display_section'] for row in owner_ritual] == [
        'chart', 'information']
    assert 'Bhootabali' not in owner_ritual[0]['text']
    assert 'Bhootabali' in owner_ritual[1]['text']

    # These sentences used to be vulnerable to substring-based inference
    # (for example, "permits" accidentally matching "permit").
    assert activities['gruhapravesha']['manual_checks'][2][
        'display_section'] == 'chart'
    assert activities['court']['manual_checks'][4][
        'display_section'] == 'chart'
    assert activities['purchase']['manual_checks'][2][
        'display_section'] == 'information'


def test_manual_weekday_applicability_is_explicit_and_narrow():
    activities = build_activity_check_contract()['activities']

    weekday_words = (
        'Sunday', 'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday',
    )
    weekday_mentions = {
        (activity, index)
        for activity, rule in ACTIVITY_RULES.items()
        for index, text in enumerate(rule.get('manual_checks', ()))
        if any(day in text for day in weekday_words)
    }
    assert weekday_mentions == {
        ('purchase', 1),
        ('business_inventory_purchase', 1),
        ('lending_money', 4),
        ('wedding', 5),
        ('upanayana', 1),
        ('gruhapravesha', 5),
        ('home_repair', 1),
    }

    assert activities['business_inventory_purchase']['manual_checks'][1][
        'applicable_varas'] == ['Shanivaram']
    assert activities['upanayana']['manual_checks'][1][
        'applicable_varas'] == ['Budhavaram']
    assert activities['home_repair']['manual_checks'][1][
        'applicable_varas'] == ['Somavaram', 'Shukravaram']

    # These are complete chart instructions or methodology notes. Mentioning a
    # weekday in their prose must not accidentally make the whole row
    # conditional on that weekday.
    always_visible = (
        ('purchase', 1),
        ('lending_money', 4),
        ('wedding', 5),
        ('gruhapravesha', 5),
    )
    for activity, source_index in always_visible:
        row = activities[activity]['manual_checks'][source_index]
        assert 'applicable_varas' not in row

    for entry in activities.values():
        for row in entry['manual_checks']:
            assert set(row.get('applicable_varas', ())).issubset(
                CANONICAL_VARAS)


def test_safety_override_rows_have_explicit_semantic_purpose():
    activities = build_activity_check_contract()['activities']
    marked = [
        (activity, row)
        for activity, entry in activities.items()
        for row in entry['manual_checks']
        if row.get('purpose') == 'safety_override'
    ]

    assert [(activity, row['source_index']) for activity, row in marked] == [
        ('court', 5),
        ('surgery', 0),
    ]
    assert all(row['display_section'] == 'practical' for _, row in marked)
