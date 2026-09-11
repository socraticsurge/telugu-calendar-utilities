import { RASI_NAMES } from '../../data/rasis';
import rulesContract from '../../data/election-chart-rules.generated.json';
import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  COMPLETE_GRAHA_FACTS_UNAVAILABLE,
  type ElectionPrimitiveRule,
  type PlanetPosition,
  type PrimitiveOutcome,
} from './contracts';
import { completePlanetPositions } from './event-admission';

const NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES = 0.02;
const BOUNDARY_EPSILON = 1e-9;

export type NaturalGrahaNature = 'benefic' | 'malefic' | 'unknown';

export interface NaturalGrahaNatureResult {
  complete: boolean;
  natures: Readonly<Record<string, NaturalGrahaNature>>;
  evidence: string[];
}

interface NaturalGrahaNatureConvention {
  fixed_malefics: string[];
  fixed_benefics: string[];
  chandra_phase_guard_degrees: number;
  phase_quantization_decimal_places: number;
  phase_quantization_rounding: 'half_up_nonnegative';
  budha_association: 'same_sidereal_rashi';
  house_system: 'whole_sign';
}

export const NATURAL_GRAHA_NATURE_CONVENTION_ID =
  'phaladeepika-natural-graha-nature-whole-sign-v1' as const;
const NATURAL_GRAHA_NATURE_CONVENTION = (
  rulesContract.conventions as unknown as Record<string, NaturalGrahaNatureConvention>
)[NATURAL_GRAHA_NATURE_CONVENTION_ID];
const CANONICAL_PLANET_ORDER = [...rulesContract.vacancy_includes];
const CANONICAL_PLANETS = new Set(CANONICAL_PLANET_ORDER);
const FIXED_MALEFICS = new Set(NATURAL_GRAHA_NATURE_CONVENTION.fixed_malefics);
const FIXED_BENEFICS = new Set(NATURAL_GRAHA_NATURE_CONVENTION.fixed_benefics);
const PHASE_QUANTIZATION_SCALE = 10 ** (
  NATURAL_GRAHA_NATURE_CONVENTION.phase_quantization_decimal_places
);
const PHASE_GUARD_UNITS = Math.floor(
  NATURAL_GRAHA_NATURE_CONVENTION.chandra_phase_guard_degrees
  * PHASE_QUANTIZATION_SCALE + 0.5,
);
const HALF_CIRCLE_UNITS = 180 * PHASE_QUANTIZATION_SCALE;
const FULL_CIRCLE_UNITS = 360 * PHASE_QUANTIZATION_SCALE;

function longitude(position: PlanetPosition): number {
  return RASI_NAMES.indexOf(position.rashi) * 30 + position.degree;
}

function unknownNatures(): Record<string, NaturalGrahaNature> {
  return Object.fromEntries(
    CANONICAL_PLANET_ORDER.map(name => [name, 'unknown' as const]),
  );
}

function resolvedChandraNature(
  positions: ReadonlyMap<string, PlanetPosition>,
): [NaturalGrahaNature, number] {
  const raw = (
    (longitude(positions.get('Chandra')!) - longitude(positions.get('Surya')!))
    % 360 + 360
  ) % 360;
  const elongationUnits = Math.floor(raw * PHASE_QUANTIZATION_SCALE + 0.5);
  const elongation = elongationUnits / PHASE_QUANTIZATION_SCALE;
  const boundaryDistanceUnits = Math.min(
    elongationUnits,
    Math.abs(elongationUnits - HALF_CIRCLE_UNITS),
    Math.abs(FULL_CIRCLE_UNITS - elongationUnits),
  );
  if (boundaryDistanceUnits <= PHASE_GUARD_UNITS) return ['unknown', elongation];
  return [elongationUnits < HALF_CIRCLE_UNITS ? 'benefic' : 'malefic', elongation];
}

