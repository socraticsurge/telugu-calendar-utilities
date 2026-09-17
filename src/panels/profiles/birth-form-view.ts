import type { GuestProfile } from '../../lib/guest-profile-store';
import { element, button } from './elements';
import { appendExistingProfiles } from './form-view';
import type { BirthPlaceCandidate, BirthProfileDerivation } from '../../lib/birth-profile-api';
import type { ProfilePanelHost, ProfileFormRequest } from './contracts';

/** Build labelled controls; request and save state stay in the form workflow. */
export function buildBirthFormView(host: ProfilePanelHost, request: ProfileFormRequest,
  initial: { place: BirthPlaceCandidate | null; calculated: BirthProfileDerivation | null }) {
  const { mode, context, profile } = request;
  const { root, store, renderIssue, renderManualForm } = host;
  const { place: initialPlace, calculated } = initial;
  const fragment = buildIntroduction(request);

  const snapshot = store.getSnapshot();
  const issue = renderIssue(snapshot);
  if (issue) fragment.append(issue);

  appendExistingProfiles(fragment, mode, context, snapshot.profiles);

  fragment.append(buildMethodChoices(host, request));

  const form = element('form', 'profiles-form profiles-birth-form');
  form.noValidate = true;

  const { nameGroup, nameInput, nameError, duplicate } = buildNameField(profile);

  const {
    knownDetails, dateInput, dateError,
    timeInput, timeError, placeInput,
    searchButton, selectedPlaceText, placeError,
    placeStatus, placeAttribution, placeResults,
  } = buildBirthFields(initialPlace, profile);

  const timeFallback = element('aside', 'profiles-time-fallback');
  const timeFallbackText = element(
    'p',
    'profiles-time-fallback__text',
    'Do not know the exact birth time? You can still save a useful manual profile if you know the Nakshatra.',
  );
  const timeFallbackButton = button(
    'Enter known astrology details instead',
    'profiles-button profiles-button--quiet',
  );
  timeFallbackButton.addEventListener('click', () => renderManualForm(mode, context, profile));
  timeFallback.append(timeFallbackText, timeFallbackButton);

  const { calculationArea, calculateButton, calculationStatus, calculationError } = buildCalculationArea(calculated);

  const reviewHost = element('div', 'profiles-birth-review-host');
  const formError = element('p', 'profiles-form__error');
  formError.id = 'profile-form-error';
  formError.setAttribute('role', 'alert');
  formError.hidden = true;

  const { actions, save, saveHelp, cancel } = buildSaveActions(mode, calculated);

  form.append(
    nameGroup,
    knownDetails,
    timeFallback,
    calculationArea,
    reviewHost,
    formError,
    saveHelp,
    actions,
  );
  fragment.append(form);
  root.replaceChildren(fragment);
  return {
    form, nameInput, nameError,
    duplicate, dateInput, dateError,
    timeInput, timeError, placeInput,
    searchButton, selectedPlaceText, placeError,
    placeStatus, placeAttribution, placeResults,
    calculateButton, calculationStatus, calculationError,
    reviewHost, formError, save,
    saveHelp, cancel,
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
  const nameHelp = element(
    'p',
    'profiles-field__help',
    'This label stays local and is never included in the calculation request.',
  );
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

function buildBirthFields(initialPlace: BirthPlaceCandidate | null, profile?: GuestProfile) {
  const knownDetails = element('fieldset', 'profiles-birth-details');
  const knownLegend = element('legend', 'profiles-birth-details__legend', 'Birth details');
  const dateTimeGrid = element('div', 'profiles-birth-details__grid');

  const dateGroup = element('div', 'profiles-field');
  const dateLabel = element('label', 'profiles-field__label', 'Date of birth');
  dateLabel.htmlFor = 'profile-birth-date';
  const dateInput = element('input', 'profiles-field__control');
  dateInput.id = 'profile-birth-date';
  dateInput.name = 'dateOfBirth';
  dateInput.type = 'date';
  dateInput.required = true;
  dateInput.setAttribute('autocomplete', 'bday');
  dateInput.value = profile?.birthDetails?.dateOfBirth || '';
  dateInput.setAttribute('aria-describedby', 'profile-birth-date-error');
  const dateError = element('p', 'profiles-field__error');
  dateError.id = 'profile-birth-date-error';
  dateError.hidden = true;
  dateGroup.append(dateLabel, dateInput, dateError);

  const timeGroup = element('div', 'profiles-field');
  const timeLabel = element('label', 'profiles-field__label', 'Time of birth');
  timeLabel.htmlFor = 'profile-birth-time';
  const timeInput = element('input', 'profiles-field__control');
  timeInput.id = 'profile-birth-time';
  timeInput.name = 'timeOfBirth';
  timeInput.type = 'time';
  timeInput.required = true;
  timeInput.value = profile?.birthDetails?.timeOfBirth || '';
  timeInput.setAttribute('aria-describedby', 'profile-birth-time-help profile-birth-time-error');
  const timeHelp = element(
    'p',
    'profiles-field__help',
    'Use the recorded local time at the birthplace. Even a small difference can change Lagna near a boundary.',
  );
  timeHelp.id = 'profile-birth-time-help';
  const timeError = element('p', 'profiles-field__error');
  timeError.id = 'profile-birth-time-error';
  timeError.hidden = true;
  timeGroup.append(timeLabel, timeInput, timeHelp, timeError);
  dateTimeGrid.append(dateGroup, timeGroup);

  const {
    placeGroup, placeInput, searchButton,
    selectedPlaceText, placeError, placeStatus,
    placeAttribution, placeResults,
  } = buildPlaceFields(initialPlace);
  knownDetails.append(knownLegend, dateTimeGrid, placeGroup);

  return {
    knownDetails, dateInput, dateError,
    timeInput, timeError, placeInput,
    searchButton, selectedPlaceText, placeError,
    placeStatus, placeAttribution, placeResults,
  };
}

function buildCalculationArea(calculated: BirthProfileDerivation | null) {
  const calculationArea = element('section', 'profiles-calculation');
  calculationArea.setAttribute('aria-labelledby', 'profile-calculation-title');
  const calculationTitle = element('h2', 'profiles-calculation__title', 'Calculate astrology details');
  calculationTitle.id = 'profile-calculation-title';
  const calculationCopy = element(
    'p',
    'profiles-calculation__copy',
    'Nothing is saved yet. Calculate first, review the chart, then save the profile.',
  );
  const calculateButton = button(
    calculated ? 'Recalculate details' : 'Calculate details',
    'profiles-button profiles-button--primary profiles-calculation__button',
  );
  calculateButton.dataset.action = 'calculate-birth-profile';
  const calculationStatus = element('p', 'profiles-calculation__status');
  calculationStatus.setAttribute('role', 'status');
  calculationStatus.setAttribute('aria-live', 'polite');
  const calculationError = element('p', 'profiles-form__error');
  calculationError.id = 'profile-calculation-error';
  calculationError.setAttribute('role', 'alert');
  calculationError.hidden = true;
  calculationArea.append(
    calculationTitle,
    calculationCopy,
    calculateButton,
    calculationStatus,
    calculationError,
  );

  return { calculationArea, calculateButton, calculationStatus, calculationError };
}

function buildSaveActions(mode: ProfileFormRequest['mode'], calculated: BirthProfileDerivation | null) {
  const actions = element('div', 'profiles-form__actions');
  const save = element(
    'button',
    'profiles-button profiles-button--primary',
    mode === 'create' ? 'Save calculated profile' : 'Save changes',
  );
  save.type = 'submit';
  save.disabled = !calculated;
  save.setAttribute('aria-describedby', 'profile-save-help');
  const saveHelp = element(
    'p',
    'profiles-field__help profiles-form__save-help',
    calculated
      ? 'Review complete. Saving keeps these details only in this browser.'
      : 'Calculate and review the astrology details before saving.',
  );
  saveHelp.id = 'profile-save-help';
  const cancel = button('Cancel', 'profiles-button profiles-button--secondary');
  actions.append(cancel, save);

  return { actions, save, saveHelp, cancel };
}

function buildPlaceFields(initialPlace: BirthPlaceCandidate | null) {
  const placeGroup = element('div', 'profiles-field profiles-place-field');
  const placeLabel = element('label', 'profiles-field__label', 'Place of birth');
  placeLabel.htmlFor = 'profile-birth-place';
  const placeSearchRow = element('div', 'profiles-place-search');
  const placeInput = element('input', 'profiles-field__control');
  placeInput.id = 'profile-birth-place';
  placeInput.name = 'placeOfBirth';
  placeInput.type = 'search';
  placeInput.maxLength = 120;
  placeInput.autocomplete = 'off';
  placeInput.placeholder = 'City or town, for example Vijayawada';
  placeInput.value = initialPlace?.label || '';
  placeInput.setAttribute(
    'aria-describedby',
    'profile-birth-place-help profile-birth-place-error profile-place-status',
  );
  const searchButton = button('Find place', 'profiles-button profiles-button--secondary');
  searchButton.dataset.action = 'search-birth-place';
  placeSearchRow.append(placeInput, searchButton);
  const placeHelp = element(
    'p',
    'profiles-field__help',
    'Choose a result so we use the correct coordinates and historical timezone. A city or town is enough; do not enter a street address.',
  );
  placeHelp.id = 'profile-birth-place-help';
  const selectedPlaceText = element('p', 'profiles-place-selected');
  selectedPlaceText.id = 'profile-place-selected';
  selectedPlaceText.hidden = !initialPlace;
  const placeError = element('p', 'profiles-field__error');
  placeError.id = 'profile-birth-place-error';
  placeError.hidden = true;
  const placeStatus = element('p', 'profiles-place-status');
  placeStatus.id = 'profile-place-status';
  placeStatus.setAttribute('role', 'status');
  placeStatus.setAttribute('aria-live', 'polite');
  const placeAttribution = element('p', 'profiles-place-attribution');
  placeAttribution.hidden = true;
  const placeResults = element('ul', 'profiles-place-results');
  placeResults.setAttribute('aria-label', 'Matching birthplaces');
  placeGroup.append(
    placeLabel,
    placeSearchRow,
    placeHelp,
    selectedPlaceText,
    placeError,
    placeStatus,
    placeAttribution,
    placeResults,
  );
  return {
    placeGroup, placeInput, searchButton,
    selectedPlaceText, placeError, placeStatus,
    placeAttribution, placeResults,
  };
}

function buildMethodChoices(host: ProfilePanelHost, request: ProfileFormRequest): HTMLElement {
  const { mode, context, profile } = request;
  const { renderManualForm } = host;
  const methods = element('section', 'profiles-methods');
  methods.setAttribute('aria-labelledby', 'profile-method-title');
  const methodsTitle = element('h2', 'profiles-methods__title', 'Choose how to add astrology details');
  methodsTitle.id = 'profile-method-title';
  const methodActions = element('div', 'profiles-methods__actions');
  const useBirthDetails = button('Use birth details', 'profiles-methods__choice profiles-methods__choice--active');
  useBirthDetails.setAttribute('aria-pressed', 'true');
  const useManualDetails = button('Enter astrology details manually', 'profiles-methods__choice');
  useManualDetails.setAttribute('aria-pressed', 'false');
  useManualDetails.addEventListener('click', () => renderManualForm(mode, context, profile));
  methodActions.append(useBirthDetails, useManualDetails);
  methods.append(methodsTitle, methodActions);


  return methods;
}

function buildIntroduction(request: ProfileFormRequest): DocumentFragment {
  const { mode } = request;
  const fragment = document.createDocumentFragment();
  const heading = element(
    'h1',
    'profiles-title',
    mode === 'create' ? 'Create profile from birth details' : 'Edit birth profile',
  );
  heading.id = 'profiles-title';
  heading.tabIndex = -1;
  const intro = element(
    'p',
    'profiles-form__intro',
    'Enter the details people usually know. We will calculate Nakshatra, Padam, Janma Rashi, Lagna, and a D1 Rashi chart for reuse across the site.',
  );
  const privacy = element(
    'p',
    'profiles-privacy',
    'Your name always stays in this browser. Date, time, and the selected place coordinates are sent only when you choose Calculate; they are not used to create an account.',
  );
  fragment.append(heading, intro, privacy);
  return fragment;
}
