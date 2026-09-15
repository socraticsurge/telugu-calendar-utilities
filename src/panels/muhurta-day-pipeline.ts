import { muCanonicalNakshatra } from '../muhurta-scorer';
import { type RankedCandidate } from '../scorer/ranking';
import { calendarEventDay, type CalendarEvent } from '../lib/calendar-data';
import { stampOf } from '../lib/format';
import {
  automatedRulesFor,
  chartAssessorCompleteFor,
  chartManualRemaindersFor,
} from '../scorer/election-chart-screening';
import activityContract from '../data/activity-rules.generated.json';
import {
  MU_PARTIAL_ASSESSOR_DISCLOSURE,
  muClassifyManualChecks,
  muRelevantManualChecks,
} from './muhurta-contracts';
import {
  muChartBoundaryNeedsReview,
  muChartCheckMinutes,
  muChartLagnasForMinutes,
  muMin,
  muValidLagnaDayData,
} from './muhurta-astronomy';
import {
  muBadWindows,
  muConfiguredDaylightPolicy,
  muDayDrop,
  muRecordNoSlotDay,
} from './muhurta-day-rules';
import {
  muInitialSlotScore,
  muPersonalDosha,
  muScoreActivityLagna,
  muScoreNityaYoga,
  muScoreParticipantChandrabalam,
  muScoreParticipantLagna,
  muScoreParticipantTarabalam,
  muScoreSlotPreferences,
  muScoreSlotTithi,
  muScoreSpecialYogas,
  muSlotDayDosha,
  muSlotDoctrinalNotes,
  muSlotElectionReasons,
  muSlotTimeFoundation,
} from './muhurta-scoring';
import { muToT } from './muhurta-format';

const MU_ACTIVITY = activityContract.rules;

export interface MuhurtaPipelineState {
  slots: Array<RankedCandidate & Record<string, unknown>>;
  slotsPerDay: Map<string, number>;
  droppedDays: unknown[];
  droppedEclipseDays: number;
  droppedModeSlots: number;
}

export function createMuhurtaPipelineState(): MuhurtaPipelineState {
  return {
    slots: [],
    slotsPerDay: new Map(),
    droppedDays: [],
    droppedEclipseDays: 0,
    droppedModeSlots: 0,
  };
}

function muCanonicalSet(values = []) {
  return new Set(values.map(muCanonicalNakshatra));
}

function muElectionRuleSets(rules) {
  return {
    allowedNakshatras: muCanonicalSet(rules.allowed_nakshatras),
    avoidNakshatras: muCanonicalSet(rules.avoid_nakshatras),
    preferNakshatras: muCanonicalSet(rules.prefer_nakshatras),
    allowedTithiNumbers: new Set(rules.allowed_tithi_numbers || []),
    preferTithiNumbers: new Set(rules.prefer_tithi_numbers || []),
    allowedTithiNames: new Set(rules.allowed_tithi_names || []),
    avoidTithiNumbers: new Set(rules.avoid_tithi_numbers || []),
    avoidVaraTithiNames: new Set(
      (rules.avoid_vara_tithi_names || []).map(pair => `${pair[0]}|${pair[1]}`),
    ),
    avoidNityaYogas: new Set(rules.avoid_nitya_yogas || []),
  };
}

function muLagnaRuleSets(rules) {
  return {
    skipYogas: new Set(rules.skip_on_yoga || []),
    avoidKaranaNames: new Set(rules.avoid_karana || []),
    preferVaras: new Set(rules.prefer_vara || []),
    allowedLagnas: new Set(rules.allowed_lagnas || []),
    preferLagnas: new Set(rules.prefer_lagnas || []),
  };
}

function muEffectiveChartRemainder(activity) {
  const chartManualRemainder = chartManualRemaindersFor(activity);
  const incompleteEmptyRemainder = chartManualRemainder !== null
    && !chartAssessorCompleteFor(activity)
    && chartManualRemainder.length === 0
    && automatedRulesFor(activity).length > 0;
  return incompleteEmptyRemainder
    ? [MU_PARTIAL_ASSESSOR_DISCLOSURE]
    : chartManualRemainder;
}

