import { describe, expect, test } from 'vitest';

import goldOracle from '../../../tests/fixtures/election_chart_gold_oracle.json';
import goldGatewayOracle from '../../../tests/fixtures/election_chart_gold_gateway_oracle.json';
import annaprasanaOracle from '../../../tests/fixtures/election_chart_annaprasana_oracle.json';
import vidyarambhaOracle from '../../../tests/fixtures/election_chart_vidyarambha_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  automatedRulesFor,
  chartAssessorCompleteFor,
  chartManualRemaindersFor,
  evaluateElectionChart,
  evaluateElectionSnapshots,
  evaluateElectionWindow,
  type ElectionChartScreening,
  type ElectionRuleOutcome,
} from '../election-chart-screening';

const PLANETS = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;

function chart(
  houses: Partial<Record<(typeof PLANETS)[number], number>> = {},
  instant = '2026-09-08T05:30:00.000Z',
): ElectionChartSnapshot {
  return {
    instant,
    lagna: { rashi: 'Kanya', degree: 12.5 },
    planets: PLANETS.map((name, index) => ({
      name,
      rashi: 'Mesha',
      degree: index + 0.25,
      house: houses[name] ?? index + 1,
      retrograde: name === 'Rahu' || name === 'Ketu',
    })),
  };
}

type PlanetName = (typeof PLANETS)[number];
type PlanetOverride = Partial<ElectionChartSnapshot['planets'][number]>;

const GOLD_POSITIONS: Record<PlanetName, {
  rashi: string;
  degree: number;
  house: number;
}> = {
  Surya: { rashi: 'Simha', degree: 11, house: 5 },
  Chandra: { rashi: 'Makara', degree: 15, house: 10 },
  Kuja: { rashi: 'Meena', degree: 1, house: 12 },
  Budha: { rashi: 'Vrishabha', degree: 5, house: 2 },
  Guru: { rashi: 'Mesha', degree: 12, house: 1 },
  Shukra: { rashi: 'Karka', degree: 21, house: 4 },
  Shani: { rashi: 'Kanya', degree: 17, house: 6 },
  Rahu: { rashi: 'Tula', degree: 8, house: 7 },
  Ketu: { rashi: 'Mesha', degree: 8, house: 1 },
};

const ANNAPRASANA_POSITIONS: Record<PlanetName, {
  rashi: string;
  degree: number;
  house: number;
}> = {
  Surya: { rashi: 'Mithuna', degree: 10, house: 3 },
  Chandra: { rashi: 'Karka', degree: 20, house: 4 },
  Kuja: { rashi: 'Kanya', degree: 1, house: 6 },
  Budha: { rashi: 'Mesha', degree: 5, house: 1 },
  Guru: { rashi: 'Vrishabha', degree: 12, house: 2 },
  Shukra: { rashi: 'Mithuna', degree: 21, house: 3 },
  Shani: { rashi: 'Kumbha', degree: 17, house: 11 },
  Rahu: { rashi: 'Simha', degree: 8, house: 5 },
  Ketu: { rashi: 'Kumbha', degree: 8, house: 11 },
};

function goldChart(
  overrides: Partial<Record<PlanetName, PlanetOverride>> = {},
  instant = '2026-09-08T05:30:00.000Z',
): ElectionChartSnapshot {
  return {
    instant,
    lagna: { rashi: 'Mesha', degree: 12.5 },
    planets: PLANETS.map(name => ({
      name,
      ...GOLD_POSITIONS[name],
      retrograde: name === 'Rahu' || name === 'Ketu',
      ...overrides[name],
    })),
  };
}

function annaprasanaChart(
  overrides: Partial<Record<PlanetName, PlanetOverride>> = {},
  instant = '2026-09-08T05:30:00.000Z',
): ElectionChartSnapshot {
  return {
    instant,
    lagna: { rashi: 'Mesha', degree: 12.5 },
    planets: PLANETS.map(name => ({
      name,
      ...ANNAPRASANA_POSITIONS[name],
      retrograde: name === 'Rahu' || name === 'Ketu',
      ...overrides[name],
    })),
  };
}

interface VidyarambhaSnapshotFixture {
  houses?: Partial<Record<PlanetName, number>>;
  mutation?: 'remove-ketu' | 'string-house' | 'duplicate-surya';
}

