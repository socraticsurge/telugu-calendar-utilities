import { type BirthChartPlanet, type BirthProfileEngine } from '../birth-profile-api';


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

export type GuestProfilePada = 1 | 2 | 3 | 4;

export interface ProfileStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem?(key: string): void;
}

export interface GuestProfile {
  id: string;
  schemaVersion: typeof GUEST_PROFILE_SCHEMA_VERSION;
  source: 'manual' | 'birth-details';
  name: string;
  nakshatra: string | null;
  pada: GuestProfilePada | null;
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

export interface StoredProfileRecord {
  id: string;
  schemaVersion: typeof GUEST_PROFILE_SCHEMA_VERSION;
  name: string;
  nak: string;
  pada: GuestProfilePada | '';
  lagna: string;
}

export interface StoredBirthProfileRecord {
  source: 'birth-details';
  nakshatra: string;
  pada: GuestProfilePada;
  lagna: string;
  birthDetails: GuestBirthDetails;
  janmaRasi: string;
  natalChart: GuestNatalChart;
  calculation: GuestProfileCalculation;
}

export interface StoredBirthProfileEnvelope {
  schemaVersion: typeof GUEST_BIRTH_PROFILE_SCHEMA_VERSION;
  revision?: string;
  profiles: Record<string, StoredBirthProfileRecord>;
}

export interface StoredProfileCommitMarker {
  schemaVersion: typeof GUEST_PROFILE_COMMIT_SCHEMA_VERSION;
  revision: string;
  baseText: string;
}

export interface GuestProfileStoreOptions {
  idFactory?: () => string;
  revisionFactory?: () => string;
}

export interface StoredProfileMigration {
  profiles: GuestProfile[];
  extensionEligibleIds: Set<string>;
  ambiguousStoredIds: Set<string>;
}

export interface StoredProfileCandidate {
  record: Record<string, unknown>;
  storedId: string | null;
}

export interface BirthProfileLoadResult {
  needsUpgrade: boolean;
  suppressPersist: boolean;
}
