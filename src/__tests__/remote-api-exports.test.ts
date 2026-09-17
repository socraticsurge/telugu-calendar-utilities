import { expect, test } from 'vitest';
import * as birth from '../lib/birth-profile-api';
import * as election from '../lib/election-chart-api';
import * as chart from '../lib/chart-contracts';
import * as contracts from '../lib/remote-api/contracts';
import { localWallTimeToInstant } from '../lib/local-chart-time';

test('legacy public exports retain their shared runtime identity', () => {
  expect(birth.BirthProfileApiError).toBe(contracts.BirthProfileApiError);
  expect(election.ElectionChartApiError).toBe(contracts.ElectionChartApiError);
  expect(election.localWallTimeToInstant).toBe(localWallTimeToInstant);
  expect(birth.fixedGrahaFactsMatch).toBe(chart.fixedGrahaFactsMatch);
  expect(birth.roundedMoonMatchesBirthFacts).toBe(chart.roundedMoonMatchesBirthFacts);
  expect(birth.wholeSignHousesMatch).toBe(chart.wholeSignHousesMatch);
  expect(birth.isContractRoundedDegree).toBe(chart.isContractRoundedDegree);
  expect(birth.BIRTH_CHART_PLANET_NAMES).toBe(chart.BIRTH_CHART_PLANET_NAMES);
});

test('neutral civil-time errors remain recognizable through the legacy facade', () => {
  expect(() => localWallTimeToInstant('2026-11-01', 90, 'America/New_York'))
    .toThrow(election.ElectionChartApiError);
});
