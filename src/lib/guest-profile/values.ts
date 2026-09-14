import { type GuestProfilePada } from './types';


let fallbackIdSequence = 0;

let fallbackRevisionSequence = 0;

export function text(value: unknown, maxLength = 80): string {
  return typeof value === 'string' ? value.trim().slice(0, maxLength) : '';
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function withinRange(value: number | null, minimum: number, maximum: number): value is number {
  return value !== null && value >= minimum && value <= maximum;
}

export function canonical(value: unknown, allowed: readonly string[]): string | null {
  const candidate = text(value);
  return allowed.includes(candidate) ? candidate : null;
}

export function exactText(value: unknown, maxLength: number): string | null {
  return typeof value === 'string'
    && value.length > 0
    && value.length <= maxLength
    && value.trim() === value
    ? value
    : null;
}

export function exactCanonical(value: unknown, allowed: readonly string[]): string | null {
  const candidate = exactText(value, 80);
  return candidate && allowed.includes(candidate) ? candidate : null;
}

export function pada(value: unknown): GuestProfilePada | null {
  if (value === '' || value === null || value === undefined) return null;
  const candidate = Number(value);
  return candidate === 1 || candidate === 2 || candidate === 3 || candidate === 4
    ? candidate
    : null;
}

export function exactPada(value: unknown): 1 | 2 | 3 | 4 | null {
  return typeof value === 'number' ? pada(value) : null;
}

export function validStoredId(value: unknown): value is string {
  return typeof value === 'string' && /^[A-Za-z0-9_-]{8,100}$/.test(value);
}

export function validRevision(value: unknown): value is string {
  return typeof value === 'string' && /^[A-Za-z0-9_-]{8,100}$/.test(value);
}

export function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value);
  return actual.length === keys.length && actual.every(key => keys.includes(key));
}

export function finite(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

export function isoDate(value: unknown): string | null {
  const candidate = text(value, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(candidate)) return null;
  const parsed = new Date(`${candidate}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== candidate
    ? null
    : candidate;
}

export function isoTime(value: unknown): string | null {
  const candidate = text(value, 5);
  return /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(candidate) ? candidate : null;
}

export function defaultIdFactory(): string {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {
    return `guest_${globalThis.crypto.randomUUID()}`;
  }
  if (globalThis.crypto && typeof globalThis.crypto.getRandomValues === 'function') {
    const values = globalThis.crypto.getRandomValues(new Uint32Array(4));
    return `guest_${Array.from(values, value => value.toString(36)).join('_')}`;
  }
  fallbackIdSequence += 1;
  return `guest_${Date.now().toString(36)}_${fallbackIdSequence.toString(36)}`;
}

export function defaultRevisionFactory(): string {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {
    return `revision_${globalThis.crypto.randomUUID()}`;
  }
  if (globalThis.crypto && typeof globalThis.crypto.getRandomValues === 'function') {
    const values = globalThis.crypto.getRandomValues(new Uint32Array(4));
    return `revision_${Array.from(values, value => value.toString(36)).join('_')}`;
  }
  fallbackRevisionSequence += 1;
  return `revision_${Date.now().toString(36)}_${fallbackRevisionSequence.toString(36)}`;
}
