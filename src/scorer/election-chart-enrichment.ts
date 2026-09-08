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
  type RemoteCalculationLocation as ElectionChartBrowserLocation,
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

interface EnrichmentProgress<TSlot extends EnrichableMuhurtamSlot> {
  survivors: TSlot[];
  processed: number;
  removedCount: number;
  chartRemovedCount: number;
  personalRemovedCount: number;
  boundaryReviewCount: number;
  qualificationCappedCount: number;
  reviewGatedCount: number;
  overlappingDispositionCount: number;
  chartRemovedRules: Map<string, {
    ruleId: string;
    label: string;
    count: number;
    evidence: string[];
  }>;
  personalRemovedRules: Map<string, { ruleId: string; label: string; count: number }>;
  engine: ElectionChartDerivation['engine'] | null;
  requestCount: number;
}

interface ChartChunk<TSlot extends EnrichableMuhurtamSlot> {
  slots: TSlot[];
  samplePlans: number[][];
  canonicalLagnaPlans: string[][];
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

function nextChartChunk<TSlot extends EnrichableMuhurtamSlot>(
  baseSlots: readonly TSlot[],
  processed: number,
): ChartChunk<TSlot> {
  const slots: TSlot[] = [];
  const samplePlans: number[][] = [];
  const canonicalLagnaPlans: string[][] = [];
  let instantCount = 0;
  while (processed + slots.length < baseSlots.length) {
    const candidate = baseSlots[processed + slots.length];
    const plan = chartCheckPlan(candidate);
    if (slots.length && instantCount + plan.minutes.length > MAX_INSTANTS_PER_REQUEST) break;
    slots.push(candidate);
    samplePlans.push(plan.minutes);
    canonicalLagnaPlans.push(plan.lagnas);
    instantCount += plan.minutes.length;
    if (instantCount >= MAX_INSTANTS_PER_REQUEST) break;
  }
  return { slots, samplePlans, canonicalLagnaPlans };
}

function recordPersonalRejection<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
  personal: ReturnType<typeof evaluatePersonalElectionSnapshots>,
): void {
  progress.removedCount += 1;
  progress.personalRemovedCount += 1;
  for (const outcome of personal.outcomes) {
    if (outcome.effect !== 'reject' || outcome.status !== 'fail') continue;
    const item = progress.personalRemovedRules.get(outcome.ruleId) || {
      ruleId: outcome.ruleId, label: outcome.label, count: 0,
    };
    item.count += 1;
    progress.personalRemovedRules.set(outcome.ruleId, item);
  }
}

function recordChartRejection<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
  screening: ElectionChartScreening,
): void {
  progress.removedCount += 1;
  progress.chartRemovedCount += 1;
  for (const outcome of screening.outcomes) {
    if (outcome.effect !== 'reject' || outcome.status !== 'fail') continue;
    const item = progress.chartRemovedRules.get(outcome.ruleId) || {
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
    progress.chartRemovedRules.set(outcome.ruleId, item);
  }
}

function retainScreenedSlot<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
  sourceSlot: TSlot,
  personal: ReturnType<typeof evaluatePersonalElectionSnapshots>,
  screening: ElectionChartScreening,
): void {
  const slot = {
    ...sourceSlot,
    personalPreferencePasses: personal.preferencePasses,
    chartScreening: screening,
    reasonGroups: {
      ...sourceSlot.reasonGroups,
      personal_source: personal.evidence,
      personal_outcomes: personal.outcomes,
    },
  };
  const qualificationFailed = screening.qualificationFailed;
  const needsReview = screening.needsReview || personal.needsReview;
  if (qualificationFailed) {
    progress.qualificationCappedCount += 1;
    if (slot.tier === 'Excellent') slot.tier = 'Good';
    slot.dayDosha ||= 'chart_qualification';
  }
  if (needsReview) {
    progress.reviewGatedCount += 1;
    if (slot.tier === 'Excellent') slot.tier = 'Good';
    if (!slot.dayDosha || slot.dayDosha === 'chart_qualification') {
      slot.dayDosha = 'practitioner_review';
    }
  }
  if (qualificationFailed && needsReview) progress.overlappingDispositionCount += 1;
  progress.survivors.push(slot);
}

