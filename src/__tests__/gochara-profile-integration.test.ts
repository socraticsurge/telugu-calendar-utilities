// @vitest-environment jsdom

import { afterEach, beforeAll, beforeEach, describe, expect, test, vi } from 'vitest';
import {
  GUEST_PROFILE_STORAGE_KEY,
  createGuestProfileStore,
  type GuestProfileStore,
  type ProfileStorage,
} from '../lib/guest-profile-store';
import { GOCHARA_SELECTION_STORAGE_KEY } from '../lib/profile-selection';

interface GocharaProfileActions {
  createProfile(): void;
  editProfile(id: string): void;
  manageProfiles(): void;
}

interface GocharaProfilesController {
  refresh(): void;
  destroy(): void;
}

let initGocharaProfiles: (
  store: GuestProfileStore,
  actions: GocharaProfileActions,
) => GocharaProfilesController;
let renderGochara: () => void;

beforeAll(async () => {
  // Keep this DOM integration test out of the strict-core TypeScript graph:
  // gochara.ts deliberately remains in the repository's relaxed panel tier.
  const panelPath = '../panels/gochara';
  const panel = await import(/* @vite-ignore */ panelPath);
  initGocharaProfiles = panel.initGocharaProfiles;
  renderGochara = panel.renderGochara;
});

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

interface StoredProfile {
  id: string;
  schemaVersion: 1;
  name: string;
  nak: string;
  pada: number | '';
  lagna: string;
}

function row(
  id: string,
  name: string,
  overrides: Partial<StoredProfile> = {},
): StoredProfile {
  return {
    id,
    schemaVersion: 1,
    name,
    nak: 'Rohini',
    pada: '',
    lagna: '',
    ...overrides,
  };
}

function writeProfiles(storage: MemoryStorage, profiles: StoredProfile[]): void {
  storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify(profiles));
}

function select(): HTMLSelectElement {
  const node = document.getElementById('go-view');
  if (!(node instanceof HTMLSelectElement)) throw new Error('Missing #go-view');
  return node;
}

function profileOption(id: string): HTMLOptionElement {
  const candidate = Array.from(select().options)
    .find(option => option.value === `profile:${id}`);
  if (!candidate) throw new Error(`Missing profile option ${id}`);
  return candidate;
}

let profileStorage: MemoryStorage;
let selectionStorage: MemoryStorage;
let store: GuestProfileStore;
let actions: GocharaProfileActions;
let controller: GocharaProfilesController | null;

beforeEach(() => {
  document.body.innerHTML = `
    <label for="go-view">Horoscope for</label>
    <select id="go-view"></select>
    <div id="go-profile-state" aria-live="polite"></div>
  `;
  selectionStorage = new MemoryStorage();
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: selectionStorage,
  });
  profileStorage = new MemoryStorage();
  store = createGuestProfileStore(profileStorage);
  actions = {
    createProfile: vi.fn(),
    editProfile: vi.fn(),
    manageProfiles: vi.fn(),
  };
  controller = null;
});

afterEach(() => {
  controller?.destroy();
  delete (globalThis as { localStorage?: Storage }).localStorage;
  vi.restoreAllMocks();
});

