// @vitest-environment jsdom

import { beforeEach, describe, expect, test, vi } from 'vitest';
import {
  GUEST_PROFILE_STORAGE_KEY,
  createGuestProfileStore,
  type GuestProfileStore,
  type ProfileStorage,
} from '../lib/guest-profile-store';
import {
  initProfilesPanel,
  type ProfilesPanelController,
} from '../panels/profiles';

class MemoryStorage implements ProfileStorage {
  readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) || null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

function ids(): () => string {
  let index = 0;
  return () => `guest_panel_${++index}`;
}

function query<T extends Element>(selector: string, parent: ParentNode = document): T {
  const node = parent.querySelector<T>(selector);
  if (!node) throw new Error(`Missing test element: ${selector}`);
  return node;
}

function buttonNamed(name: string): HTMLButtonElement {
  const match = Array.from(document.querySelectorAll<HTMLButtonElement>('button'))
    .find(candidate => candidate.textContent === name);
  if (!match) throw new Error(`Missing test button: ${name}`);
  return match;
}

function inputValue(selector: string, value: string): void {
  const input = query<HTMLInputElement | HTMLSelectElement>(selector);
  input.value = value;
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
}

function submit(): void {
  query<HTMLFormElement>('form').dispatchEvent(
    new SubmitEvent('submit', { bubbles: true, cancelable: true }),
  );
}

let storage: MemoryStorage;
let store: GuestProfileStore;
let controller: ProfilesPanelController;
let navigate: ReturnType<typeof vi.fn<(tool: string) => void>>;

beforeEach(() => {
  document.body.replaceChildren();
  const root = document.createElement('main');
  root.id = 'profiles-root';
  document.body.append(root);
  storage = new MemoryStorage();
  store = createGuestProfileStore(storage, { idFactory: ids() });
  navigate = vi.fn<(tool: string) => void>();
  controller = initProfilesPanel(store, { navigate });
});

describe('Profiles panel CRUD', () => {
  test('creates and edits a reusable profile through labelled inline forms', () => {
    buttonNamed('Create profile').click();
    expect(document.activeElement).toBe(query('#profile-name'));
    expect(query<HTMLLabelElement>('label[for="profile-name"]').textContent).toBe('Name');
    expect(query<HTMLLabelElement>('label[for="profile-nakshatra"]').textContent).toBe('Nakshatra');

    inputValue('#profile-name', 'Anu');
    inputValue('#profile-nakshatra', 'Rohini');
    inputValue('#profile-lagna', 'Karka');
    submit();

    expect(store.getSnapshot().profiles).toHaveLength(1);
    expect(store.getSnapshot().profiles[0]).toMatchObject({
      name: 'Anu', nakshatra: 'Rohini', lagna: 'Karka',
    });
    expect(query('.profiles-roster__name').textContent).toBe('Anu');
    expect(document.body.textContent).toContain('Ready · Vrishabha Janma Rashi');

    buttonNamed('Edit Anu').click();
    inputValue('#profile-name', 'Anuradha');
    inputValue('#profile-nakshatra', 'Krittika');
    inputValue('#profile-pada', '2');
    submit();

    expect(store.getSnapshot().profiles[0]).toMatchObject({
      name: 'Anuradha', nakshatra: 'Krittika', pada: 2,
    });
    expect(query('.profiles-roster__name').textContent).toBe('Anuradha');
    expect(storage.getItem(GUEST_PROFILE_STORAGE_KEY)).toContain('Anuradha');
  });

  test('requires a name and exposes its validation error accessibly', () => {
    buttonNamed('Create profile').click();
    submit();

    const name = query<HTMLInputElement>('#profile-name');
    const error = query<HTMLElement>('#profile-name-error');
    expect(name.getAttribute('aria-invalid')).toBe('true');
    expect(name.getAttribute('aria-describedby')).toContain(error.id);
    expect(error.hidden).toBe(false);
    expect(error.textContent).toBe('Enter a name for this profile.');
    expect(document.activeElement).toBe(name);
    expect(store.getSnapshot().profiles).toHaveLength(0);
  });

  test('prevents a fifth profile and explains the four-profile limit', () => {
    for (let index = 1; index <= 4; index += 1) {
      store.create({ name: `Person ${index}` });
    }
    controller.render();

    const create = buttonNamed('Create another profile');
    expect(create.disabled).toBe(true);
    expect(create.getAttribute('aria-describedby')).toBe('profiles-limit-message');
    expect(query('#profiles-limit-message').textContent).toContain('up to 4 profiles');
  });
});

