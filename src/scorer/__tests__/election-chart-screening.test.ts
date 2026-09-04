import { describe, expect, test } from 'vitest';

import goldOracle from '../../../tests/fixtures/election_chart_gold_oracle.json';
import goldGatewayOracle from '../../../tests/fixtures/election_chart_gold_gateway_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  automatedRulesFor,
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

function outcome(
  result: ElectionChartScreening,
  ruleId: string,
): ElectionRuleOutcome {
  const match = result.outcomes.find(item => item.ruleId === ruleId);
  if (!match) throw new Error(`Missing election-chart outcome ${ruleId}`);
  return match;
}

describe('source-backed election-chart predicates', () => {
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
