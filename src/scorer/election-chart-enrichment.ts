import {
  deriveElectionCharts,
  ElectionChartApiError,
  localWallTimeToInstant,
  type ElectionChartApiOptions,
  type ElectionChartDerivation,
  type ElectionChartLocation,
  type ElectionChartRequest,
} from '../lib/election-chart-api';
import { NAKSHATRA_NAMES, RASI_NAMES } from '../data/rasis';
import {
  electionChartCalculationEnabled,
  type ElectionChartLocation as ElectionChartBrowserLocation,
} from '../lib/remote-calculation-activation';
import {
  automatedRulesFor,
  evaluateElectionSnapshots,
  type ElectionChartScreening,
} from './election-chart-screening';
import {
  evaluatePersonalElectionSnapshots,
  roleForActivity,
  type PersonalElectionFacts,
  type PersonalElectionParticipant,
} from './personal-election-screening';

export interface EnrichableMuhurtamSlot {
  isoDate: string;
  s0: number;
  e0: number;
  score: number;
  tier: string;
  dayDosha: string | null;
  personalDosha?: string | null;
  reasonGroups: Record<string, unknown>;
  personalPreferencePasses?: number;
  chartScreening?: ElectionChartScreening;
  chartCheckMinutes?: number[];
  chartCheckLagnas?: Array<string | null> | null;
  chartBoundarySupported?: boolean;
  chartBoundaryNeedsReview?: boolean;
}

export type ElectionChartEnrichmentState =
  | 'screened'
  | 'not-run'
  | 'manual-only'
  | 'unsupported-system'
  | 'disabled'
  | 'unavailable';

export interface ElectionChartEnrichment<TSlot extends EnrichableMuhurtamSlot> {
  state: ElectionChartEnrichmentState;
  slots: TSlot[];
  screenedCount: number;
  removedCount: number;
  candidateLimitReached: boolean;
  chartRemovedCount: number;
  chartRemovedRules: Array<{
    ruleId: string;
    label: string;
    count: number;
    evidence: string[];
  }>;
  personalRemovedCount: number;
  personalRemovedRules: Array<{ ruleId: string; label: string; count: number }>;
  boundaryReviewCount: number;
  qualificationCappedCount: number;
  reviewGatedCount: number;
  overlappingDispositionCount: number;
  message: string;
  engine: ElectionChartDerivation['engine'] | null;
}

type DeriveElectionCharts = (
  input: ElectionChartRequest,
  options?: ElectionChartApiOptions,
) => Promise<ElectionChartDerivation>;

export interface ElectionChartEnrichmentOptions {
  activity: string;
  system: string;
  location: ElectionChartLocation;
  derive?: DeriveElectionCharts;
  signal?: AbortSignal;
  personalParticipant?: PersonalElectionParticipant | null;
  boundarySupportAvailable?: boolean;
  screeningTimeoutMs?: number;
  activationFlag?: string;
  locationLike?: ElectionChartBrowserLocation;
}

const MAX_INSTANTS_PER_REQUEST = 24;
const MAX_CHART_REQUESTS = 5;
const DEFAULT_SCREENING_TIMEOUT_MS = 20_000;
const RESULT_LIMIT = 10;
const TIER_RANK: Record<string, number> = {
  Excellent: 3,
  Good: 2,
  Fair: 1,
  Avoid: 0,
};
const NAKSHATRA_SPAN_DEGREES = 360 / 27;
const DISPLAYED_DEGREE_HALF_STEP = 0.005;

function rank<TSlot extends EnrichableMuhurtamSlot>(slots: TSlot[]): TSlot[] {
  return [...slots].sort((left, right) =>
    (TIER_RANK[right.tier] ?? -1) - (TIER_RANK[left.tier] ?? -1)
    || right.score - left.score
    || (right.personalPreferencePasses || 0) - (left.personalPreferencePasses || 0)
    || (right.chartScreening?.preferencePasses || 0)
      - (left.chartScreening?.preferencePasses || 0)
    || Number(!!left.personalDosha) - Number(!!right.personalDosha)
    || left.isoDate.localeCompare(right.isoDate)
    || left.s0 - right.s0);
}

function mergeEngineProvenance(
  current: ElectionChartDerivation['engine'] | null,
  next: ElectionChartDerivation['engine'],
): ElectionChartDerivation['engine'] {
  if (!current) return { ...next };
  if (
    current.name !== next.name
    || current.version !== next.version
    || current.ayanamsha !== next.ayanamsha
    || current.nodeConvention !== next.nodeConvention
  ) {
    throw new ElectionChartApiError(
      'invalid-response',
      'Chart screening batches returned incompatible calculation provenance.',
    );
  }
  return {
    ...current,
    ephemeris: current.ephemeris === next.ephemeris ? current.ephemeris : 'mixed',
  };
}

