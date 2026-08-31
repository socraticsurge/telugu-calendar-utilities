import { describe, expect, test, vi } from 'vitest';

import type {
  ElectionChartDerivation,
  ElectionChartRequest,
  ElectionChartSnapshot,
} from '../../lib/election-chart-api';
import { ElectionChartApiError } from '../../lib/election-chart-api';
import { NAKSHATRA_NAMES, RASI_NAMES } from '../../data/rasis';
import {
  enrichElectionChartSlots,
  projectCanonicalWholeSignHouses,
  type EnrichableMuhurtamSlot,
} from '../election-chart-enrichment';

const PLANETS = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;

function snapshot(
  instant: string,
  kujaHouse = 2,
  options: { chandraRashi?: string; lagnaRashi?: string } = {},
): ElectionChartSnapshot {
  const lagnaRashi = options.lagnaRashi || 'Mesha';
  const lagnaIndex = RASI_NAMES.indexOf(lagnaRashi);
  return {
    instant,
    lagna: { rashi: lagnaRashi, degree: 12.5 },
    planets: PLANETS.map((name, index) => {
      const house = name === 'Kuja' ? kujaHouse : 1;
      return {
      name,
      rashi: name === 'Chandra' && options.chandraRashi
        ? options.chandraRashi
        : RASI_NAMES[(lagnaIndex + house - 1) % RASI_NAMES.length],
      degree: index + 0.25,
      house,
      retrograde: name === 'Rahu' || name === 'Ketu',
      };
    }),
  };
}

function slots(count: number): EnrichableMuhurtamSlot[] {
  return Array.from({ length: count }, (_, index) => {
    const s0 = 7 * 60 + (index % 8) * 50;
    const e0 = s0 + 48;
    return {
      isoDate: `2026-09-${String(8 + Math.floor(index / 8)).padStart(2, '0')}`,
      s0,
      e0,
      score: 20 - index,
      tier: index < 6 ? 'Excellent' : 'Good',
      dayDosha: null,
      reasonGroups: {},
      chartCheckMinutes: [s0, e0 - 1],
      chartCheckLagnas: ['Mesha', 'Mesha'],
    };
  });
}

function response(request: ElectionChartRequest, rejectedSlotIndexes = new Set<number>()): ElectionChartDerivation {
  return {
    contractVersion: '1.0',
    engine: {
      name: 'DashaFlow', version: '1.2.3', ayanamsha: 'Lahiri',
      ephemeris: 'swiss', nodeConvention: 'mean',
    },
    houseSystem: 'whole_sign',
    location: request.location,
    charts: request.instants.map((instant, index) =>
      snapshot(instant, rejectedSlotIndexes.has(Math.floor(index / 2)) ? 8 : 2)),
  };
}

