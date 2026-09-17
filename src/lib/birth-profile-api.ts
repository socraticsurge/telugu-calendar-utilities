import {
  birthProfileCalculationEnabled, isLoopbackHostname, type RemoteCalculationLocation,
} from './remote-calculation-activation';
import {
  BirthProfileApiError, type BirthProfileApiOptions, type BirthProfileDerivationInput,
  type BirthProfileDerivation, type BirthPlaceSearchResult,
} from './remote-api/contracts';
import { trustedApiBase } from './remote-api/base';
import { apiErrorMessage, retryAfterSeconds, jsonPost } from './remote-api/http';
import { parsePlaceSearch } from './remote-api/places-response';
import { parseBirthProfile } from './remote-api/birth-response';

export {
  BIRTH_PROFILE_CONTRACT_VERSION, BIRTH_PROFILE_ENGINE_NAME, BIRTH_PROFILE_AYANAMSHA,
  BIRTH_CHART_PLANET_NAMES, isContractRoundedDegree, roundedMoonMatchesBirthFacts,
  wholeSignHousesMatch, fixedGrahaFactsMatch,
} from './chart-contracts';
export type { BirthChartPlanet, BirthProfileEngine, BirthPada } from './chart-contracts';
export { BirthProfileApiError } from './remote-api/contracts';
export type {
  BirthProfileApiErrorCode, BirthProfileApiOptions, BirthProfileDerivationInput,
  BirthProfileDerivation, BirthPlaceCandidate, BirthPlaceAttribution, BirthPlaceSearchResult,
} from './remote-api/contracts';

const DEFAULT_TIMEOUT_MS = 15_000;

function configuredBirthProfileApiBase(): string | undefined {
  return (
    import.meta as ImportMeta & { env?: Record<string, string | undefined> }
  ).env?.VITE_BIRTH_PROFILE_API_BASE;
}

export function birthProfileApiBase(
  locationLike: RemoteCalculationLocation = globalThis.location,
  configuredBase: string | undefined = configuredBirthProfileApiBase(),
): string {
  return trustedApiBase(configuredBase, Boolean(locationLike && isLoopbackHostname(locationLike.hostname)));
}

function birthHttpError(response: Response, payload: unknown): BirthProfileApiError {
  const rateLimited = response.status === 429;
  const fallback = rateLimited
    ? 'Too many requests. Wait a moment and try again.'
    : 'The calculation service could not complete this request.';
  return new BirthProfileApiError(
    rateLimited ? 'rate-limited' : 'request-failed',
    apiErrorMessage(payload) || fallback,
    response.status,
    retryAfterSeconds(response),
  );
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
    const response = await fetcher(
      `${birthProfileApiBase(locationLike, options.baseUrl)}${path}`,
      jsonPost(body, controller.signal),
    );
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      throw birthHttpError(response, payload);
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
  return parsePlaceSearch(await postJson('/places/search', { query: query.trim() }, options));
}

export async function deriveBirthProfile(
  input: BirthProfileDerivationInput,
  options: BirthProfileApiOptions = {},
): Promise<BirthProfileDerivation> {
  return parseBirthProfile(await postJson('/profile/derive', {
    date_of_birth: input.dateOfBirth,
    time_of_birth: input.timeOfBirth,
    latitude: input.latitude,
    longitude: input.longitude,
    timezone: input.timezone,
  }, options));
}
