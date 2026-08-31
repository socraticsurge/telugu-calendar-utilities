// @vitest-environment jsdom

import { beforeEach, describe, expect, test, vi } from 'vitest';
import {
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_STORAGE_KEY,
  createGuestProfileStore,
  type GuestProfileStore,
  type ProfileStorage,
} from '../lib/guest-profile-store';
import type {
  BirthPlaceCandidate,
  BirthProfileDerivation,
} from '../lib/birth-profile-api';
import { BirthProfileApiError } from '../lib/birth-profile-api';
import {
  initProfilesPanel,
  listenForGuestProfileStorageChanges,
  type ProfilesPanelController,
  type ProfilesPanelOptions,
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

function chooseManualEntry(): void {
  buttonNamed('Enter astrology details manually').click();
}

const VIJAYAWADA: BirthPlaceCandidate = {
  id: 'osm:123',
  label: 'Vijayawada, Andhra Pradesh, India',
  latitude: 16.5062,
  longitude: 80.648,
  timezone: 'Asia/Kolkata',
};

function calculatedProfile(): BirthProfileDerivation {
  const rashis = [
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha',
    'Kanya', 'Tula', 'Vrischika', 'Dhanu',
  ];
  return {
    contractVersion: '1.0',
    engine: {
      name: 'DashaFlow', version: '1.1.0', ayanamsha: 'Lahiri', ephemeris: 'moshier',
    },
    nakshatra: 'Rohini',
    pada: 2,
    janmaRashi: 'Vrishabha',
    lagna: 'Karka',
    lagnaDegree: 12.345,
    planets: rashis.map((rashi, index) => ({
      name: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'][index],
      rashi,
      degree: index + 0.25,
      house: index + 1,
      retrograde: index === 6,
    })),
  };
}

function installBirthApi(options: {
  searchPlaces?: ReturnType<typeof vi.fn>;
  deriveProfile?: ReturnType<typeof vi.fn>;
} = {}): {
  searchPlaces: ReturnType<typeof vi.fn>;
  deriveProfile: ReturnType<typeof vi.fn>;
} {
  controller.destroy();
  const searchPlaces = options.searchPlaces || vi.fn(async () => ({
    results: [VIJAYAWADA],
    attribution: 'OpenStreetMap contributors',
  }));
  const deriveProfile = options.deriveProfile || vi.fn(async () => calculatedProfile());
  controller = initProfilesPanel(store, {
    navigate,
    searchPlaces: searchPlaces as NonNullable<ProfilesPanelOptions['searchPlaces']>,
    deriveProfile: deriveProfile as NonNullable<ProfilesPanelOptions['deriveProfile']>,
  });
  return { searchPlaces, deriveProfile };
}

async function findAndSelectVijayawada(): Promise<void> {
  inputValue('#profile-birth-place', 'Vijayawada');
  buttonNamed('Find place').click();
  await vi.waitFor(() => {
    expect(document.querySelectorAll('.profiles-place-results__choice')).toHaveLength(1);
  });
  query<HTMLButtonElement>('.profiles-place-results__choice').click();
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
    chooseManualEntry();
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

    query<HTMLButtonElement>('button[aria-label="Edit Anu"]').click();
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
    expect(create.classList.contains('profiles-button--secondary')).toBe(true);
    expect(create.classList.contains('profiles-button--primary')).toBe(false);
    expect(create.getAttribute('aria-describedby')).toBe('profiles-limit-message');
    expect(query('#profiles-limit-message').textContent).toContain('up to 4 profiles');
  });
});

