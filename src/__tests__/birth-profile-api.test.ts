import { afterEach, describe, expect, test, vi } from 'vitest';
import {
  BirthProfileApiError,
  birthProfileApiBase,
  deriveBirthProfile,
  searchBirthPlaces,
} from '../lib/birth-profile-api';

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
}

function derivationPayload(): Record<string, unknown> {
  const rashis = [
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha',
    'Kanya', 'Tula', 'Vrischika', 'Dhanu',
  ];
  return {
    contract_version: '1.0',
    engine: {
      name: 'DashaFlow',
      version: '1.0.0',
      ayanamsha: 'Lahiri',
      ephemeris: 'moshier',
    },
    data: {
      nakshatra: 'Rohini',
      pada: 2,
      janma_rashi: 'Vrishabha',
      lagna: 'Karka',
      lagna_degree: 12.345,
      planets: rashis.map((rashi, index) => ({
        name: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'][index],
        rashi,
        degree: index + 0.25,
        house: index + 1,
        retrograde: index === 6,
      })),
    },
  };
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('birth profile API routing', () => {
  test('uses the local Astro gateway for local development and production otherwise', () => {
    expect(birthProfileApiBase({ hostname: '127.0.0.1' } as Location)).toBe(
      'http://127.0.0.1:3000/api/guest',
    );
    expect(birthProfileApiBase({ hostname: 'localhost' } as Location)).toBe(
      'http://127.0.0.1:3000/api/guest',
    );
    expect(birthProfileApiBase({ hostname: 'panchangam.astrochaganti.com' } as Location)).toBe(
      'https://astrochaganti.com/api/guest',
    );
    expect(birthProfileApiBase(
      { hostname: 'localhost' } as Location,
      'http://localhost:4310/api/guest/',
    )).toBe('http://localhost:4310/api/guest');
    expect(birthProfileApiBase(
      { hostname: 'panchangam.astrochaganti.com' } as Location,
      'http://127.0.0.1:3000/api/guest',
    )).toBe('https://astrochaganti.com/api/guest');
    expect(birthProfileApiBase(
      { hostname: 'panchangam.astrochaganti.com' } as Location,
      'https://untrusted.example/api/guest',
    )).toBe('https://astrochaganti.com/api/guest');
    expect(birthProfileApiBase(
      { hostname: 'panchangam.astrochaganti.com' } as Location,
      'https://astrochaganti.com/api/guest/',
    )).toBe('https://astrochaganti.com/api/guest');
  });

  test('searches through the stateless gateway with privacy-safe fetch settings', async () => {
    const fetcher = vi.fn(async () => jsonResponse({
      data: {
        results: [{
          id: 'osm:123',
          label: 'Vijayawada, Andhra Pradesh, India',
          latitude: 16.5062,
          longitude: 80.648,
          timezone: 'Asia/Kolkata',
        }],
        attribution: 'OpenStreetMap contributors',
      },
    })) as unknown as typeof fetch;

    const result = await searchBirthPlaces('  Vijayawada  ', {
      activationFlag: 'true',
      baseUrl: 'https://astrochaganti.com/api/guest',
      fetcher,
      locationLike: { hostname: 'panchangam.astrochaganti.com' } as Location,
    });

    expect(result.results[0].timezone).toBe('Asia/Kolkata');
    expect(fetcher).toHaveBeenCalledOnce();
    const [url, request] = (fetcher as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe('https://astrochaganti.com/api/guest/places/search');
    expect(request).toMatchObject({
      method: 'POST',
      cache: 'no-store',
      credentials: 'omit',
    });
    expect(JSON.parse(String(request.body))).toEqual({ query: 'Vijayawada' });
  });

  test('fails before scheduling or fetching when public activation is disabled', async () => {
    const fetcher = vi.fn<typeof fetch>();
    const timer = vi.spyOn(globalThis, 'setTimeout');

    await expect(searchBirthPlaces('Vijayawada', {
      activationFlag: 'TRUE',
      baseUrl: 'https://astrochaganti.com/api/guest',
      fetcher,
      locationLike: { hostname: 'panchangam.astrochaganti.com' } as Location,
    })).rejects.toMatchObject({
      code: 'disabled',
      message: expect.stringContaining('not active in this public build'),
    });

    expect(fetcher).not.toHaveBeenCalled();
    expect(timer).not.toHaveBeenCalled();
  });

  test('never routes a public request through an arbitrary or loopback override', async () => {
    const fetcher = vi.fn(async () => jsonResponse({
      data: { results: [], attribution: 'OpenStreetMap contributors' },
    })) as unknown as typeof fetch;
    const publicOptions = {
      activationFlag: 'true',
      fetcher,
      locationLike: { hostname: 'panchangam.astrochaganti.com' } as Location,
    };

    await searchBirthPlaces('Vijayawada', {
      ...publicOptions,
      baseUrl: 'http://127.0.0.1:3000/api/guest',
    });
    await searchBirthPlaces('Vijayawada', {
      ...publicOptions,
      baseUrl: 'https://untrusted.example/api/guest',
    });

    expect(fetcher).toHaveBeenNthCalledWith(
      1,
      'https://astrochaganti.com/api/guest/places/search',
      expect.any(Object),
    );
    expect(fetcher).toHaveBeenNthCalledWith(
      2,
      'https://astrochaganti.com/api/guest/places/search',
      expect.any(Object),
    );
  });

  test('rejects malformed or excessive place results instead of trusting remote HTML/data', async () => {
    const malformed = vi.fn(async () => jsonResponse({
      data: {
        results: [{
          id: 'x', label: '<img onerror=alert(1)>', latitude: 120,
          longitude: 80, timezone: 'Asia/Kolkata',
        }],
        attribution: 'provider',
      },
    })) as unknown as typeof fetch;

    await expect(searchBirthPlaces('city', { fetcher: malformed })).rejects.toMatchObject({
      code: 'invalid-response',
    });
  });
});

describe('birth profile derivation contract', () => {
  test('sends only calculation inputs, never the local profile name', async () => {
    const fetcher = vi.fn(async () => jsonResponse(derivationPayload())) as unknown as typeof fetch;
    const input = {
      dateOfBirth: '1990-05-12',
      timeOfBirth: '14:35',
      latitude: 16.5062,
      longitude: 80.648,
      timezone: 'Asia/Kolkata',
    };

    const result = await deriveBirthProfile(input, {
      activationFlag: 'true',
      baseUrl: 'https://astrochaganti.com/api/guest',
      fetcher,
      locationLike: { hostname: 'panchangam.astrochaganti.com' } as Location,
    });

    expect(result).toMatchObject({
      contractVersion: '1.0',
      nakshatra: 'Rohini',
      pada: 2,
      janmaRashi: 'Vrishabha',
      lagna: 'Karka',
      engine: { name: 'DashaFlow', ayanamsha: 'Lahiri', ephemeris: 'moshier' },
    });
    expect(result.planets).toHaveLength(9);
    const [, request] = (fetcher as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    const sent = JSON.parse(String(request.body));
    expect(sent).toEqual({
      date_of_birth: '1990-05-12',
      time_of_birth: '14:35',
      latitude: 16.5062,
      longitude: 80.648,
      timezone: 'Asia/Kolkata',
    });
    expect(JSON.stringify(sent)).not.toContain('name');
  });

  test('fails closed when contract version, planet count, or chart values are invalid', async () => {
    const payload = derivationPayload();
    payload.contract_version = '2.0';
    const fetcher = vi.fn(async () => jsonResponse(payload)) as unknown as typeof fetch;

    await expect(deriveBirthProfile({
      dateOfBirth: '1990-05-12',
      timeOfBirth: '14:35',
      latitude: 16.5062,
      longitude: 80.648,
      timezone: 'Asia/Kolkata',
    }, { fetcher })).rejects.toMatchObject({ code: 'invalid-response' });
  });

  test('surfaces rate limits and bounded server messages', async () => {
    const fetcher = vi.fn(async () => jsonResponse(
      { error: { message: 'Please wait before trying again.' } },
      { status: 429, headers: { 'Retry-After': '12' } },
    )) as unknown as typeof fetch;

    await expect(searchBirthPlaces('Vijayawada', { fetcher })).rejects.toEqual(
      expect.objectContaining<Partial<BirthProfileApiError>>({
        code: 'rate-limited',
        status: 429,
        retryAfterSeconds: 12,
        message: 'Please wait before trying again.',
      }),
    );
  });

  test('classifies network failures without exposing implementation details', async () => {
    const fetcher = vi.fn(async () => { throw new Error('secret upstream host'); }) as unknown as typeof fetch;

    await expect(searchBirthPlaces('Vijayawada', { fetcher })).rejects.toEqual(
      expect.objectContaining<Partial<BirthProfileApiError>>({
        code: 'network',
        message: 'The calculation service is unavailable. Check your connection and try again.',
      }),
    );
  });

  test('aborts a request after the configured timeout', async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn((_url: RequestInfo | URL, request?: RequestInit) => new Promise<Response>(
      (_resolve, reject) => request?.signal?.addEventListener('abort', () => {
        reject(new DOMException('aborted', 'AbortError'));
      }),
    )) as unknown as typeof fetch;

    const request = searchBirthPlaces('Vijayawada', { fetcher, timeoutMs: 25 });
    const rejection = expect(request).rejects.toMatchObject({ code: 'timeout' });
    await vi.advanceTimersByTimeAsync(25);

    await rejection;
  });
});
