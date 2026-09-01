import { beforeEach, describe, expect, test } from 'vitest';
import {
  GUEST_PROFILE_SCHEMA_VERSION,
  type GuestProfile,
  type ProfileStorage,
} from '../lib/guest-profile-store';
import {
  GOCHARA_SELECTION_STORAGE_KEY,
  MUHURTAM_PROFILE_IDS_STORAGE_KEY,
  MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY,
  adaptGuestProfile,
  gocharaProfileValue,
  loadGocharaSelection,
  loadMuhurtamProfileSelection,
  loadMuhurtamRoleSelections,
  resolveGocharaSelection,
  saveMuhurtamProfileSelection,
  saveMuhurtamRoleSelection,
  toggleMuhurtamProfileSelection,
} from '../lib/profile-selection';

class MemoryStorage implements ProfileStorage {
  readonly values = new Map<string, string>();
  denyRead = false;
  denyWrite = false;

  getItem(key: string): string | null {
    if (this.denyRead) throw new Error('read denied');
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    if (this.denyWrite) throw new Error('write denied');
    this.values.set(key, value);
  }
}

function profile(
  id: string,
  overrides: Partial<Omit<GuestProfile, 'id' | 'schemaVersion'>> = {},
): GuestProfile {
  return {
    id,
    schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
    source: 'manual',
    name: id,
    nakshatra: 'Rohini',
    pada: null,
    lagna: null,
    janmaRasi: 'Vrishabha',
    birthDetails: null,
    natalChart: null,
    calculation: null,
    ...overrides,
  };
}

let storage: MemoryStorage;

beforeEach(() => { storage = new MemoryStorage(); });

describe('profile adapter', () => {
  test('keeps stable identity and exposes the panel-compatible field shape', () => {
    const adapted = adaptGuestProfile(profile('guest_adapter', {
      name: 'Anu', nakshatra: 'Krittika', pada: 2, lagna: 'Karka',
    }));

    expect(adapted).toEqual({
      id: 'guest_adapter', name: 'Anu', nak: 'Krittika', pada: 2,
      rasi: 'Vrishabha', lagna: 'Karka',
    });
  });

  test('does not invent a Rashi for a straddling star without Padam', () => {
    expect(adaptGuestProfile(profile('guest_straddler', {
      nakshatra: 'Krittika', pada: null,
    })).rasi).toBeNull();
  });
});

