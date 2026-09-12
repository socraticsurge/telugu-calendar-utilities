import { describe, expect, test } from 'vitest';
import oracle from '../../../tests/fixtures/election_chart_benefic_rasi_oracle.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  BENEFIC_RASI_CONVENTION_ID,
  evaluateBeneficRasi,
} from '../election-assessors/benefic-rasi';

type Case = {
  id?: string;
  rashi: string;
  lord?: string;
  status: 'pass' | 'fail' | 'unknown';
  overrides?: Record<string, Partial<ElectionChartSnapshot['planets'][number]>>;
  remove?: string;
};

function chart(testCase: Case): ElectionChartSnapshot {
  return {
    ...oracle.base_chart,
    planets: oracle.base_chart.planets
      .filter(planet => planet.name !== testCase.remove)
      .map(planet => ({
        ...planet,
        ...testCase.overrides?.[planet.name],
      })),
  } as ElectionChartSnapshot;
}

describe('benefic Rasi by resolved natural lord v1', () => {
  test('matches all twelve Rasis', () => {
    expect(oracle.convention_id).toBe(BENEFIC_RASI_CONVENTION_ID);
    for (const testCase of oracle.rasi_cases as Case[]) {
      const outcome = evaluateBeneficRasi(chart(testCase), testCase.rashi);
      expect(outcome.status, testCase.rashi).toBe(testCase.status);
      expect(outcome.evidence[0]).toContain(`owned by ${testCase.lord}`);
    }
  });

  test('matches conditional-nature and invalid-input edges', () => {
    for (const testCase of oracle.nature_cases as Case[]) {
      expect(
        evaluateBeneficRasi(chart(testCase), testCase.rashi).status,
        testCase.id,
      ).toBe(testCase.status);
    }
  });
});
