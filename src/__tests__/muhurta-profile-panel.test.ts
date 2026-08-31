import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, test, vi, type Mock } from 'vitest';
import {
  GUEST_PROFILE_STORAGE_KEY,
  createGuestProfileStore,
  type GuestProfileStore,
  type ProfileStorage,
} from '../lib/guest-profile-store';
import { MUHURTAM_PROFILE_IDS_STORAGE_KEY } from '../lib/profile-selection';

interface Participant {
  id: string;
  name: string;
  nak: string;
  pada: 1 | 2 | 3 | 4 | null;
  rasi: string | null;
  lagna: string | null;
}

interface ProfilesController {
  destroy(): void;
  getParticipants(): Participant[];
  getSelectedIds(): string[];
}

interface TarabalamPanelModule {
  initTarabalamProfiles(
    store: GuestProfileStore,
    actions: {
      createProfile(): void;
      editProfile(id: string): void;
      manageProfiles(): void;
    },
  ): ProfilesController;
  tbAddRow(): void;
  tbProfiles(): Participant[];
  tbRenderProfileInputs(): void;
  tbSaveProfiles(): void;
  tbResetProfiles(): void;
}

class MemoryStorage implements ProfileStorage {
  readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

class BrowserMemoryStorage extends MemoryStorage implements Storage {
  get length(): number {
    return this.values.size;
  }

  clear(): void {
    this.values.clear();
  }

  key(index: number): string | null {
    return Array.from(this.values.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }
}

class DeniedStorage implements ProfileStorage {
  getItem(): string | null {
    throw new Error('read denied');
  }