function muRuleContext(activity, data, borrowingPurpose) {
  const rules = MU_ACTIVITY[activity] || MU_ACTIVITY.any;
  const manualChecks = muRelevantManualChecks(
    activity, data.vaaram, borrowingPurpose,
  );
  return {
    rules,
    activityLabel: rules.label,
    preferChog: rules.prefer_choghadiya || null,
    preferTithiClass: rules.prefer_tithi_class || null,
    avoidTithiClasses: rules.avoid_tithi_class || [],
    preferLagnaClass: rules.prefer_lagna_class || null,
    requiredLagnaClass: rules.required_lagna_class || null,
    cautionLagnaSolar: Boolean(rules.caution_lagna_solar),
    avoidJanmaNakshatra: Boolean(rules.avoid_janma_nakshatra),
    ...muLagnaRuleSets(rules),
    ...muElectionRuleSets(rules),
    manualGuidance: muClassifyManualChecks(activity, manualChecks),
    effectiveChartRemainder: muEffectiveChartRemainder(activity),
  };
}

function muWindowRange(window) {
  return `${muToT(muMin(window.start, window.sflag))} to ${muToT(muMin(window.end, window.eflag))}`;
}

function muGroupedWindows(windows) {
  const groups = new Map();
  for (const window of windows) {
    if (!groups.has(window.name)) groups.set(window.name, []);
    groups.get(window.name).push(muWindowRange(window));
  }
  return [...groups.entries()].map(([name, ranges]) => ({ name, ranges }));
}

function muDayContext(data, abhijit) {
  const rahuWindow = data.inauspicious.find(window => /Rahu/i.test(window.name));
  return {
    tithi: data.tithi?.name || null,
    nakshatra: data.nakshatra?.name || null,
    yoga: data.yoga?.name || null,
    sunrise: muOptionalSunrise(data.sunrise),
    abhijit: muOptionalWindow(abhijit),
    rahu: muOptionalWindow(rahuWindow),
    auspicious: muGroupedWindows(data.auspicious),
    avoid: muGroupedWindows(data.inauspicious),
  };
}

function muOptionalSunrise(sunrise) {
  return sunrise ? muToT(muMin(sunrise)) : null;
}

function muOptionalWindow(window) {
  return window ? muWindowRange(window) : null;
}

function muElectionRestrictions(ruleContext) {
  return {
    allowedNakshatras: ruleContext.allowedNakshatras,
    avoidNakshatras: ruleContext.avoidNakshatras,
    avoidJanmaNakshatra: ruleContext.avoidJanmaNakshatra,
    allowedTithiNumbers: ruleContext.allowedTithiNumbers,
    allowedTithiNames: ruleContext.allowedTithiNames,
    avoidTithiNumbers: ruleContext.avoidTithiNumbers,
    avoidVaraTithiNames: ruleContext.avoidVaraTithiNames,
  };
}

function muParticipantScores(context, foundation) {
  const { people, chandraMode, lagnaCityData } = context;
  const { facts, slotLagna } = foundation;
  const tarabalam = muScoreParticipantTarabalam(people, facts.nakshatra);
  const chandrabalam = muScoreParticipantChandrabalam(
    people, facts.lunarSign, chandraMode,
  );
  const lagnaScore = people.length && lagnaCityData && slotLagna
    ? muScoreParticipantLagna(people, slotLagna)
    : { score: 0, reasons: [], ashtamaNames: [] };
  return { tarabalam, chandrabalam, lagnaScore };
}

function muActivityScores(context, foundation, data, ruleContext) {
  const { activity, lagnaCityData, system } = context;
  const { facts, slotLagna } = foundation;
  const lagna = muScoreActivityLagna(
    slotLagna,
    ruleContext.requiredLagnaClass,
    ruleContext.allowedLagnas,
    ruleContext.preferLagnas,
    ruleContext.preferLagnaClass,
    lagnaCityData,
    ruleContext.activityLabel,
    activity === 'court' && system === 'drik',
  );
  if (!lagna) return null;
  const tithi = muScoreSlotTithi(
    facts,
    ruleContext.preferTithiClass,
    ruleContext.activityLabel,
    ruleContext.avoidTithiClasses,
    ruleContext.preferTithiNumbers,
  );
  return { lagna, tithi };
}

function muYogaScores(foundation, data, ruleContext) {
  const { facts, s0 } = foundation;
  const special = muScoreSpecialYogas(facts, ruleContext.skipYogas);
  if (!special) return null;
  const nitya = muScoreNityaYoga(
    facts, data, ruleContext.skipYogas, ruleContext.avoidNityaYogas, s0,
  );
  return nitya ? { special, nitya } : null;
}

