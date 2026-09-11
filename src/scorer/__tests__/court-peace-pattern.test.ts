import { describe, expect, test } from 'vitest';
import oracle from '../../../tests/fixtures/election_chart_court_peace_pattern_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import { KENDRA_HOUSES, MALE_RASIS } from '../election-assessors/benefic-patterns';
import {
  COURT_PEACE_PATTERN_METADATA,
  aggregateCourtPeacePatternWindow,
  evaluateCourtPeacePattern,
} from '../election-assessors/court';

type SnapshotCase = (typeof oracle.snapshot_cases)[number];

function chart(caseData: SnapshotCase): ElectionChartSnapshot {
  const changes = ('overrides' in caseData ? caseData.overrides : {}) as Record<
    string,
    Partial<(typeof oracle.base_planets)[number]>
  >;
  const omissions = new Set<string>('remove' in caseData ? caseData.remove : []);
  const remaining = oracle.base_planets
    .filter(planet => !omissions.has(planet.name))
    .map(planet => ({ ...structuredClone(planet), ...changes[planet.name] }));
  const duplicateName = 'duplicate' in caseData ? caseData.duplicate : undefined;
  if (duplicateName) {
    const source = remaining.find(planet => planet.name === duplicateName);
    if (source) remaining.push(structuredClone(source));
  }
  return { planets: remaining } as ElectionChartSnapshot;
}

function outcome(caseData: SnapshotCase) {
  return evaluateCourtPeacePattern(chart(caseData), {
    houseFrameUncertain:
      'house_frame_uncertain' in caseData && caseData.house_frame_uncertain,
  });
}

describe('Court peace-pattern information', () => {
  test('records the selected grammar, direction, odd Rasis, and inform-only effect', () => {
    expect(oracle.fixture_kind).toBe('synthetic_contract_fixture');
    expect(oracle.source_golden).toBe(false);
    expect(COURT_PEACE_PATTERN_METADATA).toEqual(oracle.metadata);
    expect(KENDRA_HOUSES).toEqual([1, 4, 7, 10]);
    expect([...MALE_RASIS]).toEqual([
      'Mesha', 'Mithuna', 'Simha', 'Tula', 'Dhanu', 'Kumbha',
    ]);
    expect(COURT_PEACE_PATTERN_METADATA.event_policy.effect).toBe('inform');
    expect(COURT_PEACE_PATTERN_METADATA.event_policy.status).toBe('specified_unwired');
  });

  test.each(oracle.snapshot_cases)('$id', (caseData) => {
    expect(outcome(caseData).status).toBe(caseData.expected_status);
  });

  test('covers each OR arm independently and together', () => {
    const cases = new Map(oracle.snapshot_cases.map(item => [item.id, item]));
    expect(outcome(cases.get('kendra-arm-only')!).evidence[0])
      .toContain('Resolved natural-benefic witness: Guru (house 4).');
    expect(outcome(cases.get('male-rasi-aspect-arm-only')!).evidence.join(' '))
      .toContain('Guru in Mithuna receives full Graha Drishti from Shukra');
    const both = outcome(cases.get('both-arms')!).evidence.join(' ');
    expect(both).toContain('Kendra arm: Resolved');
    expect(both).toContain('Male-Rasi aspect arm: Resolved');
  });

  test('a resolved miss contains no adverse legal inference', () => {
    const miss = oracle.snapshot_cases.find(item => item.id === 'neither-arm-resolved')!;
    const text = outcome(miss).evidence.join(' ').toLowerCase();
    for (const word of ['conflict', 'victory', 'loss', 'settlement']) {
      expect(text).not.toContain(word);
    }
  });

  test.each(oracle.window_cases)('$id', (window) => {
    const cases = new Map(oracle.snapshot_cases.map(item => [item.id, item]));
    const samples = window.sample_case_ids.map(caseId => outcome(cases.get(caseId)!));
    const result = aggregateCourtPeacePatternWindow(samples, {
      localLagnaTransitionsComplete: window.coverage.local_lagna_transitions_complete,
      grahaRasiTransitionsComplete: window.coverage.graha_rasi_transitions_complete,
      chandraPhaseTransitionsComplete: window.coverage.chandra_phase_transitions_complete,
      budhaAssociationTransitionsComplete:
        window.coverage.budha_association_transitions_complete,
      fullAspectTransitionsComplete: window.coverage.full_aspect_transitions_complete,
      budgetExhausted: window.coverage.budget_exhausted,
    });
    expect(result.status).toBe(window.expected_status);
    if (result.status === 'fail') {
      expect(result.evidence.join(' ').toLowerCase()).toContain('no adverse inference');
    }
  });

  test('runtime-invalid chart and options fail closed', () => {
    expect(evaluateCourtPeacePattern(
      null as unknown as ElectionChartSnapshot,
    ).status).toBe('unknown');
    expect(evaluateCourtPeacePattern(
      chart(oracle.snapshot_cases[0]),
      null as unknown as { houseFrameUncertain?: boolean },
    ).status).toBe('unknown');
  });
});
