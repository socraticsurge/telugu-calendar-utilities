"""Versioned interpretation conventions used by election-chart policies."""

from __future__ import annotations

ELECTION_CHART_CONVENTION_SCHEMA_VERSION = 2

ELECTION_CHART_CONVENTIONS: dict[str, dict] = {
    'whole-sign-physical-occupation-v1': {
        'label': 'Whole Sign physical-occupation convention v1',
        'formula': (
            'house = 1 + ((graha Rasi index - local Lagna Rasi index + 12) '
            'mod 12). “Occupies Lagna” means physical occupation of house 1; '
            'it does not mean aspect, lordship, Shadbala or Lagna strength.'
        ),
        'method_claims': [
            'election_chart.whole_sign_house_policy_v1',
        ],
    },
    'annaprasana-natural-malefic-lagna-v1': {
        'label': 'Annaprasana natural-malefic Lagna convention v1',
        'formula': (
            'Reject Surya, Kuja, Shani, mean Rahu or mean Ketu in Whole Sign '
            'house 1. When Chandra occupies house 1, let E = (Chandra '
            'longitude - Surya longitude) mod 360 degrees: 0 < E < 180 is '
            'waxing and does not fail; 180 < E < 360 is waning and fails. '
            'Return unknown within ±0.02 degrees of 0 or 180. Budha joined '
            'to a natural malefic is represented by same-sign occupation; '
            'the accompanying malefic already controls this prohibition.'
        ),
        'method_claims': [
            'election_chart.natural_malefics.bphs_3_11_modern_witness',
            'election_chart.whole_sign_house_policy_v1',
            'election_chart.mean_node_policy_v1',
            'election_chart.budha_same_sign_association_policy_v1',
            'election_chart.raman_180_degree_paksha_policy_v1',
            'election_chart.lunar_phase_boundary_guard_policy_v1',
            'election_chart.annaprasana_fail_closed_aggregation_policy_v1',
        ],
    },
    'phaladeepika-well-placed-v1': {
        'label': 'Phaladeepika well-placed convention v1',
        'formula': (
            'Outside houses 6, 8 and 12; outside an enemy Rasi; and outside '
            'debilitation Rasi or Navamsa. Chandra must also clear Surya by '
            'more than the disclosed 12-degree v1 solar-ray threshold.'
        ),
        'method_claims': [
            'election_chart.well_placed.phaladeepika_2_36',
            'election_chart.dignity.phaladeepika_1_6',
            'election_chart.relationships.phaladeepika_2_21_22',
            'election_chart.navamsa.bphs_6_12',
            'election_chart.chandra_solar_clearance_policy_v1',
            'election_chart.gold_transition_envelope_v1',
        ],
    },
    'phaladeepika-full-graha-drishti-v1': {
        'label': 'Phaladeepika full Graha Drishti convention v1',
        'formula': (
            'Every classical graha fully aspects the 7th; Kuja also the 4th '
            'and 8th, Guru the 5th and 9th, and Shani the 3rd and 10th. '
            'Rahu, Ketu and partial aspects are excluded.'
        ),
        'method_claims': [
            'election_chart.full_graha_drishti.phaladeepika_2_23',
            'election_chart.gold_transition_envelope_v1',
        ],
    },
}
