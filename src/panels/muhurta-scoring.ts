import sharedTables from '../data/shared-calendar-tables.generated.json';
import {
  MU_CHANDRA_GOOD,
  MU_CHANDRA_PUJA,
  computeDayDosha,
  muCanonicalNakshatra,
  muEndsBySolarNoon,
  muIsFavourableLagna,
  muLagnaAtMin,
  muLagnaPosition,
  muLagnaVerdict,
  muLagnasInClass,
  muScoreTithiClass,
} from '../muhurta-scorer';
import { lagnaDayFor } from '../lib/lagna-loader';
import { localWallTimeToInstant } from '../lib/election-chart-api';
import { MUHURTA_DAY } from '../data/muhurtas';
import { roleForActivity } from '../scorer/personal-election-screening';
import { automatedRulesFor } from '../scorer/election-chart-screening';
import {
  activityTithiNumber,
  muFactsAt,
  muHomaElection,
  muMin,
  muNatureBonus,
} from './muhurta-astronomy';
import {
  tbChandraOf,
  tbTaraIsGood,
  tbTaraLabel,
  tbTaraOf,
} from './tarabalam-journey';

function taroOfSafe(janma, dayNak) {
  try { return tbTaraOf(janma, dayNak); } catch (_error) { return 1; }
}

function muOrdinal(value) {
  const mod100 = value % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${value}th`;
  return `${value}${({ 1: 'st', 2: 'nd', 3: 'rd' })[value % 10] || 'th'}`;
}

const MU_GOOD_CHOG = { Amrit: 3, Shubh: 2, Labh: 2, Char: 1 };
const MU_YOGA_BONUS = { 'Sarvartha Siddhi Yoga': 2, 'Amrita Siddhi Yoga': 2,
                        'Dvipushkara Yoga': 1, 'Tripushkara Yoga': 1 };
const MU_YOGA_PENALTY = { 'Visha Yoga': -2, 'Dagdha Yoga': -2 };

// MU_TIER_NAMES, muScoreTier, muRelativeTier — imported from
// src/muhurta-scorer.ts (see the import block at the top of this
// file).
// Tier each slot relative to the min/max score in this batch — mirror
// telugu_panchangam/personal/muhurta.assign_tiers. "Excellent" means
// the best of what turned up in this search, not a fixed bar.
export { muAssignTiers, muRankCandidateSlots } from '../scorer/ranking';

// Nitya Yoga scoring — mirror telugu_panchangam/personal/nitya_yoga.py
const MU_NITYA_HARD_AVOID = new Set(sharedTables.nitya.hardAvoid);
const MU_NITYA_HARD_PENALTY = sharedTables.nitya.hardPenalty;
const MU_NITYA_PARTIAL_WINDOW_MIN = sharedTables.nitya.partialMinutes;
const MU_NITYA_PARTIAL_PENALTY = sharedTables.nitya.partialPenalty;
const MU_NITYA_AUSPICIOUS = new Set(sharedTables.nitya.auspicious);
const MU_NITYA_AUSPICIOUS_BONUS = sharedTables.nitya.auspiciousBonus;

export function muParticipantLabel(person, index: number): string {
  return `#${index + 1} (${person.name || person.nak})`;
}

export function muScoreParticipantTarabalam(people, nakshatra) {
  const favourable = [];
  const unfavourable = [];
  const unfavourableNames = [];
  let score = 0;
  people.forEach((person, index) => {
    const tara = taroOfSafe(person.nak, nakshatra);
    const label = muParticipantLabel(person, index);
    if (tbTaraIsGood(tara)) {
      favourable.push(label);
      score += 1;
    } else {
      unfavourable.push(`${label} ${tbTaraLabel(tara)}`);
      unfavourableNames.push(label);
      score -= 1;
    }
  });
  const reasons = [];
  if (favourable.length) {
    reasons.push(`Tarabalam favourable for ${favourable.join(', ')} (+${favourable.length})`);
  }
  if (unfavourable.length) {
    reasons.push(`Tarabalam avoid for ${unfavourable.join(', ')} (-${unfavourable.length})`);
  }
  return { score, reasons, unfavourableNames };
}

