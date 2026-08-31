import { beforeEach, describe, expect, test, vi } from 'vitest';
import {
  GUEST_BIRTH_PROFILE_SCHEMA_VERSION,
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
  GUEST_PROFILE_COMMIT_STORAGE_KEY,
  GUEST_PROFILE_SCHEMA_VERSION,
  GUEST_PROFILE_STORAGE_KEY,
  GuestProfileStoreError,
  canonicalLegacyGuestProfileLagna,
  browserProfileStorage,
  createGuestProfileStore,
  guestProfileReadiness,
  mergeLegacyGuestProfileRow,
  readLegacyGuestProfileRows,
  writeLegacyGuestProfileRows,
  type GuestProfile,
  type GuestProfileDraft,
  type ProfileStorage,
} from '../lib/guest-profile-store';

function ids(...values: string[]): () => string {
  let index = 0;
  return () => values[index++] || `guest_generated_${index}`;
}

class MemoryStorage implements ProfileStorage {
  private readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) || null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }
}

let storage: MemoryStorage;

function rawProfiles(): unknown[] {
  return JSON.parse(storage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
}

function rawCommit(): {
  schemaVersion: number;
  revision: string;
  baseText: string;
} {
  return JSON.parse(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY) || '{}');
}

function birthProfileDraft(name = 'Anu'): GuestProfileDraft {
  const rashis = [
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha',
    'Kanya', 'Tula', 'Vrischika', 'Dhanu',
  ];
  return {
    source: 'birth-details',
    name,
    nakshatra: 'Rohini',
    pada: 2,
    lagna: 'Karka',
    janmaRasi: 'Vrishabha',
    birthDetails: {
      dateOfBirth: '1990-05-12',
      timeOfBirth: '14:35',
      placeLabel: 'Vijayawada, Andhra Pradesh, India',
      latitude: 16.5062,
      longitude: 80.648,
      timezone: 'Asia/Kolkata',
    },
    natalChart: {
      lagnaDegree: 12.345,
      planets: rashis.map((rashi, index) => ({
        name: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'][index],
        rashi,
        degree: index + 0.25,
        house: index + 1,
        retrograde: index === 6,
      })),
    },
    calculation: {
      contractVersion: '1.0',
      engine: {
        name: 'DashaFlow', version: '1.0.0', ayanamsha: 'Lahiri', ephemeris: 'moshier',
      },
    },
  };
}

beforeEach(() => { storage = new MemoryStorage(); });

describe('legacy migration', () => {
  test('adds stable IDs and schema versions without breaking the legacy row shape', () => {
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      { name: 'Vinay', nak: 'Krittika', pada: '2', lagna: 'Mesha' },
      { name: 'Name only', nak: '', pada: '', lagna: '' },
      { name: '', nak: '', pada: '', lagna: '' },
    ]));

    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_profile_1', 'guest_profile_2'),
    });

    expect(store.getSnapshot().profiles).toEqual([
      {
        id: 'guest_profile_1',
        schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
        source: 'manual',
        name: 'Vinay',
        nakshatra: 'Krittika',
        pada: 2,
        lagna: 'Mesha',
        janmaRasi: 'Vrishabha',
        birthDetails: null,
        natalChart: null,
        calculation: null,
      },
      {
        id: 'guest_profile_2',
        schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
        source: 'manual',
        name: 'Name only',
        nakshatra: null,
        pada: null,
        lagna: null,
        janmaRasi: null,
        birthDetails: null,
        natalChart: null,
        calculation: null,
      },
    ]);
    expect(rawProfiles()).toEqual([
      {
        id: 'guest_profile_1', schemaVersion: 1, name: 'Vinay',
        nak: 'Krittika', pada: 2, lagna: 'Mesha',
      },
      {
        id: 'guest_profile_2', schemaVersion: 1, name: 'Name only',
        nak: '', pada: '', lagna: '',
      },
    ]);
  });

  test('is idempotent across reloads and repairs duplicate IDs', () => {
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      { id: 'guest_existing', schemaVersion: 1, name: 'One', nak: 'Rohini' },
      { id: 'guest_existing', schemaVersion: 1, name: 'Two', nak: 'Hasta' },
    ]));
    const first = createGuestProfileStore(storage, {
      idFactory: ids('guest_repaired'),
    });
    const firstIds = first.getSnapshot().profiles.map(profile => profile.id);
    const second = createGuestProfileStore(storage, {
      idFactory: () => { throw new Error('migration should not request another ID'); },
    });

    expect(firstIds).toEqual(['guest_existing', 'guest_repaired']);
    expect(second.getSnapshot().profiles.map(profile => profile.id)).toEqual(firstIds);
  });

  test('normalizes unknown canonical values and invalid Padam safely', () => {
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      { name: 'Known', nak: 'Not a star', pada: 8, lagna: 'Not a rasi' },
      { name: '', nak: 'Rohini', pada: 9, lagna: '' },
    ]));
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_known_1', 'guest_known_2'),
    });

    expect(store.getSnapshot().profiles).toMatchObject([
      { name: 'Known', nakshatra: null, pada: null, lagna: null },
      { name: '', nakshatra: 'Rohini', pada: null, lagna: null },
    ]);
  });

  test('does not let a discarded invalid record consume a valid stable ID', () => {
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      { id: 'guest_shared', schemaVersion: 1, nak: 'Unknown' },
      { id: 'guest_shared', schemaVersion: 1, name: 'Kept', nak: 'Rohini' },
    ]));
    const store = createGuestProfileStore(storage, {
      idFactory: () => { throw new Error('the valid ID should remain available'); },
    });

    expect(store.getSnapshot().profiles).toMatchObject([
      { id: 'guest_shared', name: 'Kept', nakshatra: 'Rohini' },
    ]);
  });
});

describe('readiness', () => {
  test('requires only Nakshatra for Muhurtam and Padam only for a straddling Horoscope star', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_krittika', 'guest_rohini'),
    });
    const krittika = store.create({ name: 'K', nakshatra: 'Krittika' });
    const rohini = store.create({ name: 'R', nakshatra: 'Rohini' });

    expect(guestProfileReadiness(krittika)).toEqual({
      muhurta: true,
      horoscope: false,
      janmaRasi: null,
      missingForHoroscope: 'pada',
    });
    expect(guestProfileReadiness(rohini)).toEqual({
      muhurta: true,
      horoscope: true,
      janmaRasi: 'Vrishabha',
      missingForHoroscope: null,
    });
  });
});

