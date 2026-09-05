import rulesContract from '../data/election-chart-rules.generated.json';
import type { ElectionChartSnapshot } from '../lib/election-chart-api';
import {
  completePlanetPositions,
  evaluateAllPlanetsInHouses,
  evaluateFullAspect,
  evaluateWellSituated,
  GOLD_MAX_SAMPLE_GAP_MINUTES,
  goldTransitionUncertainty,
  type PrimitiveOutcome,
} from './election-assessors/primitives';

export type ElectionRuleStatus = 'pass' | 'fail' | 'unknown';
export type ElectionRuleEffect = 'reject' | 'qualify' | 'prefer';

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
    | 'planet_receives_full_aspect';
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
}

const EXPECTED_PLANETS = new Set(rulesContract.vacancy_includes);
const RULES = rulesContract.rules as unknown as Record<string, ElectionChartRule[]>;
const MANUAL_REMAINDERS = rulesContract.manual_remainders as unknown as Record<string, string[]>;
const COMPLETE_ASSESSORS = new Set(
  rulesContract.complete_assessors as unknown as string[],
);

export function automatedRulesFor(activity: string): readonly ElectionChartRule[] {
  return RULES[activity] || [];
}

export function chartManualRemaindersFor(activity: string): readonly string[] | null {
  return Object.hasOwn(MANUAL_REMAINDERS, activity)
    ? MANUAL_REMAINDERS[activity]
    : null;
}

export function chartAssessorCompleteFor(activity: string): boolean {
  return COMPLETE_ASSESSORS.has(activity);
}

function completePlanetHouses(chart: ElectionChartSnapshot): Map<string, number> | null {
  if (chart.planets.length !== EXPECTED_PLANETS.size) return null;
  const result = new Map<string, number>();
  for (const planet of chart.planets) {
    if (
      !EXPECTED_PLANETS.has(planet.name) || result.has(planet.name)
      || !Number.isInteger(planet.house) || planet.house < 1 || planet.house > 12
    ) return null;
    result.set(planet.name, planet.house);
  }
  return result.size === EXPECTED_PLANETS.size ? result : null;
}

function evaluateRule(
  rule: ElectionChartRule,
  houses: ReadonlyMap<string, number> | null,
  positions: ReturnType<typeof completePlanetPositions>,
  options: ElectionChartEvaluationOptions,
): PrimitiveOutcome {
  if (rule.kind === 'planet_well_situated') {
    return evaluateWellSituated(rule, positions, options);
  }
  if (rule.kind === 'planet_receives_full_aspect') {
    return evaluateFullAspect(rule, positions);
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
  let passed: boolean;
  let evidence: string[];
  if (rule.kind === 'house_empty') {
    const occupants = Array.from(houses.entries())
      .filter(([, house]) => house === rule.house)
      .map(([name]) => name);
    passed = occupants.length === 0;
    evidence = [
      `House ${rule.house} occupants: ${occupants.length ? occupants.join(', ') : 'none'}.`,
    ];
  } else if (rule.kind === 'planet_not_house') {
    const observed = houses.get(rule.planet as string) as number;
    passed = observed !== rule.house;
    evidence = [
      `${rule.planet} occupies house ${observed}${passed
        ? `, outside house ${rule.house}.`
        : ', which is prohibited.'}`,
    ];
  } else if (rule.kind === 'planet_in_houses') {
    const observed = houses.get(rule.planet as string) as number;
    passed = (rule.houses || []).includes(observed);
    evidence = [
      `${rule.planet} occupies house ${observed}; target houses: ${(rule.houses || []).join(', ')}.`,
    ];
  } else if (rule.kind === 'any_planet_in_houses') {
    const matching = (rule.planets || []).filter(planet =>
      (rule.houses || []).includes(houses.get(planet) as number));
    passed = matching.length > 0;
    evidence = [
      `Matching grahas: ${matching.length ? matching.join(', ') : 'none'}; target houses: ${(rule.houses || []).join(', ')}.`,
    ];
  } else {
    return {
      status: 'unknown',
      evidence: [`Unsupported election-chart rule kind: ${String(rule.kind)}.`],
    };
  }
  return { status: passed ? 'pass' : 'fail', evidence };
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
    const startInstant = Date.parse(startChart.instant);
    const endInstant = Date.parse(endChart.instant);
    const gapMinutes = (endInstant - startInstant) / 60_000;
    if (
      !Number.isFinite(gapMinutes)
      || gapMinutes <= 0
      || gapMinutes > GOLD_MAX_SAMPLE_GAP_MINUTES
    ) {
      for (const rule of automatedRulesFor('gold')) {
        const details = evidence.get(rule.id) || [];
        details.push(
          'The chart instants do not prove the required ten-minute transition coverage.',
        );
        evidence.set(rule.id, details);
      }
      continue;
    }
    for (const rule of automatedRulesFor('gold')) {
      const detail = goldTransitionUncertainty(
        rule, startPositions, endPositions, gapMinutes,
      );
      if (!detail) continue;
      const details = evidence.get(rule.id) || [];
      if (!details.includes(detail)) details.push(detail);
      evidence.set(rule.id, details);
    }
  }
  return evidence;
}

export function evaluateElectionChart(
  activity: string,
  chart: ElectionChartSnapshot,
  options: ElectionChartEvaluationOptions = {},
): ElectionChartScreening {
  const houses = completePlanetHouses(chart);
  const positions = completePlanetPositions(chart, EXPECTED_PLANETS);
  return summarize(automatedRulesFor(activity).map(rule =>
    ruleOutcome(rule, evaluateRule(rule, houses, positions, options))));
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
  if (!charts.length) {
    return summarize(automatedRulesFor(activity).map(rule =>
      ruleOutcome(rule, { status: 'unknown', evidence: [] })), false);
  }
  const evaluations = charts.map(chart => evaluateElectionChart(activity, chart, options));
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
    let status: ElectionRuleStatus;
    if (
      (firstOutcome.effect === 'reject' || firstOutcome.effect === 'qualify')
      && statuses.includes('fail')
    ) {
      status = 'fail';
    } else if (statuses.includes('unknown')) {
      status = 'unknown';
    } else if (firstOutcome.effect === 'reject') {
      status = statuses.includes('fail') ? 'fail' : 'pass';
    } else if (statuses.every(value => value === 'pass')) {
      status = 'pass';
    } else if (statuses.every(value => value === 'fail')) {
      status = 'fail';
    } else {
      status = 'unknown';
    }
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