export function classifyNaturalGrahaNatures(
  chart: ElectionChartSnapshot,
): NaturalGrahaNatureResult {
  const positions = completePlanetPositions(chart, CANONICAL_PLANETS);
  if (!positions) {
    return {
      complete: false,
      natures: unknownNatures(),
      evidence: ['Complete canonical nine-graha facts are unavailable or invalid.'],
    };
  }

  const natures = unknownNatures();
  for (const name of FIXED_MALEFICS) natures[name] = 'malefic';
  for (const name of FIXED_BENEFICS) natures[name] = 'benefic';
  const [moonNature, elongation] = resolvedChandraNature(positions);
  natures.Chandra = moonNature;
  const guard = NATURAL_GRAHA_NATURE_CONVENTION.chandra_phase_guard_degrees;
  const chandraEvidence = moonNature === 'unknown'
    ? `Chandra elongation ${elongation.toFixed(4)}° is inside the inclusive ${guard.toFixed(2)}° phase-boundary guard.`
    : `Chandra elongation ${elongation.toFixed(4)}° resolves ${moonNature}.`;

  const budha = positions.get('Budha')!;
  const companions = CANONICAL_PLANET_ORDER.filter(name =>
    name !== 'Budha' && positions.get(name)?.rashi === budha.rashi);
  const maleficWitnesses = companions.filter(name => natures[name] === 'malefic');
  let budhaEvidence: string;
  if (maleficWitnesses.length) {
    natures.Budha = 'malefic';
    budhaEvidence = `Budha shares ${budha.rashi} with resolved malefic ${maleficWitnesses.join(', ')}.`;
  } else if (companions.includes('Chandra') && natures.Chandra === 'unknown') {
    natures.Budha = 'unknown';
    budhaEvidence = `Budha shares ${budha.rashi} only with phase-unknown Chandra as a possible malefic witness.`;
  } else {
    natures.Budha = 'benefic';
    budhaEvidence = `No resolved malefic shares Budha's sidereal Rasi ${budha.rashi}.`;
  }
  return {
    complete: true,
    natures: Object.fromEntries(CANONICAL_PLANET_ORDER.map(name => [name, natures[name]])),
    evidence: [chandraEvidence, budhaEvidence],
  };
}

function normalizedHouseSet(houses: unknown): ReadonlySet<number> | null {
  if (!Array.isArray(houses) || !houses.length) return null;
  if (houses.some(house =>
    !Number.isInteger(house) || house < 1 || house > 12)) return null;
  return new Set(houses);
}

function houseWitnesses(
  chart: ElectionChartSnapshot,
  houses: unknown,
): { result: NaturalGrahaNatureResult; occupants: Array<[string, number]> } | null {
  const targetHouses = normalizedHouseSet(houses);
  if (!targetHouses) return null;
  const result = classifyNaturalGrahaNatures(chart);
  if (!result.complete) return { result, occupants: [] };
  const positions = completePlanetPositions(chart, CANONICAL_PLANETS);
  if (!positions) return { result: { ...result, complete: false }, occupants: [] };
  return {
    result,
    occupants: CANONICAL_PLANET_ORDER
      .map(name => [name, positions.get(name)?.house] as const)
      .filter((item): item is [string, number] =>
        item[1] !== undefined && targetHouses.has(item[1])),
  };
}

export function evaluateExistentialBeneficHouseSet(
  chart: ElectionChartSnapshot,
  houses: readonly number[],
): PrimitiveOutcome {
  const witnesses = houseWitnesses(chart, houses);
  if (!witnesses) {
    return { status: 'unknown', evidence: ['The required house set is invalid.'] };
  }
  const { result, occupants } = witnesses;
  if (!result.complete) return { status: 'unknown', evidence: result.evidence };
  const benefics = occupants.filter(([name]) => result.natures[name] === 'benefic');
  if (benefics.length) {
    const detail = benefics.map(([name, house]) => `${name} (house ${house})`).join(', ');
    return { status: 'pass', evidence: [`Resolved natural-benefic witness: ${detail}.`] };
  }
  const unresolved = occupants.filter(([name]) => result.natures[name] === 'unknown');
  if (unresolved.length) {
    const detail = unresolved.map(([name, house]) => `${name} (house ${house})`).join(', ');
    return { status: 'unknown', evidence: [`Natural-benefic witness remains unresolved: ${detail}.`] };
  }
  return { status: 'fail', evidence: ['No resolved natural benefic occupies the required house set.'] };
}

