import { NAKSHATRA_NAMES, RASI_NAMES, rasiFromStar } from '../data/rasis';

export const GUEST_PROFILE_STORAGE_KEY = 'tc-tb-profiles';
export const GUEST_PROFILE_SCHEMA_VERSION = 1 as const;
export const MAX_GUEST_PROFILES = 4;

export type ProfilePersistence = 'persistent' | 'memory';
export type ProfileStoreIssue =
  | 'malformed-storage'
  | 'storage-unavailable'
  | 'unsupported-storage-version'
  | null;
export type ProfileStoreErrorCode = 'empty-profile' | 'profile-limit' | 'profile-not-found';

export interface ProfileStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export interface GuestProfile {
  id: string;
  schemaVersion: typeof GUEST_PROFILE_SCHEMA_VERSION;
  name: string;
  nakshatra: string | null;
  pada: 1 | 2 | 3 | 4 | null;
  lagna: string | null;
}

export interface GuestProfileDraft {
  name?: unknown;
  nakshatra?: unknown;
  pada?: unknown;
  lagna?: unknown;
}

export interface GuestProfileReadiness {
  muhurta: boolean;
  horoscope: boolean;
  janmaRasi: string | null;
  missingForHoroscope: 'nakshatra' | 'pada' | null;
}

export interface GuestProfileSnapshot {
  profiles: ReadonlyArray<Readonly<GuestProfile>>;
  persistence: ProfilePersistence;
  issue: ProfileStoreIssue;
}

export type GuestProfileListener = (snapshot: GuestProfileSnapshot) => void;

export interface LegacyGuestProfileRow extends Record<string, unknown> {
  id?: string;
  schemaVersion?: number;
  name?: string;
  nak?: string;
  nakshatra?: string;
  pada?: string | number;
  lagna?: string;
}

export interface LegacyGuestProfileFields {
  name: string;
  nak: string;
  pada: string | number;
  lagna: string;
}

interface StoredProfileRecord {
  id: string;
  schemaVersion: typeof GUEST_PROFILE_SCHEMA_VERSION;
  name: string;
  nak: string;
  pada: 1 | 2 | 3 | 4 | '';
  lagna: string;
}

interface GuestProfileStoreOptions {
  idFactory?: () => string;
}

let fallbackIdSequence = 0;

export class GuestProfileStoreError extends Error {
  constructor(public readonly code: ProfileStoreErrorCode) {
    super(code);
    this.name = 'GuestProfileStoreError';
  }
}

function text(value: unknown, maxLength = 80): string {
  return typeof value === 'string' ? value.trim().slice(0, maxLength) : '';
}

function canonical(value: unknown, allowed: readonly string[]): string | null {
  const candidate = text(value);
  return allowed.includes(candidate) ? candidate : null;
}

function pada(value: unknown): 1 | 2 | 3 | 4 | null {
  if (value === '' || value === null || value === undefined) return null;
  const candidate = Number(value);
  return candidate === 1 || candidate === 2 || candidate === 3 || candidate === 4
    ? candidate
    : null;
}

function validStoredId(value: unknown): value is string {
  return typeof value === 'string' && /^[A-Za-z0-9_-]{8,100}$/.test(value);
}

function hasProfileContent(value: Record<string, unknown>): boolean {
  return ['name', 'nak', 'nakshatra', 'pada', 'lagna']
    .some(key => text(value[key]) !== '');
}

function clone(profile: GuestProfile): GuestProfile {
  return { ...profile };
}

function toStored(profile: GuestProfile): StoredProfileRecord {
  return {
    id: profile.id,
    schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
    name: profile.name,
    nak: profile.nakshatra || '',
    pada: profile.pada || '',
    lagna: profile.lagna || '',
  };
}

