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
  createProfile(trigger: HTMLElement): void;
  editProfile(id: string, trigger: HTMLElement): void;
  manageProfiles(trigger: HTMLElement): void;
}

interface GocharaProfilesController {
  refresh(): void;
  selectProfile(id: string): boolean;
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
    expect(edit?.textContent).toBe('Complete Active');
    edit?.click();
    expect(actions.editProfile).toHaveBeenCalledWith('guest_active', edit);
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
    const create = document.querySelector<HTMLButtonElement>('[data-go-profile-action="create"]');
    create?.click();
    expect(actions.createProfile).toHaveBeenCalledWith(create);

    store.create({ name: 'Ready', nakshatra: 'Rohini' });
    const manage = document.querySelector<HTMLButtonElement>('[data-go-profile-action="manage"]');
    manage?.click();
    expect(actions.manageProfiles).toHaveBeenCalledWith(manage);
  });

  test('makes every disabled incomplete profile reachable through an explicit Complete action', () => {
    writeProfiles(profileStorage, [
      row('guest_no_star', 'No star', { nak: '' }),
      row('guest_no_pada', 'No Padam', { nak: 'Krittika', pada: '' }),
    ]);
    store.reload();

    controller = initGocharaProfiles(store, actions);

    expect(profileOption('guest_no_star').textContent).toBe('No star · Needs Nakshatra');
    expect(profileOption('guest_no_star').disabled).toBe(true);
    expect(profileOption('guest_no_pada').textContent).toBe('No Padam · Needs Padam');
    expect(profileOption('guest_no_pada').disabled).toBe(true);
    const complete = Array.from(
      document.querySelectorAll<HTMLButtonElement>('[data-go-profile-action="edit"]'),
    );
    expect(complete.map(button => button.textContent)).toEqual([
      'Complete No star · Needs Nakshatra',
      'Complete No Padam · Needs Padam',
    ]);
    complete[1].click();
    expect(actions.editProfile).toHaveBeenCalledWith('guest_no_pada', complete[1]);
  });

  test('selectProfile persists and renders an existing Horoscope-ready profile only', () => {
    writeProfiles(profileStorage, [
      row('guest_ready', 'Ready'),
      row('guest_incomplete', 'Incomplete', { nak: '' }),
    ]);
    store.reload();
    controller = initGocharaProfiles(store, actions);

    expect(controller.selectProfile('guest_ready')).toBe(true);
    expect(select().value).toBe('profile:guest_ready');
    expect(selectionStorage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe('profile:guest_ready');
    expect(document.querySelector('.go-profile-context')?.textContent)
      .toContain("Using Ready's saved birth star");
    expect(document.activeElement).toBe(select());

    expect(controller.selectProfile('guest_incomplete')).toBe(false);
    expect(controller.selectProfile('guest_missing')).toBe(false);
    expect(select().value).toBe('profile:guest_ready');
    expect(selectionStorage.getItem(GOCHARA_SELECTION_STORAGE_KEY)).toBe('profile:guest_ready');
  });

  test('selectProfile never changes the independent Muhurtam participant selection', () => {
    const muhurtaKey = 'tc-mu-profile-ids';
    writeProfiles(profileStorage, [row('guest_ready', 'Ready')]);
    store.reload();
    selectionStorage.setItem(muhurtaKey, JSON.stringify(['guest_other']));
    controller = initGocharaProfiles(store, actions);

    expect(controller.selectProfile('guest_ready')).toBe(true);
    expect(selectionStorage.getItem(muhurtaKey)).toBe(JSON.stringify(['guest_other']));
  });

  test('restores focus to the equivalent action after a subscribed rerender', () => {
    writeProfiles(profileStorage, [
      row('guest_ready', 'Ready'),
      row('guest_incomplete', 'Incomplete', { nak: '' }),
    ]);
    store.reload();
    controller = initGocharaProfiles(store, actions);
    const before = document.querySelector<HTMLButtonElement>(
      '[data-go-profile-focus="edit:guest_incomplete"]',
    );
    before?.focus();

    store.update('guest_ready', { name: 'Renamed' });

    const after = document.querySelector<HTMLButtonElement>(
      '[data-go-profile-focus="edit:guest_incomplete"]',
    );
    expect(after).not.toBe(before);
    expect(document.activeElement).toBe(after);
  });
});