export function evaluateForbiddenMaleficHouseSet(
  chart: ElectionChartSnapshot,
  houses: readonly number[],
): PrimitiveOutcome {
  const witnesses = houseWitnesses(chart, houses);
  if (!witnesses) {
    return { status: 'unknown', evidence: ['The forbidden house set is invalid.'] };
  }
  const { result, occupants } = witnesses;
  if (!result.complete) return { status: 'unknown', evidence: result.evidence };
  const malefics = occupants.filter(([name]) => result.natures[name] === 'malefic');
  if (malefics.length) {
    const detail = malefics.map(([name, house]) => `${name} (house ${house})`).join(', ');
    return { status: 'fail', evidence: [`Forbidden natural-malefic witness: ${detail}.`] };
  }
  const unresolved = occupants.filter(([name]) => result.natures[name] === 'unknown');
  if (unresolved.length) {
    const detail = unresolved.map(([name, house]) => `${name} (house ${house})`).join(', ');
    return { status: 'unknown', evidence: [`Forbidden-malefic check remains unresolved: ${detail}.`] };
  }
  return { status: 'pass', evidence: ['No resolved natural malefic occupies the forbidden house set.'] };
}

export function evaluateHouseFreeOfNaturalMalefics(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition> | null,
  options: { houseFrameUncertain?: boolean } = {},
): PrimitiveOutcome {
  if (!positions) {
    return { status: 'unknown', evidence: [COMPLETE_GRAHA_FACTS_UNAVAILABLE] };
  }
  if (options.houseFrameUncertain) {
    return { status: 'unknown', evidence: ['The local-Lagna house frame is uncertain.'] };
  }

  const fixed = (rule.fixed_malefics || []).filter(
    name => positions.get(name)?.house === rule.house,
  );
  if (fixed.length) {
    return {
      status: 'fail',
      evidence: [`Natural malefics in Lagna: ${fixed.join(', ')}.`],
    };
  }

  const chandra = positions.get('Chandra');
  const surya = positions.get('Surya');
  if (!chandra || !surya) {
    return { status: 'unknown', evidence: [COMPLETE_GRAHA_FACTS_UNAVAILABLE] };
  }
  if (chandra.house !== rule.house) {
    return {
      status: 'pass',
      evidence: ['Natural malefics in Lagna: none; Chandra is outside Lagna.'],
    };
  }

  const elongation = ((longitude(chandra) - longitude(surya)) % 360 + 360) % 360;
  const guard = rule.lunar_phase_guard_degrees
    ?? NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES;
  const boundaryDistance = Math.min(
    elongation, 360 - elongation, Math.abs(elongation - 180),
  );
  if (boundaryDistance <= guard + BOUNDARY_EPSILON) {
    return {
      status: 'unknown',
      evidence: [
        `Chandra occupies Lagna at ${elongation.toFixed(2)}° solar elongation, inside the disclosed ±${guard.toFixed(2)}° phase boundary guard.`,
      ],
    };
  }
  if (elongation > 180) {
    return {
      status: 'fail',
      evidence: [
        `Natural malefics in Lagna: waning Chandra (${elongation.toFixed(2)}° solar elongation).`,
      ],
    };
  }
  return {
    status: 'pass',
    evidence: [
      `Natural malefics in Lagna: none; waxing Chandra (${elongation.toFixed(2)}° solar elongation) is not malefic under this convention.`,
    ],
  };
}
