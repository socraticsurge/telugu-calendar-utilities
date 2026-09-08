import { RASI_NAMES } from '../../data/rasis';
import {
  COMPLETE_GRAHA_FACTS_UNAVAILABLE,
  type ElectionPrimitiveRule,
  type PlanetPosition,
  type PrimitiveOutcome,
} from './contracts';

const NAVAMSA_WIDTH_DEGREES = 30 / 9;
const NAVAMSA_ROUNDING_GUARD_DEGREES = 0.01;
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

function navamsaStart(rashiIndex: number): number {
  const modality = rashiIndex % 3;
  if (modality === 0) return rashiIndex;
  if (modality === 1) return (rashiIndex + 8) % 12;
  return (rashiIndex + 4) % 12;
}

export function navamsaRashi(position: PlanetPosition): string | null {
  const nearBoundary = Array.from({ length: 10 }, (_, index) =>
    NAVAMSA_WIDTH_DEGREES * index).some(boundary =>
    Math.abs(position.degree - boundary) <= NAVAMSA_ROUNDING_GUARD_DEGREES);
  if (nearBoundary) return null;

  const rashiIndex = RASI_NAMES.indexOf(position.rashi);
  const division = Math.min(8, Math.floor(position.degree / NAVAMSA_WIDTH_DEGREES));
  return RASI_NAMES[(navamsaStart(rashiIndex) + division) % 12];
}

