import type { GuestProfile } from '../../lib/guest-profile-store';
import { element, button, appendOption } from './elements';
import { appendExistingProfiles } from './form-view';
import { manualIntroText, nakshatraHelpText } from './form-view';
import { NAKSHATRA_NAMES, RASI_NAMES } from '../../data/rasis';
import type { ProfilePanelHost, ProfileFormRequest, ResolvedProfilesPanelContext } from './contracts';

/** Build labelled controls; request and save state stay in the form workflow. */
export function buildManualFormView(host: ProfilePanelHost, request: ProfileFormRequest) {
  const { mode, context, profile } = request;
  const { root, store, birthCalculationActive, renderIssue, renderBirthForm } = host;
  const fragment = buildIntroduction(request);

  if (!birthCalculationActive) {
    const calculationNotice = element(
      'p',
      'profiles-notice profiles-notice--warning',
      'Birth-detail calculation is not active in this public build. You can still create and use a profile by entering the astrology details you already know.',
    );
    calculationNotice.id = 'profile-calculation-disabled-message';
    fragment.append(calculationNotice);
  }

  const methods = birthCalculationActive ? element('section', 'profiles-methods') : null;
  if (methods) {
    methods.setAttribute('aria-labelledby', 'profile-method-title');
    const methodsTitle = element('h2', 'profiles-methods__title', 'Choose how to add astrology details');
    methodsTitle.id = 'profile-method-title';
    const methodActions = element('div', 'profiles-methods__actions');
    const useBirthDetails = button('Use birth details', 'profiles-methods__choice');
    useBirthDetails.setAttribute('aria-pressed', 'false');
    const useManualDetails = button('Enter astrology details manually', 'profiles-methods__choice profiles-methods__choice--active');
    useManualDetails.setAttribute('aria-pressed', 'true');
    useBirthDetails.addEventListener('click', () => renderBirthForm(mode, context, profile));
    methodActions.append(useBirthDetails, useManualDetails);
    methods.append(methodsTitle, methodActions);
  }
  const snapshot = store.getSnapshot();
  const issue = renderIssue(snapshot);
  if (issue) fragment.append(issue);

  appendExistingProfiles(fragment, mode, context, snapshot.profiles);
  if (methods) fragment.append(methods);

  const form = element('form', 'profiles-form');
  form.noValidate = true;

  const { nameGroup, nameInput, nameError, duplicate } = buildNameField(profile);

  const { nakshatraGroup, nakshatraSelect, nakshatraError } = buildNakshatraField(context, profile);

  const { padaGroup, padaSelect, padaError } = buildPadaField(context, nakshatraSelect, profile);

  const { lagnaGroup, lagnaSelect } = buildLagnaField(profile);

  const formError = element('p', 'profiles-form__error');
  formError.id = 'profile-form-error';
  formError.setAttribute('role', 'alert');
  formError.hidden = true;

  const actions = element('div', 'profiles-form__actions');
  const save = element('button', 'profiles-button profiles-button--primary', mode === 'create' ? 'Save profile' : 'Save changes');
  save.type = 'submit';
  const cancel = button('Cancel', 'profiles-button profiles-button--secondary');
  actions.append(cancel, save);
  form.append(nameGroup, nakshatraGroup, padaGroup, lagnaGroup, formError, actions);
  fragment.append(form);
  root.replaceChildren(fragment);
  return {
    form, nameInput, nameError,
    duplicate, nakshatraSelect, nakshatraError,
    padaSelect, padaError, lagnaSelect,
    formError, cancel,
  };
}

