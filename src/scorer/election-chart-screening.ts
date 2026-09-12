import rulesContract from '../data/election-chart-rules.generated.json';
import type { ElectionChartSnapshot } from '../lib/election-chart-api';
import {
  completePlanetPositions,
  evaluateAllPlanetsInHouses,
  evaluateFullAspect,
  evaluateHouseFreeOfNaturalMalefics,
  evaluateWellSituated,
  GOLD_MAX_SAMPLE_GAP_MINUTES,
  goldTransitionUncertainty,
  type PrimitiveOutcome,
} from './election-assessors/primitives';
import {
  aggregateCourtGuruTrikonaWindow,
  evaluateCourtGuruTrikona,
} from './election-assessors/chart-geometry';
import {
  aggregateCourtLagnaSixthLordSeparationWindow,
  aggregateCourtMeshaD1D9Window,
  aggregateCourtPeacePatternWindow,
  aggregateCourtSixthHouseNaturalMaleficWindow,
  evaluateCourtLagnaSixthLordSeparation,
  evaluateCourtMeshaD1D9,
  evaluateCourtPeacePattern,
  evaluateCourtSixthHouseNaturalMalefic,
} from './election-assessors/court';

export type ElectionRuleStatus = 'pass' | 'fail' | 'unknown';
export type ElectionRuleEffect = 'reject' | 'qualify' | 'prefer' | 'inform';

export interface ElectionChartRule {
  id: string;
  label: string;
  kind:
    | 'house_empty'
    | 'planet_not_house'
    | 'planet_in_houses'
    | 'any_planet_in_houses'
    | 'all_planets_in_houses'
    | 'planet_well_situated'
    | 'planet_receives_full_aspect'
    | 'house_free_of_natural_malefics'
    | 'court_mesha_d1_d9'
    | 'court_guru_trikona'
    | 'court_no_natural_malefic_h6'
    | 'court_lagna_sixth_lord_separation'
    | 'court_peace_pattern';
  effect: ElectionRuleEffect;
  source_claim: string;
  source_locator: string;
  house?: number;
  houses?: number[];
  planet?: string;
  planets?: string[];
  avoid_houses?: number[];
  enemy_rashis?: string[];
  debilitation_rashi?: string;
  navamsa_debilitation_rashi?: string;
  aspectors?: string[];
  solar_clearance_degrees?: number;
  solar_clearance_guard_degrees?: number;
  fixed_malefics?: string[];
  lunar_phase_guard_degrees?: number;
  convention_id?: string;
  convention_label?: string;
  formula?: string;
  method_claims?: string[];
  decision_policy_claim?: string;
}

export interface ElectionRuleOutcome {
  ruleId: string;
  label: string;
  effect: ElectionRuleEffect;
  sourceClaim: string;
  sourceLocator: string;
  status: ElectionRuleStatus;
  evidence: string[];
  conventionId?: string;
  conventionLabel?: string;
  formula?: string;
  methodClaims?: string[];
  decisionPolicyClaim?: string;
}

export interface ElectionChartScreening {
  outcomes: ElectionRuleOutcome[];
  rejected: boolean;
  needsReview: boolean;
  preferencePasses: number;
  qualificationFailed: boolean;
  stable: boolean;
  boundaryConventionUncertain?: boolean;
}

export interface ElectionChartEvaluationOptions {
  houseFrameUncertain?: boolean;
  authoritativeLagnaRashi?: string | null;
  authoritativeLagnaRashis?: Array<string | null>;
  lagnaAuthorityUncertain?: boolean;
  supportedSystem?: boolean;
  courtTransitionCoverage?: CourtTransitionCoverage;
}

export interface CourtTransitionCoverage {
  localLagnaTransitionsComplete: boolean;
  lagnaNavamsaTransitionsComplete: boolean;
  guruRasiTransitionsComplete: boolean;
  grahaRasiTransitionsComplete: boolean;
  chandraPhaseTransitionsComplete: boolean;
  budhaAssociationTransitionsComplete: boolean;
  lagnaLordRasiTransitionsComplete: boolean;
  sixthLordRasiTransitionsComplete: boolean;
  fullAspectTransitionsComplete: boolean;
  budgetExhausted: boolean;
}

