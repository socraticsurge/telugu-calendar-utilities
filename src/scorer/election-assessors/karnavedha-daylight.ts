export const KARNAVEDHA_DAYLIGHT_POLICY_ID = 'raman-karnavedha-daylight-v1';
export const KARNAVEDHA_DAYLIGHT_POLICY_CLAIM =
  'election_day.karnavedha_daylight_policy_v1';
export const KARNAVEDHA_TITHI_RULE_ID = 'karnavedha.daylight-tithi-single';
export const KARNAVEDHA_NAKSHATRA_RULE_ID = 'karnavedha.daylight-nakshatra-single';

const SOURCE_CLAIM = 'muhurta.karnavedha';
const SOURCE_LOCATOR = 'B. V. Raman, Chapter VIII, \'Ear boring (Karnavedha),\' '
  + 'inspected in the 2020 Chistabo derivative at internal printed p. 23 '
  + '(physical PDF p. 26)';
const TIME = /^(?:[01]\d|2[0-3]):[0-5]\d$/;

export type KarnavedhaDaylightStatus = 'pass' | 'fail' | 'unknown';

export interface KarnavedhaParsedSpan {
  name?: string | null;
  start?: string | null;
  sflag?: string | null;
  end?: string | null;
  eflag?: string | null;
}

export interface KarnavedhaDaylightInput {
  sunrise?: string | null;
  sunset?: string | null;
  tithi?: KarnavedhaParsedSpan | null;
  nakshatra?: KarnavedhaParsedSpan | null;
}

export interface KarnavedhaDaylightOutcome {
  ruleId: string;
  label: string;
  effect: 'reject';
  sourceClaim: string;
  sourceLocator: string;
  policyId: string;
  decisionPolicyClaim: string;
  interval: '[local sunrise, local sunset)';
  status: KarnavedhaDaylightStatus;
  evidence: string[];
  activeName?: string;
  transition?: string;
}

export interface KarnavedhaDaylightAssessment {
  policyId: string;
  policyClaim: string;
  interval: '[local sunrise, local sunset)';
  outcomes: KarnavedhaDaylightOutcome[];
  rejected: boolean;
  needsReview: boolean;
  admissible: boolean;
}

const CONFIGURATION_ERROR =
  'The configured Karnavedha daylight policy is missing or unsupported.';

interface Rule {
  id: string;
  label: string;
  limb: 'Tithi' | 'Nakshatra';
  attribute: 'tithi' | 'nakshatra';
}

const RULES: readonly Rule[] = [
  {
    id: KARNAVEDHA_TITHI_RULE_ID,
    label: 'One Tithi rules throughout local daylight',
    limb: 'Tithi',
    attribute: 'tithi',
  },
  {
    id: KARNAVEDHA_NAKSHATRA_RULE_ID,
    label: 'One Nakshatra rules throughout local daylight',
    limb: 'Nakshatra',
    attribute: 'nakshatra',
  },
];

function minute(time: unknown, flag: unknown = null): number | null {
  if (typeof time !== 'string' || !TIME.test(time)) return null;
  if (flag !== null && flag !== undefined && flag !== '+1' && flag !== '-1') {
    return null;
  }
  const [hour, value] = time.split(':').map(Number);
  return hour * 60 + value + (flag === '+1' ? 1_440 : flag === '-1' ? -1_440 : 0);
}

function boundaryLabel(time: string, flag: string | null | undefined): string {
  if (flag === '+1') return `${time} next day`;
  if (flag === '-1') return `${time} previous day`;
  return time;
}

function base(rule: Rule): Omit<KarnavedhaDaylightOutcome, 'status' | 'evidence'> {
  return {
    ruleId: rule.id,
    label: rule.label,
    effect: 'reject',
    sourceClaim: SOURCE_CLAIM,
    sourceLocator: SOURCE_LOCATOR,
    policyId: KARNAVEDHA_DAYLIGHT_POLICY_ID,
    decisionPolicyClaim: KARNAVEDHA_DAYLIGHT_POLICY_CLAIM,
    interval: '[local sunrise, local sunset)',
  };
}

function unknown(rule: Rule, detail: string): KarnavedhaDaylightOutcome {
  return { ...base(rule), status: 'unknown', evidence: [detail] };
}