export function muParticipantChandraResult(person, index: number, lunarSign) {
  if (!person.rasi) return null;
  const chandra = tbChandraOf(person.rasi, lunarSign);
  if (!chandra) return null;
  const label = muParticipantLabel(person, index);
  if (MU_CHANDRA_GOOD.has(chandra.pos)) return { kind: 'good', label, score: 1 };
  if (MU_CHANDRA_PUJA.has(chandra.pos)) {
    return { kind: 'puja', label, text: `${label} Moon@${chandra.pos}`, score: 0 };
  }
  const ashtama = chandra.pos === 8;
  return {
    kind: 'avoid', label, ashtama,
    text: `${label}${ashtama ? ' Ashtama' : ''} Moon@${chandra.pos}`,
    score: -1,
  };
}

export function muScoreParticipantChandrabalam(people, lunarSign, chandraMode) {
  const good = [];
  const puja = [];
  const avoid = [];
  const avoidNames = [];
  const pujaNames = [];
  let hasAshtama = false;
  let score = 0;
  people.forEach((person, index) => {
    const result = muParticipantChandraResult(person, index, lunarSign);
    if (!result) return;
    score += result.score;
    if (result.kind === 'good') good.push(result.label);
    if (result.kind === 'puja') {
      puja.push(result.text);
      pujaNames.push(result.label);
    }
    if (result.kind === 'avoid') {
      avoid.push(result.text);
      avoidNames.push(result.label);
      hasAshtama ||= result.ashtama;
    }
  });
  const reasons = [];
  if (good.length) reasons.push(`Chandrabalam favourable for ${good.join(', ')} (+${good.length})`);
  if (puja.length) reasons.push(`Chandrabalam remedial for ${puja.join(', ')} (puja recommended)`);
  if (avoid.length) reasons.push(`Chandrabalam avoid for ${avoid.join(', ')} (-${avoid.length})`);
  const drop = (
    chandraMode === 'strict' && (puja.length > 0 || avoid.length > 0)
  ) || (
    chandraMode === 'puja_ok' && avoid.length > 0
  );
  return { score, reasons, avoidNames, pujaNames, hasAshtama, drop };
}

export function muLagnaReferenceOutcome(
  label: string,
  reference,
  slotLagna,
  suffix: string,
  includeNeutral: boolean,
) {
  if (!reference) return null;
  const position = muLagnaPosition(reference, slotLagna);
  if (position === 8) {
    return { kind: 'ashtama', label, score: -1, text: `${label} lagna@8 from ${reference}${suffix}` };
  }
  if (position && muIsFavourableLagna(position)) {
    return {
      kind: 'favourable', label, score: 1,
      text: `${label} ${muLagnaVerdict(position)}@${position} from ${reference}${suffix}`,
    };
  }
  return includeNeutral && position
    ? { kind: 'neutral', label, score: 0, text: `${label} ${muOrdinal(position)} from ${reference}${suffix}` }
    : null;
}

export function muScoreParticipantLagna(people, slotLagna) {
  const groups = {
    favourableRashi: [], favourableLagna: [],
    ashtamaRashi: [], ashtamaLagna: [],
    neutralRashi: [], neutralLagna: [],
  };
  const ashtamaNames = [];
  let score = 0;
  people.forEach((person, index) => {
    const label = muParticipantLabel(person, index);
    const outcomes: Array<[
      string,
      ReturnType<typeof muLagnaReferenceOutcome>,
    ]> = [
      ['Rashi', muLagnaReferenceOutcome(label, person.rasi, slotLagna, '', !!person.lagna)],
      ['Lagna', muLagnaReferenceOutcome(label, person.lagna, slotLagna, ' lagna', true)],
    ];
    for (const [source, outcome] of outcomes) {
      if (!outcome) continue;
      score += outcome.score;
      groups[`${outcome.kind}${source}`].push(outcome.text);
      if (outcome.kind === 'ashtama' && !ashtamaNames.includes(label)) {
        ashtamaNames.push(label);
      }
    }
  });
  const reasons = [];
  for (const [key, label] of [
    ['favourableRashi', 'favourable'], ['favourableLagna', 'favourable'],
    ['ashtamaRashi', 'Ashtama'], ['ashtamaLagna', 'Ashtama'],
    ['neutralRashi', 'neutral'], ['neutralLagna', 'neutral'],
  ]) {
    const entries = groups[key];
    if (!entries.length) continue;
    let suffix = ` (+${entries.length})`;
    if (key.startsWith('ashtama')) suffix = ` (-${entries.length})`;
    if (key.startsWith('neutral')) suffix = ' (no effect)';
    reasons.push(`${slotLagna} lagna ${label} for ${entries.join(', ')}${suffix}`);
  }
  return { score, reasons, ashtamaNames };
}

