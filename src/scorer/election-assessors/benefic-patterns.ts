import { RASI_NAMES } from '../../data/rasis';
import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import {
  evaluateFullAspect,
} from './chart-geometry';
import type { PrimitiveOutcome } from './contracts';
import { completePlanetPositions } from './event-admission';
import {
  classifyNaturalGrahaNatures,
  evaluateExistentialBeneficHouseSet,
} from './graha-nature';

export const MALE_RASIS = new Set(RASI_NAMES.filter((_, index) => index % 2 === 0));
export const KENDRA_HOUSES = [1, 4, 7, 10] as const;
const CLASSICAL_GRAHAS = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani',
] as const;
const ALL_GRAHAS = new Set([
  ...CLASSICAL_GRAHAS, 'Rahu', 'Ketu',
]);
const RASI_ROUNDING_GUARD_DEGREES = 0.01;

function prefixed(label: string, outcome: PrimitiveOutcome): string[] {
  return outcome.evidence.map(item => `${label}: ${item}`);
}

function maleRasiBeneficAspect(chart: ElectionChartSnapshot): PrimitiveOutcome {
  const positions = completePlanetPositions(chart, ALL_GRAHAS);
  const nature = classifyNaturalGrahaNatures(chart);
  if (!positions || !nature.complete) {
    return {
      status: 'unknown',
      evidence: nature.evidence.length
        ? nature.evidence
        : ['Complete canonical nine-graha facts are unavailable.'],
    };
  }

  const witnesses: string[] = [];
  let unresolved = false;
  for (const targetName of CLASSICAL_GRAHAS) {
    const target = positions.get(targetName)!;
    const targetNature = nature.natures[targetName];
    const nearBoundary = Math.min(target.degree, 30 - target.degree)
      <= RASI_ROUNDING_GUARD_DEGREES;
    if (!MALE_RASIS.has(target.rashi)) {
      unresolved ||= nearBoundary && ['benefic', 'unknown'].includes(targetNature);
      continue;
    }

    const beneficSources = CLASSICAL_GRAHAS.filter(name =>
      name !== targetName && nature.natures[name] === 'benefic');
    const unresolvedSources = CLASSICAL_GRAHAS.filter(name =>
      name !== targetName && nature.natures[name] === 'unknown');
    const beneficAspect = evaluateFullAspect({
      kind: 'planet_receives_full_aspect',
      planet: targetName,
      aspectors: beneficSources,
    }, positions);
    const unresolvedAspect = evaluateFullAspect({
      kind: 'planet_receives_full_aspect',
      planet: targetName,
      aspectors: unresolvedSources,
    }, positions);
    if (targetNature === 'benefic' && beneficAspect.status === 'pass') {
      const aspectors = beneficAspect.evidence[0].split(': ', 2)[1].replace(/\.$/, '');
      witnesses.push(
        `${targetName} in ${target.rashi} receives full Graha Drishti from ${aspectors}`,
      );
    } else if (
      (targetNature === 'unknown' && (
        beneficAspect.status !== 'fail' || unresolvedAspect.status !== 'fail'
      ))
      || (targetNature === 'benefic' && (
        beneficAspect.status === 'unknown' || unresolvedAspect.status !== 'fail'
      ))
    ) {
      unresolved = true;
    }
  }

  if (witnesses.length) {
    return {
      status: 'pass',
      evidence: [`Resolved natural-benefic witness: ${witnesses.join('; ')}.`],
    };
  }
  if (unresolved) {
    return {
      status: 'unknown',
      evidence: ['A possible natural-benefic male-Rasi aspect witness is unresolved.'],
    };
  }
  return {
    status: 'fail',
    evidence: [
      'No resolved natural benefic in an odd Rasi receives a full classical aspect from another resolved natural benefic.',
    ],
  };
}

export function evaluateBeneficKendraOrMaleRasiAspect(
  chart: ElectionChartSnapshot,
  options: { houseFrameUncertain?: boolean } = {},
): PrimitiveOutcome {
  if (
    !options || typeof options !== 'object' || Array.isArray(options)
    || (options.houseFrameUncertain !== undefined
      && typeof options.houseFrameUncertain !== 'boolean')
  ) {
    return { status: 'unknown', evidence: ['The benefic-pattern configuration is malformed.'] };
  }
  if (options.houseFrameUncertain) {
    return {
      status: 'unknown',
      evidence: ['The validated local-Lagna house frame is unavailable or conflicting.'],
    };
  }
  if (!chart || typeof chart !== 'object' || Array.isArray(chart)) {
    return {
      status: 'unknown',
      evidence: ['Complete canonical nine-graha facts are unavailable.'],
    };
  }

  const kendra = evaluateExistentialBeneficHouseSet(chart, KENDRA_HOUSES);
  const maleRasiAspect = maleRasiBeneficAspect(chart);
  const evidence = [
    ...prefixed('Kendra arm', kendra),
    ...prefixed('Male-Rasi aspect arm', maleRasiAspect),
  ];
  if ([kendra.status, maleRasiAspect.status].includes('pass')) {
    return { status: 'pass', evidence };
  }
  if ([kendra.status, maleRasiAspect.status].includes('unknown')) {
    return { status: 'unknown', evidence };
  }
  return { status: 'fail', evidence };
}
