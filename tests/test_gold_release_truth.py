"""Release-facing Gold copy must stay inside the implemented scope."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_gold_reference_pages_limit_completion_to_event_specific_clauses():
    profile = _read('docs/reference/28-gold-jewelry-profile.md')
    method = _read('docs/reference/54-muhurtam-election-chart-screening.md')

    for raw_document in (profile, method):
        document = ' '.join(raw_document.split())
        assert 'event-specific' in document
        assert 'general election-chart baseline' in document
        assert '#284' in document
        assert 'raw score' in document
        assert 'maximum' in document
        assert 'Good' in document
        assert 'both counts' in document

    assert 'After a complete, valid Drik screen, the Gold chart remainder is empty' \
        not in profile
    assert 'No chart remainder after a complete, valid Drik screen under Gold v1' \
        not in method


def test_machine_readable_record_generates_the_same_gold_scope_contract():
    registry = json.loads(_read('docs/reference/computations.json'))
    record = next(
        item for item in registry['computations']
        if item['id'] == 'personal.muhurta-slot-ranking'
    )
    release_text = ' '.join([
        record['provenance']['note'],
        *record['limitations'],
        *record['method']['notes'],
        *record['method']['worked_examples'][-1]['result'],
    ])

    assert 'four event-specific' in release_text
    assert 'general election-chart baseline' in release_text
    assert 'unchanged raw score' in release_text
    assert 'maximum rating' in release_text
    assert 'both dispositions' in release_text
    assert 'exact overlap' in release_text
    assert 'election_chart.gold_transition_envelope_v1' in (
        record['provenance']['claim_ids'])
    assert 'partially_verified' in record['provenance'][
        'verification_states'
    ]


def test_research_inventory_is_explicitly_a_dated_pre_gold_baseline():
    research = _read('docs/research/election-chart-automation/report-source.md')

    assert 'Pre-Gold program baseline (captured 2026-08-29)' in research
    assert 'At this pre-Gold snapshot' in research
    assert 'The current contract contains 23 deterministic predicates' \
        not in research


def test_current_reference_pages_publish_the_32_rule_successor_contract():
    features = ' '.join(
        _read('docs/reference/04-user-facing-features.md').split()
    )
    flow = ' '.join(
        _read('docs/reference/05-data-flow-and-muhurta.md').split()
    )

    assert 'one of 32 deterministic chart predicates' in features
    assert 'one of 30 deterministic chart predicates' not in features
    assert 'one of 29 deterministic chart predicates' not in features
    assert 'one of 28 deterministic chart predicates' not in features
    assert 'one of 27 deterministic chart predicates' not in features
    assert 'one of 23 deterministic chart predicates' not in features
    assert '15 source-backed activity profiles' in flow
    assert 'complete 32-rule matrix' in flow
    assert 'complete 30-rule matrix' not in flow
    assert 'complete 29-rule matrix' not in flow
    assert 'complete 28-rule matrix' not in flow
    assert 'complete 27-rule matrix' not in flow
    assert 'complete 23-rule matrix' not in flow
    for document in (features, flow):
        assert 'Gold / jewelry purchase' in document
        assert '`qualify`' in document
        assert 'general election-chart baseline' in document
    assert 'Annaprasana' in features
    assert 'five mandatory prohibitions' in features
    assert 'tie-break evidence only' in features
    assert 'Karnavedha' in features
    assert 'half-open local daylight interval' in features
    assert 'vacant-8th' in features


def test_activity_coverage_publishes_scoped_aksharabhyasa_truth():
    coverage = _read('docs/reference/16-activity-provenance-coverage.md')
    normalized = ' '.join(coverage.split())

    assert (
        '| `vidyarambha` | Aksharabhyasa (First-letter writing) | '
        '`muhurta.vidyarambha` | Verified scoped Chapter VIII profile; '
        'two deterministic clauses are Drik browser post-screened, while '
        'the overall assessor remains partial/provisional |'
    ) in normalized
    assert 'exact 32-predicate matrix' in normalized
    assert 'exact 29-predicate matrix' not in normalized
    assert 'Education commencement (Vidyarambha)' not in coverage
    assert 'exact 27-predicate matrix' not in coverage


def test_gold_docs_distinguish_synthetic_and_actual_gateway_evidence():
    profile = _read('docs/reference/28-gold-jewelry-profile.md')
    method = _read('docs/reference/54-muhurtam-election-chart-screening.md')
    research = _read('docs/research/election-chart-automation/report-source.md')

    for document in (profile, method, research):
        assert 'election_chart_gold_oracle.json' in document
        assert 'election_chart_gold_gateway_oracle.json' in document
        assert 'Hyderabad' in document
        assert 'Sydney' in document
        assert '4106f09708a154f1c2401880ebe8f9c0b9162eb5' in document
        assert 'c84fd856b17120c80e1bb7e455246a0ec8e429ea' in document