export function muScoreActivityLagna(
  slotLagna,
  requiredLagnaClass,
  allowedLagnas,
  preferLagnas,
  preferLagnaClass,
  lagnaCityData,
  activityLabel: string,
  allowConditionalAdmission = false,
) {
  const reasons = [];
  let score = 0;
  if (requiredLagnaClass) {
    const required = muLagnasInClass(requiredLagnaClass);
    if (!slotLagna || !required?.has(slotLagna)) return null;
    reasons.push(`${slotLagna} lagna satisfies required ${requiredLagnaClass} class`);
  }
  if (allowedLagnas.size) {
    if (!slotLagna) return null;
    if (!allowedLagnas.has(slotLagna)) {
      if (!allowConditionalAdmission) return null;
      reasons.push(
        `${slotLagna} lagna retained provisionally for exact Navamsa assessment`,
      );
    } else {
      reasons.push(`${slotLagna} lagna is admitted for ${activityLabel}`);
    }
  }
  if (slotLagna && preferLagnas.has(slotLagna)) {
    score += 1;
    reasons.push(`${slotLagna} lagna specifically favoured for ${activityLabel} (+1)`);
  }
  if (preferLagnaClass && lagnaCityData) {
    const favoured = muLagnasInClass(preferLagnaClass);
    if (slotLagna && favoured?.has(slotLagna)) {
      score += 1;
      reasons.push(`${slotLagna} lagna (${preferLagnaClass}) favoured for ${activityLabel} (+1)`);
    }
  }
  return { score, reasons };
}

export function muScoreSlotTithi(
  facts,
  preferTithiClass,
  activityLabel: string,
  avoidTithiClasses,
  preferTithiNumbers,
) {
  const result = muScoreTithiClass(
    facts.tithi, preferTithiClass, activityLabel, facts.nakshatra,
    facts.specialYogas, avoidTithiClasses,
  );
  const dayReasons = result.dayReason ? [result.dayReason] : [];
  const activityReasons = result.activityReason ? [result.activityReason] : [];
  let score = result.bonus;
  const tithiNumber = activityTithiNumber(facts.tithi);
  if (tithiNumber && preferTithiNumbers.has(tithiNumber)) {
    score += 1;
    activityReasons.push(`${facts.tithi} specifically favoured for ${activityLabel} (+1)`);
  }
  return { score, family: result.family, dayReasons, activityReasons };
}

export function muScoreSpecialYogas(facts, skipYogas) {
  let score = 0;
  const reasons = [];
  for (const yoga of facts.specialYogas) {
    if (MU_YOGA_BONUS[yoga]) {
      score += MU_YOGA_BONUS[yoga];
      reasons.push(`${yoga} day (+${MU_YOGA_BONUS[yoga]})`);
    }
    if (MU_YOGA_PENALTY[yoga] === undefined) continue;
    if (skipYogas.has(yoga)) return null;
    score += MU_YOGA_PENALTY[yoga];
    reasons.push(`${yoga} day (${MU_YOGA_PENALTY[yoga]})`);
  }
  return { score, reasons };
}

export function muScoreNityaYoga(facts, data, skipYogas, avoidNityaYogas, startMinute: number) {
  const yoga = facts.yoga;
  if (avoidNityaYogas.has(yoga)) return null;
  if (MU_NITYA_HARD_AVOID.has(yoga)) {
    if (skipYogas.size) return null;
    return { score: MU_NITYA_HARD_PENALTY, reason: `${yoga} yoga (${MU_NITYA_HARD_PENALTY})` };
  }
  if (MU_NITYA_PARTIAL_WINDOW_MIN[yoga] !== undefined && data.yoga) {
    const windowMin = MU_NITYA_PARTIAL_WINDOW_MIN[yoga];
    const yogaStartMin = yoga === data.yoga.name
      ? muMin(data.yoga.start, data.yoga.sflag)
      : muMin(data.yoga.end, data.yoga.eflag);
    return startMinute - yogaStartMin <= windowMin
      ? { score: MU_NITYA_PARTIAL_PENALTY, reason: `${yoga} yoga dosha-window (${MU_NITYA_PARTIAL_PENALTY})` }
      : { score: 0, reason: null };
  }
  return MU_NITYA_AUSPICIOUS.has(yoga)
    ? { score: MU_NITYA_AUSPICIOUS_BONUS, reason: `${yoga} yoga (+${MU_NITYA_AUSPICIOUS_BONUS})` }
    : { score: 0, reason: null };
}