  setItem(): void {
    throw new Error('write denied');
  }
}

function ids(...values: string[]): () => string {
  let index = 0;
  return () => values[index++] || `guest_generated_${index}`;
}

function renderPanelFixture(): void {
  document.body.innerHTML = `
    <section class="tb-section">
      <header><button class="tb-reset" onclick="tbResetProfiles()">clear all</button></header>
      <div id="tb-profiles"></div>
      <button id="tb-add-btn" class="tb-add" onclick="tbAddRow()">add</button>
    </section>
    <div id="tb-summary">old summary</div>
    <div id="tb-result">old result</div>
    <div id="mu-context">old context</div>
    <div id="mu-result">old slots</div>
  `;
}

function changeCheckbox(id: string, checked: boolean): void {
  const checkbox = document.querySelector<HTMLInputElement>(
    `input[data-profile-selection="${id}"]`,
  );
  if (!checkbox) throw new Error(`Missing profile checkbox ${id}`);
  checkbox.checked = checked;
  checkbox.dispatchEvent(new Event('change', { bubbles: true }));
}

function clickAction(action: string): void {
  const button = document.querySelector<HTMLButtonElement>(`button[data-action="${action}"]`);
  if (!button) throw new Error(`Missing action ${action}`);
  button.click();
}

function chooseManualValues(values: {
  name?: string;
  nakshatra?: string;
  pada?: string;
  lagna?: string;
}): void {
  let row = document.querySelector<HTMLElement>('[data-manual-id]');
  if (!row) throw new Error('Missing manual participant');
  if (values.name !== undefined) {
    const input = row.querySelector<HTMLInputElement>('input[type="text"]')!;
    input.value = values.name;
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }
  if (values.nakshatra !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[0];
    select.value = values.nakshatra;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
  row = document.querySelector<HTMLElement>('[data-manual-id]')!;
  if (values.pada !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[1];
    select.value = values.pada;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
  row = document.querySelector<HTMLElement>('[data-manual-id]')!;
  if (values.lagna !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[2];
    select.value = values.lagna;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
}

let panel: TarabalamPanelModule;
let controller: ProfilesController | null = null;
let profileStorage: MemoryStorage;
let browserStorage: BrowserMemoryStorage;
let store: GuestProfileStore;
let createProfile: Mock<() => void>;
let editProfile: Mock<(id: string) => void>;
let manageProfiles: Mock<() => void>;

function initialize(): ProfilesController {
  controller = panel.initTarabalamProfiles(
    store,
    { createProfile, editProfile, manageProfiles },
  );
  return controller;
}

beforeAll(async () => {
  // Keep the deliberately relaxed, DOM-heavy legacy panel out of the strict
  // core TypeScript graph while still exercising its real runtime module.
  const panelPath = '../panels/' + 'tarabalam';
  panel = await import(panelPath) as TarabalamPanelModule;
});

beforeEach(() => {
  browserStorage = new BrowserMemoryStorage();
  vi.stubGlobal('localStorage', browserStorage);
  renderPanelFixture();
  profileStorage = new MemoryStorage();
  store = createGuestProfileStore(profileStorage);
  createProfile = vi.fn<() => void>();
  editProfile = vi.fn<(id: string) => void>();
  manageProfiles = vi.fn<() => void>();
});

afterEach(() => {
  controller?.destroy();
  controller = null;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

afterAll(() => {
  vi.unstubAllGlobals();
});

describe('Muhurtam saved-profile participants', () => {
  test('feeds only checked, ready stable-ID adapters to the existing calculation seam', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo', 'guest_incomplete'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta', lagna: 'Karka' });
    store.create({ name: 'Needs star' });
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '["guest_alpha"]');

    initialize();

    expect(panel.tbProfiles()).toEqual([{
      id: 'guest_alpha', name: 'Alpha', nak: 'Rohini', pada: null,
      rasi: 'Vrishabha', lagna: null,
    }]);
    expect(document.querySelector<HTMLInputElement>(
      'input[data-profile-selection="guest_incomplete"]',
    )?.disabled).toBe(true);

    changeCheckbox('guest_bravo', true);
    changeCheckbox('guest_alpha', false);

    expect(panel.tbProfiles()).toEqual([{
      id: 'guest_bravo', name: 'Bravo', nak: 'Hasta', pada: null,
      rasi: 'Kanya', lagna: 'Karka',
    }]);
    expect(controller?.getSelectedIds()).toEqual(['guest_bravo']);
  });

  test('keeps the no-profile path and supports a labelled, session-only person', () => {
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    initialize();

    expect(panel.tbProfiles()).toEqual([]);
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'No participant screening is selected',
    );

    clickAction('add-manual');
    const labels = Array.from(document.querySelectorAll(
      '[data-manual-id] .muhurta-manual-field__label',
    ))
      .map(label => label.textContent);
    expect(labels).toEqual(expect.arrayContaining(['Name', 'Birth star', 'Padam', 'Lagna']));
    chooseManualValues({
      name: 'One-off guest', nakshatra: 'Krittika', pada: '2', lagna: 'Karka',
    });

    expect(panel.tbProfiles()).toEqual([{
      id: expect.stringMatching(/^manual_/),
      name: 'One-off guest', nak: 'Krittika', pada: 2,
      rasi: 'Vrishabha', lagna: 'Karka',
    }]);
    expect(store.getSnapshot().profiles).toEqual([]);
    expect(profileStorage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBeNull();
  });

  test('caps saved and manual participants at four in total', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_one', 'guest_two', 'guest_three', 'guest_four'),
    });
    for (const name of ['One', 'Two', 'Three', 'Four']) {
      store.create({ name, nakshatra: 'Rohini' });
    }
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    initialize();

    clickAction('add-manual');
    chooseManualValues({ nakshatra: 'Hasta' });
    for (const id of ['guest_one', 'guest_two', 'guest_three']) changeCheckbox(id, true);

    expect(panel.tbProfiles()).toHaveLength(4);
    expect(document.querySelector<HTMLInputElement>(
      'input[data-profile-selection="guest_four"]',
    )?.disabled).toBe(true);
    expect(document.querySelector<HTMLButtonElement>(
      'button[data-action="add-manual"]',
    )?.disabled).toBe(true);

    panel.tbAddRow();
    expect(document.querySelectorAll('[data-manual-id]')).toHaveLength(1);
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'Choose up to 4 participants',
    );
  });

