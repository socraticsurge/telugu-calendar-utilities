import { isLoopbackHostname, trimTrailingSlashes } from '../remote-calculation-activation';

const PRODUCTION_API_BASE = 'https://astrochaganti.com/api/guest';
const LOCAL_API_BASE = 'http://127.0.0.1:3000/api/guest';
function normalizedConfiguredBase(
  configuredBase: string | undefined,
  trust: (url: URL) => boolean,
): string | null {
  if (!configuredBase) return null;
  try {
    const url = new URL(configuredBase);
    if (!trust(url)) return null;
    return trimTrailingSlashes(configuredBase);
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
    && trimTrailingSlashes(url.pathname) === canonical.pathname
    && !url.username
    && !url.password
    && !url.search
    && !url.hash;
}

export function trustedApiBase(configuredBase: string | undefined, local: boolean): string {
  if (local) return normalizedConfiguredBase(configuredBase, isTrustedLoopbackBase) || LOCAL_API_BASE;
  return normalizedConfiguredBase(configuredBase, isTrustedProductionBase) || PRODUCTION_API_BASE;
}
