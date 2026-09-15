/// <reference types="vite/client" />
/** Structured-data pilot. Old deployments remain usable through the ICS fallback. */
import { calendarEvents, type CalendarEvent } from './calendar-data';
import { FEED_BASE_URL, feedFilename, loadFeed } from './feed-loader';
import { isLoopbackHostname } from './remote-calculation-activation';

const cache = new Map<string, Map<string, CalendarEvent>>();

function structuredDataEnabled(): boolean {
  const environment = import.meta.env;
  const flag = environment.VITE_STRUCTURED_CALENDAR_ENABLED;
  if (flag !== undefined) return flag === 'true';
  return isLoopbackHostname(globalThis.location?.hostname ?? '')
    && new URLSearchParams(globalThis.location?.search).get('calendarData') === 'structured';
}

async function structuredFeed(url: string, city: string, system: string) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000);
  try {
    const response = await fetch(url, { signal: controller.signal });
    return response.ok ? calendarEvents(await response.json(), city, system) : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

export async function loadCalendarFeed(
  city: string,
  system: string,
  structured = structuredDataEnabled(),
): Promise<Map<string, CalendarEvent>> {
  // Roll out only after the sidecars are published; old static deployments
  // must not acquire speculative 404s or extra request latency.
  if (!structured) return loadFeed(city, system);
  const key = `${city}|${system}`;
  const cached = cache.get(key);
  if (cached) return cached;
  const filename = feedFilename(city, system).replace(/\.ics$/, '.days-v1.json');
  let events = await structuredFeed(`feeds/${filename}`, city, system);
  if (!events && globalThis.location?.hostname !== new URL(FEED_BASE_URL).hostname) {
    events = await structuredFeed(`${FEED_BASE_URL}${filename}`, city, system);
  }
  if (!events) return loadFeed(city, system);
  cache.set(key, events);
  return events;
}
