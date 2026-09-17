export function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

/** Keep endpoint-specific error identity while decoding required response fields. */
export function required<T>(value: T | null, invalid: () => Error): T {
  if (value === null) throw invalid();
  return value;
}

export function boundedArray(value: unknown, min: number, max: number): unknown[] | null {
  if (!Array.isArray(value)) return null;
  return value.length >= min && value.length <= max ? value : null;
}

export function finite(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

export function withinRange(value: number | null, min: number, max: number): value is number {
  return value !== null && Number.isFinite(value) && value >= min && value <= max;
}

export function nonEmpty(value: unknown, maxLength = 200): string | null {
  return typeof value === 'string' && value.trim() && value.length <= maxLength
    ? value.trim()
    : null;
}

export function exactNonEmpty(value: unknown, maxLength = 200): string | null {
  return typeof value === 'string'
    && value.length > 0
    && value.length <= maxLength
    && value.trim() === value
    ? value
    : null;
}