describe('birth-details profile journey', () => {
  test('defaults to manual entry when public birth calculation is disabled', () => {
    controller.destroy();
    controller = initProfilesPanel(store, {
      navigate,
      birthCalculationEnabled: false,
    });

    buttonNamed('Create profile').click();

    expect(query('.profiles-title').textContent).toBe('Create profile manually');
    expect(document.querySelector('#profile-birth-date')).toBeNull();
    expect(document.body.textContent).toContain(
      'Birth-detail calculation is not active in this public build',
    );
    expect(document.body.textContent).not.toContain('Use birth details');
    expect(query<HTMLSelectElement>('#profile-nakshatra')).toBeTruthy();
  });

  test('makes birth details the default and calculates a reviewable, local profile', async () => {
    const { searchPlaces, deriveProfile } = installBirthApi();
    buttonNamed('Create profile').click();

    expect(query('.profiles-title').textContent).toBe('Create profile from birth details');
    expect(buttonNamed('Use birth details').getAttribute('aria-pressed')).toBe('true');
    expect(document.body.textContent).toContain('Your name always stays in this browser');
    inputValue('#profile-name', 'Anu');
    inputValue('#profile-birth-date', '1990-05-12');
    inputValue('#profile-birth-time', '14:35');
    await findAndSelectVijayawada();

    expect(searchPlaces).toHaveBeenCalledWith('Vijayawada');
    expect(store.getSnapshot().profiles).toHaveLength(0);
    buttonNamed('Calculate details').click();
    await vi.waitFor(() => {
      expect(buttonNamed('Save calculated profile').disabled).toBe(false);
    });

    expect(deriveProfile).toHaveBeenCalledWith({
      dateOfBirth: '1990-05-12',
      timeOfBirth: '14:35',
      latitude: 16.5062,
      longitude: 80.648,
      timezone: 'Asia/Kolkata',
    });
    expect(JSON.stringify(deriveProfile.mock.calls[0][0])).not.toContain('Anu');
    expect(query('.profiles-birth-facts').textContent).toContain('NakshatraRohini');
    expect(query('.profiles-birth-facts').textContent).toContain('Janma RashiVrishabha');
    expect(document.querySelectorAll('.profiles-chart__cell')).toHaveLength(12);
    expect(document.querySelectorAll('.profiles-chart-table tbody tr')).toHaveLength(9);
    expect(query('.profiles-birth-review__method').textContent).toContain('Lahiri ayanamsha');
    expect(query<HTMLAnchorElement>('.profiles-birth-review__reference').href).toBe(
      'http://localhost:3000/docs/reference/53-birth-profile-calculation',
    );
    expect(store.getSnapshot().profiles).toHaveLength(0);

    submit();
    expect(store.getSnapshot().profiles[0]).toMatchObject({
      source: 'birth-details',
      name: 'Anu',
      nakshatra: 'Rohini',
      pada: 2,
      janmaRasi: 'Vrishabha',
      lagna: 'Karka',
      birthDetails: {
        placeLabel: 'Vijayawada, Andhra Pradesh, India',
        timezone: 'Asia/Kolkata',
      },
      calculation: { engine: { name: 'DashaFlow', ephemeris: 'moshier' } },
    });
    expect(query('.profiles-roster__source').textContent).toBe('Calculated from birth details');
    expect(storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toContain('Vijayawada');
  });

  test('invalidates a reviewed calculation whenever a calculation input changes', async () => {
    installBirthApi();
    controller.openCreate();
    inputValue('#profile-name', 'Anu');
    inputValue('#profile-birth-date', '1990-05-12');
    inputValue('#profile-birth-time', '14:35');
    await findAndSelectVijayawada();
    buttonNamed('Calculate details').click();
    await vi.waitFor(() => expect(document.querySelector('.profiles-birth-review')).not.toBeNull());

    inputValue('#profile-birth-date', '1990-05-13');

    expect(document.querySelector('.profiles-birth-review')).toBeNull();
    expect(buttonNamed('Save calculated profile').disabled).toBe(true);
    expect(query('#profile-save-help').textContent).toContain('Calculate and review');
  });

  test('offers manual entry when exact birth time is unknown', () => {
    installBirthApi();
    controller.openCreate({ returnTo: 'tarabalam', requiredFor: 'muhurta' });

    buttonNamed('Enter known astrology details instead').click();

    expect(query('.profiles-title').textContent).toBe('Create profile manually');
    expect(query<HTMLSelectElement>('#profile-nakshatra')).toBeTruthy();
    expect(query('.profiles-form__intro').textContent).toContain('Padam and Lagna are optional');
  });

  test('shows a retryable place-search error without discarding entered birth details', async () => {
    let attempt = 0;
    const searchPlaces = vi.fn(async () => {
      attempt += 1;
      if (attempt === 1) {
        throw new BirthProfileApiError(
          'network',
          'The calculation service is unavailable. Check your connection and try again.',
        );
      }
      return { results: [VIJAYAWADA], attribution: 'OpenStreetMap contributors' };
    });
    installBirthApi({ searchPlaces });
    controller.openCreate();
    inputValue('#profile-name', 'Anu');
    inputValue('#profile-birth-date', '1990-05-12');
    inputValue('#profile-birth-time', '14:35');
    inputValue('#profile-birth-place', 'Vijayawada');

    buttonNamed('Find place').click();
    await vi.waitFor(() => expect(query('#profile-birth-place-error').textContent).toContain('unavailable'));
    expect(query<HTMLInputElement>('#profile-birth-date').value).toBe('1990-05-12');
    expect(query<HTMLInputElement>('#profile-birth-time').value).toBe('14:35');

    buttonNamed('Find place').click();
    await vi.waitFor(() => {
      expect(document.querySelectorAll('.profiles-place-results__choice')).toHaveLength(1);
    });
    expect(searchPlaces).toHaveBeenCalledTimes(2);
  });
});

describe('saved profile detail view', () => {
  test('keeps a saved calculated profile viewable but not editable while calculation is disabled', () => {
    const result = calculatedProfile();
    store.create({
      source: 'birth-details',
      name: 'Anu',
      nakshatra: result.nakshatra,
      pada: result.pada,
      janmaRasi: result.janmaRashi,
      lagna: result.lagna,
      birthDetails: {
        dateOfBirth: '1990-05-12',
        timeOfBirth: '14:35',
        placeLabel: VIJAYAWADA.label,
        latitude: VIJAYAWADA.latitude,
        longitude: VIJAYAWADA.longitude,
        timezone: VIJAYAWADA.timezone,
      },
      natalChart: { lagnaDegree: result.lagnaDegree, planets: result.planets },
      calculation: { contractVersion: result.contractVersion, engine: result.engine },
    });
    controller.destroy();
    controller = initProfilesPanel(store, {
      navigate,
      birthCalculationEnabled: false,
    });

    expect(query<HTMLButtonElement>('button[aria-label="Edit Anu"]').disabled).toBe(true);
    query<HTMLButtonElement>('button[aria-label="View Anu"]').click();

    expect(query<HTMLButtonElement>('[data-action="edit-profile"]').disabled).toBe(true);
    expect(query('[role="img"][aria-label*="D1 Rashi chart"]')).toBeTruthy();
    expect(document.body.textContent).toContain('Your saved calculation remains');
    expect(store.getSnapshot().profiles[0].source).toBe('birth-details');
  });

  test('opens a calculated profile without recalculating or mutating browser storage', () => {
    const { searchPlaces, deriveProfile } = installBirthApi();
    const result = calculatedProfile();
    store.create({
      source: 'birth-details',
      name: 'Anu',
      nakshatra: result.nakshatra,
      pada: result.pada,
      janmaRasi: result.janmaRashi,
      lagna: result.lagna,
      birthDetails: {
        dateOfBirth: '1990-05-12',
        timeOfBirth: '14:35',
        placeLabel: VIJAYAWADA.label,
        latitude: VIJAYAWADA.latitude,
        longitude: VIJAYAWADA.longitude,
        timezone: VIJAYAWADA.timezone,
      },
      natalChart: {
        lagnaDegree: result.lagnaDegree,
        planets: result.planets,
      },
      calculation: {
        contractVersion: result.contractVersion,
        engine: result.engine,
      },
    });
    controller.render();
    const expectedSnapshot = store.getSnapshot();
    const expectedStorage = new Map(storage.values);
    const setItem = vi.spyOn(storage, 'setItem');
    setItem.mockClear();

    const view = query<HTMLButtonElement>('button[aria-label="View Anu"]');
    view.focus();
    view.click();

    expect(query<HTMLHeadingElement>('h1').textContent).toBe('Anu');
    expect(document.activeElement).toBe(query('#profiles-title'));
    expect(document.body.textContent).toContain('Vijayawada, Andhra Pradesh, India');
    expect(document.body.textContent).toContain('Asia/Kolkata');
    expect(document.body.textContent).toContain('Rohini');
    expect(document.body.textContent).toContain('Vrishabha');
    expect(document.body.textContent).toContain('Karka');
    expect(query('[role="img"][aria-label*="D1 Rashi chart"]')).toBeTruthy();
    expect(query<HTMLTableElement>('table').caption?.textContent).toBe(
      'Planet positions in the D1 Rashi chart',
    );
    expect(document.querySelectorAll('tbody tr')).toHaveLength(9);
    expect(document.body.textContent).toContain('DashaFlow 1.1.0');
    expect(document.body.textContent).toContain('Lahiri ayanamsha');
    expect(document.body.textContent).toContain('moshier ephemeris');
    expect(document.body.textContent).toContain('contract 1.0');
    expect(query<HTMLAnchorElement>('a').textContent).toBe(
      'How this is calculated and verified',
    );
    expect(query<HTMLAnchorElement>('a').getAttribute('href')).toBe(
      '/docs/reference/53-birth-profile-calculation',
    );
    expect(searchPlaces).not.toHaveBeenCalled();
    expect(deriveProfile).not.toHaveBeenCalled();
    expect(setItem).not.toHaveBeenCalled();
    expect(store.getSnapshot()).toEqual(expectedSnapshot);
    expect(storage.values).toEqual(expectedStorage);
  });

  test('returns focus to the same roster action and opens editing from the detail view', () => {
    store.create({ name: 'Anu', nakshatra: 'Rohini', lagna: 'Karka' });
    controller.render();
    const view = query<HTMLButtonElement>('button[aria-label="View Anu"]');
    view.focus();
    view.click();

    buttonNamed('Back to profiles').click();

    const replacement = query<HTMLButtonElement>('button[aria-label="View Anu"]');
    expect(document.activeElement).toBe(replacement);
    replacement.click();
    buttonNamed('Edit profile').click();
    expect(query<HTMLInputElement>('#profile-name').value).toBe('Anu');
    expect(document.activeElement).toBe(query('#profile-name'));
  });

  test('converts a calculated profile to manual without retaining birth provenance', () => {
    installBirthApi();
    const result = calculatedProfile();
    const profile = store.create({
      source: 'birth-details',
      name: 'Anu',
      nakshatra: result.nakshatra,
      pada: result.pada,
      janmaRasi: result.janmaRashi,
      lagna: result.lagna,
      birthDetails: {
        dateOfBirth: '1990-05-12',
        timeOfBirth: '14:35',
        placeLabel: VIJAYAWADA.label,
        latitude: VIJAYAWADA.latitude,
        longitude: VIJAYAWADA.longitude,
        timezone: VIJAYAWADA.timezone,
      },
      natalChart: { lagnaDegree: result.lagnaDegree, planets: result.planets },
      calculation: { contractVersion: result.contractVersion, engine: result.engine },
    });
    controller.render();

    controller.openEdit(profile.id);
    buttonNamed('Enter astrology details manually').click();
    inputValue('#profile-name', 'Manual Anu');
    submit();

    expect(store.get(profile.id)).toMatchObject({
      source: 'manual',
      name: 'Manual Anu',
      birthDetails: null,
      natalChart: null,
      calculation: null,
    });
    const extensions = JSON.parse(
      storage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) || '{}',
    ) as { profiles?: Record<string, unknown> };
    expect(extensions.profiles).not.toHaveProperty(profile.id);
  });

  test('shows only known facts for a manual profile and does not fabricate a chart or provenance', () => {
    store.create({ name: 'Manual Meera', nakshatra: 'Krittika', lagna: 'Tula' });
    controller.render();

    query<HTMLButtonElement>('button[aria-label="View Manual Meera"]').click();

    expect(query<HTMLHeadingElement>('h1').textContent).toBe('Manual Meera');
    expect(document.body.textContent).toContain('Krittika');
    expect(document.body.textContent).toContain('Tula');
    expect(document.body.textContent).toContain('Muhurtam');
    expect(document.body.textContent).toContain('Daily Horoscope');
    expect(document.body.textContent).toContain(
      'Natal chart and calculation details are available only for profiles calculated from birth details.',
    );
    expect(document.querySelector('[role="img"][aria-label*="D1 Rashi chart"]')).toBeNull();
    expect(document.querySelector('table')).toBeNull();
    expect(document.body.textContent).not.toContain('DashaFlow');
    expect(Array.from(document.querySelectorAll('a')).some(link =>
      link.textContent === 'How this is calculated and verified')).toBe(false);
  });

  test('offers ready profiles direct Daily Horoscope and Muhurtam actions', () => {
    const onViewDailyHoroscope = vi.fn<(profileId: string) => void>();
    const onFindMuhurtam = vi.fn<(profileId: string) => void>();
    controller.destroy();
    controller = initProfilesPanel(store, {
      navigate,
      onViewDailyHoroscope,
      onFindMuhurtam,
    });
    const profile = store.create({
      name: 'Anu',
      nakshatra: 'Rohini',
      pada: 2,
    });

    query<HTMLButtonElement>('button[aria-label="View Anu"]').click();
    buttonNamed('View Daily Horoscope').click();
    buttonNamed('Find Muhurtam').click();

    expect(onViewDailyHoroscope).toHaveBeenCalledOnce();
    expect(onViewDailyHoroscope).toHaveBeenCalledWith(profile.id);
    expect(onFindMuhurtam).toHaveBeenCalledOnce();
    expect(onFindMuhurtam).toHaveBeenCalledWith(profile.id);
    expect(navigate).not.toHaveBeenCalled();
  });

  test('shows only journeys supported by the profile readiness state', () => {
    store.create({ name: 'Name only' });
    store.create({ name: 'Muhurtam only', nakshatra: 'Krittika' });
    controller.render();

    query<HTMLButtonElement>('button[aria-label="View Name only"]').click();
    expect(document.body.textContent).not.toContain('View Daily Horoscope');
    expect(document.body.textContent).not.toContain('Find Muhurtam');

    buttonNamed('Back to profiles').click();
    query<HTMLButtonElement>('button[aria-label="View Muhurtam only"]').click();
    expect(document.body.textContent).not.toContain('View Daily Horoscope');
    expect(buttonNamed('Find Muhurtam')).toBeTruthy();
  });

  test('gives every saved profile an accessible View action', () => {
    store.create({ name: 'Anu' });
    store.create({ name: 'Bala' });
    controller.render();

    expect(query<HTMLButtonElement>('button[aria-label="View Anu"]').textContent).toBe('View');
    expect(query<HTMLButtonElement>('button[aria-label="View Bala"]').textContent).toBe('View');
  });

  test('refreshes an open detail after a store update without losing action focus', () => {
    const profile = store.create({ name: 'Anu', nakshatra: 'Rohini' });
    controller.render();
    query<HTMLButtonElement>('button[aria-label="View Anu"]').click();
    const edit = buttonNamed('Edit profile');
    edit.focus();

    store.update(profile.id, { name: 'Anuradha' });

    expect(query<HTMLHeadingElement>('h1').textContent).toBe('Anuradha');
    expect(document.activeElement).toBe(buttonNamed('Edit profile'));
  });

  test('returns to the roster heading if an open profile is removed', () => {
    const profile = store.create({ name: 'Anu', nakshatra: 'Rohini' });
    controller.render();
    query<HTMLButtonElement>('button[aria-label="View Anu"]').click();

    store.remove(profile.id);

    expect(document.body.textContent).toContain('Save a person once');
    expect(document.activeElement).toBe(query('#profiles-title'));
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
    chooseManualEntry();
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
    const trigger = query<HTMLButtonElement>('button[aria-label="Delete Anu"]');
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

    query<HTMLButtonElement>('button[aria-label="Delete One"]').click();
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
  test('reloads only for guest-profile changes and localStorage clear events', () => {
    const reload = vi.spyOn(store, 'reload');
    const stop = listenForGuestProfileStorageChanges(store, window);

    window.dispatchEvent(new StorageEvent('storage', { key: 'tc-city' }));
    expect(reload).not.toHaveBeenCalled();

    window.dispatchEvent(new StorageEvent('storage', { key: GUEST_PROFILE_STORAGE_KEY }));
    window.dispatchEvent(new StorageEvent('storage', { key: GUEST_BIRTH_PROFILE_STORAGE_KEY }));
    window.dispatchEvent(new StorageEvent('storage', { key: null }));
    expect(reload).toHaveBeenCalledTimes(3);

    stop();
    window.dispatchEvent(new StorageEvent('storage', { key: GUEST_PROFILE_STORAGE_KEY }));
    expect(reload).toHaveBeenCalledTimes(3);
  });

  test('preserves an unsaved edit and focus while an external reload updates the store', () => {
    const original = store.create({ name: 'Original', nakshatra: 'Rohini' });
    controller.openEdit(original.id);
    const name = query<HTMLInputElement>('#profile-name');
    inputValue('#profile-name', 'Unsaved local edit');
    name.focus();

    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      {
        id: original.id, schemaVersion: 1, name: 'Changed in another tab',
        nak: 'Hasta', pada: '', lagna: '',
      },
      {
        id: 'guest_external_2', schemaVersion: 1, name: 'Added elsewhere',
        nak: 'Pushya', pada: '', lagna: '',
      },
    ]));
    store.reload();

    expect(query<HTMLInputElement>('#profile-name')).toBe(name);
    expect(name.value).toBe('Unsaved local edit');
    expect(document.activeElement).toBe(name);
    expect(store.getSnapshot().profiles.map(profile => profile.name)).toEqual([
      'Changed in another tab', 'Added elsewhere',
    ]);

    buttonNamed('Cancel').click();
    expect(document.body.textContent).toContain('Changed in another tab');
    expect(document.body.textContent).toContain('Added elsewhere');
    expect(document.querySelector('form')).toBeNull();
  });

  test('preserves an unsaved create form across external clear, then shows the latest empty store', () => {
    store.create({ name: 'Existing' });
    controller.openCreate();
    const name = query<HTMLInputElement>('#profile-name');
    inputValue('#profile-name', 'Unsaved new person');
    name.focus();
    const stop = listenForGuestProfileStorageChanges(store, window);

    storage.setItem(GUEST_PROFILE_STORAGE_KEY, '[]');
    window.dispatchEvent(new StorageEvent('storage', { key: null }));

    expect(query<HTMLInputElement>('#profile-name')).toBe(name);
    expect(name.value).toBe('Unsaved new person');
    expect(document.activeElement).toBe(name);
    expect(store.getSnapshot().profiles).toHaveLength(0);

    buttonNamed('Cancel').click();
    expect(document.body.textContent).toContain('Save a person once');
    expect(document.body.textContent).not.toContain('Existing');
    stop();
  });

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

  test('explains that unrecognized profile storage stays private and session-only', () => {
    const root = query<HTMLElement>('#profiles-root');
    controller.destroy();
    storage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      {
        id: 'guest_supported', schemaVersion: 1, name: 'Supported',
        nak: 'Rohini', pada: 2, lagna: 'Karka',
      },
      { futureOnly: { keep: true } },
    ]));
    store = createGuestProfileStore(storage, { idFactory: ids() });
    controller = initProfilesPanel(store, { root, navigate });

    const alert = query<HTMLElement>('[role="alert"]');
    expect(alert.textContent).toContain('newer or unrecognized format');
    expect(alert.textContent).toContain('last only for this session');
    expect(alert.textContent).toContain('saved browser data was not overwritten');
  });

  test('returns to the originating journey after contextual save or cancel', () => {
    controller.openCreate({ returnTo: 'tarabalam' });
    buttonNamed('Cancel').click();
    expect(navigate).toHaveBeenLastCalledWith('tarabalam');

    controller.openCreate({ returnTo: 'gochara' });
    chooseManualEntry();
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

  test('returns the exact created profile to the originating journey', () => {
    const onSaved = vi.fn();
    controller.openCreate({ returnTo: 'gochara', onSaved });
    chooseManualEntry();
    inputValue('#profile-name', 'Anu');
    inputValue('#profile-nakshatra', 'Rohini');
    submit();

    const created = store.getSnapshot().profiles[0];
    expect(onSaved).toHaveBeenCalledOnce();
    expect(onSaved).toHaveBeenCalledWith(created);
    expect(onSaved.mock.calls[0][0]).toEqual({
      id: 'guest_panel_1',
      schemaVersion: 1,
      source: 'manual',
      name: 'Anu',
      nakshatra: 'Rohini',
      pada: null,
      lagna: null,
      janmaRasi: 'Vrishabha',
      birthDetails: null,
      natalChart: null,
      calculation: null,
    });
    expect(navigate).toHaveBeenLastCalledWith('gochara');
  });

  test('returns an updated profile without changing its stable ID', () => {
    const original = store.create({ name: 'Anu', nakshatra: 'Rohini' });
    const onSaved = vi.fn();
    controller.openEdit(original.id, { returnTo: 'tarabalam', onSaved });
    inputValue('#profile-name', 'Anuradha');
    submit();

    expect(onSaved).toHaveBeenCalledOnce();
    expect(onSaved.mock.calls[0][0]).toMatchObject({
      id: original.id,
      name: 'Anuradha',
      nakshatra: 'Rohini',
    });
    expect(store.getSnapshot().profiles[0].id).toBe(original.id);
    expect(navigate).toHaveBeenLastCalledWith('tarabalam');
  });

  test('does not report a saved profile when contextual editing is cancelled', () => {
    const onSaved = vi.fn();
    controller.openCreate({ returnTo: 'gochara', onSaved });
    inputValue('#profile-name', 'Discard me');
    buttonNamed('Cancel').click();

    expect(onSaved).not.toHaveBeenCalled();
    expect(store.getSnapshot().profiles).toHaveLength(0);
    expect(navigate).toHaveBeenLastCalledWith('gochara');
  });

  test('restores focus to the originating trigger after contextual navigation', () => {
    const trigger = document.createElement('button');
    trigger.textContent = 'Originating action';
    document.body.prepend(trigger);
    const focus = vi.spyOn(trigger, 'focus');
    navigate.mockImplementation(() => {
      expect(focus).toHaveBeenCalledTimes(navigate.mock.calls.length - 1);
    });

    controller.openCreate({ returnTo: 'gochara', focusTarget: trigger });
    buttonNamed('Cancel').click();
    expect(navigate).toHaveBeenLastCalledWith('gochara');
    expect(focus).toHaveBeenCalledOnce();
    expect(document.activeElement).toBe(trigger);

    controller.openCreate({ returnTo: 'tarabalam', focusTarget: trigger });
    chooseManualEntry();
    inputValue('#profile-name', 'Anu');
    submit();
    expect(navigate).toHaveBeenLastCalledWith('tarabalam');
    expect(focus).toHaveBeenCalledTimes(2);
    expect(document.activeElement).toBe(trigger);
  });

  test('requires the birth details that Daily Horoscope readiness reports missing', () => {
    controller.openCreate({ returnTo: 'gochara', requiredFor: 'horoscope' });
    chooseManualEntry();
    expect(query('.profiles-form__intro').textContent).toContain('Lagna remains optional');
    inputValue('#profile-name', 'Anu');
    submit();

    const nakshatra = query<HTMLSelectElement>('#profile-nakshatra');
    const nakshatraError = query<HTMLElement>('#profile-nakshatra-error');
    expect(nakshatra.getAttribute('aria-invalid')).toBe('true');
    expect(nakshatra.getAttribute('aria-describedby')).toContain(nakshatraError.id);
    expect(nakshatraError.textContent).toContain('Daily Horoscope');
    expect(document.activeElement).toBe(nakshatra);
    expect(store.getSnapshot().profiles).toHaveLength(0);

    inputValue('#profile-nakshatra', 'Krittika');
    submit();

    const pada = query<HTMLSelectElement>('#profile-pada');
    const padaError = query<HTMLElement>('#profile-pada-error');
    expect(pada.getAttribute('aria-invalid')).toBe('true');
    expect(pada.getAttribute('aria-describedby')).toContain(padaError.id);
    expect(padaError.textContent).toContain('Krittika spans two Rashis');
    expect(document.activeElement).toBe(pada);
    expect(store.getSnapshot().profiles).toHaveLength(0);

    inputValue('#profile-pada', '2');
    submit();
    expect(store.getSnapshot().profiles[0]).toMatchObject({
      name: 'Anu', nakshatra: 'Krittika', pada: 2,
    });
    expect(navigate).toHaveBeenLastCalledWith('gochara');
  });

  test('allows Daily Horoscope save without Padam when readiness can derive a Rashi', () => {
    controller.openCreate({ returnTo: 'gochara', requiredFor: 'horoscope' });
    chooseManualEntry();
    inputValue('#profile-name', 'Rohini profile');
    inputValue('#profile-nakshatra', 'Rohini');
    submit();

    expect(store.getSnapshot().profiles[0]).toMatchObject({
      nakshatra: 'Rohini', pada: null,
    });
    expect(navigate).toHaveBeenLastCalledWith('gochara');
  });

  test('requires only Nakshatra for a contextual Muhurtam profile', () => {
    controller.openCreate({ returnTo: 'tarabalam', requiredFor: 'muhurta' });
    chooseManualEntry();
    expect(query('.profiles-form__intro').textContent).toContain('Padam and Lagna are optional');
    inputValue('#profile-name', 'Anu');
    submit();

    const nakshatra = query<HTMLSelectElement>('#profile-nakshatra');
    const error = query<HTMLElement>('#profile-nakshatra-error');
    expect(nakshatra.getAttribute('aria-invalid')).toBe('true');
    expect(error.textContent).toContain('Muhurtam');
    expect(document.activeElement).toBe(nakshatra);

    inputValue('#profile-nakshatra', 'Krittika');
    submit();
    expect(store.getSnapshot().profiles[0]).toMatchObject({
      name: 'Anu', nakshatra: 'Krittika', pada: null,
    });
    expect(navigate).toHaveBeenLastCalledWith('tarabalam');
  });

  test('keeps birth details optional in the normal Profiles destination', () => {
    controller.openCreate();
    chooseManualEntry();
    inputValue('#profile-name', 'Name only');
    submit();

    expect(store.getSnapshot().profiles[0]).toMatchObject({
      name: 'Name only', nakshatra: null, pada: null, lagna: null,
    });
    expect(document.body.textContent).toContain('Needs Nakshatra');
    expect(navigate).not.toHaveBeenCalled();
  });

  test('shows existing profiles and journey readiness before contextual creation', () => {
    const hostileName = '<img src=x onerror=alert(1)>';
    store.create({ name: hostileName });
    store.create({ name: 'Ready person', nakshatra: 'Rohini' });

    controller.openCreate({ returnTo: 'gochara', requiredFor: 'horoscope' });

    const existing = query<HTMLElement>('.profiles-form__existing');
    const form = query<HTMLFormElement>('.profiles-form');
    expect(existing.compareDocumentPosition(form) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(existing.textContent).toContain(hostileName);
    expect(existing.textContent).toContain('Needs Nakshatra');
    expect(existing.textContent).toContain('Ready for Daily Horoscope');
    expect(existing.textContent).toContain('edit that profile instead');
    expect(existing.querySelector('img')).toBeNull();
    expect(existing.querySelector('dialog')).toBeNull();
  });
});
