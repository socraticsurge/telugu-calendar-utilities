import { rasiFromStar } from '../../data/rasis';
import {
  BIRTH_PROFILE_CONTRACT_VERSION, BIRTH_PROFILE_ENGINE_NAME, BIRTH_PROFILE_AYANAMSHA,
  BIRTH_CHART_PLANET_NAMES, isRashi, isNakshatra, isPada, isChartDegree, isChartHouse, isBirthEphemeris,
  roundedMoonMatchesBirthFacts, wholeSignHousesMatch, fixedGrahaFactsMatch, type BirthChartPlanet,
  type BirthPada, type BirthProfileEngine,
} from '../chart-contracts';
import { BirthProfileApiError, type BirthProfileDerivation } from './contracts';
import { record, finite, exactNonEmpty, required } from './values';

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

function parseEngine(value: unknown): BirthProfileEngine | null {
  const item = record(value);
  if (!item) return null;
  const name = exactNonEmpty(item.name, 60);
  const version = exactNonEmpty(item.version, 40);
  const ayanamsha = exactNonEmpty(item.ayanamsha, 40);
  const ephemeris = exactNonEmpty(item.ephemeris, 20);
  if (name !== BIRTH_PROFILE_ENGINE_NAME || !version) return null;
  if (ayanamsha !== BIRTH_PROFILE_AYANAMSHA || !isBirthEphemeris(ephemeris)) return null;
  return { name, version, ayanamsha, ephemeris };
}

function parseBirthFacts(value: unknown) {
  const data = record(value);
  if (!data) return null;
  const nakshatra = exactNonEmpty(data.nakshatra, 60);
  const pada = finite(data.pada);
  const janmaRashi = exactNonEmpty(data.janma_rashi, 40);
  const lagna = exactNonEmpty(data.lagna, 40);
  const lagnaDegree = finite(data.lagna_degree);
  if (!isNakshatra(nakshatra)) return null;
  if (!isPada(pada) || !isRashi(janmaRashi)) return null;
  if (rasiFromStar(nakshatra, pada) !== janmaRashi) return null;
  if (!isRashi(lagna) || !isChartDegree(lagnaDegree)) return null;
  return { nakshatra, pada, janmaRashi, lagna, lagnaDegree };
}

function parsePlanets(value: unknown): BirthChartPlanet[] | null {
  if (!Array.isArray(value) || value.length !== 9) return null;
  const planets = value.map((planet, index) => parsePlanet(planet, BIRTH_CHART_PLANET_NAMES[index]));
  return planets.every((planet): planet is BirthChartPlanet => planet !== null) ? planets : null;
}

function validBirthProfileChart(
  planets: readonly BirthChartPlanet[],
  facts: { nakshatra: string; pada: BirthPada; janmaRashi: string; lagna: string },
): boolean {
  if (!roundedMoonMatchesBirthFacts(facts.nakshatra, facts.pada, facts.janmaRashi, planets[1])) return false;
  return wholeSignHousesMatch(facts.lagna, planets) && fixedGrahaFactsMatch(planets);
}

export function parseBirthProfile(value: unknown): BirthProfileDerivation {
  const payload = required(record(value), invalidResponse);
  const version = exactNonEmpty(payload.contract_version, 20);
  if (version !== BIRTH_PROFILE_CONTRACT_VERSION) throw invalidResponse();
  const data = required(record(payload.data), invalidResponse);
  const engine = required(parseEngine(payload.engine), invalidResponse);
  const facts = required(parseBirthFacts(data), invalidResponse);
  const planets = required(parsePlanets(data.planets), invalidResponse);
  if (!validBirthProfileChart(planets, facts)) throw invalidResponse();
  return { contractVersion: BIRTH_PROFILE_CONTRACT_VERSION, engine, ...facts, planets };
}

function invalidResponse(): BirthProfileApiError {
  return new BirthProfileApiError('invalid-response', 'The calculation service returned an invalid response.');
}