function chandraNakshatraBoundaryUncertain(longitude: number, rashiIndex: number): boolean {
  const rashiStart = rashiIndex * 30;
  const rashiEnd = rashiStart + 30;
  for (let boundaryIndex = 1; boundaryIndex < 27; boundaryIndex += 1) {
    const boundary = boundaryIndex * NAKSHATRA_SPAN_DEGREES;
    if (boundary <= rashiStart || boundary >= rashiEnd) continue;
    if (Math.abs(longitude - boundary) <= DISPLAYED_DEGREE_HALF_STEP + 1e-9) {
      return true;
    }
  }
  return false;
}

function exactPersonalFacts(
  chart: ElectionChartDerivation['charts'][number],
  canonicalLagna: string,
): PersonalElectionFacts {
  const chandra = chart.planets.find(planet => planet.name === 'Chandra');
  const rashiIndex = chandra ? RASI_NAMES.indexOf(chandra.rashi) : -1;
  const longitude = rashiIndex >= 0 && chandra
    ? rashiIndex * 30 + chandra.degree
    : null;
  const nakshatra = longitude === null
    || chandraNakshatraBoundaryUncertain(longitude, rashiIndex)
    ? ''
    : NAKSHATRA_NAMES[Math.floor(longitude / (360 / 27)) % 27] || '';
  return {
    nakshatra,
    lunarRashi: chandra?.rashi || null,
    lagna: canonicalLagna,
  };
}

/**
 * Project Whole Sign houses in the same validated Lagna frame used by the
 * browser's Drik shortlist. The sidecar's planetary Rashi/degree remains the
 * astronomical input; its house numbers are deliberately not trusted across
 * known ascendant-boundary convention differences.
 */
export function projectCanonicalWholeSignHouses(
  chart: ElectionChartDerivation['charts'][number],
  canonicalLagna: string,
): ElectionChartDerivation['charts'][number] {
  const lagnaIndex = RASI_NAMES.indexOf(canonicalLagna);
  if (lagnaIndex < 0) throw new Error('Invalid canonical Lagna frame.');
  return {
    ...chart,
    planets: chart.planets.map(planet => {
      const planetIndex = RASI_NAMES.indexOf(planet.rashi);
      if (planetIndex < 0) throw new Error('Invalid planetary Rashi.');
      return {
        ...planet,
        house: ((planetIndex - lagnaIndex + RASI_NAMES.length) % RASI_NAMES.length) + 1,
      };
    }),
  };
}

function canUnprocessedBeat(
  candidate: EnrichableMuhurtamSlot,
  boundary: EnrichableMuhurtamSlot,
): boolean {
  const tierDelta = (TIER_RANK[candidate.tier] ?? -1) - (TIER_RANK[boundary.tier] ?? -1);
  if (tierDelta !== 0) return tierDelta > 0;
  return candidate.score >= boundary.score;
}

function baseResult<TSlot extends EnrichableMuhurtamSlot>(
  state: Exclude<ElectionChartEnrichmentState, 'screened'>,
  slots: readonly TSlot[],
  message: string,
): ElectionChartEnrichment<TSlot> {
  return {
    state,
    slots: slots.slice(0, RESULT_LIMIT).map(slot => ({ ...slot })),
    screenedCount: 0,
    removedCount: 0,
    candidateLimitReached: false,
    chartRemovedCount: 0,
    chartRemovedRules: [],
    personalRemovedCount: 0,
    personalRemovedRules: [],
    boundaryReviewCount: 0,
    qualificationCappedCount: 0,
    reviewGatedCount: 0,
    overlappingDispositionCount: 0,
    message,
    engine: null,
  };
}

function reviewGatedResult<TSlot extends EnrichableMuhurtamSlot>(
  state: 'disabled' | 'unavailable',
  slots: readonly TSlot[],
  message: string,
): ElectionChartEnrichment<TSlot> {
  const result = baseResult(state, slots, message);
  result.slots = result.slots.map(slot => ({
    ...slot,
    tier: slot.tier === 'Excellent' ? 'Good' : slot.tier,
    dayDosha: slot.dayDosha || 'practitioner_review',
  }));
  result.reviewGatedCount = result.slots.length;
  return result;
}

function unavailableResult<TSlot extends EnrichableMuhurtamSlot>(
  slots: readonly TSlot[],
  message: string,
): ElectionChartEnrichment<TSlot> {
  return reviewGatedResult('unavailable', slots, message);
}