export function muScoreSlotPreferences(options) {
  const {
    facts, varaReason, preferNakshatras, amrita, s0, e0,
    preferChog, choghadiya, avoidKaranaNames, activityLabel,
  } = options;
  const slotReasons = [];
  const activityReasons = [];
  let score = 0;
  if (varaReason) {
    score += 1;
    activityReasons.push(varaReason);
  }
  if (preferNakshatras.has(facts.nakshatra)) {
    score += 1;
    activityReasons.push(`${facts.nakshatra} specifically favoured for ${activityLabel} (+1)`);
  }
  if (amrita.some(window =>
    s0 < muMin(window.end, window.eflag)
    && muMin(window.start, window.sflag) < e0)) {
    score += 2;
    slotReasons.push('overlaps Amrita Kalam (+2)');
  }
  if (preferChog?.[0] === choghadiya.name) {
    score += preferChog[1];
    activityReasons.push(`${choghadiya.name} favoured for ${activityLabel} (+${preferChog[1]})`);
  }
  for (const karana of avoidKaranaNames) {
    activityReasons.push(`${karana} karana avoided`);
  }
  return { score, slotReasons, activityReasons };
}

export function muSlotDoctrinalNotes(options): { notes: string[]; siddhiYogas: string[] } {
  const {
    cautionLagnaSolar, lagnaCityData, slotLagna, solarSign,
    specialYogas, taraUnfavNames, chandraAvoidNames, tithiFamily,
  } = options;
  const notes = [];
  if (cautionLagnaSolar && lagnaCityData && slotLagna === solarSign) {
    notes.push(`Source caution · ${slotLagna} Lagna is occupied by Surya; ` +
      'Raman associates this with delay from hard rock.');
  }
  const siddhiYogas = specialYogas.filter(yoga =>
    yoga === 'Sarvartha Siddhi Yoga' || yoga === 'Amrita Siddhi Yoga');
  const hasPushkara = specialYogas.some(yoga =>
    yoga === 'Dvipushkara Yoga' || yoga === 'Tripushkara Yoga');
  if (siddhiYogas.length && taraUnfavNames.length) {
    notes.push(`${siddhiYogas.join(' + ')} traditionally rectifies tara dosha ` +
      `(Muhurta Chintamani) · ${taraUnfavNames.join(', ')} mitigated.`);
  }
  if (siddhiYogas.length && chandraAvoidNames.length) {
    notes.push('Chandra dosha is not rectified by Siddhi yogas · ' +
      `${chandraAvoidNames.join(', ')} remains a personal caution.`);
  }
  if (hasPushkara && tithiFamily === 'Rikta') {
    notes.push(`Pushkara amplifies the day's nature; combined with Rikta tithi, ` +
      'even small inauspicious factors magnify.');
  }
  return { notes, siddhiYogas };
}

export function muPersonalDosha(options): string | null {
  const {
    chandraAvoidNames, hasAshtama, ashtamaLagnaNames,
    chandraPujaNames, taraUnfavNames, siddhiYogas,
  } = options;
  if (chandraAvoidNames.length) {
    return hasAshtama ? 'ashtama_chandra' : 'chandra_avoid';
  }
  if (ashtamaLagnaNames.length) return 'ashtama_lagna';
  if (chandraPujaNames.length) return 'chandra_remedial';
  return taraUnfavNames.length && !siddhiYogas.length ? 'tara_dosha' : null;
}

export function muSlotDayDosha(options) {
  const {
    tithiFamily, facts, nityaYoga, system, effectiveChartRemainder,
    rules, manualGuidance, personal,
  } = options;
  const computed = computeDayDosha({
    tithiFamily,
    isAmavasya: /Amavasya/i.test(facts.tithi),
    hasYogaPenalty: facts.specialYogas.some(
      yoga => MU_YOGA_PENALTY[yoga] !== undefined),
    nityaHardAvoid: MU_NITYA_HARD_AVOID.has(nityaYoga),
  });
  const unresolvedSourcePrerequisite = (
    system === 'drik' && effectiveChartRemainder !== null
      ? effectiveChartRemainder.length > 0
      : !!rules.manual_prerequisites || manualGuidance.chart.length > 0
  );
  return computed || (unresolvedSourcePrerequisite || personal.needsReview
    ? 'practitioner_review'
    : null);
}

export function muDominantChoghadiya(choghadiya, startMinute: number, endMinute: number) {
  let best = null;
  let bestOverlap = 0;
  const touched = [];
  for (const block of choghadiya) {
    const blockStart = muMin(block.start);
    const blockEnd = muMin(block.end);
    const overlap = Math.min(endMinute, blockEnd) - Math.max(startMinute, blockStart);
    if (overlap <= 0) continue;
    touched.push(block.name);
    if (overlap > bestOverlap) {
      best = block;
      bestOverlap = overlap;
    }
  }
  return {
    block: best,
    straddle: best ? touched.find(name => name !== best.name) || null : null,
  };
}

