export interface BirthProfileCalculationActivation {
  enabled: boolean;
  source: 'explicit' | 'local-default' | 'disabled';
}

export type BirthProfileLocation = Pick<Location, 'hostname'> | undefined;

function configuredBirthProfileFlag(): string | undefined {
  return (
    import.meta as ImportMeta & { env?: Record<string, string | undefined> }
  ).env?.VITE_BIRTH_PROFILE_API_ENABLED;
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