function unavailableMessage(error: unknown): string {
  if (error instanceof ElectionChartApiError && error.code === 'disabled') {
    return 'Panchangam-ranked; exact chart screening is not active in this public build.';
  }
  if (error instanceof ElectionChartApiError && error.code === 'rate-limited') {
    const seconds = error.retryAfterSeconds === null
      ? null
      : Math.min(3_600, Math.max(1, Math.ceil(error.retryAfterSeconds)));
    if (seconds !== null) {
      const wait = seconds >= 120
        ? `about ${Math.ceil(seconds / 60)} minutes`
        : `about ${seconds} seconds`;
      return `Panchangam-ranked; exact chart screening is busy. Try again in ${wait}.`;
    }
    return 'Panchangam-ranked; exact chart screening is busy. Wait a moment and try again.';
  }
  return 'Panchangam-ranked; exact chart screening is temporarily unavailable.';
}

interface ChartCheckPlan {
  minutes: number[];
  lagnas: string[];
}

function chartCheckPlan(slot: EnrichableMuhurtamSlot): ChartCheckPlan {
  const endMinute = Math.max(slot.s0, slot.e0 - 1);
  const minutes = [...new Set([
    slot.s0,
    ...(slot.chartCheckMinutes || []),
    endMinute,
  ])].sort((left, right) => left - right);
  if (
    !minutes.length || minutes.length > MAX_INSTANTS_PER_REQUEST
    || minutes.some(minute =>
      !Number.isInteger(minute) || minute < slot.s0 || minute > endMinute)
  ) {
    throw new Error('Invalid chart sampling plan.');
  }
  const lagnas = slot.chartCheckLagnas;
  if (
    !Array.isArray(lagnas) || lagnas.length !== minutes.length
    || lagnas.some(lagna => typeof lagna !== 'string' || !RASI_NAMES.includes(lagna))
  ) {
    throw new Error('Canonical Lagna mapping is unavailable.');
  }
  return { minutes, lagnas: lagnas as string[] };
}

