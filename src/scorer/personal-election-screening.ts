import { NAKSHATRA_NAMES, RASI_NAMES } from '../data/rasis';

export type MuhurtamParticipantRole = 'traveller' | 'homeowner' | 'mother' | 'patient';
export type PersonalRuleStatus = 'pass' | 'fail' | 'unknown';
export type PersonalRuleEffect = 'reject' | 'prefer';

export interface MuhurtamRoleRequirement {
  role: MuhurtamParticipantRole;
  label: string;
  prompt: string;
  cardinality: 1;
  required: true;
  ruleIds: string[];
}

export interface PersonalElectionParticipant {
  id: string;
  name: string;
  nakshatra: string | null;
  janmaRashi: string | null;
  janmaLagna: string | null;
}

export interface PersonalElectionFacts {
  nakshatra: string;
  lunarRashi: string | null;
  lagna: string | null;
}

export interface PersonalElectionScreening {
  rejected: boolean;
  needsReview: boolean;
  preferencePasses: number;
  evidence: string[];
  outcomes: PersonalElectionOutcome[];
  stable: boolean;
}

export interface PersonalElectionOutcome {
  ruleId: string;
  label: string;
  effect: PersonalRuleEffect;
  sourceClaim: string;
  sourceLocator: string;
  status: PersonalRuleStatus;
  inputs: Record<string, unknown>;
}

interface PersonalRuleDefinition {
  ruleId: string;
  label: string;
  effect: PersonalRuleEffect;
  sourceClaim: string;
  sourceLocator: string;
}

const LOCATORS = {
  travel: "B. V. Raman, Chapter XIV, 'Journeys' and 'Long-distance Journeys,' inspected in the 2020 Chistabo derivative at internal printed pp. 60-61 (physical PDF pp. 64-65)",
  gruhapravesha: "B. V. Raman, Chapter XII, 'House building,' section 'Entering a new house,' inspected in the 2020 Chistabo derivative at internal printed pp. 52-54 (physical PDF pp. 56-58)",
  seemantha: "B. V. Raman, Chapter VII-VIII transition, 'Seemantha,' inspected in the 2020 Chistabo derivative at internal printed pp. 21-22 (physical PDF pp. 24-25)",
  surgery: "B. V. Raman, Chapter XV, 'Surgical Operations,' inspected in the 2020 Chistabo derivative at internal printed pp. 64-65 (physical PDF pp. 68-69)",
} as const;

const PERSONAL_RULES: Record<string, PersonalRuleDefinition[]> = {
  travel: [
    {
      ruleId: 'personal.travel.lagna-exclusions',
      label: "Candidate Lagna avoids the 1st, 5th, 7th and 9th from the traveller's Janma Lagna",
      effect: 'reject', sourceClaim: 'muhurta.travel', sourceLocator: LOCATORS.travel,
    },
    {
      ruleId: 'personal.travel.janma-rashi-lagna',
      label: "Candidate Lagna matches the traveller's Janma Rashi",
      effect: 'prefer', sourceClaim: 'muhurta.travel', sourceLocator: LOCATORS.travel,
    },
  ],
  gruhapravesha: [{
    ruleId: 'personal.gruhapravesha.natal-anchor-match',
    label: "Candidate Nakshatra, Chandra Rashi or Lagna matches the householder's natal anchor",
    effect: 'prefer', sourceClaim: 'muhurta.gruhapravesha', sourceLocator: LOCATORS.gruhapravesha,
  }],
  seemantha: [{
    ruleId: 'personal.seemantha.birth-star-exclusions',
    label: "Candidate Nakshatra avoids the 3rd, 7th, 8th, 10th and 22nd from the mother's birth star",
    effect: 'reject', sourceClaim: 'muhurta.seemantha', sourceLocator: LOCATORS.seemantha,
  }],
  surgery: [{
    ruleId: 'personal.surgery.chandra-outside-janma-rashi',
    label: "Chandra is outside the patient's Janma Rashi",
    effect: 'reject', sourceClaim: 'muhurta.surgery', sourceLocator: LOCATORS.surgery,
  }],
};

