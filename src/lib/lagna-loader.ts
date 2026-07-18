// Lagna (rising sign) data layer: cached per-session, per-city fetch.
// Consumed by the Today panel's lagna strip and the muhurta finder's
// lagna scoring.

import { slug, FEED_BASE_URL } from './feed-loader';

// The served JSON is precomputed by scripts/build_lagna_json.py; the
// panels index into it dynamically, so the per-day shape stays `any`.
interface LagnaData { start: string; days: any[]; }

// --- Lagna data layer: cached per-session, per-city fetch ---
const LAGNA_CACHE = new Map<string, Promise<LagnaData | null>>();
async function loadLagna(city: string): Promise<LagnaData | null> {
  if (LAGNA_CACHE.has(city)) return LAGNA_CACHE.get(city)!;
  const filename = `${slug(city)}-lagna.json`;
  let promise = fetch(`feeds/${filename}`).then(r => r.ok ? r.json() : null).catch(() => null);
  promise = promise.then(d => d || fetch(`${FEED_BASE_URL}${filename}`).then(r => r.ok ? r.json() : null).catch(() => null));
  LAGNA_CACHE.set(city, promise);
  return promise;
}

function lagnaDayFor(data: LagnaData | null, isoDate: string): any {
  if (!data || !data.days || !data.days.length) return null;
  const direct = data.days.find((d: any) => d.date === isoDate);
  if (direct) return direct;
  // Fallback for older formats without 'date': offset from data.start.
  const start = new Date(`${data.start}T00:00:00`);
  const target = new Date(`${isoDate}T00:00:00`);
  const idx = Math.round((target.getTime() - start.getTime()) / 86400000);
  return data.days[idx] || null;
}


export { loadLagna, lagnaDayFor };