async function screenChartChunk<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
  chunk: ChartChunk<TSlot>,
  options: ElectionChartEnrichmentOptions,
  derive: DeriveElectionCharts,
  screeningDeadline: number,
): Promise<void> {
  const instants = chunk.slots.flatMap((slot, index) =>
    chunk.samplePlans[index].map(minute =>
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
  progress.requestCount += 1;
  progress.engine = mergeEngineProvenance(progress.engine, response.engine);
  let chartOffset = 0;
  for (let index = 0; index < chunk.slots.length; index += 1) {
    const charts = response.charts.slice(
      chartOffset,
      chartOffset + chunk.samplePlans[index].length,
    );
    chartOffset += chunk.samplePlans[index].length;
    const canonicalCharts = charts.map((chart, chartIndex) =>
      projectCanonicalWholeSignHouses(
        chart,
        chunk.canonicalLagnaPlans[index][chartIndex],
      ));
    const sourceSlot = chunk.slots[index];
    const boundaryAffectsGeneric = Boolean(sourceSlot.chartBoundaryNeedsReview)
      && automatedRulesFor(options.activity).length > 0;
    const boundaryAffectsPersonal = Boolean(sourceSlot.chartBoundaryNeedsReview)
      && (options.activity === 'travel' || options.activity === 'gruhapravesha');
    if (boundaryAffectsGeneric || boundaryAffectsPersonal) progress.boundaryReviewCount += 1;
    const personal = evaluatePersonalElectionSnapshots(
      options.activity,
      options.personalParticipant || null,
      canonicalCharts.map((chart, chartIndex) => {
        const facts = exactPersonalFacts(chart, chunk.canonicalLagnaPlans[index][chartIndex]);
        return boundaryAffectsPersonal ? { ...facts, lagna: null } : facts;
      }),
    );
    const screening: ElectionChartScreening = {
      ...evaluateElectionSnapshots(options.activity, canonicalCharts, {
        houseFrameUncertain: boundaryAffectsGeneric,
      }),
      ...(boundaryAffectsGeneric ? { boundaryConventionUncertain: true } : {}),
    };
    if (personal.rejected) recordPersonalRejection(progress, personal);
    else if (screening.rejected) recordChartRejection(progress, screening);
    else retainScreenedSlot(progress, sourceSlot, personal, screening);
  }
  progress.processed += chunk.slots.length;
}

function newEnrichmentProgress<TSlot extends EnrichableMuhurtamSlot>(): EnrichmentProgress<TSlot> {
  return {
    survivors: [],
    processed: 0,
    removedCount: 0,
    chartRemovedCount: 0,
    personalRemovedCount: 0,
    boundaryReviewCount: 0,
    qualificationCappedCount: 0,
    reviewGatedCount: 0,
    overlappingDispositionCount: 0,
    chartRemovedRules: new Map(),
    personalRemovedRules: new Map(),
    engine: null,
    requestCount: 0,
  };
}

function removalSummary<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
): string {
  const parts: string[] = [];
  if (progress.chartRemovedCount) {
    parts.push(`${progress.chartRemovedCount} failed an exact chart requirement`);
  }
  if (progress.personalRemovedCount) {
    parts.push(`${progress.personalRemovedCount} failed a profile-specific source requirement`);
  }
  return parts.length ? ` ${parts.join('; ')}.` : '';
}

function dispositionSummary<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
): string {
  const parts: string[] = [];
  if (progress.qualificationCappedCount) {
    const verb = progress.qualificationCappedCount === 1 ? 'has' : 'have';
    parts.push(`${progress.qualificationCappedCount} retained slot${progress.qualificationCappedCount === 1 ? '' : 's'} ${verb} a conclusive event-specific condition miss; the raw score is unchanged and the maximum rating is Good`);
  }
  if (progress.reviewGatedCount) {
    const verb = progress.reviewGatedCount === 1 ? 'is' : 'are';
    parts.push(`${progress.reviewGatedCount} retained slot${progress.reviewGatedCount === 1 ? '' : 's'} ${verb} indeterminate at a calculation boundary or missing fact; the raw score is unchanged and the maximum rating is Good pending review`);
  }
  return parts.length ? ` ${parts.join('; ')}.` : '';
}

function overlapSummary<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
): string {
  const count = progress.overlappingDispositionCount;
  if (!count) return '';
  const verb = count === 1 ? 'is' : 'are';
  return ` ${count} retained slot${count === 1 ? '' : 's'} ${verb} included in both disposition counts because a conclusive miss and a separate unknown can coexist.`;
}