const ROLE_BY_ACTIVITY: Record<string, MuhurtamRoleRequirement> = {
  travel: {
    role: 'traveller',
    label: 'Primary traveller',
    prompt: 'Whose birth chart should govern the journey-specific checks?',
    cardinality: 1, required: true,
    ruleIds: PERSONAL_RULES.travel.map(rule => rule.ruleId),
  },
  gruhapravesha: {
    role: 'homeowner',
    label: 'Primary householder',
    prompt: 'Whose birth chart should govern the home-entry checks?',
    cardinality: 1, required: true,
    ruleIds: PERSONAL_RULES.gruhapravesha.map(rule => rule.ruleId),
  },
  seemantha: {
    role: 'mother',
    label: 'Mother',
    prompt: 'Whose birth star should govern the Seemantha checks?',
    cardinality: 1, required: true,
    ruleIds: PERSONAL_RULES.seemantha.map(rule => rule.ruleId),
  },
  surgery: {
    role: 'patient',
    label: 'Patient',
    prompt: 'Whose birth chart should govern the surgery checks?',
    cardinality: 1, required: true,
    ruleIds: PERSONAL_RULES.surgery.map(rule => rule.ruleId),
  },
};

export function roleForActivity(activity: string): MuhurtamRoleRequirement | null {
  return ROLE_BY_ACTIVITY[activity] || null;
}

function emptyResult(): PersonalElectionScreening {
  return {
    rejected: false,
    needsReview: false,
    preferencePasses: 0,
    evidence: [],
    outcomes: [],
    stable: true,
  };
}

function addOutcome(
  result: PersonalElectionScreening,
  definition: PersonalRuleDefinition,
  status: PersonalRuleStatus,
  inputs: Record<string, unknown>,
  evidence: string,
): void {
  result.outcomes.push({ ...definition, status, inputs });
  result.evidence.push(evidence);
  if (status === 'unknown') result.needsReview = true;
  if (status === 'fail' && definition.effect === 'reject') result.rejected = true;
  if (status === 'pass' && definition.effect === 'prefer') result.preferencePasses += 1;
}

function inclusivePosition(order: readonly string[], origin: string, target: string): number | null {
  const from = order.indexOf(origin);
  const to = order.indexOf(target);
  return from < 0 || to < 0 ? null : ((to - from + order.length) % order.length) + 1;
}