export async function enrichElectionChartSlots<TSlot extends EnrichableMuhurtamSlot>(
  baseSlots: readonly TSlot[],
  options: ElectionChartEnrichmentOptions,
): Promise<ElectionChartEnrichment<TSlot>> {
  if (!baseSlots.length) {
    return baseResult(
      'not-run',
      baseSlots,
      'No shortlisted slot was available for exact chart screening.',
    );
  }
  if (!automatedRulesFor(options.activity).length && !roleForActivity(options.activity)) {
    return baseResult(
      'manual-only',
      baseSlots,
      'No deterministic election-chart rule is defined for this activity, so no exact chart request was needed.',
    );
  }
  if (options.system !== 'drik') {
    return baseResult(
      'unsupported-system',
      baseSlots,
      'Exact election-chart screening currently uses Drik/Lahiri and was not blended into this selected system.',
    );
  }
  if (!electionChartCalculationEnabled(options.locationLike, options.activationFlag)) {
    return reviewGatedResult(
      'disabled',
      baseSlots,
      'Panchangam-ranked; exact chart screening is not active in this public build.',
    );
  }
  if (options.boundarySupportAvailable === false) {
    return unavailableResult(
      baseSlots,
      'Panchangam-ranked; exact chart screening is unavailable because the Lagna transition map could not be loaded.',
    );
  }

  const derive = options.derive || deriveElectionCharts;
  const survivors: TSlot[] = [];
  let processed = 0;
  let removedCount = 0;
  let chartRemovedCount = 0;
  let personalRemovedCount = 0;
  let boundaryReviewCount = 0;
  let qualificationCappedCount = 0;
  let reviewGatedCount = 0;
  let overlappingDispositionCount = 0;
  const chartRemovedRules = new Map<string, {
    ruleId: string;
    label: string;
    count: number;
    evidence: string[];
  }>();
  const personalRemovedRules = new Map<string, { ruleId: string; label: string; count: number }>();
  let engine: ElectionChartDerivation['engine'] | null = null;
  let requestCount = 0;
  const screeningDeadline = Date.now() + Math.max(
    1,
    options.screeningTimeoutMs ?? DEFAULT_SCREENING_TIMEOUT_MS,
  );

  try {
    while (processed < baseSlots.length && requestCount < MAX_CHART_REQUESTS) {
      const chunk: TSlot[] = [];
      const samplePlans: number[][] = [];
      const canonicalLagnaPlans: string[][] = [];
      let instantCount = 0;
      while (processed + chunk.length < baseSlots.length) {
        const candidate = baseSlots[processed + chunk.length];
        const plan = chartCheckPlan(candidate);
        if (chunk.length && instantCount + plan.minutes.length > MAX_INSTANTS_PER_REQUEST) break;
        chunk.push(candidate);
        samplePlans.push(plan.minutes);
        canonicalLagnaPlans.push(plan.lagnas);
        instantCount += plan.minutes.length;
        if (instantCount >= MAX_INSTANTS_PER_REQUEST) break;
      }
      const instants = chunk.flatMap((slot, index) =>
        samplePlans[index].map(minute =>
          localWallTimeToInstant(slot.isoDate, minute, options.location.timezone)));
      const remainingTimeoutMs = screeningDeadline - Date.now();
      if (remainingTimeoutMs <= 0) {
        throw new Error('Election-chart screening deadline exceeded.');
      }
      const response = await derive(
        { location: options.location, instants },
        {
          activationFlag: options.activationFlag,
          locationLike: options.locationLike,
          signal: options.signal,
          timeoutMs: remainingTimeoutMs,
        },
      );
      requestCount += 1;
      engine = mergeEngineProvenance(engine, response.engine);
      let chartOffset = 0;
      for (let index = 0; index < chunk.length; index += 1) {
        const charts = response.charts.slice(
          chartOffset,
          chartOffset + samplePlans[index].length,
        );
        chartOffset += samplePlans[index].length;
        const canonicalCharts = charts.map((chart, chartIndex) =>
          projectCanonicalWholeSignHouses(
            chart,
            canonicalLagnaPlans[index][chartIndex],
          ));
        const boundaryAffectsGeneric = !!chunk[index].chartBoundaryNeedsReview
          && automatedRulesFor(options.activity).length > 0;
        const boundaryAffectsPersonal = !!chunk[index].chartBoundaryNeedsReview
          && (options.activity === 'travel' || options.activity === 'gruhapravesha');
        const boundaryNeedsReview = boundaryAffectsGeneric || boundaryAffectsPersonal;
        if (boundaryNeedsReview) boundaryReviewCount += 1;
        const personal = evaluatePersonalElectionSnapshots(
          options.activity,
          options.personalParticipant || null,
          canonicalCharts.map((chart, chartIndex) => {
            const facts = exactPersonalFacts(chart, canonicalLagnaPlans[index][chartIndex]);
            return boundaryAffectsPersonal ? { ...facts, lagna: null } : facts;
          }),
        );
        const screening = {
          ...evaluateElectionSnapshots(options.activity, canonicalCharts, {
            houseFrameUncertain: boundaryAffectsGeneric,
          }),
          ...(boundaryAffectsGeneric
            ? { boundaryConventionUncertain: true }
            : {}),
        };
        if (personal.rejected) {
          removedCount += 1;
          personalRemovedCount += 1;
          for (const outcome of personal.outcomes) {
            if (outcome.effect !== 'reject' || outcome.status !== 'fail') continue;
            const item = personalRemovedRules.get(outcome.ruleId) || {
              ruleId: outcome.ruleId, label: outcome.label, count: 0,
            };
            item.count += 1;
            personalRemovedRules.set(outcome.ruleId, item);
          }
          continue;
        }
        if (screening.rejected) {
          removedCount += 1;
          chartRemovedCount += 1;
          for (const outcome of screening.outcomes) {
            if (outcome.effect !== 'reject' || outcome.status !== 'fail') continue;
            const item = chartRemovedRules.get(outcome.ruleId) || {
              ruleId: outcome.ruleId,
              label: outcome.label,
              count: 0,
              evidence: [],
            };
            item.count += 1;
            for (const observed of outcome.evidence || []) {
              if (!item.evidence.includes(observed) && item.evidence.length < 3) {
                item.evidence.push(observed);
              }
            }
            chartRemovedRules.set(outcome.ruleId, item);
          }
          continue;
        }
        const slot = {
          ...chunk[index],
          personalPreferencePasses: personal.preferencePasses,
          chartScreening: screening,
          reasonGroups: {
            ...chunk[index].reasonGroups,
            personal_source: personal.evidence,
            personal_outcomes: personal.outcomes,
          },
        };
        const qualificationFailed = screening.qualificationFailed;
        const needsReview = screening.needsReview || personal.needsReview;
        if (qualificationFailed) {
          qualificationCappedCount += 1;
          if (slot.tier === 'Excellent') slot.tier = 'Good';
          slot.dayDosha ||= 'chart_qualification';
        }
        if (needsReview) {
          reviewGatedCount += 1;
          if (slot.tier === 'Excellent') slot.tier = 'Good';
          if (!slot.dayDosha || slot.dayDosha === 'chart_qualification') {
            slot.dayDosha = 'practitioner_review';
          }
        }
        if (qualificationFailed && needsReview) {
          overlappingDispositionCount += 1;
        }
        survivors.push(slot);
      }
      processed += chunk.length;
      const ranked = rank(survivors);
      if (ranked.length >= RESULT_LIMIT) {
        const boundary = ranked[RESULT_LIMIT - 1];
        const next = baseSlots[processed];
        if (!next || !canUnprocessedBeat(next, boundary)) break;
      }
    }
  } catch (error) {
    if (options.signal?.aborted) throw error;
    if (processed > 0) {
      const shown = rank(survivors).slice(0, RESULT_LIMIT);
      const removalParts = [
        chartRemovedCount
          ? `${chartRemovedCount} failed an exact chart requirement`
          : '',
        personalRemovedCount
          ? `${personalRemovedCount} failed a profile-specific source requirement`
          : '',
      ].filter(Boolean);
      const removalSummary = removalParts.length
        ? ` ${removalParts.join('; ')}.`
        : '';
      return {
        state: 'unavailable',
        slots: shown,
        screenedCount: processed,
        removedCount,
        candidateLimitReached: processed < baseSlots.length,
        chartRemovedCount,
        chartRemovedRules: [...chartRemovedRules.values()],
        personalRemovedCount,
        personalRemovedRules: [...personalRemovedRules.values()],
        boundaryReviewCount,
        qualificationCappedCount,
        reviewGatedCount,
        overlappingDispositionCount,
        message: `${processed} highest-ranked candidates received exact chart screening before screening stopped early; only ${shown.length} already-screened survivor${shown.length === 1 ? ' is' : 's are'} shown.${removalSummary} Unprocessed candidates were not shown. ${unavailableMessage(error)}`,
        engine,
      };
    }
    return unavailableResult(
      baseSlots,
      unavailableMessage(error),
    );
  }

  const candidateLimitReached = requestCount >= MAX_CHART_REQUESTS
    && processed < baseSlots.length;
  const removalParts = [
    chartRemovedCount
      ? `${chartRemovedCount} failed an exact chart requirement`
      : '',
    personalRemovedCount
      ? `${personalRemovedCount} failed a profile-specific source requirement`
      : '',
  ].filter(Boolean);
  const removalSummary = removalParts.length ? ` ${removalParts.join('; ')}.` : '';
  const dispositionParts = [
    qualificationCappedCount
      ? `${qualificationCappedCount} retained slot${qualificationCappedCount === 1 ? ' has' : 's have'} a conclusive event-specific condition miss; the raw score is unchanged and the maximum rating is Good`
      : '',
    reviewGatedCount
      ? `${reviewGatedCount} retained slot${reviewGatedCount === 1 ? ' is' : 's are'} indeterminate at a calculation boundary or missing fact; the raw score is unchanged and the maximum rating is Good pending review`
      : '',
  ].filter(Boolean);
  const dispositionSummary = dispositionParts.length
    ? ` ${dispositionParts.join('; ')}.`
    : '';
  const overlapSummary = overlappingDispositionCount
    ? ` ${overlappingDispositionCount} retained slot${overlappingDispositionCount === 1 ? ' is' : 's are'} included in both disposition counts because a conclusive miss and a separate unknown can coexist.`
    : '';

  return {
    state: 'screened',
    slots: rank(survivors).slice(0, RESULT_LIMIT),
    screenedCount: processed,
    removedCount,
    candidateLimitReached,
    chartRemovedCount,
    chartRemovedRules: [...chartRemovedRules.values()],
    personalRemovedCount,
    personalRemovedRules: [...personalRemovedRules.values()],
    boundaryReviewCount,
    qualificationCappedCount,
    reviewGatedCount,
    overlappingDispositionCount,
    message: candidateLimitReached
      ? `${processed} highest-ranked candidates received chart screening; the per-search safety budget was reached, so ${Math.min(survivors.length, RESULT_LIMIT)} surviving slot${Math.min(survivors.length, RESULT_LIMIT) === 1 ? '' : 's'} are shown.${removalSummary}${dispositionSummary}${overlapSummary}`
      : removedCount
        ? `${processed} shortlisted slots received chart screening.${removalSummary}${dispositionSummary}${overlapSummary}`
        : `${processed} shortlisted slots received exact chart screening across every sampled state.${dispositionSummary}${overlapSummary}`,
    engine,
  };
}
