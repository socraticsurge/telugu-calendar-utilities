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

const RASHIS = {
  Surya: 'Mesha', Chandra: 'Vrishabha', Kuja: 'Mithuna', Budha: 'Karka',
  Guru: 'Simha', Shukra: 'Kanya', Shani: 'Tula', Rahu: 'Vrischika', Ketu: 'Dhanu',
} as const;

function chart(
  overrides: Partial<Record<(typeof PLANETS)[number], string>> = {},
  instant = '2026-09-12T06:00:00.000Z',
): ElectionChartSnapshot {
  return {
    instant,
    lagna: { rashi: 'Mesha', degree: 12 },
    planets: PLANETS.map((name, index) => ({
      name,
      rashi: overrides[name] || RASHIS[name],
      degree: 5 + index,
      house: index + 1,
      retrograde: name === 'Rahu' || name === 'Ketu',
    })),
  };
}

describe('integrated Raman Borrowing assessor', () => {
  test('registers one reject predicate without alternate-lineage rules', () => {
    const rules = automatedRulesFor('borrowing_money');
    expect(rules.map(rule => rule.id)).toEqual([
      'borrowing.same-rasi-chandra-kuja-shani',
    ]);
    expect(rules[0]).toMatchObject({
      effect: 'reject',
      convention_id: 'same-rasi-distributive-conjunction-v1',
      decision_policy_claim:
        'election_chart.borrowing_same_rasi_conjunction_reject_policy_v1',
    });
    expect(rules.some(rule => /chintamani|drik/i.test(rule.id))).toBe(false);
    expect(chartManualRemaindersFor('borrowing_money')).toEqual([]);
    expect(chartAssessorCompleteFor('borrowing_money')).toBe(true);
  });

  test('rejects either conjunction and retains unknown transition coverage', () => {
    expect(evaluateElectionChart('borrowing_money', chart({ Kuja: 'Vrishabha' })))
      .toMatchObject({ rejected: true, needsReview: false });
    expect(evaluateElectionChart('borrowing_money', chart({ Shani: 'Vrishabha' })))
      .toMatchObject({ rejected: true, needsReview: false });

    const incomplete = evaluateElectionSnapshots(
      'borrowing_money', [chart(), chart({}, '2026-09-12T06:10:00.000Z')],
      { borrowingTransitionCoverage: {
        rasiTransitionsComplete: false, budgetExhausted: false,
      } },
    );
    expect(incomplete.outcomes[0].status).toBe('unknown');
    expect(incomplete.needsReview).toBe(true);

    const unsupported = evaluateElectionSnapshots(
      'borrowing_money', [chart(), chart({}, '2026-09-12T06:10:00.000Z')],
      {
        supportedSystem: false,
        borrowingTransitionCoverage: {
          rasiTransitionsComplete: true, budgetExhausted: false,
        },
      },
    );
    expect(unsupported).toMatchObject({ rejected: false, needsReview: true });
    expect(unsupported.outcomes[0].status).toBe('unknown');
  });

  test('preserves an interior rejection even when the endpoints pass', () => {
    const result = evaluateElectionSnapshots('borrowing_money', [
      chart({}, '2026-09-12T06:00:00.000Z'),
      chart({ Kuja: 'Vrishabha' }, '2026-09-12T06:05:00.000Z'),
      chart({}, '2026-09-12T06:10:00.000Z'),
    ], { borrowingTransitionCoverage: {
      rasiTransitionsComplete: true, budgetExhausted: false,
    } });
    expect(result.rejected).toBe(true);
    expect(result.outcomes[0].status).toBe('fail');
  });
});
