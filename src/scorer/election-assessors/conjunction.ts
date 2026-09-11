import { RASI_NAMES } from '../../data/rasis';
import type { PlanetPosition, PrimitiveOutcome } from './contracts';

export const CONJUNCTION_FACTS_UNAVAILABLE =
  'Complete canonical nine-graha Rasi facts are unavailable.';
const CANONICAL_GRAHAS = new Set([
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani', 'Rahu', 'Ketu',
]);

export const SAME_RASI_CONJUNCTION_METADATA = {
  source_statement: {
    claim_id: 'muhurta.borrowing_money',
    text: 'Avoid Chandra conjoined with Mangala or Shani.',
    locator: "B. V. Raman, Chapter X, 'Borrowing Money,' inspected in the 2020 Chistabo derivative at internal printed p. 45 (physical PDF p. 49)",
  },
  convention: {
    id: 'same-rasi-distributive-conjunction-v1',
    method_claim_id: 'election_chart.same_rasi_distributive_conjunction_policy_v1',
    formula: 'R(Chandra) = R(Kuja) OR R(Chandra) = R(Shani)',
    degree_orb: null,
  },
  event_policy: {
    id: 'borrowing-money.same-rasi-conjunction-reject-v1',
    decision_claim_id: 'election_chart.borrowing_same_rasi_conjunction_reject_policy_v1',
    activity: 'borrowing_money',
    effect: 'reject',
    status: 'specified_unwired',
    delivery_issue: 271,
  },
} as const;

export function evaluateSameRasiChandraConjunction(
  positions: ReadonlyMap<string, PlanetPosition> | null,
): PrimitiveOutcome {
  if (
    !positions
    || positions.size !== CANONICAL_GRAHAS.size
    || Array.from(positions).some(([name, position]) =>
      !CANONICAL_GRAHAS.has(name)
      || position.name !== name
      || !RASI_NAMES.includes(position.rashi))
  ) {
    return { status: 'unknown', evidence: [CONJUNCTION_FACTS_UNAVAILABLE] };
  }
  const chandra = positions?.get('Chandra');
  const kuja = positions?.get('Kuja');
  const shani = positions?.get('Shani');
  if (!chandra || !kuja || !shani) {
    return { status: 'unknown', evidence: [CONJUNCTION_FACTS_UNAVAILABLE] };
  }

  const matches = [
    ...(kuja.rashi === chandra.rashi ? ['Kuja'] : []),
    ...(shani.rashi === chandra.rashi ? ['Shani'] : []),
  ];
  if (matches.length) {
    const names = matches.length === 2
      ? 'Chandra, Kuja and Shani'
      : `Chandra and ${matches[0]}`;
    return {
      status: 'fail',
      evidence: [`Same-Rasi conjunction: ${names} in ${chandra.rashi}.`],
    };
  }

  return {
    status: 'pass',
    evidence: [
      `Chandra: ${chandra.rashi}; Kuja: ${kuja.rashi}; Shani: ${shani.rashi}; no same-Rasi conjunction.`,
    ],
  };
}

export function aggregateSameRasiConjunctionWindow(
  samples: readonly PrimitiveOutcome[],
  options: { transitionComplete: boolean; budgetExhausted: boolean },
): PrimitiveOutcome {
  const failed = samples.find(sample => sample.status === 'fail');
  if (failed) return failed;
  const unknown = samples.find(sample => sample.status === 'unknown');
  if (unknown) return unknown;
  if (!samples.length) {
    return { status: 'unknown', evidence: ['No sampled chart states are available.'] };
  }
  if (options.budgetExhausted) {
    return {
      status: 'unknown',
      evidence: [
        "The chart-request budget was exhausted before this window's coverage was complete.",
      ],
    };
  }
  if (!options.transitionComplete) {
    return {
      status: 'unknown',
      evidence: [
        'All sampled states pass, but Rasi-transition coverage is incomplete.',
      ],
    };
  }
  return {
    status: 'pass',
    evidence: [
      'Every sampled state resolves Chandra in a different Rasi from Kuja and Shani.',
    ],
  };
}