function buildNameField(profile?: GuestProfile) {
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
  const nameHelp = element('p', 'profiles-field__help', 'Use the name you will recognize in personalized tools.');
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

function buildNakshatraField(context: ResolvedProfilesPanelContext, profile?: GuestProfile) {
  const nakshatraGroup = element('div', 'profiles-field');
  const nakshatraLabel = element('label', 'profiles-field__label', 'Nakshatra');
  nakshatraLabel.htmlFor = 'profile-nakshatra';
  const nakshatraSelect = element('select', 'profiles-field__control');
  nakshatraSelect.id = 'profile-nakshatra';
  nakshatraSelect.name = 'nakshatra';
  nakshatraSelect.setAttribute('aria-describedby', 'profile-nakshatra-help profile-nakshatra-error');
  appendOption(nakshatraSelect, '', 'Not added yet');
  for (const nakshatra of NAKSHATRA_NAMES) appendOption(nakshatraSelect, nakshatra, nakshatra);
  nakshatraSelect.value = profile?.nakshatra || '';
  const nakshatraHelp = element(
    'p',
    'profiles-field__help',
    nakshatraHelpText(context.requiredFor),
  );
  nakshatraHelp.id = 'profile-nakshatra-help';
  const nakshatraError = element('p', 'profiles-field__error');
  nakshatraError.id = 'profile-nakshatra-error';
  nakshatraError.hidden = true;
  nakshatraGroup.append(nakshatraLabel, nakshatraSelect, nakshatraHelp, nakshatraError);

  return { nakshatraGroup, nakshatraSelect, nakshatraError };
}

function buildPadaField(context: ResolvedProfilesPanelContext, nakshatraSelect: HTMLSelectElement, profile?: GuestProfile) {
  const padaGroup = element('div', 'profiles-field');
  const padaLabel = element('label', 'profiles-field__label', 'Padam');
  padaLabel.htmlFor = 'profile-pada';
  const padaSelect = element('select', 'profiles-field__control');
  padaSelect.id = 'profile-pada';
  padaSelect.name = 'pada';
  padaSelect.setAttribute('aria-describedby', 'profile-pada-help profile-pada-error');
  appendOption(padaSelect, '', 'Not known');
  for (let value = 1; value <= 4; value += 1) appendOption(padaSelect, String(value), `Padam ${value}`);
  padaSelect.value = profile?.pada ? String(profile.pada) : '';
  padaSelect.disabled = !nakshatraSelect.value;
  const padaHelp = element(
    'p',
    'profiles-field__help',
    context.requiredFor === 'muhurta'
      ? 'Optional for Muhurtam.'
      : 'Needed only when the Nakshatra spans two Rashis.',
  );
  padaHelp.id = 'profile-pada-help';
  const padaError = element('p', 'profiles-field__error');
  padaError.id = 'profile-pada-error';
  padaError.hidden = true;
  padaGroup.append(padaLabel, padaSelect, padaHelp, padaError);

  return { padaGroup, padaSelect, padaError };
}

function buildLagnaField(profile?: GuestProfile) {
  const lagnaGroup = element('div', 'profiles-field');
  const lagnaLabel = element('label', 'profiles-field__label', 'Lagna');
  lagnaLabel.htmlFor = 'profile-lagna';
  const lagnaSelect = element('select', 'profiles-field__control');
  lagnaSelect.id = 'profile-lagna';
  lagnaSelect.name = 'lagna';
  lagnaSelect.setAttribute('aria-describedby', 'profile-lagna-help');
  appendOption(lagnaSelect, '', 'Not added');
  for (const rasi of RASI_NAMES) appendOption(lagnaSelect, rasi, rasi);
  lagnaSelect.value = profile?.lagna || '';
  const lagnaHelp = element('p', 'profiles-field__help', 'Optional. Used only by journeys that support a Lagna view.');
  lagnaHelp.id = 'profile-lagna-help';
  lagnaGroup.append(lagnaLabel, lagnaSelect, lagnaHelp);

  return { lagnaGroup, lagnaSelect };
}

function buildIntroduction(request: ProfileFormRequest): DocumentFragment {
  const { mode, context } = request;
  const fragment = document.createDocumentFragment();
  const heading = element('h1', 'profiles-title', mode === 'create' ? 'Create profile manually' : 'Edit profile manually');
  heading.id = 'profiles-title';
  heading.tabIndex = -1;
  const intro = element(
    'p',
    'profiles-form__intro',
    manualIntroText(context.requiredFor),
  );
  const privacy = element(
    'p',
    'profiles-privacy',
    'Saved only in this browser. Manual details are never sent to a server. No account, cloud sync, or recovery.',
  );
  fragment.append(heading, intro, privacy);
  return fragment;
}
