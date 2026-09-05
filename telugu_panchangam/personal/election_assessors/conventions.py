"""Versioned interpretation conventions used by election-chart policies."""

from __future__ import annotations

ELECTION_CHART_CONVENTION_SCHEMA_VERSION = 2

ELECTION_CHART_CONVENTIONS: dict[str, dict] = {
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
    'vidyarambha-benefic-trio-co-location-v1': {
        'label': 'Aksharabhyasa benefic-trio co-location convention v1',
        'formula': (
            'H(Budha) = 9 AND H(Shukra) = 9 AND H(Guru) = 9. '
            'All three named grahas must occupy the ninth house in every '
            'sampled chart state; one or two matching placements do not '
            'satisfy the preference.'
        ),
        'method_claims': [
            'election_chart.vidyarambha_co_location_policy_v1',
            'election_chart.vidyarambha_reject_precedence_policy_v1',
        ],
    },
}
