import { describe, expect, test, vi } from 'vitest';

import {
  deriveElectionCharts,
  electionChartApiBase,
  localWallTimeToInstant,
} from '../lib/election-chart-api';

const PLANETS = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;

function validResponse() {
  return {
    contract_version: '1.0',
    engine: {
      name: 'DashaFlow', version: '1.2.3', ayanamsha: 'Lahiri', ephemeris: 'swiss',
      node_convention: 'mean',
    },
    house_system: 'whole_sign',
    location: { latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
    data: {
      charts: ['2026-09-08T05:30:00.000Z'].map(instant => ({
        instant,
        lagna: { rashi: 'Kanya', degree: 12.5 },
        planets: PLANETS.map((name, index) => ({
          name, rashi: 'Mesha', degree: index + 0.25,
          house: index + 1, retrograde: name === 'Rahu' || name === 'Ketu',
        })),
      })),
    },
  };
}

describe('election-chart gateway client', () => {
  test('allows only a loopback HTTP override for isolated local chart testing', () => {
    expect(electionChartApiBase('http://127.0.0.1:19014/api/guest/')).toBe(
      'http://127.0.0.1:19014/api/guest',
    );
    expect(electionChartApiBase('https://untrusted.example/api/guest')).not.toContain(
      'untrusted.example',
    );
  });

  test('converts city wall time to the correct UTC instant across DST', () => {
    expect(localWallTimeToInstant('2026-01-15', 9 * 60 + 30, 'America/New_York'))
      .toBe('2026-01-15T14:30:00.000Z');
    expect(localWallTimeToInstant('2026-07-15', 9 * 60 + 30, 'America/New_York'))
      .toBe('2026-07-15T13:30:00.000Z');
  });

  test('rejects nonexistent and ambiguous DST civil minutes', () => {
    expect(() => localWallTimeToInstant(
      '2026-03-08', 2 * 60 + 30, 'America/New_York',
    )).toThrow(/does not exist/);
    expect(() => localWallTimeToInstant(
      '2026-11-01', 1 * 60 + 30, 'America/New_York',
    )).toThrow(/ambiguous/);
  });

  test('rejects normalized impossible dates while accepting a real leap day', () => {
    expect(localWallTimeToInstant('2028-02-29', 0, 'UTC'))
      .toBe('2028-02-29T00:00:00.000Z');
    for (const invalidDate of ['2026-02-29', '2026-02-31', '2026-04-31', '2026-13-01']) {
      expect(() => localWallTimeToInstant(invalidDate, 0, 'UTC'))
        .toThrow(/local chart date is invalid/);
    }
  });

  test('sends only location and candidate instants with no credentials', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(
      JSON.stringify(validResponse()),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ));
    await deriveElectionCharts({
      location: { latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
      instants: ['2026-09-08T05:30:00.000Z'],
    }, { baseUrl: 'https://example.test/api/guest', fetcher });

    const [, init] = fetcher.mock.calls[0];
    expect(JSON.parse(String(init?.body))).toEqual({
      contract_version: '1.0',
      location: { latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
      instants: ['2026-09-08T05:30:00.000Z'],
    });
    expect(init?.credentials).toBe('omit');
    expect(init?.cache).toBe('no-store');
  });

  test.each([
    ['incomplete', (payload: ReturnType<typeof validResponse>) => {
      payload.data.charts[0].planets.pop();
    }],
    ['reordered', (payload: ReturnType<typeof validResponse>) => {
      const planets = payload.data.charts[0].planets;
      [planets[0], planets[1]] = [planets[1], planets[0]];
    }],
  ])('rejects %s chart responses', async (_label, mutate) => {
    const payload = validResponse();
    mutate(payload);
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(
      JSON.stringify(payload),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ));
    await expect(deriveElectionCharts({
      location: payload.location,
      instants: ['2026-09-08T05:30:00.000Z'],
    }, { baseUrl: 'https://example.test/api/guest', fetcher }))
      .rejects.toMatchObject({ code: 'invalid-response' });
  });

  test('accepts a valid mixed-ephemeris batch', async () => {
    const payload = validResponse();
    payload.engine.ephemeris = 'mixed';
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(
      JSON.stringify(payload),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ));

    await expect(deriveElectionCharts({
      location: payload.location,
      instants: ['2026-09-08T05:30:00.000Z'],
    }, { baseUrl: 'https://example.test/api/guest', fetcher }))
      .resolves.toMatchObject({ engine: { ephemeris: 'mixed' } });
  });

  test('classifies the browser deadline as unavailable timeout evidence', async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation((_input, init) => (
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => {
          reject(new DOMException('Aborted', 'AbortError'));
        }, { once: true });
      })
    ));

    await expect(deriveElectionCharts({
      location: { latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
      instants: ['2026-09-08T05:30:00.000Z'],
    }, { baseUrl: 'https://example.test/api/guest', fetcher, timeoutMs: 5 }))
      .rejects.toMatchObject({ code: 'timeout', status: null });
  });

  test('preserves rate-limit status and bounded retry guidance', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(
      JSON.stringify({ error: 'Busy' }),
      { status: 429, headers: { 'Content-Type': 'application/json', 'Retry-After': '12' } },
    ));

    await expect(deriveElectionCharts({
      location: { latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
      instants: ['2026-09-08T05:30:00.000Z'],
    }, { baseUrl: 'https://example.test/api/guest', fetcher }))
      .rejects.toMatchObject({
        code: 'rate-limited', status: 429, retryAfterSeconds: 12,
      });
  });

  test.each([
    ['wrong engine', (payload: ReturnType<typeof validResponse>) => {
      payload.engine.name = 'OtherEngine';
    }],
    ['wrong ayanamsha', (payload: ReturnType<typeof validResponse>) => {
      payload.engine.ayanamsha = 'Tropical';
    }],
    ['wrong node convention', (payload: ReturnType<typeof validResponse>) => {
      payload.engine.node_convention = 'true';
    }],
    ['non-canonical Rashi', (payload: ReturnType<typeof validResponse>) => {
      payload.data.charts[0].lagna.rashi = 'Virgo';
    }],
  ])('rejects %s rather than blending it into Drik/Lahiri', async (_label, mutate) => {
    const payload = validResponse();
    mutate(payload);
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response(
      JSON.stringify(payload),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ));

    await expect(deriveElectionCharts({
      location: payload.location,
      instants: ['2026-09-08T05:30:00.000Z'],
    }, { baseUrl: 'https://example.test/api/guest', fetcher }))
      .rejects.toMatchObject({ code: 'invalid-response' });
  });
});
