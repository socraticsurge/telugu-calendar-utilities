import { afterEach, expect, test, vi } from 'vitest';
import { BirthProfileApiError, searchBirthPlaces } from '../lib/birth-profile-api';
import { ElectionChartApiError, deriveElectionCharts } from '../lib/election-chart-api';

const input = {
  location: { latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
  instants: ['2026-09-08T05:30:00.000Z'],
};
const local = { hostname: 'localhost' };

afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });

test('election request validation precedes activation and network effects', async () => {
  const fetcher = vi.fn<typeof fetch>();
  await expect(deriveElectionCharts({ ...input, instants: [] }, {
    activationFlag: 'false', locationLike: local, fetcher,
  })).rejects.toMatchObject({ name: 'ElectionChartApiError', code: 'invalid-request' });
  expect(fetcher).not.toHaveBeenCalled();
});

test('malformed successful JSON retains endpoint-specific error identity', async () => {
  const fetcher = vi.fn<typeof fetch>().mockImplementation(async () => new Response('{'));
  await expect(searchBirthPlaces('city', { fetcher, locationLike: local }))
    .rejects.toBeInstanceOf(BirthProfileApiError);
  await expect(deriveElectionCharts(input, { fetcher, locationLike: local }))
    .rejects.toBeInstanceOf(ElectionChartApiError);
});

test('an unsolicited AbortError has different existing endpoint classifications', async () => {
  const fetcher = vi.fn<typeof fetch>().mockRejectedValue(new DOMException('abort', 'AbortError'));
  await expect(searchBirthPlaces('city', { fetcher, locationLike: local }))
    .rejects.toMatchObject({ code: 'timeout', message: 'The calculation took too long. Try again.' });
  await expect(deriveElectionCharts(input, { fetcher, locationLike: local }))
    .rejects.toMatchObject({ code: 'network', message: 'Chart screening is temporarily unavailable.' });
});

test.each([null, '0', '-2', 'tomorrow', 'Infinity'])('ignores invalid Retry-After %s', async retry => {
  const fetcher = vi.fn<typeof fetch>().mockImplementation(async () => new Response('{}', {
    status: 429, headers: retry === null ? {} : { 'Retry-After': retry },
  }));
  await expect(searchBirthPlaces('city', { fetcher, locationLike: local }))
    .rejects.toMatchObject({ code: 'rate-limited', status: 429, retryAfterSeconds: null });
  await expect(deriveElectionCharts(input, { fetcher, locationLike: local }))
    .rejects.toMatchObject({ code: 'rate-limited', status: 429, retryAfterSeconds: null });
});

test('default deadlines remain 15 seconds for birth and 20 for election', async () => {
  const timer = vi.spyOn(globalThis, 'setTimeout');
  const clear = vi.spyOn(globalThis, 'clearTimeout');
  const fetcher = vi.fn<typeof fetch>().mockRejectedValue(new Error('offline'));
  await searchBirthPlaces('city', { fetcher, locationLike: local }).catch(() => undefined);
  await deriveElectionCharts(input, { fetcher, locationLike: local }).catch(() => undefined);
  expect(timer.mock.calls.map(call => call[1])).toEqual([15_000, 20_000]);
  expect(clear).toHaveBeenCalledTimes(2);
});

test('external election cancellation is classified as timeout and removes its listener', async () => {
  const external = new AbortController();
  const remove = vi.spyOn(external.signal, 'removeEventListener');
  const fetcher = vi.fn<typeof fetch>().mockImplementation((_url, init) => new Promise((_resolve, reject) => {
    init?.signal?.addEventListener('abort', () => reject(new Error('cancelled')));
  }));
  const result = deriveElectionCharts(input, { fetcher, locationLike: local, signal: external.signal });
  const assertion = expect(result).rejects.toMatchObject({ code: 'timeout' });
  external.abort();
  await assertion;
  expect(remove).toHaveBeenCalledWith('abort', expect.any(Function));
});
