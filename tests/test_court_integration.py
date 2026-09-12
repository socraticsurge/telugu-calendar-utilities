"""The five Raman Court clauses operate as one bounded, alias-safe assessor."""

from telugu_panchangam.personal.election_chart import (
    evaluate_election_chart,
    evaluate_election_snapshots,
)
from telugu_panchangam.personal.election_chart_rules import (
    ELECTION_CHART_COMPLETE_ASSESSORS,
    ELECTION_CHART_MANUAL_REMAINDERS,
    ELECTION_CHART_RULES,
)

PLANETS = (
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
    'Shukra', 'Shani', 'Rahu', 'Ketu',
)

POSITIONS = {
    'Surya': ('Karka', 10.0, 4),
    'Chandra': ('Tula', 20.0, 7),
    'Kuja': ('Mesha', 12.0, 1),
    'Budha': ('Tula', 10.0, 7),
    'Guru': ('Mesha', 18.0, 1),
    'Shukra': ('Vrishabha', 15.0, 2),
    'Shani': ('Makara', 8.0, 10),
    'Rahu': ('Kumbha', 9.0, 11),
    'Ketu': ('Simha', 9.0, 5),
}


def _chart(*, instant='2026-09-08T05:30:00.000Z', **overrides):
    planets = []
    for name in PLANETS:
        rashi, degree, house = POSITIONS[name]
        values = {
            'name': name,
            'rashi': rashi,
            'degree': degree,
            'house': house,
            'retrograde': name in {'Rahu', 'Ketu'},
        }
        values.update(overrides.get(name, {}))
        planets.append(values)
    return {
        'instant': instant,
        'lagna': {'rashi': 'Mesha', 'degree': 12.5},
        'planets': planets,
    }


def _coverage(**overrides):
    coverage = {
        'local_lagna_transitions_complete': True,
        'lagna_navamsa_transitions_complete': True,
        'guru_rasi_transitions_complete': True,
        'graha_rasi_transitions_complete': True,
        'chandra_phase_transitions_complete': True,
        'budha_association_transitions_complete': True,
        'lagna_lord_rasi_transitions_complete': True,
        'sixth_lord_rasi_transitions_complete': True,
        'full_aspect_transitions_complete': True,
        'budget_exhausted': False,
    }
    coverage.update(overrides)
    return coverage


def _outcome(result, rule_id):
    return next(item for item in result['outcomes'] if item['rule_id'] == rule_id)


def test_court_registers_exactly_five_complete_default_rules():
    rules = ELECTION_CHART_RULES['court']

    assert [rule['id'] for rule in rules] == [
        'court.mesha-lagna-or-navamsa',
        'court.guru-trikona',
        'court.house-6-without-natural-malefic',
        'court.lagna-sixth-lords-max-separated',
        'court.peace-benefic-pattern',
    ]
    assert [rule['effect'] for rule in rules] == [
        'reject', 'prefer', 'reject', 'prefer', 'inform',
    ]
    assert all(rule['source_claim'] == 'muhurta.court.filing_lawsuit' for rule in rules)
    assert ELECTION_CHART_MANUAL_REMAINDERS['court'] == ()
    assert 'court' in ELECTION_CHART_COMPLETE_ASSESSORS
    assert all('chintamani' not in rule['id'] for rule in rules)


def test_court_reject_preference_and_information_effects_are_distinct():
    result = evaluate_election_chart(
        'court', _chart(), authoritative_lagna_rashi='Mesha'
    )

    assert result['rejected'] is False
    assert result['needs_review'] is False
    assert result['preference_passes'] == 2
    assert [item['status'] for item in result['outcomes']] == [
        'pass', 'pass', 'pass', 'pass', 'pass',
    ]

    rejected = evaluate_election_chart(
        'court',
        _chart(Shani={'rashi': 'Kanya', 'house': 6}),
        authoritative_lagna_rashi='Mesha',
    )
    assert rejected['rejected'] is True
    assert _outcome(
        rejected, 'court.house-6-without-natural-malefic'
    )['status'] == 'fail'
    assert rejected['preference_passes'] == 2

    preference_miss = evaluate_election_chart(
        'court',
        _chart(
            Guru={'rashi': 'Mithuna', 'house': 3},
            Budha={'rashi': 'Kanya', 'house': 6},
        ),
        authoritative_lagna_rashi='Mesha',
    )
    assert preference_miss['rejected'] is False
    assert preference_miss['preference_passes'] == 0

    peace = _outcome(result, 'court.peace-benefic-pattern')
    assert peace['effect'] == 'inform'
    assert peace['status'] == 'pass'
    assert result['preference_passes'] == 2


def test_litigation_is_result_identical_to_court_and_unknown_never_passes():
    chart = _chart()
    options = {'authoritative_lagna_rashi': 'Mesha'}
    assert evaluate_election_chart('litigation', chart, **options) == (
        evaluate_election_chart('court', chart, **options)
    )

    unresolved = evaluate_election_chart('court', chart)
    assert _outcome(
        unresolved, 'court.mesha-lagna-or-navamsa'
    )['status'] == 'unknown'
    assert unresolved['rejected'] is False
    assert unresolved['needs_review'] is True


def test_court_window_preserves_interior_reject_and_incomplete_coverage():
    passing = _chart(instant='2026-09-08T05:30:00.000Z')
    failing = _chart(
        instant='2026-09-08T05:35:00.000Z',
        Shani={'rashi': 'Kanya', 'house': 6},
    )
    end = _chart(instant='2026-09-08T05:40:00.000Z')
    result = evaluate_election_snapshots(
        'court',
        [passing, failing, end],
        authoritative_lagna_rashis=['Mesha', 'Mesha', 'Mesha'],
        court_transition_coverage=_coverage(),
    )
    assert result['rejected'] is True
    assert _outcome(
        result, 'court.house-6-without-natural-malefic'
    )['status'] == 'fail'

    incomplete = evaluate_election_snapshots(
        'court',
        [passing, end],
        authoritative_lagna_rashis=['Mesha', 'Mesha'],
        court_transition_coverage=_coverage(
            lagna_navamsa_transitions_complete=False,
            guru_rasi_transitions_complete=False,
        ),
    )
    assert incomplete['rejected'] is False
    assert incomplete['needs_review'] is True
    assert _outcome(
        incomplete, 'court.mesha-lagna-or-navamsa'
    )['status'] == 'unknown'
    assert _outcome(incomplete, 'court.guru-trikona')['status'] == 'unknown'