const EXPECTED_PLANETS = new Set(rulesContract.vacancy_includes);
const RULES = rulesContract.rules as unknown as Record<string, ElectionChartRule[]>;
const MANUAL_REMAINDERS = rulesContract.manual_remainders as unknown as Record<string, string[]>;
const COMPLETE_ASSESSORS = new Set(
  rulesContract.complete_assessors as unknown as string[],
);

export function automatedRulesFor(activity: string): readonly ElectionChartRule[] {
  return RULES[activity === 'litigation' ? 'court' : activity] || [];
}

export function chartManualRemaindersFor(activity: string): readonly string[] | null {
  activity = activity === 'litigation' ? 'court' : activity;
  return Object.hasOwn(MANUAL_REMAINDERS, activity)
    ? MANUAL_REMAINDERS[activity]
    : null;
}

export function chartAssessorCompleteFor(activity: string): boolean {
  return COMPLETE_ASSESSORS.has(activity === 'litigation' ? 'court' : activity);
}

function evaluateHouseEmpty(
  rule: ElectionChartRule,
  houses: ReadonlyMap<string, number>,
): PrimitiveOutcome {
  const occupants = Array.from(houses.entries())
    .filter(([, house]) => house === rule.house)
    .map(([name]) => name);
  return {
    status: occupants.length === 0 ? 'pass' : 'fail',
    evidence: [`House ${rule.house} occupants: ${occupants.length ? occupants.join(', ') : 'none'}.`],
  };
}

function evaluatePlanetNotHouse(
  rule: ElectionChartRule,
  houses: ReadonlyMap<string, number>,
): PrimitiveOutcome {
  const observed = houses.get(rule.planet as string) as number;
  const passed = observed !== rule.house;
  return {
    status: passed ? 'pass' : 'fail',
    evidence: [`${rule.planet} occupies house ${observed}${passed
      ? `, outside house ${rule.house}.`
      : ', which is prohibited.'}`],
  };
}

function evaluatePlanetInHouses(
  rule: ElectionChartRule,
  houses: ReadonlyMap<string, number>,
): PrimitiveOutcome {
  const observed = houses.get(rule.planet as string) as number;
  return {
    status: (rule.houses || []).includes(observed) ? 'pass' : 'fail',
    evidence: [`${rule.planet} occupies house ${observed}; target houses: ${(rule.houses || []).join(', ')}.`],
  };
}

function anyPlanetEvidence(rule: ElectionChartRule, matching: readonly string[]): string {
  if ((rule.houses || []).length === 1 && rule.houses?.[0] === 1) {
    const planets = rule.planets || [];
    const named = planets.length > 1
      ? `${planets.slice(0, -1).join(', ')} and ${planets.at(-1)}`
      : planets.join('');
    return `Lagna occupants among ${named}: ${matching.length ? matching.join(', ') : 'none'}.`;
  }
  return `Matching grahas: ${matching.length ? matching.join(', ') : 'none'}; target houses: ${(rule.houses || []).join(', ')}.`;
}

function evaluateAnyPlanetInHouses(
  rule: ElectionChartRule,
  houses: ReadonlyMap<string, number>,
): PrimitiveOutcome {
  const matching = (rule.planets || []).filter(planet =>
    (rule.houses || []).includes(houses.get(planet) as number));
  return {
    status: matching.length > 0 ? 'pass' : 'fail',
    evidence: [anyPlanetEvidence(rule, matching)],
  };
}

function evaluateHouseRule(
  rule: ElectionChartRule,
  houses: ReadonlyMap<string, number>,
): PrimitiveOutcome {
  if (rule.kind === 'house_empty') return evaluateHouseEmpty(rule, houses);
  if (rule.kind === 'planet_not_house') return evaluatePlanetNotHouse(rule, houses);
  if (rule.kind === 'planet_in_houses') return evaluatePlanetInHouses(rule, houses);
  if (rule.kind === 'any_planet_in_houses') return evaluateAnyPlanetInHouses(rule, houses);
  return {
    status: 'unknown',
    evidence: [`Unsupported election-chart rule kind: ${String(rule.kind)}.`],
  };
}

