import { isOwnedBirthProfileRecord } from './guest-profile/birth-ownership';
import { hasUnsupportedRows as containsUnsupportedRows, migrateStoredRows } from './guest-profile/migration';
import { isOwnedOrphanTransaction } from './guest-profile/orphan-recovery';
import {
  clone,
  hasContent,
  normalizeProfile,
  toStored,
  toStoredBirthProfile,
  mergeProfileDraft,
} from './guest-profile/profiles';
import {
  GUEST_BIRTH_PROFILE_SCHEMA_VERSION,
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
  GUEST_PROFILE_COMMIT_STORAGE_KEY,
  GUEST_PROFILE_STORAGE_KEY,
  MAX_GUEST_PROFILES,
  type BirthProfileLoadResult,
  type GuestProfile,
  type GuestProfileDraft,
  type GuestProfileListener,
  type GuestProfileSnapshot,
  type GuestProfileStoreOptions,
  type ProfilePersistence,
  type ProfileStorage,
  type ProfileStoreErrorCode,
  type ProfileStoreIssue,
  type StoredBirthProfileEnvelope,
  type StoredBirthProfileRecord,
  type StoredProfileCommitMarker,
  type StoredProfileMigration,
} from './guest-profile/types';
import {
  defaultIdFactory,
  defaultRevisionFactory,
  hasExactKeys,
  validRevision,
  validStoredId,
  isRecord,
} from './guest-profile/values';

export {
  browserProfileStorage,
  canonicalLegacyGuestProfileLagna,
  mergeLegacyGuestProfileRow,
  readLegacyGuestProfileRows,
  removeLegacyGuestProfileRow,
  writeLegacyGuestProfileRows,
} from './guest-profile/legacy';
export { guestProfileReadiness } from './guest-profile/profiles';
export {
  GUEST_BIRTH_PROFILE_SCHEMA_VERSION,
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
  GUEST_PROFILE_COMMIT_STORAGE_KEY,
  GUEST_PROFILE_SCHEMA_VERSION,
  GUEST_PROFILE_STORAGE_KEY,
  MAX_GUEST_PROFILES,
} from './guest-profile/types';
export type {
  GuestBirthDetails,
  GuestNatalChart,
  GuestProfile,
  GuestProfileCalculation,
  GuestProfileDraft,
  GuestProfileListener,
  GuestProfilePada,
  GuestProfileReadiness,
  GuestProfileSnapshot,
  LegacyGuestProfileFields,
  LegacyGuestProfileRow,
  ProfilePersistence,
  ProfileStorage,
  ProfileStoreErrorCode,
  ProfileStoreIssue,
} from './guest-profile/types';

