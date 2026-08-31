import {
  birthProfileCalculationEnabled,
  isLoopbackHostname,
  type BirthProfileLocation,
} from './remote-calculation-activation';

export const BIRTH_PROFILE_CONTRACT_VERSION = '1.0' as const;

const PRODUCTION_API_BASE = 'https://astrochaganti.com/api/guest';
const LOCAL_API_BASE = 'http://127.0.0.1:3000/api/guest';
const DEFAULT_TIMEOUT_MS = 15_000;

export interface BirthPlaceCandidate {
  id: string;
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface BirthPlaceSearchResult {
  results: BirthPlaceCandidate[];
  attribution: string;
}

export interface BirthProfileDerivationInput {
  dateOfBirth: string;
  timeOfBirth: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface BirthChartPlanet {
  name: string;
  rashi: string;
  degree: number;
  house: number;
  retrograde: boolean;
}

export interface BirthProfileEngine {
  name: string;
  version: string;
  ayanamsha: string;
  ephemeris: 'swiss' | 'moshier' | 'unknown';
}

export interface BirthProfileDerivation {
  contractVersion: typeof BIRTH_PROFILE_CONTRACT_VERSION;
  engine: BirthProfileEngine;
  nakshatra: string;
  pada: 1 | 2 | 3 | 4;
  janmaRashi: string;
  lagna: string;
  lagnaDegree: number;
  planets: BirthChartPlanet[];
}

export type BirthProfileApiErrorCode =
  | 'disabled'
  | 'invalid-response'
  | 'network'
  | 'rate-limited'
  | 'request-failed'
  | 'timeout';

export class BirthProfileApiError extends Error {
  constructor(
    public readonly code: BirthProfileApiErrorCode,
    message: string,
    public readonly status: number | null = null,
    public readonly retryAfterSeconds: number | null = null,
  ) {
    super(message);
    this.name = 'BirthProfileApiError';
  }
}

export interface BirthProfileApiOptions {
  activationFlag?: string;
  baseUrl?: string;
  fetcher?: typeof fetch;
  locationLike?: BirthProfileLocation;
  timeoutMs?: number;
}

function configuredBirthProfileApiBase(): string | undefined {
  return (
    import.meta as ImportMeta & { env?: Record<string, string | undefined> }
  ).env?.VITE_BIRTH_PROFILE_API_BASE;
}

function normalizedConfiguredBase(
  configuredBase: string | undefined,
  trust: (url: URL) => boolean,
): string | null {
  if (!configuredBase) return null;
  try {
    const url = new URL(configuredBase);
    if (!trust(url)) return null;
    return configuredBase.replace(/\/+$/, '');
  } catch {
    return null;
  }
}

function isTrustedLoopbackBase(url: URL): boolean {
  return url.protocol === 'http:'
    && isLoopbackHostname(url.hostname)
    && !url.username
    && !url.password
    && !url.search
    && !url.hash;
}

function isTrustedProductionBase(url: URL): boolean {
  const canonical = new URL(PRODUCTION_API_BASE);
  return url.protocol === 'https:'
    && url.hostname === canonical.hostname
    && url.port === canonical.port
    && url.pathname.replace(/\/+$/, '') === canonical.pathname
    && !url.username
    && !url.password
    && !url.search
    && !url.hash;
}

export function birthProfileApiBase(
  locationLike: BirthProfileLocation = globalThis.location,
  configuredBase: string | undefined = configuredBirthProfileApiBase(),
): string {
  if (locationLike && isLoopbackHostname(locationLike.hostname)) {
    return normalizedConfiguredBase(configuredBase, isTrustedLoopbackBase) || LOCAL_API_BASE;
  }
  return normalizedConfiguredBase(configuredBase, isTrustedProductionBase) || PRODUCTION_API_BASE;
}

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function finite(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function nonEmpty(value: unknown, maxLength = 200): string | null {
  return typeof value === 'string' && value.trim() && value.length <= maxLength
    ? value.trim()
    : null;
}

function parsePlace(value: unknown): BirthPlaceCandidate | null {
  const item = record(value);
  if (!item) return null;
  const id = nonEmpty(item.id, 160);
  const label = nonEmpty(item.label, 240);
  const latitude = finite(item.latitude);
  const longitude = finite(item.longitude);
  const timezone = nonEmpty(item.timezone, 80);
  if (!id || !label || latitude === null || longitude === null || !timezone) return null;
  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) return null;
  return { id, label, latitude, longitude, timezone };
}

function parsePlanet(value: unknown): BirthChartPlanet | null {
  const item = record(value);
  if (!item) return null;
  const name = nonEmpty(item.name, 40);
  const rashi = nonEmpty(item.rashi, 40);
  const degree = finite(item.degree);
  const house = finite(item.house);
  if (!name || !rashi || degree === null || house === null || typeof item.retrograde !== 'boolean') {
    return null;
  }
  if (degree < 0 || degree >= 30 || !Number.isInteger(house) || house < 1 || house > 12) return null;
  return { name, rashi, degree, house, retrograde: item.retrograde };
}

function apiErrorMessage(value: unknown): string | null {
  const payload = record(value);
  if (!payload) return null;
  const direct = nonEmpty(payload.error, 240);
  if (direct) return direct;
  const nested = record(payload.error);
  return nested ? nonEmpty(nested.message, 240) : null;
}

async function postJson(
  path: string,
  body: Record<string, unknown>,
  options: BirthProfileApiOptions,
): Promise<unknown> {
  const locationLike = options.locationLike ?? globalThis.location;
  if (!birthProfileCalculationEnabled(locationLike, options.activationFlag)) {
    throw new BirthProfileApiError(
      'disabled',
      'Birth-detail calculation is not active in this public build. Enter known astrology details manually instead.',
    );
  }
  const fetcher = options.fetcher || globalThis.fetch;
  const controller = new AbortController();
  const timeout = globalThis.setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  );
  try {
    const response = await fetcher(`${birthProfileApiBase(locationLike, options.baseUrl)}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
      credentials: 'omit',
      signal: controller.signal,
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const message = apiErrorMessage(payload)
        || (response.status === 429
          ? 'Too many requests. Wait a moment and try again.'
          : 'The calculation service could not complete this request.');
      const retryAfter = Number(response.headers.get('Retry-After'));
      throw new BirthProfileApiError(
        response.status === 429 ? 'rate-limited' : 'request-failed',
        message,
        response.status,
        Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : null,
      );
    }
    return payload;
  } catch (error) {
    if (error instanceof BirthProfileApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new BirthProfileApiError('timeout', 'The calculation took too long. Try again.');
    }
    throw new BirthProfileApiError(
      'network',
      'The calculation service is unavailable. Check your connection and try again.',
    );
  } finally {
    globalThis.clearTimeout(timeout);
  }
}

export async function searchBirthPlaces(
  query: string,
  options: BirthProfileApiOptions = {},
): Promise<BirthPlaceSearchResult> {
  const payload = record(await postJson('/places/search', { query: query.trim() }, options));
  const data = payload ? record(payload.data) : null;
  const rawResults = data && Array.isArray(data.results) ? data.results : null;
  const attribution = data ? nonEmpty(data.attribution, 240) : null;
  if (!rawResults || !attribution) {
    throw new BirthProfileApiError('invalid-response', 'Place search returned an invalid response.');
  }
  const results = rawResults.map(parsePlace).filter((value): value is BirthPlaceCandidate => value !== null);
  if (results.length !== rawResults.length || results.length > 5) {
    throw new BirthProfileApiError('invalid-response', 'Place search returned an invalid response.');
  }
  return { results, attribution };
}

export async function deriveBirthProfile(
  input: BirthProfileDerivationInput,
  options: BirthProfileApiOptions = {},
): Promise<BirthProfileDerivation> {
  const payload = record(await postJson('/profile/derive', {
    date_of_birth: input.dateOfBirth,
    time_of_birth: input.timeOfBirth,
    latitude: input.latitude,
    longitude: input.longitude,
    timezone: input.timezone,
  }, options));
  const engineRecord = payload ? record(payload.engine) : null;
  const data = payload ? record(payload.data) : null;
  const version = payload ? nonEmpty(payload.contract_version, 20) : null;
  const name = engineRecord ? nonEmpty(engineRecord.name, 60) : null;
  const engineVersion = engineRecord ? nonEmpty(engineRecord.version, 40) : null;
  const ayanamsha = engineRecord ? nonEmpty(engineRecord.ayanamsha, 40) : null;
  const ephemeris = engineRecord ? nonEmpty(engineRecord.ephemeris, 20) : null;
  const nakshatra = data ? nonEmpty(data.nakshatra, 60) : null;
  const pada = data ? finite(data.pada) : null;
  const janmaRashi = data ? nonEmpty(data.janma_rashi, 40) : null;
  const lagna = data ? nonEmpty(data.lagna, 40) : null;
  const lagnaDegree = data ? finite(data.lagna_degree) : null;
  const rawPlanets = data && Array.isArray(data.planets) ? data.planets : null;
  const planets = rawPlanets
    ? rawPlanets.map(parsePlanet).filter((planet): planet is BirthChartPlanet => planet !== null)
    : [];

  if (
    version !== BIRTH_PROFILE_CONTRACT_VERSION
    || !name || !engineVersion || !ayanamsha
    || (ephemeris !== 'swiss' && ephemeris !== 'moshier' && ephemeris !== 'unknown')
    || !nakshatra || (pada !== 1 && pada !== 2 && pada !== 3 && pada !== 4)
    || !janmaRashi || !lagna || lagnaDegree === null || lagnaDegree < 0 || lagnaDegree >= 30
    || !rawPlanets || planets.length !== 9 || planets.length !== rawPlanets.length
  ) {
    throw new BirthProfileApiError('invalid-response', 'The calculation service returned an invalid response.');
  }

  return {
    contractVersion: BIRTH_PROFILE_CONTRACT_VERSION,
    engine: {
      name,
      version: engineVersion,
      ayanamsha,
      ephemeris,
    },
    nakshatra,
    pada,
    janmaRashi,
    lagna,
    lagnaDegree,
    planets,
  };
}
