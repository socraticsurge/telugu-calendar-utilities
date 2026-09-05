import { describe, expect, test } from 'vitest';

import oracle from '../../../tests/fixtures/karnavedha_daylight_drikpanchang_oracle.json';
import {
  KARNAVEDHA_DAYLIGHT_POLICY_ID,
  KARNAVEDHA_NAKSHATRA_RULE_ID,
  KARNAVEDHA_TITHI_RULE_ID,
  evaluateConfiguredKarnavedhaDaylight,
  evaluateKarnavedhaDaylight,
  type KarnavedhaDaylightInput,
} from '../election-assessors/karnavedha-daylight';

function minuteParts(value: string, baseDate: string): { time: string; flag: string | null } {
  const match = value.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/);
  if (!match) throw new Error(`Invalid fixture timestamp: ${value}`);
  const delta = (Date.parse(`${match[1]}T00:00:00Z`) - Date.parse(`${baseDate}T00:00:00Z`))
    / 86_400_000;
  return {
    time: match[2],
    flag: delta === 1 ? '+1' : delta === -1 ? '-1' : null,
  };
}

function inputFromFixture(testCase: (typeof oracle.cases)[number]): KarnavedhaDaylightInput {
  const tithi = minuteParts(testCase.drikpanchang.tithi_transition, testCase.date);
  const nakshatra = minuteParts(
    testCase.drikpanchang.nakshatra_transition,
    testCase.date,
  );
  return {
    sunrise: minuteParts(testCase.drikpanchang.sunrise, testCase.date).time,
    sunset: minuteParts(testCase.drikpanchang.sunset, testCase.date).time,
    tithi: {
      name: 'Fixture Tithi',
      start: '00:00',
      sflag: null,
      end: tithi.time,
      eflag: tithi.flag,
    },
    nakshatra: {
      name: 'Fixture Nakshatra',
      start: '00:00',
      sflag: null,
      end: nakshatra.time,
      eflag: nakshatra.flag,
    },
  };
}

function status(result: ReturnType<typeof evaluateKarnavedhaDaylight>, ruleId: string) {
  return result.outcomes.find(item => item.ruleId === ruleId)?.status;
}

describe('Karnavedha daylight policy', () => {
  test('uses the same named policy and all eight external fixture categories', () => {
    expect(oracle.policy_id).toBe(KARNAVEDHA_DAYLIGHT_POLICY_ID);
    expect(oracle.comparison.tolerance_seconds).toBe(120);
    expect(oracle.comparison.maximum_observed_delta_seconds).toBeLessThanOrEqual(120);

    for (const testCase of oracle.cases) {
      const result = evaluateKarnavedhaDaylight(inputFromFixture(testCase));
      expect(status(result, KARNAVEDHA_TITHI_RULE_ID), testCase.id)
        .toBe(testCase.expected.tithi);
      expect(status(result, KARNAVEDHA_NAKSHATRA_RULE_ID), testCase.id)
        .toBe(testCase.expected.nakshatra);
      expect(result.admissible, testCase.id).toBe(
        Object.values(testCase.expected).every(value => value === 'pass'),
      );
    }
  });

  test('uses half-open daylight semantics and fails closed at minute ambiguity', () => {
    const exactSunset = evaluateKarnavedhaDaylight({
      sunrise: '06:00', sunset: '18:00',
      tithi: { name: 'Tithi A', start: '05:00', end: '18:00' },
      nakshatra: { name: 'Star A', start: '05:00', end: '18:01' },
    });
    expect(status(exactSunset, KARNAVEDHA_TITHI_RULE_ID)).toBe('unknown');
    expect(status(exactSunset, KARNAVEDHA_NAKSHATRA_RULE_ID)).toBe('pass');
    expect(exactSunset.admissible).toBe(false);

    const interior = evaluateKarnavedhaDaylight({
      sunrise: '06:00', sunset: '18:00',
      tithi: { name: 'Tithi A', start: '05:00', end: '17:59' },
      nakshatra: { name: 'Star A', start: '05:00', end: '18:01' },
    });
    expect(status(interior, KARNAVEDHA_TITHI_RULE_ID)).toBe('fail');
    expect(interior.rejected).toBe(true);
  });

  test.each([
    ['missing Tithi policy', undefined, KARNAVEDHA_DAYLIGHT_POLICY_ID],
    ['missing Nakshatra policy', KARNAVEDHA_DAYLIGHT_POLICY_ID, undefined],
    ['both policies missing', undefined, undefined],
    ['unsupported Tithi policy', 'unsupported-v2', KARNAVEDHA_DAYLIGHT_POLICY_ID],
    ['unsupported Nakshatra policy', KARNAVEDHA_DAYLIGHT_POLICY_ID, 'unsupported-v2'],
    ['malformed policy type', true, KARNAVEDHA_DAYLIGHT_POLICY_ID],
  ])('%s fails closed before the panel can admit a day', (
    _label, tithiPolicy, nakshatraPolicy,
  ) => {
    const result = evaluateConfiguredKarnavedhaDaylight(
      inputFromFixture(oracle.cases[0]),
      tithiPolicy,
      nakshatraPolicy,
    );

    expect(result.outcomes.map(item => item.status)).toEqual([
      'unknown', 'unknown',
    ]);
    expect(result.outcomes.every(item => item.evidence.some(detail =>
      detail.includes('missing or unsupported')))).toBe(true);
    expect(result).toEqual(expect.objectContaining({
      rejected: false,
      needsReview: true,
      admissible: false,
    }));
  });

  test.each([
    ['missing limb', { sunrise: '06:00', sunset: '18:00', tithi: null, nakshatra: null }],
    ['invalid time', {
      sunrise: '06:00', sunset: '18:00',
      tithi: { name: 'A', start: '05:00', end: 'noon' },
      nakshatra: { name: 'B', start: '05:00', end: '19:00' },
    }],
    ['span not active at sunrise', {
      sunrise: '06:00', sunset: '18:00',
      tithi: { name: 'A', start: '06:01', end: '19:00' },
      nakshatra: { name: 'B', start: '05:00', end: '19:00' },
    }],
    ['unsupported day flag', {
      sunrise: '06:00', sunset: '18:00',
      tithi: { name: 'A', start: '05:00', end: '19:00', eflag: '+2' },
      nakshatra: { name: 'B', start: '05:00', end: '19:00' },
    }],
  ] as const)('$0 returns unknown rather than admitting', (_label, input) => {
    const result = evaluateKarnavedhaDaylight(input as KarnavedhaDaylightInput);
    expect(result.outcomes.some(item => item.status === 'unknown')).toBe(true);
    expect(result.needsReview).toBe(true);
    expect(result.admissible).toBe(false);
  });
});
