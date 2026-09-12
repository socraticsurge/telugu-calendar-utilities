"""Versioned interpretation conventions used by election-chart policies."""

from __future__ import annotations

ELECTION_CHART_CONVENTION_SCHEMA_VERSION = 4

ELECTION_CHART_CONVENTIONS: dict[str, dict] = {
    'court-canonical-local-d1-sidecar-d9-v1': {
        'label': 'Court canonical D1-or-guarded-D9 convention v1',
        'formula': (
            'Pass when the canonical local Drik/Lahiri D1 Lagna Rasi is '
            'Mesha, or when the sidecar Lagna Rasi agrees with that canonical '
            'D1 and its guarded BPHS-modality Navamsa is Mesha.'
        ),
        'method_claims': [
            'election_chart.whole_sign_house_policy_v1',
            'election_chart.navamsa.bphs_6_12',
        ],
    },
    'court-peace-benefic-subject-continuity-v1': {
        'label': 'Court peace benefic subject-continuity convention v1',
        'formula': (
            'Pass when a resolved natural benefic occupies Whole Sign house '
            '1, 4, 7 or 10, or when a resolved natural benefic occupies an '
            'odd Rasi and receives a full classical aspect from another '
            'resolved natural benefic. The result is non-ranking information.'
        ),
        'male_rasis': [
            'Mesha', 'Mithuna', 'Simha', 'Tula', 'Dhanu', 'Kumbha',
        ],
        'aspect_direction': 'benefic_receiver_from_benefic_source',
        'method_claims': [
            'election_chart.court_peace_pattern_policy_v1',
        ],
    },
    'court-lagna-sixth-lord-whole-sign-opposition-v1': {
        'label': 'Court Lagna-sixth-lord Whole Sign opposition convention v1',
        'formula': (
            'Derive the Lagna Rasi and sixth-house Rasi lords from the '
            'classical seven-graha ownership table, then require '
            'min(abs(R1 - R2), 12 - abs(R1 - R2)) = 6. Rahu and Ketu are '
            'never sign lords. This is a binary, score-neutral Court '
            'preference rather than a source-supplied numeric formula.'
        ),
        'maximum_shortest_distance': 6,
        'house_system': 'whole_sign',
        'nodes_are_lords': False,
        'method_claims': [
            'election_chart.court_lagna_sixth_lord_separation_policy_v1',
        ],
    },
    'phaladeepika-natural-graha-nature-whole-sign-v1': {
        'label': 'Phaladeepika natural-graha nature Whole Sign convention v1',
        'formula': (
            'Surya, Kuja, Shani, Rahu and Ketu are fixed malefics; Guru and '
            'Shukra are fixed benefics. Chandra is benefic for normalized '
            'Surya-Chandra elongation 0.02° < E < 179.98°, malefic for '
            '180.02° < E < 359.98°, and unknown inside the inclusive '
            '0.02° guards around 0°/180°/360° after ten-decimal, '
            'non-negative round-half-up quantization. Budha is malefic when '
            'a resolved malefic shares its sidereal Rasi, unknown when only '
            'phase-unknown Chandra can decide, and otherwise benefic.'
        ),
        'fixed_malefics': ['Surya', 'Kuja', 'Shani', 'Rahu', 'Ketu'],
        'fixed_benefics': ['Guru', 'Shukra'],
        'chandra_phase_guard_degrees': 0.02,
        'phase_quantization_decimal_places': 10,
        'phase_quantization_rounding': 'half_up_nonnegative',
        'budha_association': 'same_sidereal_rashi',
        'house_system': 'whole_sign',
        'method_claims': [
            'election_chart.natural_graha_nature.phaladeepika_2_27',
            'election_chart.natural_malefics.bphs_3_11_modern_witness',
            'election_chart.budha_same_sign_association_policy_v1',
            'election_chart.raman_180_degree_paksha_policy_v1',
            'election_chart.lunar_phase_boundary_guard_policy_v1',
            'election_chart.mean_node_policy_v1',
        ],
    },
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
