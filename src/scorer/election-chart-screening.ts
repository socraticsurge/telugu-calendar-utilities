import rulesContract from '../data/election-chart-rules.generated.json';
import type { ElectionChartSnapshot } from '../lib/election-chart-api';

export type ElectionRuleStatus = 'pass' | 'fail' | 'unknown';
export type ElectionRuleEffect = 'reject' | 'prefer';

export interface ElectionChartRule {
  id: string;
  label: string;
  kind: 'house_empty' | 'planet_not_house' | 'planet_in_houses' | 'any_planet_in_houses';
  effect: ElectionRuleEffect;
  source_claim: string;
  source_locator: string;
  house?: number;
  houses?: number[];
  planet?: string;
  planets?: string[];
}

export interface ElectionRuleOutcome {
  ruleId: string;
  label: string;
  effect: ElectionRuleEffect;
  sourceClaim: string;
  sourceLocator: string;
  status: ElectionRuleStatus;
}

export interface ElectionChartScreening {
  outcomes: ElectionRuleOutcome[];
  rejected: boolean;
  needsReview: boolean;
  preferencePasses: number;
  stable: boolean;
  boundaryConventionUncertain?: boolean;
}

const EXPECTED_PLANETS = new Set(rulesContract.vacancy_includes);
const RULES = rulesContract.rules as unknown as Record<string, ElectionChartRule[]>;
const MANUAL_REMAINDERS = rulesContract.manual_remainders as unknown as Record<string, string[]>;

export function automatedRulesFor(activity: string): readonly ElectionChartRule[] {
  return RULES[activity] || [];
}

export function chartManualRemaindersFor(activity: string): readonly string[] | null {
  return Object.hasOwn(MANUAL_REMAINDERS, activity)
    ? MANUAL_REMAINDERS[activity]
    : null;
}

function completePlanetHouses(chart: ElectionChartSnapshot): Map<string, number> | null {
  if (chart.planets.length !== EXPECTED_PLANETS.size) return null;
  const result = new Map<string, number>();
  for (const planet of chart.planets) {
    if (!EXPECTED_PLANETS.has(planet.name) || result.has(planet.name)) return null;
    result.set(planet.name, planet.house);
  }
  return result.size === EXPECTED_PLANETS.size ? result : null;
}

function evaluateRule(
  rule: ElectionChartRule,
  houses: ReadonlyMap<string, number> | null,
): ElectionRuleStatus {
  if (!houses) return 'unknown';
  let passed: boolean;
  if (rule.kind === 'house_empty') {
    passed = !Array.from(houses.values()).includes(rule.house as number);
  } else if (rule.kind === 'planet_not_house') {
    passed = houses.get(rule.planet as string) !== rule.house;
  } else if (rule.kind === 'planet_in_houses') {
    passed = (rule.houses || []).includes(houses.get(rule.planet as string) as number);
  } else {
    passed = (rule.planets || []).some(planet =>
      (rule.houses || []).includes(houses.get(planet) as number));
  }
  return passed ? 'pass' : 'fail';
}

function summarize(outcomes: ElectionRuleOutcome[], stable = true): ElectionChartScreening {
  return {
    outcomes,
    rejected: outcomes.some(outcome => outcome.effect === 'reject' && outcome.status === 'fail'),
    needsReview: outcomes.some(outcome => outcome.status === 'unknown'),
    preferencePasses: outcomes.filter(
      outcome => outcome.effect === 'prefer' && outcome.status === 'pass',
    ).length,
    stable,
  };
}

export function evaluateElectionChart(
  activity: string,
  chart: ElectionChartSnapshot,
): ElectionChartScreening {
  const houses = completePlanetHouses(chart);
  return summarize(automatedRulesFor(activity).map(rule => ({
    ruleId: rule.id,
    label: rule.label,
    effect: rule.effect,
    sourceClaim: rule.source_claim,
    sourceLocator: rule.source_locator,
    status: evaluateRule(rule, houses),
  })));
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
): ElectionChartScreening {
  if (!charts.length) {
    return summarize(automatedRulesFor(activity).map(rule => ({
      ruleId: rule.id,
      label: rule.label,
      effect: rule.effect,
      sourceClaim: rule.source_claim,
      sourceLocator: rule.source_locator,
      status: 'unknown' as const,
    })), false);
  }
  const evaluations = charts.map(chart => evaluateElectionChart(activity, chart));
  const first = evaluations[0];
  let stable = true;
  const outcomes = first.outcomes.map(firstOutcome => {
    const statuses = evaluations.map(result =>
      result.outcomes.find(outcome => outcome.ruleId === firstOutcome.ruleId)?.status
      || 'unknown');
    if (!statuses.every(status => status === statuses[0])) stable = false;
    let status: ElectionRuleStatus;
    if (statuses.includes('unknown')) {
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
    return { ...firstOutcome, status };
  });
  return summarize(outcomes, stable);
}