describe('Gochara stable selection', () => {
  test.each(['', '0', '6', '11'])('preserves whole-sky and numeric Rashi mode %j', value => {
    const resolved = resolveGocharaSelection(value, []);
    expect(resolved.value).toBe(value);
    expect(resolved.fallback).toBeNull();
    expect(resolved.kind).toBe(value === '' ? 'whole-sky' : 'rashi');
  });

  test.each(['p1', 'p1r', 'p1l'])('migrates legacy %s once to a stable ready profile ID', legacy => {
    const profiles = [
      profile('guest_first'),
      profile('guest_second', { name: 'Second', lagna: 'Karka' }),
    ];
    storage.setItem(GOCHARA_SELECTION_STORAGE_KEY, legacy);

    const migrated = loadGocharaSelection(storage, profiles);

    expect(migrated.value).toBe(gocharaProfileValue('guest_second'));
    expect(migrated.profile).toMatchObject({ id: 'guest_second', name: 'Second' });
    expect(migrated.legacySelectionDetected).toBe(true);
    expect(migrated.migratedFromLegacy).toBe(true);
    expect(storage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe('profile:guest_second');
  });

  test('recreates the legacy ready-profile order before assigning a stable ID', () => {
    const profiles = [
      profile('guest_incomplete', { nakshatra: 'Krittika', pada: null }),
      profile('guest_ready'),
    ];
    storage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'p0');

    const result = loadGocharaSelection(storage, profiles);

    expect(result.value).toBe(gocharaProfileValue('guest_ready'));
    expect(result.profile).toMatchObject({ id: 'guest_ready' });
    expect(result.fallback).toBeNull();
    expect(result.legacySelectionDetected).toBe(true);
    expect(result.migratedFromLegacy).toBe(true);
    expect(storage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe(
      'profile:guest_ready',
    );
  });

  test('does not shift a later legacy selection when an incomplete row precedes it', () => {
    const profiles = [
      profile('guest_incomplete', { nakshatra: 'Krittika', pada: null }),
      profile('guest_alice'),
      profile('guest_bob'),
    ];
    storage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'p1');

    const result = loadGocharaSelection(storage, profiles);

    expect(result.value).toBe(gocharaProfileValue('guest_bob'));
    expect(result.profile).toMatchObject({ id: 'guest_bob' });
    expect(storage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe(
      'profile:guest_bob',
    );
  });

  test('survives profile reorder and edit after the legacy value is migrated', () => {
    const original = [
      profile('guest_one'),
      profile('guest_stable', { name: 'Before' }),
    ];
    storage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'p1');
    loadGocharaSelection(storage, original);
    const reorderedAndEdited = [
      profile('guest_stable', { name: 'After', lagna: 'Simha' }),
      profile('guest_one'),
    ];

    const result = loadGocharaSelection(storage, reorderedAndEdited);

    expect(result.value).toBe('profile:guest_stable');
    expect(result.profile).toMatchObject({ id: 'guest_stable', name: 'After', lagna: 'Simha' });
    expect(result.migratedFromLegacy).toBe(false);
  });

  test('falls back with an explanation when the active profile is deleted', () => {
    storage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'profile:guest_deleted');

    const result = loadGocharaSelection(storage, []);

    expect(result.value).toBe('');
    expect(result.fallback).toMatchObject({ code: 'profile-deleted' });
    expect(result.fallback?.message).toContain('no longer available');
    expect(storage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe('');
  });

  test('falls back when an edit makes the active profile Horoscope-incomplete', () => {
    storage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'profile:guest_edited');
    const result = loadGocharaSelection(storage, [
      profile('guest_edited', { nakshatra: null, pada: null }),
    ]);

    expect(result.value).toBe('');
    expect(result.fallback).toMatchObject({
      code: 'profile-not-horoscope-ready', missingField: 'nakshatra',
    });
    expect(result.fallback?.message).toContain('birth star');
  });

  test('rejects malformed selections and an out-of-range Rashi safely', () => {
    for (const invalid of ['12', '-1', 'profile:', 'not-a-view']) {
      const result = resolveGocharaSelection(invalid, []);
      expect(result.value).toBe('');
      expect(result.fallback).toMatchObject({ code: 'invalid-selection' });
    }
  });

  test('tolerates storage denial and reports an in-memory fallback', () => {
    storage.denyRead = true;
    const result = loadGocharaSelection(storage, [profile('guest_unused')]);

    expect(result).toMatchObject({
      value: '', persistence: 'memory', storageIssue: 'storage-unavailable',
      fallback: { code: 'storage-unavailable' },
    });
  });
});