describe('CRUD and subscriptions', () => {
  test('creates, updates, removes and clears stable profiles', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_profile_a', 'guest_profile_b'),
    });
    const listener = vi.fn();
    store.subscribe(listener);

    const created = store.create({ name: ' A ', nakshatra: 'Rohini' });
    const updated = store.update(created.id, { name: 'Anu', lagna: 'Karka' });
    expect(updated).toMatchObject({
      id: created.id, name: 'Anu', nakshatra: 'Rohini', lagna: 'Karka',
    });
    expect(store.remove(created.id)).toBe(true);
    expect(store.remove(created.id)).toBe(false);
    store.create({ name: 'B' });
    store.clear();

    expect(store.getSnapshot().profiles).toEqual([]);
    expect(listener).toHaveBeenCalledTimes(5);
    expect(rawProfiles()).toEqual([]);
  });

  test('returns copies instead of mutable internal state', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_immutable'),
    });
    const created = store.create({ name: 'Original' });
    created.name = 'Changed outside';
    const fromGet = store.get(created.id)!;
    fromGet.name = 'Changed again';

    const snapshot = store.getSnapshot();
    expect(store.get(created.id)?.name).toBe('Original');
    expect(Object.isFrozen(snapshot)).toBe(true);
    expect(Object.isFrozen(snapshot.profiles)).toBe(true);
    expect(Object.isFrozen(snapshot.profiles[0])).toBe(true);
  });

  test('one listener cannot mutate the snapshot seen by another listener', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_listeners'),
    });
    const lengths: number[] = [];
    store.subscribe(snapshot => {
      try {
        (snapshot.profiles as GuestProfile[]).pop();
      } catch { /* the frozen array rejects this mutation */ }
    });
    store.subscribe(snapshot => lengths.push(snapshot.profiles.length));

    store.create({ name: 'Still present' });
    expect(lengths).toEqual([1]);
  });

  test('listener changes apply only to the next notification', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_listener_snapshot', 'guest_listener_next'),
    });
    const calls: string[] = [];
    const later = () => calls.push('later');
    store.subscribe(() => {
      calls.push('first');
      store.subscribe(later);
    });

    store.create({ name: 'One' });
    expect(calls).toEqual(['first']);
    store.create({ name: 'Two' });
    expect(calls).toEqual(['first', 'first', 'later']);
  });

  test('isolates faulty listeners after a persisted mutation', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_listener_failure'),
    });
    const received: string[] = [];
    store.subscribe(() => { throw new Error('render failed'); });
    store.subscribe(snapshot => received.push(snapshot.profiles[0].name));

    expect(() => store.create({ name: 'Persisted' })).not.toThrow();
    expect(rawProfiles()).toMatchObject([{ name: 'Persisted' }]);
    expect(received).toEqual(['Persisted']);
  });

  test('rejects empty records, unknown IDs and a fifth profile', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids(
        'guest_limit_1', 'guest_limit_2', 'guest_limit_3',
        'guest_limit_4', 'guest_limit_5',
      ),
    });
    expect(() => store.create({})).toThrowError(
      expect.objectContaining<Partial<GuestProfileStoreError>>({ code: 'empty-profile' }),
    );
    for (let i = 1; i <= 4; i += 1) store.create({ name: `Person ${i}` });
    expect(() => store.create({ name: 'Five' })).toThrowError(
      expect.objectContaining<Partial<GuestProfileStoreError>>({ code: 'profile-limit' }),
    );
    expect(() => store.update('missing_id', { name: 'No' })).toThrowError(
      expect.objectContaining<Partial<GuestProfileStoreError>>({ code: 'profile-not-found' }),
    );
  });

  test('keeps quote and HTML payloads inert as plain stored data', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_untrusted'),
    });
    const name = `\"><img src=x onerror=alert('x')>`;
    const profile = store.create({ name, nakshatra: 'Hasta' });

    expect(profile.name).toBe(name);
    expect((rawProfiles()[0] as { name: string }).name).toBe(name);
  });
});

