import { describe, expect, test } from 'vitest';
import oracle from '../../../tests/fixtures/election_chart_court_lord_separation_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  COURT_LAGNA_SIXTH_LORD_SEPARATION_METADATA,
  aggregateCourtLagnaSixthLordSeparationWindow,
  evaluateCourtLagnaSixthLordSeparation,
} from '../election-assessors/court';
import {
  CLASSICAL_RASI_LORDS,
  deriveLagnaSixthLords,
} from '../election-assessors/lordship';

type SnapshotCase = (typeof oracle.snapshot_cases)[number];

function chart(caseData: SnapshotCase): ElectionChartSnapshot {
  const planets = structuredClone(oracle.base_planets);
  const overrides = 'overrides' in caseData ? caseData.overrides : undefined;
  for (const planet of planets) {
    Object.assign(planet, overrides?.[planet.name as keyof typeof overrides]);
  }
  const removed = new Set('remove' in caseData ? caseData.remove : []);
  const remaining = planets.filter(item => !removed.has(item.name));
  if ('duplicate' in caseData && caseData.duplicate) {
    remaining.push(structuredClone(
      remaining.find(item => item.name === caseData.duplicate)!,
    ));
  }
  return { planets: remaining } as ElectionChartSnapshot;
}

function outcome(caseData: SnapshotCase) {
  return evaluateCourtLagnaSixthLordSeparation(chart(caseData), {
    authoritativeLagnaRashi: caseData.lagna,
    lagnaAuthorityUncertain:
      'lagna_authority_uncertain' in caseData && caseData.lagna_authority_uncertain,
  });
}

describe('Court Lagna-sixth-lord separation', () => {
  test('separates source wording, computation convention, and unwired preference', () => {
    expect(oracle.fixture_kind).toBe('synthetic_contract_fixture');
    expect(oracle.source_golden).toBe(false);
    expect(COURT_LAGNA_SIXTH_LORD_SEPARATION_METADATA).toEqual(oracle.metadata);
    expect(COURT_LAGNA_SIXTH_LORD_SEPARATION_METADATA.event_policy.effect)
      .toBe('prefer');
    expect(COURT_LAGNA_SIXTH_LORD_SEPARATION_METADATA.event_policy.status)
      .toBe('specified_unwired');
  });

  test('covers all twelve Lagnas and never derives a node as lord', () => {
    const lords = new Set<string>(Object.values(CLASSICAL_RASI_LORDS));
    expect(lords.has('Rahu')).toBe(false);
    expect(lords.has('Ketu')).toBe(false);
    for (const caseData of oracle.lagna_cases) {
      expect(deriveLagnaSixthLords(caseData.lagna)).toEqual({
        lagnaLord: caseData.lagna_lord,
        sixthRashi: caseData.sixth_rashi,
        sixthLord: caseData.sixth_lord,
      });
    }
  });

  test.each(oracle.snapshot_cases)('$id', (caseData) => {
    expect(outcome(caseData)).toEqual(caseData.expected);
  });

  test.each(oracle.window_cases)('$id', (window) => {
    const cases = new Map(oracle.snapshot_cases.map(item => [item.id, item]));
    const samples = window.sample_case_ids.map(caseId => outcome(cases.get(caseId)!));
    expect(aggregateCourtLagnaSixthLordSeparationWindow(samples, {
      localLagnaTransitionsComplete: window.coverage.local_lagna_transitions_complete,
      lagnaLordRasiTransitionsComplete:
        window.coverage.lagna_lord_rasi_transitions_complete,
      sixthLordRasiTransitionsComplete:
        window.coverage.sixth_lord_rasi_transitions_complete,
      budgetExhausted: window.coverage.budget_exhausted,
    })).toEqual(window.expected);
  });

  test('runtime-invalid chart and options fail closed', () => {
    expect(evaluateCourtLagnaSixthLordSeparation(
      null as unknown as ElectionChartSnapshot,
      { authoritativeLagnaRashi: 'Mesha' },
    ).status).toBe('unknown');
    expect(evaluateCourtLagnaSixthLordSeparation(
      chart(oracle.snapshot_cases[0]),
      null as unknown as { authoritativeLagnaRashi?: string },
    ).status).toBe('unknown');
    expect(evaluateCourtLagnaSixthLordSeparation(chart(oracle.snapshot_cases[0]), {
      authoritativeLagnaRashi: 'Mesha',
      lagnaAuthorityUncertain: 'yes' as unknown as boolean,
    }).status).toBe('unknown');
  });
});