function ordinal(value: number): string {
  const mod100 = value % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${value}th`;
  const suffix: Record<number, string> = { 1: 'st', 2: 'nd', 3: 'rd' };
  return `${value}${suffix[value % 10] || 'th'}`;
}

export function evaluatePersonalElectionRules(
  activity: string,
  participant: PersonalElectionParticipant | null,
  facts: PersonalElectionFacts,
): PersonalElectionScreening {
  const result = emptyResult();
  const role = roleForActivity(activity);
  if (!role) return result;
  if (!participant) {
    for (const rule of PERSONAL_RULES[activity]) {
      addOutcome(
        result,
        rule,
        'unknown',
        { participantRole: role.role, participantSelected: false },
        `Choose the ${role.label.toLowerCase()} for ${rule.label.toLowerCase()}.`,
      );
    }
    return result;
  }

  if (activity === 'travel') {
    const [lagnaRule, rashiRule] = PERSONAL_RULES.travel;
    if (!participant.janmaLagna || !facts.lagna) {
      addOutcome(
        result, lagnaRule, 'unknown',
        { janmaLagna: participant.janmaLagna, candidateLagna: facts.lagna },
        `Travel Lagna screening needs ${participant.name}'s Janma Lagna and the candidate Lagna.`,
      );
    } else {
      const position = inclusivePosition(RASI_NAMES, participant.janmaLagna, facts.lagna);
      if (position === null) {
        addOutcome(
          result, lagnaRule, 'unknown',
          { janmaLagna: participant.janmaLagna, candidateLagna: facts.lagna },
          'The travel Lagna position could not be resolved.',
        );
      } else {
        const excluded = [1, 5, 7, 9].includes(position);
        addOutcome(
          result, lagnaRule, excluded ? 'fail' : 'pass',
          { janmaLagna: participant.janmaLagna, candidateLagna: facts.lagna, position },
          excluded
            ? `${facts.lagna} is ${position === 1 ? 'the same as' : `the ${ordinal(position)} from`} ${participant.name}'s Janma Lagna; the travel source excludes it.`
            : `${facts.lagna} avoids the travel source's 1st, 5th, 7th and 9th Lagna exclusions.`,
        );
      }
    }
    const rashiResolved = !!participant.janmaRashi && !!facts.lagna;
    const rashiMatches = rashiResolved && facts.lagna === participant.janmaRashi;
    addOutcome(
      result, rashiRule, rashiResolved ? (rashiMatches ? 'pass' : 'fail') : 'unknown',
      { janmaRashi: participant.janmaRashi, candidateLagna: facts.lagna },
      rashiMatches
        ? `${facts.lagna} Lagna matches ${participant.name}'s Janma Rashi.`
        : rashiResolved
          ? `${facts.lagna} Lagna does not match ${participant.name}'s Janma Rashi; this is not a rejection.`
          : `Travel preference screening needs ${participant.name}'s Janma Rashi and the candidate Lagna.`,
    );
    return result;
  }

  if (activity === 'gruhapravesha') {
    const matches: string[] = [];
    if (participant.nakshatra && facts.nakshatra === participant.nakshatra) {
      matches.push('Janma Nakshatra');
    }
    if (participant.janmaRashi && facts.lunarRashi === participant.janmaRashi) {
      matches.push('Janma Rashi');
    }
    if (participant.janmaLagna && facts.lagna === participant.janmaLagna) {
      matches.push('Janma Lagna');
    }
    const inputs = {
      janmaNakshatra: participant.nakshatra,
      candidateNakshatra: facts.nakshatra,
      janmaRashi: participant.janmaRashi,
      candidateChandraRashi: facts.lunarRashi,
      janmaLagna: participant.janmaLagna,
      candidateLagna: facts.lagna,
    };
    const pairs = [
      [participant.nakshatra, facts.nakshatra],
      [participant.janmaRashi, facts.lunarRashi],
      [participant.janmaLagna, facts.lagna],
    ];
    const allPairsResolved = pairs.every(([origin, candidate]) => !!origin && !!candidate);
    const status: PersonalRuleStatus = matches.length
      ? 'pass'
      : allPairsResolved ? 'fail' : 'unknown';
    addOutcome(
      result,
      PERSONAL_RULES.gruhapravesha[0],
      status,
      inputs,
      matches.length
        ? `${participant.name}'s ${matches.join(' / ')} supports this Gruhapravesha election.`
        : allPairsResolved
          ? 'No owner-specific Janma match is present; this is not a rejection.'
          : 'A home-entry match cannot be ruled out until all three natal and candidate anchors are available.',
    );
    return result;
  }

  if (activity === 'seemantha') {
    const rule = PERSONAL_RULES.seemantha[0];
    if (!participant.nakshatra) {
      addOutcome(
        result, rule, 'unknown',
        { janmaNakshatra: null, candidateNakshatra: facts.nakshatra, position: null },
        `Seemantha screening needs ${participant.name}'s Janma Nakshatra.`,
      );
      return result;
    }
    const position = inclusivePosition(NAKSHATRA_NAMES, participant.nakshatra, facts.nakshatra);
    if (position === null) {
      addOutcome(
        result, rule, 'unknown',
        { janmaNakshatra: participant.nakshatra, candidateNakshatra: facts.nakshatra, position },
        'The Seemantha birth-star position could not be resolved.',
      );
      return result;
    }
    const excluded = [3, 7, 8, 10, 22].includes(position);
    addOutcome(
      result, rule, excluded ? 'fail' : 'pass',
      { janmaNakshatra: participant.nakshatra, candidateNakshatra: facts.nakshatra, position },
      excluded
        ? `${facts.nakshatra} is the ${ordinal(position)} Nakshatra from ${participant.name}'s birth star; the Seemantha source excludes it.`
        : `The mother's ${ordinal(position)} Nakshatra position is admitted.`,
    );
    return result;
  }

  const rule = PERSONAL_RULES.surgery[0];
  if (!participant.janmaRashi || !facts.lunarRashi) {
    addOutcome(
      result, rule, 'unknown',
      { janmaRashi: participant.janmaRashi, candidateChandraRashi: facts.lunarRashi },
      `Surgery screening needs ${participant.name}'s Janma Rashi and candidate Chandra Rashi.`,
    );
    return result;
  }
  const excluded = facts.lunarRashi === participant.janmaRashi;
  addOutcome(
    result, rule, excluded ? 'fail' : 'pass',
    { janmaRashi: participant.janmaRashi, candidateChandraRashi: facts.lunarRashi },
    excluded
      ? `Chandra is in ${participant.name}'s Janma Rashi; the surgery source excludes it.`
      : `Chandra is outside ${participant.name}'s Janma Rashi.`,
  );
  return result;
}

