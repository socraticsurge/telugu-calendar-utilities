import { NAKSHATRA_NAMES, RASI_NAMES, rasiFromStar } from '../data/rasis';
import type { BirthChartPlanet, BirthProfileEngine } from './birth-profile-api';

export const GUEST_PROFILE_STORAGE_KEY = 'tc-tb-profiles';
export const GUEST_BIRTH_PROFILE_STORAGE_KEY = 'tc-birth-profile-data';
export const GUEST_PROFILE_COMMIT_STORAGE_KEY = 'tc-profile-storage-commit';
export const GUEST_PROFILE_SCHEMA_VERSION = 1 as const;
export const GUEST_BIRTH_PROFILE_SCHEMA_VERSION = 1 as const;
export const GUEST_PROFILE_COMMIT_SCHEMA_VERSION = 1 as const;
export const MAX_GUEST_PROFILES = 4;

export type ProfilePersistence = 'persistent' | 'memory';
export type ProfileStoreIssue =
  | 'malformed-storage'
  | 'malformed-birth-storage'
  | 'uncommitted-birth-storage'
  | 'storage-unavailable'
  | 'unsupported-storage-version'
  | null;
export type ProfileStoreErrorCode = 'empty-profile' | 'profile-limit' | 'profile-not-found';

export interface ProfileStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem?(key: string): void;
}

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

export interface GuestProfile {
  id: string;
  schemaVersion: typeof GUEST_PROFILE_SCHEMA_VERSION;
  source: 'manual' | 'birth-details';
  name: string;
  nakshatra: string | null;
  pada: 1 | 2 | 3 | 4 | null;
  lagna: string | null;
  janmaRasi: string | null;
  birthDetails: GuestBirthDetails | null;
  natalChart: GuestNatalChart | null;
  calculation: GuestProfileCalculation | null;
}

export interface GuestProfileDraft {
  source?: unknown;
  name?: unknown;
  nakshatra?: unknown;
  pada?: unknown;
  lagna?: unknown;
  janmaRasi?: unknown;
  birthDetails?: unknown;
  natalChart?: unknown;
  calculation?: unknown;
}

export interface GuestBirthDetails {
  dateOfBirth: string;
  timeOfBirth: string;
  placeLabel: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface GuestNatalChart {
  lagnaDegree: number;
  planets: BirthChartPlanet[];
}

export interface GuestProfileCalculation {
  contractVersion: string;
  engine: BirthProfileEngine;
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

interface StoredBirthProfileRecord {
  source: 'birth-details';
  nakshatra: string;
  pada: 1 | 2 | 3 | 4;
  lagna: string;
  birthDetails: GuestBirthDetails;
  janmaRasi: string;
  natalChart: GuestNatalChart;
  calculation: GuestProfileCalculation;
}

interface StoredBirthProfileEnvelope {
  schemaVersion: typeof GUEST_BIRTH_PROFILE_SCHEMA_VERSION;
  revision?: string;
  profiles: Record<string, StoredBirthProfileRecord>;
}

interface StoredProfileCommitMarker {
  schemaVersion: typeof GUEST_PROFILE_COMMIT_SCHEMA_VERSION;
  revision: string;
  baseText: string;
}

interface GuestProfileStoreOptions {
  idFactory?: () => string;
  revisionFactory?: () => string;
}

let fallbackIdSequence = 0;
let fallbackRevisionSequence = 0;

interface StoredProfileMigration {
  profiles: GuestProfile[];
  extensionEligibleIds: Set<string>;
  ambiguousStoredIds: Set<string>;
}

interface BirthProfileLoadResult {
  needsUpgrade: boolean;
  suppressPersist: boolean;
}

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

function validRevision(value: unknown): value is string {
  return typeof value === 'string' && /^[A-Za-z0-9_-]{8,100}$/.test(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value);
  return actual.length === keys.length && actual.every(key => keys.includes(key));
}

function isOwnedBirthDetails(value: unknown): boolean {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  const normalized = normalizeBirthDetails(record);
  return normalized !== null && hasExactKeys(record, [
    'dateOfBirth', 'timeOfBirth', 'placeLabel', 'latitude', 'longitude', 'timezone',
  ])
    && record.dateOfBirth === normalized.dateOfBirth
    && record.timeOfBirth === normalized.timeOfBirth
    && record.placeLabel === normalized.placeLabel
    && Object.is(record.latitude, normalized.latitude)
    && Object.is(record.longitude, normalized.longitude)
    && record.timezone === normalized.timezone;
}

function isOwnedPlanet(value: unknown): boolean {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  const normalized = normalizePlanet(record);
  return normalized !== null
    && hasExactKeys(record, ['name', 'rashi', 'degree', 'house', 'retrograde'])
    && record.name === normalized.name
    && record.rashi === normalized.rashi
    && Object.is(record.degree, normalized.degree)
    && Object.is(record.house, normalized.house)
    && record.retrograde === normalized.retrograde;
}

function isOwnedNatalChart(value: unknown): boolean {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  const normalized = normalizeNatalChart(record);
  return normalized !== null
    && hasExactKeys(record, ['lagnaDegree', 'planets'])
    && Object.is(record.lagnaDegree, normalized.lagnaDegree)
    && Array.isArray(record.planets)
    && record.planets.every(isOwnedPlanet);
}

function isOwnedCalculation(value: unknown): boolean {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, ['contractVersion', 'engine'])) return false;
  if (!record.engine || typeof record.engine !== 'object' || Array.isArray(record.engine)) {
    return false;
  }
  const engine = record.engine as Record<string, unknown>;
  const normalized = normalizeCalculation(record);
  return normalized !== null && hasExactKeys(
    engine,
    ['name', 'version', 'ayanamsha', 'ephemeris'],
  )
    && record.contractVersion === normalized.contractVersion
    && engine.name === normalized.engine.name
    && engine.version === normalized.engine.version
    && engine.ayanamsha === normalized.engine.ayanamsha
    && engine.ephemeris === normalized.engine.ephemeris;
}

