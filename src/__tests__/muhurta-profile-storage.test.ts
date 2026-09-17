import { describe, expect, test, vi } from 'vitest';
import { GUEST_BIRTH_PROFILE_STORAGE_KEY, GUEST_PROFILE_COMMIT_STORAGE_KEY, GUEST_PROFILE_STORAGE_KEY, createGuestProfileStore } from '../lib/guest-profile-store';
import { MUHURTAM_PROFILE_IDS_STORAGE_KEY } from '../lib/profile-selection';
import { usePanelFixture, type PanelFixture, DeniedStorage, ids, clickAction } from './muhurta-profile/fixtures';
import type { ProfilesController } from './muhurta-profile/types';

let panel: PanelFixture['panel'];
let profileStorage: PanelFixture['profileStorage'];
let browserStorage: PanelFixture['browserStorage'];
let store: PanelFixture['store'];
let createProfile: PanelFixture['createProfile'];
let editProfile: PanelFixture['editProfile'];
let manageProfiles: PanelFixture['manageProfiles'];
let controller: ProfilesController | null = null;

function initialize(): ProfilesController {
  controller = panel.initTarabalamProfiles(
    store,
    { createProfile, editProfile, manageProfiles },
  );
  return controller;
}

usePanelFixture(fixture => {
  ({ panel, profileStorage, browserStorage, store, createProfile, editProfile, manageProfiles } = fixture);
}, () => {
  controller?.destroy();
  controller = null;
});

describe('Muhurtam storage failure and legacy compatibility', () => {
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
