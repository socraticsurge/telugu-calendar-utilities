import { beforeEach, describe, expect, test, vi } from 'vitest';
import {
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
}

let storage: MemoryStorage;

function rawProfiles(): unknown[] {
  return JSON.parse(storage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
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
        name: 'Vinay',
        nakshatra: 'Krittika',
        pada: 2,
        lagna: 'Mesha',
      },
      {
        id: 'guest_profile_2',
        schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
        name: 'Name only',
        nakshatra: null,
        pada: null,
        lagna: null,
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