function isOwnedBirthProfileRecord(value: unknown): value is StoredBirthProfileRecord {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  return hasExactKeys(record, [
    'source', 'nakshatra', 'pada', 'lagna', 'birthDetails',
    'janmaRasi', 'natalChart', 'calculation',
  ])
    && record.source === 'birth-details'
    && canonical(record.nakshatra, NAKSHATRA_NAMES) === record.nakshatra
    && pada(record.pada) === record.pada
    && canonical(record.lagna, RASI_NAMES) === record.lagna
    && canonical(record.janmaRasi, RASI_NAMES) === record.janmaRasi
    && isOwnedBirthDetails(record.birthDetails)
    && isOwnedNatalChart(record.natalChart)
    && isOwnedCalculation(record.calculation);
}

function hasProfileContent(value: Record<string, unknown>): boolean {
  return ['name', 'nak', 'nakshatra', 'pada', 'lagna']
    .some(key => text(value[key]) !== '');
}

const STORED_PROFILE_KEYS = new Set([
  'id', 'schemaVersion', 'name', 'nak', 'nakshatra', 'pada', 'lagna',
]);

function isBlankLegacyPlaceholder(value: Record<string, unknown>): boolean {
  const legacyKeys = new Set(['name', 'nak', 'nakshatra', 'pada', 'lagna']);
  const keys = Object.keys(value);
  return keys.length > 0 && keys.every(key => legacyKeys.has(key));
}

function hasUnownedProfileKeys(value: Record<string, unknown>): boolean {
  return Object.keys(value).some(key => !STORED_PROFILE_KEYS.has(key));
}

