import { describe, expect, test, vi } from 'vitest';
import { GUEST_PROFILE_STORAGE_KEY, createGuestProfileStore } from '../lib/guest-profile-store';
import { MUHURTAM_PROFILE_IDS_STORAGE_KEY, MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY } from '../lib/profile-selection';
import { usePanelFixture, type PanelFixture, ids, renderPanelFixture, changeCheckbox, clickAction, chooseManualValues } from './muhurta-profile/fixtures';
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

  test('asks for the source-specific primary role and restores its stable saved ID', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta' });
    localStorage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_alpha","guest_bravo"]',
    );
    const active = initialize();
    const activity = document.querySelector<HTMLSelectElement>('#mu-activity')!;
    activity.value = 'surgery';
    activity.dispatchEvent(new Event('change', { bubbles: true }));

    const role = document.querySelector<HTMLSelectElement>('[data-muhurta-role]')!;
    expect(role).toBeTruthy();
    expect(role.closest('label')?.textContent).toContain('Patient');
    expect(active.getRoleParticipant('surgery')?.id).toBe('guest_alpha');

    role.value = 'guest_bravo';
    role.dispatchEvent(new Event('change', { bubbles: true }));
    expect(active.getRoleParticipant('surgery')?.id).toBe('guest_bravo');
    expect(JSON.parse(
      localStorage.getItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY) || '{}',
    )).toEqual({ version: 1, roles: { surgery: 'guest_bravo' } });

    store.update('guest_bravo', { name: 'Bravo edited' });
    expect(active.getRoleParticipant('surgery')).toMatchObject({
      id: 'guest_bravo', name: 'Bravo edited',
    });

    controller?.destroy();
    controller = null;
    renderPanelFixture();
    const activityAfterReload = document.querySelector<HTMLSelectElement>('#mu-activity')!;
    activityAfterReload.value = 'surgery';
    const restored = initialize();
    expect(restored.getRoleParticipant('surgery')).toMatchObject({
      id: 'guest_bravo', name: 'Bravo edited',
    });

    store.remove('guest_bravo');
    expect(restored.getRoleParticipant('surgery')?.id).toBe('guest_alpha');
    expect(JSON.parse(
      localStorage.getItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY) || '{}',
    )).toEqual({ version: 1, roles: { surgery: 'guest_alpha' } });

    activityAfterReload.value = 'gold';
    activityAfterReload.dispatchEvent(new Event('change', { bubbles: true }));
    expect(document.querySelector('[data-muhurta-role]')).toBeNull();
  });

  test('keeps the Borrowing purpose ephemeral and shows only active guidance', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta' });
    localStorage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_alpha","guest_bravo"]',
    );
    const active = initialize();
    const activity = document.querySelector<HTMLSelectElement>('#mu-activity')!;
    activity.value = 'borrowing_money';
    activity.dispatchEvent(new Event('change', { bubbles: true }));

    const borrower = document.querySelector<HTMLSelectElement>(
      '[data-muhurta-role="primary_borrower"]',
    )!;
    const purpose = document.querySelector<HTMLSelectElement>(
      '[data-borrowing-purpose]',
    )!;
    expect(borrower).toBeTruthy();
    expect(active.getRoleParticipant('borrowing_money')?.id).toBe('guest_alpha');
    expect(active.getBorrowingPurpose()).toBe('other_or_unknown');

    purpose.value = 'business';
    purpose.dispatchEvent(new Event('change', { bubbles: true }));
    expect(active.getBorrowingPurpose()).toBe('business');
    const business = panel.muClassifyManualChecks(
      'borrowing_money',
      panel.muRelevantManualChecks('borrowing_money', 'Budhavaram', 'business'),
    );
    expect(business.chart.join(' ')).toContain('Business purpose');
    expect(business.chart.join(' ')).not.toContain('Quick domestic');
    expect(localStorage.getItem('borrowing-purpose')).toBeNull();
    expect(localStorage.getItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY))
      .not.toContain('business');

    controller?.destroy();
    controller = null;
    renderPanelFixture();
    const activityAfterReload = document.querySelector<HTMLSelectElement>('#mu-activity')!;
    activityAfterReload.value = 'borrowing_money';
    const restored = initialize();
    expect(restored.getBorrowingPurpose()).toBe('other_or_unknown');
  });

  test('labels a missing required Borrowing participant as unresolved', () => {
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    const activity = document.querySelector<HTMLSelectElement>('#mu-activity')!;
    activity.value = 'borrowing_money';
    initialize();

    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'No primary borrower is selected',
    );
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'required primary borrower check otherwise remains unresolved',
    );
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

});
