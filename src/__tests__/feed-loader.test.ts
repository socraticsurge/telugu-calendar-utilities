import { afterEach, describe, expect, test, vi } from 'vitest';

import { FEED_BASE_URL, feedFilename, loadFeed } from '../lib/feed-loader';

const ONE_DAY_FEED = [
  'BEGIN:VCALENDAR',
  'BEGIN:VEVENT',
  'DTSTART;VALUE=DATE:20260829',
  'SUMMARY:Krishna Pratipat · Purva Bhadrapada',
  'DESCRIPTION:Hyderabad test day',
  'END:VEVENT',
  'END:VCALENDAR',
].join('\r\n');

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('feed loader local preview fallback', () => {
  test('falls back when the local dev server returns index HTML with status 200', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(new Response('<!doctype html><title>Vite app</title>', {
        status: 200,
        headers: { 'Content-Type': 'text/html' },
      }))
      .mockResolvedValueOnce(new Response(ONE_DAY_FEED, {
        status: 200,
        headers: { 'Content-Type': 'text/calendar' },
      }));
    vi.stubGlobal('fetch', fetcher);

    const city = 'Local Fallback Test';
    const events = await loadFeed(city, 'drik');

    expect(events.get('20260829')?.description).toBe('Hyderabad test day');
    expect(fetcher).toHaveBeenNthCalledWith(1, `feeds/${feedFilename(city, 'drik')}`);
    expect(fetcher).toHaveBeenNthCalledWith(
      2,
      `${FEED_BASE_URL}${feedFilename(city, 'drik')}`,
    );
  });

  test('does not call production when the local feed parses successfully', async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(ONE_DAY_FEED, { status: 200 }));
    vi.stubGlobal('fetch', fetcher);

    const events = await loadFeed('Local Feed Test', 'drik');

    expect(events.has('20260829')).toBe(true);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