export class GuestProfileStoreError extends Error {
  constructor(public readonly code: ProfileStoreErrorCode) {
    super(code);
    this.name = 'GuestProfileStoreError';
  }
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
    const profile = normalizeProfile(draft, this.freshId());
    if (!hasContent(profile)) throw new GuestProfileStoreError('empty-profile');
    this.profiles = [...this.profiles, profile];
    this.persist();
    this.emit();
    return clone(profile);
  }

  update(id: string, patch: GuestProfileDraft): GuestProfile {
    const index = this.profiles.findIndex(profile => profile.id === id);
    if (index < 0) throw new GuestProfileStoreError('profile-not-found');
    const current = this.profiles[index];
    const next = normalizeProfile(mergeProfileDraft(current, patch), current.id);
    if (!hasContent(next)) throw new GuestProfileStoreError('empty-profile');
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

  private freshId(seen = new Set(this.profiles.map(profile => profile.id))): string {
    for (let attempt = 0;attempt < 100;attempt += 1) {
      const candidate = this.idFactory();
      if (validStoredId(candidate) && !seen.has(candidate)) return candidate;
    }
    throw new Error('Unable to create a unique guest profile ID');
  }

  private freshRevision(): string {
    for (let attempt = 0;attempt < 100;attempt += 1) {
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

    const hasUnsupportedRows = containsUnsupportedRows(raw);
    if (hasUnsupportedRows) {
      // Never discard or overwrite data that this store cannot safely own,
      // including newer schemas, opaque rows, and profiles beyond its limit.
      // Compatible v1/legacy rows remain available in memory for this session.
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
    }

    const migration = migrateStoredRows(raw, seen => this.freshId(seen));
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
        this.discardableOrphan = isOwnedOrphanTransaction(birthText, commitText);
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

  private readBirthProfileStorage(
    initial: boolean,
  ): { rawText: string | null; commitText: string | null } | null {
    try {
      return {
        rawText: this.storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY),
        commitText: this.storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY),
      };
    } catch {
      this.persistence = 'memory';
      this.issue = 'storage-unavailable';
      if (initial) this.profiles = [];
      return null;
    }
  }

  private parseStoredCommit(
    commitText: string | null,
  ): StoredProfileCommitMarker | null | undefined {
    if (!commitText) return null;
    let value: unknown;
    try {
      value = JSON.parse(commitText);
    } catch {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return undefined;
    }
    if (!isRecord(value)) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return undefined;
    }
    const record = value as Record<string, unknown>;
    if (
      record.schemaVersion !== GUEST_PROFILE_COMMIT_SCHEMA_VERSION
      || !validRevision(record.revision)
      || typeof record.baseText !== 'string'
      || !hasExactKeys(record, ['schemaVersion', 'revision', 'baseText'])
    ) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return undefined;
    }
    return {
      schemaVersion: GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
      revision: record.revision,
      baseText: record.baseText,
    };
  }

  private parseBirthProfileEnvelope(rawText: string): Record<string, unknown> | null {
    let value: unknown;
    try {
      value = JSON.parse(rawText);
    } catch {
      this.issue = 'malformed-birth-storage';
      this.clearBirthProfileExtensions();
      return null;
    }
    if (!isRecord(value)) {
      this.issue = 'malformed-birth-storage';
      this.clearBirthProfileExtensions();
      return null;
    }
    const envelope = value as Record<string, unknown>;
    const version = envelope.schemaVersion;
    if (typeof version !== 'number' || !Number.isFinite(version)
      || version > GUEST_BIRTH_PROFILE_SCHEMA_VERSION) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return null;
    }
    if (version !== GUEST_BIRTH_PROFILE_SCHEMA_VERSION
      || !envelope.profiles || typeof envelope.profiles !== 'object'
      || Array.isArray(envelope.profiles)) {
      this.issue = 'malformed-birth-storage';
      this.clearBirthProfileExtensions();
      return null;
    }
    const envelopeKeys = envelope.revision === undefined
      ? ['schemaVersion', 'profiles']
      : ['schemaVersion', 'revision', 'profiles'];
    if (!hasExactKeys(envelope, envelopeKeys)
      || (envelope.revision !== undefined && !validRevision(envelope.revision))) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return null;
    }
    return envelope;
  }

  private mergeBirthProfileExtensions(
    extensions: Record<string, unknown>,
  ): boolean {
    let extensionMismatch = false;
    this.profiles = this.profiles.map(profile => {
      const extension = extensions[profile.id];
      if (!extension) return profile;
      const record = extension as StoredBirthProfileRecord;
      if (
        record.nakshatra !== profile.nakshatra
        || Number(record.pada) !== profile.pada
        || record.lagna !== profile.lagna
      ) {
        extensionMismatch = true;
        return profile;
      }
      const combined = normalizeProfile({
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
      if (combined.source === 'birth-details') return combined;
      extensionMismatch = true;
      return profile;
    });
    return !extensionMismatch;
  }

  private committedEnvelopeMatches(
    commit: StoredProfileCommitMarker | null,
    envelopeRevision: unknown,
    baseText: string,
  ): commit is StoredProfileCommitMarker {
    return validRevision(envelopeRevision)
      && commit?.revision === envelopeRevision
      && commit.baseText === baseText;
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
    const storage = this.readBirthProfileStorage(initial);
    if (!storage) return { ...noUpgrade, suppressPersist: true };
    const commit = this.parseStoredCommit(storage.commitText);
    if (commit === undefined) return { ...noUpgrade, suppressPersist: true };
    if (!storage.rawText) {
      return this.missingBirthEnvelopeResult(commit);
    }
    const envelope = this.parseBirthProfileEnvelope(storage.rawText);
    if (!envelope) return { ...noUpgrade, suppressPersist: true };
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
    if (!this.acceptBirthRevision(commit, envelopeRevision, baseText)) {
      return { ...noUpgrade, suppressPersist: true };
    }

    const extensionIds = Object.keys(extensions);
    if (extensionIds.some(id =>
      migration.ambiguousStoredIds.has(id)
      || !migration.extensionEligibleIds.has(id))) {
      this.persistence = 'memory';
      this.issue = 'unsupported-storage-version';
      return { ...noUpgrade, suppressPersist: true };
    }

    if (!this.mergeBirthProfileExtensions(extensions)) {
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

  private missingBirthEnvelopeResult(commit: StoredProfileCommitMarker | null): BirthProfileLoadResult {
    if (commit) this.issue = 'uncommitted-birth-storage';
    return { needsUpgrade: false, suppressPersist: Boolean(commit) };
  }

  private acceptBirthRevision(
    commit: StoredProfileCommitMarker | null,
    envelopeRevision: unknown,
    baseText: string,
  ): boolean {
    if (envelopeRevision === undefined && commit === null) return true;
    if (!this.committedEnvelopeMatches(commit, envelopeRevision, baseText)) {
      this.issue = 'uncommitted-birth-storage';
      return false;
    }
    this.lastRevision = commit.revision;
    return true;
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
