import {
  BirthProfileApiError, type BirthPlaceCandidate, type BirthProfileDerivation,
} from '../../lib/birth-profile-api';
import { type GuestProfileDraft } from '../../lib/guest-profile-store';
import { ElectionChartApiError, localWallTimeToInstant } from '../../lib/election-chart-api';

export function isoDateInTimeZone(now: Date, timeZone: string): string | null {
  try {
    const formatter = new Intl.DateTimeFormat('en-CA-u-ca-gregory-nu-latn', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
    const values: Record<string, string> = {};
    for (const part of formatter.formatToParts(now)) {
      if (part.type !== 'literal') values[part.type] = part.value;
    }
    return values.year && values.month && values.day
      ? `${values.year}-${values.month}-${values.day}`
      : null;
  } catch {
    return null;
  }
}
export function showFieldError(input: HTMLElement, error: HTMLElement, message: string): void {
  input.setAttribute('aria-invalid', 'true');
  error.textContent = message;
  error.hidden = false;
}

export function validateRequiredBirthInputs(
  fields: BirthValidationFields,
  selectedPlace: BirthPlaceCandidate | null,
): BirthPlaceCandidate | null {
  const invalid = requiredBirthFields(fields, selectedPlace).filter(field => !field.valid);
  for (const field of invalid) showFieldError(field.input, field.error, field.message);
  if (invalid.length === 0) return selectedPlace;
  invalid[0].input.focus();
  return null;
}

function requiredBirthFields(fields: BirthValidationFields, place: BirthPlaceCandidate | null) {
  return [
    { input: fields.dateInput, error: fields.dateError, valid: Boolean(fields.dateInput.value),
      message: 'Enter a valid birth date that is not in the future.' },
    { input: fields.timeInput, error: fields.timeError, valid: /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(fields.timeInput.value),
      message: 'Enter the recorded local birth time.' },
    { input: fields.placeInput, error: fields.placeError, valid: Boolean(place),
      message: 'Find and select a birthplace from the results.' },
  ];
}

export function wallTimeErrorMessage(error: unknown): string | null {
  if (!(error instanceof ElectionChartApiError)) return null;
  if (error.message.includes('ambiguous')) {
    return 'This local time occurred twice at the selected birthplace. Enter known astrology details manually instead.';
  }
  if (error.message.includes('does not exist')) {
    return 'This local time did not occur at the selected birthplace because the clocks changed. Enter known astrology details manually instead.';
  }
  return null;
}

export interface BirthValidationFields {
  dateInput: HTMLInputElement;
  dateError: HTMLElement;
  timeInput: HTMLInputElement;
  timeError: HTMLElement;
  placeInput: HTMLInputElement;
  placeError: HTMLElement;
}

export function validatedBirthInstant(
  fields: BirthValidationFields,
  place: BirthPlaceCandidate,
  now: Date,
): string | null {
  const { dateInput, dateError, timeInput, timeError, placeInput, placeError } = fields;
  const maxDate = isoDateInTimeZone(now, place.timezone);
  if (!maxDate) {
    showFieldError(placeInput, placeError, 'The selected birthplace has an invalid time zone.');
    placeInput.focus();
    return null;
  }
  dateInput.max = maxDate;
  if (dateInput.value > maxDate) {
    showFieldError(dateInput, dateError, 'Enter a valid birth date that is not in the future.');
    dateInput.focus();
    return null;
  }
  const [birthHour, birthMinute] = timeInput.value.split(':').map(Number);
  let birthInstant: string;
  try {
    birthInstant = localWallTimeToInstant(
      dateInput.value,
      birthHour * 60 + birthMinute,
      place.timezone,
    );
  } catch (error) {
    const timeMessage = wallTimeErrorMessage(error);
    if (timeMessage) {
      showFieldError(timeInput, timeError, timeMessage);
      timeInput.focus();
      return null;
    }
    showFieldError(placeInput, placeError, 'The selected birthplace or time zone is invalid.');
    placeInput.focus();
    return null;
  }
  if (Date.parse(birthInstant) <= now.getTime()) return birthInstant;
  showFieldError(
    timeInput,
    timeError,
    'Birth date and time cannot be in the future at the selected birthplace.',
  );
  timeInput.focus();
  return null;
}
export function birthApiMessage(error: unknown): string {
  if (!(error instanceof BirthProfileApiError)) {
    return 'We could not calculate this profile. Check the details and try again.';
  }
  if (error.code === 'rate-limited' && error.retryAfterSeconds) {
    return `Too many requests. Try again in about ${error.retryAfterSeconds} seconds.`;
  }
  return error.message;
}

export function birthDraft(
  input: { name: string; dateOfBirth: string; timeOfBirth: string },
  place: BirthPlaceCandidate,
  result: BirthProfileDerivation,
): GuestProfileDraft {
  const { name, dateOfBirth, timeOfBirth } = input;
  return {
    source: 'birth-details',
    name,
    nakshatra: result.nakshatra,
    pada: result.pada,
    janmaRasi: result.janmaRashi,
    lagna: result.lagna,
    birthDetails: {
      dateOfBirth,
      timeOfBirth,
      placeLabel: place.label,
      latitude: place.latitude,
      longitude: place.longitude,
      timezone: place.timezone,
    },
    natalChart: {
      lagnaDegree: result.lagnaDegree,
      planets: result.planets,
    },
    calculation: {
      contractVersion: result.contractVersion,
      engine: result.engine,
    },
  };
}
