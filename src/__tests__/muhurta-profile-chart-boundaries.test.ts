import { describe, expect, test, vi } from 'vitest';
import type { ElectionChartRequest, ElectionChartSnapshot } from '../lib/election-chart-api';
import { enrichElectionChartSlots, type EnrichableMuhurtamSlot } from '../scorer/election-chart-enrichment';
import { usePanelFixture, type PanelFixture } from './muhurta-profile/fixtures';

let panel: PanelFixture['panel'];

usePanelFixture(fixture => {
  ({ panel } = fixture);
});

function sydneyChartFixture() {
  const day = {
    sunrise: '06:49',
    lagna0: 5,
    transitions: Array.from({ length: 12 }, (_, index) => [
      466 + index * 80,
      (6 + index) % 12,
    ]),
    cycleEnd: 1440,
  };
  const buildSlot = (
    startMinute: number,
    endMinute: number,
  ): EnrichableMuhurtamSlot => {
    const minutes = panel.muChartCheckMinutes(day, startMinute, endMinute);
    return {
      isoDate: '2026-05-28',
      s0: startMinute,
      e0: endMinute,
      score: 12,
      tier: 'Excellent',
      dayDosha: null,
      reasonGroups: {},
      chartCheckMinutes: minutes,
      chartCheckLagnas: panel.muChartLagnasForMinutes(day, minutes),
      chartBoundarySupported: panel.muValidLagnaDayData(day),
      chartBoundaryNeedsReview: panel.muChartBoundaryNeedsReview(
        day, startMinute, endMinute,
      ),
    };
  };
  const planets = [
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
    'Shukra', 'Shani', 'Rahu', 'Ketu',
  ];
  const derive = vi.fn(async (request: ElectionChartRequest) => ({
    contractVersion: '1.0' as const,
    engine: {
      name: 'DashaFlow', version: '1.1.0', ayanamsha: 'Lahiri',
      ephemeris: 'swiss' as const, nodeConvention: 'mean' as const,
    },
    houseSystem: 'whole_sign' as const,
    location: request.location,
    charts: request.instants.map((instant, index): ElectionChartSnapshot => ({
      instant,
      // The sidecar changes two minutes after the canonical 14:35 boundary.
      lagna: { rashi: index < request.instants.length - 1 ? 'Kanya' : 'Tula', degree: 29.5 },
      planets: planets.map((name, planetIndex) => ({
        name,
        rashi: name === 'Kuja' ? 'Vrishabha' : 'Kanya',
        degree: planetIndex + 0.25,
        house: 12,
        retrograde: name === 'Rahu' || name === 'Ketu',
      })),
    })),
  }));
  return { buildSlot, derive };
}

