export interface RemoteCalculationActivation {
  enabled: boolean;
  source: 'explicit' | 'local-default' | 'disabled';
}

export type BirthProfileCalculationActivation = RemoteCalculationActivation;
export type ElectionChartCalculationActivation = RemoteCalculationActivation;
export type RemoteCalculationLocation = Pick<Location, 'hostname'> | undefined;
export type BirthProfileLocation = RemoteCalculationLocation;
export type ElectionChartLocation = RemoteCalculationLocation;

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

/**
 * A missing flag keeps loopback development convenient. Every public build
 * and every explicit local configuration fails closed unless the value is the
 * exact, case-sensitive string `true`.
 */
export function birthProfileCalculationActivation(
  locationLike: BirthProfileLocation = globalThis.location,
  flag: string | undefined = configuredBirthProfileFlag(),
): BirthProfileCalculationActivation {
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

export function birthProfileCalculationEnabled(
  locationLike?: BirthProfileLocation,
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
  locationLike: ElectionChartLocation = globalThis.location,
  flag: string | undefined = configuredElectionChartFlag(),
): ElectionChartCalculationActivation {
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

export function electionChartCalculationEnabled(
  locationLike?: ElectionChartLocation,
  flag?: string,
): boolean {
  return electionChartCalculationActivation(locationLike, flag).enabled;
}
