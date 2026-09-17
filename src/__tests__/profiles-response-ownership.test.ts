// @vitest-environment jsdom
import { beforeEach, describe, expect, test, vi } from 'vitest';
import { createGuestProfileStore, type GuestProfileStore } from '../lib/guest-profile-store';
import type { BirthPlaceCandidate, BirthProfileDerivation } from '../lib/birth-profile-api';
import { initProfilesPanel, type ProfilesPanelController, type ProfilesPanelOptions } from '../panels/profiles';

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

const TEST_ATTRIBUTIONS = [{
  label: '© OpenStreetMap contributors',
  url: 'https://www.openstreetmap.org/copyright',
}];

function calculatedProfile(): BirthProfileDerivation {
  const rashis = [
    'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha',
    'Kanya', 'Tula', 'Vrischika', 'Vrishabha',
  ];
  const planets = [
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
    'Shukra', 'Shani', 'Rahu', 'Ketu',
  ];
  const houses = [10, 11, 12, 1, 2, 3, 4, 5, 11];
  return {
    contractVersion: '1.0',
    engine: {
      name: 'DashaFlow', version: '1.1.0', ayanamsha: 'Lahiri', ephemeris: 'moshier',
    },
    nakshatra: 'Rohini',
    pada: 2,
    janmaRashi: 'Vrishabha',
    lagna: 'Karka',
    lagnaDegree: 12.35,
    planets: rashis.map((rashi, index) => ({
      name: planets[index],
      rashi,
      degree: index === 1 ? 15 : index === 8 ? 7.25 : index + 0.25,
      house: houses[index],
      retrograde: index >= 6,
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
    attributions: TEST_ATTRIBUTIONS,
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


let store: GuestProfileStore;
let controller: ProfilesPanelController;
let navigate: ReturnType<typeof vi.fn<(tool: string) => void>>;

beforeEach(() => {
  document.body.innerHTML = '<main id="profiles-root"></main>';
  const values = new Map<string, string>();
  store = createGuestProfileStore({
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => { values.set(key, value); },
    removeItem: key => { values.delete(key); },
  });
  navigate = vi.fn<(tool: string) => void>();
  controller = initProfilesPanel(store, { navigate, birthCalculationEnabled: true });
});

describe('profile workflow response ownership', () => {
  function pendingCalculation() {
    let resolve!: (result: BirthProfileDerivation) => void;
    const deriveProfile = vi.fn(() => new Promise<BirthProfileDerivation>(done => { resolve = done; }));
    installBirthApi({ deriveProfile });
    return { deriveProfile, finish: () => resolve(calculatedProfile()) };
  }

  async function startCalculation(): Promise<void> {
    controller.openCreate({ returnTo: 'gochara' });
    inputValue('#profile-name', 'Anu');
    inputValue('#profile-birth-date', '1990-05-12');
    inputValue('#profile-birth-time', '14:35');
    await findAndSelectVijayawada();
    buttonNamed('Calculate details').click();
  }

  test('ignores a calculation completed after its birth inputs change', async () => {
    const pending = pendingCalculation();
    await startCalculation();
    inputValue('#profile-birth-time', '14:36');
    pending.finish();
    await Promise.resolve();
    expect(document.querySelector('.profiles-birth-review')).toBeNull();
    expect(buttonNamed('Save calculated profile').disabled).toBe(true);
    expect(store.getSnapshot().profiles).toHaveLength(0);
    expect(pending.deriveProfile).toHaveBeenCalledWith({
      dateOfBirth: '1990-05-12', timeOfBirth: '14:35',
      latitude: VIJAYAWADA.latitude, longitude: VIJAYAWADA.longitude,
      timezone: VIJAYAWADA.timezone,
    });
  });

  test('ignores a calculation completed after cancelling into another journey', async () => {
    const pending = pendingCalculation();
    await startCalculation();
    buttonNamed('Cancel').click();
    const markup = query('#profiles-root').innerHTML;
    pending.finish();
    await Promise.resolve();
    expect(query('#profiles-root').innerHTML).toBe(markup);
    expect(navigate).toHaveBeenCalledWith('gochara');
    expect(store.getSnapshot().profiles).toHaveLength(0);
  });

  test('does not attach an old search response to a replacement form', async () => {
    let finish!: (value: { results: BirthPlaceCandidate[]; attribution: string; attributions: typeof TEST_ATTRIBUTIONS }) => void;
    const searchPlaces = vi.fn(() => new Promise(done => { finish = done; }));
    installBirthApi({ searchPlaces });
    controller.openCreate();
    inputValue('#profile-birth-place', 'Vijayawada');
    buttonNamed('Find place').click();
    chooseManualEntry();
    const markup = query('#profiles-root').innerHTML;
    finish({ results: [VIJAYAWADA], attribution: 'OpenStreetMap contributors', attributions: TEST_ATTRIBUTIONS });
    await Promise.resolve();
    expect(query('#profiles-root').innerHTML).toBe(markup);
    expect(document.querySelector('.profiles-place-results')).toBeNull();
    expect(store.getSnapshot().profiles).toHaveLength(0);
  });
});