function evaluateRule(
  rule: ElectionChartRule,
  chart: ElectionChartSnapshot,
  houses: ReadonlyMap<string, number> | null,
  positions: ReturnType<typeof completePlanetPositions>,
  options: ElectionChartEvaluationOptions,
): PrimitiveOutcome {
  if (rule.kind === 'court_mesha_d1_d9') {
    return evaluateCourtMeshaD1D9(chart, {
      authoritativeD1Rashi: options.authoritativeLagnaRashi,
      lagnaAuthorityUncertain: options.lagnaAuthorityUncertain,
      supportedSystem: options.supportedSystem,
    });
  }
  if (rule.kind === 'court_guru_trikona') {
    return evaluateCourtGuruTrikona(chart, options);
  }
  if (rule.kind === 'court_no_natural_malefic_h6') {
    return evaluateCourtSixthHouseNaturalMalefic(chart, options);
  }
  if (rule.kind === 'court_lagna_sixth_lord_separation') {
    return evaluateCourtLagnaSixthLordSeparation(chart, {
      authoritativeLagnaRashi: options.authoritativeLagnaRashi,
      lagnaAuthorityUncertain: options.lagnaAuthorityUncertain,
    });
  }
  if (rule.kind === 'court_peace_pattern') {
    return evaluateCourtPeacePattern(chart, options);
  }
  if (rule.kind === 'planet_well_situated') {
    return evaluateWellSituated(rule, positions, options);
  }
  if (rule.kind === 'planet_receives_full_aspect') {
    return evaluateFullAspect(rule, positions);
  }
  if (rule.kind === 'house_free_of_natural_malefics') {
    return evaluateHouseFreeOfNaturalMalefics(rule, positions, options);
  }
  if (rule.kind === 'all_planets_in_houses') {
    return evaluateAllPlanetsInHouses(rule, houses, options);
  }
  if (!houses || options.houseFrameUncertain) {
    return {
      status: 'unknown',
      evidence: ['Complete Whole Sign house facts are unavailable.'],
    };
  }
  return evaluateHouseRule(rule, houses);
}

function ruleOutcome(
  rule: ElectionChartRule,
  result: PrimitiveOutcome,
): ElectionRuleOutcome {
  return {
    ruleId: rule.id,
    label: rule.label,
    effect: rule.effect,
    sourceClaim: rule.source_claim,
    sourceLocator: rule.source_locator,
    status: result.status,
    evidence: result.evidence,
    ...(rule.convention_id ? { conventionId: rule.convention_id } : {}),
    ...(rule.convention_label ? { conventionLabel: rule.convention_label } : {}),
    ...(rule.formula ? { formula: rule.formula } : {}),
    ...(rule.method_claims ? { methodClaims: rule.method_claims } : {}),
    ...(rule.decision_policy_claim
      ? { decisionPolicyClaim: rule.decision_policy_claim }
      : {}),
  };
}

function summarize(outcomes: ElectionRuleOutcome[], stable = true): ElectionChartScreening {
  return {
    outcomes,
    rejected: outcomes.some(outcome => outcome.effect === 'reject' && outcome.status === 'fail'),
    needsReview: outcomes.some(outcome => outcome.status === 'unknown'),
    preferencePasses: outcomes.filter(
      outcome => outcome.effect === 'prefer' && outcome.status === 'pass',
    ).length,
    qualificationFailed: outcomes.some(
      outcome => outcome.effect === 'qualify' && outcome.status === 'fail',
    ),
    stable,
  };
}

type PlanetPositions = NonNullable<ReturnType<typeof completePlanetPositions>>;

function recordMissingGoldCoverage(evidence: Map<string, string[]>): void {
  for (const rule of automatedRulesFor('gold')) {
    const details = evidence.get(rule.id) || [];
    details.push('The chart instants do not prove the required ten-minute transition coverage.');
    evidence.set(rule.id, details);
  }
}

function recordGoldTransitionUncertainty(
  evidence: Map<string, string[]>,
  startPositions: PlanetPositions,
  endPositions: PlanetPositions,
  gapMinutes: number,
): void {
  for (const rule of automatedRulesFor('gold')) {
    const detail = goldTransitionUncertainty(rule, startPositions, endPositions, gapMinutes);
    if (!detail) continue;
    const details = evidence.get(rule.id) || [];
    if (!details.includes(detail)) details.push(detail);
    evidence.set(rule.id, details);
  }
}

