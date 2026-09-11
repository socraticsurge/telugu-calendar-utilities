import { describe, expect, test } from 'vitest';
import oracle from '../../../tests/fixtures/election_chart_court_mesha_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  COURT_MESHA_D1_D9_METADATA,
  aggregateCourtMeshaD1D9Window,
  courtMeshaAdmissionKind,
  evaluateCourtMeshaD1D9,
} from '../election-assessors/court';

type SnapshotCase = (typeof oracle.snapshot_cases)[number];

function outcome(caseData: SnapshotCase) {
  return evaluateCourtMeshaD1D9(
    caseData.chart as ElectionChartSnapshot | null,
    {
      authoritativeD1Rashi: caseData.authoritative_d1_rashi,
      lagnaAuthorityUncertain:
        'lagna_authority_uncertain' in caseData
        && caseData.lagna_authority_uncertain,
      supportedSystem:
        !('supported_system' in caseData) || caseData.supported_system,
    },
  );
}

describe('Court Mesha D1/D9 foundation', () => {
  test('separates synthetic fixture, source, method, effect, and admission policy', () => {
    expect(oracle.fixture_kind).toBe('synthetic_contract_fixture');
    expect(oracle.source_golden).toBe(false);
    expect(COURT_MESHA_D1_D9_METADATA).toEqual(oracle.metadata);
    expect(COURT_MESHA_D1_D9_METADATA.source_statement.claim_id).not.toBe(
      COURT_MESHA_D1_D9_METADATA.event_policy.effect_claim_id,
    );
    expect(COURT_MESHA_D1_D9_METADATA.event_policy.status).toBe('specified_unwired');
    expect(COURT_MESHA_D1_D9_METADATA.conditional_admission.delivery_issue).toBe(285);
  });

  test.each(oracle.snapshot_cases)('$id', (caseData) => {
    expect(outcome(caseData)).toEqual(caseData.expected);
  });

  test('only an unresolved non-Mesha D9 alternative is provisional', () => {
    const cases = new Map(oracle.snapshot_cases.map(item => [item.id, item]));
    const passed = outcome(cases.get('non-mesha-d1-mesha-d9-passes')!);
    const failed = outcome(cases.get('resolved-non-mesha-d1-and-d9-fail')!);
    const unknown = outcome(cases.get('internal-navamsa-boundary-is-unknown')!);

    expect(courtMeshaAdmissionKind('Mesha')).toBe('unconditional');
    expect(courtMeshaAdmissionKind('Vrishabha')).toBe('provisional');
    expect(courtMeshaAdmissionKind('Vrishabha', unknown)).toBe('provisional');
    expect(courtMeshaAdmissionKind('Vrishabha', passed)).toBe('admitted');
    expect(courtMeshaAdmissionKind('Vrishabha', failed)).toBe('rejected');
    expect(courtMeshaAdmissionKind(null)).toBe('unavailable');
  });

  test.each(oracle.window_cases)('$id', (window) => {
    const cases = new Map(oracle.snapshot_cases.map(item => [item.id, item]));
    const samples = window.sample_case_ids.map(caseId => outcome(cases.get(caseId)!));
    const expected = 'expected_case_id' in window
      && typeof window.expected_case_id === 'string'
      ? cases.get(window.expected_case_id)!.expected
      : window.expected;
    expect(aggregateCourtMeshaD1D9Window(samples, {
      localLagnaTransitionsComplete: window.coverage.local_lagna_transitions_complete,
      lagnaNavamsaTransitionsComplete:
        window.coverage.lagna_navamsa_transitions_complete,
      budgetExhausted: window.coverage.budget_exhausted,
    })).toEqual(expected);
  });

  test('runtime-invalid chart and coverage inputs fail closed', () => {
    expect(evaluateCourtMeshaD1D9(
      { lagna: { rashi: 'Vrishabha', degree: Number.NaN } } as ElectionChartSnapshot,
      { authoritativeD1Rashi: 'Vrishabha' },
    ).status).toBe('unknown');

    const pass = outcome(oracle.snapshot_cases[0]);
    expect(aggregateCourtMeshaD1D9Window(
      [pass],
      null as unknown as Parameters<typeof aggregateCourtMeshaD1D9Window>[1],
    ).status).toBe('unknown');
  });
});
