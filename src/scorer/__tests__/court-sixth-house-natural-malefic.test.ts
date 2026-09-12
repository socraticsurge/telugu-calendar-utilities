import { describe, expect, test } from 'vitest';
import oracle from '../../../tests/fixtures/election_chart_court_house6_malefic_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  COURT_SIXTH_HOUSE_NATURAL_MALEFIC_METADATA,
  aggregateCourtSixthHouseNaturalMaleficWindow,
  courtSixthHouseCandidateDisposition,
  evaluateCourtSixthHouseNaturalMalefic,
} from '../election-assessors/court';

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
  return evaluateCourtSixthHouseNaturalMalefic(chart(caseData), {
    houseFrameUncertain:
      'house_frame_uncertain' in caseData && caseData.house_frame_uncertain,
  });
}

describe('Court sixth-house natural-malefic exclusion', () => {
  test('keeps the synthetic oracle, source statement, convention, and effect explicit', () => {
    expect(oracle.fixture_kind).toBe('synthetic_contract_fixture');
    expect(oracle.source_golden).toBe(false);
    expect(COURT_SIXTH_HOUSE_NATURAL_MALEFIC_METADATA).toEqual(oracle.metadata);
    expect(COURT_SIXTH_HOUSE_NATURAL_MALEFIC_METADATA.event_policy.status)
      .toBe('implemented');
  });

  test.each(oracle.snapshot_cases)('$id', (caseData) => {
    expect(outcome(caseData)).toEqual(caseData.expected);
  });

  test.each(oracle.window_cases)('$id', (window) => {
    const cases = new Map(oracle.snapshot_cases.map(item => [item.id, item]));
    const samples = window.sample_case_ids.map(caseId => outcome(cases.get(caseId)!));
    expect(aggregateCourtSixthHouseNaturalMaleficWindow(samples, {
      localLagnaTransitionsComplete: window.coverage.local_lagna_transitions_complete,
      grahaRasiTransitionsComplete: window.coverage.graha_rasi_transitions_complete,
      chandraPhaseTransitionsComplete: window.coverage.chandra_phase_transitions_complete,
      budhaAssociationTransitionsComplete:
        window.coverage.budha_association_transitions_complete,
      budgetExhausted: window.coverage.budget_exhausted,
    })).toEqual(window.expected);
  });

  test('projects only a known failure to the accepted reject disposition', () => {
    expect(courtSixthHouseCandidateDisposition({ status: 'fail', evidence: [] }))
      .toBe('reject');
    expect(courtSixthHouseCandidateDisposition({ status: 'pass', evidence: [] }))
      .toBe('retain');
    expect(courtSixthHouseCandidateDisposition({ status: 'unknown', evidence: [] }))
      .toBe('review');
  });

  test('fails closed for runtime-invalid charts, options, samples, and coverage', () => {
    expect(evaluateCourtSixthHouseNaturalMalefic(
      null as unknown as ElectionChartSnapshot,
    ).status).toBe('unknown');
    expect(evaluateCourtSixthHouseNaturalMalefic(chart(oracle.snapshot_cases[0]), {
      houseFrameUncertain: 'yes' as unknown as boolean,
    }).status).toBe('unknown');
    const sparse = new Array(1) as ReturnType<typeof outcome>[];
    const complete = {
      localLagnaTransitionsComplete: true,
      grahaRasiTransitionsComplete: true,
      chandraPhaseTransitionsComplete: true,
      budhaAssociationTransitionsComplete: true,
      budgetExhausted: false,
    };
    expect(aggregateCourtSixthHouseNaturalMaleficWindow(sparse, complete)).toEqual({
      status: 'unknown',
      evidence: ['Represented chart states are malformed or incomplete.'],
    });
    expect(aggregateCourtSixthHouseNaturalMaleficWindow(
      [outcome(oracle.snapshot_cases[0])],
      null as unknown as Parameters<typeof aggregateCourtSixthHouseNaturalMaleficWindow>[1],
    )).toEqual({
      status: 'unknown',
      evidence: ['Window transition metadata is malformed or incomplete.'],
    });
  });
});
