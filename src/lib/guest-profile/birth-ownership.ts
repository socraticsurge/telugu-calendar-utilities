import { NAKSHATRA_NAMES, RASI_NAMES } from '../../data/rasis';
import { BIRTH_CHART_PLANET_NAMES, fixedGrahaFactsMatch, roundedMoonMatchesBirthFacts, wholeSignHousesMatch } from '../birth-profile-api';
import { normalizeBirthDetails, normalizeCalculation, normalizeNatalChart, normalizePlanet } from './birth-normalization';
import { type StoredBirthProfileRecord } from './types';
import { canonical, hasExactKeys, pada, isRecord } from './values';


export function isOwnedBirthDetails(value: unknown): boolean {
  if (!isRecord(value)) return false;
  const record = value as Record<string, unknown>;
  const normalized = normalizeBirthDetails(record);
  return normalized !== null && hasExactKeys(record, [
    'dateOfBirth', 'timeOfBirth', 'placeLabel', 'latitude', 'longitude', 'timezone',
  ])
    && record.dateOfBirth === normalized.dateOfBirth
    && record.timeOfBirth === normalized.timeOfBirth
    && record.placeLabel === normalized.placeLabel
    && Object.is(record.latitude, normalized.latitude)
    && Object.is(record.longitude, normalized.longitude)
    && record.timezone === normalized.timezone;
}

export function isOwnedPlanet(value: unknown, expectedName: string): boolean {
  if (!isRecord(value)) return false;
  const record = value as Record<string, unknown>;
  const normalized = normalizePlanet(record, expectedName);
  return normalized !== null
    && hasExactKeys(record, ['name', 'rashi', 'degree', 'house', 'retrograde'])
    && record.name === normalized.name
    && record.rashi === normalized.rashi
    && Object.is(record.degree, normalized.degree)
    && Object.is(record.house, normalized.house)
    && record.retrograde === normalized.retrograde;
}

export function isOwnedNatalChart(value: unknown): boolean {
  if (!isRecord(value)) return false;
  const record = value as Record<string, unknown>;
  const normalized = normalizeNatalChart(record);
  return normalized !== null
    && hasExactKeys(record, ['lagnaDegree', 'planets'])
    && Object.is(record.lagnaDegree, normalized.lagnaDegree)
    && Array.isArray(record.planets)
    && record.planets.every((planet, index) =>
      isOwnedPlanet(planet, BIRTH_CHART_PLANET_NAMES[index] || ''));
}

export function isOwnedCalculation(value: unknown): boolean {
  if (!isRecord(value)) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, ['contractVersion', 'engine'])) return false;
  if (!isRecord(record.engine)) {
    return false;
  }
  const engine = record.engine as Record<string, unknown>;
  const normalized = normalizeCalculation(record);
  return normalized !== null && hasExactKeys(
    engine,
    ['name', 'version', 'ayanamsha', 'ephemeris'],
  )
    && record.contractVersion === normalized.contractVersion
    && engine.name === normalized.engine.name
    && engine.version === normalized.engine.version
    && engine.ayanamsha === normalized.engine.ayanamsha
    && engine.ephemeris === normalized.engine.ephemeris;
}

export function isOwnedBirthProfileRecord(value: unknown): value is StoredBirthProfileRecord {
  if (!isRecord(value)) return false;
  const record = value as Record<string, unknown>;
  const nakshatra = canonical(record.nakshatra, NAKSHATRA_NAMES);
  const padaValue = pada(record.pada);
  const lagna = canonical(record.lagna, RASI_NAMES);
  const janmaRasi = canonical(record.janmaRasi, RASI_NAMES);
  const natalChart = normalizeNatalChart(record.natalChart);
  return hasExactKeys(record, [
    'source', 'nakshatra', 'pada', 'lagna', 'birthDetails',
    'janmaRasi', 'natalChart', 'calculation',
  ])
    && record.source === 'birth-details'
    && nakshatra === record.nakshatra
    && padaValue === record.pada
    && lagna === record.lagna
    && janmaRasi === record.janmaRasi
    && isOwnedBirthDetails(record.birthDetails)
    && isOwnedNatalChart(record.natalChart)
    && isOwnedCalculation(record.calculation)
    && nakshatra !== null
    && padaValue !== null
    && janmaRasi !== null
    && natalChart !== null
    && lagna !== null
    && wholeSignHousesMatch(lagna, natalChart.planets)
    && fixedGrahaFactsMatch(natalChart.planets)
    && roundedMoonMatchesBirthFacts(
      nakshatra,
      padaValue,
      janmaRasi,
      natalChart.planets[1],
    );
}
