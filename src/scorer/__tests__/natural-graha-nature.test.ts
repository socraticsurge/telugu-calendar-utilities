import { describe, expect, test } from 'vitest';

import fixture from '../../../tests/fixtures/natural_graha_nature_v1.json';
import rulesContract from '../../data/election-chart-rules.generated.json';
import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  NATURAL_GRAHA_NATURE_CONVENTION_ID,
  classifyNaturalGrahaNatures,
  evaluateExistentialBeneficHouseSet,
  evaluateForbiddenMaleficHouseSet,
} from '../election-assessors/graha-nature';

type PlanetOverride = Partial<ElectionChartSnapshot['planets'][number]>;
type Overrides = Record<string, PlanetOverride>;

function chart(overrides: Overrides = {}): ElectionChartSnapshot {
  const result = structuredClone(fixture.base_chart) as ElectionChartSnapshot;
  result.planets = result.planets.map(planet => ({
    ...planet,
    ...(overrides[planet.name] || {}),
  }));
  return result;
}

function invalidChart(mutation: (typeof fixture.invalid_cases)[number]['mutation']) {
  const result = chart();
  if (mutation.kind === 'remove') {
    result.planets = result.planets.filter(item => item.name !== mutation.planet);
    return result;
  }
  const planet = result.planets.find(item => item.name === mutation.planet);
  if (!planet) throw new Error(`Missing fixture planet ${mutation.planet}`);
  const mutable = planet as unknown as Record<string, unknown>;
  if (mutation.kind === 'rename') mutable.name = mutation.value;
  else mutable[mutation.field as string] = mutation.value;
  return result;
}

describe('natural-graha nature v1', () => {
  test('the TypeScript primitive consumes the generated convention contract', () => {
    const convention = rulesContract.conventions[
      NATURAL_GRAHA_NATURE_CONVENTION_ID
    ];

    expect(fixture.convention_id).toBe(NATURAL_GRAHA_NATURE_CONVENTION_ID);
    expect(convention).toEqual(expect.objectContaining({
      fixed_malefics: ['Surya', 'Kuja', 'Shani', 'Rahu', 'Ketu'],
      fixed_benefics: ['Guru', 'Shukra'],
      chandra_phase_guard_degrees: 0.02,
      phase_quantization_decimal_places: 10,
      phase_quantization_rounding: 'half_up_nonnegative',
      budha_association: 'same_sidereal_rashi',
      house_system: 'whole_sign',
    }));
    expect(new Set(convention.method_claims)).toEqual(new Set([
      'election_chart.natural_graha_nature.phaladeepika_2_27',
      'election_chart.natural_malefics.bphs_3_11_modern_witness',
      'election_chart.budha_same_sign_association_policy_v1',
      'election_chart.raman_180_degree_paksha_policy_v1',
      'election_chart.lunar_phase_boundary_guard_policy_v1',
      'election_chart.mean_node_policy_v1',
    ]));
  });

  test.each(fixture.classifier_cases)('$id', testCase => {
    const result = classifyNaturalGrahaNatures(
      chart(testCase.overrides as Overrides),
    );

    expect(result.complete).toBe(true);
    expect(result.natures).toEqual(expect.objectContaining(testCase.expected));
    expect(result.evidence).toHaveLength(2);
  });

  test.each(fixture.invalid_cases)('$id fails closed', testCase => {
    const result = classifyNaturalGrahaNatures(
      invalidChart(testCase.mutation),
    );

    expect(result.complete).toBe(false);
    expect(Object.keys(result.natures)).toEqual(rulesContract.vacancy_includes);
    expect(new Set(Object.values(result.natures))).toEqual(new Set(['unknown']));
    expect(result.evidence[0]).toContain('unavailable or invalid');
  });

  test.each(fixture.predicate_cases)('$id', testCase => {
    const input = chart(testCase.overrides as Overrides);
    const outcome = testCase.predicate === 'existential_benefic'
      ? evaluateExistentialBeneficHouseSet(input, testCase.houses)
      : evaluateForbiddenMaleficHouseSet(input, testCase.houses);

    expect(outcome.status).toBe(testCase.expected_status);
    expect(outcome.evidence.join(' ')).toContain(testCase.evidence_contains);
  });

  test.each([
    [], [0], [13], [true], '1', null,
  ])('malformed house set %j returns unknown', houses => {
    expect(evaluateExistentialBeneficHouseSet(
      chart(), houses as unknown as number[],
    ).status).toBe('unknown');
    expect(evaluateForbiddenMaleficHouseSet(
      chart(), houses as unknown as number[],
    ).status).toBe('unknown');
  });

  test('missing chart data keeps both predicates unknown', () => {
    const incomplete = chart();
    incomplete.planets.pop();

    expect(evaluateExistentialBeneficHouseSet(incomplete, [1]).status)
      .toBe('unknown');
    expect(evaluateForbiddenMaleficHouseSet(incomplete, [1]).status)
      .toBe('unknown');
  });
});

