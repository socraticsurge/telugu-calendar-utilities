import { describe, expect, test } from 'vitest';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  automatedRulesFor,
  chartManualRemaindersFor,
  evaluateElectionChart,
  evaluateElectionSnapshots,
  evaluateElectionWindow,
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

describe('source-backed election-chart predicates', () => {
  test('Gold remains manual because its qualitative aspect rule is undefined', () => {
    expect(automatedRulesFor('gold')).toEqual([]);
    expect(chartManualRemaindersFor('gold')).toBeNull();
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
      sourceLocator: expect.stringContaining('printed pp. 41-42'),
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
