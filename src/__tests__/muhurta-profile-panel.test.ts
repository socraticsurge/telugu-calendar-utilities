import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, test, vi, type Mock } from 'vitest';
import {
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_COMMIT_STORAGE_KEY,
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
  selectProfile(id: string): boolean;
}

interface TarabalamPanelModule {
  initTarabalamProfiles(
    store: GuestProfileStore,
    actions: {
      createProfile(trigger: HTMLElement): void;
      editProfile(id: string, trigger: HTMLElement): void;
      manageProfiles(trigger: HTMLElement): void;
    },
  ): ProfilesController;
  tbAddRow(): void;
  tbProfiles(): Participant[];
  tbRenderProfileInputs(): void;
  tbRemoveRow(index: number): void;
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
    <input id="tb-from" value="2026-08-28">
    <input id="tb-to" value="2026-09-04">
    <select id="mu-activity"><option value="wedding" selected>Wedding</option></select>
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

function clickAction(action: string): HTMLButtonElement {
  const button = document.querySelector<HTMLButtonElement>(`button[data-action="${action}"]`);
  if (!button) throw new Error(`Missing action ${action}`);
  button.click();
  return button;
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
let createProfile: Mock<(trigger: HTMLElement) => void>;
let editProfile: Mock<(id: string, trigger: HTMLElement) => void>;
let manageProfiles: Mock<(trigger: HTMLElement) => void>;

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
  createProfile = vi.fn<(trigger: HTMLElement) => void>();
  editProfile = vi.fn<(id: string, trigger: HTMLElement) => void>();
  manageProfiles = vi.fn<(trigger: HTMLElement) => void>();
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
    const incompleteRow = Array.from(
      document.querySelectorAll<HTMLElement>('[data-profile-id]'),
    ).find(row => row.dataset.profileId === 'guest_incomplete');
    expect(incompleteRow?.querySelector<HTMLButtonElement>(
      'button[data-action="edit-profile"]',
    )?.textContent).toBe('Complete profile');

    changeCheckbox('guest_bravo', true);
    changeCheckbox('guest_alpha', false);

    expect(panel.tbProfiles()).toEqual([{
      id: 'guest_bravo', name: 'Bravo', nak: 'Hasta', pada: null,
      rasi: 'Kanya', lagna: 'Karka',
    }]);
    expect(controller?.getSelectedIds()).toEqual(['guest_bravo']);
  });

  test('contextually selects a ready profile without disturbing the current search', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta' });
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '["guest_bravo"]');
    localStorage.setItem('tc-go-view', 'profile:guest_bravo');
    localStorage.setItem('unrelated-preference', 'keep');
    const active = initialize();
    clickAction('add-manual');
    chooseManualValues({ name: 'One-off', nakshatra: 'Revati', pada: '3' });
    const manualId = panel.tbProfiles().find(profile => profile.id.startsWith('manual_'))?.id;
    const profileRowsBefore = profileStorage.getItem(GUEST_PROFILE_STORAGE_KEY);
    const write = vi.spyOn(browserStorage, 'setItem');
    write.mockClear();

    expect(active.selectProfile('guest_alpha')).toBe(true);

    expect(active.getSelectedIds()).toEqual(['guest_bravo', 'guest_alpha']);
    expect(panel.tbProfiles().map(profile => profile.id)).toEqual([
      'guest_bravo',
      'guest_alpha',
      manualId,
    ]);
    expect(write).toHaveBeenCalledOnce();
    expect(write).toHaveBeenCalledWith(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_bravo","guest_alpha"]',
    );
    expect(localStorage.getItem('tc-go-view')).toBe('profile:guest_bravo');
    expect(localStorage.getItem('unrelated-preference')).toBe('keep');
    expect(profileStorage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(profileRowsBefore);
    expect((document.querySelector('#tb-from') as HTMLInputElement).value).toBe('2026-08-28');
    expect((document.querySelector('#tb-to') as HTMLInputElement).value).toBe('2026-09-04');
    expect((document.querySelector('#mu-activity') as HTMLSelectElement).value).toBe('wedding');
  });

  test('refuses missing and incomplete contextual profiles without persisting a choice', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_incomplete'),
    });
    store.create({ name: 'Needs star' });
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    const active = initialize();
    const write = vi.spyOn(browserStorage, 'setItem');
    write.mockClear();

    expect(active.selectProfile('guest_missing')).toBe(false);
    expect(active.selectProfile('guest_incomplete')).toBe(false);

    expect(active.getSelectedIds()).toEqual([]);
    expect(write).not.toHaveBeenCalled();
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'Complete this profile with a birth star',
    );
  });

  test('enforces the aggregate four-person limit during contextual selection', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_one', 'guest_two', 'guest_three', 'guest_four'),
    });
    for (const name of ['One', 'Two', 'Three', 'Four']) {
      store.create({ name, nakshatra: 'Rohini' });
    }
    localStorage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_one","guest_two","guest_three"]',
    );
    const active = initialize();
    clickAction('add-manual');
    const write = vi.spyOn(browserStorage, 'setItem');
    write.mockClear();

    expect(active.selectProfile('guest_four')).toBe(false);

    expect(active.getSelectedIds()).toEqual(['guest_one', 'guest_two', 'guest_three']);
    expect(document.querySelectorAll('[data-manual-id]')).toHaveLength(1);
    expect(localStorage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe(
      '["guest_one","guest_two","guest_three"]',
    );
    expect(write).not.toHaveBeenCalled();
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'Choose up to 4 participants',
    );
  });

  test('restores keyboard focus after saved and manual selection rerenders', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    initialize();

    const checkbox = document.querySelector<HTMLInputElement>(
      'input[data-profile-selection="guest_alpha"]',
    )!;
    checkbox.focus();
    changeCheckbox('guest_alpha', true);
    expect(document.activeElement).toBe(document.querySelector(
      'input[data-profile-selection="guest_alpha"]',
    ));

    clickAction('add-manual');
    for (const [field, value] of [
      ['nakshatra', 'Hasta'],
      ['pada', '2'],
      ['lagna', 'Karka'],
    ] as const) {
      const select = document.querySelector<HTMLSelectElement>(
        `select[data-manual-field="${field}"]`,
      )!;
      select.focus();
      select.value = value;
      select.dispatchEvent(new Event('change', { bubbles: true }));
      expect(document.activeElement).toBe(document.querySelector(
        `select[data-manual-field="${field}"]`,
      ));
    }
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

    const editTrigger = clickAction('edit-profile');
    const createTrigger = clickAction('create-profile');
    const manageTrigger = clickAction('manage-profiles');
    expect(editProfile).toHaveBeenCalledWith('guest_hostile', editTrigger);
    expect(createProfile).toHaveBeenCalledWith(createTrigger);
    expect(manageProfiles).toHaveBeenCalledWith(manageTrigger);
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

  test('fails closed for controller-absent mutations and reserves deletion for reset all', () => {
    const base = JSON.stringify([{
      id: 'guest_fallback_birth', schemaVersion: 1, name: 'Anu',
      nak: 'Rohini', pada: 2, lagna: 'Karka',
    }]);
    const birthBytes = '{"sensitive":{"opaque":"keep-exactly"}}';
    const commitBytes = '{"committed":{"opaque":"keep-exactly"}}';
    localStorage.setItem(GUEST_PROFILE_STORAGE_KEY, base);
    localStorage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);
    localStorage.setItem(GUEST_PROFILE_COMMIT_STORAGE_KEY, commitBytes);
    panel.tbRenderProfileInputs();
    document.querySelector<HTMLInputElement>('#tb-name-0')!.value = 'Edited';
    const originalRows = document.querySelectorAll('.tb-profile-row').length;

    panel.tbSaveProfiles();
    panel.tbAddRow();
    panel.tbRemoveRow(0);
    expect(localStorage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(base);
    expect(localStorage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
    expect(localStorage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBe(commitBytes);
    expect(document.querySelectorAll('.tb-profile-row')).toHaveLength(originalRows);

    const removeItem = vi.spyOn(browserStorage, 'removeItem');
    panel.tbResetProfiles();
    expect(removeItem.mock.calls).toEqual([
      [GUEST_BIRTH_PROFILE_STORAGE_KEY],
      [GUEST_PROFILE_COMMIT_STORAGE_KEY],
      [GUEST_PROFILE_STORAGE_KEY],
    ]);
    expect(localStorage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBeNull();
  });

  test('keeps controller-absent mutation inert when storage reads are denied', () => {
    const setItem = vi.fn();
    const removeItem = vi.fn();
    vi.stubGlobal('localStorage', {
      getItem: () => { throw new DOMException('denied', 'SecurityError'); },
      setItem,
      removeItem,
    });
    const originalRows = document.querySelectorAll('.tb-profile-row').length;

    expect(() => panel.tbSaveProfiles()).not.toThrow();
    expect(() => panel.tbAddRow()).not.toThrow();
    expect(() => panel.tbRemoveRow(0)).not.toThrow();
    expect(setItem).not.toHaveBeenCalled();
    expect(removeItem).not.toHaveBeenCalled();
    expect(document.querySelectorAll('.tb-profile-row')).toHaveLength(originalRows);
  });
});