function assessment(
  outcomes: KarnavedhaDaylightOutcome[],
): KarnavedhaDaylightAssessment {
  return {
    policyId: KARNAVEDHA_DAYLIGHT_POLICY_ID,
    policyClaim: KARNAVEDHA_DAYLIGHT_POLICY_CLAIM,
    interval: '[local sunrise, local sunset)',
    outcomes,
    rejected: outcomes.some(outcome => outcome.status === 'fail'),
    needsReview: outcomes.some(outcome => outcome.status === 'unknown'),
    admissible: outcomes.every(outcome => outcome.status === 'pass'),
  };
}

function evaluateLimb(
  input: KarnavedhaDaylightInput,
  rule: Rule,
  sunrise: number,
  sunset: number,
): KarnavedhaDaylightOutcome {
  const span = input[rule.attribute];
  if (!span || typeof span !== 'object') {
    return unknown(rule, `${rule.limb} transition span is unavailable.`);
  }
  const { name, start, sflag = null, end, eflag = null } = span;
  if (typeof name !== 'string' || !name.trim()) {
    return unknown(rule, `${rule.limb} name is unavailable.`);
  }
  const startMinute = minute(start, sflag);
  const endMinute = minute(end, eflag);
  if (startMinute === null || endMinute === null) {
    return unknown(rule, `${rule.limb} transition boundary is malformed.`);
  }
  if (startMinute >= endMinute) {
    return unknown(rule, `${rule.limb} transition span is not ordered.`);
  }
  if (startMinute > sunrise || endMinute <= sunrise) {
    return unknown(
      rule,
      `${name} does not contain local sunrise, so the active ${rule.limb} boundary is uncertain.`,
    );
  }
  if (endMinute === sunset) {
    return unknown(
      rule,
      `${name} changes in the displayed sunset minute; minute-precision feed data cannot prove whether the transition is inside the half-open daylight interval.`,
    );
  }
  const transition = boundaryLabel(end as string, eflag);
  if (endMinute < sunset) {
    return {
      ...base(rule),
      status: 'fail',
      evidence: [
        `${name} ends at ${transition}, inside daylight [${input.sunrise}, ${input.sunset}).`,
      ],
      activeName: name,
      transition,
    };
  }
  return {
    ...base(rule),
    status: 'pass',
    evidence: [`${name} remains active throughout daylight; its next transition is ${transition}.`],
    activeName: name,
    transition,
  };
}

export function evaluateKarnavedhaDaylight(
  input: KarnavedhaDaylightInput,
): KarnavedhaDaylightAssessment {
  const sunrise = minute(input.sunrise);
  const sunset = minute(input.sunset);
  const validDaylight = sunrise !== null && sunset !== null && sunrise < sunset;
  const outcomes = validDaylight
    ? RULES.map(rule => evaluateLimb(input, rule, sunrise, sunset))
    : RULES.map(rule => unknown(
      rule,
      'Local daylight boundaries are missing, malformed, or unordered.',
    ));
  return assessment(outcomes);
}

/** Apply the configured named policy, failing closed on contract drift. */
export function evaluateConfiguredKarnavedhaDaylight(
  input: KarnavedhaDaylightInput,
  tithiPolicy: unknown,
  nakshatraPolicy: unknown,
): KarnavedhaDaylightAssessment {
  if (
    tithiPolicy !== KARNAVEDHA_DAYLIGHT_POLICY_ID
    || nakshatraPolicy !== KARNAVEDHA_DAYLIGHT_POLICY_ID
  ) {
    return assessment(RULES.map(rule => unknown(rule, CONFIGURATION_ERROR)));
  }
  return evaluateKarnavedhaDaylight(input);
}

export function karnavedhaDaylightDropReason(
  assessment: KarnavedhaDaylightAssessment,
): string {
  const details = assessment.outcomes.flatMap(outcome => {
    if (outcome.status === 'pass') return [];
    const limb = outcome.ruleId === KARNAVEDHA_TITHI_RULE_ID ? 'Tithi' : 'Nakshatra';
    if (outcome.status === 'fail' && outcome.transition) {
      return [`${limb} changes at ${outcome.transition} inside local daylight`];
    }
    return [`${limb} boundary could not be verified`];
  });
  return details.length
    ? `Karnavedha daylight rule · ${details.join('; ')}`
    : 'Karnavedha daylight rule admitted';
}