describe('Muhurtam stable participant selection', () => {
  test('initializes an absent key from existing Muhurtam-ready profiles once', () => {
    const profiles = [
      profile('guest_ready_a', { name: 'A' }),
      profile('guest_name_only', { nakshatra: null, name: 'Incomplete' }),
      profile('guest_straddler', { nakshatra: 'Krittika', pada: null, name: 'K' }),
    ];

    const result = loadMuhurtamProfileSelection(storage, profiles);

    expect(result.selectedIds).toEqual(['guest_ready_a', 'guest_straddler']);
    expect(result.profiles).toEqual([
      { id: 'guest_ready_a', name: 'A', nak: 'Rohini', pada: null, rasi: 'Vrishabha', lagna: null },
      { id: 'guest_straddler', name: 'K', nak: 'Krittika', pada: null, rasi: null, lagna: null },
    ]);
    expect(result.initializedFromProfiles).toBe(true);
    expect(result.message).toContain('existing Muhurtam-ready profiles');
    expect(storage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe(
      '["guest_ready_a","guest_straddler"]',
    );
  });

  test('an explicit empty list stays empty instead of reinitializing', () => {
    storage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    const result = loadMuhurtamProfileSelection(storage, [profile('guest_ready')]);

    expect(result.selectedIds).toEqual([]);
    expect(result.initializedFromProfiles).toBe(false);
  });

  test('persists IDs independently of profile record order and reflects edits', () => {
    storage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_second","guest_first"]',
    );
    const reordered = [
      profile('guest_first', { name: 'First edited' }),
      profile('guest_second', { name: 'Second edited' }),
    ];

    const result = loadMuhurtamProfileSelection(storage, reordered);

    expect(result.selectedIds).toEqual(['guest_second', 'guest_first']);
    expect(result.profiles.map(candidate => candidate.name)).toEqual([
      'Second edited', 'First edited',
    ]);
  });

  test('filters deleted and no-longer-ready IDs and repairs storage', () => {
    storage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_ready","guest_deleted","guest_incomplete"]',
    );
    const profiles = [
      profile('guest_ready'),
      profile('guest_incomplete', { nakshatra: null }),
    ];

    const result = loadMuhurtamProfileSelection(storage, profiles);

    expect(result.selectedIds).toEqual(['guest_ready']);
    expect(result.dropped).toEqual([
      { id: 'guest_deleted', reason: 'deleted' },
      { id: 'guest_incomplete', reason: 'not-muhurta-ready' },
    ]);
    expect(storage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe('["guest_ready"]');
  });

  test.each(['{broken', '{}', 'null'])('recovers malformed storage %j without throwing', raw => {
    storage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, raw);

    const result = loadMuhurtamProfileSelection(storage, [profile('guest_ready')]);

    expect(result.selectedIds).toEqual([]);
    expect(result.storageIssue).toBe('malformed-storage');
    expect(result.message).toContain('unreadable');
    expect(storage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe('[]');
  });

  test('keeps valid IDs from a mixed array while normalizing invalid entries', () => {
    storage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_ready",42,"guest_ready",null]',
    );
    const result = loadMuhurtamProfileSelection(storage, [profile('guest_ready')]);

    expect(result.selectedIds).toEqual(['guest_ready']);
    expect(storage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe('["guest_ready"]');
  });

  test('rejects a fifth participant without disturbing the selected four', () => {
    const profiles = Array.from({ length: 5 }, (_, index) =>
      profile(`guest_person_${index + 1}`));
    const firstFour = profiles.slice(0, 4).map(candidate => candidate.id);

    const result = toggleMuhurtamProfileSelection(
      storage,
      firstFour,
      'guest_person_5',
      true,
      profiles,
    );

    expect(result.selectedIds).toEqual(firstFour);
    expect(result.selectionIssue).toBe('selection-limit');
    expect(result.dropped).toContainEqual({
      id: 'guest_person_5', reason: 'selection-limit',
    });
    expect(result.message).toContain('up to 4');
    expect(JSON.parse(storage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY) || '[]')).toEqual(firstFour);
  });

  test('caps bulk saves at four ready stable IDs', () => {
    const profiles = Array.from({ length: 5 }, (_, index) =>
      profile(`guest_bulk_${index + 1}`));
    const result = saveMuhurtamProfileSelection(
      storage,
      profiles.map(candidate => candidate.id),
      profiles,
    );

    expect(result.selectedIds).toEqual(profiles.slice(0, 4).map(candidate => candidate.id));
    expect(result.selectionIssue).toBe('selection-limit');
    expect(result.dropped).toEqual([
      { id: 'guest_bulk_5', reason: 'selection-limit' },
    ]);
  });

  test('persists a safe empty state so later contextual creation stays isolated', () => {
    const result = loadMuhurtamProfileSelection(storage, []);

    expect(result).toMatchObject({
      selectedIds: [], profiles: [], initializedFromProfiles: false,
      storageIssue: null, selectionIssue: null,
    });
    expect(storage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe('[]');

    const afterHoroscopeCreation = loadMuhurtamProfileSelection(
      storage,
      [profile('guest_created_elsewhere')],
    );
    expect(afterHoroscopeCreation.selectedIds).toEqual([]);
    expect(afterHoroscopeCreation.initializedFromProfiles).toBe(false);
  });

  test('tolerates read and write denial without losing the current-page selection', () => {
    storage.denyRead = true;
    const fromDeniedRead = loadMuhurtamProfileSelection(
      storage,
      [profile('guest_ready')],
    );
    expect(fromDeniedRead).toMatchObject({
      selectedIds: ['guest_ready'], persistence: 'memory',
      storageIssue: 'storage-unavailable', initializedFromProfiles: true,
    });

    storage.denyRead = false;
    storage.denyWrite = true;
    const fromDeniedWrite = saveMuhurtamProfileSelection(
      storage,
      ['guest_ready'],
      [profile('guest_ready')],
    );
    expect(fromDeniedWrite).toMatchObject({
      selectedIds: ['guest_ready'], persistence: 'memory',
      storageIssue: 'storage-unavailable',
    });
  });
});

