import { record, nonEmpty } from './values';

export function apiErrorMessage(value: unknown): string | null {
  const payload = record(value);
  if (!payload) return null;
  const direct = nonEmpty(payload.error, 240);
  if (direct) return direct;
  const nested = record(payload.error);
  return nested ? nonEmpty(nested.message, 240) : null;
}

export function retryAfterSeconds(response: Response): number | null {
  const seconds = Number(response.headers.get('Retry-After'));
  return Number.isFinite(seconds) && seconds > 0 ? seconds : null;
}

export function jsonPost(body: unknown, signal: AbortSignal): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store',
    credentials: 'omit',
    signal,
  };
}
