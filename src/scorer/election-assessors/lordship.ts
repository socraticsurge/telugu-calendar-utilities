import { RASI_NAMES } from '../../data/rasis';
import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import type { PrimitiveOutcome } from './contracts';
import { completePlanetPositions } from './event-admission';

export const LORD_POSITION_FACTS_UNAVAILABLE =
  'Complete canonical nine-graha position facts are unavailable or conflicting.';

const CANONICAL_GRAHAS = new Set([
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani', 'Rahu', 'Ketu',
]);

export const CLASSICAL_RASI_LORDS = Object.freeze({
  Mesha: 'Kuja',
  Vrishabha: 'Shukra',
  Mithuna: 'Budha',
  Karka: 'Chandra',
  Simha: 'Surya',
  Kanya: 'Budha',
  Tula: 'Shukra',
  Vrischika: 'Kuja',
  Dhanu: 'Guru',
  Makara: 'Shani',
  Kumbha: 'Shani',
  Meena: 'Guru',
} as const satisfies Readonly<Record<string, string>>);

export function deriveLagnaSixthLords(lagnaRashi: string): {
  lagnaLord: string;
  sixthRashi: string;
  sixthLord: string;
} | null {
  const lagnaIndex = RASI_NAMES.indexOf(lagnaRashi);
  if (lagnaIndex < 0) return null;
  const sixthRashi = RASI_NAMES[(lagnaIndex + 5) % 12];
  return {
    lagnaLord: CLASSICAL_RASI_LORDS[
      lagnaRashi as keyof typeof CLASSICAL_RASI_LORDS
    ],
    sixthRashi,
    sixthLord: CLASSICAL_RASI_LORDS[
      sixthRashi as keyof typeof CLASSICAL_RASI_LORDS
    ],
  };
}

export function wholeSignShortestDistance(
  leftRashi: string,
  rightRashi: string,
): number | null {
  const left = RASI_NAMES.indexOf(leftRashi);
  const right = RASI_NAMES.indexOf(rightRashi);
  if (left < 0 || right < 0) return null;
  const delta = Math.abs(left - right);
  return Math.min(delta, 12 - delta);
}

export function evaluateRasiLordSeparation(
  chart: ElectionChartSnapshot,
  options: {
    firstRashi: string;
    secondRashi: string;
    requiredShortestDistance: number;
  },
): PrimitiveOutcome {
  if (
    !options || typeof options !== 'object' || Array.isArray(options)
    || !RASI_NAMES.includes(options.firstRashi)
    || !RASI_NAMES.includes(options.secondRashi)
    || !Number.isInteger(options.requiredShortestDistance)
    || options.requiredShortestDistance < 0
    || options.requiredShortestDistance > 6
  ) {
    return {
      status: 'unknown',
      evidence: ['The Rasi-lord separation configuration is incomplete.'],
    };
  }
  if (
    !chart || typeof chart !== 'object' || Array.isArray(chart)
    || !Array.isArray(chart.planets)
    || Array.from({ length: chart.planets.length }, (_, index) => chart.planets[index])
      .some(planet => !planet)
  ) {
    return { status: 'unknown', evidence: [LORD_POSITION_FACTS_UNAVAILABLE] };
  }
  const positions = completePlanetPositions(chart, CANONICAL_GRAHAS);
  if (!positions) {
    return { status: 'unknown', evidence: [LORD_POSITION_FACTS_UNAVAILABLE] };
  }

  const firstLord = CLASSICAL_RASI_LORDS[
    options.firstRashi as keyof typeof CLASSICAL_RASI_LORDS
  ];
  const secondLord = CLASSICAL_RASI_LORDS[
    options.secondRashi as keyof typeof CLASSICAL_RASI_LORDS
  ];
  const firstPosition = positions.get(firstLord)!;
  const secondPosition = positions.get(secondLord)!;
  const distance = wholeSignShortestDistance(firstPosition.rashi, secondPosition.rashi);
  if (distance === null) {
    return { status: 'unknown', evidence: [LORD_POSITION_FACTS_UNAVAILABLE] };
  }

  const evidence = firstLord === secondLord
    ? `${options.firstRashi} and ${options.secondRashi} share lord ${firstLord} in ${firstPosition.rashi}; shortest Whole Sign distance is 0 (required ${options.requiredShortestDistance}).`
    : `${options.firstRashi} lord ${firstLord} is in ${firstPosition.rashi}; ${options.secondRashi} lord ${secondLord} is in ${secondPosition.rashi}; shortest Whole Sign distance is ${distance} (required ${options.requiredShortestDistance}).`;
  return {
    status: distance === options.requiredShortestDistance ? 'pass' : 'fail',
    evidence: [evidence],
  };
}
