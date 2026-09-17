import { type ProfilesPanelContext, type ResolvedProfilesPanelContext } from './contracts';
import { element } from './elements';
import { GuestProfileStore, guestProfileReadiness, type GuestProfile } from '../../lib/guest-profile-store';

export function displayName(profile: GuestProfile): string {
  return profile.name || 'Unnamed profile';
}

export function buildNameField(helpText: string, profile?: GuestProfile) {
  const nameGroup = element('div', 'profiles-field');
  const nameLabel = element('label', 'profiles-field__label', 'Name');
  nameLabel.htmlFor = 'profile-name';
  const nameInput = element('input', 'profiles-field__control');
  nameInput.id = 'profile-name';
  nameInput.name = 'name';
  nameInput.type = 'text';
  nameInput.required = true;
  nameInput.maxLength = 80;
  nameInput.autocomplete = 'name';
  nameInput.value = profile?.name || '';
  nameInput.setAttribute('aria-describedby', 'profile-name-help profile-name-error profile-name-duplicate');
  const nameHelp = element('p', 'profiles-field__help', helpText);
  nameHelp.id = 'profile-name-help';
  const nameError = element('p', 'profiles-field__error');
  nameError.id = 'profile-name-error';
  nameError.hidden = true;
  const duplicate = element('p', 'profiles-field__warning');
  duplicate.id = 'profile-name-duplicate';
  duplicate.setAttribute('role', 'status');
  duplicate.hidden = true;
  nameGroup.append(nameLabel, nameInput, nameHelp, nameError, duplicate);
  return { nameGroup, nameInput, nameError, duplicate };
}

export function normalizedName(value: string): string {
  return value.trim().toLocaleLowerCase();
}
export function updateProfileDuplicateWarning(
  duplicate: HTMLElement,
  nameInput: HTMLInputElement,
  store: GuestProfileStore,
  profileId?: string,
): void {
  const candidate = normalizedName(nameInput.value);
  const duplicateProfile = candidate
    ? store.getSnapshot().profiles.find(existing => (
      existing.id !== profileId && normalizedName(existing.name) === candidate
    ))
    : undefined;
  duplicate.hidden = !duplicateProfile;
  duplicate.textContent = duplicateProfile
    ? `A profile named ${displayName(duplicateProfile)} already exists. You can still save this profile.`
    : '';
}
export const contextualReadinessText = (
  profile: GuestProfile,
  requiredFor?: ProfilesPanelContext['requiredFor'],
): string => {
  const readiness = guestProfileReadiness(profile);
  if (requiredFor === 'muhurta') {
    return readiness.muhurta ? 'Ready for Muhurtam' : 'Needs Nakshatra';
  }
  if (requiredFor === 'horoscope') {
    if (readiness.horoscope) return 'Ready for Daily Horoscope';
    return readiness.missingForHoroscope === 'pada' ? 'Needs Padam' : 'Needs Nakshatra';
  }
  if (readiness.muhurta && readiness.horoscope) return 'Ready for both journeys';
  if (readiness.muhurta) {
    return readiness.missingForHoroscope === 'pada'
      ? 'Ready for Muhurtam · Needs Padam for Daily Horoscope'
      : 'Ready for Muhurtam';
  }
  return 'Needs Nakshatra';
};

export const appendExistingProfiles = (
  fragment: DocumentFragment,
  mode: 'create' | 'edit',
  context: ResolvedProfilesPanelContext,
  profiles: readonly Readonly<GuestProfile>[],
): void => {
  if (mode !== 'create' || (!context.returnTo && !context.requiredFor) || profiles.length === 0) return;
  const existing = element('section', 'profiles-form__existing');
  existing.setAttribute('aria-labelledby', 'profiles-existing-title');
  const existingTitle = element('h2', 'profiles-form__existing-title', 'Already saved');
  existingTitle.id = 'profiles-existing-title';
  const existingHint = element(
    'p',
    'profiles-form__existing-hint',
    'If this person is already listed, cancel and edit that profile instead of creating a duplicate.',
  );
  const existingList = element('ul', 'profiles-form__existing-list');
  for (const existingProfile of profiles) {
    const item = element('li', 'profiles-form__existing-item');
    item.append(
      element('span', 'profiles-form__existing-name', displayName(existingProfile)),
      element(
        'span',
        'profiles-form__existing-readiness',
        contextualReadinessText(existingProfile, context.requiredFor),
      ),
    );
    existingList.append(item);
  }
  existing.append(existingTitle, existingHint, existingList);
  fragment.append(existing);
};


export function manualIntroText(requiredFor?: ProfilesPanelContext['requiredFor']): string {
  if (requiredFor === 'horoscope') {
    return 'Add the birth details needed for Daily Horoscope. Nakshatra is required; Padam is required only when the birth star spans two Rashis. Lagna remains optional.';
  }
  if (requiredFor === 'muhurta') {
    return 'Add a name and Nakshatra to use this profile in Muhurtam. Padam and Lagna are optional for this journey.';
  }
  return 'Start with a name. Nakshatra makes the profile ready for Muhurtam; Padam may be needed to derive Janma Rashi for Daily Horoscope.';
}

export function nakshatraHelpText(requiredFor?: ProfilesPanelContext['requiredFor']): string {
  if (requiredFor === 'horoscope') {
    return 'Required to derive Janma Rashi for Daily Horoscope.';
  }
  if (requiredFor === 'muhurta') return 'Required for Muhurtam.';
  return 'Required for Muhurtam and for deriving Janma Rashi.';
}

export function validateProfileName(
  name: string,
  input: HTMLInputElement,
  error: HTMLElement,
): boolean {
  if (name) return true;
  input.setAttribute('aria-invalid', 'true');
  error.textContent = 'Enter a name for this profile.';
  error.hidden = false;
  input.focus();
  return false;
}
