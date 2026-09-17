import {
  BIRTH_CHART_PLANET_NAMES, fixedGrahaFactsMatch, wholeSignHousesMatch,
  isRashi, isChartDegree, isChartHouse, isBirthEphemeris, type BirthChartPlanet,
} from '../chart-contracts';
import {
  ELECTION_CHART_CONTRACT_VERSION, ELECTION_CHART_BATCH_LIMIT, ElectionChartApiError,
  type ElectionChartSnapshot, type ElectionChartEngine, type ElectionChartDerivation,
  type ElectionChartRequest, type ElectionChartLocation,
} from './contracts';
import { record, finite, exactNonEmpty, withinRange, required, boundedArray } from './values';

function parsePlanet(value: unknown, expectedName: string): BirthChartPlanet | null {
  const item = record(value);
  if (!item) return null;
  const name = exactNonEmpty(item.name, 40);
  const rashi = exactNonEmpty(item.rashi, 40);
  const degree = finite(item.degree);
  const house = finite(item.house);
  if (name !== expectedName || !isRashi(rashi)) return null;
  if (!isChartDegree(degree) || !isChartHouse(house)) return null;
  if (typeof item.retrograde !== 'boolean') return null;
  return { name, rashi, degree, house, retrograde: item.retrograde };
}

function parsePlanets(value: unknown): BirthChartPlanet[] | null {
  const values = required(boundedArray(value, 9, 9), invalidResponse);
  const planets = values.map((planet, index) => parsePlanet(planet, BIRTH_CHART_PLANET_NAMES[index]));
  return planets.every((planet): planet is BirthChartPlanet => planet !== null) ? planets : null;
}

function parseLagna(value: unknown): ElectionChartSnapshot['lagna'] | null {
  const item = required(record(value), invalidResponse);
  const rashi = exactNonEmpty(item.rashi, 40);
  const degree = finite(item.degree);
  return isRashi(rashi) && isChartDegree(degree) ? { rashi, degree } : null;
}

function parseSnapshot(value: unknown, expectedInstant: string): ElectionChartSnapshot | null {
  const item = required(record(value), invalidResponse);
  const lagna = parseLagna(item.lagna);
  const instant = exactNonEmpty(item.instant, 40);
  const planets = parsePlanets(item.planets);
  if (instant !== expectedInstant) return null;
  if (!lagna || !planets) return null;
  if (!wholeSignHousesMatch(lagna.rashi, planets) || !fixedGrahaFactsMatch(planets)) return null;
  return { instant, lagna, planets };
}

function validRequestLocation(location: ElectionChartLocation): boolean {
  if (!withinRange(location.latitude, -90, 90) || !withinRange(location.longitude, -180, 180)) return false;
  return Boolean(location.timezone) && location.timezone.length <= 80;
}

function canonicalInstant(instant: string): boolean {
  const parsed = new Date(instant);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString() === instant;
}

function validInstants(instants: string[]): boolean {
  if (!instants.length || instants.length > ELECTION_CHART_BATCH_LIMIT) return false;
  return new Set(instants).size === instants.length && instants.every(canonicalInstant);
}

export function validateRequest(input: ElectionChartRequest): void {
  if (!validRequestLocation(input.location) || !validInstants(input.instants)) {
    throw new ElectionChartApiError('invalid-request', 'The chart request is invalid.');
  }
}

function parseEngine(value: unknown): ElectionChartEngine | null {
  const engine = record(value);
  if (!engine) return null;
  const name = exactNonEmpty(engine.name, 60);
  const version = exactNonEmpty(engine.version, 40);
  const ayanamsha = exactNonEmpty(engine.ayanamsha, 40);
  const ephemeris = exactNonEmpty(engine.ephemeris, 20);
  const nodeConvention = exactNonEmpty(engine.node_convention, 20);
  if (name !== 'DashaFlow' || !version) return null;
  if (ayanamsha !== 'Lahiri') return null;
  if (nodeConvention !== 'mean') return null;
  if (!isBirthEphemeris(ephemeris) && ephemeris !== 'mixed') return null;
  return { name, version, ayanamsha, ephemeris, nodeConvention };
}

function matchesLocation(value: unknown, expected: ElectionChartLocation): boolean {
  const location = required(record(value), invalidResponse);
  return finite(location.latitude) === expected.latitude
    && finite(location.longitude) === expected.longitude
    && exactNonEmpty(location.timezone, 80) === expected.timezone;
}

function parseCharts(value: unknown, instants: string[]): ElectionChartSnapshot[] | null {
  const values = required(boundedArray(value, instants.length, instants.length), invalidResponse);
  const charts = values.map((chart, index) => parseSnapshot(chart, instants[index]));
  return charts.every((chart): chart is ElectionChartSnapshot => chart !== null) ? charts : null;
}

function validContract(result: Record<string, unknown> | null): boolean {
  return result?.contract_version === ELECTION_CHART_CONTRACT_VERSION
    && result.house_system === 'whole_sign';
}

export function parseElectionChartDerivation(
  payload: unknown,
  input: ElectionChartRequest,
): ElectionChartDerivation {
  const result = required(record(payload), invalidResponse);
  if (!validContract(result)) throw invalidResponse();
  if (!matchesLocation(result.location, input.location)) throw invalidResponse();
  const data = required(record(result.data), invalidResponse);
  const engine = required(parseEngine(result.engine), invalidResponse);
  const charts = required(parseCharts(data.charts, input.instants), invalidResponse);
  return {
    contractVersion: ELECTION_CHART_CONTRACT_VERSION,
    engine,
    houseSystem: 'whole_sign',
    location: input.location,
    charts,
  };
}

function invalidResponse(): ElectionChartApiError {
  return new ElectionChartApiError('invalid-response', 'The chart service returned an invalid response.');
}