export function muSlotTimeFoundation(options) {
  const {
    mi, srMin, ssMin, muLen, rules, bad, data, abhijit,
    chartLocation, isoDate, date, lagnaCityData, system, activity,
  } = options;
  const s0 = Math.round(srMin + mi * muLen);
  const e0 = Math.round(srMin + (mi + 1) * muLen);
  if (rules.forenoon_only && !muEndsBySolarNoon(e0, srMin, ssMin)) return null;
  if (bad.some(([start, end]) => s0 < end && start < e0)) return null;
  const dominant = muDominantChoghadiya(data.choghadiya, s0, e0);
  if (!dominant.block) return null;
  const slotStart = chartLocation
    ? new Date(localWallTimeToInstant(isoDate, s0, chartLocation.timezone))
    : new Date(date.getTime() + s0 * 60000);
  const facts = muFactsAt(slotStart, data.vaaram);
  const lagnaDay = lagnaCityData ? lagnaDayFor(lagnaCityData, isoDate) : null;
  return {
    s0,
    e0,
    dominant,
    choghadiya: dominant.block,
    base: MU_GOOD_CHOG[dominant.block.name] || 0,
    muRow: MUHURTA_DAY[mi],
    isAbhijit: mi === 7 && !!abhijit,
    facts,
    lagnaDay,
    slotLagna: lagnaDay ? muLagnaAtMin(lagnaDay, s0) : null,
    personal: {
      rejected: false,
      needsReview: system !== 'drik' && !!roleForActivity(activity),
      preferencePasses: 0,
      evidence: system !== 'drik' && roleForActivity(activity)
        ? ['Source-specific personal screening is currently limited to Drik/Lahiri.']
        : [],
      outcomes: [],
      stable: true,
    },
  };
}

export function muSlotElectionReasons(facts, rules, restrictions, data, people) {
  let reasons = [];
  if (rules.require_homa_election) {
    const election = muHomaElection(facts);
    if (!election.admitted) return null;
    reasons = election.reasons;
  }
  if (restrictions.allowedNakshatras.size &&
      !restrictions.allowedNakshatras.has(facts.nakshatra)) return null;
  if (restrictions.avoidNakshatras.has(facts.nakshatra)) return null;
  if (restrictions.avoidJanmaNakshatra && people.some(
    person => muCanonicalNakshatra(person.nak) === facts.nakshatra)) return null;
  const tithiNumber = activityTithiNumber(facts.tithi);
  if (restrictions.allowedTithiNumbers.size &&
      !restrictions.allowedTithiNumbers.has(tithiNumber)) return null;
  if (restrictions.allowedTithiNames.size &&
      !restrictions.allowedTithiNames.has(facts.tithi)) return null;
  if (restrictions.avoidTithiNumbers.has(tithiNumber)) return null;
  return restrictions.avoidVaraTithiNames.has(`${data.vaaram}|${facts.tithi}`)
    ? null
    : reasons;
}

export function muInitialSlotScore(foundation, electionReasons) {
  const { base, muRow, isAbhijit, dominant, choghadiya } = foundation;
  const natureBonus = muNatureBonus(isAbhijit, muRow[2]);
  const muLabel = muRow[0] + (isAbhijit ? ' (Abhijit)' : '');
  const muDeity = muRow[1] ? ` · ${muRow[1]}` : '';
  const straddleDescription = dominant.straddle
    ? ` (spans ${dominant.straddle})`
    : '';
  const chogDescription = `${choghadiya.name} choghadiya${straddleDescription}`;
  const chogLine = base ? `${chogDescription} (+${base})` : chogDescription;
  return {
    score: base + natureBonus,
    slotQuality: [
      `${muLabel} muhurta${muDeity} · ${muRow[2]} (${natureBonus >= 0 ? '+' : ''}${natureBonus})`,
      chogLine,
    ],
    dayQuality: [],
    groupFit: [],
    activityMatch: [...electionReasons],
  };
}

export function muActivityNeedsLagna(activity: string, rules): boolean {
  return Boolean(
    rules.prefer_lagna_class
    || rules.required_lagna_class
    || rules.allowed_lagnas?.length
    || rules.skip_on_combust?.length
    || automatedRulesFor(activity).length
  );
}
