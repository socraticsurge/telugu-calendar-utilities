import { NAKSHATRA_NAMES, RASI_NAMES } from '../../data/rasis';
import { isOwnedBirthProfileRecord } from './birth-ownership';
import {
  GUEST_BIRTH_PROFILE_SCHEMA_VERSION,
  GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
  GUEST_PROFILE_SCHEMA_VERSION,
  MAX_GUEST_PROFILES,
  type StoredBirthProfileEnvelope,
  type StoredProfileCommitMarker,
  type StoredProfileRecord,
} from './types';
import {
  canonical,
  hasExactKeys,
  pada,
  text,
  validRevision,
  validStoredId,
  isRecord,
} from './values';


export function isOwnedOrphanTransaction(
  birthText: string | null,
  commitText: string | null,
): boolean {
  if (!isOwnedOrphanBirthText(birthText) || !isOwnedOrphanCommitText(commitText)) {
    return false;
  }
  if (birthText === null || commitText === null) return true;
  const envelope = JSON.parse(birthText) as StoredBirthProfileEnvelope;
  const commit = JSON.parse(commitText) as StoredProfileCommitMarker;
  if (!envelope.revision || envelope.revision !== commit.revision) return false;
  const rows = ownedOrphanBaseRows(commit.baseText);
  if (!rows) return false;
  return Object.entries(envelope.profiles).every(([id, extension]) => {
    const row = rows.get(id);
    return Boolean(row)
      && extension.nakshatra === row!.nak
      && extension.pada === row!.pada
      && extension.lagna === row!.lagna;
  });
}

export function ownedOrphanBaseRows(rawText: string): Map<string, StoredProfileRecord> | null {
  let value: unknown;
  try {
    value = JSON.parse(rawText);
  } catch {
    return null;
  }
  if (!Array.isArray(value) || value.length > MAX_GUEST_PROFILES) return null;
  const rows = new Map<string, StoredProfileRecord>();
  for (const item of value) {
    if (!isRecord(item)) return null;
    const record = item as Record<string, unknown>;
    if (!hasExactKeys(record, ['id', 'schemaVersion', 'name', 'nak', 'pada', 'lagna'])) {
      return null;
    }
    if (!validStoredId(record.id) || rows.has(record.id)) return null;
    if (!canonicalBaseContent(record)) return null;
    rows.set(record.id, record as unknown as StoredProfileRecord);
  }
  return rows;
}

function canonicalBaseContent(record: Record<string, unknown>): boolean {
  if (record.schemaVersion !== GUEST_PROFILE_SCHEMA_VERSION) return false;
  if (typeof record.name !== 'string' || text(record.name) !== record.name) return false;
  if (!(record.nak === '' || canonical(record.nak, NAKSHATRA_NAMES) === record.nak)) return false;
  if (!(record.pada === '' || pada(record.pada) === record.pada)) return false;
  if (!(record.lagna === '' || canonical(record.lagna, RASI_NAMES) === record.lagna)) return false;
  return Boolean(record.name || record.nak || record.lagna);
}

export function isOwnedOrphanCommitText(rawText: string | null): boolean {
  if (rawText === null) return true;
  let value: unknown;
  try {
    value = JSON.parse(rawText);
  } catch {
    return false;
  }
  if (!isRecord(value)) return false;
  const record = value as Record<string, unknown>;
  return hasExactKeys(record, ['schemaVersion', 'revision', 'baseText'])
    && record.schemaVersion === GUEST_PROFILE_COMMIT_SCHEMA_VERSION
    && validRevision(record.revision)
    && typeof record.baseText === 'string'
    && ownedOrphanBaseRows(record.baseText) !== null;
}

export function isOwnedOrphanBirthText(rawText: string | null): boolean {
  if (rawText === null) return true;
  let value: unknown;
  try {
    value = JSON.parse(rawText);
  } catch {
    return false;
  }
  if (!isRecord(value)) return false;
  const envelope = value as Record<string, unknown>;
  if (envelope.schemaVersion !== GUEST_BIRTH_PROFILE_SCHEMA_VERSION) return false;
  if (!isRecord(envelope.profiles)) return false;
  const keys = envelope.revision === undefined
    ? ['schemaVersion', 'profiles']
    : ['schemaVersion', 'revision', 'profiles'];
  if (!hasExactKeys(envelope, keys)) return false;
  if (envelope.revision !== undefined && !validRevision(envelope.revision)) return false;
  return Object.values(envelope.profiles as Record<string, unknown>)
    .every(isOwnedBirthProfileRecord);
}
