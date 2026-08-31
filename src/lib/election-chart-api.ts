import type { BirthChartPlanet, BirthProfileEngine } from './birth-profile-api';
import { birthProfileApiBase } from './birth-profile-api';
import { RASI_NAMES } from '../data/rasis';

export const ELECTION_CHART_CONTRACT_VERSION = '1.0' as const;
export const ELECTION_CHART_BATCH_LIMIT = 24;
const DEFAULT_TIMEOUT_MS = 20_000;
const CANONICAL_PLANET_ORDER = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;
const CANONICAL_PLANETS = new Set<string>(CANONICAL_PLANET_ORDER);
const CANONICAL_RASHIS = new Set<string>(RASI_NAMES);

export interface ElectionChartEngine extends Omit<BirthProfileEngine, 'ephemeris'> {
  ephemeris: BirthProfileEngine['ephemeris'] | 'mixed';
  nodeConvention: 'mean';
}

export interface ElectionChartLocation {
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface ElectionChartSnapshot {
  instant: string;
  lagna: { rashi: string; degree: number };
  planets: BirthChartPlanet[];
}

export interface ElectionChartDerivation {
  contractVersion: typeof ELECTION_CHART_CONTRACT_VERSION;
  engine: ElectionChartEngine;
  houseSystem: 'whole_sign';
  location: ElectionChartLocation;
  charts: ElectionChartSnapshot[];
}

export interface ElectionChartRequest {
  location: ElectionChartLocation;
  instants: string[];
}

export type ElectionChartApiErrorCode =
  | 'invalid-request'
  | 'invalid-response'
  | 'network'
  | 'rate-limited'
  | 'request-failed'
  | 'timeout';

export class ElectionChartApiError extends Error {
  constructor(
    public readonly code: ElectionChartApiErrorCode,
    message: string,
    public readonly status: number | null = null,
    public readonly retryAfterSeconds: number | null = null,
  ) {
    super(message);
    this.name = 'ElectionChartApiError';
  }
}

export interface ElectionChartApiOptions {
  baseUrl?: string;
  fetcher?: typeof fetch;
  timeoutMs?: number;
  signal?: AbortSignal;
}

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function nonEmpty(value: unknown, maxLength = 200): string | null {
  return typeof value === 'string' && value.trim() && value.length <= maxLength
    ? value.trim()
    : null;
}

function finite(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function parsePlanet(value: unknown): BirthChartPlanet | null {
  const item = record(value);
  if (!item) return null;
  const name = nonEmpty(item.name, 40);
  const rashi = nonEmpty(item.rashi, 40);
  const degree = finite(item.degree);
  const house = finite(item.house);
  if (
    !name || !CANONICAL_PLANETS.has(name) || !rashi || !CANONICAL_RASHIS.has(rashi)
    || degree === null || degree < 0 || degree >= 30
    || house === null || !Number.isInteger(house) || house < 1 || house > 12
    || typeof item.retrograde !== 'boolean'
  ) return null;
  return { name, rashi, degree, house, retrograde: item.retrograde };
}

function parseSnapshot(value: unknown, expectedInstant: string): ElectionChartSnapshot | null {
  const item = record(value);
  const lagna = item ? record(item.lagna) : null;
  const instant = item ? nonEmpty(item.instant, 40) : null;
  const rashi = lagna ? nonEmpty(lagna.rashi, 40) : null;
  const degree = lagna ? finite(lagna.degree) : null;
  const rawPlanets = item && Array.isArray(item.planets) ? item.planets : null;
  const planets = rawPlanets?.map(parsePlanet).filter(
    (planet): planet is BirthChartPlanet => planet !== null,
  ) || [];
  if (
    instant !== expectedInstant || !rashi || !CANONICAL_RASHIS.has(rashi)
    || degree === null || degree < 0 || degree >= 30
    || !rawPlanets || rawPlanets.length !== 9 || planets.length !== rawPlanets.length
    || new Set(planets.map(planet => planet.name)).size !== 9
    || planets.some((planet, index) => planet.name !== CANONICAL_PLANET_ORDER[index])
  ) return null;
  return { instant, lagna: { rashi, degree }, planets };
}

export function electionChartApiBase(
  configuredBase: string | undefined = (
    import.meta as ImportMeta & { env?: Record<string, string | undefined> }
  ).env?.VITE_ELECTION_CHART_API_BASE,
): string {
  if (configuredBase) {
    try {
      const url = new URL(configuredBase);
      const loopback = url.hostname === '127.0.0.1'
        || url.hostname === 'localhost'
        || url.hostname === '[::1]';
      if (url.protocol === 'http:' && loopback) return configuredBase.replace(/\/+$/, '');
    } catch {
      // Invalid test-only configuration falls back to the canonical gateway.
    }
  }
  return birthProfileApiBase();
}

function validateRequest(input: ElectionChartRequest): void {
  const { latitude, longitude, timezone } = input.location;
  if (
    !Number.isFinite(latitude) || latitude < -90 || latitude > 90
    || !Number.isFinite(longitude) || longitude < -180 || longitude > 180
    || !timezone || timezone.length > 80
    || !input.instants.length || input.instants.length > ELECTION_CHART_BATCH_LIMIT
    || new Set(input.instants).size !== input.instants.length
    || input.instants.some(instant => {
      const parsed = new Date(instant);
      return Number.isNaN(parsed.getTime()) || parsed.toISOString() !== instant;
    })
  ) {
    throw new ElectionChartApiError('invalid-request', 'The chart request is invalid.');
  }
}

function apiErrorMessage(value: unknown): string | null {
  const payload = record(value);
  if (!payload) return null;
  const direct = nonEmpty(payload.error, 240);
  if (direct) return direct;
  const nested = record(payload.error);
  return nested ? nonEmpty(nested.message, 240) : null;
}

/** Convert a city-local date/minute pair into an exact UTC ISO instant. */
export function localWallTimeToInstant(
  isoDate: string,
  minuteOfDay: number,
  timeZone: string,
): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate);
  if (!match || !Number.isInteger(minuteOfDay) || minuteOfDay < 0 || minuteOfDay >= 2880) {
    throw new ElectionChartApiError('invalid-request', 'The local chart time is invalid.');
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const calendarDate = new Date(Date.UTC(year, month - 1, day));
  if (
    year < 100 || year > 9999
    || calendarDate.getUTCFullYear() !== year
    || calendarDate.getUTCMonth() + 1 !== month
    || calendarDate.getUTCDate() !== day
  ) {
    throw new ElectionChartApiError('invalid-request', 'The local chart date is invalid.');
  }
  const wallEpoch = calendarDate.getTime() + minuteOfDay * 60_000;
  const wall = new Date(wallEpoch);
  const target = {
    year: wall.getUTCFullYear(), month: wall.getUTCMonth() + 1, day: wall.getUTCDate(),
    hour: wall.getUTCHours(), minute: wall.getUTCMinutes(),
  };
  let formatter: Intl.DateTimeFormat;
  try {
    formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hourCycle: 'h23',
    });
  } catch {
    throw new ElectionChartApiError('invalid-request', 'The selected time zone is invalid.');
  }
  const zonedParts = (epoch: number): Record<string, number> => {
    const values: Record<string, number> = {};
    for (const part of formatter.formatToParts(new Date(epoch))) {
      if (part.type !== 'literal') values[part.type] = Number(part.value);
    }
    return values;
  };
  // Discover every UTC offset observed around this civil date, then retain
  // only instants that round-trip to the requested wall minute. This makes
  // DST gaps and repeated fold minutes explicit instead of silently choosing
  // one of two possible instants.
  const offsets = new Set<number>();
  for (let deltaHours = -36; deltaHours <= 36; deltaHours += 6) {
    const probe = wallEpoch + deltaHours * 60 * 60 * 1000;
    const parts = zonedParts(probe);
    const represented = Date.UTC(
      parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second,
    );
    offsets.add(represented - probe);
  }
  const candidates = new Set<number>();
  for (const offset of offsets) {
    const candidate = wallEpoch - offset;
    const roundTrip = zonedParts(candidate);
    if (
      roundTrip.year === target.year && roundTrip.month === target.month
      && roundTrip.day === target.day && roundTrip.hour === target.hour
      && roundTrip.minute === target.minute
    ) candidates.add(candidate);
  }
  if (candidates.size !== 1) {
    throw new ElectionChartApiError(
      'invalid-request',
      candidates.size
        ? 'That local time is ambiguous in the selected time zone.'
        : 'That local time does not exist in the selected time zone.',
    );
  }
  return new Date([...candidates][0]).toISOString();
}

