// Feed loading — URL construction, fetch with local→production
// fallback, and the per-(city, system) parse cache.
// Extracted verbatim from main.ts (one-shell decomposition).

import { parseEvents } from './ics';

export const FEED_BASE_URL = 'https://panchangam.astrochaganti.com/feeds/';

export function slug(name: string): string {
  return name.toLowerCase().replace(/\s+/g, '-').replace(/,/g, '');
}

export function feedFilename(city: string, system: string, variant = ''): string {
  const suffix = variant ? `-${variant}` : '';
  return `${slug(city)}-${system}${suffix}.ics`;
}

const FEED_CACHE = new Map<string, Map<string, { summary: string; description: string }>>();

export async function loadFeed(city: string, system: string) {
  const key = `${city}|${system}`;
  if (FEED_CACHE.has(key)) return FEED_CACHE.get(key)!;
  // Relative path on the deployed site; fall back to the live feed URL
  // so the page also works when previewed locally without a feeds/ dir.
  let res = await fetch(`feeds/${feedFilename(city, system)}`).catch(() => null);
  if (!res || !res.ok) res = await fetch(`${FEED_BASE_URL}${feedFilename(city, system)}`);
  if (!res.ok) throw new Error('fetch failed');
  const events = parseEvents(await res.text());
  FEED_CACHE.set(key, events);
  return events;
}