describe('birth profile extension storage', () => {
  test('keeps the legacy base row compatible while round-tripping birth details and chart provenance', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_birth_profile'),
    });
    const created = store.create(birthProfileDraft());

    expect(created).toMatchObject({
      source: 'birth-details',
      nakshatra: 'Rohini',
      pada: 2,
      janmaRasi: 'Vrishabha',
      lagna: 'Karka',
      birthDetails: { timezone: 'Asia/Kolkata' },
      calculation: { contractVersion: '1.0' },
    });
    expect(rawProfiles()).toEqual([{
      id: 'guest_birth_profile', schemaVersion: 1, name: 'Anu',
      nak: 'Rohini', pada: 2, lagna: 'Karka',
    }]);

    const extension = JSON.parse(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}');
    expect(extension).toMatchObject({
      schemaVersion: GUEST_BIRTH_PROFILE_SCHEMA_VERSION,
      profiles: {
        guest_birth_profile: {
          source: 'birth-details',
          nakshatra: 'Rohini',
          pada: 2,
          lagna: 'Karka',
          janmaRasi: 'Vrishabha',
          birthDetails: { placeLabel: 'Vijayawada, Andhra Pradesh, India' },
          natalChart: { lagnaDegree: 12.345 },
          calculation: { engine: { name: 'DashaFlow' } },
        },
      },
    });

    const reloaded = createGuestProfileStore(storage, {
      idFactory: () => { throw new Error('stable row should not need a new ID'); },
    });
    expect(reloaded.get('guest_birth_profile')).toEqual(created);
  });

  test('binds the birth envelope to an exact committed base payload', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_bound_profile'),
      revisionFactory: ids('revision_bound_001'),
    });
    const created = store.create(birthProfileDraft());
    const baseText = storage.getItem(GUEST_PROFILE_STORAGE_KEY)!;
    const envelope = JSON.parse(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}');
    const commit = rawCommit();

    expect(Object.keys(commit).sort()).toEqual(['baseText', 'revision', 'schemaVersion']);
    expect(commit).toEqual({
      schemaVersion: GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
      revision: 'revision_bound_001',
      baseText,
    });
    expect(envelope.revision).toBe(commit.revision);
    expect(rawProfiles()).toEqual([{
      id: 'guest_bound_profile', schemaVersion: 1, name: 'Anu',
      nak: 'Rohini', pada: 2, lagna: 'Karka',
    }]);

    const reloaded = createGuestProfileStore(storage, {
      idFactory: () => { throw new Error('the committed ID must stay stable'); },
      revisionFactory: ids('revision_unused_001'),
    });
    expect(reloaded.get(created.id)).toEqual(created);
  });

  test.each([
    ['base write', GUEST_PROFILE_STORAGE_KEY],
    ['birth-envelope write', GUEST_BIRTH_PROFILE_STORAGE_KEY],
    ['commit-marker write', GUEST_PROFILE_COMMIT_STORAGE_KEY],
  ])('does not attach same-derived birth data after a failed %s', (_label, failureKey) => {
    let armed = false;
    const flaky: ProfileStorage = {
      getItem: key => storage.getItem(key),
      setItem: (key, value) => {
        if (armed && key === failureKey) throw new DOMException('full', 'QuotaExceededError');
        storage.setItem(key, value);
      },
      removeItem: key => storage.removeItem(key),
    };
    const store = createGuestProfileStore(flaky, {
      idFactory: ids('guest_torn_profile'),
      revisionFactory: ids('revision_before_001', 'revision_after_002'),
    });
    const created = store.create(birthProfileDraft());
    const originalBase = storage.getItem(GUEST_PROFILE_STORAGE_KEY);
    const originalCommit = storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY);
    armed = true;

    store.update(created.id, {
      birthDetails: {
        ...created.birthDetails!,
        placeLabel: 'Same chart, newly corrected birthplace label',
      },
    });

    expect(store.getSnapshot()).toMatchObject({
      persistence: 'memory', issue: 'storage-unavailable',
    });
    if (failureKey === GUEST_PROFILE_STORAGE_KEY) {
      expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(originalBase);
      expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBe(originalCommit);
      const retainedEnvelope = JSON.parse(
        storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}',
      );
      expect(retainedEnvelope.revision).toBe('revision_before_001');
    } else {
      expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(originalBase);
      expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBeNull();
      expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBeNull();
    }

    const reloaded = createGuestProfileStore(storage, {
      idFactory: () => { throw new Error('the stored ID must stay stable'); },
      revisionFactory: ids('revision_unused_001'),
    });
    expect(reloaded.getSnapshot()).toMatchObject({ persistence: 'persistent' });
    expect(reloaded.get(created.id)).toMatchObject({
      source: failureKey === GUEST_PROFILE_STORAGE_KEY ? 'birth-details' : 'manual',
    });
  });

  test.each([
    ['base write', GUEST_PROFILE_STORAGE_KEY],
    ['birth-envelope write', GUEST_BIRTH_PROFILE_STORAGE_KEY],
    ['commit-marker write', GUEST_PROFILE_COMMIT_STORAGE_KEY],
  ])('keeps first-create storage recoverable after a failed %s', (_label, failureKey) => {
    let armed = true;
    const flaky: ProfileStorage = {
      getItem: key => storage.getItem(key),
      setItem: (key, value) => {
        if (armed && key === failureKey) throw new DOMException('full', 'QuotaExceededError');
        storage.setItem(key, value);
      },
      removeItem: key => storage.removeItem(key),
    };
    const store = createGuestProfileStore(flaky, {
      idFactory: ids('guest_first_failure'),
      revisionFactory: ids('revision_first_failure'),
    });

    store.create(birthProfileDraft());
    expect(store.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_first_failure', source: 'birth-details' }],
      persistence: 'memory', issue: 'storage-unavailable',
    });
    if (failureKey === GUEST_PROFILE_STORAGE_KEY) {
      expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBeNull();
    } else {
      expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).not.toBeNull();
    }
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBeNull();
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBeNull();

    armed = false;
    const recovered = createGuestProfileStore(flaky, {
      idFactory: ids('guest_after_failure'),
      revisionFactory: ids('revision_after_failure'),
    });
    expect(recovered.getSnapshot()).toMatchObject({
      persistence: 'persistent', issue: null,
    });
    if (failureKey === GUEST_PROFILE_STORAGE_KEY) {
      recovered.create({ name: 'Recovered' });
      expect(recovered.getSnapshot().profiles).toMatchObject([{ name: 'Recovered' }]);
    } else {
      expect(recovered.get('guest_first_failure')).toMatchObject({
        source: 'manual', birthDetails: null,
      });
    }
  });

  test('restores a coherent cross-tab snapshot only after the final commit marker', () => {
    const initial = createGuestProfileStore(storage, {
      idFactory: ids('guest_cross_tab'),
      revisionFactory: ids('revision_cross_tab_001'),
    });
    const created = initial.create(birthProfileDraft());
    const reader = createGuestProfileStore(storage, {
      idFactory: () => { throw new Error('the stored ID must stay stable'); },
      revisionFactory: ids('revision_reader_unused'),
    });

    const nextStorage = new MemoryStorage();
    for (const key of [
      GUEST_PROFILE_STORAGE_KEY,
      GUEST_BIRTH_PROFILE_STORAGE_KEY,
      GUEST_PROFILE_COMMIT_STORAGE_KEY,
    ]) nextStorage.setItem(key, storage.getItem(key)!);
    const writer = createGuestProfileStore(nextStorage, {
      revisionFactory: ids('revision_cross_tab_002'),
    });
    writer.update(created.id, {
      birthDetails: {
        ...created.birthDetails!,
        placeLabel: 'Cross-tab corrected birthplace label',
      },
    });

    storage.setItem(
      GUEST_PROFILE_STORAGE_KEY,
      nextStorage.getItem(GUEST_PROFILE_STORAGE_KEY)!,
    );
    reader.reload();
    expect(reader.getSnapshot().issue).toBeNull();
    expect(reader.get(created.id)).toMatchObject({
      source: 'birth-details',
      birthDetails: { placeLabel: 'Vijayawada, Andhra Pradesh, India' },
    });

    storage.setItem(
      GUEST_BIRTH_PROFILE_STORAGE_KEY,
      nextStorage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)!,
    );
    reader.reload();
    expect(reader.getSnapshot().issue).toBe('uncommitted-birth-storage');
    expect(reader.get(created.id)?.source).toBe('manual');

    storage.setItem(
      GUEST_PROFILE_COMMIT_STORAGE_KEY,
      nextStorage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)!,
    );
    reader.reload();
    expect(reader.getSnapshot().issue).toBeNull();
    expect(reader.get(created.id)).toMatchObject({
      source: 'birth-details',
      birthDetails: { placeLabel: 'Cross-tab corrected birthplace label' },
    });
  });

  test('upgrades a unique unbound legacy birth extension on first load', () => {
    const source = new MemoryStorage();
    const sourceStore = createGuestProfileStore(source, {
      idFactory: ids('guest_legacy_birth'),
      revisionFactory: ids('revision_source_001'),
    });
    const created = sourceStore.create(birthProfileDraft());
    const legacyEnvelope = JSON.parse(source.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}');
    delete legacyEnvelope.revision;
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, source.getItem(GUEST_PROFILE_STORAGE_KEY)!);
    storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, JSON.stringify(legacyEnvelope));

    const migrated = createGuestProfileStore(storage, {
      idFactory: () => { throw new Error('the legacy stable ID must be reused'); },
      revisionFactory: ids('revision_upgrade_001'),
    });

    expect(migrated.get(created.id)).toEqual(created);
    const upgradedEnvelope = JSON.parse(
      storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}',
    );
    expect(upgradedEnvelope.revision).toBe('revision_upgrade_001');
    expect(rawCommit()).toEqual({
      schemaVersion: GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
      revision: 'revision_upgrade_001',
      baseText: storage.getItem(GUEST_PROFILE_STORAGE_KEY),
    });
    migrated.reload();
    expect(migrated.get(created.id)?.source).toBe('birth-details');
  });

  test.each([
    ['schema type', (envelope: Record<string, unknown>) => {
      envelope.schemaVersion = '1';
    }],
    ['envelope', (envelope: Record<string, unknown>) => {
      envelope.futurePayload = { keep: true };
    }],
    ['profile record', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, Record<string, unknown>>;
      profiles.guest_opaque_birth.futurePayload = { keep: true };
    }],
    ['birth details', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, Record<string, unknown>>;
      const details = profiles.guest_opaque_birth.birthDetails as Record<string, unknown>;
      details.futurePayload = { keep: true };
    }],
    ['natal chart', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, Record<string, unknown>>;
      const chart = profiles.guest_opaque_birth.natalChart as Record<string, unknown>;
      chart.futurePayload = { keep: true };
    }],
    ['planet', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, Record<string, unknown>>;
      const chart = profiles.guest_opaque_birth.natalChart as Record<string, unknown>;
      const planets = chart.planets as Array<Record<string, unknown>>;
      planets[0].futurePayload = { keep: true };
    }],
    ['calculation', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, Record<string, unknown>>;
      const calculation = profiles.guest_opaque_birth.calculation as Record<string, unknown>;
      calculation.futurePayload = { keep: true };
    }],
    ['engine', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, Record<string, unknown>>;
      const calculation = profiles.guest_opaque_birth.calculation as Record<string, unknown>;
      const engine = calculation.engine as Record<string, unknown>;
      engine.futurePayload = { keep: true };
    }],
    ['noncanonical recognized value', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, Record<string, unknown>>;
      const details = profiles.guest_opaque_birth.birthDetails as Record<string, unknown>;
      details.placeLabel = ` ${String(details.placeLabel)}`;
    }],
    ['overlong recognized value', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, Record<string, unknown>>;
      const details = profiles.guest_opaque_birth.birthDetails as Record<string, unknown>;
      details.placeLabel = 'X'.repeat(241);
    }],
    ['primitive profile value', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, unknown>;
      profiles.guest_opaque_birth = 'opaque-sensitive-value';
    }],
    ['array profile value', (envelope: Record<string, unknown>) => {
      const profiles = envelope.profiles as Record<string, unknown>;
      profiles.guest_opaque_birth = ['opaque', { keep: true }];
    }],
  ])('preserves unrecognized legacy birth %s bytes across session mutations', (_label, mutate) => {
    const source = new MemoryStorage();
    const sourceStore = createGuestProfileStore(source, {
      idFactory: ids('guest_opaque_birth'),
      revisionFactory: ids('revision_source_opaque'),
    });
    sourceStore.create(birthProfileDraft());
    const envelope = JSON.parse(
      source.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}',
    ) as Record<string, unknown>;
    delete envelope.revision;
    mutate(envelope);
    const baseBytes = source.getItem(GUEST_PROFILE_STORAGE_KEY)!;
    const birthBytes = JSON.stringify(envelope, null, 2);
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, baseBytes);
    storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);

    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_session_opaque'),
      revisionFactory: ids('revision_must_not_write'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_opaque_birth', source: 'manual' }],
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(baseBytes);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBeNull();

    store.update('guest_opaque_birth', { name: 'Session edit' });
    const added = store.create({ name: 'Session person' });
    store.reload();
    expect(store.get(added.id)?.name).toBe('Session person');
    expect(store.remove('guest_opaque_birth')).toBe(true);
    store.clear();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(baseBytes);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBeNull();
  });

  test.each([
    ['birth envelope', true, false],
    ['commit marker', false, true],
    ['birth envelope and commit marker', true, true],
  ])('fails closed for an orphan %s when the base key is absent', (
    _label,
    includeBirth,
    includeCommit,
  ) => {
    const birthBytes = '{"opaqueSensitiveBirth":"keep-exactly"}';
    const commitBytes = '{"opaqueCommit":"keep-exactly"}';
    if (includeBirth) storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);
    if (includeCommit) storage.setItem(GUEST_PROFILE_COMMIT_STORAGE_KEY, commitBytes);

    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_orphan_session'),
      revisionFactory: ids('revision_must_not_write'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [], persistence: 'memory', issue: 'uncommitted-birth-storage',
    });
    expect(store.canDiscardUncommittedStorage()).toBe(false);
    expect(store.discardUncommittedStorage()).toBe(false);
    const created = store.create({ name: 'Session only', nakshatra: 'Rohini' });
    store.reload();
    expect(store.get(created.id)?.name).toBe('Session only');
    store.clear();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBeNull();
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(
      includeBirth ? birthBytes : null,
    );
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBe(
      includeCommit ? commitBytes : null,
    );
  });

  test('offers explicit cleanup only for a recognized orphan transaction', () => {
    const source = new MemoryStorage();
    const sourceStore = createGuestProfileStore(source, {
      idFactory: ids('guest_owned_orphan'),
      revisionFactory: ids('revision_owned_orphan'),
    });
    sourceStore.create(birthProfileDraft());
    const birthBytes = source.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)!;
    storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);
    const removed: string[] = [];
    const tracked: ProfileStorage = {
      getItem: key => storage.getItem(key),
      setItem: (key, value) => storage.setItem(key, value),
      removeItem: key => {
        removed.push(key);
        storage.removeItem(key);
      },
    };
    const store = createGuestProfileStore(tracked, {
      idFactory: ids('guest_after_orphan_cleanup'),
      revisionFactory: ids('revision_after_orphan_cleanup'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [], persistence: 'memory', issue: 'uncommitted-birth-storage',
    });
    expect(store.canDiscardUncommittedStorage()).toBe(true);
    expect(store.discardUncommittedStorage()).toBe(true);
    expect(removed).toEqual([
      GUEST_BIRTH_PROFILE_STORAGE_KEY,
      GUEST_PROFILE_COMMIT_STORAGE_KEY,
      GUEST_PROFILE_STORAGE_KEY,
    ]);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBeNull();
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBeNull();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBeNull();
    expect(store.getSnapshot()).toMatchObject({
      profiles: [], persistence: 'persistent', issue: null,
    });
    expect(store.create({ name: 'Recovered' }).name).toBe('Recovered');
  });

  test.each([
    ['unowned marker base bytes', () => {
      const markerBytes = JSON.stringify({
        schemaVersion: GUEST_PROFILE_COMMIT_SCHEMA_VERSION,
        revision: 'revision_unowned_marker',
        baseText: JSON.stringify([{
          id: 'guest_future_marker', schemaVersion: 2, name: 'Future',
          nak: 'Rohini', pada: 2, lagna: 'Karka', futurePayload: { keep: true },
        }]),
      });
      return { birthBytes: null, commitBytes: markerBytes };
    }],
    ['mismatched envelope and marker revisions', () => {
      const source = new MemoryStorage();
      const sourceStore = createGuestProfileStore(source, {
        idFactory: ids('guest_mismatch_orphan'),
        revisionFactory: ids('revision_mismatch_birth'),
      });
      sourceStore.create(birthProfileDraft());
      const commit = JSON.parse(
        source.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY) || '{}',
      );
      commit.revision = 'revision_mismatch_commit';
      return {
        birthBytes: source.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY),
        commitBytes: JSON.stringify(commit),
      };
    }],
  ])('does not offer destructive cleanup for %s', (_label, companionBytes) => {
    const { birthBytes, commitBytes } = companionBytes();
    if (birthBytes !== null) storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);
    if (commitBytes !== null) storage.setItem(GUEST_PROFILE_COMMIT_STORAGE_KEY, commitBytes);
    const store = createGuestProfileStore(storage);

    expect(store.getSnapshot()).toMatchObject({
      profiles: [], persistence: 'memory', issue: 'uncommitted-birth-storage',
    });
    expect(store.canDiscardUncommittedStorage()).toBe(false);
    expect(store.discardUncommittedStorage()).toBe(false);
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBeNull();
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBe(commitBytes);
  });

  test('keeps cross-tab reads fail-closed until a reset removes all three keys', () => {
    const writer = createGuestProfileStore(storage, {
      idFactory: ids('guest_reset_lifecycle'),
      revisionFactory: ids('revision_reset_lifecycle'),
    });
    writer.create(birthProfileDraft());
    const reader = createGuestProfileStore(storage);

    storage.removeItem(GUEST_BIRTH_PROFILE_STORAGE_KEY);
    reader.reload();
    expect(reader.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_reset_lifecycle', source: 'manual' }],
      persistence: 'persistent', issue: 'uncommitted-birth-storage',
    });

    storage.removeItem(GUEST_PROFILE_COMMIT_STORAGE_KEY);
    reader.reload();
    expect(reader.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_reset_lifecycle', source: 'manual' }],
      persistence: 'persistent', issue: null,
    });

    storage.removeItem(GUEST_PROFILE_STORAGE_KEY);
    reader.reload();
    expect(reader.getSnapshot()).toMatchObject({
      profiles: [], persistence: 'persistent', issue: null,
    });
  });

  test('fails closed when duplicate stored IDs make a birth extension ambiguous', () => {
    const source = new MemoryStorage();
    const sourceStore = createGuestProfileStore(source, {
      idFactory: ids('guest_duplicate'),
      revisionFactory: ids('revision_source_001'),
    });
    sourceStore.create(birthProfileDraft());
    const legacyEnvelope = JSON.parse(source.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}');
    delete legacyEnvelope.revision;
    const duplicateBase = JSON.stringify([
      {
        id: 'guest_duplicate', schemaVersion: 1, name: 'First',
        nak: 'Rohini', pada: 2, lagna: 'Karka',
      },
      {
        id: 'guest_duplicate', schemaVersion: 1, name: 'Second',
        nak: 'Rohini', pada: 2, lagna: 'Karka',
      },
    ]);
    const birthBytes = JSON.stringify(legacyEnvelope);
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, duplicateBase);
    storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_repaired'),
      revisionFactory: ids('revision_unused_001'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [
        { id: 'guest_duplicate', source: 'manual' },
        { id: 'guest_repaired', source: 'manual' },
      ],
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(duplicateBase);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);

    store.reload();
    store.update('guest_duplicate', { name: 'Session edit' });
    store.remove('guest_repaired');
    store.clear();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(duplicateBase);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
  });

  test('never attaches an extension to an ID synthesized during migration', () => {
    const source = new MemoryStorage();
    const sourceStore = createGuestProfileStore(source, {
      idFactory: ids('guest_collision'),
      revisionFactory: ids('revision_source_001'),
    });
    sourceStore.create(birthProfileDraft());
    const legacyEnvelope = JSON.parse(source.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}');
    delete legacyEnvelope.revision;
    const baseBytes = JSON.stringify([{
      schemaVersion: 1, name: 'No stored ID', nak: 'Rohini', pada: 2, lagna: 'Karka',
    }]);
    const birthBytes = JSON.stringify(legacyEnvelope);
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, baseBytes);
    storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);

    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_collision'),
      revisionFactory: ids('revision_unused_001'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_collision', source: 'manual', birthDetails: null }],
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(baseBytes);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
  });

  test('commits manual conversion and deletion without retaining stale extensions', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_manual_commit', 'guest_deleted_commit'),
      revisionFactory: ids(
        'revision_lifecycle_001',
        'revision_lifecycle_002',
        'revision_lifecycle_003',
        'revision_lifecycle_004',
      ),
    });
    const converted = store.create(birthProfileDraft('Converted'));
    store.update(converted.id, { source: 'manual' });
    const deleted = store.create(birthProfileDraft('Deleted'));
    store.remove(deleted.id);

    const envelope = JSON.parse(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}');
    expect(envelope.profiles).toEqual({});
    expect(envelope.revision).toBe(rawCommit().revision);
    expect(rawCommit().baseText).toBe(storage.getItem(GUEST_PROFILE_STORAGE_KEY));

    const reloaded = createGuestProfileStore(storage, {
      revisionFactory: ids('revision_unused_001'),
    });
    expect(reloaded.get(converted.id)).toMatchObject({
      source: 'manual', birthDetails: null, natalChart: null, calculation: null,
    });
    expect(reloaded.get(deleted.id)).toBeNull();
  });

  test('removes the birth extension when a profile is intentionally converted to manual entry', () => {
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_birth_manual'),
    });
    const created = store.create(birthProfileDraft());
    const updated = store.update(created.id, {
      source: 'manual',
      nakshatra: 'Hasta',
      pada: 3,
      lagna: 'Kanya',
    });

    expect(updated).toMatchObject({
      source: 'manual', birthDetails: null, natalChart: null, calculation: null,
    });
    const extension = JSON.parse(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}');
    expect(extension.profiles).toEqual({});
  });

  test('recovers malformed extension data without deleting the compatible base profile', () => {
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([{
      id: 'guest_birth_damage', schemaVersion: 1, name: 'Anu',
      nak: 'Rohini', pada: 2, lagna: 'Karka',
    }]));
    storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, '{broken');

    const store = createGuestProfileStore(storage);

    expect(store.getSnapshot()).toMatchObject({
      issue: 'malformed-birth-storage',
      profiles: [{ id: 'guest_birth_damage', source: 'manual', name: 'Anu' }],
    });
    expect(JSON.parse(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}')).toEqual({
      schemaVersion: GUEST_BIRTH_PROFILE_SCHEMA_VERSION,
      profiles: {},
    });
  });

  test('does not combine a partially written extension with stale derived base fields', () => {
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([{
      id: 'guest_partial_write', schemaVersion: 1, name: 'Anu',
      nak: 'Rohini', pada: 2, lagna: 'Karka',
    }]));
    const temporary = new MemoryStorage();
    const sourceStore = createGuestProfileStore(temporary, {
      idFactory: ids('guest_partial_write'),
    });
    sourceStore.create({
      ...birthProfileDraft(),
      nakshatra: 'Hasta',
      pada: 3,
      lagna: 'Kanya',
      janmaRasi: 'Kanya',
    });
    storage.setItem(
      GUEST_BIRTH_PROFILE_STORAGE_KEY,
      temporary.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '',
    );

    const store = createGuestProfileStore(storage);
    expect(store.get('guest_partial_write')).toMatchObject({
      source: 'manual',
      nakshatra: 'Rohini',
      pada: 2,
      lagna: 'Karka',
      birthDetails: null,
    });
  });

  test('preserves a future birth-extension envelope byte-for-byte', () => {
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([{
      id: 'guest_birth_future', schemaVersion: 1, name: 'Future',
      nak: 'Rohini', pada: 2, lagna: 'Karka',
    }]));
    const future = JSON.stringify({
      schemaVersion: 2,
      profiles: { guest_birth_future: { future: true } },
    });
    storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, future);

    const store = createGuestProfileStore(storage);
    expect(store.getSnapshot()).toMatchObject({
      persistence: 'memory', issue: 'unsupported-storage-version',
    });
    store.update('guest_birth_future', { name: 'Session only' });
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(future);
  });
});