function clone(profile: GuestProfile): GuestProfile {
  return {
    ...profile,
    birthDetails: profile.birthDetails ? { ...profile.birthDetails } : null,
    natalChart: profile.natalChart
      ? { ...profile.natalChart, planets: profile.natalChart.planets.map(planet => ({ ...planet })) }
      : null,
    calculation: profile.calculation
      ? { ...profile.calculation, engine: { ...profile.calculation.engine } }
      : null,
  };
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

function finite(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function isoDate(value: unknown): string | null {
  const candidate = text(value, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(candidate)) return null;
  const parsed = new Date(`${candidate}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== candidate
    ? null
    : candidate;
}

function isoTime(value: unknown): string | null {
  const candidate = text(value, 5);
  return /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(candidate) ? candidate : null;
}

function normalizeBirthDetails(value: unknown): GuestBirthDetails | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  const dateOfBirth = isoDate(record.dateOfBirth);
  const timeOfBirth = isoTime(record.timeOfBirth);
  const placeLabel = text(record.placeLabel, 240);
  const latitude = finite(record.latitude);
  const longitude = finite(record.longitude);
  const timezone = text(record.timezone, 80);
  if (
    !dateOfBirth || !timeOfBirth || !placeLabel || !timezone
    || latitude === null || latitude < -90 || latitude > 90
    || longitude === null || longitude < -180 || longitude > 180
  ) return null;
  return { dateOfBirth, timeOfBirth, placeLabel, latitude, longitude, timezone };
}

function normalizePlanet(value: unknown): BirthChartPlanet | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  const name = text(record.name, 40);
  const rashi = canonical(record.rashi, RASI_NAMES);
  const degree = finite(record.degree);
  const house = finite(record.house);
  if (
    !name || !rashi || degree === null || degree < 0 || degree >= 30
    || house === null || !Number.isInteger(house) || house < 1 || house > 12
    || typeof record.retrograde !== 'boolean'
  ) return null;
  return { name, rashi, degree, house, retrograde: record.retrograde };
}

function normalizeNatalChart(value: unknown): GuestNatalChart | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  const lagnaDegree = finite(record.lagnaDegree);
  const rawPlanets = Array.isArray(record.planets) ? record.planets : null;
  if (lagnaDegree === null || lagnaDegree < 0 || lagnaDegree >= 30 || !rawPlanets) return null;
  const planets = rawPlanets.map(normalizePlanet).filter((item): item is BirthChartPlanet => item !== null);
  return planets.length === 9 && planets.length === rawPlanets.length
    ? { lagnaDegree, planets }
    : null;
}

function normalizeCalculation(value: unknown): GuestProfileCalculation | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  const engineValue = record.engine;
  if (!engineValue || typeof engineValue !== 'object' || Array.isArray(engineValue)) return null;
  const engineRecord = engineValue as Record<string, unknown>;
  const contractVersion = text(record.contractVersion, 20);
  const name = text(engineRecord.name, 60);
  const version = text(engineRecord.version, 40);
  const ayanamsha = text(engineRecord.ayanamsha, 40);
  const ephemeris = text(engineRecord.ephemeris, 20);
  if (
    !contractVersion || !name || !version || !ayanamsha
    || (ephemeris !== 'swiss' && ephemeris !== 'moshier' && ephemeris !== 'unknown')
  ) return null;
  return { contractVersion, engine: { name, version, ayanamsha, ephemeris } };
}

function toStoredBirthProfile(profile: GuestProfile): StoredBirthProfileRecord | null {
  if (
    profile.source !== 'birth-details' || !profile.birthDetails || !profile.janmaRasi
    || !profile.natalChart || !profile.calculation
  ) return null;
  return {
    source: 'birth-details',
    nakshatra: profile.nakshatra!,
    pada: profile.pada!,
    lagna: profile.lagna!,
    birthDetails: { ...profile.birthDetails },
    janmaRasi: profile.janmaRasi,
    natalChart: {
      lagnaDegree: profile.natalChart.lagnaDegree,
      planets: profile.natalChart.planets.map(planet => ({ ...planet })),
    },
    calculation: {
      contractVersion: profile.calculation.contractVersion,
      engine: { ...profile.calculation.engine },
    },
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

function defaultRevisionFactory(): string {
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
  private readonly revisionFactory: () => string;
  private lastRevision: string | null = null;
  private discardableOrphan = false;

  constructor(
    private readonly storage: ProfileStorage,
    options: GuestProfileStoreOptions = {},
  ) {
    this.idFactory = options.idFactory || defaultIdFactory;
    this.revisionFactory = options.revisionFactory || defaultRevisionFactory;
    this.load(true);
  }

  getSnapshot(): GuestProfileSnapshot {
    const profiles = Object.freeze(
      this.profiles.map(profile => {
        const item = clone(profile);
        if (item.birthDetails) Object.freeze(item.birthDetails);
        if (item.natalChart) {
          item.natalChart.planets.forEach(Object.freeze);
          Object.freeze(item.natalChart.planets);
          Object.freeze(item.natalChart);
        }
        if (item.calculation) {
          Object.freeze(item.calculation.engine);
          Object.freeze(item.calculation);
        }
        return Object.freeze(item);
      }),
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
      source: patch.source === undefined ? current.source : patch.source,
      name: patch.name === undefined ? current.name : patch.name,
      nakshatra: patch.nakshatra === undefined ? current.nakshatra : patch.nakshatra,
      pada: patch.pada === undefined ? current.pada : patch.pada,
      lagna: patch.lagna === undefined ? current.lagna : patch.lagna,
      janmaRasi: patch.janmaRasi === undefined ? current.janmaRasi : patch.janmaRasi,
      birthDetails: patch.birthDetails === undefined ? current.birthDetails : patch.birthDetails,
      natalChart: patch.natalChart === undefined ? current.natalChart : patch.natalChart,
      calculation: patch.calculation === undefined ? current.calculation : patch.calculation,
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
    const profilesChanged = this.profiles.length > 0;
    const previousPersistence = this.persistence;
    const previousIssue = this.issue;
    this.profiles = [];
    this.persist();
    if (
      profilesChanged
      || this.persistence !== previousPersistence
      || this.issue !== previousIssue
    ) this.emit();
  }

  canDiscardUncommittedStorage(): boolean {
    return this.discardableOrphan && typeof this.storage.removeItem === 'function';
  }

  discardUncommittedStorage(): boolean {
    if (!this.canDiscardUncommittedStorage()) return false;
    try {
      this.storage.removeItem!(GUEST_BIRTH_PROFILE_STORAGE_KEY);
      this.storage.removeItem!(GUEST_PROFILE_COMMIT_STORAGE_KEY);
      this.storage.removeItem!(GUEST_PROFILE_STORAGE_KEY);
    } catch {
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
      this.emit();
      return false;
    }
    this.profiles = [];
    this.persistence = 'persistent';
    this.issue = null;
    this.discardableOrphan = false;
    this.emit();
    return true;
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
    const padaValue = nakshatra ? pada(draft.pada) : null;
    const lagna = canonical(draft.lagna, RASI_NAMES);
    const birthDetails = normalizeBirthDetails(draft.birthDetails);
    const natalChart = normalizeNatalChart(draft.natalChart);
    const calculation = normalizeCalculation(draft.calculation);
    const suppliedRasi = canonical(draft.janmaRasi, RASI_NAMES);
    const derivedRasi = nakshatra ? rasiFromStar(nakshatra, padaValue) : null;
    const isBirthDerived = draft.source === 'birth-details'
      && Boolean(birthDetails && natalChart && calculation && suppliedRasi && nakshatra && padaValue && lagna);
    return {
      id,
      schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
      source: isBirthDerived ? 'birth-details' : 'manual',
      name: text(draft.name),
      nakshatra,
      pada: padaValue,
      lagna,
      janmaRasi: isBirthDerived ? suppliedRasi : derivedRasi,
      birthDetails: isBirthDerived ? birthDetails : null,
      natalChart: isBirthDerived ? natalChart : null,
      calculation: isBirthDerived ? calculation : null,
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

  private freshRevision(): string {
    for (let attempt = 0; attempt < 100; attempt += 1) {
      const candidate = this.revisionFactory();
      if (validRevision(candidate) && candidate !== this.lastRevision) {
        this.lastRevision = candidate;
        return candidate;
      }
    }
    throw new Error('Unable to create a profile storage revision');
  }

  private load(initial: boolean): void {
    this.discardableOrphan = false;
    const rawText = this.readStoredText(initial);
    if (rawText === undefined) return;
    if (rawText === null) {
      this.profiles = [];
      this.failClosedForOrphanCompanions(initial);
      return;
    }

    const raw = this.parseStoredRows(rawText);
    if (raw === null) {
      if (!this.failClosedForMalformedBaseCompanions(initial)) this.persist();
      return;
    }

    const hasUnsupportedRows = this.hasUnsupportedRows(raw);
    if (hasUnsupportedRows) {
      // Never discard or overwrite data that this store cannot safely own,
      // including newer schemas, opaque rows, and profiles beyond its limit.
      // Compatible v1/legacy rows remain available in memory for this session.
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
    }

    const migration = this.migrateStoredRows(raw);
    this.profiles = migration.profiles;
    const birthLoad = this.loadBirthProfileExtensions(
      initial,
      rawText,
      migration,
      hasUnsupportedRows,
    );
    const normalizedText = JSON.stringify(this.profiles.map(toStored));
    if (
      !birthLoad.suppressPersist
      && (normalizedText !== rawText || birthLoad.needsUpgrade)
    ) this.persist();
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

  private failClosedForOrphanCompanions(initial: boolean): void {
    try {
      const birthText = this.storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY);
      const commitText = this.storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY);
      if (birthText !== null || commitText !== null) {
        this.persistence = 'memory';
        this.issue = 'uncommitted-birth-storage';
        this.discardableOrphan = this.isOwnedOrphanTransaction(birthText, commitText);
      }
    } catch {
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
      if (initial) this.profiles = [];
    }
  }

  private failClosedForMalformedBaseCompanions(initial: boolean): boolean {
    try {
      const birthText = this.storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY);
      const commitText = this.storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY);
      if (birthText === null && commitText === null) return false;
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return true;
    } catch {
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
      if (initial) this.profiles = [];
      return true;
    }
  }

  private isOwnedOrphanBirthText(rawText: string | null): boolean {
    if (rawText === null) return true;
    let value: unknown;
    try {
      value = JSON.parse(rawText);
    } catch {
      return false;
    }
    if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
    const envelope = value as Record<string, unknown>;
    if (envelope.schemaVersion !== GUEST_BIRTH_PROFILE_SCHEMA_VERSION) return false;
    if (!envelope.profiles || typeof envelope.profiles !== 'object'
      || Array.isArray(envelope.profiles)) return false;
    const keys = envelope.revision === undefined
      ? ['schemaVersion', 'profiles']
      : ['schemaVersion', 'revision', 'profiles'];
    if (!hasExactKeys(envelope, keys)) return false;
    if (envelope.revision !== undefined && !validRevision(envelope.revision)) return false;
    return Object.values(envelope.profiles as Record<string, unknown>)
      .every(isOwnedBirthProfileRecord);
  }

  private isOwnedOrphanCommitText(rawText: string | null): boolean {
    if (rawText === null) return true;
    let value: unknown;
    try {
      value = JSON.parse(rawText);
    } catch {
      return false;
    }
    if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
    const record = value as Record<string, unknown>;
    return hasExactKeys(record, ['schemaVersion', 'revision', 'baseText'])
      && record.schemaVersion === GUEST_PROFILE_COMMIT_SCHEMA_VERSION
      && validRevision(record.revision)
      && typeof record.baseText === 'string'
      && this.ownedOrphanBaseRows(record.baseText) !== null;
  }

  private ownedOrphanBaseRows(rawText: string): Map<string, StoredProfileRecord> | null {
    let value: unknown;
    try {
      value = JSON.parse(rawText);
    } catch {
      return null;
    }
    if (!Array.isArray(value) || value.length > MAX_GUEST_PROFILES) return null;
    const rows = new Map<string, StoredProfileRecord>();
    for (const item of value) {
      if (!item || typeof item !== 'object' || Array.isArray(item)) return null;
      const record = item as Record<string, unknown>;
      if (!hasExactKeys(record, ['id', 'schemaVersion', 'name', 'nak', 'pada', 'lagna'])) {
        return null;
      }
      if (
        !validStoredId(record.id)
        || rows.has(record.id)
        || record.schemaVersion !== GUEST_PROFILE_SCHEMA_VERSION
        || typeof record.name !== 'string'
        || text(record.name) !== record.name
        || !(record.nak === '' || canonical(record.nak, NAKSHATRA_NAMES) === record.nak)
        || !(record.pada === '' || pada(record.pada) === record.pada)
        || !(record.lagna === '' || canonical(record.lagna, RASI_NAMES) === record.lagna)
        || !(record.name || record.nak || record.lagna)
      ) return null;
      rows.set(record.id, record as unknown as StoredProfileRecord);
    }
    return rows;
  }

  private isOwnedOrphanTransaction(
    birthText: string | null,
    commitText: string | null,
  ): boolean {
    if (!this.isOwnedOrphanBirthText(birthText) || !this.isOwnedOrphanCommitText(commitText)) {
      return false;
    }
    if (birthText === null || commitText === null) return true;
    const envelope = JSON.parse(birthText) as StoredBirthProfileEnvelope;
    const commit = JSON.parse(commitText) as StoredProfileCommitMarker;
    if (!envelope.revision || envelope.revision !== commit.revision) return false;
    const rows = this.ownedOrphanBaseRows(commit.baseText);
    if (!rows) return false;
    return Object.entries(envelope.profiles).every(([id, extension]) => {
      const row = rows.get(id);
      return Boolean(row)
        && extension.nakshatra === row!.nak
        && extension.pada === row!.pada
        && extension.lagna === row!.lagna;
    });
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
    return null;
  }

  private hasUnsupportedRows(raw: unknown[]): boolean {
    let supportedProfiles = 0;
    for (const value of raw) {
      if (!value || typeof value !== 'object' || Array.isArray(value)) return true;
      const record = value as Record<string, unknown>;
      const version = Number(record.schemaVersion);
      if (Number.isFinite(version) && version > GUEST_PROFILE_SCHEMA_VERSION) return true;
      if (hasUnownedProfileKeys(record)) return true;
      if (!hasProfileContent(record)) {
        if (isBlankLegacyPlaceholder(record)) continue;
        return true;
      }

      const profile = this.normalize({
        source: 'manual',
        name: record.name,
        nakshatra: record.nakshatra ?? record.nak,
        pada: record.pada,
        lagna: record.lagna,
      }, 'guest_validation');
      if (this.hasContent(profile)) supportedProfiles += 1;
      if (supportedProfiles > MAX_GUEST_PROFILES) return true;
    }
    return false;
  }

  private migrateStoredRows(raw: unknown[]): StoredProfileMigration {
    const candidates: Array<{
      record: Record<string, unknown>;
      storedId: string | null;
    }> = [];
    const storedIdCounts = new Map<string, number>();
    for (const value of raw) {
      if (!value || typeof value !== 'object' || Array.isArray(value)) continue;
      const record = value as Record<string, unknown>;
      if (Number(record.schemaVersion) > GUEST_PROFILE_SCHEMA_VERSION) continue;
      if (!hasProfileContent(record)) continue;
      const preview = this.normalize({
        source: 'manual',
        name: record.name,
        nakshatra: record.nakshatra ?? record.nak,
        pada: record.pada,
        lagna: record.lagna,
      }, 'guest_validation');
      if (!this.hasContent(preview)) continue;
      const storedId = validStoredId(record.id) ? record.id : null;
      candidates.push({ record, storedId });
      if (storedId) storedIdCounts.set(storedId, (storedIdCounts.get(storedId) || 0) + 1);
    }

    const seen = new Set<string>();
    const migrated: GuestProfile[] = [];
    const extensionEligibleIds = new Set<string>();
    const ambiguousStoredIds = new Set(
      Array.from(storedIdCounts)
        .filter(([, count]) => count > 1)
        .map(([id]) => id),
    );
    for (const { record, storedId } of candidates) {
      if (migrated.length >= MAX_GUEST_PROFILES) break;
      const id = storedId && !seen.has(storedId)
        ? storedId
        : this.freshId(seen);
      const profile = this.normalize({
        source: 'manual',
        name: record.name,
        nakshatra: record.nakshatra ?? record.nak,
        pada: record.pada,
        lagna: record.lagna,
      }, id);
      if (this.hasContent(profile)) {
        seen.add(id);
        migrated.push(profile);
        if (storedId === id && storedIdCounts.get(storedId) === 1) {
          extensionEligibleIds.add(id);
        }
      }
    }
    return {
      profiles: migrated,
      extensionEligibleIds,
      ambiguousStoredIds,
    };
  }

  private persist(): void {
    if (this.persistence === 'memory') return;
    try {
      const revision = this.freshRevision();
      const baseText = JSON.stringify(this.profiles.map(toStored));
      const extensions: Record<string, StoredBirthProfileRecord> = {};
      for (const profile of this.profiles) {
        const stored = toStoredBirthProfile(profile);
        if (stored) extensions[profile.id] = stored;
      }
      const envelope: StoredBirthProfileEnvelope = {
        schemaVersion: GUEST_BIRTH_PROFILE_SCHEMA_VERSION,
        revision,
        profiles: extensions,
      };
      const commit: StoredProfileCommitMarker = {
        schemaVersion: GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
        revision,
        baseText,
      };
      // The marker is the commit point. Readers ignore the birth envelope until
      // both earlier writes match this exact revision and exact base payload.
      this.storage.setItem(GUEST_PROFILE_STORAGE_KEY, baseText);
      this.storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, JSON.stringify(envelope));
      this.storage.setItem(GUEST_PROFILE_COMMIT_STORAGE_KEY, JSON.stringify(commit));
    } catch {
      // Do not clean up or roll back here. localStorage has no atomic
      // compare-and-swap, so either action could overwrite a newer tab's
      // transaction. The unchanged marker keeps every partial write detached.
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
    }
  }

  private loadBirthProfileExtensions(
    initial: boolean,
    baseText: string,
    migration: StoredProfileMigration,
    baseHasUnsupportedRows: boolean,
  ): BirthProfileLoadResult {
    const noUpgrade: BirthProfileLoadResult = {
      needsUpgrade: false,
      suppressPersist: false,
    };
    let rawText: string | null;
    let commitText: string | null;
    try {
      rawText = this.storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY);
      commitText = this.storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY);
    } catch {
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
      if (initial) this.profiles = [];
      return { ...noUpgrade, suppressPersist: true };
    }

    let commit: StoredProfileCommitMarker | null = null;
    if (commitText) {
      let value: unknown;
      try {
        value = JSON.parse(commitText);
      } catch {
        this.persistence = 'memory';
        this.issue = 'unsupported-storage-version';
        return { ...noUpgrade, suppressPersist: true };
      }
      if (!value || typeof value !== 'object' || Array.isArray(value)) {
        this.persistence = 'memory';
        this.issue = 'unsupported-storage-version';
        return { ...noUpgrade, suppressPersist: true };
      }
      const record = value as Record<string, unknown>;
      const keys = Object.keys(record);
      if (
        record.schemaVersion !== GUEST_PROFILE_COMMIT_SCHEMA_VERSION
        || !validRevision(record.revision)
        || typeof record.baseText !== 'string'
        || keys.length !== 3
        || !keys.every(key => ['schemaVersion', 'revision', 'baseText'].includes(key))
      ) {
        this.persistence = 'memory';
        this.issue = 'unsupported-storage-version';
        return { ...noUpgrade, suppressPersist: true };
      }
      commit = {
        schemaVersion: GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
        revision: record.revision,
        baseText: record.baseText,
      };
    }

    if (!rawText) {
      if (commit) {
        this.issue = 'uncommitted-birth-storage';
        return { ...noUpgrade, suppressPersist: true };
      }
      return noUpgrade;
    }

    let value: unknown;
    try {
      value = JSON.parse(rawText);
    } catch {
      this.issue = 'malformed-birth-storage';
      this.clearBirthProfileExtensions();
      return { ...noUpgrade, suppressPersist: true };
    }
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      this.issue = 'malformed-birth-storage';
      this.clearBirthProfileExtensions();
      return { ...noUpgrade, suppressPersist: true };
    }
    const envelope = value as Record<string, unknown>;
    const version = envelope.schemaVersion;
    if (typeof version !== 'number' || !Number.isFinite(version)) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return { ...noUpgrade, suppressPersist: true };
    }
    if (version > GUEST_BIRTH_PROFILE_SCHEMA_VERSION) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return { ...noUpgrade, suppressPersist: true };
    }
    if (version !== GUEST_BIRTH_PROFILE_SCHEMA_VERSION
      || !envelope.profiles || typeof envelope.profiles !== 'object'
      || Array.isArray(envelope.profiles)) {
      this.issue = 'malformed-birth-storage';
      this.clearBirthProfileExtensions();
      return { ...noUpgrade, suppressPersist: true };
    }

    const envelopeKeys = envelope.revision === undefined
      ? ['schemaVersion', 'profiles']
      : ['schemaVersion', 'revision', 'profiles'];
    if (!hasExactKeys(envelope, envelopeKeys)) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return { ...noUpgrade, suppressPersist: true };
    }
    if (envelope.revision !== undefined && !validRevision(envelope.revision)) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return { ...noUpgrade, suppressPersist: true };
    }

    const extensions = envelope.profiles as Record<string, unknown>;
    if (baseHasUnsupportedRows && Object.keys(extensions).length > 0) {
      return { ...noUpgrade, suppressPersist: true };
    }

    if (Object.values(extensions).some(extension => !isOwnedBirthProfileRecord(extension))) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return { ...noUpgrade, suppressPersist: true };
    }

    const envelopeRevision = envelope.revision;
    const isLegacyEnvelope = envelopeRevision === undefined && commit === null;
    if (!isLegacyEnvelope) {
      if (
        !validRevision(envelopeRevision)
        || !commit
        || commit.revision !== envelopeRevision
        || commit.baseText !== baseText
      ) {
        this.issue = 'uncommitted-birth-storage';
        return { ...noUpgrade, suppressPersist: true };
      }
      this.lastRevision = commit.revision;
    }

    const extensionIds = Object.keys(extensions);
    if (extensionIds.some(id =>
      migration.ambiguousStoredIds.has(id)
      || !migration.extensionEligibleIds.has(id))) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return { ...noUpgrade, suppressPersist: true };
    }

    let extensionMismatch = false;
    this.profiles = this.profiles.map(profile => {
      const extension = extensions[profile.id];
      if (!extension) return profile;
      const record = extension as StoredBirthProfileRecord;
      // Revision and exact-base checks establish the committed snapshot. Keep
      // the derived-field guard as defense in depth before joining both keys.
      if (
        record.nakshatra !== profile.nakshatra
        || Number(record.pada) !== profile.pada
        || record.lagna !== profile.lagna
      ) {
        extensionMismatch = true;
        return profile;
      }
      const combined = this.normalize({
        source: record.source,
        name: profile.name,
        nakshatra: profile.nakshatra,
        pada: profile.pada,
        lagna: profile.lagna,
        janmaRasi: record.janmaRasi,
        birthDetails: record.birthDetails,
        natalChart: record.natalChart,
        calculation: record.calculation,
      }, profile.id);
      if (combined.source !== 'birth-details') {
        extensionMismatch = true;
        return profile;
      }
      return combined;
    });
    if (extensionMismatch) {
      this.issue = 'uncommitted-birth-storage';
      return { ...noUpgrade, suppressPersist: true };
    }
    return {
      needsUpgrade: isLegacyEnvelope,
      suppressPersist: false,
    };
  }

  private clearBirthProfileExtensions(): void {
    if (this.persistence === 'memory') return;
    try {
      const empty: StoredBirthProfileEnvelope = {
        schemaVersion: GUEST_BIRTH_PROFILE_SCHEMA_VERSION,
        profiles: {},
      };
      this.storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, JSON.stringify(empty));
      this.storage.setItem(GUEST_PROFILE_COMMIT_STORAGE_KEY, '');
    } catch {
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
    }
  }

  private emit(): void {
    const snapshot = this.getSnapshot();
    const listeners = Array.from(this.listeners);
    for (const listener of listeners) {
      // Store mutations have already been persisted. A faulty UI observer must
      // neither turn that successful mutation into an exception nor prevent
      // other subscribers from receiving the same immutable snapshot.
      try {
        listener(snapshot);
      } catch {
        // Subscriber failures belong to the subscriber, not the store.
      }
    }
  }
}

export function createGuestProfileStore(
  storage: ProfileStorage,
  options: GuestProfileStoreOptions = {},
): GuestProfileStore {
  return new GuestProfileStore(storage, options);
}
