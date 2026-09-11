import { RASI_NAMES } from '../../data/rasis';
import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import { navamsaRashi } from './chart-geometry';
import type { PlanetPosition, PrimitiveOutcome } from './contracts';
import { evaluateForbiddenMaleficHouseSet } from './graha-nature';

const NAVAMSA_ROUNDING_GUARD_DEGREES = 0.01;

export const COURT_MESHA_D1_D9_METADATA = {
  source_statement: {
    claim_id: 'muhurta.court.filing_lawsuit',
    text: 'The Lagna should be Mesha, or at least the Navamsa must be Mesha.',
    locator: "B. V. Raman, Chapter XVII, 'Miscellaneous elections,' section 'Filing law-suits,' inspected in the 2020 Chistabo derivative at internal printed p. 67 (physical PDF p. 71)",
  },
  convention: {
    id: 'court-canonical-local-d1-sidecar-d9-v1',
    method_claim_ids: [
      'election_chart.whole_sign_house_policy_v1',
      'election_chart.navamsa.bphs_6_12',
    ],
    formula: 'canonical local D1 Lagna Rasi = Mesha OR BPHS-modality Navamsa(sidecar Lagna Rasi, degree) = Mesha',
    d1_authority: 'canonical local Drik/Lahiri Lagna Rasi',
    d9_authority: 'sidecar Lagna degree only when its Rasi agrees with canonical local D1',
    navamsa_boundary_guard_degrees: NAVAMSA_ROUNDING_GUARD_DEGREES,
    unsupported_system: 'unknown',
  },
  event_policy: {
    id: 'court.mesha-lagna-or-navamsa',
    activity: 'court',
    effect: 'reject',
    effect_claim_id: 'muhurta.court.effect_policy_v1',
    status: 'specified_unwired',
    delivery_issue: 395,
  },
  conditional_admission: {
    id: 'court.mesha-navamsa-unresolved',
    status: 'specified_unwired',
    delivery_issue: 285,
    rule: 'Only a valid non-Mesha D1 candidate whose D9 alternative is not yet resolved may be provisionally retained.',
  },
} as const;

export const COURT_SIXTH_HOUSE_NATURAL_MALEFIC_METADATA = {
  source_statement: {
    claim_id: 'muhurta.court.filing_lawsuit',
    text: 'Place no malefic in the 6th.',
    locator: "B. V. Raman, Chapter XVII, 'Miscellaneous elections,' section 'Filing law-suits,' inspected in the 2020 Chistabo derivative at internal printed p. 67 (physical PDF p. 71)",
  },
  convention: {
    classifier_id: 'phaladeepika-natural-graha-nature-whole-sign-v1',
    house_occupation_id: 'whole-sign-physical-occupation-v1',
    method_claim_ids: [
      'election_chart.natural_graha_nature.phaladeepika_2_27',
      'election_chart.budha_same_sign_association_policy_v1',
      'election_chart.raman_180_degree_paksha_policy_v1',
      'election_chart.lunar_phase_boundary_guard_policy_v1',
      'election_chart.whole_sign_house_policy_v1',
    ],
    formula: 'no graha p has H(p) = 6 and natural_nature(p) = malefic',
    house_system: 'whole_sign',
    frame: 'validated_local_lagna',
  },
  event_policy: {
    id: 'court.house-6-without-natural-malefic',
    activity: 'court',
    effect: 'reject',
    effect_claim_id: 'muhurta.court.effect_policy_v1',
    status: 'specified_unwired',
    delivery_issue: 397,
  },
} as const;

export interface CourtMeshaD1D9Options {
  authoritativeD1Rashi?: string | null;
  lagnaAuthorityUncertain?: boolean;
  supportedSystem?: boolean;
}

export interface CourtMeshaD1D9Coverage {
  localLagnaTransitionsComplete: boolean;
  lagnaNavamsaTransitionsComplete: boolean;
  budgetExhausted: boolean;
}

export interface CourtSixthHouseNaturalMaleficCoverage {
  localLagnaTransitionsComplete: boolean;
  grahaRasiTransitionsComplete: boolean;
  chandraPhaseTransitionsComplete: boolean;
  budhaAssociationTransitionsComplete: boolean;
  budgetExhausted: boolean;
}

function exactLagna(
  chart: ElectionChartSnapshot | null | undefined,
): { rashi: string; degree: number } | null {
  if (!chart || typeof chart !== 'object' || Array.isArray(chart)) return null;
  const lagna = chart.lagna;
  if (
    !lagna || typeof lagna !== 'object' || Array.isArray(lagna)
    || !RASI_NAMES.includes(lagna.rashi)
    || typeof lagna.degree !== 'number' || !Number.isFinite(lagna.degree)
    || lagna.degree < 0 || lagna.degree >= 30
  ) return null;
  return { rashi: lagna.rashi, degree: lagna.degree };
}