describe('storage failures', () => {
  test('recovers malformed JSON without crashing and reports the incident', () => {
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, '{broken');
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_unused'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [], persistence: 'persistent', issue: 'malformed-storage',
    });
    expect(rawProfiles()).toEqual([]);
    expect(readLegacyGuestProfileRows(storage)).toEqual([]);
  });

  test.each([
    ['owned', () => {
      const source = new MemoryStorage();
      const sourceStore = createGuestProfileStore(source, {
        idFactory: ids('guest_malformed_owned'),
        revisionFactory: ids('revision_malformed_owned'),
      });
      sourceStore.create(birthProfileDraft());
      return {
        birthBytes: source.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)!,
        commitBytes: source.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)!,
      };
    }],
    ['opaque', () => ({
      birthBytes: '{"futureSensitive":{"keep":"exactly"}}',
      commitBytes: '{"futureCommit":{"keep":"exactly"}}',
    })],
  ])('preserves malformed base and %s companion bytes fail-closed', (_label, bytes) => {
    const baseBytes = '{broken';
    const { birthBytes, commitBytes } = bytes();
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, baseBytes);
    storage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);
    storage.setItem(GUEST_PROFILE_COMMIT_STORAGE_KEY, commitBytes);
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_malformed_session'),
      revisionFactory: ids('revision_must_not_write'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [], persistence: 'memory', issue: 'unsupported-storage-version',
    });
    const created = store.create({ name: 'Session only' });
    store.reload();
    expect(store.get(created.id)?.name).toBe('Session only');
    store.clear();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(baseBytes);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBe(commitBytes);
  });

  test('attempts marker cleanup even when birth-envelope cleanup throws', () => {
    const removeAttempts: string[] = [];
    const flaky: ProfileStorage = {
      getItem: key => storage.getItem(key),
      setItem: (key, value) => {
        if (key === GUEST_PROFILE_COMMIT_STORAGE_KEY) {
          throw new DOMException('full', 'QuotaExceededError');
        }
        storage.setItem(key, value);
      },
      removeItem: key => {
        removeAttempts.push(key);
        if (key === GUEST_BIRTH_PROFILE_STORAGE_KEY) {
          throw new DOMException('denied', 'SecurityError');
        }
        storage.removeItem(key);
      },
    };
    const store = createGuestProfileStore(flaky, {
      idFactory: ids('guest_cleanup_attempt'),
      revisionFactory: ids('revision_cleanup_attempt'),
    });

    store.create(birthProfileDraft());

    expect(store.getSnapshot()).toMatchObject({
      persistence: 'memory', issue: 'storage-unavailable',
    });
    expect(removeAttempts).toEqual([
      GUEST_BIRTH_PROFILE_STORAGE_KEY,
      GUEST_PROFILE_COMMIT_STORAGE_KEY,
    ]);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).not.toBeNull();
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBeNull();
    const reloaded = createGuestProfileStore(storage);
    expect(reloaded.getSnapshot()).toMatchObject({
      persistence: 'persistent', issue: 'uncommitted-birth-storage',
    });
    expect(reloaded.get('guest_cleanup_attempt')).toMatchObject({
      source: 'manual', birthDetails: null,
    });
  });

  test('does not destructively downgrade records from a newer schema', () => {
    const future = JSON.stringify([
      { id: 'guest_future', schemaVersion: 2, name: 'Future', nak: 'Rohini', extra: true },
    ]);
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, future);
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_unused'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [], persistence: 'memory', issue: 'unsupported-storage-version',
    });
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(future);
  });

  test('preserves an unrecognized commit marker and all bound bytes', () => {
    const sourceStore = createGuestProfileStore(storage, {
      idFactory: ids('guest_marker_future'),
      revisionFactory: ids('revision_marker_001'),
    });
    sourceStore.create(birthProfileDraft());
    const baseBytes = storage.getItem(GUEST_PROFILE_STORAGE_KEY)!;
    const birthBytes = storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)!;
    const marker = rawCommit() as Record<string, unknown>;
    marker.futurePayload = { keep: true };
    const markerBytes = JSON.stringify(marker, null, 2);
    storage.setItem(GUEST_PROFILE_COMMIT_STORAGE_KEY, markerBytes);

    const store = createGuestProfileStore(storage, {
      revisionFactory: ids('revision_unused_001'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_marker_future', source: 'manual' }],
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    store.clear();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(baseBytes);
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
    expect(storage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBe(markerBytes);
  });

  test('never overwrites mixed v1 and future-schema bytes across reloads or attempted edits', () => {
    const mixed = JSON.stringify([
      {
        id: 'guest_supported', schemaVersion: 1, name: 'Supported',
        nak: 'Rohini', pada: '', lagna: '',
      },
      {
        id: 'guest_future', schemaVersion: 2, name: 'Future',
        nak: 'Hasta', pada: '', lagna: '', futureField: { keep: true },
      },
    ]);
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, mixed);
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_unused'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_supported', name: 'Supported' }],
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    store.reload();
    expect(store.update('guest_supported', { name: 'Session edit' }).name).toBe('Session edit');
    expect(() => store.update('guest_future', { name: 'Downgrade attempt' })).toThrowError(
      expect.objectContaining<Partial<GuestProfileStoreError>>({ code: 'profile-not-found' }),
    );
    store.reload();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(mixed);

    const repeatedLoad = createGuestProfileStore(storage, {
      idFactory: ids('guest_still_unused'),
    });
    expect(repeatedLoad.get('guest_supported')?.name).toBe('Supported');
    expect(repeatedLoad.get('guest_future')).toBeNull();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(mixed);
  });

  test.each([
    ['primitive', 'opaque-future-row'],
    ['array', ['opaque', { keep: true }]],
    ['unknown object', { futureOnly: { keep: true } }],
    ['contentless v1 object', {
      id: 'guest_hidden', schemaVersion: 1, name: '', nak: '', pada: '', lagna: '',
      privateNote: 'keep-hidden',
    }],
  ])('keeps exact bytes and uses session memory for an unrecognized %s row', (_label, opaque) => {
    const original = JSON.stringify([
      opaque,
      {
        id: 'guest_supported', schemaVersion: 1, name: 'Supported',
        nak: 'Rohini', pada: 2, lagna: 'Karka',
      },
    ], null, 2);
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, original);
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_session_added'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_supported', name: 'Supported' }],
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);

    store.update('guest_supported', { name: 'Session edit' });
    const added = store.create({ name: 'Session added', nakshatra: 'Hasta' });
    store.reload();
    expect(store.get('guest_supported')?.name).toBe('Session edit');
    expect(store.get(added.id)?.name).toBe('Session added');
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);

    expect(store.remove('guest_supported')).toBe(true);
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);
    store.clear();
    expect(store.getSnapshot().profiles).toEqual([]);
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);

    const repeatedLoad = createGuestProfileStore(storage, {
      idFactory: ids('guest_still_unused'),
    });
    expect(repeatedLoad.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_supported', name: 'Supported' }],
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);
  });

  test('keeps a visible v1 profile with an additive field byte-for-byte', () => {
    const original = JSON.stringify([{
      id: 'guest_additive', schemaVersion: 1, name: 'Supported',
      nak: 'Rohini', pada: 2, lagna: 'Karka',
      futurePayload: { privateNote: 'keep this' },
    }], null, 2);
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, original);
    const store = createGuestProfileStore(storage);

    expect(store.getSnapshot()).toMatchObject({
      profiles: [{ id: 'guest_additive', name: 'Supported' }],
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);

    store.update('guest_additive', { name: 'Session edit' });
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);
    expect(store.remove('guest_additive')).toBe(true);
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);
    store.clear();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);
  });

  test('keeps an extra valid profile tail byte-for-byte and enforces four visible profiles', () => {
    const rows = Array.from({ length: 5 }, (_, index) => ({
      id: `guest_overflow_${index + 1}`,
      schemaVersion: 1,
      name: `Person ${index + 1}`,
      nak: 'Rohini',
      pada: 2,
      lagna: 'Karka',
    }));
    const original = JSON.stringify(rows, null, 2);
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, original);
    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_session_fifth'),
    });

    expect(store.getSnapshot()).toMatchObject({
      profiles: rows.slice(0, 4).map(row => ({ id: row.id, name: row.name })),
      persistence: 'memory',
      issue: 'unsupported-storage-version',
    });
    expect(store.get('guest_overflow_5')).toBeNull();
    expect(() => store.create({ name: 'Blocked fifth' })).toThrowError(
      expect.objectContaining<Partial<GuestProfileStoreError>>({ code: 'profile-limit' }),
    );
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);

    store.update('guest_overflow_1', { name: 'Session edit' });
    expect(store.remove('guest_overflow_2')).toBe(true);
    const added = store.create({ name: 'Session fifth' });
    store.reload();
    expect(store.get('guest_overflow_1')?.name).toBe('Session edit');
    expect(store.get(added.id)?.name).toBe('Session fifth');
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);

    store.clear();
    expect(store.getSnapshot().profiles).toEqual([]);
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(original);
  });

  test('legacy form edits preserve future schema fields instead of downgrading them', () => {
    const merged = mergeLegacyGuestProfileRow({
      id: 'guest_future', schemaVersion: 2, extra: { future: true },
      name: 'Before', nak: 'Rohini', pada: '', lagna: '',
    }, {
      name: 'After', nak: 'Hasta', pada: '3', lagna: 'Karka',
    });

    expect(merged).toEqual({
      id: 'guest_future', schemaVersion: 2, extra: { future: true },
      name: 'After', nak: 'Hasta', pada: '3', lagna: 'Karka',
    });
  });

  test('whole-array legacy writes retain hidden and future rows across reload', () => {
    const futureBytes = 'future\u0000payload::do-not-rewrite';
    const futureRow = {
      id: 'guest_future', schemaVersion: 2, name: 'Future', nak: 'Rohini',
      extension: { bytes: futureBytes, enabled: true },
    };
    const hiddenLagnaOnly = {
      id: 'guest_hidden', schemaVersion: 1, name: '', nak: '', pada: '',
      lagna: 'Karka', privateNote: 'lagna-only row',
    };
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      { id: 'guest_visible', schemaVersion: 1, name: 'Before', nak: 'Hasta', pada: 3, lagna: '' },
      hiddenLagnaOnly,
      futureRow,
    ]));

    writeLegacyGuestProfileRows(storage, [{
      name: 'After', nak: 'Hasta', pada: '3', lagna: 'Mesha',
    }]);
    const afterEdit = storage.getItem(GUEST_PROFILE_STORAGE_KEY)!;
    expect(JSON.parse(afterEdit)).toEqual([
      { id: 'guest_visible', schemaVersion: 1, name: 'After', nak: 'Hasta', pada: '3', lagna: 'Mesha' },
      hiddenLagnaOnly,
      futureRow,
    ]);
    expect(afterEdit).toContain(JSON.stringify(hiddenLagnaOnly));
    expect(afterEdit).toContain(JSON.stringify(futureRow));

    const store = createGuestProfileStore(storage, {
      idFactory: ids('guest_unused'),
    });
    store.reload();
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(afterEdit);
  });

  test('Gochara compatibility fails closed for a noncanonical legacy lagna', () => {
    expect(canonicalLegacyGuestProfileLagna('Mesha')).toBe('Mesha');
    expect(canonicalLegacyGuestProfileLagna('not-a-rasi')).toBeNull();
    expect(canonicalLegacyGuestProfileLagna(-1)).toBeNull();
  });

  test('falls back to in-memory use when storage reads are denied', () => {
    const denied: ProfileStorage = {
      getItem: () => { throw new DOMException('denied', 'SecurityError'); },
      setItem: () => { throw new DOMException('denied', 'SecurityError'); },
    };
    const store = createGuestProfileStore(denied, {
      idFactory: ids('guest_memory'),
    });
    const created = store.create({ name: 'Session only', nakshatra: 'Pushya' });

    expect(store.get(created.id)?.name).toBe('Session only');
    expect(store.getSnapshot()).toMatchObject({
      persistence: 'memory', issue: 'storage-unavailable',
    });
  });

  test('falls back to memory when access to the browser storage property is denied', () => {
    const lazyStorage = browserProfileStorage(() => {
      throw new DOMException('denied', 'SecurityError');
    });

    const store = createGuestProfileStore(lazyStorage, {
      idFactory: ids('guest_property_denied'),
    });
    const created = store.create({ name: 'Session profile' });

    expect(store.get(created.id)?.name).toBe('Session profile');
    expect(store.getSnapshot()).toMatchObject({
      persistence: 'memory', issue: 'storage-unavailable',
    });
  });

  test('keeps the successful in-memory edit when a later write is denied', () => {
    const backing = new Map<string, string>();
    let denyWrites = false;
    const flaky: ProfileStorage = {
      getItem: key => backing.get(key) || null,
      setItem: (key, value) => {
        if (denyWrites) throw new DOMException('full', 'QuotaExceededError');
        backing.set(key, value);
      },
    };
    const store = createGuestProfileStore(flaky, {
      idFactory: ids('guest_flaky'),
    });
    const created = store.create({ name: 'First' });
    denyWrites = true;
    store.update(created.id, { name: 'Still usable' });
    store.reload();

    expect(store.get(created.id)?.name).toBe('Still usable');
    expect(store.getSnapshot()).toMatchObject({
      persistence: 'memory', issue: 'storage-unavailable',
    });
  });

  test('clear notifies when an empty store loses persistence', () => {
    let denyWrites = false;
    const flaky: ProfileStorage = {
      getItem: () => null,
      setItem: () => {
        if (denyWrites) throw new DOMException('full', 'QuotaExceededError');
      },
    };
    const store = createGuestProfileStore(flaky);
    const listener = vi.fn();
    store.subscribe(listener);

    denyWrites = true;
    store.clear();

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenLastCalledWith(expect.objectContaining({
      profiles: [], persistence: 'memory', issue: 'storage-unavailable',
    }));
  });
});
