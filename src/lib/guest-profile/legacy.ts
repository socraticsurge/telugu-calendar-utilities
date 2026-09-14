import { RASI_NAMES } from '../../data/rasis';
import {
  GUEST_PROFILE_SCHEMA_VERSION,
  GUEST_PROFILE_STORAGE_KEY,
  type LegacyGuestProfileFields,
  type LegacyGuestProfileRow,
  type ProfileStorage,
} from './types';
import { canonical, text } from './values';


/**
 * Lazily resolve browser storage so an origin that denies access to the
 * `localStorage` property still reaches GuestProfileStore's in-memory fallback.
 */
export function browserProfileStorage(
  storageProvider: () => ProfileStorage = () => globalThis.localStorage,
): ProfileStorage {
  return {
    getItem(key) {
      return storageProvider().getItem(key);
    },
    setItem(key, value) {
      storageProvider().setItem(key, value);
    },
    removeItem(key) {
      storageProvider().removeItem?.(key);
    },
  };
}

export function hasProfileContent(value: Record<string, unknown>): boolean {
  return ['name', 'nak', 'nakshatra', 'pada', 'lagna']
    .some(key => text(value[key]) !== '');
}

export const STORED_PROFILE_KEYS = new Set([
  'id', 'schemaVersion', 'name', 'nak', 'nakshatra', 'pada', 'lagna',
]);

export function isBlankLegacyPlaceholder(value: Record<string, unknown>): boolean {
  const legacyKeys = new Set(['name', 'nak', 'nakshatra', 'pada', 'lagna']);
  const keys = Object.keys(value);
  return keys.length > 0 && keys.every(key => legacyKeys.has(key));
}

export function hasUnownedProfileKeys(value: Record<string, unknown>): boolean {
  return Object.keys(value).some(key => !STORED_PROFILE_KEYS.has(key));
}

/** Safe compatibility reader for the two legacy panels during migration. */
export function readLegacyGuestProfileRows(storage: ProfileStorage): LegacyGuestProfileRow[] {
  try {
    const parsed: unknown = JSON.parse(storage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
    return Array.isArray(parsed)
      ? parsed.filter((value): value is LegacyGuestProfileRow =>
        Boolean(value) && typeof value === 'object' && !Array.isArray(value))
      : [];
  } catch {
    return [];
  }
}

/**
 * Writes only the form-controlled prefix of the legacy array.  The Tarabalam
 * form still has fewer visible rows than the shared store can contain, so a
 * compatibility edit must leave hidden lagna-only rows and newer-schema rows
 * (including arbitrary future payload values) unchanged.
 */
export function writeLegacyGuestProfileRows(
  storage: ProfileStorage,
  fields: readonly LegacyGuestProfileFields[],
): void {
  let previous: unknown[] = [];
  try {
    const parsed: unknown = JSON.parse(storage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
    if (Array.isArray(parsed)) previous = parsed;
  } catch {
    // Match the legacy writer's recovery: a fresh editable prefix replaces an
    // unreadable payload, while valid trailing values are never discarded.
  }

  const next = previous.slice();
  fields.forEach((row, index) => {
    const current = previous[index];
    next[index] = mergeLegacyGuestProfileRow(
      current && typeof current === 'object' && !Array.isArray(current)
        ? current as LegacyGuestProfileRow
        : {},
      row,
    );
  });
  storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify(next));
}

/** Remove one legacy row without filtering or rebuilding unrelated rows. */
export function removeLegacyGuestProfileRow(storage: ProfileStorage, index: number): void {
  let previous: unknown[] = [];
  try {
    const parsed: unknown = JSON.parse(storage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
    if (Array.isArray(parsed)) previous = parsed;
  } catch {
    // An unreadable payload has no compatible row to retain.
  }
  previous.splice(index, 1);
  storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify(previous));
}

/** Compatibility data is deliberately permissive; consumers must validate it. */
export function canonicalLegacyGuestProfileLagna(value: unknown): string | null {
  return canonical(value, RASI_NAMES);
}

/** Preserve additive/future fields while the legacy Muhurtam form still writes this key. */
export function mergeLegacyGuestProfileRow(
  previous: LegacyGuestProfileRow,
  fields: LegacyGuestProfileFields,
): LegacyGuestProfileRow {
  const next: LegacyGuestProfileRow = { ...previous, ...fields };
  if (typeof previous.id === 'string') {
    next.id = previous.id;
    if (typeof previous.schemaVersion !== 'number') {
      next.schemaVersion = GUEST_PROFILE_SCHEMA_VERSION;
    }
  }
  return next;
}