function muScoreCandidate(input) {
  const { context, foundation, data, ruleContext, varaReason, amrita } = input;
  const { activity, people } = context;
  const { facts, personal, s0, e0, choghadiya } = foundation;
  const electionReasons = muSlotElectionReasons(
    facts,
    ruleContext.rules,
    muElectionRestrictions(ruleContext),
    data,
    activity === 'borrowing_money' ? [] : people,
  );
  if (!electionReasons) return null;

  const initial = muInitialSlotScore(foundation, electionReasons);
  const { slotQuality, dayQuality, groupFit, activityMatch } = initial;
  let { score } = initial;

  const { tarabalam, chandrabalam, lagnaScore } = muParticipantScores(
    context, foundation,
  );
  score += tarabalam.score;
  groupFit.push(...tarabalam.reasons);
  score += chandrabalam.score;
  groupFit.push(...chandrabalam.reasons);
  if (chandrabalam.drop) return { modeDrop: true };
  score += lagnaScore.score;
  groupFit.push(...lagnaScore.reasons);

  const activityScores = muActivityScores(context, foundation, data, ruleContext);
  if (!activityScores) return null;
  score += activityScores.lagna.score + activityScores.tithi.score;
  activityMatch.push(...activityScores.lagna.reasons);
  dayQuality.push(...activityScores.tithi.dayReasons);
  activityMatch.push(...activityScores.tithi.activityReasons);

  const yogaScores = muYogaScores(foundation, data, ruleContext);
  if (!yogaScores) return null;
  score += yogaScores.special.score + yogaScores.nitya.score;
  dayQuality.push(...yogaScores.special.reasons);
  if (yogaScores.nitya.reason) dayQuality.push(yogaScores.nitya.reason);

  const preferenceScore = muScoreSlotPreferences({
    facts,
    varaReason,
    preferNakshatras: ruleContext.preferNakshatras,
    amrita,
    s0,
    e0,
    preferChog: ruleContext.preferChog,
    choghadiya,
    avoidKaranaNames: ruleContext.avoidKaranaNames,
    activityLabel: ruleContext.activityLabel,
  });
  score += preferenceScore.score;
  slotQuality.push(...preferenceScore.slotReasons);
  activityMatch.push(...preferenceScore.activityReasons);

  return {
    score,
    slotQuality,
    dayQuality,
    groupFit,
    activityMatch,
    tarabalam,
    chandrabalam,
    lagnaScore,
    tithiFamily: activityScores.tithi.family,
    nityaYoga: facts.yoga,
    personal,
  };
}

function muCandidateEvidence(input) {
  const { context, scored, foundation, data, ruleContext, daylightPolicy } = input;
  const { cautionLagnaSolar, effectiveChartRemainder, manualGuidance, rules } = ruleContext;
  const { facts, slotLagna, personal } = foundation;
  const { notes, siddhiYogas } = muSlotDoctrinalNotes({
    cautionLagnaSolar,
    lagnaCityData: context.lagnaCityData,
    slotLagna,
    solarSign: data.solarSign,
    specialYogas: facts.specialYogas,
    taraUnfavNames: scored.tarabalam.unfavourableNames,
    chandraAvoidNames: scored.chandrabalam.avoidNames,
    tithiFamily: scored.tithiFamily,
  });
  const reasonGroups = {
    slot_quality: scored.slotQuality,
    day_quality: scored.dayQuality,
    group_fit: scored.groupFit,
    activity_match: scored.activityMatch,
    personal_source: personal.evidence,
    personal_outcomes: personal.outcomes,
    day_source_outcomes: daylightPolicy?.outcomes || [],
    notes,
    chart_validation: manualGuidance.chart,
    chart_remainder: effectiveChartRemainder,
    information: manualGuidance.information,
    practical: manualGuidance.practical,
  };
  const personalDosha = muPersonalDosha({
    chandraAvoidNames: scored.chandrabalam.avoidNames,
    hasAshtama: scored.chandrabalam.hasAshtama,
    ashtamaLagnaNames: scored.lagnaScore.ashtamaNames,
    chandraPujaNames: scored.chandrabalam.pujaNames,
    taraUnfavNames: scored.tarabalam.unfavourableNames,
    siddhiYogas,
  });
  const dayDosha = muSlotDayDosha({
    tithiFamily: scored.tithiFamily,
    facts,
    nityaYoga: scored.nityaYoga,
    system: context.system,
    effectiveChartRemainder,
    rules,
    manualGuidance,
    personal,
  });
  return { reasonGroups, personalDosha, dayDosha };
}