export function evaluateCourtMeshaD1D9(
  chart: ElectionChartSnapshot | null,
  options: CourtMeshaD1D9Options = {},
): PrimitiveOutcome {
  if (
    (options.supportedSystem !== undefined
      && typeof options.supportedSystem !== 'boolean')
    || (options.lagnaAuthorityUncertain !== undefined
      && typeof options.lagnaAuthorityUncertain !== 'boolean')
  ) {
    return {
      status: 'unknown',
      evidence: ['The Court D1/D9 evaluator configuration is malformed.'],
    };
  }
  if (options.supportedSystem === false) {
    return {
      status: 'unknown',
      evidence: [
        'The Court D1/D9 predicate is supported only on the authoritative Drik chart path.',
      ],
    };
  }
  if (options.lagnaAuthorityUncertain) {
    return {
      status: 'unknown',
      evidence: [
        'The local Lagna authority is missing, conflicting, or inside its transition guard.',
      ],
    };
  }
  const d1Rashi = options.authoritativeD1Rashi;
  if (!d1Rashi || !RASI_NAMES.includes(d1Rashi)) {
    return {
      status: 'unknown',
      evidence: ['The authoritative local Drik/Lahiri D1 Lagna Rasi is unavailable.'],
    };
  }
  if (d1Rashi === 'Mesha') {
    return {
      status: 'pass',
      evidence: ['The authoritative local D1 Lagna is Mesha; D9 is not needed.'],
    };
  }

  const lagna = exactLagna(chart);
  if (!lagna) {
    return {
      status: 'unknown',
      evidence: ['Authoritative exact Lagna facts for the D9 alternative are unavailable.'],
    };
  }
  if (lagna.rashi !== d1Rashi) {
    return {
      status: 'unknown',
      evidence: [
        `The sidecar Lagna Rasi ${lagna.rashi} disagrees with authoritative local D1 ${d1Rashi}, so its degree cannot determine D9.`,
      ],
    };
  }

  const d9Rashi = navamsaRashi({
    name: 'Lagna',
    rashi: lagna.rashi,
    degree: lagna.degree,
    house: 1,
    retrograde: false,
  } as PlanetPosition);
  if (d9Rashi === null) {
    return {
      status: 'unknown',
      evidence: [
        'The exact Lagna degree is inside the 0.01-degree Navamsa boundary guard.',
      ],
    };
  }
  if (d9Rashi === 'Mesha') {
    return {
      status: 'pass',
      evidence: [
        `The authoritative local D1 Lagna is ${d1Rashi} and its guarded BPHS-modality D9 is Mesha.`,
      ],
    };
  }
  return {
    status: 'fail',
    evidence: [
      `The authoritative local D1 Lagna is ${d1Rashi} and its guarded BPHS-modality D9 is ${d9Rashi}; neither is Mesha.`,
    ],
  };
}

export function courtMeshaAdmissionKind(
  authoritativeD1Rashi: string | null | undefined,
  d9Outcome: PrimitiveOutcome | null = null,
): 'unavailable' | 'unconditional' | 'provisional' | 'admitted' | 'rejected' {
  if (!authoritativeD1Rashi || !RASI_NAMES.includes(authoritativeD1Rashi)) {
    return 'unavailable';
  }
  if (authoritativeD1Rashi === 'Mesha') return 'unconditional';
  if (!d9Outcome || d9Outcome.status === 'unknown') return 'provisional';
  if (d9Outcome.status === 'pass') return 'admitted';
  if (d9Outcome.status === 'fail') return 'rejected';
  return 'unavailable';
}

function validOutcome(sample: PrimitiveOutcome | undefined): boolean {
  return Boolean(
    sample
    && ['pass', 'fail', 'unknown'].includes(sample.status)
    && Array.isArray(sample.evidence)
    && sample.evidence.every(item => typeof item === 'string'),
  );
}

function validCoverage(
  coverage: CourtMeshaD1D9Coverage | null | undefined,
): coverage is CourtMeshaD1D9Coverage {
  return Boolean(
    coverage && typeof coverage === 'object' && !Array.isArray(coverage)
    && typeof coverage.localLagnaTransitionsComplete === 'boolean'
    && typeof coverage.lagnaNavamsaTransitionsComplete === 'boolean'
    && typeof coverage.budgetExhausted === 'boolean',
  );
}

interface CourtRejectWindowCoverage {
  budgetExhausted: boolean;
  transitions: ReadonlyArray<readonly [string, boolean]>;
}

function humanJoin(items: readonly string[]): string {
  if (items.length < 3) return items.join(' and ');
  return `${items.slice(0, -1).join(', ')}, and ${items.at(-1)}`;
}

