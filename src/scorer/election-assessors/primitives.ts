import { RASI_NAMES } from '../../data/rasis';
import type { ElectionChartSnapshot } from '../../lib/election-chart-api';

export type PrimitiveStatus = 'pass' | 'fail' | 'unknown';

export interface PrimitiveOutcome {
  status: PrimitiveStatus;
  evidence: string[];
}

export interface ElectionPrimitiveRule {
  planet?: string;
  planets?: string[];
  houses?: number[];
  avoid_houses?: number[];
  enemy_rashis?: string[];
  debilitation_rashi?: string;
  navamsa_debilitation_rashi?: string;
  aspectors?: string[];
  solar_clearance_degrees?: number;
  solar_clearance_guard_degrees?: number;
  house?: number;
  fixed_malefics?: string[];
  lunar_phase_guard_degrees?: number;
}

interface PlanetPosition {
  name: string;
  rashi: string;
  degree: number;
  house: number;
  retrograde: boolean;
}

export function evaluateAllPlanetsInHouses(
  rule: ElectionPrimitiveRule,
  houses: ReadonlyMap<string, number> | null,
  options: { houseFrameUncertain?: boolean } = {},
): PrimitiveOutcome {
  if (!houses || options.houseFrameUncertain) {
    return {
      status: 'unknown',
      evidence: ['Complete Whole Sign house facts are unavailable.'],
    };
  }
  const planets = rule.planets;
  const targetHouses = rule.houses;
  if (
    !planets?.length
    || planets.some(planet => typeof planet !== 'string' || !planet)
    || new Set(planets).size !== planets.length
    || !targetHouses?.length
    || targetHouses.some(house => !Number.isInteger(house) || house < 1 || house > 12)
    || planets.some(planet => !houses.has(planet))
  ) {
    return {
      status: 'unknown',
      evidence: ['The grouped-graha rule configuration is incomplete.'],
    };
  }
  const passed = planets.every(planet => targetHouses.includes(houses.get(planet)!));
  const observed = planets
    .map(planet => `${planet} house ${houses.get(planet)}`)
    .join('; ');
  return {
    status: passed ? 'pass' : 'fail',
    evidence: [`${observed}; all must be in house ${targetHouses.join(', ')}.`],
  };
}

const NAVAMSA_WIDTH_DEGREES = 30 / 9;
const NAVAMSA_ROUNDING_GUARD_DEGREES = 0.01;
const NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES = 0.02;
const BOUNDARY_EPSILON = 1e-9;
const RASI_ROUNDING_GUARD_DEGREES = 0.01;

export const GOLD_MAX_SAMPLE_GAP_MINUTES = 10;
export const GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY = 24;
export const GOLD_MAX_RELATIVE_MOTION_DEGREES_PER_DAY = 48;
export const CONTRACT_DEGREE_HALF_STEP = 0.005;

const FULL_ASPECT_OFFSETS: Readonly<Record<string, ReadonlySet<number>>> = {
  Surya: new Set([6]),
  Chandra: new Set([6]),
  Kuja: new Set([3, 6, 7]),
  Budha: new Set([6]),
  Guru: new Set([4, 6, 8]),
  Shukra: new Set([6]),
  Shani: new Set([2, 6, 9]),
};

function longitude(position: PlanetPosition): number {
  return RASI_NAMES.indexOf(position.rashi) * 30 + position.degree;
}

