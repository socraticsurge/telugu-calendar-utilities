import {
  electionChartCalculationEnabled, isLoopbackHostname,
  type RemoteCalculationLocation as ElectionChartBrowserLocation,
} from './remote-calculation-activation';
import {
  ElectionChartApiError, ELECTION_CHART_CONTRACT_VERSION, type ElectionChartApiOptions,
  type ElectionChartRequest, type ElectionChartDerivation,
} from './remote-api/contracts';
import { trustedApiBase } from './remote-api/base';
import { apiErrorMessage, retryAfterSeconds, jsonPost } from './remote-api/http';
import { validateRequest, parseElectionChartDerivation } from './remote-api/election-response';

export {
  ElectionChartApiError, ELECTION_CHART_CONTRACT_VERSION, ELECTION_CHART_BATCH_LIMIT,
} from './remote-api/contracts';
export type {
  ElectionChartApiErrorCode, ElectionChartApiOptions, ElectionChartRequest,
  ElectionChartDerivation, ElectionChartEngine, ElectionChartLocation, ElectionChartSnapshot,
} from './remote-api/contracts';
export { localWallTimeToInstant } from './local-chart-time';

const DEFAULT_TIMEOUT_MS = 20_000;

function configuredElectionChartApiBase(): string | undefined {
  return (
    import.meta as ImportMeta & { env?: Record<string, string | undefined> }
  ).env?.VITE_ELECTION_CHART_API_BASE;
}

export function electionChartApiBase(
  configuredBase: string | undefined = configuredElectionChartApiBase(),
  locationLike: ElectionChartBrowserLocation = globalThis.location,
): string {
  return trustedApiBase(configuredBase, isLoopbackHostname(locationLike.hostname));
}

function electionChartHttpError(response: Response, payload: unknown): ElectionChartApiError {
  const rateLimited = response.status === 429;
  const fallback = rateLimited
    ? 'Chart screening is busy. Wait a moment and try again.'
    : 'Chart screening could not complete this request.';
  return new ElectionChartApiError(
    rateLimited ? 'rate-limited' : 'request-failed',
    apiErrorMessage(payload) || fallback,
    response.status,
    retryAfterSeconds(response),
  );
}

export async function deriveElectionCharts(
  input: ElectionChartRequest,
  options: ElectionChartApiOptions = {},
): Promise<ElectionChartDerivation> {
  validateRequest(input);
  const locationLike = options.locationLike ?? globalThis.location;
  if (!electionChartCalculationEnabled(locationLike, options.activationFlag)) {
    throw new ElectionChartApiError(
      'disabled',
      'Exact election-chart screening is not active in this public build.',
    );
  }
  const baseUrl = electionChartApiBase(options.baseUrl, locationLike);
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
      `${baseUrl}/muhurta/election-charts`,
      jsonPost({
        contract_version: ELECTION_CHART_CONTRACT_VERSION,
        location: input.location,
        instants: input.instants,
      }, controller.signal),
    );
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) throw electionChartHttpError(response, payload);
    return parseElectionChartDerivation(payload, input);
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