function defaultIdFactory(): string {
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

export function guestProfileReadiness(profile: GuestProfile): GuestProfileReadiness {
  const janmaRasi = profile.nakshatra
    ? rasiFromStar(profile.nakshatra, profile.pada)
    : null;
  let missingForHoroscope: GuestProfileReadiness['missingForHoroscope'] = null;
  if (profile.nakshatra === null) {
    missingForHoroscope = 'nakshatra';
  } else if (janmaRasi === null) {
    missingForHoroscope = 'pada';
  }
  return {
    muhurta: profile.nakshatra !== null,
    horoscope: janmaRasi !== null,
    janmaRasi,
    missingForHoroscope,
  };
}

export class GuestProfileStore {
  private profiles: GuestProfile[] = [];
  private persistence: ProfilePersistence = 'persistent';
  private issue: ProfileStoreIssue = null;
  private readonly listeners = new Set<GuestProfileListener>();
  private readonly idFactory: () => string;

  constructor(
    private readonly storage: ProfileStorage,
    options: GuestProfileStoreOptions = {},
  ) {
    this.idFactory = options.idFactory || defaultIdFactory;
    this.load(true);
  }

  getSnapshot(): GuestProfileSnapshot {
    const profiles = Object.freeze(
      this.profiles.map(profile => Object.freeze(clone(profile))),
    );
    return Object.freeze({
      profiles,
      persistence: this.persistence,
      issue: this.issue,
    });
  }

  get(id: string): GuestProfile | null {
    const profile = this.profiles.find(candidate => candidate.id === id);
    return profile ? clone(profile) : null;
  }

  subscribe(listener: GuestProfileListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  create(draft: GuestProfileDraft): GuestProfile {
    if (this.profiles.length >= MAX_GUEST_PROFILES) {
      throw new GuestProfileStoreError('profile-limit');
    }
    const profile = this.normalize(draft, this.freshId());
    if (!this.hasContent(profile)) throw new GuestProfileStoreError('empty-profile');
    this.profiles = [...this.profiles, profile];
    this.persist();
    this.emit();
    return clone(profile);
  }

  update(id: string, patch: GuestProfileDraft): GuestProfile {
    const index = this.profiles.findIndex(profile => profile.id === id);
    if (index < 0) throw new GuestProfileStoreError('profile-not-found');
    const current = this.profiles[index];
    const next = this.normalize({
      name: patch.name === undefined ? current.name : patch.name,
      nakshatra: patch.nakshatra === undefined ? current.nakshatra : patch.nakshatra,
      pada: patch.pada === undefined ? current.pada : patch.pada,
      lagna: patch.lagna === undefined ? current.lagna : patch.lagna,
    }, current.id);
    if (!this.hasContent(next)) throw new GuestProfileStoreError('empty-profile');
    this.profiles = this.profiles.map((profile, i) => i === index ? next : profile);
    this.persist();
    this.emit();
    return clone(next);
  }

  remove(id: string): boolean {
    const next = this.profiles.filter(profile => profile.id !== id);
    if (next.length === this.profiles.length) return false;
    this.profiles = next;
    this.persist();
    this.emit();
    return true;
  }

  clear(): void {
    const changed = this.profiles.length > 0;
    this.profiles = [];
    this.persist();
    if (changed) this.emit();
  }

  reload(): void {
    // A failed write makes the in-memory state authoritative for this page.
    // Re-reading stale storage would silently discard the guest's edits.
    if (this.persistence === 'memory') return;
    this.load(false);
    this.emit();
  }

  private normalize(draft: GuestProfileDraft, id: string): GuestProfile {
    const nakshatra = canonical(draft.nakshatra, NAKSHATRA_NAMES);
    return {
      id,
      schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
      name: text(draft.name),
      nakshatra,
      pada: nakshatra ? pada(draft.pada) : null,
      lagna: canonical(draft.lagna, RASI_NAMES),
    };
  }

  private hasContent(profile: GuestProfile): boolean {
    return Boolean(profile.name || profile.nakshatra || profile.lagna);
  }

  private freshId(seen = new Set(this.profiles.map(profile => profile.id))): string {
    for (let attempt = 0; attempt < 100; attempt += 1) {
      const candidate = this.idFactory();
      if (validStoredId(candidate) && !seen.has(candidate)) return candidate;
    }
    throw new Error('Unable to create a unique guest profile ID');
  }

  private load(initial: boolean): void {
    const rawText = this.readStoredText(initial);
    if (rawText === undefined) return;
    if (rawText === null) {
      this.profiles = [];
      return;
    }

    const raw = this.parseStoredRows(rawText);
    if (raw === null) return;

    const hasFutureVersion = this.hasFutureVersion(raw);
    if (hasFutureVersion) {
      // Never downgrade or overwrite data written by a newer profile schema.
      // Compatible v1/legacy rows remain available in memory for this session.
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
    }

    this.profiles = this.migrateStoredRows(raw);
    const normalizedText = JSON.stringify(this.profiles.map(toStored));
    if (normalizedText !== rawText) this.persist();
  }

  private readStoredText(initial: boolean): string | null | undefined {
    try {
      const rawText = this.storage.getItem(GUEST_PROFILE_STORAGE_KEY);
      this.persistence = 'persistent';
      if (!initial || this.issue === 'storage-unavailable') this.issue = null;
      return rawText;
    } catch {
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
      if (initial) this.profiles = [];
      return undefined;
    }
  }

  private parseStoredRows(rawText: string): unknown[] | null {
    try {
      const raw: unknown = JSON.parse(rawText);
      if (Array.isArray(raw)) return raw;
    } catch {
      // The recovery below handles both invalid JSON and a non-array payload.
    }

    this.profiles = [];
    this.issue = 'malformed-storage';
    this.persist();
    return null;
  }

  private hasFutureVersion(raw: unknown[]): boolean {
    return raw.some(value => {
      if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
      const version = Number((value as Record<string, unknown>).schemaVersion);
      return Number.isFinite(version) && version > GUEST_PROFILE_SCHEMA_VERSION;
    });
  }

  private migrateStoredRows(raw: unknown[]): GuestProfile[] {
    const seen = new Set<string>();
    const migrated: GuestProfile[] = [];
    for (const value of raw.slice(0, MAX_GUEST_PROFILES)) {
      if (!value || typeof value !== 'object' || Array.isArray(value)) continue;
      const record = value as Record<string, unknown>;
      if (Number(record.schemaVersion) > GUEST_PROFILE_SCHEMA_VERSION) continue;
      if (!hasProfileContent(record)) continue;
      const id = validStoredId(record.id) && !seen.has(record.id)
        ? record.id
        : this.freshId(seen);
      const profile = this.normalize({
        name: record.name,
        nakshatra: record.nakshatra ?? record.nak,
        pada: record.pada,
        lagna: record.lagna,
      }, id);
      if (this.hasContent(profile)) {
        seen.add(id);
        migrated.push(profile);
      }
    }
    return migrated;
  }

  private persist(): void {
    if (this.persistence === 'memory') return;
    try {
      this.storage.setItem(
        GUEST_PROFILE_STORAGE_KEY,
        JSON.stringify(this.profiles.map(toStored)),
      );
    } catch {
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
    }
  }

  private emit(): void {
    const snapshot = this.getSnapshot();
    const listeners = Array.from(this.listeners);
    for (const listener of listeners) listener(snapshot);
  }
}

export function createGuestProfileStore(
  storage: ProfileStorage,
  options: GuestProfileStoreOptions = {},
): GuestProfileStore {
  return new GuestProfileStore(storage, options);
}
