export interface RemoteCalculationActivation {
  enabled: boolean;
  source: 'explicit' | 'local-default' | 'disabled';
}

export type RemoteCalculationLocation = Pick<Location, 'hostname'>;

function configuredBirthProfileFlag(): string | undefined {
  return (
    import.meta as ImportMeta & { env?: Record<string, string | undefined> }
  ).env?.VITE_BIRTH_PROFILE_API_ENABLED;
}

function configuredElectionChartFlag(): string | undefined {
  return (
    import.meta as ImportMeta & { env?: Record<string, string | undefined> }
  ).env?.VITE_ELECTION_CHART_API_ENABLED;
}

export function isLoopbackHostname(hostname: string): boolean {
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]';
}

export function trimTrailingSlashes(value: string): string {
  let end = value.length;
  while (end > 0 && value[end - 1] === '/') end -= 1;
  return value.slice(0, end);
}

/**
 * A missing flag keeps loopback development convenient. Every public build
 * and every explicit local configuration fails closed unless the value is the
 * exact, case-sensitive string `true`.
 */
function remoteCalculationActivation(
  locationLike: RemoteCalculationLocation | undefined,
  flag: string | undefined,
): RemoteCalculationActivation {
  if (flag !== undefined) {
    return flag === 'true'
      ? { enabled: true, source: 'explicit' }
      : { enabled: false, source: 'disabled' };
  }
  if (locationLike && isLoopbackHostname(locationLike.hostname)) {
    return { enabled: true, source: 'local-default' };
  }
  return { enabled: false, source: 'disabled' };
}

export function birthProfileCalculationActivation(
  locationLike: RemoteCalculationLocation = globalThis.location,
  flag: string | undefined = configuredBirthProfileFlag(),
): RemoteCalculationActivation {
  return remoteCalculationActivation(locationLike, flag);
}

export function birthProfileCalculationEnabled(
  locationLike?: RemoteCalculationLocation,
  flag?: string,
): boolean {
  return birthProfileCalculationActivation(locationLike, flag).enabled;
}

/**
 * Election-chart activation is deliberately independent from birth-profile
 * activation. A missing flag is convenient only on loopback; every public
 * build and every explicit configuration fails closed unless the value is the
 * exact, case-sensitive string `true`.
 */
export function electionChartCalculationActivation(
  locationLike: RemoteCalculationLocation = globalThis.location,
  flag: string | undefined = configuredElectionChartFlag(),
): RemoteCalculationActivation {
  return remoteCalculationActivation(locationLike, flag);
}

export function electionChartCalculationEnabled(
  locationLike?: RemoteCalculationLocation,
  flag?: string,
): boolean {
  return electionChartCalculationActivation(locationLike, flag).enabled;
}