function vidyarambhaChart(
  fixture: VidyarambhaSnapshotFixture,
  index = 0,
): ElectionChartSnapshot {
  const houses: Record<PlanetName, number> = {
    Surya: 1, Chandra: 2, Kuja: 3, Budha: 9, Guru: 9,
    Shukra: 9, Shani: 4, Rahu: 5, Ketu: 6,
    ...fixture.houses,
  };
  const result: ElectionChartSnapshot = {
    instant: `2030-11-17T0${index}:00:00.000Z`,
    lagna: { rashi: 'Mesha', degree: 12.5 },
    planets: PLANETS.map((name, position) => ({
      name,
      rashi: 'Mesha',
      degree: position + 0.25,
      house: houses[name],
      retrograde: name === 'Rahu' || name === 'Ketu',
    })),
  };
  if (fixture.mutation === 'remove-ketu') result.planets.pop();
  if (fixture.mutation === 'string-house') {
    (result.planets[0] as unknown as { house: string }).house = '1';
  }
  if (fixture.mutation === 'duplicate-surya') result.planets.at(-1)!.name = 'Surya';
  return result;
}

function outcome(
  result: ElectionChartScreening,
  ruleId: string,
): ElectionRuleOutcome {
  const match = result.outcomes.find(item => item.ruleId === ruleId);
  if (!match) throw new Error(`Missing election-chart outcome ${ruleId}`);
  return match;
}

