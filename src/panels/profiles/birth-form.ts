import { saveProfile, failedSaveView, saveErrorMessage } from './profile-save';
import { buildBirthFormView } from './birth-form-view';
import { type ResolvedProfilesPanelContext, type ProfilePanelHost } from './contracts';
import { element, button } from './elements';
import { updateProfileDuplicateWarning, validateProfileName } from './form-view';
import {
  isoDateInTimeZone, validateRequiredBirthInputs, validatedBirthInstant,
  birthApiMessage, birthDraft,
} from './birth-validation';
import { renderNatalReview } from './natal-view';
import {
  deriveBirthProfile, searchBirthPlaces, type BirthPlaceAttribution,
  type BirthPlaceCandidate, type BirthProfileDerivation,
} from '../../lib/birth-profile-api';
import { type GuestProfile } from '../../lib/guest-profile-store';

export const renderBirthForm = (
  host: ProfilePanelHost,
  mode: 'create' | 'edit',
  context: ResolvedProfilesPanelContext,
  profile?: GuestProfile,
): void => {
  const { store, options, birthCalculationActive, renderManualForm, renderList, returnToOrigin } = host;
  const deriveProfile = options.deriveProfile || deriveBirthProfile;
  if (!birthCalculationActive) {
    renderManualForm(mode, context, profile);
    return;
  }
  host.setFormMethod('birth-details');
  const initialPlace: BirthPlaceCandidate | null = profile?.birthDetails
    ? {
      id: `saved:${profile.id}`,
      label: profile.birthDetails.placeLabel,
      latitude: profile.birthDetails.latitude,
      longitude: profile.birthDetails.longitude,
      timezone: profile.birthDetails.timezone,
    }
    : null;
  const initialResult: BirthProfileDerivation | null = profile?.source === 'birth-details'
    && profile.nakshatra && profile.pada && profile.janmaRasi && profile.lagna
    && profile.natalChart && profile.calculation
    ? {
      contractVersion: '1.0',
      engine: { ...profile.calculation.engine },
      nakshatra: profile.nakshatra,
      pada: profile.pada,
      janmaRashi: profile.janmaRasi,
      lagna: profile.lagna,
      lagnaDegree: profile.natalChart.lagnaDegree,
      planets: profile.natalChart.planets.map(planet => ({ ...planet })),
    }
    : null;
  let selectedPlace = initialPlace;
  let calculated = initialResult;
  let placeSearchSequence = 0;
  let calculationSequence = 0;

  const {
    form, nameInput, nameError,
    duplicate, dateInput, dateError,
    timeInput, timeError, placeInput,
    searchButton, selectedPlaceText, placeError,
    placeStatus, placeAttribution, placeResults,
    calculateButton, calculationStatus, calculationError,
    reviewHost, formError, save,
    saveHelp, cancel,
  } = buildBirthFormView(host, { mode, context, profile }, { place: initialPlace, calculated });

  const updateSelectedPlace = (): void => {
    selectedPlaceText.hidden = !selectedPlace;
    selectedPlaceText.textContent = selectedPlace
      ? `Selected: ${selectedPlace.label} · ${selectedPlace.timezone}`
      : '';
    const maxDate = selectedPlace
      ? isoDateInTimeZone(new Date(), selectedPlace.timezone)
      : null;
    if (maxDate) dateInput.max = maxDate;
    else dateInput.removeAttribute('max');
  };
  const updateReview = (): void => {
    reviewHost.replaceChildren();
    if (calculated) reviewHost.append(renderNatalReview(calculated));
    save.disabled = !calculated;
    saveHelp.textContent = calculated
      ? 'Review complete. Saving keeps these details only in this browser.'
      : 'Calculate and review the astrology details before saving.';
    calculateButton.textContent = calculated ? 'Recalculate details' : 'Calculate details';
    calculateButton.classList.toggle('profiles-button--primary', !calculated);
    calculateButton.classList.toggle('profiles-button--secondary', Boolean(calculated));
  };
  const invalidateCalculation = (): void => {
    calculationSequence += 1;
    calculated = null;
    calculateButton.disabled = false;
    calculateButton.removeAttribute('aria-busy');
    calculationStatus.textContent = '';
    calculationError.hidden = true;
    calculationError.textContent = '';
    updateReview();
  };
  const clearFieldError = (input: HTMLElement, error: HTMLElement): void => {
    input.removeAttribute('aria-invalid');
    error.hidden = true;
    error.textContent = '';
  };
  const updateDuplicateWarning = updateProfileDuplicateWarning.bind(
    null, duplicate, nameInput, store, profile?.id,
  );
  const showPlaceResults = (
    results: BirthPlaceCandidate[],
    attribution: string,
    attributions: BirthPlaceAttribution[],
  ): void => {
    placeResults.replaceChildren();
    placeAttribution.replaceChildren();
    placeAttribution.hidden = results.length === 0;
    if (results.length === 0) {
      placeStatus.textContent = 'No matching places found. Try a nearby city or add a state or country.';
      return;
    }
    placeStatus.textContent = `${results.length} ${results.length === 1 ? 'place' : 'places'} found.`;
    placeAttribution.append(document.createTextNode(`${attribution}: `));
    attributions.forEach((entry, index) => {
      if (index > 0) placeAttribution.append(document.createTextNode(' · '));
      const link = document.createElement('a');
      link.href = entry.url;
      link.textContent = entry.label;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      placeAttribution.append(link);
    });
    for (const candidate of results) {
      const item = element('li', 'profiles-place-results__item');
      const selectPlace = button(candidate.label, 'profiles-place-results__choice');
      selectPlace.append(element('span', 'profiles-place-results__timezone', candidate.timezone));
      selectPlace.addEventListener('click', () => {
        selectedPlace = candidate;
        placeInput.value = candidate.label;
        clearFieldError(placeInput, placeError);
        placeResults.replaceChildren();
        placeStatus.textContent = 'Birthplace selected.';
        invalidateCalculation();
        clearFieldError(dateInput, dateError);
        clearFieldError(timeInput, timeError);
        updateSelectedPlace();
        calculateButton.focus();
      });
      item.append(selectPlace);
      placeResults.append(item);
    }
  };

  const runPlaceSearch = async (): Promise<void> => {
    const query = placeInput.value.trim();
    if (query.length < 2) {
      placeInput.setAttribute('aria-invalid', 'true');
      placeError.textContent = 'Enter at least two characters to find a city or town.';
      placeError.hidden = false;
      placeInput.focus();
      return;
    }
    const sequence = ++placeSearchSequence;
    searchButton.disabled = true;
    placeInput.setAttribute('aria-busy', 'true');
    clearFieldError(placeInput, placeError);
    placeStatus.textContent = 'Searching for places…';
    placeAttribution.hidden = true;
    placeAttribution.replaceChildren();
    placeResults.replaceChildren();
    try {
      const response = await (options.searchPlaces || searchBirthPlaces)(query);
      if (sequence !== placeSearchSequence) return;
      showPlaceResults(
        response.results,
        response.attribution,
        response.attributions,
      );
    } catch (error) {
      if (sequence !== placeSearchSequence) return;
      placeError.textContent = birthApiMessage(error);
      placeError.hidden = false;
      placeStatus.textContent = '';
    } finally {
      if (sequence === placeSearchSequence) {
        searchButton.disabled = false;
        placeInput.removeAttribute('aria-busy');
      }
    }
  };

  nameInput.addEventListener('input', () => {
    if (nameInput.value.trim()) clearFieldError(nameInput, nameError);
    updateDuplicateWarning();
  });
  dateInput.addEventListener('input', () => {
    clearFieldError(dateInput, dateError);
    invalidateCalculation();
  });
  timeInput.addEventListener('input', () => {
    clearFieldError(timeInput, timeError);
    invalidateCalculation();
  });
  placeInput.addEventListener('input', () => {
    clearFieldError(placeInput, placeError);
    placeStatus.textContent = '';
    placeResults.replaceChildren();
    placeSearchSequence += 1;
    if (placeInput.value.trim() !== selectedPlace?.label) {
      selectedPlace = null;
      updateSelectedPlace();
      invalidateCalculation();
    }
  });
  placeInput.addEventListener('keydown', event => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    void runPlaceSearch();
  });
  searchButton.addEventListener('click', () => { void runPlaceSearch(); });

  calculateButton.addEventListener('click', async () => {
    const calculationPlace = validateRequiredBirthInputs(
      { dateInput, dateError, timeInput, timeError, placeInput, placeError },
      selectedPlace,
    );
    if (!calculationPlace) return;
    const now = new Date();
    const birthInstant = validatedBirthInstant(
      { dateInput, dateError, timeInput, timeError, placeInput, placeError },
      calculationPlace,
      now,
    );
    if (!birthInstant) return;

    const sequence = ++calculationSequence;
    calculateButton.disabled = true;
    calculateButton.setAttribute('aria-busy', 'true');
    calculationError.hidden = true;
    calculationError.textContent = '';
    calculationStatus.textContent = 'Calculating the birth chart…';
    try {
      const nextResult = await deriveProfile({
        dateOfBirth: dateInput.value,
        timeOfBirth: timeInput.value,
        latitude: calculationPlace.latitude,
        longitude: calculationPlace.longitude,
        timezone: calculationPlace.timezone,
      });
      if (sequence !== calculationSequence) return;
      calculated = nextResult;
      calculationStatus.textContent = 'Calculation complete. Review the results below.';
      updateReview();
      reviewHost.querySelector<HTMLElement>('#profile-review-title')?.focus();
    } catch (error) {
      if (sequence !== calculationSequence) return;
      calculated = null;
      calculationError.textContent = birthApiMessage(error);
      calculationError.hidden = false;
      calculationStatus.textContent = '';
      updateReview();
    } finally {
      if (sequence === calculationSequence) {
        calculateButton.disabled = false;
        calculateButton.removeAttribute('aria-busy');
      }
    }
  });

  cancel.addEventListener('click', () => {
    placeSearchSequence += 1;
    calculationSequence += 1;
    host.setView({ kind: 'list' });
    renderList();
    returnToOrigin(context);
  });

  form.addEventListener('submit', event => {
    event.preventDefault();
    const name = nameInput.value.trim();
    if (!validateProfileName(name, nameInput, nameError)) return;
    if (!selectedPlace || !calculated) {
      calculationError.textContent = 'Calculate and review the astrology details before saving.';
      calculationError.hidden = false;
      calculateButton.focus();
      return;
    }

    formError.hidden = true;
    formError.textContent = '';
    const draft = birthDraft(
      { name, dateOfBirth: dateInput.value, timeOfBirth: timeInput.value },
      selectedPlace,
      calculated,
    );
    host.setView({ kind: 'list' });
    try {
      const savedProfile = saveProfile(store, mode, profile, draft);
      renderList();
      returnToOrigin(context, savedProfile);
    } catch (error) {
      host.setView(failedSaveView(mode, profile, context));
      formError.hidden = false;
      formError.textContent = saveErrorMessage(error);
    }
  });

  updateSelectedPlace();
  updateDuplicateWarning();
  updateReview();
  nameInput.focus();
};
