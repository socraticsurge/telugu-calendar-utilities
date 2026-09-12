import type { ElectionChartSnapshot } from '../lib/election-chart-api';
import { RASI_NAMES } from '../data/rasis';
import type { CourtTransitionCoverage } from './election-chart-screening';

const MAX_SAMPLE_GAP_MINUTES = 10;
const MAX_GRAHA_MOTION_DEGREES_PER_DAY = 24;
const MAX_RELATIVE_MOTION_DEGREES_PER_DAY = 48;
const NAVAMSA_WIDTH_DEGREES = 30 / 9;
const DISPLAYED_DEGREE_HALF_STEP = 0.005;
const PLANET_NAMES = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
  'Shukra', 'Shani', 'Rahu', 'Ketu',
] as const;

function absoluteLongitude(position: ElectionChartSnapshot['planets'][number]): number {
  return RASI_NAMES.indexOf(position.rashi) * 30 + position.degree;
}

function circularDistance(left: number, right: number): number {
  return Math.abs(((right - left + 540) % 360) - 180);
}

function pairGapMinutes(
  start: ElectionChartSnapshot,
  end: ElectionChartSnapshot,
): number | null {
  const gap = (Date.parse(end.instant) - Date.parse(start.instant)) / 60_000;
  return Number.isFinite(gap) && gap > 0 && gap <= MAX_SAMPLE_GAP_MINUTES
    ? gap
    : null;
}

function rasiCoverage(
  charts: readonly ElectionChartSnapshot[],
  planetNames: ReadonlySet<string>,
): boolean {
  for (let index = 1; index < charts.length; index += 1) {
    const start = charts[index - 1];
    const end = charts[index];
    const gap = pairGapMinutes(start, end);
    if (gap === null) return false;
    const budget = MAX_GRAHA_MOTION_DEGREES_PER_DAY * gap / (24 * 60);
    for (const name of planetNames) {
      const left = start.planets.find(planet => planet.name === name);
      const right = end.planets.find(planet => planet.name === name);
      if (!left || !right) return false;
      if (circularDistance(absoluteLongitude(left), absoluteLongitude(right))
        > budget + 2 * DISPLAYED_DEGREE_HALF_STEP) return false;
      if (
        left.rashi === right.rashi
        && [left, right].some(position =>
          Math.min(position.degree, 30 - position.degree)
          <= budget + DISPLAYED_DEGREE_HALF_STEP)
      ) return false;
    }
  }
  return charts.length > 0;
}

function phaseCoverage(charts: readonly ElectionChartSnapshot[]): boolean {
  for (let index = 1; index < charts.length; index += 1) {
    const start = charts[index - 1];
    const end = charts[index];
    const gap = pairGapMinutes(start, end);
    if (gap === null) return false;
    const leftSun = start.planets.find(planet => planet.name === 'Surya');
    const leftMoon = start.planets.find(planet => planet.name === 'Chandra');
    const rightSun = end.planets.find(planet => planet.name === 'Surya');
    const rightMoon = end.planets.find(planet => planet.name === 'Chandra');
    if (!leftSun || !leftMoon || !rightSun || !rightMoon) return false;
    const left = (absoluteLongitude(leftMoon) - absoluteLongitude(leftSun) + 360) % 360;
    const right = (absoluteLongitude(rightMoon) - absoluteLongitude(rightSun) + 360) % 360;
    const budget = MAX_RELATIVE_MOTION_DEGREES_PER_DAY * gap / (24 * 60);
    if (circularDistance(left, right) > budget + 2 * DISPLAYED_DEGREE_HALF_STEP) {
      return false;
    }
    const samePhase = (left < 180) === (right < 180);
    const nearBoundary = (value: number) => Math.min(
      value, Math.abs(value - 180), 360 - value,
    ) <= budget + DISPLAYED_DEGREE_HALF_STEP;
    if (samePhase && (nearBoundary(left) || nearBoundary(right))) return false;
  }
  return charts.length > 0;
}

function lagnaNavamsaCoverage(
  charts: readonly ElectionChartSnapshot[],
  canonicalLagnas: readonly string[],
): boolean {
  if (charts.length !== canonicalLagnas.length || !charts.length) return false;
  for (let index = 0; index < charts.length; index += 1) {
    const lagna = charts[index].lagna;
    if (
      lagna.rashi !== canonicalLagnas[index]
      || !Number.isFinite(lagna.degree)
      || lagna.degree < 0 || lagna.degree >= 30
    ) return false;
    const distanceToBoundary = Math.min(...Array.from(
      { length: 10 },
      (_, boundary) => Math.abs(lagna.degree - boundary * NAVAMSA_WIDTH_DEGREES),
    ));
    if (distanceToBoundary <= 0.01) return false;
    if (index === 0) continue;
    if (pairGapMinutes(charts[index - 1], charts[index]) === null) return false;
    const previous = charts[index - 1].lagna;
    const forward = (
      RASI_NAMES.indexOf(lagna.rashi) * 30 + lagna.degree
      - (RASI_NAMES.indexOf(previous.rashi) * 30 + previous.degree)
      + 360
    ) % 360;
    if (forward >= NAVAMSA_WIDTH_DEGREES) return false;
  }
  return true;
}

/** Infer fail-closed Court transition coverage from the bounded sampling plan. */
export function inferCourtTransitionCoverage(
  charts: readonly ElectionChartSnapshot[],
  canonicalLagnas: readonly string[],
  localLagnaTransitionsComplete: boolean,
): CourtTransitionCoverage {
  const allGrahas = new Set(PLANET_NAMES);
  const grahaRasiTransitionsComplete = rasiCoverage(charts, allGrahas);
  return {
    localLagnaTransitionsComplete,
    lagnaNavamsaTransitionsComplete:
      lagnaNavamsaCoverage(charts, canonicalLagnas),
    guruRasiTransitionsComplete: rasiCoverage(charts, new Set(['Guru'])),
    grahaRasiTransitionsComplete,
    chandraPhaseTransitionsComplete: phaseCoverage(charts),
    budhaAssociationTransitionsComplete: grahaRasiTransitionsComplete,
    lagnaLordRasiTransitionsComplete: grahaRasiTransitionsComplete,
    sixthLordRasiTransitionsComplete: grahaRasiTransitionsComplete,
    fullAspectTransitionsComplete: grahaRasiTransitionsComplete,
    budgetExhausted: false,
  };
}