describe('source-backed election-chart predicates', () => {
  test('Aksharabhyasa declares a scoped partial two-rule assessor', () => {
    const rules = automatedRulesFor('vidyarambha');
    expect(rules.map(rule => rule.id)).toEqual([
      'vidyarambha.house-8-vacant',
      'vidyarambha.budha-shukra-guru-9',
    ]);
    expect(rules.map(rule => rule.effect)).toEqual(['reject', 'prefer']);
    expect(rules[1]).toEqual(expect.objectContaining({
      kind: 'all_planets_in_houses',
      planets: ['Budha', 'Shukra', 'Guru'],
      houses: [9],
      convention_id: 'vidyarambha-benefic-trio-co-location-v1',
      decision_policy_claim:
        'election_chart.vidyarambha_reject_precedence_policy_v1',
      method_claims: [
        'election_chart.vidyarambha_co_location_policy_v1',
        'election_chart.vidyarambha_reject_precedence_policy_v1',
      ],
    }));
    expect(chartManualRemaindersFor('vidyarambha')).toEqual([]);
    expect(chartAssessorCompleteFor('vidyarambha')).toBe(false);
    expect(chartAssessorCompleteFor('gold')).toBe(true);
    expect(chartAssessorCompleteFor('annaprasana')).toBe(true);
    expect(chartAssessorCompleteFor('karnavedha')).toBe(true);
  });

  test.each(vidyarambhaOracle.cases)(
    'shared Python/TypeScript Aksharabhyasa oracle: $id',
    testCase => {
      const result = evaluateElectionSnapshots(
        'vidyarambha',
        testCase.snapshots.map((snapshot, index) =>
          vidyarambhaChart(snapshot as VidyarambhaSnapshotFixture, index)),
        { houseFrameUncertain: testCase.house_frame_uncertain || false },
      );

      expect(result.outcomes.map(item => item.status)).toEqual(
        testCase.expected_statuses,
      );
      expect(result.rejected).toBe(testCase.rejected);
      expect(result.needsReview).toBe(testCase.needs_review);
      expect(result.preferencePasses).toBe(testCase.preference_passes);
      expect(result.stable).toBe(testCase.stable);
    },
  );

  test('hard reject wins while trio preference changes no score or tier', () => {
    const result = evaluateElectionChart('vidyarambha', vidyarambhaChart({
      houses: { Rahu: 8, Budha: 9, Shukra: 9, Guru: 9 },
    }));

    expect(result.rejected).toBe(true);
    expect(result.preferencePasses).toBe(1);
    expect(outcome(result, 'vidyarambha.house-8-vacant').evidence).toEqual([
      'House 8 occupants: Rahu.',
    ]);
    expect(outcome(result, 'vidyarambha.budha-shukra-guru-9')).toEqual(
      expect.objectContaining({
        status: 'pass',
        evidence: [
          'Budha house 9; Shukra house 9; Guru house 9; all must be in house 9.',
        ],
      }),
    );
  });

  test('Annaprasana declares the six-rule Raman transcription assessor', () => {
    const rules = automatedRulesFor('annaprasana');

    expect(rules.map(rule => rule.id)).toEqual([
      'annaprasana.house-10-vacant',
      'annaprasana.budha-not-7',
      'annaprasana.kuja-not-8',
      'annaprasana.shukra-not-9',
      'annaprasana.benefic-occupies-lagna',
      'annaprasana.no-natural-malefic-in-lagna',
    ]);
    expect(rules.map(rule => rule.effect)).toEqual([
      'reject', 'reject', 'reject', 'reject', 'prefer', 'reject',
    ]);
    expect(rules.every(rule => rule.source_claim
      === 'muhurta.annaprasana.raman_transcription_chart')).toBe(true);
    expect(rules.every(rule => rule.source_locator
      === "B. V. Raman, Chapter VIII, 'First feeding on rice (Annaprasana),' inspected in the 2020 Chistabo derivative at internal printed p. 22 (physical PDF p. 25)"))
      .toBe(true);
    expect(rules[4].decision_policy_claim).toBe(
      'election_chart.annaprasana.raman_transcription_policy_v1');
    expect(rules[4].convention_id).toBe(
      'whole-sign-physical-occupation-v1');
    expect(rules[5].convention_id).toBe(
      'annaprasana-natural-malefic-lagna-v1');
    expect(new Set(rules[5].method_claims)).toEqual(new Set([
      'election_chart.natural_malefics.bphs_3_11_modern_witness',
      'election_chart.whole_sign_house_policy_v1',
      'election_chart.mean_node_policy_v1',
      'election_chart.budha_same_sign_association_policy_v1',
      'election_chart.raman_180_degree_paksha_policy_v1',
      'election_chart.lunar_phase_boundary_guard_policy_v1',
      'election_chart.annaprasana_fail_closed_aggregation_policy_v1',
    ]));
    expect(chartManualRemaindersFor('annaprasana')).toEqual([]);
    expect(chartAssessorCompleteFor('annaprasana')).toBe(true);
    expect(chartAssessorCompleteFor('gold')).toBe(true);
    expect(chartAssessorCompleteFor('karnavedha')).toBe(true);
    expect(chartAssessorCompleteFor('pilgrimage')).toBe(false);
  });

  test.each(annaprasanaOracle.cases)(
    'shared Python/TypeScript Annaprasana oracle: $id',
    testCase => {
      const result = evaluateElectionChart(
        'annaprasana',
        annaprasanaChart(
          testCase.overrides as Partial<Record<PlanetName, PlanetOverride>>,
        ),
      );

      expect(result.outcomes.map(item => item.status)).toEqual(
        testCase.expected_statuses,
      );
      expect(result.rejected).toBe(testCase.rejected);
      expect(result.preferencePasses).toBe(testCase.preference_passes);
      expect(result.needsReview).toBe(testCase.needs_review);
    },
  );

  test.each(annaprasanaOracle.geographic_cases)(
    'multi-city live-projection Annaprasana golden case: $id',
    testCase => {
      const result = evaluateElectionChart(
        'annaprasana', testCase.chart as ElectionChartSnapshot,
      );

      expect(result.outcomes.map(item => item.status)).toEqual(
        testCase.expected_statuses,
      );
      expect(result.rejected).toBe(testCase.rejected);
      expect(result.preferencePasses).toBe(testCase.preference_passes);
      expect(result.needsReview).toBe(testCase.needs_review);

      const rashis = [
        'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
        'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
      ];
      const lagnaIndex = rashis.indexOf(testCase.chart.lagna.rashi);
      expect(testCase.chart.planets.every(planet => planet.house === (
        (rashis.indexOf(planet.rashi) - lagnaIndex + 12) % 12
      ) + 1)).toBe(true);
    },
  );

  test('Annaprasana geographic goldens span Hyderabad, Sydney and two dates', () => {
    expect(new Set(
      annaprasanaOracle.geographic_cases.map(testCase => testCase.city),
    )).toEqual(new Set(['Hyderabad', 'Sydney']));
    expect(new Set(
      annaprasanaOracle.geographic_cases.map(
        testCase => testCase.chart.instant.slice(0, 10),
      ),
    ).size).toBe(2);
    expect(annaprasanaOracle.geographic_source).toEqual({
      service: 'DashaFlow sidecar /calculate',
      engine: 'DashaFlow 1.1.0',
      ayanamsha: 'Lahiri',
      ephemeris: 'moshier',
      retrieved_on: '2026-08-30',
      projection_note: 'Planet Rashis and degrees come from the live sidecar. Houses are the returned Whole Sign projection and are re-evaluated by the assessor; no birth-profile data is involved.',
    });
  });

  test('Annaprasana reports observed facts for each predicate shape', () => {
    const result = evaluateElectionChart('annaprasana', annaprasanaChart());

    expect(outcome(result, 'annaprasana.house-10-vacant').evidence).toEqual([
      'House 10 occupants: none.',
    ]);
    expect(outcome(result, 'annaprasana.budha-not-7').evidence).toEqual([
      'Budha occupies house 1, outside house 7.',
    ]);
    expect(outcome(result, 'annaprasana.benefic-occupies-lagna').evidence).toEqual([
      'Lagna occupants among Budha, Guru and Shukra: Budha.',
    ]);
    expect(outcome(result, 'annaprasana.no-natural-malefic-in-lagna').evidence).toEqual([
      'Natural malefics in Lagna: none; Chandra is outside Lagna.',
    ]);
  });

  test('Annaprasana waxing and waning Chandra follow the disclosed split', () => {
    const waning = evaluateElectionChart('annaprasana', annaprasanaChart({
      Chandra: { rashi: 'Mesha', degree: 5, house: 1 },
    }));
    const waxing = evaluateElectionChart('annaprasana', annaprasanaChart({
      Surya: { rashi: 'Meena', degree: 10, house: 12 },
      Chandra: { rashi: 'Mesha', degree: 20, house: 1 },
    }));

    expect(outcome(waning,
      'annaprasana.no-natural-malefic-in-lagna').status).toBe('fail');
    expect(outcome(waning,
      'annaprasana.no-natural-malefic-in-lagna').evidence.join(' '))
      .toContain('waning Chandra');
    expect(waning.rejected).toBe(true);
    expect(outcome(waxing,
      'annaprasana.no-natural-malefic-in-lagna').status).toBe('pass');
    expect(outcome(waxing,
      'annaprasana.no-natural-malefic-in-lagna').evidence.join(' '))
      .toContain('waxing Chandra');
    expect(waxing.rejected).toBe(false);
  });

  test.each([0, 0.02, 179.98, 180, 180.02])(
    'Annaprasana phase guard includes the %.2f degree boundary cell',
    elongation => {
      const chandra = elongation < 20
        ? { rashi: 'Tula', degree: 10 + elongation, house: 1 }
        : { rashi: 'Mesha', degree: elongation - 170, house: 1 };
      const result = evaluateElectionChart('annaprasana', annaprasanaChart({
        Surya: { rashi: 'Tula', degree: 10, house: 7 },
        Chandra: chandra,
      }));

      expect(outcome(result,
        'annaprasana.no-natural-malefic-in-lagna').status).toBe('unknown');
      expect(result.needsReview).toBe(true);
    },
  );

  test('Annaprasana fixed malefic failure dominates phase unknown', () => {
    const result = evaluateElectionChart('annaprasana', annaprasanaChart({
      Surya: { rashi: 'Mesha', degree: 10, house: 1 },
      Chandra: { rashi: 'Mesha', degree: 10, house: 1 },
    }));

    expect(outcome(result,
      'annaprasana.no-natural-malefic-in-lagna')).toEqual(
      expect.objectContaining({
        status: 'fail',
        evidence: ['Natural malefics in Lagna: Surya.'],
      }),
    );
    expect(result).toEqual(expect.objectContaining({
      rejected: true,
      needsReview: false,
    }));
  });

  test('Annaprasana window aggregation is effect-aware and fail-closed', () => {
    const preferenceMixed = evaluateElectionSnapshots('annaprasana', [
      annaprasanaChart(),
      annaprasanaChart(
        { Budha: { rashi: 'Vrishabha', house: 2 } },
        '2026-09-08T05:40:00.000Z',
      ),
    ]);
    const mandatoryFailAndUnknown = evaluateElectionSnapshots('annaprasana', [
      annaprasanaChart({
        Surya: { rashi: 'Mesha', degree: 10, house: 1 },
      }),
      annaprasanaChart({
        Surya: { rashi: 'Tula', degree: 10, house: 7 },
        Chandra: { rashi: 'Mesha', degree: 10, house: 1 },
      }, '2026-09-08T05:40:00.000Z'),
    ]);

    expect(outcome(preferenceMixed,
      'annaprasana.benefic-occupies-lagna').status).toBe('unknown');
    expect(preferenceMixed.needsReview).toBe(true);
    expect(outcome(mandatoryFailAndUnknown,
      'annaprasana.no-natural-malefic-in-lagna').status).toBe('fail');
    expect(mandatoryFailAndUnknown.rejected).toBe(true);
  });

  test('Annaprasana absent commendation is a preference miss only', () => {
    const result = evaluateElectionChart('annaprasana', annaprasanaChart({
      Budha: { rashi: 'Vrishabha', house: 2 },
    }));

    expect(outcome(result,
      'annaprasana.benefic-occupies-lagna').status).toBe('fail');
    expect(result).toEqual(expect.objectContaining({
      preferencePasses: 0,
      rejected: false,
      needsReview: false,
    }));
  });

  test('Annaprasana incomplete and uncertain frames fail closed', () => {
    const incomplete = annaprasanaChart();
    incomplete.planets.pop();
    const missing = evaluateElectionChart('annaprasana', incomplete);
    const uncertain = evaluateElectionChart('annaprasana', annaprasanaChart(), {
      houseFrameUncertain: true,
    });

    expect(missing.outcomes.every(item => item.status === 'unknown')).toBe(true);
    expect(uncertain.outcomes.every(item => item.status === 'unknown')).toBe(true);
  });

  test.each([
    true as unknown as number,
    false as unknown as number,
    0,
    13,
    7.5,
    Number.NaN,
    Number.POSITIVE_INFINITY,
  ])('Annaprasana invalid house value %s fails closed', invalidHouse => {
    const chart = annaprasanaChart();
    chart.planets[0].house = invalidHouse;

    const result = evaluateElectionChart('annaprasana', chart);

    expect(result.outcomes.every(item => item.status === 'unknown')).toBe(true);
    expect(result.rejected).toBe(false);
    expect(result.needsReview).toBe(true);
  });

  test('Gold declares four qualification rules and no chart remainder', () => {
    const rules = automatedRulesFor('gold');
    expect(rules.map(rule => rule.id)).toEqual([
      'gold.surya-well-situated',
      'gold.chandra-well-situated',
      'gold.surya-fully-aspected',
      'gold.chandra-fully-aspected',
    ]);
    expect(rules.every(rule => rule.effect === 'qualify')).toBe(true);
    expect(rules.every(rule => !!rule.convention_id)).toBe(true);
    expect(rules.every(rule => !!rule.method_claims?.length)).toBe(true);
    expect(rules.every(rule =>
      rule.decision_policy_claim
        === 'election_chart.gold_qualification_policy_v1')).toBe(true);
    const classical = new Set([
      'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani',
    ]);
    for (const rule of rules.filter(item => item.kind === 'planet_receives_full_aspect')) {
      expect(rule.aspectors?.every(aspector => classical.has(aspector))).toBe(true);
      expect(rule.aspectors).not.toContain(rule.planet);
      expect(rule.aspectors).not.toContain('Rahu');
      expect(rule.aspectors).not.toContain('Ketu');
    }
    expect(chartManualRemaindersFor('gold')).toEqual([]);
  });

  test.each(goldOracle.cases)(
    'shared Python/TypeScript Gold oracle: $id',
    testCase => {
      const result = evaluateElectionChart(
        'gold',
        goldChart(testCase.overrides as Partial<Record<PlanetName, PlanetOverride>>),
      );

      expect(result.outcomes.map(item => item.status)).toEqual(
        testCase.expected_statuses,
      );
      expect(result.qualificationFailed).toBe(testCase.qualification_failed);
      expect(result.needsReview).toBe(testCase.needs_review);
    },
  );

  test.each(goldGatewayOracle.cases)(
    'real multi-city/date Gold gateway oracle: $id',
    testCase => {
      const result = evaluateElectionChart(
        'gold',
        testCase.chart as ElectionChartSnapshot,
      );

      expect(result.outcomes.map(item => item.status)).toEqual(
        testCase.expected_statuses,
      );
      expect(result.qualificationFailed).toBe(testCase.qualification_failed);
      expect(result.needsReview).toBe(testCase.needs_review);
    },
  );

  test('real Gold gateway oracle covers every required golden disposition', () => {
    expect(new Set(goldGatewayOracle.cases.map(item => item.city))).toEqual(
      new Set(['Hyderabad', 'Sydney']),
    );
    expect(new Set(goldGatewayOracle.cases.map(
      item => item.chart.instant.slice(0, 10),
    )).size).toBeGreaterThanOrEqual(2);
    expect(new Set(goldGatewayOracle.cases.flatMap(item => item.coverage))).toEqual(
      new Set(['pass', 'fail', 'unknown', 'conflict', 'boundary']),
    );
  });

  test('Gold golden fixture passes both placement and full-aspect clauses', () => {
    const result = evaluateElectionChart('gold', goldChart());

    expect(result.outcomes.map(item => item.status)).toEqual([
      'pass', 'pass', 'pass', 'pass',
    ]);
    expect(result).toEqual(expect.objectContaining({
      rejected: false,
      needsReview: false,
      preferencePasses: 0,
      qualificationFailed: false,
      stable: true,
    }));
    expect(outcome(result, 'gold.surya-fully-aspected').evidence).toEqual([
      'Full Graha Drishti to Surya: Guru.',
    ]);
    expect(outcome(result, 'gold.chandra-fully-aspected').evidence).toEqual([
      'Full Graha Drishti to Chandra: Shukra.',
    ]);
  });

  test.each([
    ['gold.surya-well-situated', { Surya: { house: 6 } }, 'house 6'],
    ['gold.chandra-well-situated', { Chandra: { house: 8 } }, 'house 8'],
    [
      'gold.surya-well-situated',
      { Surya: { rashi: 'Vrishabha' } },
      'enemy Rasi Vrishabha',
    ],
    [
      'gold.surya-well-situated',
      { Surya: { rashi: 'Tula' } },
      'debilitation Rasi Tula',
    ],
    [
      'gold.surya-well-situated',
      { Surya: { degree: 20.1 } },
      'debilitation Navamsa Tula',
    ],
    [
      'gold.chandra-well-situated',
      { Chandra: { rashi: 'Simha', degree: 21 } },
      'solar clearance 10.00° below 12°',
    ],
  ] as const)(
    '%s fails a known adverse factor without rejecting the slot',
    (ruleId, overrides, evidence) => {
      const result = evaluateElectionChart('gold', goldChart(overrides));
      const ruleOutcome = outcome(result, ruleId);

      expect(ruleOutcome.status).toBe('fail');
      expect(ruleOutcome.evidence.join(' ')).toContain(evidence);
      expect(result.qualificationFailed).toBe(true);
      expect(result.rejected).toBe(false);
    },
  );

  test.each([
    [
      { Surya: { degree: 10 } },
      'gold.surya-well-situated',
      'Navamsa boundary',
    ],
    [
      { Chandra: { rashi: 'Simha', degree: 23 } },
      'gold.chandra-well-situated',
      'solar-clearance threshold',
    ],
  ] as const)(
    'Gold guard band fails closed for %s',
    (overrides, ruleId, evidence) => {
      const result = evaluateElectionChart('gold', goldChart(overrides));
      const ruleOutcome = outcome(result, ruleId);

      expect(ruleOutcome.status).toBe('unknown');
      expect(ruleOutcome.evidence.join(' ')).toContain(evidence);
      expect(result.needsReview).toBe(true);
      expect(result.qualificationFailed).toBe(false);
    },
  );

  test('Gold literal full-aspect convention accepts Shani as an aspector', () => {
    const result = evaluateElectionChart('gold', goldChart({
      Guru: { rashi: 'Mithuna' },
      Shani: { rashi: 'Mithuna' },
    }));

    expect(outcome(result, 'gold.surya-fully-aspected')).toEqual(
      expect.objectContaining({
        status: 'pass',
        evidence: expect.arrayContaining(['Full Graha Drishti to Surya: Shani.']),
      }),
    );
    expect(outcome(result, 'gold.chandra-fully-aspected').status).toBe('pass');
  });

  test.each([
    ['gold.surya-fully-aspected', { Guru: { rashi: 'Mithuna' } }],
    ['gold.chandra-fully-aspected', { Shukra: { rashi: 'Simha' } }],
  ] as const)('%s fails when no listed full aspect reaches its target', (
    ruleId, overrides,
  ) => {
    const result = evaluateElectionChart('gold', goldChart(overrides));
    const ruleOutcome = outcome(result, ruleId);

    expect(ruleOutcome.status).toBe('fail');
    expect(ruleOutcome.evidence[0]).toMatch(/^No v1 full Graha Drishti/);
    expect(result.qualificationFailed).toBe(true);
    expect(result.needsReview).toBe(false);
  });

  test('Gold lets a sampled fail dominate unknown for the same rule', () => {
    const result = evaluateElectionSnapshots('gold', [
      goldChart({}, '2026-09-08T05:30:00.000Z'),
      goldChart({ Surya: { degree: 10 } }, '2026-09-08T05:40:00.000Z'),
      goldChart({ Surya: { house: 6 } }, '2026-09-08T05:50:00.000Z'),
    ]);

    expect(outcome(result, 'gold.surya-well-situated').status).toBe('fail');
    expect(result).toEqual(expect.objectContaining({
      stable: false,
      qualificationFailed: true,
      needsReview: true,
      rejected: false,
    }));
  });

  test('Gold fails closed when a Navamsa transition is possible between samples', () => {
    const result = evaluateElectionSnapshots('gold', [
      goldChart({ Surya: { degree: 9.96 } }, '2026-09-08T05:30:00.000Z'),
      goldChart({ Surya: { degree: 9.96 } }, '2026-09-08T05:35:00.000Z'),
    ]);

    expect(outcome(result, 'gold.surya-well-situated')).toEqual(
      expect.objectContaining({
        status: 'unknown',
        evidence: expect.arrayContaining([
          expect.stringContaining('transition cannot be excluded'),
        ]),
      }),
    );
    expect(result).toEqual(expect.objectContaining({ stable: false, needsReview: true }));
  });

  test('Gold fails closed when a solar-clearance transition is possible', () => {
    const result = evaluateElectionSnapshots('gold', [
      goldChart({ Chandra: { rashi: 'Simha', degree: 23.1 } },
        '2026-09-08T05:30:00.000Z'),
      goldChart({ Chandra: { rashi: 'Simha', degree: 23.1 } },
        '2026-09-08T05:35:00.000Z'),
    ]);

    expect(outcome(result, 'gold.chandra-well-situated')).toEqual(
      expect.objectContaining({
        status: 'unknown',
        evidence: expect.arrayContaining([
          expect.stringContaining('solar-clearance transition'),
        ]),
      }),
    );
    expect(result.needsReview).toBe(true);
  });

  test('Gold fails closed when adjacent chart samples exceed ten minutes', () => {
    const result = evaluateElectionSnapshots('gold', [
      goldChart({}, '2026-09-08T05:30:00.000Z'),
      goldChart({}, '2026-09-08T05:41:00.000Z'),
    ]);

    expect(new Set(result.outcomes.map(item => item.status))).toEqual(new Set(['unknown']));
    expect(result.outcomes.every(item => item.evidence.some(detail =>
      detail.includes('ten-minute transition coverage')))).toBe(true);
    expect(result).toEqual(expect.objectContaining({ stable: false, needsReview: true }));
  });

  test('Gold aspect geometry fails closed at a rounded Rasi boundary', () => {
    const result = evaluateElectionChart('gold', goldChart({ Guru: { degree: 0 } }));

    expect(outcome(result, 'gold.surya-fully-aspected')).toEqual(
      expect.objectContaining({
        status: 'unknown',
        evidence: ['A possible aspector is within the rounded Rasi boundary guard.'],
      }),
    );
  });

  test('Gold accepts one secure aspect despite another aspector boundary', () => {
    const result = evaluateElectionChart('gold', goldChart({
      Guru: { degree: 0 },
      Shani: { rashi: 'Mithuna' },
    }));

    expect(outcome(result, 'gold.surya-fully-aspected')).toEqual(
      expect.objectContaining({
        status: 'pass',
        evidence: expect.arrayContaining(['Full Graha Drishti to Surya: Shani.']),
      }),
    );
  });

  test('Gold accepts a continuous aspect despite unrelated sampled motion', () => {
    const result = evaluateElectionSnapshots('gold', [
      goldChart({
        Guru: { rashi: 'Mithuna' },
        Shani: { rashi: 'Mithuna' },
      }, '2026-09-08T05:30:00.000Z'),
      goldChart({
        Guru: { rashi: 'Dhanu' },
        Shani: { rashi: 'Mithuna' },
      }, '2026-09-08T05:35:00.000Z'),
    ]);

    expect(outcome(result, 'gold.surya-fully-aspected')).toEqual(
      expect.objectContaining({
        status: 'pass',
        evidence: expect.arrayContaining(['Full Graha Drishti to Surya: Shani.']),
      }),
    );
    expect(outcome(result, 'gold.chandra-fully-aspected').status).toBe('pass');
  });

  test('Gold uncertain house frame keeps full-aspect results computable', () => {
    const result = evaluateElectionSnapshots('gold', [goldChart()], {
      houseFrameUncertain: true,
    });

    expect(result.outcomes.map(item => item.status)).toEqual([
      'unknown', 'unknown', 'pass', 'pass',
    ]);
    expect(result.needsReview).toBe(true);
    expect(result.qualificationFailed).toBe(false);
  });

  test('Gold incomplete chart makes all four qualifications unknown', () => {
    const incomplete = goldChart();
    incomplete.planets.pop();
    const result = evaluateElectionChart('gold', incomplete);

    expect(result.outcomes.map(item => item.status)).toEqual([
      'unknown', 'unknown', 'unknown', 'unknown',
    ]);
    expect(result).toEqual(expect.objectContaining({
      needsReview: true,
      qualificationFailed: false,
      rejected: false,
    }));
  });

  test('manual remainder omits clauses already represented by deterministic rules', () => {
    expect(chartManualRemaindersFor('wedding')?.join(' ')).not.toMatch(
      /7th house|Mangala.*8th|Shukra.*6th/i,
    );
    expect(chartManualRemaindersFor('pilgrimage')).toEqual([]);
  });

  test('Wedding rejects a named prohibition and reports the exact rule', () => {
    const result = evaluateElectionChart('wedding', chart({ Kuja: 8 }));
    expect(result.rejected).toBe(true);
    expect(result.outcomes).toContainEqual(expect.objectContaining({
      ruleId: 'wedding.kuja-not-8',
      status: 'fail',
      effect: 'reject',
      sourceLocator: expect.stringContaining('internal printed pp. 41-42'),
    }));
  });

  test('Vacant-house checks include Rahu and Ketu under the disclosed convention', () => {
    const result = evaluateElectionChart('gruhapravesha', chart({ Rahu: 8 }));
    expect(result.rejected).toBe(true);
    expect(result.outcomes).toContainEqual(expect.objectContaining({
      ruleId: 'gruhapravesha.house-8-vacant',
      status: 'fail',
    }));
  });

  test('Karnavedha automates the vacant eighth-house clause completely', () => {
    expect(automatedRulesFor('karnavedha').map(rule => rule.id)).toEqual([
      'karnavedha.house-8-vacant',
    ]);
    expect(chartManualRemaindersFor('karnavedha')).toEqual([]);

    const passing = evaluateElectionChart(
      'karnavedha',
      chart(Object.fromEntries(PLANETS.map(name => [name, 1]))),
    );
    expect(passing).toEqual(expect.objectContaining({
      rejected: false,
      needsReview: false,
      stable: true,
    }));
    expect(outcome(passing, 'karnavedha.house-8-vacant')).toEqual(
      expect.objectContaining({ status: 'pass', effect: 'reject' }),
    );

    const failing = evaluateElectionChart('karnavedha', chart({ Ketu: 8 }));
    expect(failing.rejected).toBe(true);
    expect(outcome(failing, 'karnavedha.house-8-vacant')).toEqual(
      expect.objectContaining({ status: 'fail', effect: 'reject' }),
    );

    const incomplete = chart();
    incomplete.planets.pop();
    const unknown = evaluateElectionChart('karnavedha', incomplete);
    expect(unknown).toEqual(expect.objectContaining({
      rejected: false,
      needsReview: true,
    }));
    expect(outcome(unknown, 'karnavedha.house-8-vacant').status).toBe('unknown');
  });

  test.each([0, 13, true, false])(
    'invalid election house %j fails closed to unknown',
    invalidHouse => {
      const invalid = chart();
      (invalid.planets[0] as unknown as { house: unknown }).house = invalidHouse;

      const result = evaluateElectionChart('karnavedha', invalid);

      expect(result).toEqual(expect.objectContaining({
        rejected: false,
        needsReview: true,
      }));
      expect(result.outcomes.every(item => item.status === 'unknown')).toBe(true);
    },
  );

  test('Positive placements are tie-break evidence, not raw-score bonuses', () => {
    const result = evaluateElectionChart('job', chart({ Surya: 10, Kuja: 4 }));
    expect(result.rejected).toBe(false);
    expect(result.preferencePasses).toBe(1);
    expect(result.outcomes).toContainEqual(expect.objectContaining({
      ruleId: 'job.surya-or-kuja-10-11',
      status: 'pass',
      effect: 'prefer',
    }));
  });

  test('A condition that changes within the slot remains unresolved', () => {
    const start = chart({ Kuja: 7 }, '2026-09-08T05:30:00.000Z');
    const end = chart({ Kuja: 8 }, '2026-09-08T06:18:00.000Z');
    const result = evaluateElectionWindow('wedding', start, end);
    expect(result.rejected).toBe(true);
    expect(result.stable).toBe(false);
    expect(result.outcomes).toContainEqual(expect.objectContaining({
      ruleId: 'wedding.kuja-not-8',
      status: 'fail',
    }));
  });

  test('an interior failure cannot hide behind matching endpoint charts', () => {
    const result = evaluateElectionSnapshots('wedding', [
      chart({ Kuja: 7 }, '2026-09-08T05:30:00.000Z'),
      chart({ Kuja: 8 }, '2026-09-08T05:54:00.000Z'),
      chart({ Kuja: 7 }, '2026-09-08T06:18:00.000Z'),
    ]);
    expect(result.rejected).toBe(true);
    expect(result.stable).toBe(false);
    expect(result.outcomes).toContainEqual(expect.objectContaining({
      ruleId: 'wedding.kuja-not-8', status: 'fail',
    }));
  });

  test('Missing one of the nine grahas fails closed as unknown', () => {
    const incomplete = chart();
    incomplete.planets = incomplete.planets.slice(0, 8);
    const result = evaluateElectionChart('wedding', incomplete);
    expect(result.rejected).toBe(false);
    expect(result.needsReview).toBe(true);
    expect(result.outcomes.every(outcome => outcome.status === 'unknown')).toBe(true);
  });
});
