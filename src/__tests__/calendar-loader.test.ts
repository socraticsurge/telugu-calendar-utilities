import { afterEach, expect, it, vi } from 'vitest';
import fixtures from '../../tests/fixtures/calendar-data-contract.json';

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.resetModules(); });

it('keeps normal builds on the legacy path until the sidecars are published', async () => {
  vi.stubEnv('VITE_STRUCTURED_CALENDAR_ENABLED', 'false');
  const fetcher = vi.fn().mockResolvedValue({ ok: true, text: async () =>
    'BEGIN:VEVENT\nDTSTART;VALUE=DATE:20260718\nSUMMARY:Legacy\nDESCRIPTION:Text\nEND:VEVENT' });
  vi.stubGlobal('fetch', fetcher);
  const { loadCalendarFeed } = await import('../lib/calendar-loader');
  expect((await loadCalendarFeed('Hyderabad', 'drik')).size).toBe(1);
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher.mock.calls[0][0]).toMatch(/\.ics$/);
});

it('enables published structured data through the explicit build flag', async () => {
  vi.stubEnv('VITE_STRUCTURED_CALENDAR_ENABLED', 'true');
  const fixture = fixtures[0];
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => fixture }));
  const { loadCalendarFeed } = await import('../lib/calendar-loader');
  expect((await loadCalendarFeed(fixture.city, fixture.system)).size).toBe(2);
});

it('prefers validated structured data and caches successful loads', async () => {
  const fixture = fixtures[0];
  const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => fixture });
  vi.stubGlobal('fetch', fetcher);
  const { loadCalendarFeed } = await import('../lib/calendar-loader');
  const first = await loadCalendarFeed(fixture.city, fixture.system, true);
  expect(first.size).toBe(2);
  expect(await loadCalendarFeed(fixture.city, fixture.system, true)).toBe(first);
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher.mock.calls[0][0]).toContain('.days-v1.json');
});

it('uses the production structured feed when a local preview lacks data', async () => {
  const fixture = fixtures[0];
  const fetcher = vi.fn().mockResolvedValueOnce({ ok: false })
    .mockResolvedValueOnce({ ok: true, json: async () => fixture });
  vi.stubGlobal('fetch', fetcher);
  const { loadCalendarFeed } = await import('../lib/calendar-loader');
  expect((await loadCalendarFeed(fixture.city, fixture.system, true)).size).toBe(2);
  expect(fetcher.mock.calls[1][0]).toContain('https://panchangam.astrochaganti.com/feeds/');
});

it('falls back to the existing feed when structured files are unavailable or invalid', async () => {
  const fetcher = vi.fn().mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValueOnce({ ok: true, json: async () => ({ schemaVersion: 99 }) })
    .mockResolvedValueOnce({ ok: true, text: async () =>
      'BEGIN:VEVENT\nDTSTART;VALUE=DATE:20260718\nSUMMARY:Legacy\nDESCRIPTION:Text\nEND:VEVENT' });
  vi.stubGlobal('fetch', fetcher);
  const { loadCalendarFeed } = await import('../lib/calendar-loader');
  expect((await loadCalendarFeed('Hyderabad', 'drik', true)).get('20260718'))
    .toEqual({ summary: 'Legacy', description: 'Text' });
});

it('does not disguise failure when neither data format is available', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
  const { loadCalendarFeed } = await import('../lib/calendar-loader');
  await expect(loadCalendarFeed('Hyderabad', 'drik', true)).rejects.toThrow('fetch failed');
});