describe('readiness and hostile data', () => {
  test('shows why incomplete profiles are not ready for each personalized journey', () => {
    store.create({ name: 'Name only' });
    store.create({ name: 'Star only', nakshatra: 'Krittika' });
    controller.render();

    const rows = document.querySelectorAll<HTMLElement>('.profiles-roster__item');
    expect(rows[0].textContent).toContain('MuhurtamNeeds Nakshatra');
    expect(rows[0].textContent).toContain('Daily HoroscopeNeeds Nakshatra');
    expect(rows[1].textContent).toContain('MuhurtamReady');
    expect(rows[1].textContent).toContain('Daily HoroscopeNeeds Padam');
  });

  test('renders stored HTML payloads as inert text', () => {
    const payload = `"><img src=x onerror=alert('x')>`;
    store.create({ name: payload, nakshatra: 'Hasta' });
    controller.render();

    expect(document.querySelector('img')).toBeNull();
    expect(query('.profiles-roster__name').textContent).toBe(payload);
    expect(document.body.textContent).toContain(payload);
  });

  test('warns without blocking when a name duplicates another profile', () => {
    store.create({ name: 'Anu', nakshatra: 'Rohini' });
    controller.openCreate();
    inputValue('#profile-name', ' anu ');

    const warning = query<HTMLElement>('#profile-name-duplicate');
    expect(warning.hidden).toBe(false);
    expect(warning.getAttribute('role')).toBe('status');
    expect(warning.textContent).toContain('already exists');

    submit();
    expect(store.getSnapshot().profiles).toHaveLength(2);
  });
});

describe('safe destructive actions', () => {
  test('cancels deletion through the native dialog and restores trigger focus', () => {
    store.create({ name: 'Anu' });
    controller.render();
    const trigger = buttonNamed('Delete Anu');
    trigger.focus();
    trigger.click();

    const dialog = query<HTMLDialogElement>('dialog');
    expect(dialog.hasAttribute('open')).toBe(true);
    dialog.dispatchEvent(new Event('cancel', { cancelable: true }));

    expect(store.getSnapshot().profiles).toHaveLength(1);
    expect(document.querySelector('dialog')).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  test('confirms deletion and supports cancelling then confirming clear-all', () => {
    store.create({ name: 'One' });
    store.create({ name: 'Two' });
    controller.render();

    buttonNamed('Delete One').click();
    buttonNamed('Delete profile').click();
    expect(store.getSnapshot().profiles.map(profile => profile.name)).toEqual(['Two']);

    const clearTrigger = buttonNamed('Clear all profiles');
    clearTrigger.focus();
    clearTrigger.click();
    buttonNamed('Cancel').click();
    expect(store.getSnapshot().profiles).toHaveLength(1);
    expect(document.activeElement).toBe(clearTrigger);

    clearTrigger.click();
    query<HTMLButtonElement>('dialog .profiles-button--danger').click();
    expect(store.getSnapshot().profiles).toHaveLength(0);
    expect(document.body.textContent).toContain('Save a person once');
  });
});

describe('storage and contextual journeys', () => {
  test('explains session-only storage failure and malformed-data recovery', () => {
    const root = query<HTMLElement>('#profiles-root');
    controller.destroy();
    const denied: ProfileStorage = {
      getItem: () => { throw new DOMException('denied', 'SecurityError'); },
      setItem: () => { throw new DOMException('denied', 'SecurityError'); },
    };
    const deniedStore = createGuestProfileStore(denied, { idFactory: ids() });
    initProfilesPanel(deniedStore, { root, navigate });
    expect(query<HTMLElement>('[role="alert"]').textContent).toContain('only for this session');

    root.replaceChildren();
    const malformedStorage = new MemoryStorage();
    malformedStorage.setItem(GUEST_PROFILE_STORAGE_KEY, '{broken');
    const malformedStore = createGuestProfileStore(malformedStorage, { idFactory: ids() });
    initProfilesPanel(malformedStore, { root, navigate });
    expect(query<HTMLElement>('[role="alert"]').textContent).toContain('damaged and has been reset');
  });

  test('returns to the originating journey after contextual save or cancel', () => {
    controller.openCreate({ returnTo: 'tarabalam' });
    buttonNamed('Cancel').click();
    expect(navigate).toHaveBeenLastCalledWith('tarabalam');

    controller.openCreate({ returnTo: 'gochara' });
    inputValue('#profile-name', 'Anu');
    inputValue('#profile-nakshatra', 'Rohini');
    submit();
    expect(navigate).toHaveBeenLastCalledWith('gochara');

    const profile = store.getSnapshot().profiles[0];
    controller.openEdit(profile.id, { returnTo: 'tarabalam' });
    inputValue('#profile-name', 'Anuradha');
    submit();
    expect(navigate).toHaveBeenLastCalledWith('tarabalam');
  });
});