function muProcessSlot(input) {
  const { context, state, day, data, isoDate, ruleContext, dayValues, mi } = input;
  const foundation = muSlotTimeFoundation({
    mi,
    ...dayValues,
    rules: ruleContext.rules,
    data,
    chartLocation: context.chartLocation,
    isoDate,
    date: day,
    lagnaCityData: context.lagnaCityData,
    system: context.system,
    activity: context.activity,
  });
  if (!foundation) return;
  const scored = muScoreCandidate({
    context,
    foundation,
    data,
    ruleContext,
    varaReason: dayValues.varaReason,
    amrita: dayValues.amrita,
  });
  if (!scored) return;
  if (scored.modeDrop) {
    state.droppedModeSlots += 1;
    return;
  }

  const evidence = muCandidateEvidence({
    context,
    scored,
    foundation,
    data,
    ruleContext,
    daylightPolicy: dayValues.daylightPolicy,
  });
  const { s0, e0, lagnaDay, personal } = foundation;
  const chartCheckMinutes = muChartCheckMinutes(lagnaDay, s0, e0);
  state.slots.push({
    d: new Date(day),
    isoDate,
    s0,
    e0,
    score: scored.score,
    reasons: [
      ...scored.slotQuality,
      ...scored.groupFit,
      ...scored.dayQuality,
      ...scored.activityMatch,
    ],
    ...evidence,
    dayCtx: dayValues.dayCtx,
    personalPreferencePasses: personal.preferencePasses,
    chartCheckMinutes,
    chartCheckLagnas: muChartLagnasForMinutes(lagnaDay, chartCheckMinutes),
    chartBoundarySupported: muValidLagnaDayData(lagnaDay),
    chartBoundaryNeedsReview: muChartBoundaryNeedsReview(lagnaDay, s0, e0),
  });
  state.slotsPerDay.set(isoDate, (state.slotsPerDay.get(isoDate) || 0) + 1);
}

export function processMuhurtaDay(context, state: MuhurtaPipelineState, day, event: CalendarEvent): void {
  const data = calendarEventDay(event);
  const isoDate = stampOf(day).replace(/^(\d{4})(\d{2})(\d{2})$/, '$1-$2-$3');
  const ruleContext = muRuleContext(
    context.activity, data, context.borrowingPurpose,
  );
  const daylightPolicy = muConfiguredDaylightPolicy(
    context.activity, data, ruleContext.rules,
  );
  const dayDrop = muDayDrop(
    data,
    ruleContext.rules,
    ruleContext.activityLabel,
    daylightPolicy,
    context.lagnaCityData,
    isoDate,
  );
  if (dayDrop) {
    if (dayDrop.eclipse) state.droppedEclipseDays += 1;
    state.droppedDays.push(dayDrop.entry);
    return;
  }

  const varaBonus = data.vaaram && ruleContext.preferVaras.has(data.vaaram);
  const varaReason = varaBonus
    ? `${data.vaaram} favoured for ${ruleContext.activityLabel} (+1)`
    : null;
  const bad = muBadWindows(data, ruleContext.avoidKaranaNames);
  const abhijit = data.auspicious.find(
    window => window.name === 'Abhijit Muhurta',
  );
  const srMin = muMin(data.sunrise);
  const ssMin = muMin(data.sunset);
  const dayValues = {
    srMin,
    ssMin,
    muLen: (ssMin - srMin) / 15,
    bad,
    abhijit,
    amrita: data.auspicious.filter(window => window.name === 'Amrita Kalam'),
    varaReason,
    daylightPolicy,
    dayCtx: muDayContext(data, abhijit),
  };
  for (let muhurtaIndex = 0; muhurtaIndex < 15; muhurtaIndex += 1) {
    muProcessSlot({
      context,
      state,
      day,
      data,
      isoDate,
      ruleContext,
      dayValues,
      mi: muhurtaIndex,
    });
  }
  muRecordNoSlotDay({
    slotsPerDay: state.slotsPerDay,
    droppedDays: state.droppedDays,
    isoDate,
    data,
    skipYogas: ruleContext.skipYogas,
    activityLabel: ruleContext.activityLabel,
    people: context.people,
    chandraMode: context.chandraMode,
  });
}