/** Compatibility wrapper for a two-snapshot offered window. */
export function evaluatePersonalElectionWindow(
  activity: string,
  participant: PersonalElectionParticipant | null,
  startFacts: PersonalElectionFacts,
  endFacts: PersonalElectionFacts,
): PersonalElectionScreening {
  const result = evaluatePersonalElectionSnapshots(
    activity, participant, [startFacts, endFacts],
  );
  return {
    ...result,
    outcomes: result.outcomes.map(outcome => ({
      ...outcome,
      inputs: {
        start: outcome.inputs.start,
        end: outcome.inputs.end,
      },
    })),
  };
}

/** Conservatively combine personal outcomes at every sampled chart state. */
export function evaluatePersonalElectionSnapshots(
  activity: string,
  participant: PersonalElectionParticipant | null,
  facts: readonly PersonalElectionFacts[],
): PersonalElectionScreening {
  const evaluations = (facts.length ? facts : [{
    nakshatra: '', lunarRashi: null, lagna: null,
  }]).map(item => evaluatePersonalElectionRules(activity, participant, item));
  const start = evaluations[0];
  const result = emptyResult();
  result.stable = facts.length > 0;

  for (const startOutcome of start.outcomes) {
    const boundaryOutcomes = evaluations.map(evaluation =>
      evaluation.outcomes.find(outcome => outcome.ruleId === startOutcome.ruleId));
    const statuses = boundaryOutcomes.map(outcome => outcome?.status || 'unknown');
    let status: PersonalRuleStatus = 'unknown';
    if (statuses.includes('unknown')) {
      status = 'unknown';
    } else if (startOutcome.effect === 'reject') {
      status = statuses.includes('fail') ? 'fail' : 'pass';
    } else if (statuses.every(value => value === 'pass')) {
      status = 'pass';
    } else if (statuses.every(value => value === 'fail')) {
      status = 'fail';
    } else {
      status = 'unknown';
    }
    if (!statuses.every(value => value === statuses[0])) result.stable = false;
    const missingEvidence = [...new Set(evaluations.flatMap((evaluation, index) => {
      const outcome = boundaryOutcomes[index];
      if (outcome?.status !== 'unknown') return [];
      const outcomeIndex = evaluation.outcomes.findIndex(
        candidate => candidate.ruleId === startOutcome.ruleId,
      );
      return outcomeIndex >= 0 && evaluation.evidence[outcomeIndex]
        ? [evaluation.evidence[outcomeIndex]]
        : [];
    }))];
    addOutcome(
      result,
      startOutcome,
      status,
      {
        start: boundaryOutcomes[0]?.inputs || null,
        end: boundaryOutcomes[boundaryOutcomes.length - 1]?.inputs || null,
        boundaries: boundaryOutcomes.map(outcome => outcome?.inputs || null),
      },
      status === 'pass'
        ? `Every sampled window state passes: ${startOutcome.label}.`
        : status === 'fail' && startOutcome.effect === 'prefer'
          ? `The source preference is absent throughout the sampled window: ${startOutcome.label}.`
          : status === 'fail'
            ? `At least one sampled window state fails: ${startOutcome.label}.`
            : missingEvidence.length
              ? missingEvidence.join(' ')
              : `The sampled window states do not give one stable result: ${startOutcome.label}.`,
    );
  }
  return result;
}