export function evaluateHouseFreeOfNaturalMalefics(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition> | null,
  options: { houseFrameUncertain?: boolean } = {},
): PrimitiveOutcome {
  if (!positions) {
    return { status: 'unknown', evidence: ['Complete graha facts are unavailable.'] };
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
    return { status: 'unknown', evidence: ['Complete graha facts are unavailable.'] };
  }
  if (chandra.house !== rule.house) {
    return {
      status: 'pass',
      evidence: ['Natural malefics in Lagna: none; Chandra is outside Lagna.'],
    };
  }

  const elongation = (
    (longitude(chandra) - longitude(surya)) % 360 + 360
  ) % 360;
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

export function completePlanetPositions(
  chart: ElectionChartSnapshot,
  expectedPlanets: ReadonlySet<string>,
): ReadonlyMap<string, PlanetPosition> | null {
  if (chart.planets.length !== expectedPlanets.size) return null;
  const result = new Map<string, PlanetPosition>();
  for (const planet of chart.planets) {
    if (
      !expectedPlanets.has(planet.name) || result.has(planet.name)
      || !RASI_NAMES.includes(planet.rashi)
      || !Number.isFinite(planet.degree) || planet.degree < 0 || planet.degree >= 30
      || !Number.isInteger(planet.house) || planet.house < 1 || planet.house > 12
      || typeof planet.retrograde !== 'boolean'
    ) return null;
    result.set(planet.name, { ...planet });
  }
  return result.size === expectedPlanets.size ? result : null;
}

export function navamsaRashi(position: PlanetPosition): string | null {
  const nearBoundary = Array.from({ length: 10 }, (_, index) =>
    NAVAMSA_WIDTH_DEGREES * index).some(boundary =>
    Math.abs(position.degree - boundary) <= NAVAMSA_ROUNDING_GUARD_DEGREES);
  if (nearBoundary) return null;

  const rashiIndex = RASI_NAMES.indexOf(position.rashi);
  const modality = rashiIndex % 3;
  const start = modality === 0
    ? rashiIndex
    : modality === 1
      ? (rashiIndex + 8) % 12
      : (rashiIndex + 4) % 12;
  const division = Math.min(8, Math.floor(position.degree / NAVAMSA_WIDTH_DEGREES));
  return RASI_NAMES[(start + division) % 12];
}

export function evaluateWellSituated(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition> | null,
  options: { houseFrameUncertain?: boolean } = {},
): PrimitiveOutcome {
  const planetName = rule.planet || '';
  const position = positions?.get(planetName);
  if (!position) {
    return { status: 'unknown', evidence: ['Complete graha facts are unavailable.'] };
  }

  const navamsa = navamsaRashi(position);
  const adverse: string[] = [];
  let solarClearanceUncertain = false;
  if (!options.houseFrameUncertain && (rule.avoid_houses || []).includes(position.house)) {
    adverse.push(`house ${position.house}`);
  }
  if ((rule.enemy_rashis || []).includes(position.rashi)) {
    adverse.push(`enemy Rasi ${position.rashi}`);
  }
  if (position.rashi === rule.debilitation_rashi) {
    adverse.push(`debilitation Rasi ${position.rashi}`);
  }
  if (navamsa !== null && navamsa === rule.navamsa_debilitation_rashi) {
    adverse.push(`debilitation Navamsa ${navamsa}`);
  }
  if (rule.solar_clearance_degrees !== undefined) {
    const surya = positions?.get('Surya');
    if (!surya) {
      return {
        status: 'unknown',
        evidence: ['Surya facts needed for solar clearance are unavailable.'],
      };
    }
    const longitude = RASI_NAMES.indexOf(position.rashi) * 30 + position.degree;
    const solarLongitude = RASI_NAMES.indexOf(surya.rashi) * 30 + surya.degree;
    const separation = Math.abs(
      ((longitude - solarLongitude + 180) % 360 + 360) % 360 - 180,
    );
    const guard = rule.solar_clearance_guard_degrees || 0;
    if (separation < rule.solar_clearance_degrees - guard) {
      adverse.push(
        `solar clearance ${separation.toFixed(2)}° below ${rule.solar_clearance_degrees}°`,
      );
    } else if (separation <= rule.solar_clearance_degrees + guard) {
      solarClearanceUncertain = true;
    }
  }
  if (adverse.length) {
    return { status: 'fail', evidence: [`${planetName}: ${adverse.join('; ')}.`] };
  }
  if (navamsa === null || solarClearanceUncertain || options.houseFrameUncertain) {
    const reasons = [
      ...(navamsa === null ? ['Navamsa boundary'] : []),
      ...(solarClearanceUncertain ? ['solar-clearance threshold'] : []),
      ...(options.houseFrameUncertain ? ['local-Lagna house frame'] : []),
    ];
    return {
      status: 'unknown',
      evidence: [
        `${planetName}: ${position.rashi} ${position.degree.toFixed(2)}° is within the rounded ${reasons.join(' and ')} guard.`,
      ],
    };
  }
  return {
    status: 'pass',
    evidence: [
      `${planetName}: ${position.rashi}, house ${position.house}, ${navamsa} Navamsa; no v1 adverse placement factor.`,
    ],
  };
}

export function evaluateFullAspect(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition> | null,
): PrimitiveOutcome {
  const targetName = rule.planet || '';
  const target = positions?.get(targetName);
  if (!target) {
    return { status: 'unknown', evidence: ['Complete graha facts are unavailable.'] };
  }
  if (Math.min(target.degree, 30 - target.degree) <= RASI_ROUNDING_GUARD_DEGREES) {
    return {
      status: 'unknown',
      evidence: ['The target graha is within the rounded Rasi boundary guard.'],
    };
  }
  const targetIndex = RASI_NAMES.indexOf(target.rashi);
  const aspectors: string[] = [];
  let uncertainAspector = false;
  for (const sourceName of rule.aspectors || []) {
    if (sourceName === targetName) continue;
    const source = positions?.get(sourceName);
    const offsets = FULL_ASPECT_OFFSETS[sourceName];
    if (!source || !offsets) {
      return {
        status: 'unknown',
        evidence: ['Complete classical-graha aspect facts are unavailable.'],
      };
    }
    if (Math.min(source.degree, 30 - source.degree) <= RASI_ROUNDING_GUARD_DEGREES) {
      uncertainAspector = true;
      continue;
    }
    const sourceIndex = RASI_NAMES.indexOf(source.rashi);
    if (offsets.has((targetIndex - sourceIndex + 12) % 12)) aspectors.push(sourceName);
  }
  if (!aspectors.length) {
    if (uncertainAspector) {
      return {
        status: 'unknown',
        evidence: ['A possible aspector is within the rounded Rasi boundary guard.'],
      };
    }
    return { status: 'fail', evidence: [`No v1 full Graha Drishti reaches ${targetName}.`] };
  }
  return {
    status: 'pass',
    evidence: [`Full Graha Drishti to ${targetName}: ${aspectors.join(', ')}.`],
  };
}

function nearBoundary(
  degree: number,
  boundaries: readonly number[],
  motionBudget: number,
): boolean {
  return Math.min(...boundaries.map(boundary => Math.abs(degree - boundary)))
    <= motionBudget + CONTRACT_DEGREE_HALF_STEP;
}

function rasiTransitionUnrepresented(
  start: PlanetPosition,
  end: PlanetPosition,
  motionBudget: number,
): boolean {
  if (start.rashi !== end.rashi) return false;
  return [start, end].some(position =>
    nearBoundary(position.degree, [0, 30], motionBudget));
}

function navamsaTransitionUnrepresented(
  start: PlanetPosition,
  end: PlanetPosition,
  motionBudget: number,
): boolean {
  const startDivision = Math.floor(start.degree / NAVAMSA_WIDTH_DEGREES);
  const endDivision = Math.floor(end.degree / NAVAMSA_WIDTH_DEGREES);
  if (start.rashi !== end.rashi || startDivision !== endDivision) return false;
  const boundaries = Array.from({ length: 10 }, (_, index) =>
    NAVAMSA_WIDTH_DEGREES * index);
  return [start, end].some(position =>
    nearBoundary(position.degree, boundaries, motionBudget));
}

function shortestSeparation(left: PlanetPosition, right: PlanetPosition): number {
  const leftLongitude = RASI_NAMES.indexOf(left.rashi) * 30 + left.degree;
  const rightLongitude = RASI_NAMES.indexOf(right.rashi) * 30 + right.degree;
  return Math.abs(
    ((leftLongitude - rightLongitude + 180) % 360 + 360) % 360 - 180,
  );
}

function motionExceedsEnvelope(
  start: PlanetPosition,
  end: PlanetPosition,
  motionBudget: number,
): boolean {
  return shortestSeparation(start, end)
    > motionBudget + 2 * CONTRACT_DEGREE_HALF_STEP;
}

function fullAspectSources(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition>,
): Set<string> {
  const targetName = rule.planet || '';
  const target = positions.get(targetName) as PlanetPosition;
  const targetIndex = RASI_NAMES.indexOf(target.rashi);
  return new Set((rule.aspectors || []).filter(sourceName => {
    if (sourceName === targetName) return false;
    const source = positions.get(sourceName) as PlanetPosition;
    return FULL_ASPECT_OFFSETS[sourceName].has(
      (targetIndex - RASI_NAMES.indexOf(source.rashi) + 12) % 12,
    );
  }));
}

/**
 * Find a Gold predicate transition that the ten-minute cadence cannot disprove.
 * Different endpoint states represent both sides of a boundary. Matching
 * endpoint states are expanded by the documented angular-motion envelope and
 * fail closed if a cross-and-return remains possible.
 */
export function goldTransitionUncertainty(
  rule: ElectionPrimitiveRule & { kind?: string },
  startPositions: ReadonlyMap<string, PlanetPosition>,
  endPositions: ReadonlyMap<string, PlanetPosition>,
  gapMinutes: number,
): string | null {
  const bodyBudget = GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY
    * gapMinutes / (24 * 60);
  const targetName = rule.planet || '';
  const targetStart = startPositions.get(targetName) as PlanetPosition;
  const targetEnd = endPositions.get(targetName) as PlanetPosition;

  if (rule.kind === 'planet_well_situated') {
    const relevant = [
      targetName,
      ...(rule.solar_clearance_degrees !== undefined ? ['Surya'] : []),
    ];
    if (relevant.some(name => motionExceedsEnvelope(
      startPositions.get(name) as PlanetPosition,
      endPositions.get(name) as PlanetPosition,
      bodyBudget,
    ))) {
      return `${targetName}: sampled motion exceeds the Gold v1 transition envelope.`;
    }
    if (
      rasiTransitionUnrepresented(targetStart, targetEnd, bodyBudget)
      || navamsaTransitionUnrepresented(targetStart, targetEnd, bodyBudget)
    ) {
      return `${targetName}: a Rasi or Navamsa transition cannot be excluded between these rounded samples.`;
    }
    if (rule.solar_clearance_degrees !== undefined) {
      const relativeBudget = GOLD_MAX_RELATIVE_MOTION_DEGREES_PER_DAY
        * gapMinutes / (24 * 60) + 2 * CONTRACT_DEGREE_HALF_STEP;
      const separations = [
        shortestSeparation(
          targetStart,
          startPositions.get('Surya') as PlanetPosition,
        ),
        shortestSeparation(
          targetEnd,
          endPositions.get('Surya') as PlanetPosition,
        ),
      ];
      if (Math.min(...separations.map(value =>
        Math.abs(value - (rule.solar_clearance_degrees as number))))
        <= relativeBudget) {
        return `${targetName}: the ${rule.solar_clearance_degrees}° solar-clearance transition cannot be excluded between samples.`;
      }
    }
    return null;
  }

  if (rule.kind === 'planet_receives_full_aspect') {
    if (motionExceedsEnvelope(targetStart, targetEnd, bodyBudget)) {
      return `${targetName}: sampled motion exceeds the Gold v1 transition envelope.`;
    }
    const startSources = fullAspectSources(rule, startPositions);
    const endSources = fullAspectSources(rule, endPositions);
    for (const sourceName of startSources) {
      if (!endSources.has(sourceName)) continue;
      const sourceStart = startPositions.get(sourceName) as PlanetPosition;
      const sourceEnd = endPositions.get(sourceName) as PlanetPosition;
      if (
        !motionExceedsEnvelope(sourceStart, sourceEnd, bodyBudget)
        && targetStart.rashi === targetEnd.rashi
        && sourceStart.rashi === sourceEnd.rashi
        && !rasiTransitionUnrepresented(targetStart, targetEnd, bodyBudget)
        && !rasiTransitionUnrepresented(sourceStart, sourceEnd, bodyBudget)
      ) return null;
    }
    return `${targetName}: a continuously present full Graha Drishti cannot be proved between samples.`;
  }
  return null;
}