function aggregateCourtRejectWindow(
  samples: readonly PrimitiveOutcome[],
  coverage: CourtRejectWindowCoverage | null,
  successEvidence: string,
): PrimitiveOutcome {
  const failed = Array.isArray(samples)
    ? samples.find(sample => sample?.status === 'fail')
    : undefined;
  if (failed) return failed;
  if (
    !Array.isArray(samples)
    || Array.from({ length: samples.length }, (_, index) => samples[index])
      .some(sample => !validOutcome(sample))
  ) {
    return {
      status: 'unknown',
      evidence: ['Represented chart states are malformed or incomplete.'],
    };
  }
  const unknown = samples.find(sample => sample.status === 'unknown');
  if (unknown) return unknown;
  if (!samples.length) {
    return { status: 'unknown', evidence: ['No represented chart states are available.'] };
  }
  if (!coverage) {
    return {
      status: 'unknown',
      evidence: ['Window transition metadata is malformed or incomplete.'],
    };
  }
  if (coverage.budgetExhausted) {
    return {
      status: 'unknown',
      evidence: [
        "The chart-request budget was exhausted before this window's coverage was complete.",
      ],
    };
  }
  const missing = coverage.transitions
    .filter(([, complete]) => !complete)
    .map(([name]) => name);
  if (missing.length) {
    return {
      status: 'unknown',
      evidence: [
        `All represented states pass, but ${humanJoin(missing)} transition coverage is incomplete.`,
      ],
    };
  }
  return { status: 'pass', evidence: [successEvidence] };
}

export function aggregateCourtMeshaD1D9Window(
  samples: readonly PrimitiveOutcome[],
  coverage: CourtMeshaD1D9Coverage,
): PrimitiveOutcome {
  const normalized = validCoverage(coverage) ? {
    budgetExhausted: coverage.budgetExhausted,
    transitions: [
      ['local-Lagna', coverage.localLagnaTransitionsComplete],
      ['Lagna-Navamsa', coverage.lagnaNavamsaTransitionsComplete],
    ] as const,
  } : null;
  return aggregateCourtRejectWindow(
    samples,
    normalized,
    'Every represented state resolves the Court Mesha D1-or-D9 condition as satisfied.',
  );
}

export function evaluateCourtSixthHouseNaturalMalefic(
  chart: ElectionChartSnapshot,
  options: { houseFrameUncertain?: boolean } = {},
): PrimitiveOutcome {
  if (
    options.houseFrameUncertain !== undefined
    && typeof options.houseFrameUncertain !== 'boolean'
  ) {
    return {
      status: 'unknown',
      evidence: ['The Court sixth-house evaluator configuration is malformed.'],
    };
  }
  if (
    !chart || typeof chart !== 'object' || Array.isArray(chart)
    || !Array.isArray(chart.planets)
    || Array.from({ length: chart.planets.length }, (_, index) => chart.planets[index])
      .some(planet => !planet)
  ) {
    return {
      status: 'unknown',
      evidence: ['Complete canonical nine-graha facts are unavailable or invalid.'],
    };
  }
  if (options.houseFrameUncertain) {
    return {
      status: 'unknown',
      evidence: [
        'The validated local-Lagna house frame is unavailable or disagrees with sidecar facts.',
      ],
    };
  }
  return evaluateForbiddenMaleficHouseSet(chart, [6]);
}

export function courtSixthHouseCandidateDisposition(
  outcome: PrimitiveOutcome,
): 'reject' | 'retain' | 'review' {
  if (!outcome || typeof outcome !== 'object' || Array.isArray(outcome)) return 'review';
  if (outcome.status === 'fail') return 'reject';
  if (outcome.status === 'pass') return 'retain';
  return 'review';
}

function validCourtSixthHouseCoverage(
  coverage: CourtSixthHouseNaturalMaleficCoverage | null | undefined,
): coverage is CourtSixthHouseNaturalMaleficCoverage {
  return Boolean(
    coverage && typeof coverage === 'object' && !Array.isArray(coverage)
    && typeof coverage.localLagnaTransitionsComplete === 'boolean'
    && typeof coverage.grahaRasiTransitionsComplete === 'boolean'
    && typeof coverage.chandraPhaseTransitionsComplete === 'boolean'
    && typeof coverage.budhaAssociationTransitionsComplete === 'boolean'
    && typeof coverage.budgetExhausted === 'boolean',
  );
}

export function aggregateCourtSixthHouseNaturalMaleficWindow(
  samples: readonly PrimitiveOutcome[],
  coverage: CourtSixthHouseNaturalMaleficCoverage,
): PrimitiveOutcome {
  const normalized = validCourtSixthHouseCoverage(coverage) ? {
    budgetExhausted: coverage.budgetExhausted,
    transitions: [
      ['local-Lagna', coverage.localLagnaTransitionsComplete],
      ['graha-Rasi', coverage.grahaRasiTransitionsComplete],
      ['Chandra-phase', coverage.chandraPhaseTransitionsComplete],
      ['Budha-association', coverage.budhaAssociationTransitionsComplete],
    ] as const,
  } : null;
  return aggregateCourtRejectWindow(
    samples,
    normalized,
    'Every represented state keeps Whole Sign house 6 free of resolved natural malefics.',
  );
}
