import { describe, expect, test } from 'vitest';
import interpretations from '../../data/election-chart-interpretations.generated.json';
import oracle from '../../../tests/fixtures/election_chart_same_rasi_conjunction_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  SAME_RASI_CONJUNCTION_METADATA,
  aggregateSameRasiConjunctionWindow,
  evaluateSameRasiChandraConjunction,
} from '../election-assessors/conjunction';
import { completePlanetPositions } from '../election-assessors/event-admission';

const EXPECTED_PLANETS = new Set([
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani', 'Rahu', 'Ketu',
]);

type SnapshotCase = (typeof oracle.snapshot_cases)[number];

function chart(caseData: SnapshotCase): ElectionChartSnapshot {
  const mutableCase = caseData as SnapshotCase & {
    overrides?: Record<string, Partial<(typeof oracle.base_planets)[number]>>;
    remove?: string[];
    duplicate?: string;
    conflict?: { name: string; rashi: string; replace: string };
  };
  const planets = oracle.base_planets
    .map(planet => ({ ...planet, ...(mutableCase.overrides?.[planet.name] || {}) }))
    .filter(planet => !mutableCase.remove?.includes(planet.name));
  if (mutableCase.duplicate) {
    planets.push({ ...planets.find(planet => planet.name === mutableCase.duplicate)! });
  }
  if (mutableCase.conflict) {
    const replaced = planets.find(planet => planet.name === mutableCase.conflict!.replace)!;
    replaced.name = mutableCase.conflict.name;
    replaced.rashi = mutableCase.conflict.rashi;
  }
  return {
    instant: '2026-09-11T00:00:00.000Z',
    lagna: { rashi: 'Mesha', degree: 10 },
    planets,
  } as ElectionChartSnapshot;
}

function evaluate(caseData: SnapshotCase) {
  return evaluateSameRasiChandraConjunction(
    completePlanetPositions(chart(caseData), EXPECTED_PLANETS),
  );
}

describe('same-Rasi distributive conjunction v1', () => {
  test('keeps source wording, computation convention and event policy separate', () => {
    expect(SAME_RASI_CONJUNCTION_METADATA).toEqual(oracle.metadata);
    expect(SAME_RASI_CONJUNCTION_METADATA.source_statement.claim_id).not.toBe(
      SAME_RASI_CONJUNCTION_METADATA.convention.method_claim_id,
    );
    expect(SAME_RASI_CONJUNCTION_METADATA.event_policy.status).toBe('specified_unwired');

    const entry = interpretations.interpretations[
      SAME_RASI_CONJUNCTION_METADATA.convention.id
    ];
    expect(entry.source_claims).toEqual([
      SAME_RASI_CONJUNCTION_METADATA.source_statement.claim_id,
    ]);
    expect(entry.method_claims).toEqual([
      SAME_RASI_CONJUNCTION_METADATA.convention.method_claim_id,
    ]);
    expect(entry.event_policy_claims).toEqual([
      SAME_RASI_CONJUNCTION_METADATA.event_policy.decision_claim_id,
    ]);
    expect(entry.implementation_status).toBe('implemented');
    expect(entry.event_wiring_status).toBe('specified_unwired');
  });

  test.each(oracle.snapshot_cases)('matches the shared snapshot oracle: $id', caseData => {
    expect(evaluate(caseData)).toEqual(caseData.expected);
  });

  test.each(oracle.window_cases)('matches the shared window oracle: $id', window => {
    const cases = new Map(oracle.snapshot_cases.map(caseData => [caseData.id, caseData]));
    const samples = window.sample_case_ids.map(caseId => evaluate(cases.get(caseId)!));
    expect(aggregateSameRasiConjunctionWindow(samples, {
      transitionComplete: window.transition_complete,
      budgetExhausted: window.budget_exhausted,
    })).toEqual(window.expected);
  });
});
