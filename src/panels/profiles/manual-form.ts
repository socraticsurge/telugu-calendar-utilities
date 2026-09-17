import { saveProfile, failedSaveView, saveErrorMessage } from './profile-save';
import { buildManualFormView } from './manual-form-view';
import { type ResolvedProfilesPanelContext, type ProfilePanelHost } from './contracts';
import { updateProfileDuplicateWarning, validateProfileName } from './form-view';
import {
  GUEST_PROFILE_SCHEMA_VERSION, guestProfileReadiness, type GuestProfile,
  type GuestProfileDraft,
} from '../../lib/guest-profile-store';

export function manualPada(value: string): GuestProfile['pada'] {
  const parsed = Number(value);
  if (parsed === 1 || parsed === 2 || parsed === 3 || parsed === 4) return parsed;
  return null;
}

export function manualProfileCandidate(
  profile: GuestProfile | undefined,
  fields: { name: string; nakshatra: string; pada: string; lagna: string },
): GuestProfile {
  const { name, nakshatra, pada, lagna } = fields;
  return {
    id: profile?.id || 'profile-preview',
    schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
    source: 'manual',
    name,
    nakshatra: nakshatra || null,
    pada: manualPada(pada),
    lagna: lagna || null,
    janmaRasi: null,
    birthDetails: null,
    natalChart: null,
    calculation: null,
  };
}

export function validateManualJourney(
  context: ResolvedProfilesPanelContext,
  candidate: GuestProfile,
  fields: {
    nakshatraSelect: HTMLSelectElement; nakshatraError: HTMLElement;
    padaSelect: HTMLSelectElement; padaError: HTMLElement;
  },
): boolean {
  const { nakshatraSelect, nakshatraError, padaSelect, padaError } = fields;
  const readiness = guestProfileReadiness(candidate);
  if (context.requiredFor && !readiness.muhurta) {
    nakshatraSelect.setAttribute('aria-invalid', 'true');
    nakshatraError.textContent = context.requiredFor === 'horoscope'
      ? 'Add a Nakshatra to use this profile in Daily Horoscope.'
      : 'Add a Nakshatra to use this profile in Muhurtam.';
    nakshatraError.hidden = false;
    nakshatraSelect.focus();
    return false;
  }
  if (context.requiredFor !== 'horoscope' || readiness.missingForHoroscope !== 'pada') {
    return true;
  }
  padaSelect.setAttribute('aria-invalid', 'true');
  padaError.textContent = `Select a Padam because ${nakshatraSelect.value} spans two Rashis.`;
  padaError.hidden = false;
  padaSelect.focus();
  return false;
}

export const renderManualForm = (
  host: ProfilePanelHost,
  mode: 'create' | 'edit',
  context: ResolvedProfilesPanelContext,
  profile?: GuestProfile,
): void => {
  const { store, renderList, returnToOrigin } = host;
  host.setFormMethod('manual');
  const {
    form, nameInput, nameError,
    duplicate, nakshatraSelect, nakshatraError,
    padaSelect, padaError, lagnaSelect,
    formError, cancel,
  } = buildManualFormView(host, { mode, context, profile });

  const updateDuplicateWarning = updateProfileDuplicateWarning.bind(
    null, duplicate, nameInput, store, profile?.id,
  );
  nameInput.addEventListener('input', () => {
    if (nameInput.value.trim()) {
      nameInput.removeAttribute('aria-invalid');
      nameError.hidden = true;
      nameError.textContent = '';
    }
    updateDuplicateWarning();
  });
  nakshatraSelect.addEventListener('change', () => {
    if (nakshatraSelect.value) {
      nakshatraSelect.removeAttribute('aria-invalid');
      nakshatraError.hidden = true;
      nakshatraError.textContent = '';
    }
    padaSelect.disabled = !nakshatraSelect.value;
    if (padaSelect.disabled) padaSelect.value = '';
    padaSelect.removeAttribute('aria-invalid');
    padaError.hidden = true;
    padaError.textContent = '';
  });
  padaSelect.addEventListener('change', () => {
    if (!padaSelect.value) return;
    padaSelect.removeAttribute('aria-invalid');
    padaError.hidden = true;
    padaError.textContent = '';
  });
  updateDuplicateWarning();

  cancel.addEventListener('click', () => {
    host.setView({ kind: 'list' });
    renderList();
    returnToOrigin(context);
  });

  form.addEventListener('submit', event => {
    event.preventDefault();
    const name = nameInput.value.trim();
    if (!validateProfileName(name, nameInput, nameError)) return;

    formError.hidden = true;
    formError.textContent = '';
    const draft: GuestProfileDraft = {
      source: 'manual',
      name,
      nakshatra: nakshatraSelect.value,
      pada: padaSelect.value,
      lagna: lagnaSelect.value,
      birthDetails: null,
      natalChart: null,
      calculation: null,
    };
    const candidate = manualProfileCandidate(
      profile,
      { name, nakshatra: nakshatraSelect.value, pada: padaSelect.value, lagna: lagnaSelect.value },
    );
    if (!validateManualJourney(
      context,
      candidate,
      { nakshatraSelect, nakshatraError, padaSelect, padaError },
    )) return;
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
  nameInput.focus();
};
