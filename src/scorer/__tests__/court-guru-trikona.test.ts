import { describe, expect, test } from 'vitest';
import oracle from '../../../tests/fixtures/election_chart_court_guru_trikona_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  COURT_GURU_TRIKONA_METADATA,
  aggregateCourtGuruTrikonaWindow,
  evaluateCourtGuruTrikona,
} from '../election-assessors/chart-geometry';

type SnapshotCase = (typeof oracle.snapshot_cases)[number];

function chart(caseData: SnapshotCase): ElectionChartSnapshot {
  const planets = structuredClone(oracle.base_planets);
  if ('guru' in caseData && caseData.guru) {
    Object.assign(planets.find(item => item.name === 'Guru')!, caseData.guru);
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
  return evaluateCourtGuruTrikona(chart(caseData), {
    houseFrameUncertain:
      'house_frame_uncertain' in caseData && caseData.house_frame_uncertain,
  });
}

describe('Court Guru-Trikona foundation', () => {
  test('labels the shared oracle as synthetic rather than a source golden', () => {
    expect(oracle.fixture_kind).toBe('synthetic_contract_fixture');
    expect(oracle.source_golden).toBe(false);
  });

  test('separates source wording, computation convention, and integrated effect', () => {
    expect(COURT_GURU_TRIKONA_METADATA).toEqual(oracle.metadata);
    expect(COURT_GURU_TRIKONA_METADATA.source_statement.claim_id).not.toBe(
      COURT_GURU_TRIKONA_METADATA.convention.method_claim_id,
    );
    expect(COURT_GURU_TRIKONA_METADATA.event_policy.status).toBe('implemented');
  });

  test.each(oracle.snapshot_cases)('$id', (caseData) => {
    expect(outcome(caseData)).toEqual(caseData.expected);
  });

  test.each(oracle.window_cases)('$id', (window) => {
    const cases = new Map(oracle.snapshot_cases.map(item => [item.id, item]));
    const samples = window.sample_case_ids.map(caseId => outcome(cases.get(caseId)!));
    expect(aggregateCourtGuruTrikonaWindow(samples, {
      localLagnaTransitionsComplete: window.coverage.local_lagna_transitions_complete,
      guruRasiTransitionsComplete: window.coverage.guru_rasi_transitions_complete,
      budgetExhausted: window.coverage.budget_exhausted,
    })).toEqual(window.expected);
  });

  test('runtime-invalid charts and sparse arrays fail closed', () => {
    expect(evaluateCourtGuruTrikona(null as unknown as ElectionChartSnapshot)).toEqual({
      status: 'unknown',
      evidence: ['Complete canonical nine-graha Whole Sign facts are unavailable.'],
    });
    const sparsePlanets = { planets: new Array(9) } as ElectionChartSnapshot;
    expect(evaluateCourtGuruTrikona(sparsePlanets)).toEqual({
      status: 'unknown',
      evidence: ['Complete canonical nine-graha Whole Sign facts are unavailable.'],
    });
    const sparse = new Array(1) as ReturnType<typeof outcome>[];
    expect(aggregateCourtGuruTrikonaWindow(sparse, {
      localLagnaTransitionsComplete: true,
      guruRasiTransitionsComplete: true,
      budgetExhausted: false,
    })).toEqual({
      status: 'unknown',
      evidence: ['Represented chart states are malformed or incomplete.'],
    });
  });

  test('a known fail dominates malformed transition metadata', () => {
    const fail = outcome(oracle.snapshot_cases.find(item => item.id === 'guru-house-4-fail')!);
    expect(aggregateCourtGuruTrikonaWindow(
      [fail], null as unknown as Parameters<typeof aggregateCourtGuruTrikonaWindow>[1],
    )).toEqual(fail);
  });

  test.each([
    null,
    [],
    { localLagnaTransitionsComplete: true },
  ])('passing samples fail closed for malformed transition metadata %#', (coverage) => {
    const pass = outcome(oracle.snapshot_cases.find(item => item.id === 'guru-house-5-pass')!);
    expect(aggregateCourtGuruTrikonaWindow(
      [pass], coverage as unknown as Parameters<typeof aggregateCourtGuruTrikonaWindow>[1],
    )).toEqual({
      status: 'unknown',
      evidence: ['Window transition metadata is malformed or incomplete.'],
    });
  });
});