const LOCATION = { latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' };

describe('bounded election-chart enrichment', () => {
  test('recomputes every Whole Sign house in the canonical Lagna frame', () => {
    const raw = snapshot('2026-09-08T05:30:00.000Z', 8, { lagnaRashi: 'Kanya' });
    raw.planets = raw.planets.map(planet => ({ ...planet, house: 12 }));
    const projected = projectCanonicalWholeSignHouses(raw, 'Tula');
    expect(projected.lagna.rashi).toBe('Kanya');
    expect(projected.planets.map(planet => planet.house)).toEqual(
      projected.planets.map(planet => {
        const planetIndex = [
          'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
          'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
        ].indexOf(planet.rashi);
        return ((planetIndex - 6 + 12) % 12) + 1;
      }),
    );
    expect(projected.planets.map(planet => planet.house))
      .not.toEqual(Array.from({ length: 9 }, () => 12));
  });

  test('uses the canonical Hyderabad Meena frame at the documented 10:19 boundary', async () => {
    const base = slots(1);
    base[0].isoDate = '2026-01-15';
    base[0].s0 = 619;
    base[0].e0 = 620;
    base[0].chartCheckMinutes = [619];
    base[0].chartCheckLagnas = ['Meena'];
    const derive = vi.fn(async (request: ElectionChartRequest) => {
      const chart = snapshot(request.instants[0], 2, { lagnaRashi: 'Kumbha' });
      chart.planets = chart.planets.map(planet => planet.name === 'Ketu'
        ? { ...planet, rashi: 'Simha', house: 7 }
        : { ...planet, rashi: 'Mesha', house: 3 });
      return { ...response(request), charts: [chart] };
    });
    const result = await enrichElectionChartSlots(base, {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.slots).toHaveLength(1);
    expect(result.chartRemovedCount).toBe(0);
    expect(result.slots[0].chartScreening?.outcomes).toContainEqual(
      expect.objectContaining({ ruleId: 'wedding.house-7-vacant', status: 'pass' }),
    );
  });

  test('uses the canonical Sydney Tula frame for travel and purchase boundary facts', async () => {
    const boundarySlot = slots(1)[0];
    boundarySlot.isoDate = '2026-05-28';
    boundarySlot.s0 = 875;
    boundarySlot.e0 = 876;
    boundarySlot.chartCheckMinutes = [875];
    boundarySlot.chartCheckLagnas = ['Tula'];
    const derive = vi.fn(async (request: ElectionChartRequest) => {
      const chart = snapshot(request.instants[0], 8, { lagnaRashi: 'Kanya' });
      chart.planets = chart.planets.map(planet => {
        if (planet.name === 'Chandra' || planet.name === 'Shukra') {
          return { ...planet, rashi: 'Tula', house: 2 };
        }
        return { ...planet, rashi: 'Mesha', house: planet.name === 'Kuja' ? 8 : 9 };
      });
      return { ...response(request), charts: [chart] };
    });
    const travel = await enrichElectionChartSlots([boundarySlot], {
      activity: 'travel', system: 'drik', location: LOCATION, derive,
      personalParticipant: {
        id: 'traveller', name: 'Traveller', nakshatra: 'Rohini',
        janmaRashi: 'Vrishabha', janmaLagna: 'Vrishabha',
      },
    });
    expect(travel.chartRemovedCount).toBe(0);
    expect(travel.slots).toHaveLength(1);
    expect(travel.slots[0].chartScreening?.outcomes).toContainEqual(
      expect.objectContaining({ ruleId: 'travel.kuja-not-8', status: 'pass' }),
    );

    const purchase = await enrichElectionChartSlots([boundarySlot], {
      activity: 'purchase', system: 'drik', location: LOCATION, derive,
    });
    expect(purchase.slots).toHaveLength(1);
    expect(purchase.slots[0].chartScreening?.preferencePasses).toBe(2);
  });

  test('does not claim screening when there are no candidates', async () => {
    const derive = vi.fn();
    const result = await enrichElectionChartSlots([], {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.state).toBe('not-run');
    expect(result.screenedCount).toBe(0);
    expect(derive).not.toHaveBeenCalled();
  });

  test('does not call the service when an activity has no deterministic rules', async () => {
    const derive = vi.fn();
    const result = await enrichElectionChartSlots(slots(12), {
      activity: 'gold', system: 'drik', location: LOCATION, derive,
    });
    expect(result.state).toBe('manual-only');
    expect(result.slots).toHaveLength(10);
    expect(derive).not.toHaveBeenCalled();
  });

  test('does not blend a Drik/Lahiri chart into a non-Drik search', async () => {
    const derive = vi.fn();
    const result = await enrichElectionChartSlots(slots(12), {
      activity: 'wedding', system: 'vakya', location: LOCATION, derive,
    });
    expect(result.state).toBe('unsupported-system');
    expect(derive).not.toHaveBeenCalled();
  });

  test('uses at most 24 instants per request and refills rejected results', async () => {
    let call = 0;
    const derive = vi.fn(async (request: ElectionChartRequest) => {
      call += 1;
      expect(request.instants.length).toBeLessThanOrEqual(24);
      return response(request, call === 1 ? new Set([0, 1, 2]) : new Set());
    });
    const result = await enrichElectionChartSlots(slots(18), {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.state).toBe('screened');
    expect(result.slots).toHaveLength(10);
    expect(result.removedCount).toBe(3);
    expect(derive).toHaveBeenCalledTimes(2);
  });

  test('shares one deadline across every request in a search', async () => {
    let now = 1_000;
    const clock = vi.spyOn(Date, 'now').mockImplementation(() => now);
    let call = 0;
    const derive = vi.fn(async (
      request: ElectionChartRequest,
      _options?: { timeoutMs?: number },
    ) => {
      call += 1;
      if (call === 1) now += 15_000;
      return response(request, call === 1 ? new Set([0, 1, 2]) : new Set());
    });
    try {
      const result = await enrichElectionChartSlots(slots(18), {
        activity: 'wedding', system: 'drik', location: LOCATION, derive,
        screeningTimeoutMs: 20_000,
      });
      expect(result.state).toBe('screened');
      expect(derive).toHaveBeenCalledTimes(2);
      expect(derive.mock.calls[0][1]?.timeoutMs).toBe(20_000);
      expect(derive.mock.calls[1][1]?.timeoutMs).toBe(5_000);
    } finally {
      clock.mockRestore();
    }
  });

  test('stops instead of starting another request after the search deadline', async () => {
    let now = 1_000;
    const clock = vi.spyOn(Date, 'now').mockImplementation(() => now);
    const derive = vi.fn(async (request: ElectionChartRequest) => {
      now += 20_001;
      return response(request, new Set([0, 1, 2]));
    });
    try {
      const result = await enrichElectionChartSlots(slots(18), {
        activity: 'wedding', system: 'drik', location: LOCATION, derive,
        screeningTimeoutMs: 20_000,
      });
      expect(result.state).toBe('unavailable');
      expect(derive).toHaveBeenCalledTimes(1);
      expect(result.message).toMatch(/temporarily unavailable/);
    } finally {
      clock.mockRestore();
    }
  });

  test('checks an interior Lagna-transition state and rejects a hidden failure', async () => {
    const base = slots(1);
    base[0].chartCheckMinutes = [420, 439, 440, 441, 467];
    base[0].chartCheckLagnas = ['Mesha', 'Mesha', 'Mesha', 'Mesha', 'Mesha'];
    const derive = vi.fn(async (request: ElectionChartRequest) => ({
      ...response(request),
      charts: request.instants.map((instant, index) =>
        snapshot(instant, index === 2 ? 8 : 2)),
    }));
    const result = await enrichElectionChartSlots(base, {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
      boundarySupportAvailable: true,
    });
    expect(derive.mock.calls[0][0].instants).toHaveLength(5);
    expect(result.slots).toEqual([]);
    expect(result.chartRemovedCount).toBe(1);
  });

  test('fails the whole enrichment closed when a sample lacks canonical Lagna evidence', async () => {
    const base = slots(1);
    base[0].chartCheckLagnas = null;
    const derive = vi.fn();
    const result = await enrichElectionChartSlots(base, {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
      boundarySupportAvailable: true,
    });
    expect(result.state).toBe('unavailable');
    expect(result.slots[0].tier).toBe('Good');
    expect(derive).not.toHaveBeenCalled();
  });

  test('review-gates a convention-ambiguous boundary edge instead of inventing a house rejection', async () => {
    const base = slots(1);
    base[0].chartBoundaryNeedsReview = true;
    const derive = vi.fn(async (request: ElectionChartRequest) => ({
      ...response(request),
      charts: request.instants.map(instant => snapshot(instant, 8)),
    }));
    const result = await enrichElectionChartSlots(base, {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
      boundarySupportAvailable: true,
    });
    expect(result.state).toBe('screened');
    expect(result.slots).toHaveLength(1);
    expect(result.slots[0].tier).toBe('Good');
    expect(result.slots[0].chartScreening).toEqual(expect.objectContaining({
      rejected: false,
      needsReview: true,
      stable: false,
      boundaryConventionUncertain: true,
    }));
    expect(result.slots[0].chartScreening?.outcomes.every(
      outcome => outcome.status === 'unknown',
    )).toBe(true);
    expect(result.chartRemovedCount).toBe(0);
    expect(result.boundaryReviewCount).toBe(1);
    expect(result.message).toMatch(/boundary-adjacent candidate remains review-gated/);
  });

  test('boundary review does not suppress a Lagna-independent personal rejection', async () => {
    const base = slots(1);
    base[0].chartBoundaryNeedsReview = true;
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const result = await enrichElectionChartSlots(base, {
      activity: 'surgery', system: 'drik', location: LOCATION, derive,
      personalParticipant: {
        id: 'patient-1', name: 'Patient', nakshatra: null,
        janmaRashi: 'Mesha', janmaLagna: null,
      },
    });
    expect(result.slots).toEqual([]);
    expect(result.personalRemovedCount).toBe(1);
    expect(result.boundaryReviewCount).toBe(1);
  });

  test('refuses a chart-screened claim when the Lagna transition map is unavailable', async () => {
    const derive = vi.fn();
    const result = await enrichElectionChartSlots(slots(2), {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
      boundarySupportAvailable: false,
    });
    expect(result.state).toBe('unavailable');
    expect(result.slots.every(slot => slot.tier !== 'Excellent')).toBe(true);
    expect(result.message).toMatch(/transition map could not be loaded/);
    expect(derive).not.toHaveBeenCalled();
  });

  test('caps screening at five requests without falling back to unscreened slots', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) =>
      response(request, new Set(Array.from({ length: 12 }, (_, index) => index))));
    const result = await enrichElectionChartSlots(slots(72), {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.state).toBe('screened');
    expect(result.screenedCount).toBe(60);
    expect(result.removedCount).toBe(60);
    expect(result.slots).toEqual([]);
    expect(result.candidateLimitReached).toBe(true);
    expect(result.message).toMatch(/safety budget was reached/);
    expect(derive).toHaveBeenCalledTimes(5);
  });

  test('candidate-cap message reports the displayed survivor count', async () => {
    const base = slots(72).map(slot => ({ ...slot, score: 10, tier: 'Good' }));
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const result = await enrichElectionChartSlots(base, {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.candidateLimitReached).toBe(true);
    expect(result.slots).toHaveLength(10);
    expect(result.message).toContain('10 surviving slots are shown');
    expect(result.message).not.toContain('60 surviving');
    expect(derive).toHaveBeenCalledTimes(5);
  });

  test('keeps a clean slot ahead of an equal-score personal-dosha slot', async () => {
    const base = slots(2).map(slot => ({ ...slot, score: 10, tier: 'Good' }));
    base[0].personalDosha = 'tara_dosha';
    base[1].personalDosha = null;
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const result = await enrichElectionChartSlots(base, {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.slots[0].personalDosha).toBeNull();
  });

  test('an exact stable pass does not cap an otherwise Excellent slot', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const result = await enrichElectionChartSlots(slots(1), {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.slots).toHaveLength(1);
    expect(result.slots[0].tier).toBe('Excellent');
    expect(result.slots[0].dayDosha).toBeNull();
  });

  test('uses exact returned Chandra across sampled states for surgery screening', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const result = await enrichElectionChartSlots(slots(1), {
      activity: 'surgery', system: 'drik', location: LOCATION, derive,
      personalParticipant: {
        id: 'patient-1', name: 'Patient', nakshatra: null,
        janmaRashi: 'Mesha', janmaLagna: null,
      },
    });
    expect(result.slots).toEqual([]);
    expect(result.removedCount).toBe(1);
    expect(result.chartRemovedCount).toBe(0);
    expect(result.personalRemovedCount).toBe(1);
    expect(result.personalRemovedRules).toEqual([expect.objectContaining({
      ruleId: 'personal.surgery.chandra-outside-janma-rashi', count: 1,
    })]);
    expect(result.message).toContain('1 failed a profile-specific source requirement');
  });

  test('uses exact returned Chandra longitude for Seemantha Nakshatra exclusions', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const result = await enrichElectionChartSlots(slots(1), {
      activity: 'seemantha', system: 'drik', location: LOCATION, derive,
      personalParticipant: {
        id: 'mother-1', name: 'Mother',
        // Chandra at 1.25 degrees Mesha is Ashwini. Choosing the star two
        // positions before it makes Ashwini the excluded third position.
        nakshatra: NAKSHATRA_NAMES[25], janmaRashi: null, janmaLagna: null,
      },
    });
    expect(result.slots).toEqual([]);
    expect(result.chartRemovedCount).toBe(0);
    expect(result.personalRemovedCount).toBe(1);
    expect(result.personalRemovedRules[0]?.ruleId)
      .toBe('personal.seemantha.birth-star-exclusions');
  });

  test('uses exact returned Lagna for the Travel prohibition', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const base = slots(1);
    base[0].chartCheckLagnas = ['Kanya', 'Kanya'];
    const result = await enrichElectionChartSlots(base, {
      activity: 'travel', system: 'drik', location: LOCATION, derive,
      personalParticipant: {
        id: 'traveller-1', name: 'Traveller', nakshatra: null,
        janmaRashi: 'Vrishabha', janmaLagna: 'Kanya',
      },
    });
    expect(result.slots).toEqual([]);
    expect(result.personalRemovedRules[0]?.ruleId)
      .toBe('personal.travel.lagna-exclusions');
  });

  test('uses an exact Gruhapravesha natal match only as a tie-breaker', async () => {
    const base = slots(2).map(slot => ({ ...slot, score: 10, tier: 'Good' }));
    const derive = vi.fn(async (request: ElectionChartRequest) => ({
      ...response(request),
      charts: request.instants.map((instant, index) => snapshot(
        instant,
        2,
        { chandraRashi: index < 2 ? 'Vrishabha' : 'Mesha' },
      )),
    }));
    const result = await enrichElectionChartSlots(base, {
      activity: 'gruhapravesha', system: 'drik', location: LOCATION, derive,
      personalParticipant: {
        id: 'owner-1', name: 'Owner', nakshatra: NAKSHATRA_NAMES[0],
        janmaRashi: null, janmaLagna: null,
      },
    });
    expect(result.slots).toHaveLength(2);
    expect(result.slots[0].isoDate).toBe(base[1].isoDate);
    expect(result.slots[0].personalPreferencePasses).toBe(1);
    expect(result.slots.every(slot => slot.score === 10)).toBe(true);
  });

  test('uses personal failure as the exclusive primary removal reason', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => ({
      ...response(request),
      charts: request.instants.map(instant => snapshot(instant, 8)),
    }));
    const result = await enrichElectionChartSlots(slots(1), {
      activity: 'surgery', system: 'drik', location: LOCATION, derive,
      personalParticipant: {
        id: 'patient-1', name: 'Patient', nakshatra: null,
        janmaRashi: 'Mesha', janmaLagna: null,
      },
    });
    expect(result.removedCount).toBe(1);
    expect(result.personalRemovedCount).toBe(1);
    expect(result.chartRemovedCount).toBe(0);
  });

  test('retains unresolved personal checks for review without inventing a rejection', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const result = await enrichElectionChartSlots(slots(1), {
      activity: 'surgery', system: 'drik', location: LOCATION, derive,
      personalParticipant: null,
    });
    expect(result.slots).toHaveLength(1);
    expect(result.slots[0].tier).toBe('Good');
    expect(result.slots[0].dayDosha).toBe('practitioner_review');
    expect(result.slots[0].reasonGroups.personal_outcomes).toEqual([
      expect.objectContaining({ status: 'unknown' }),
    ]);
    expect(result.personalRemovedCount).toBe(0);
  });

  test('a failed service preserves the Panchangam shortlist with honest state', async () => {
    const derive = vi.fn(async () => { throw new Error('offline'); });
    const base = slots(12);
    const result = await enrichElectionChartSlots(base, {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.state).toBe('unavailable');
    expect(result.slots.map(slot => slot.score)).toEqual(
      base.slice(0, 10).map(slot => slot.score),
    );
    expect(result.slots.every(slot => slot.tier !== 'Excellent')).toBe(true);
    expect(result.slots.every(slot => slot.dayDosha === 'practitioner_review')).toBe(true);
    expect(result.message).toMatch(/Panchangam-ranked/);
  });

  test('preserves bounded retry guidance when the chart service is busy', async () => {
    const derive = vi.fn(async () => {
      throw new ElectionChartApiError(
        'rate-limited', 'untrusted upstream detail', 429, 125,
      );
    });
    const result = await enrichElectionChartSlots(slots(1), {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
    });
    expect(result.state).toBe('unavailable');
    expect(result.message).toBe(
      'Panchangam-ranked; exact chart screening is busy. Try again in about 3 minutes.',
    );
    expect(result.message).not.toContain('untrusted');
  });

  test.each(['surgery', 'seemantha', 'travel'])(
    'a failed service preserves prior generic profile scoring for %s',
    async activity => {
      const derive = vi.fn(async () => { throw new Error('offline'); });
      const base = slots(1);
      base[0].personalDosha = 'tara_dosha';
      const result = await enrichElectionChartSlots(base, {
        activity, system: 'drik', location: LOCATION, derive,
        personalParticipant: {
          id: 'person-1', name: 'Person', nakshatra: 'Rohini',
          janmaRashi: 'Vrishabha', janmaLagna: 'Mesha',
        },
      });
      expect(result.state).toBe('unavailable');
      expect(result.slots[0].score).toBe(base[0].score);
      expect(result.slots[0].personalDosha).toBe('tara_dosha');
    },
  );

  test('network payload contains only location and instants', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    await enrichElectionChartSlots(slots(2), {
      activity: 'wedding', system: 'drik', location: LOCATION, derive,
      personalParticipant: {
        id: 'private-id', name: 'Private name', nakshatra: 'Rohini',
        janmaRashi: 'Vrishabha', janmaLagna: 'Mesha',
      },
    });
    const request = derive.mock.calls[0][0];
    expect(Object.keys(request).sort()).toEqual(['instants', 'location']);
  });

  test('disabled screening preserves and review-gates the shortlist without deriving', async () => {
    const derive = vi.fn(async (request: ElectionChartRequest) => response(request));
    const now = vi.spyOn(Date, 'now');
    const base = slots(12);
    try {
      const result = await enrichElectionChartSlots(base, {
        activity: 'wedding',
        system: 'drik',
        location: LOCATION,
        derive,
        activationFlag: 'false',
        locationLike: { hostname: '127.0.0.1' } as Location,
      });
      expect(result.state).toBe('disabled');
      expect(result.slots.map(slot => slot.score)).toEqual(
        base.slice(0, 10).map(slot => slot.score),
      );
      expect(result.slots.every(slot => slot.tier !== 'Excellent')).toBe(true);
      expect(result.slots.every(
        slot => slot.dayDosha === 'practitioner_review',
      )).toBe(true);
      expect(result.message).toMatch(/not active in this public build/);
      expect(derive).not.toHaveBeenCalled();
      expect(now).not.toHaveBeenCalled();
    } finally {
      now.mockRestore();
    }
  });
});
