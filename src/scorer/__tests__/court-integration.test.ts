import { describe, expect, test } from 'vitest';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  automatedRulesFor,
  chartAssessorCompleteFor,
  chartManualRemaindersFor,
  evaluateElectionChart,
  evaluateElectionSnapshots,
} from '../election-chart-screening';

const PLANETS = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;

const POSITIONS = {
  Surya: { rashi: 'Karka', degree: 10, house: 4 },
  Chandra: { rashi: 'Tula', degree: 20, house: 7 },
  Kuja: { rashi: 'Mesha', degree: 12, house: 1 },
  Budha: { rashi: 'Tula', degree: 10, house: 7 },
  Guru: { rashi: 'Mesha', degree: 18, house: 1 },
  Shukra: { rashi: 'Vrishabha', degree: 15, house: 2 },
  Shani: { rashi: 'Makara', degree: 8, house: 10 },
  Rahu: { rashi: 'Kumbha', degree: 9, house: 11 },
  Ketu: { rashi: 'Simha', degree: 9, house: 5 },
};

type Planet = (typeof PLANETS)[number];
type Override = Partial<ElectionChartSnapshot['planets'][number]>;

function chart(
  overrides: Partial<Record<Planet, Override>> = {},
  instant = '2026-09-08T05:30:00.000Z',
): ElectionChartSnapshot {
  return {
    instant,
    lagna: { rashi: 'Mesha', degree: 12.5 },
    planets: PLANETS.map(name => ({
      name,
      ...POSITIONS[name],
      retrograde: name === 'Rahu' || name === 'Ketu',
      ...overrides[name],
    })),
  };
}

function coverage(overrides: Record<string, boolean> = {}) {
  return {
    localLagnaTransitionsComplete: true,
    lagnaNavamsaTransitionsComplete: true,
    guruRasiTransitionsComplete: true,
    grahaRasiTransitionsComplete: true,
    chandraPhaseTransitionsComplete: true,
    budhaAssociationTransitionsComplete: true,
    lagnaLordRasiTransitionsComplete: true,
    sixthLordRasiTransitionsComplete: true,
    fullAspectTransitionsComplete: true,
    budgetExhausted: false,
    ...overrides,
  };
}

describe('integrated Court chart assessor', () => {
  test('registers five default Raman clauses and no optional Chintamani clause', () => {
    const rules = automatedRulesFor('court');
    expect(rules.map(rule => rule.id)).toEqual([
      'court.mesha-lagna-or-navamsa',
      'court.guru-trikona',
      'court.house-6-without-natural-malefic',
      'court.lagna-sixth-lords-max-separated',
      'court.peace-benefic-pattern',
    ]);
    expect(rules.map(rule => rule.effect)).toEqual([
      'reject', 'prefer', 'reject', 'prefer', 'inform',
    ]);
    expect(chartManualRemaindersFor('court')).toEqual([]);
    expect(chartAssessorCompleteFor('court')).toBe(true);
    expect(rules.some(rule => rule.id.includes('chintamani'))).toBe(false);
  });

  test('keeps reject, preference, and information effects separate', () => {
    const passing = evaluateElectionChart('court', chart(), {
      authoritativeLagnaRashi: 'Mesha',
    });
    expect(passing.outcomes.map(item => item.status)).toEqual([
      'pass', 'pass', 'pass', 'pass', 'pass',
    ]);
    expect(passing.rejected).toBe(false);
    expect(passing.needsReview).toBe(false);
    expect(passing.preferencePasses).toBe(2);

    const rejected = evaluateElectionChart('court', chart({
      Shani: { rashi: 'Kanya', house: 6 },
    }), { authoritativeLagnaRashi: 'Mesha' });
    expect(rejected.rejected).toBe(true);
    expect(rejected.preferencePasses).toBe(2);
    expect(rejected.outcomes.find(item =>
      item.ruleId === 'court.house-6-without-natural-malefic')?.status).toBe('fail');

    const preferenceMiss = evaluateElectionChart('court', chart({
      Guru: { rashi: 'Mithuna', house: 3 },
      Budha: { rashi: 'Kanya', house: 6 },
    }), { authoritativeLagnaRashi: 'Mesha' });
    expect(preferenceMiss.rejected).toBe(false);
    expect(preferenceMiss.preferencePasses).toBe(0);
  });

  test('makes litigation result-identical and never treats unknown as pass', () => {
    const snapshot = chart();
    const options = { authoritativeLagnaRashi: 'Mesha' };
    expect(evaluateElectionChart('litigation', snapshot, options)).toEqual(
      evaluateElectionChart('court', snapshot, options),
    );

    const unresolved = evaluateElectionChart('court', snapshot);
    expect(unresolved.outcomes.find(item =>
      item.ruleId === 'court.mesha-lagna-or-navamsa')?.status).toBe('unknown');
    expect(unresolved.rejected).toBe(false);
    expect(unresolved.needsReview).toBe(true);
  });

  test('preserves an interior reject and exposes incomplete transitions', () => {
    const snapshots = [
      chart({}, '2026-09-08T05:30:00.000Z'),
      chart({ Shani: { rashi: 'Kanya', house: 6 } }, '2026-09-08T05:35:00.000Z'),
      chart({}, '2026-09-08T05:40:00.000Z'),
    ];
    const result = evaluateElectionSnapshots('court', snapshots, {
      authoritativeLagnaRashis: ['Mesha', 'Mesha', 'Mesha'],
      courtTransitionCoverage: coverage(),
    });
    expect(result.rejected).toBe(true);
    expect(result.outcomes.find(item =>
      item.ruleId === 'court.house-6-without-natural-malefic')?.status).toBe('fail');

    const incomplete = evaluateElectionSnapshots('court', [snapshots[0], snapshots[2]], {
      authoritativeLagnaRashis: ['Mesha', 'Mesha'],
      courtTransitionCoverage: coverage({
        lagnaNavamsaTransitionsComplete: false,
        guruRasiTransitionsComplete: false,
      }),
    });
    expect(incomplete.rejected).toBe(false);
    expect(incomplete.needsReview).toBe(true);
    expect(incomplete.outcomes.find(item =>
      item.ruleId === 'court.mesha-lagna-or-navamsa')?.status).toBe('unknown');
    expect(incomplete.outcomes.find(item =>
      item.ruleId === 'court.guru-trikona')?.status).toBe('unknown');
  });
});