function partialUnavailableResult<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
  baseSlotCount: number,
  error: unknown,
): ElectionChartEnrichment<TSlot> {
  const shown = rank(progress.survivors).slice(0, RESULT_LIMIT);
  const shownPhrase = shown.length === 1 ? 'survivor is' : 'survivors are';
  return {
    state: 'unavailable',
    slots: shown,
    screenedCount: progress.processed,
    removedCount: progress.removedCount,
    candidateLimitReached: progress.processed < baseSlotCount,
    chartRemovedCount: progress.chartRemovedCount,
    chartRemovedRules: [...progress.chartRemovedRules.values()],
    personalRemovedCount: progress.personalRemovedCount,
    personalRemovedRules: [...progress.personalRemovedRules.values()],
    boundaryReviewCount: progress.boundaryReviewCount,
    qualificationCappedCount: progress.qualificationCappedCount,
    reviewGatedCount: progress.reviewGatedCount,
    overlappingDispositionCount: progress.overlappingDispositionCount,
    message: `${progress.processed} highest-ranked candidates received exact chart screening before screening stopped early; only ${shown.length} already-screened ${shownPhrase} shown.${removalSummary(progress)} Unprocessed candidates were not shown. ${unavailableMessage(error)}`,
    engine: progress.engine,
  };
}

function screenedMessage<TSlot extends EnrichableMuhurtamSlot>(
  progress: EnrichmentProgress<TSlot>,
  candidateLimitReached: boolean,
): string {
  const removals = removalSummary(progress);
  const dispositions = dispositionSummary(progress);
  const overlap = overlapSummary(progress);
  if (candidateLimitReached) {
    const shown = Math.min(progress.survivors.length, RESULT_LIMIT);
    const suffix = shown === 1 ? '' : 's';
    return `${progress.processed} highest-ranked candidates received chart screening; the per-search safety budget was reached, so ${shown} surviving slot${suffix} are shown.${removals}${dispositions}${overlap}`;
  }
  if (progress.removedCount) {
    return `${progress.processed} shortlisted slots received chart screening.${removals}${dispositions}${overlap}`;
  }
  return `${progress.processed} shortlisted slots received exact chart screening across every sampled state.${dispositions}${overlap}`;
}

function enrichmentPreflight<TSlot extends EnrichableMuhurtamSlot>(
  baseSlots: readonly TSlot[],
  options: ElectionChartEnrichmentOptions,
): ElectionChartEnrichment<TSlot> | null {
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
  return null;
}

export async function enrichElectionChartSlots<TSlot extends EnrichableMuhurtamSlot>(
  baseSlots: readonly TSlot[],
  options: ElectionChartEnrichmentOptions,
): Promise<ElectionChartEnrichment<TSlot>> {
  const preflight = enrichmentPreflight(baseSlots, options);
  if (preflight) return preflight;

  const derive = options.derive || deriveElectionCharts;
  const progress = newEnrichmentProgress<TSlot>();
  const screeningDeadline = Date.now() + Math.max(
    1,
    options.screeningTimeoutMs ?? DEFAULT_SCREENING_TIMEOUT_MS,
  );

  try {
    while (progress.processed < baseSlots.length && progress.requestCount < MAX_CHART_REQUESTS) {
      const chunk = nextChartChunk(baseSlots, progress.processed);
      await screenChartChunk(progress, chunk, options, derive, screeningDeadline);
      const ranked = rank(progress.survivors);
      if (ranked.length >= RESULT_LIMIT) {
        const boundary = ranked[RESULT_LIMIT - 1];
        const next = baseSlots[progress.processed];
        if (!next || !canUnprocessedBeat(next, boundary)) break;
      }
    }
  } catch (error) {
    if (options.signal?.aborted) throw error;
    if (progress.processed > 0) {
      return partialUnavailableResult(progress, baseSlots.length, error);
    }
    return unavailableResult(
      baseSlots,
      unavailableMessage(error),
    );
  }

  const candidateLimitReached = progress.requestCount >= MAX_CHART_REQUESTS
    && progress.processed < baseSlots.length;

  return {
    state: 'screened',
    slots: rank(progress.survivors).slice(0, RESULT_LIMIT),
    screenedCount: progress.processed,
    removedCount: progress.removedCount,
    candidateLimitReached,
    chartRemovedCount: progress.chartRemovedCount,
    chartRemovedRules: [...progress.chartRemovedRules.values()],
    personalRemovedCount: progress.personalRemovedCount,
    personalRemovedRules: [...progress.personalRemovedRules.values()],
    boundaryReviewCount: progress.boundaryReviewCount,
    qualificationCappedCount: progress.qualificationCappedCount,
    reviewGatedCount: progress.reviewGatedCount,
    overlappingDispositionCount: progress.overlappingDispositionCount,
    message: screenedMessage(progress, candidateLimitReached),
    engine: progress.engine,
  };
}