  test('survives reorder and edits, then removes only a deleted stable ID', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo', 'guest_charlie'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta' });
    store.create({ name: 'Charlie', nakshatra: 'Revati' });
    localStorage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_alpha","guest_charlie"]',
    );
    initialize();

    store.update('guest_charlie', { name: 'Charlie edited', lagna: 'Simha' });
    const rows = JSON.parse(profileStorage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
    profileStorage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      rows[2], rows[1], rows[0],
    ]));
    store.reload();

    expect(panel.tbProfiles().map(profile => [profile.id, profile.name])).toEqual([
      ['guest_alpha', 'Alpha'],
      ['guest_charlie', 'Charlie edited'],
    ]);

    store.remove('guest_alpha');

    expect(panel.tbProfiles().map(profile => profile.id)).toEqual(['guest_charlie']);
    expect(localStorage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe(
      '["guest_charlie"]',
    );
  });

  test('surfaces storage failure while keeping current-page participants usable', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_available'),
    });
    store.create({ name: 'Available', nakshatra: 'Rohini' });
    vi.stubGlobal('localStorage', {
      getItem: () => { throw new Error('denied'); },
      setItem: () => { throw new Error('denied'); },
    });

    initialize();

    expect(panel.tbProfiles().map(profile => profile.id)).toEqual(['guest_available']);
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'this browser cannot save them',
    );
  });

  test('surfaces unavailable profile storage without crashing the no-profile path', () => {
    store = createGuestProfileStore(new DeniedStorage());
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');

    initialize();

    expect(panel.tbProfiles()).toEqual([]);
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'Browser storage is unavailable',
    );
  });

  test('renders hostile saved names as inert text and wires contextual actions', () => {
    const hostile = `"><img src=x onerror=alert('x')>`;
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_hostile'),
    });
    store.create({ name: hostile, nakshatra: 'Rohini' });

    initialize();

    const root = document.querySelector('#tb-profiles')!;
    expect(root.querySelector('img')).toBeNull();
    expect(root.textContent).toContain(hostile);

    clickAction('edit-profile');
    clickAction('create-profile');
    clickAction('manage-profiles');
    expect(editProfile).toHaveBeenCalledWith('guest_hostile');
    expect(createProfile).toHaveBeenCalledOnce();
    expect(manageProfiles).toHaveBeenCalledOnce();
  });

  test('clear selection never deletes profiles or Gochara preferences', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_keep'),
    });
    store.create({ name: 'Keep me', nakshatra: 'Rohini' });
    localStorage.setItem('tc-go-view', 'profile:guest_keep');
    localStorage.setItem('tc-go-rasi', '4');
    initialize();
    clickAction('add-manual');

    panel.tbResetProfiles();

    expect(store.get('guest_keep')).not.toBeNull();
    expect(localStorage.getItem('tc-go-view')).toBe('profile:guest_keep');
    expect(localStorage.getItem('tc-go-rasi')).toBe('4');
    expect(localStorage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe('[]');
    expect(panel.tbProfiles()).toEqual([]);
    expect(document.querySelectorAll('[data-manual-id]')).toHaveLength(0);
    for (const id of ['tb-summary', 'tb-result', 'mu-context', 'mu-result']) {
      expect(document.getElementById(id)?.textContent).toBe('');
    }
  });

  test('keeps the controller-absent compatibility form additive and inert', () => {
    const hostileName = `Alpha"><img src=x onerror=alert('x')>`;
    const stored = [
      {
        id: 'guest_alpha', schemaVersion: 1, name: hostileName,
        nak: 'Rohini', pada: 2, lagna: 'Karka', futureField: { keep: true },
      },
      {
        id: 'guest_hidden', schemaVersion: 99, name: '', nak: '',
        pada: '', lagna: 'Simha', futureOnly: 'keep-hidden',
      },
      'opaque-future-row',
    ];
    localStorage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify(stored));

    panel.tbRenderProfileInputs();

    expect(document.querySelector('#tb-profiles img')).toBeNull();
    const input = document.querySelector<HTMLInputElement>('#tb-name-0')!;
    expect(input.value).toBe(hostileName);
    input.value = 'Alpha updated';
    panel.tbSaveProfiles();

    const after = JSON.parse(localStorage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
    expect(after[0]).toMatchObject({
      id: 'guest_alpha', schemaVersion: 1, name: 'Alpha updated',
      futureField: { keep: true },
    });
    expect(after[1]).toEqual(stored[1]);
    expect(after[2]).toBe('opaque-future-row');
    expect(panel.tbProfiles()).toEqual([{
      id: 'guest_alpha', name: 'Alpha updated', nak: 'Rohini', pada: 2,
      rasi: 'Vrishabha', lagna: 'Karka',
    }]);
  });
});
