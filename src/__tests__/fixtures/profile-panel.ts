import type { BirthPlaceCandidate, BirthProfileDerivation } from '../../lib/birth-profile-api';

export function query<T extends Element>(selector: string, parent: ParentNode = document): T {
  const node = parent.querySelector<T>(selector);
  if (!node) throw new Error(`Missing test element: ${selector}`);
  return node;
}

export function buttonNamed(name: string): HTMLButtonElement {
  const match = Array.from(document.querySelectorAll<HTMLButtonElement>('button'))
    .find(candidate => candidate.textContent === name);
  if (!match) throw new Error(`Missing test button: ${name}`);
  return match;
}

export function inputValue(selector: string, value: string): void {
  const input = query<HTMLInputElement | HTMLSelectElement>(selector);
  input.value = value;
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
}

export function chooseManualEntry(): void {
  buttonNamed('Enter astrology details manually').click();
}

export const VIJAYAWADA: BirthPlaceCandidate = {
  id: 'osm:123',
  label: 'Vijayawada, Andhra Pradesh, India',
  latitude: 16.5062,
  longitude: 80.648,
  timezone: 'Asia/Kolkata',
};

export const TEST_ATTRIBUTIONS = [{
  label: '© OpenStreetMap contributors',
  url: 'https://www.openstreetmap.org/copyright',
}];

export function calculatedProfile(): BirthProfileDerivation {
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