function validGoldTransitionGap(gapMinutes: number): boolean {
  return Number.isFinite(gapMinutes)
    && gapMinutes > 0
    && gapMinutes <= GOLD_MAX_SAMPLE_GAP_MINUTES;
}

function goldTransitionEvidence(
  charts: readonly ElectionChartSnapshot[],
): ReadonlyMap<string, string[]> {
  const evidence = new Map<string, string[]>();
  for (let index = 1; index < charts.length; index += 1) {
    const startChart = charts[index - 1];
    const endChart = charts[index];
    const startPositions = completePlanetPositions(startChart, EXPECTED_PLANETS);
    const endPositions = completePlanetPositions(endChart, EXPECTED_PLANETS);
    if (!startPositions || !endPositions) continue;
    const gapMinutes = (Date.parse(endChart.instant) - Date.parse(startChart.instant)) / 60_000;
    if (validGoldTransitionGap(gapMinutes)) {
      recordGoldTransitionUncertainty(evidence, startPositions, endPositions, gapMinutes);
    } else {
      recordMissingGoldCoverage(evidence);
    }
  }
  return evidence;
}

function combinedRuleStatus(
  effect: ElectionRuleEffect,
  statuses: readonly ElectionRuleStatus[],
): ElectionRuleStatus {
  if ((effect === 'reject' || effect === 'qualify') && statuses.includes('fail')) return 'fail';
  if (statuses.includes('unknown')) return 'unknown';
  if (effect === 'reject') return 'pass';
  if (statuses.every(value => value === 'pass')) return 'pass';
  if (statuses.every(value => value === 'fail')) return 'fail';
  return 'unknown';
}

const INCOMPLETE_COURT_COVERAGE: CourtTransitionCoverage = {
  localLagnaTransitionsComplete: false,
  lagnaNavamsaTransitionsComplete: false,
  guruRasiTransitionsComplete: false,
  grahaRasiTransitionsComplete: false,
  chandraPhaseTransitionsComplete: false,
  budhaAssociationTransitionsComplete: false,
  lagnaLordRasiTransitionsComplete: false,
  sixthLordRasiTransitionsComplete: false,
  fullAspectTransitionsComplete: false,
  budgetExhausted: false,
};

function aggregateCourtRule(
  ruleId: string,
  samples: readonly PrimitiveOutcome[],
  coverage: CourtTransitionCoverage,
): PrimitiveOutcome {
  const shared = {
    localLagnaTransitionsComplete: coverage.localLagnaTransitionsComplete,
    budgetExhausted: coverage.budgetExhausted,
  };
  if (ruleId === 'court.mesha-lagna-or-navamsa') {
    return aggregateCourtMeshaD1D9Window(samples, {
      ...shared,
      lagnaNavamsaTransitionsComplete: coverage.lagnaNavamsaTransitionsComplete,
    });
  }
  if (ruleId === 'court.guru-trikona') {
    return aggregateCourtGuruTrikonaWindow(samples, {
      ...shared,
      guruRasiTransitionsComplete: coverage.guruRasiTransitionsComplete,
    });
  }
  if (ruleId === 'court.house-6-without-natural-malefic') {
    return aggregateCourtSixthHouseNaturalMaleficWindow(samples, {
      ...shared,
      grahaRasiTransitionsComplete: coverage.grahaRasiTransitionsComplete,
      chandraPhaseTransitionsComplete: coverage.chandraPhaseTransitionsComplete,
      budhaAssociationTransitionsComplete:
        coverage.budhaAssociationTransitionsComplete,
    });
  }
  if (ruleId === 'court.lagna-sixth-lords-max-separated') {
    return aggregateCourtLagnaSixthLordSeparationWindow(samples, {
      ...shared,
      lagnaLordRasiTransitionsComplete:
        coverage.lagnaLordRasiTransitionsComplete,
      sixthLordRasiTransitionsComplete:
        coverage.sixthLordRasiTransitionsComplete,
    });
  }
  return aggregateCourtPeacePatternWindow(samples, {
    ...shared,
    grahaRasiTransitionsComplete: coverage.grahaRasiTransitionsComplete,
    chandraPhaseTransitionsComplete: coverage.chandraPhaseTransitionsComplete,
    budhaAssociationTransitionsComplete:
      coverage.budhaAssociationTransitionsComplete,
    fullAspectTransitionsComplete: coverage.fullAspectTransitionsComplete,
  });
}

