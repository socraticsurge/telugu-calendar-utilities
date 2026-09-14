import { hasProfileContent, hasUnownedProfileKeys, isBlankLegacyPlaceholder } from './legacy';
import { hasContent, normalizeProfile } from './profiles';
import {
  GUEST_PROFILE_SCHEMA_VERSION,
  MAX_GUEST_PROFILES,
  type GuestProfile,
  type StoredProfileCandidate,
  type StoredProfileMigration,
} from './types';
import { validStoredId, isRecord } from './values';


export function migrateStoredRows(raw: unknown[], freshId: (seen: Set<string>) => string): StoredProfileMigration {
  const candidates = storedProfileCandidates(raw);
  const storedIdCounts = new Map<string, number>();
  for (const { storedId } of candidates) {
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
      : freshId(seen);
    const profile = normalizeProfile({
      source: 'manual',
      name: record.name,
      nakshatra: record.nakshatra ?? record.nak,
      pada: record.pada,
      lagna: record.lagna,
    }, id);
    if (hasContent(profile)) {
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

export function storedProfileCandidates(raw: unknown[]): StoredProfileCandidate[] {
  const candidates: StoredProfileCandidate[] = [];
  for (const value of raw) {
    if (!isRecord(value)) continue;
    const record = value as Record<string, unknown>;
    if (Number(record.schemaVersion) > GUEST_PROFILE_SCHEMA_VERSION) continue;
    if (!hasProfileContent(record)) continue;
    const preview = normalizeProfile({
      source: 'manual',
      name: record.name,
      nakshatra: record.nakshatra ?? record.nak,
      pada: record.pada,
      lagna: record.lagna,
    }, 'guest_validation');
    if (!hasContent(preview)) continue;
    candidates.push({ record, storedId: validStoredId(record.id) ? record.id : null });
  }
  return candidates;
}

export function hasUnsupportedRows(raw: unknown[]): boolean {
  let supportedProfiles = 0;
  for (const value of raw) {
    const classification = classifyStoredRow(value);
    if (classification === 'unsupported') return true;
    if (classification === 'supported') supportedProfiles += 1;
    if (supportedProfiles > MAX_GUEST_PROFILES) return true;
  }
  return false;
}

export function classifyStoredRow(value: unknown): 'unsupported' | 'blank' | 'empty' | 'supported' {
  if (!isRecord(value)) return 'unsupported';
  const record = value as Record<string, unknown>;
  const version = Number(record.schemaVersion);
  if (Number.isFinite(version) && version > GUEST_PROFILE_SCHEMA_VERSION) return 'unsupported';
  if (hasUnownedProfileKeys(record)) return 'unsupported';
  if (!hasProfileContent(record)) {
    return isBlankLegacyPlaceholder(record) ? 'blank' : 'unsupported';
  }
  const profile = normalizeProfile({
    source: 'manual',
    name: record.name,
    nakshatra: record.nakshatra ?? record.nak,
    pada: record.pada,
    lagna: record.lagna,
  }, 'guest_validation');
  return hasContent(profile) ? 'supported' : 'empty';
}
