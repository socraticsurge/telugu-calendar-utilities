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

const PLANETS = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;

const RASHIS = {
  Surya: 'Mesha', Chandra: 'Vrishabha', Kuja: 'Mithuna', Budha: 'Karka',
  Guru: 'Simha', Shukra: 'Kanya', Shani: 'Tula', Rahu: 'Vrischika', Ketu: 'Dhanu',
} as const;

function chart(instant: string): ElectionChartSnapshot {
  return {
    instant,
    lagna: { rashi: 'Mesha', degree: 12 },
    planets: PLANETS.map((name, index) => ({
      name,
      rashi: RASHIS[name],
      degree: 10 + index,
      house: index + 1,
      retrograde: name === 'Rahu' || name === 'Ketu',
    })),
  };
}

describe('Borrowing chart enrichment privacy and location parity', () => {
  test.each([
    ['Hyderabad', '2026-09-12', { latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' }],
    ['New York', '2026-11-02', { latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' }],
  ])('sends only location and instants for %s', async (_label, isoDate, location) => {
    const slot: EnrichableMuhurtamSlot = {
      isoDate,
      s0: 420,
      e0: 430,
      score: 10,
      tier: 'Good',
      dayDosha: null,
      reasonGroups: {},
      chartCheckMinutes: [420, 429],
      chartCheckLagnas: ['Mesha', 'Mesha'],
    };
    const derive = vi.fn(async (request: ElectionChartRequest): Promise<ElectionChartDerivation> => ({
      contractVersion: '1.0',
      engine: {
        name: 'DashaFlow', version: '1.2.3', ayanamsha: 'Lahiri',
        ephemeris: 'swiss', nodeConvention: 'mean',
      },
      houseSystem: 'whole_sign',
      location: request.location,
      charts: request.instants.map(chart),
    }));

    await enrichElectionChartSlots([slot], {
      activity: 'borrowing_money',
      system: 'drik',
      location,
      derive,
      personalParticipant: {
        id: 'private-profile-id',
        name: 'Private borrower',
        nakshatra: 'Rohini',
        janmaRashi: 'Vrishabha',
        janmaLagna: 'Karka',
      },
    });

    const request = derive.mock.calls[0][0];
    expect(Object.keys(request).sort()).toEqual(['instants', 'location']);
    expect(JSON.stringify(request)).not.toMatch(
      /Private borrower|private-profile-id|Rohini|Vrishabha|Karka|business|amount|lender/i,
    );
    expect(request.location).toEqual(location);
    expect(request.instants).toHaveLength(2);
  });
});
