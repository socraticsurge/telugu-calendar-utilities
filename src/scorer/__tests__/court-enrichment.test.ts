import { describe, expect, test, vi } from 'vitest';

import type {
  ElectionChartDerivation,
  ElectionChartRequest,
  ElectionChartSnapshot,
} from '../../lib/election-chart-api';
import {
  enrichElectionChartSlots,
  type EnrichableMuhurtamSlot,
} from '../election-chart-enrichment';
import { inferCourtTransitionCoverage } from '../court-transition-coverage';

const PLANETS = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;

const RASHIS = [
  'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
  'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
];

const HOUSES = {
  Surya: 4, Chandra: 7, Kuja: 1, Budha: 7, Guru: 1,
  Shukra: 2, Shani: 10, Rahu: 11, Ketu: 5,
};

function courtSnapshot(instant: string, lagnaRashi = 'Mesha'): ElectionChartSnapshot {
  const lagnaIndex = RASHIS.indexOf(lagnaRashi);
  return {
    instant,
    lagna: { rashi: lagnaRashi, degree: 12.5 },
    planets: PLANETS.map((name, index) => ({
      name,
      rashi: RASHIS[(lagnaIndex + HOUSES[name] - 1) % 12],
      degree: name === 'Chandra' ? 20 : name === 'Surya' ? 10 : index + 8,
      house: HOUSES[name],
      retrograde: name === 'Rahu' || name === 'Ketu',
    })),
  };
}

function slot(lagnaRashi = 'Mesha'): EnrichableMuhurtamSlot {
  return {
    isoDate: '2026-09-08',
    s0: 420,
    e0: 441,
    score: 12,
    tier: 'Excellent',
    dayDosha: null,
    reasonGroups: {},
    chartCheckMinutes: [420, 430, 440],
    chartCheckLagnas: [lagnaRashi, lagnaRashi, lagnaRashi],
    chartBoundarySupported: true,
    chartBoundaryNeedsReview: false,
  };
}

const LOCATION = {
  latitude: 17.385,
  longitude: 78.4867,
  timezone: 'Asia/Kolkata',
};

function response(
  request: ElectionChartRequest,
  lagnaRashi = 'Mesha',
): ElectionChartDerivation {
  return {
    contractVersion: '1.0',
    engine: {
      name: 'DashaFlow', version: '1.2.3', ayanamsha: 'Lahiri',
      ephemeris: 'swiss', nodeConvention: 'mean',
    },
    houseSystem: 'whole_sign',
    location: request.location,
    charts: request.instants.map(instant => courtSnapshot(instant, lagnaRashi)),
  };
}

describe('Court browser enrichment', () => {
  test('infers complete bounded coverage and resolves all five clauses', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const result = await enrichElectionChartSlots([slot()], {
      activity: 'court', system: 'drik', location: LOCATION, derive,
    });

    expect(result.state).toBe('screened');
    expect(result.reviewGatedCount).toBe(0);
    expect(result.chartRemovedCount).toBe(0);
    expect(result.slots[0].chartScreening?.outcomes).toHaveLength(5);
    expect(result.slots[0].chartScreening?.needsReview).toBe(false);
    expect(Object.keys(derive.mock.calls[0][0]).sort()).toEqual(['instants', 'location']);
  });

  test('resolves the non-Mesha D1 alternative only through guarded Mesha D9', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) =>
      response(request, 'Vrishabha'));
    const result = await enrichElectionChartSlots([slot('Vrishabha')], {
      activity: 'court', system: 'drik', location: LOCATION, derive,
    });

    expect(result.slots).toHaveLength(1);
    expect(result.slots[0].chartScreening?.outcomes[0]).toEqual(
      expect.objectContaining({
        ruleId: 'court.mesha-lagna-or-navamsa', status: 'pass',
      }),
    );
  });

  test('keeps alias parity and fails closed on unsupported or unavailable paths', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const court = await enrichElectionChartSlots([slot()], {
      activity: 'court', system: 'drik', location: LOCATION, derive,
    });
    const litigation = await enrichElectionChartSlots([slot()], {
      activity: 'litigation', system: 'drik', location: LOCATION, derive,
    });
    expect(litigation.slots[0].chartScreening).toEqual(
      court.slots[0].chartScreening,
    );

    const unsupported = await enrichElectionChartSlots([slot()], {
      activity: 'court', system: 'vakya', location: LOCATION, derive,
    });
    expect(unsupported.state).toBe('unsupported-system');

    const unavailable = await enrichElectionChartSlots([slot()], {
      activity: 'court', system: 'drik', location: LOCATION,
      activationFlag: 'false', derive,
    });
    expect(unavailable.state).toBe('disabled');
    expect(unavailable.reviewGatedCount).toBe(1);
  });

  test('marks cadence gaps and hidden transition risk incomplete', () => {
    const charts = [
      courtSnapshot('2026-09-08T05:30:00.000Z'),
      courtSnapshot('2026-09-08T05:45:00.000Z'),
    ];
    const result = inferCourtTransitionCoverage(charts, ['Mesha', 'Mesha'], true);
    expect(result.localLagnaTransitionsComplete).toBe(true);
    expect(result.grahaRasiTransitionsComplete).toBe(false);
    expect(result.lagnaNavamsaTransitionsComplete).toBe(false);
    expect(result.chandraPhaseTransitionsComplete).toBe(false);
  });
});
