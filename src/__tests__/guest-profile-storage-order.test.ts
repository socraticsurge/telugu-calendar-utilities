import { describe, expect, test } from 'vitest';
import {
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_COMMIT_STORAGE_KEY,
  GUEST_PROFILE_STORAGE_KEY,
  createGuestProfileStore,
  type ProfileStorage,
} from '../lib/guest-profile-store';

const TRANSACTION_KEYS = [
  GUEST_PROFILE_STORAGE_KEY,
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_COMMIT_STORAGE_KEY,
];

class RecordingStorage implements ProfileStorage {
  readonly calls: Array<[string, string]> = [];
  private readonly values = new Map<string, string>();
  private writes = 0;

  constructor(private readonly failWriteAt: number | null = null) {}

  getItem(key: string): string | null {
    this.calls.push(['get', key]);
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.calls.push(['set', key]);
    this.writes += 1;
    if (this.writes === this.failWriteAt) throw new Error('Synthetic write denial');
    this.values.set(key, value);
  }

  removeItem(key: string): void {
    this.calls.push(['remove', key]);
    this.values.delete(key);
  }
}

function createStore(storage: ProfileStorage) {
  let revision = 0;
  return createGuestProfileStore(storage, {
    idFactory: () => 'guest_order_check',
    revisionFactory: () => `revision_order_${++revision}`,
  });
}

describe('profile persistence side-effect ordering', () => {
  test.each([null, 1, 2, 3])('notifies after the transaction stops at write %s', failure => {
    const storage = new RecordingStorage(failure);
    const store = createStore(storage);
    storage.calls.length = 0;
    const observerCalls: Array<Array<[string, string]>> = [];
    store.subscribe(() => observerCalls.push(storage.calls.slice()));

    store.create({ name: 'Synthetic profile', nakshatra: 'Rohini', pada: 2 });

    const expected = TRANSACTION_KEYS.slice(0, failure ?? 3).map(key => ['set', key]);
    expect(storage.calls).toEqual(expected);
    expect(observerCalls).toEqual([expected]);
    expect(store.getSnapshot().profiles[0].name).toBe('Synthetic profile');
    expect(store.getSnapshot().persistence).toBe(failure === null ? 'persistent' : 'memory');
    expect(store.getSnapshot().issue).toBe(failure === null ? null : 'storage-unavailable');

    if (failure !== null) {
      store.reload();
      expect(storage.calls).toEqual(expected);
      expect(observerCalls).toEqual([expected]);
    }
  });

  test('an undefined patch retains a value while an explicit null clears it', () => {
    const store = createStore(new RecordingStorage());
    const saved = store.create({ name: 'Synthetic profile', nakshatra: 'Rohini', pada: 2 });
    const updated = store.update(saved.id, { name: undefined, pada: null });
    expect(updated.name).toBe(saved.name);
    expect(updated.pada).toBeNull();
    expect(updated.nakshatra).toBe(saved.nakshatra);
    expect(updated.id).toBe(saved.id);
  });
});