describe('Daily Horoscope profile selector', () => {
  test.each(['', '0', '6', '11'])('restores and preserves the %j non-profile view', value => {
    selectionStorage.setItem(GOCHARA_SELECTION_STORAGE_KEY, value);

    controller = initGocharaProfiles(store, actions);

    expect(select().value).toBe(value);
    select().dispatchEvent(new Event('change', { bubbles: true }));
    expect(selectionStorage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe(value);
  });

  test('migrates a legacy indexed selection to one stable profile ID', () => {
    writeProfiles(profileStorage, [
      row('guest_first', 'First'),
      row('guest_second', 'Second', { lagna: 'Karka' }),
    ]);
    store.reload();
    selectionStorage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'p1r');

    controller = initGocharaProfiles(store, actions);

    expect(select().value).toBe('profile:guest_second');
    expect(selectionStorage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe('profile:guest_second');
    expect(profileOption('guest_second').textContent)
      .toBe('Second · Vrishabha Rashi + Karka Lagna');
  });

  test('tracks the selected person by ID through reorder and edits via its own store subscription', () => {
    writeProfiles(profileStorage, [
      row('guest_first', 'First'),
      row('guest_stable', 'Before'),
    ]);
    store.reload();
    selectionStorage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'profile:guest_stable');
    controller = initGocharaProfiles(store, actions);

    writeProfiles(profileStorage, [
      row('guest_stable', 'After', { lagna: 'Simha' }),
      row('guest_first', 'First'),
    ]);
    store.reload();

    expect(select().value).toBe('profile:guest_stable');
    expect(profileOption('guest_stable').textContent)
      .toBe('After · Vrishabha Rashi + Simha Lagna');
    expect(document.querySelector('.go-profile-context')?.textContent)
      .toContain("Using After's saved birth star");
  });

  test('falls back safely when the active profile is deleted', () => {
    writeProfiles(profileStorage, [row('guest_delete', 'Delete me')]);
    store.reload();
    selectionStorage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'profile:guest_delete');
    controller = initGocharaProfiles(store, actions);

    store.remove('guest_delete');

    expect(select().value).toBe('');
    expect(selectionStorage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe('');
    expect(document.querySelector('.go-profile-notice')?.textContent)
      .toContain('no longer available');
    expect(document.querySelector<HTMLButtonElement>('[data-go-profile-action="create"]'))
      .not.toBeNull();
  });

  test('disables incomplete profiles and offers the exact edit when an active one becomes incomplete', () => {
    writeProfiles(profileStorage, [
      row('guest_no_star', 'No star', { nak: '' }),
      row('guest_no_pada', 'No Padam', { nak: 'Krittika', pada: '' }),
      row('guest_active', 'Active'),
    ]);
    store.reload();
    selectionStorage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'profile:guest_active');
    controller = initGocharaProfiles(store, actions);

    expect(profileOption('guest_no_star')).toMatchObject({
      disabled: true,
      textContent: 'No star · Needs Nakshatra',
    });
    expect(profileOption('guest_no_pada')).toMatchObject({
      disabled: true,
      textContent: 'No Padam · Needs Padam',
    });

    store.update('guest_active', { nakshatra: 'Krittika', pada: null });

    expect(select().value).toBe('');
    expect(selectionStorage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe('');
    expect(document.querySelector('.go-profile-notice')?.textContent)
      .toContain('Padam is needed');
    const edit = document.querySelector<HTMLButtonElement>('[data-go-profile-action="edit"]');
    expect(edit?.textContent).toBe('Edit Active');
    edit?.click();
    expect(actions.editProfile).toHaveBeenCalledWith('guest_active');
  });

  test('keeps an HTML-like profile name inert while rebuilding options and context', () => {
    const malicious = `"><img src=x onerror=alert('x')>`;
    writeProfiles(profileStorage, [row('guest_inert', malicious)]);
    store.reload();
    selectionStorage.setItem(GOCHARA_SELECTION_STORAGE_KEY, 'profile:guest_inert');

    controller = initGocharaProfiles(store, actions);

    expect(profileOption('guest_inert').textContent)
      .toBe(`${malicious} · Vrishabha Rashi`);
    expect(document.querySelector('img')).toBeNull();
    expect(document.querySelector('.go-profile-context')?.textContent)
      .toContain(malicious);
  });

  test('continues in memory without uncaught errors when selection storage is denied', () => {
    selectionStorage.denyRead = true;
    selectionStorage.denyWrite = true;

    expect(() => {
      controller = initGocharaProfiles(store, actions);
    }).not.toThrow();
    expect(document.querySelector('.go-profile-notice')?.textContent)
      .toContain('preferences are unavailable');

    select().value = '4';
    expect(() => select().dispatchEvent(new Event('change', { bubbles: true })))
      .not.toThrow();
    expect(() => renderGochara()).not.toThrow();
    expect(select().value).toBe('4');
    expect(document.querySelector('.go-profile-notice')?.textContent)
      .toContain('cannot save it');
  });

  test('routes empty and managed states through the supplied journey actions', () => {
    controller = initGocharaProfiles(store, actions);
    document.querySelector<HTMLButtonElement>('[data-go-profile-action="create"]')?.click();
    expect(actions.createProfile).toHaveBeenCalledTimes(1);

    store.create({ name: 'Ready', nakshatra: 'Rohini' });
    document.querySelector<HTMLButtonElement>('[data-go-profile-action="manage"]')?.click();
    expect(actions.manageProfiles).toHaveBeenCalledTimes(1);
  });
});
