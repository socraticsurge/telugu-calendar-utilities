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

async function parsedFeed(response: Response | null): Promise<ReturnType<typeof parseEvents> | null> {
  if (!response?.ok) return null;
  const events = parseEvents(await response.text());
  return events.size ? events : null;
}

export async function loadFeed(city: string, system: string) {
  const key = `${city}|${system}`;
  if (FEED_CACHE.has(key)) return FEED_CACHE.get(key)!;
  // Relative path on the deployed site; fall back to the live feed URL
  // so the page also works when previewed locally without a feeds/ dir. Vite
  // serves index.html with status 200 for an unknown relative path, so HTTP
  // status alone is insufficient: an empty parse must also trigger fallback.
  const localResponse = await fetch(`feeds/${feedFilename(city, system)}`).catch(() => null);
  let events = await parsedFeed(localResponse);
  if (!events) {
    const productionResponse = await fetch(
      `${FEED_BASE_URL}${feedFilename(city, system)}`,
    ).catch(() => null);
    events = await parsedFeed(productionResponse);
  }
  if (!events) throw new Error('fetch failed');
  FEED_CACHE.set(key, events);
  return events;
}