export async function deriveElectionCharts(
  input: ElectionChartRequest,
  options: ElectionChartApiOptions = {},
): Promise<ElectionChartDerivation> {
  validateRequest(input);
  const fetcher = options.fetcher || globalThis.fetch;
  const controller = new AbortController();
  const onExternalAbort = (): void => controller.abort();
  options.signal?.addEventListener('abort', onExternalAbort, { once: true });
  const timeout = globalThis.setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  );
  try {
    const response = await fetcher(
      `${options.baseUrl || electionChartApiBase()}/muhurta/election-charts`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_version: ELECTION_CHART_CONTRACT_VERSION,
          location: input.location,
          instants: input.instants,
        }),
        cache: 'no-store',
        credentials: 'omit',
        signal: controller.signal,
      },
    );
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const retryAfter = Number(response.headers.get('Retry-After'));
      throw new ElectionChartApiError(
        response.status === 429 ? 'rate-limited' : 'request-failed',
        apiErrorMessage(payload) || (response.status === 429
          ? 'Chart screening is busy. Wait a moment and try again.'
          : 'Chart screening could not complete this request.'),
        response.status,
        Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : null,
      );
    }

    const result = record(payload);
    const engine = result ? record(result.engine) : null;
    const location = result ? record(result.location) : null;
    const data = result ? record(result.data) : null;
    const rawCharts = data && Array.isArray(data.charts) ? data.charts : null;
    const charts = rawCharts?.map((chart, index) => parseSnapshot(chart, input.instants[index])) || [];
    const engineName = engine ? nonEmpty(engine.name, 60) : null;
    const engineVersion = engine ? nonEmpty(engine.version, 40) : null;
    const ayanamsha = engine ? nonEmpty(engine.ayanamsha, 40) : null;
    const ephemeris = engine ? nonEmpty(engine.ephemeris, 20) : null;
    const nodeConvention = engine ? nonEmpty(engine.node_convention, 20) : null;
    const latitude = location ? finite(location.latitude) : null;
    const longitude = location ? finite(location.longitude) : null;
    const timezone = location ? nonEmpty(location.timezone, 80) : null;
    if (
      result?.contract_version !== ELECTION_CHART_CONTRACT_VERSION
      || result.house_system !== 'whole_sign'
      || engineName !== 'DashaFlow' || !engineVersion || ayanamsha !== 'Lahiri'
      || nodeConvention !== 'mean'
      || (ephemeris !== 'swiss' && ephemeris !== 'moshier'
        && ephemeris !== 'unknown' && ephemeris !== 'mixed')
      || latitude !== input.location.latitude || longitude !== input.location.longitude
      || timezone !== input.location.timezone
      || !rawCharts || rawCharts.length !== input.instants.length
      || charts.some(chart => chart === null)
    ) {
      throw new ElectionChartApiError(
        'invalid-response',
        'The chart service returned an invalid response.',
      );
    }
    return {
      contractVersion: ELECTION_CHART_CONTRACT_VERSION,
      engine: {
        name: engineName,
        version: engineVersion,
        ayanamsha,
        ephemeris: ephemeris as ElectionChartEngine['ephemeris'],
        nodeConvention: 'mean',
      },
      houseSystem: 'whole_sign',
      location: input.location,
      charts: charts as ElectionChartSnapshot[],
    };
  } catch (error) {
    if (error instanceof ElectionChartApiError) throw error;
    if (controller.signal.aborted) {
      throw new ElectionChartApiError('timeout', 'Chart screening took too long.');
    }
    throw new ElectionChartApiError('network', 'Chart screening is temporarily unavailable.');
  } finally {
    globalThis.clearTimeout(timeout);
    options.signal?.removeEventListener('abort', onExternalAbort);
  }
}