function adversePlacementFactors(
  rule: ElectionPrimitiveRule,
  position: PlanetPosition,
  navamsa: string | null,
  houseFrameUncertain: boolean,
): string[] {
  const adverse: string[] = [];
  if (!houseFrameUncertain && (rule.avoid_houses || []).includes(position.house)) {
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
  return adverse;
}

interface SolarClearanceState {
  adverse: string | null;
  uncertain: boolean;
  unavailable: PrimitiveOutcome | null;
}

function solarClearanceState(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition>,
  position: PlanetPosition,
): SolarClearanceState {
  const threshold = rule.solar_clearance_degrees;
  if (threshold === undefined) {
    return { adverse: null, uncertain: false, unavailable: null };
  }
  const surya = positions.get('Surya');
  if (!surya) {
    return {
      adverse: null,
      uncertain: false,
      unavailable: {
        status: 'unknown',
        evidence: ['Surya facts needed for solar clearance are unavailable.'],
      },
    };
  }
  const separation = Math.abs(
    ((longitude(position) - longitude(surya) + 180) % 360 + 360) % 360 - 180,
  );
  const guard = rule.solar_clearance_guard_degrees || 0;
  if (separation < threshold - guard) {
    return {
      adverse: `solar clearance ${separation.toFixed(2)}° below ${threshold}°`,
      uncertain: false,
      unavailable: null,
    };
  }
  return {
    adverse: null,
    uncertain: separation <= threshold + guard,
    unavailable: null,
  };
}

function guardReasons(
  navamsa: string | null,
  solarClearanceUncertain: boolean,
  houseFrameUncertain: boolean,
): string[] {
  const reasons: string[] = [];
  if (navamsa === null) reasons.push('Navamsa boundary');
  if (solarClearanceUncertain) reasons.push('solar-clearance threshold');
  if (houseFrameUncertain) reasons.push('local-Lagna house frame');
  return reasons;
}

export function evaluateWellSituated(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition> | null,
  options: { houseFrameUncertain?: boolean } = {},
): PrimitiveOutcome {
  const planetName = rule.planet || '';
  const position = positions?.get(planetName);
  if (!position || !positions) {
    return { status: 'unknown', evidence: [COMPLETE_GRAHA_FACTS_UNAVAILABLE] };
  }

  const navamsa = navamsaRashi(position);
  const adverse = adversePlacementFactors(
    rule, position, navamsa, Boolean(options.houseFrameUncertain),
  );
  const solar = solarClearanceState(rule, positions, position);
  if (solar.unavailable) return solar.unavailable;
  if (solar.adverse) adverse.push(solar.adverse);
  if (adverse.length) {
    return { status: 'fail', evidence: [`${planetName}: ${adverse.join('; ')}.`] };
  }

  const reasons = guardReasons(
    navamsa, solar.uncertain, Boolean(options.houseFrameUncertain),
  );
  if (reasons.length) {
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

interface AspectCandidate {
  aspector: string | null;
  uncertain: boolean;
  complete: boolean;
}

function aspectCandidate(
  sourceName: string,
  targetName: string,
  targetIndex: number,
  positions: ReadonlyMap<string, PlanetPosition>,
): AspectCandidate {
  if (sourceName === targetName) {
    return { aspector: null, uncertain: false, complete: true };
  }
  const source = positions.get(sourceName);
  const offsets = FULL_ASPECT_OFFSETS[sourceName];
  if (!source || !offsets) {
    return { aspector: null, uncertain: false, complete: false };
  }
  if (Math.min(source.degree, 30 - source.degree) <= RASI_ROUNDING_GUARD_DEGREES) {
    return { aspector: null, uncertain: true, complete: true };
  }
  const sourceIndex = RASI_NAMES.indexOf(source.rashi);
  const aspector = offsets.has((targetIndex - sourceIndex + 12) % 12)
    ? sourceName
    : null;
  return { aspector, uncertain: false, complete: true };
}

export function evaluateFullAspect(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition> | null,
): PrimitiveOutcome {
  const targetName = rule.planet || '';
  const target = positions?.get(targetName);
  if (!target || !positions) {
    return { status: 'unknown', evidence: [COMPLETE_GRAHA_FACTS_UNAVAILABLE] };
  }
  if (Math.min(target.degree, 30 - target.degree) <= RASI_ROUNDING_GUARD_DEGREES) {
    return {
      status: 'unknown',
      evidence: ['The target graha is within the rounded Rasi boundary guard.'],
    };
  }

  const aspectors: string[] = [];
  let uncertainAspector = false;
  const targetIndex = RASI_NAMES.indexOf(target.rashi);
  for (const sourceName of rule.aspectors || []) {
    const candidate = aspectCandidate(sourceName, targetName, targetIndex, positions);
    if (!candidate.complete) {
      return {
        status: 'unknown',
        evidence: ['Complete classical-graha aspect facts are unavailable.'],
      };
    }
    if (candidate.aspector) aspectors.push(candidate.aspector);
    uncertainAspector ||= candidate.uncertain;
  }

  if (aspectors.length) {
    return {
      status: 'pass',
      evidence: [`Full Graha Drishti to ${targetName}: ${aspectors.join(', ')}.`],
    };
  }
  if (uncertainAspector) {
    return {
      status: 'unknown',
      evidence: ['A possible aspector is within the rounded Rasi boundary guard.'],
    };
  }
  return { status: 'fail', evidence: [`No v1 full Graha Drishti reaches ${targetName}.`] };
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
  return Math.abs(
    ((longitude(left) - longitude(right) + 180) % 360 + 360) % 360 - 180,
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

function wellSituatedTransitionUncertainty(
  rule: ElectionPrimitiveRule,
  startPositions: ReadonlyMap<string, PlanetPosition>,
  endPositions: ReadonlyMap<string, PlanetPosition>,
  bodyBudget: number,
): string | null {
  const targetName = rule.planet || '';
  const targetStart = startPositions.get(targetName) as PlanetPosition;
  const targetEnd = endPositions.get(targetName) as PlanetPosition;
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

  const threshold = rule.solar_clearance_degrees;
  if (threshold === undefined) return null;
  const relativeBudget = GOLD_MAX_RELATIVE_MOTION_DEGREES_PER_DAY
    * bodyBudget / GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY
    + 2 * CONTRACT_DEGREE_HALF_STEP;
  const separations = [
    shortestSeparation(targetStart, startPositions.get('Surya') as PlanetPosition),
    shortestSeparation(targetEnd, endPositions.get('Surya') as PlanetPosition),
  ];
  if (Math.min(...separations.map(value => Math.abs(value - threshold))) <= relativeBudget) {
    return `${targetName}: the ${threshold}° solar-clearance transition cannot be excluded between samples.`;
  }
  return null;
}

function continuousFullAspectProved(
  targetStart: PlanetPosition,
  targetEnd: PlanetPosition,
  sourceStart: PlanetPosition,
  sourceEnd: PlanetPosition,
  bodyBudget: number,
): boolean {
  return !motionExceedsEnvelope(sourceStart, sourceEnd, bodyBudget)
    && targetStart.rashi === targetEnd.rashi
    && sourceStart.rashi === sourceEnd.rashi
    && !rasiTransitionUnrepresented(targetStart, targetEnd, bodyBudget)
    && !rasiTransitionUnrepresented(sourceStart, sourceEnd, bodyBudget);
}

function fullAspectTransitionUncertainty(
  rule: ElectionPrimitiveRule,
  startPositions: ReadonlyMap<string, PlanetPosition>,
  endPositions: ReadonlyMap<string, PlanetPosition>,
  bodyBudget: number,
): string | null {
  const targetName = rule.planet || '';
  const targetStart = startPositions.get(targetName) as PlanetPosition;
  const targetEnd = endPositions.get(targetName) as PlanetPosition;
  if (motionExceedsEnvelope(targetStart, targetEnd, bodyBudget)) {
    return `${targetName}: sampled motion exceeds the Gold v1 transition envelope.`;
  }

  const startSources = fullAspectSources(rule, startPositions);
  const endSources = fullAspectSources(rule, endPositions);
  for (const sourceName of startSources) {
    if (!endSources.has(sourceName)) continue;
    if (continuousFullAspectProved(
      targetStart,
      targetEnd,
      startPositions.get(sourceName) as PlanetPosition,
      endPositions.get(sourceName) as PlanetPosition,
      bodyBudget,
    )) return null;
  }
  return `${targetName}: a continuously present full Graha Drishti cannot be proved between samples.`;
}

export function goldTransitionUncertainty(
  rule: ElectionPrimitiveRule,
  startPositions: ReadonlyMap<string, PlanetPosition>,
  endPositions: ReadonlyMap<string, PlanetPosition>,
  gapMinutes: number,
): string | null {
  const bodyBudget = GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY
    * gapMinutes / (24 * 60);
  if (rule.kind === 'planet_well_situated') {
    return wellSituatedTransitionUncertainty(
      rule, startPositions, endPositions, bodyBudget,
    );
  }
  if (rule.kind === 'planet_receives_full_aspect') {
    return fullAspectTransitionUncertainty(
      rule, startPositions, endPositions, bodyBudget,
    );
  }
  return null;
}