describe('Muhurtam stable role selection', () => {
  test('persists a bounded saved-profile role by stable ID and restores edits', () => {
    const profiles = [
      profile('guest_a', { name: 'A' }),
      profile('guest_b', { name: 'B' }),
    ];
    const saved = saveMuhurtamRoleSelection(
      storage, {}, 'surgery', 'guest_b', profiles,
    );
    expect(saved.selections).toEqual({ surgery: 'guest_b' });
    expect(JSON.parse(storage.getItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY) || '{}'))
      .toEqual({ version: 1, roles: { surgery: 'guest_b' } });

    const restored = loadMuhurtamRoleSelections(storage, [
      profile('guest_b', { name: 'B edited' }),
      profile('guest_a', { name: 'A' }),
    ]);
    expect(restored.selections).toEqual({ surgery: 'guest_b' });
  });

  test('repairs deleted, incomplete, unknown-activity and malformed role state', () => {
    storage.setItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY, JSON.stringify({
      version: 1,
      roles: {
        travel: 'guest_ready',
        surgery: 'guest_deleted',
        seemantha: 'guest_incomplete',
        invented: 'guest_ready',
      },
    }));
    const result = loadMuhurtamRoleSelections(storage, [
      profile('guest_ready'),
      profile('guest_incomplete', { nakshatra: null }),
    ]);
    expect(result.selections).toEqual({ travel: 'guest_ready' });
    expect(JSON.parse(storage.getItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY) || '{}'))
      .toEqual({ version: 1, roles: { travel: 'guest_ready' } });

    storage.setItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY, '{broken');
    expect(loadMuhurtamRoleSelections(storage, [profile('guest_ready')]))
      .toMatchObject({ selections: {}, storageIssue: 'malformed-storage' });
  });

  test('keeps transient participant IDs and denied storage out of persistence', () => {
    const profiles = [profile('guest_ready')];
    const transient = saveMuhurtamRoleSelection(
      storage, {}, 'travel', 'manual_1', profiles,
    );
    expect(transient.selections).toEqual({});

    storage.denyRead = true;
    expect(loadMuhurtamRoleSelections(storage, profiles)).toMatchObject({
      selections: {}, persistence: 'memory', storageIssue: 'storage-unavailable',
    });
    storage.denyRead = false;
    storage.denyWrite = true;
    expect(saveMuhurtamRoleSelection(
      storage, {}, 'travel', 'guest_ready', profiles,
    )).toMatchObject({
      selections: { travel: 'guest_ready' },
      persistence: 'memory', storageIssue: 'storage-unavailable',
    });
  });
});
