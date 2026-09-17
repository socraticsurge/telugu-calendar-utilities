import { RASI_NAMES } from '../../data/rasis';
import {
  BIRTH_CHART_PLANET_NAMES,
  BIRTH_PROFILE_AYANAMSHA,
  BIRTH_PROFILE_CONTRACT_VERSION,
  BIRTH_PROFILE_ENGINE_NAME,
  isContractRoundedDegree,
  type BirthChartPlanet,
} from '../chart-contracts';
import { type GuestBirthDetails, type GuestNatalChart, type GuestProfileCalculation } from './types';
import {
  exactCanonical,
  exactText,
  finite,
  isoDate,
  isoTime,
  text,
  isRecord,
  withinRange,
} from './values';


export function normalizeBirthDetails(value: unknown): GuestBirthDetails | null {
  if (!isRecord(value)) return null;
  const record = value as Record<string, unknown>;
  const dateOfBirth = isoDate(record.dateOfBirth);
  const timeOfBirth = isoTime(record.timeOfBirth);
  const placeLabel = text(record.placeLabel, 240);
  const latitude = finite(record.latitude);
  const longitude = finite(record.longitude);
  const timezone = text(record.timezone, 80);
  if (!dateOfBirth || !timeOfBirth || !placeLabel || !timezone) return null;
  if (!withinRange(latitude, -90, 90) || !withinRange(longitude, -180, 180)) return null;
  return { dateOfBirth, timeOfBirth, placeLabel, latitude, longitude, timezone };
}

export function normalizePlanet(value: unknown, expectedName: string): BirthChartPlanet | null {
  if (!isRecord(value)) return null;
  const record = value as Record<string, unknown>;
  const name = exactText(record.name, 40);
  const rashi = exactCanonical(record.rashi, RASI_NAMES);
  const degree = finite(record.degree);
  const house = finite(record.house);
  if (
    name !== expectedName || !rashi || !validDegree(degree) || !validHouse(house)
    || typeof record.retrograde !== 'boolean'
  ) return null;
  return { name, rashi, degree, house, retrograde: record.retrograde };
}

export function normalizeNatalChart(value: unknown): GuestNatalChart | null {
  if (!isRecord(value)) return null;
  const record = value as Record<string, unknown>;
  const lagnaDegree = finite(record.lagnaDegree);
  const rawPlanets = Array.isArray(record.planets) ? record.planets : null;
  if (!validDegree(lagnaDegree) || !rawPlanets) return null;
  const planets = rawPlanets
    .map((planet, index) => normalizePlanet(planet, BIRTH_CHART_PLANET_NAMES[index] || ''))
    .filter((item): item is BirthChartPlanet => item !== null);
  return planets.length === 9 && planets.length === rawPlanets.length
    ? { lagnaDegree, planets }
    : null;
}

export function normalizeCalculation(value: unknown): GuestProfileCalculation | null {
  if (!isRecord(value)) return null;
  const record = value as Record<string, unknown>;
  const engineValue = record.engine;
  if (!isRecord(engineValue)) return null;
  const engineRecord = engineValue as Record<string, unknown>;
  const contractVersion = exactText(record.contractVersion, 20);
  const name = exactText(engineRecord.name, 60);
  const version = exactText(engineRecord.version, 40);
  const ayanamsha = exactText(engineRecord.ayanamsha, 40);
  const ephemeris = exactText(engineRecord.ephemeris, 20);
  if (
    contractVersion !== BIRTH_PROFILE_CONTRACT_VERSION
    || name !== BIRTH_PROFILE_ENGINE_NAME
    || !version
    || ayanamsha !== BIRTH_PROFILE_AYANAMSHA
    || !knownEphemeris(ephemeris)
  ) return null;
  return { contractVersion, engine: { name, version, ayanamsha, ephemeris } };
}

function validDegree(value: number | null): value is number {
  return value !== null && isContractRoundedDegree(value);
}

function validHouse(value: number | null): value is number {
  return withinRange(value, 1, 12) && Number.isInteger(value);
}

function knownEphemeris(value: string | null): value is 'swiss' | 'moshier' | 'unknown' {
  return value === 'swiss' || value === 'moshier' || value === 'unknown';
}