describe('Muhurtam chart boundary evidence', () => {
  test('samples both sides of every Lagna transition inside a slot', () => {
    const day = {
      sunrise: '06:00',
      lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [70, 6],
        [95, 7], [200, 8], [300, 9], [400, 10], [500, 11], [600, 0],
      ],
      cycleEnd: 1440,
    };
    const minutes = panel.muChartCheckMinutes(day, 420, 470);
    expect(minutes).toEqual([
      420, 429, 430, 431, 440, 450, 454, 455, 456, 460, 469,
    ]);
    expect(panel.muChartLagnasForMinutes(day, minutes)).toEqual([
      'Kanya', 'Kanya', 'Tula', 'Tula', 'Tula',
      'Tula', 'Tula', 'Vrischika', 'Vrischika', 'Vrischika', 'Vrischika',
    ]);
    expect(panel.muChartBoundaryNeedsReview(day, 420, 470)).toBe(false);
    expect(panel.muChartBoundaryNeedsReview(day, 430, 470)).toBe(true);
    expect(panel.muChartBoundaryNeedsReview(day, 420, 430)).toBe(true);
  });

  test('retains the Hyderabad single-minute boundary evidence', () => {
    const hyderabadDay = {
      sunrise: '06:49',
      lagna0: 10,
      transitions: Array.from({ length: 12 }, (_, index) => [
        210 + index * 100,
        (11 + index) % 12,
      ]),
      cycleEnd: 1440,
    };
    const hyderabadMinutes = panel.muChartCheckMinutes(hyderabadDay, 619, 620);
    expect(hyderabadMinutes).toEqual([619]);
    expect(panel.muChartLagnasForMinutes(hyderabadDay, hyderabadMinutes))
      .toEqual(['Meena']);
    expect(panel.muChartBoundaryNeedsReview(hyderabadDay, 619, 620)).toBe(true);
  });

  test('caps the Sydney boundary-edge candidate conservatively', async () => {
    const { buildSlot, derive } = sydneyChartFixture();
    const edge = buildSlot(875, 876);
    expect(edge.chartCheckLagnas).toEqual(['Tula']);
    expect(edge.chartBoundaryNeedsReview).toBe(true);
    const edgeResult = await enrichElectionChartSlots([edge], {
      activity: 'wedding', system: 'drik',
      location: { latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
      derive,
    });
    expect(edgeResult.slots).toHaveLength(1);
    expect(edgeResult.slots[0].tier).toBe('Good');
    expect(edgeResult.slots[0].chartScreening).toEqual(expect.objectContaining({
      boundaryConventionUncertain: true,
      rejected: false,
      needsReview: true,
    }));
  });

  test('rejects the Sydney full-band candidate on chart evidence', async () => {
    const { buildSlot, derive } = sydneyChartFixture();
    const fullBand = buildSlot(869, 882);
    expect(fullBand.chartBoundaryNeedsReview).toBe(false);
    expect(new Set(fullBand.chartCheckLagnas)).toEqual(new Set(['Kanya', 'Tula']));
    const fullResult = await enrichElectionChartSlots([fullBand], {
      activity: 'wedding', system: 'drik',
      location: { latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
      derive,
    });
    expect(fullResult.slots).toEqual([]);
    expect(fullResult.chartRemovedCount).toBe(1);
  });

  test.each([
    null,
    { sunrise: '06:00', lagna0: 0, transitions: [], cycleEnd: 1440 },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [105, 0],
      ],
      cycleEnd: 1440,
    },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 2],
      ],
      cycleEnd: 1440,
    },
  ])('rejects malformed Lagna day evidence %#', malformed => {
    expect(panel.muValidLagnaDayData(malformed)).toBe(false);
    expect(panel.muChartCheckMinutes(malformed, 420, 470)).toEqual([420, 469]);
    expect(panel.muChartLagnasForMinutes(malformed, [420, 469])).toBeNull();
    expect(panel.muChartBoundaryNeedsReview(malformed, 420, 470)).toBe(true);
  });

  test('accepts a validated second-cycle tail from current generated data', () => {
    const extended = {
      sunrise: '06:00',
      lagna0: 3,
      transitions: Array.from({ length: 24 }, (_, index) => [
        (index + 1) * 55,
        (4 + index) % 12,
      ]),
      cycleEnd: 2880,
    };
    expect(panel.muValidLagnaDayData(extended)).toBe(true);
  });

  test('accepts the published Hyderabad terminal transition at exclusive cycle end', () => {
    const publishedHyderabadDay = {
      date: '2026-09-17',
      sunrise: '06:04',
      guruCombust: false,
      shukraCombust: false,
      lagna0: 4,
      transitions: [
        [4, 5], [129, 6], [259, 7], [393, 8], [519, 9],
        [630, 10], [728, 11], [823, 0], [928, 1], [1049, 2],
        [1181, 3], [1313, 4], [1440, 5],
      ],
      cycleEnd: 1440,
    };

    expect(panel.muValidLagnaDayData(publishedHyderabadDay)).toBe(true);
    expect(panel.muChartLagnasForMinutes(publishedHyderabadDay, [364, 367, 368]))
      .toEqual(['Simha', 'Simha', 'Kanya']);
    const cycleEndMinute = 364 + publishedHyderabadDay.cycleEnd;
    expect(panel.muChartLagnasForMinutes(
      publishedHyderabadDay, [cycleEndMinute - 10, cycleEndMinute - 1],
    )).toEqual(['Simha', 'Simha']);
    expect(panel.muChartLagnasForMinutes(
      publishedHyderabadDay, [cycleEndMinute],
    )).toBeNull();
    expect(panel.muChartLagnasForMinutes(
      publishedHyderabadDay, [cycleEndMinute - 1, cycleEndMinute],
    )).toBeNull();
    expect(panel.muChartCheckMinutes(
      publishedHyderabadDay, cycleEndMinute - 10, cycleEndMinute,
    )).toEqual([cycleEndMinute - 10, cycleEndMinute - 1]);
    expect(panel.muChartBoundaryNeedsReview(
      publishedHyderabadDay, cycleEndMinute - 10, cycleEndMinute,
    )).toBe(true);
  });

  test('accepts a published Sydney second-cycle terminal transition', () => {
    const transitionOffsets = [
      5, 84, 174, 286, 422, 567, 710, 853, 997, 1139, 1261, 1359,
      1441, 1520, 1610, 1723, 1859, 2003, 2146, 2289, 2433, 2575,
      2697, 2795, 2877,
    ];
    const publishedSydneyDay = {
      date: '2026-09-17',
      sunrise: '05:52',
      lagna0: 4,
      transitions: transitionOffsets.map((offset, index) => [
        offset, (5 + index) % 12,
      ]),
      cycleEnd: 2877,
    };

    expect(panel.muValidLagnaDayData(publishedSydneyDay)).toBe(true);
  });

  test.each([
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 0],
        [1440, 1], [1441, 2],
      ],
      cycleEnd: 1440,
    },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 0],
        [1440, 3],
      ],
      cycleEnd: 1440,
    },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 0],
        [1441, 1],
      ],
      cycleEnd: 1440,
    },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [0, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 0],
      ],
      cycleEnd: 1440,
    },
  ])('rejects invalid terminal or post-cycle Lagna transitions %#', malformed => {
    expect(panel.muValidLagnaDayData(malformed)).toBe(false);
  });

  test('accepts a first transition rounded to the sunrise minute', () => {
    const roundedAtSunrise = {
      sunrise: '06:00',
      lagna0: 3,
      transitions: Array.from({ length: 13 }, (_, index) => [
        index * 60,
        (4 + index) % 12,
      ]),
      cycleEnd: 1440,
    };
    expect(panel.muValidLagnaDayData(roundedAtSunrise)).toBe(true);
    expect(panel.muChartCheckMinutes(roundedAtSunrise, 360, 390)).toEqual([
      360, 361, 370, 380, 389,
    ]);
    expect(panel.muChartBoundaryNeedsReview(roundedAtSunrise, 360, 390)).toBe(true);
  });

});
