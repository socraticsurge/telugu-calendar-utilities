import { NAKSHATRA_NAMES, RASI_NAMES, rasiFromStar } from '../data/rasis';

export const BIRTH_PROFILE_CONTRACT_VERSION = '1.0' as const;
export const BIRTH_PROFILE_ENGINE_NAME = 'DashaFlow' as const;
export const BIRTH_PROFILE_AYANAMSHA = 'Lahiri' as const;
export const BIRTH_CHART_PLANET_NAMES = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;

const ROUNDED_DEGREE_HALF_STEP = 0.005;
const ROUNDED_OPPOSITION_TOLERANCE = ROUNDED_DEGREE_HALF_STEP * 2;
const ANGLE_EPSILON = 1e-9;
const HUNDREDTH_ALIGNMENT_EPSILON = 1e-9;

export interface BirthChartPlanet {
  name: string;
  rashi: string;
  degree: number;
  house: number;
  retrograde: boolean;
}

export interface BirthProfileEngine {
  name: string;
  version: string;
  ayanamsha: string;
  ephemeris: 'swiss' | 'moshier' | 'unknown';
}

export type BirthPada = 1 | 2 | 3 | 4;

export function isRashi(value: string | null): value is string {
  return value !== null && RASI_NAMES.includes(value);
}

export function isNakshatra(value: string | null): value is string {
  return value !== null && NAKSHATRA_NAMES.includes(value);
}

export function isPada(value: number | null): value is BirthPada {
  return value !== null && [1, 2, 3, 4].includes(value);
}

export function isChartDegree(value: number | null): value is number {
  return value !== null && isContractRoundedDegree(value);
}

export function isChartHouse(value: number | null): value is number {
  return value !== null && Number.isInteger(value) && value >= 1 && value <= 12;
}

export function isBirthEphemeris(value: string | null): value is BirthProfileEngine['ephemeris'] {
  return value !== null && ['swiss', 'moshier', 'unknown'].includes(value);
}

/** Accept hundredth-degree values, including the next representable value below 30. */
export function isContractRoundedDegree(degree: number): boolean {
  return Number.isFinite(degree)
    && degree >= 0
    && degree < 30
    && Math.abs(degree * 100 - Math.round(degree * 100))
      <= HUNDREDTH_ALIGNMENT_EPSILON;
}

/**
 * Validate the Moon facts that bind the derived birth fields to the chart.
 * DashaFlow returns sign-local degrees rounded to two decimal places.  The
 * +/-0.005 degree interval deliberately accepts either side of a rounded
 * Nakshatra/Padam boundary instead of inventing precision the response lacks.
 */
export function roundedMoonMatchesBirthFacts(
  nakshatra: string,
  pada: BirthPada,
  janmaRashi: string,
  moon: BirthChartPlanet,
): boolean {
  const nakshatraIndex = NAKSHATRA_NAMES.indexOf(nakshatra);
  const rashiIndex = RASI_NAMES.indexOf(janmaRashi);
  if (
    !moonIdentifiesBirthFacts(nakshatra, pada, janmaRashi, moon)
  ) return false;

  const padaWidth = 360 / (NAKSHATRA_NAMES.length * 4);
  const padaIndex = nakshatraIndex * 4 + pada - 1;
  const padaStart = padaIndex * padaWidth;
  const padaEnd = (padaIndex + 1) * padaWidth;
  const rashiStart = rashiIndex * 30;
  const possibleStart = rashiStart + Math.max(0, moon.degree - ROUNDED_DEGREE_HALF_STEP);
  const possibleEnd = rashiStart + Math.min(30, moon.degree + ROUNDED_DEGREE_HALF_STEP);

  return possibleStart <= padaEnd + ANGLE_EPSILON
    && possibleEnd >= padaStart - ANGLE_EPSILON;
}

function moonIdentifiesBirthFacts(
  nakshatra: string, pada: BirthPada, janmaRashi: string, moon: BirthChartPlanet,
): boolean {
  if (!NAKSHATRA_NAMES.includes(nakshatra) || !isRashi(janmaRashi)) return false;
  if (moon.name !== 'Chandra' || moon.rashi !== janmaRashi) return false;
  return rasiFromStar(nakshatra, pada) === janmaRashi;
}

/** The contract uses Whole Sign houses, with the Lagna sign as house one. */
export function wholeSignHousesMatch(
  lagna: string,
  planets: readonly BirthChartPlanet[],
): boolean {
  const lagnaIndex = RASI_NAMES.indexOf(lagna);
  if (lagnaIndex < 0 || planets.length !== BIRTH_CHART_PLANET_NAMES.length) return false;
  return planets.every(planet => {
    const rashiIndex = RASI_NAMES.indexOf(planet.rashi);
    return rashiIndex >= 0
      && planet.house === ((rashiIndex - lagnaIndex + RASI_NAMES.length) % RASI_NAMES.length) + 1;
  });
}

/** Validate contract-fixed motion flags and the derived Ketu opposition. */
export function fixedGrahaFactsMatch(planets: readonly BirthChartPlanet[]): boolean {
  if (planets.length !== BIRTH_CHART_PLANET_NAMES.length) return false;
  const [surya, chandra, , , , , , rahu, ketu] = planets;
  if (
    surya.retrograde
    || chandra.retrograde
    || !rahu.retrograde
    || !ketu.retrograde
  ) return false;

  const rahuRashiIndex = RASI_NAMES.indexOf(rahu.rashi);
  const ketuRashiIndex = RASI_NAMES.indexOf(ketu.rashi);
  if (rahuRashiIndex < 0 || ketuRashiIndex < 0) return false;
  const rahuLongitude = rahuRashiIndex * 30 + rahu.degree;
  const ketuLongitude = ketuRashiIndex * 30 + ketu.degree;
  const separation = (ketuLongitude - rahuLongitude + 360) % 360;
  return Math.abs(separation - 180)
    <= ROUNDED_OPPOSITION_TOLERANCE + ANGLE_EPSILON;
}
