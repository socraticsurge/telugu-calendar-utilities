import { describe, expect, test } from 'vitest';

import projection from '../../../tests/fixtures/election_chart_vidyarambha_projection.json';

import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  chartAssessorCompleteFor,
  evaluateElectionSnapshots,
} from '../election-chart-screening';


describe('Vidyarambha projection replay', () => {
  test('generated completion register distinguishes complete from partial assessors', () => {
    expect(chartAssessorCompleteFor('vidyarambha')).toBe(false);
    expect(chartAssessorCompleteFor('gold')).toBe(true);
    expect(chartAssessorCompleteFor('purchase')).toBe(false);
  });

  test('capture distinguishes externally anchored and local-only cases', () => {
    expect(projection.capture).toMatchObject({
      kind: 'deterministic_dasha_flow_http_contract_replay',
      retrieved_on: '2026-08-30',
      engine: {
        name: 'DashaFlow',
        version: '1.1.0',
        ayanamsha: 'Lahiri',
        ephemeris: 'moshier',
        node_convention: 'mean',
        house_system: 'whole_sign',
      },
    });
    expect(projection.capture.external_anchor.scope).toContain(
      'Only the first instant',
    );
    expect(projection.capture.local_gateway_contract.scope).toContain(
      'not externally published-page matches',
    );
    const external = new Set(projection.capture.external_anchor.cases);
    for (const testCase of projection.cases) {
      if (external.has(testCase.id)) {
        expect(testCase).toHaveProperty('source_url');
      } else {
        expect(testCase).not.toHaveProperty('source_url');
        expect(testCase.verification_scope).toBe(
          'local_gateway_projection_not_external_match',
        );
      }
    }
  });

  test.each(projection.cases)(
    'replays $id through the TypeScript assessor',
    testCase => {
      expect(testCase.charts.map(chart => chart.instant)).toEqual(
        testCase.request.instants,
      );
      const result = evaluateElectionSnapshots(
        'vidyarambha',
        testCase.charts as ElectionChartSnapshot[],
      );

      expect(result.outcomes.map(item => item.status)).toEqual(
        testCase.expected_statuses,
      );
      expect(result.rejected).toBe(testCase.rejected);
      expect(result.needsReview).toBe(testCase.needs_review);
      expect(result.preferencePasses).toBe(testCase.preference_passes);
      expect(result.stable).toBe(testCase.stable);
    },
  );
});