function evaluateCourtWindowOutcomes(
  evaluations: readonly ElectionChartScreening[],
  suppliedCoverage: CourtTransitionCoverage | undefined,
): ElectionChartScreening {
  const coverage = suppliedCoverage || INCOMPLETE_COURT_COVERAGE;
  const first = evaluations[0];
  let stable = true;
  const outcomes = first.outcomes.map(firstOutcome => {
    const matching = evaluations.map(result => result.outcomes.find(
      outcome => outcome.ruleId === firstOutcome.ruleId,
    ));
    const samples = matching.map(item => ({
      status: item?.status || 'unknown',
      evidence: item?.evidence || [],
    }) as PrimitiveOutcome);
    const result = aggregateCourtRule(firstOutcome.ruleId, samples, coverage);
    stable &&= result.status !== 'unknown'
      && samples.every(sample => sample.status === samples[0].status);
    return { ...firstOutcome, status: result.status, evidence: result.evidence };
  });
  return summarize(outcomes, stable);
}

export function evaluateElectionChart(
  activity: string,
  chart: ElectionChartSnapshot,
  options: ElectionChartEvaluationOptions = {},
): ElectionChartScreening {
  const positions = completePlanetPositions(chart, EXPECTED_PLANETS);
  const houses = positions
    ? new Map(Array.from(positions, ([name, position]) => [name, position.house]))
    : null;
  return summarize(automatedRulesFor(activity).map(rule =>
    ruleOutcome(rule, evaluateRule(rule, chart, houses, positions, options))));
}

export function evaluateElectionWindow(
  activity: string,
  startChart: ElectionChartSnapshot,
  endChart: ElectionChartSnapshot,
): ElectionChartScreening {
  return evaluateElectionSnapshots(activity, [startChart, endChart]);
}

/** Conservatively combine every sampled state inside one offered window. */
export function evaluateElectionSnapshots(
  activity: string,
  charts: readonly ElectionChartSnapshot[],
  options: ElectionChartEvaluationOptions = {},
): ElectionChartScreening {
  activity = activity === 'litigation' ? 'court' : activity;
  if (!charts.length) {
    return summarize(automatedRulesFor(activity).map(rule =>
      ruleOutcome(rule, { status: 'unknown', evidence: [] })), false);
  }
  const lagnaRashis = options.authoritativeLagnaRashis;
  const evaluations = charts.map((chart, index) => evaluateElectionChart(
    activity,
    chart,
    {
      ...options,
      authoritativeLagnaRashi: lagnaRashis?.length === charts.length
        ? lagnaRashis[index]
        : options.authoritativeLagnaRashi,
    },
  ));
  if (activity === 'court') {
    return evaluateCourtWindowOutcomes(evaluations, options.courtTransitionCoverage);
  }
  const first = evaluations[0];
  const transitionEvidence = activity === 'gold'
    ? goldTransitionEvidence(charts)
    : new Map<string, string[]>();
  let stable = true;
  const outcomes = first.outcomes.map(firstOutcome => {
    const statuses = evaluations.map(result =>
      result.outcomes.find(outcome => outcome.ruleId === firstOutcome.ruleId)?.status
      || 'unknown');
    if (!statuses.every(status => status === statuses[0])) stable = false;
    let status = combinedRuleStatus(firstOutcome.effect, statuses);
    const extraEvidence = transitionEvidence.get(firstOutcome.ruleId) || [];
    const transitionApplied = status === 'pass' && extraEvidence.length > 0;
    if (transitionApplied) {
      status = 'unknown';
      stable = false;
    }
    const evidence = evaluations
      .map(result => result.outcomes.find(
        outcome => outcome.ruleId === firstOutcome.ruleId))
      .filter((outcome): outcome is ElectionRuleOutcome =>
        !!outcome && outcome.status === status)
      .flatMap(outcome => outcome.evidence)
      .filter((detail, index, all) => all.indexOf(detail) === index)
      .concat(transitionApplied ? extraEvidence : [])
      .filter((detail, index, all) => all.indexOf(detail) === index)
      .slice(0, 3);
    return { ...firstOutcome, status, evidence };
  });
  return summarize(outcomes, stable);
}
