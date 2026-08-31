import { NAKSHATRA_NAMES, RASI_NAMES } from '../data/rasis';
import {
  GUEST_PROFILE_SCHEMA_VERSION,
  MAX_GUEST_PROFILES,
  GuestProfileStore,
  GuestProfileStoreError,
  guestProfileReadiness,
  type GuestProfile,
  type GuestProfileSnapshot,
} from '../lib/guest-profile-store';

export interface ProfilesPanelContext {
  returnTo?: string;
  onSaved?: (profile: GuestProfile) => void;
  focusTarget?: HTMLElement | null;
  requiredFor?: 'horoscope' | 'muhurta';
}

export interface ProfilesPanelOptions {
  navigate: (tool: string) => void;
  root?: HTMLElement;
}

export interface ProfilesPanelController {
  openCreate(context?: ProfilesPanelContext): void;
  openEdit(profileId: string, context?: ProfilesPanelContext): void;
  render(): void;
  destroy(): void;
}

type PanelView =
  | { kind: 'list' }
  | { kind: 'create'; context: ProfilesPanelContext }
  | { kind: 'edit'; profileId: string; context: ProfilesPanelContext };

function element<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function button(text: string, className: string): HTMLButtonElement {
  const node = element('button', className, text);
  node.type = 'button';
  return node;
}

function appendOption(
  select: HTMLSelectElement,
  value: string,
  label: string,
): void {
  const option = element('option');
  option.value = value;
  option.textContent = label;
  select.append(option);
}

function issueMessage(snapshot: GuestProfileSnapshot): string | null {
  if (snapshot.issue === 'malformed-storage') {
    return 'Saved profile data was damaged and has been reset. You can create profiles again.';
  }
  if (snapshot.issue === 'unsupported-storage-version') {
    return 'These profiles use a newer format. Changes on this page last only for this session; your saved browser data was not overwritten.';
  }
  if (snapshot.persistence === 'memory' || snapshot.issue === 'storage-unavailable') {
    return 'Browser storage is unavailable. Profiles created now last only for this session.';
  }
  return null;
}

function displayName(profile: GuestProfile): string {
  return profile.name || 'Unnamed profile';
}

function normalizedName(value: string): string {
  return value.trim().toLocaleLowerCase();
}

function restoreFocus(node: HTMLElement | null): void {
  if (node && node.isConnected) {
    node.focus();
    if (document.activeElement === node) return;
  }
  const heading = document.querySelector<HTMLElement>('#profiles-title');
  heading?.focus();
}

function showNativeDialog(dialog: HTMLDialogElement): void {
  if (typeof dialog.showModal === 'function') {
    dialog.showModal();
  } else {
    // jsdom and older embedded browsers do not expose the method, but retaining
    // the native element and open state preserves semantics and testability.
    dialog.setAttribute('open', '');
  }
}

function closeNativeDialog(dialog: HTMLDialogElement): void {
  if (typeof dialog.close === 'function') {
    dialog.close();
  } else {
    dialog.removeAttribute('open');
  }
  dialog.remove();
}

function createConfirmDialog(config: {
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => void;
  trigger: HTMLElement;
}): HTMLDialogElement {
  const dialog = element('dialog', 'profiles-dialog');
  const id = `profiles-dialog-${Math.random().toString(36).slice(2)}`;
  const title = element('h2', 'profiles-dialog__title', config.title);
  title.id = `${id}-title`;
  const description = element('p', 'profiles-dialog__description', config.description);
  description.id = `${id}-description`;
  dialog.setAttribute('aria-labelledby', title.id);
  dialog.setAttribute('aria-describedby', description.id);

  const actions = element('div', 'profiles-dialog__actions');
  const cancel = button('Cancel', 'profiles-button profiles-button--secondary');
  const confirm = button(config.confirmLabel, 'profiles-button profiles-button--danger');
  actions.append(cancel, confirm);
  dialog.append(title, description, actions);

  const cancelAndRestore = (): void => {
    closeNativeDialog(dialog);
    restoreFocus(config.trigger);
  };
  cancel.addEventListener('click', cancelAndRestore);
  dialog.addEventListener('cancel', event => {
    event.preventDefault();
    cancelAndRestore();
  });
  confirm.addEventListener('click', () => {
    closeNativeDialog(dialog);
    config.onConfirm();
  });
  document.body.append(dialog);
  showNativeDialog(dialog);
  cancel.focus();
  return dialog;
}

export function initProfilesPanel(
  store: GuestProfileStore,
  options: ProfilesPanelOptions,
): ProfilesPanelController {
  const root = options.root || document.querySelector<HTMLElement>('#profiles-root');
  if (!root) throw new Error('Profiles panel root #profiles-root was not found');

  let view: PanelView = { kind: 'list' };

  const returnToOrigin = (
    context: ProfilesPanelContext,
    savedProfile?: GuestProfile,
  ): void => {
    if (context.returnTo) options.navigate(context.returnTo);
    // Select and focus only after the origin is visible again. Hidden controls
    // cannot reliably receive focus in real browsers.
    if (savedProfile) context.onSaved?.(savedProfile);
    const focusTarget = context.focusTarget;
    if (focusTarget && focusTarget.isConnected) focusTarget.focus();
  };

  const renderIssue = (snapshot: GuestProfileSnapshot): HTMLElement | null => {
    const message = issueMessage(snapshot);
    if (!message) return null;
    const notice = element('div', 'profiles-notice profiles-notice--warning', message);
    notice.setAttribute('role', 'alert');
    notice.dataset.profileIssue = snapshot.issue || snapshot.persistence;
    return notice;
  };

  const renderReadiness = (profile: GuestProfile): HTMLDListElement => {
    const readiness = guestProfileReadiness(profile);
    const list = element('dl', 'profiles-readiness');

    const muhurtaTerm = element('dt', 'profiles-readiness__term', 'Muhurtam');
    const muhurtaValue = element(
      'dd',
      `profiles-readiness__value ${readiness.muhurta ? 'profiles-readiness__value--ready' : 'profiles-readiness__value--needs-details'}`,
      readiness.muhurta ? 'Ready' : 'Needs Nakshatra',
    );
    const horoscopeTerm = element('dt', 'profiles-readiness__term', 'Daily Horoscope');
    let horoscopeText = 'Ready';
    if (readiness.missingForHoroscope === 'nakshatra') horoscopeText = 'Needs Nakshatra';
    if (readiness.missingForHoroscope === 'pada') horoscopeText = 'Needs Padam';
    if (readiness.horoscope && readiness.janmaRasi) {
      horoscopeText = `Ready · ${readiness.janmaRasi} Janma Rashi`;
    }
    const horoscopeValue = element(
      'dd',
      `profiles-readiness__value ${readiness.horoscope ? 'profiles-readiness__value--ready' : 'profiles-readiness__value--needs-details'}`,
      horoscopeText,
    );
    list.append(muhurtaTerm, muhurtaValue, horoscopeTerm, horoscopeValue);
    return list;
  };

  const contextualReadinessText = (
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

  const renderProfile = (profile: Readonly<GuestProfile>): HTMLLIElement => {
    const item = element('li', 'profiles-roster__item');
    item.dataset.profileId = profile.id;
    const identity = element('div', 'profiles-roster__identity');
    const name = element('h3', 'profiles-roster__name', displayName(profile));
    const details = element('p', 'profiles-roster__details');
    const facts: string[] = [];
    if (profile.nakshatra) {
      facts.push(profile.pada
        ? `${profile.nakshatra}, Padam ${profile.pada}`
        : profile.nakshatra);
    } else {
      facts.push('Birth star not added');
    }
    if (profile.lagna) facts.push(`${profile.lagna} Lagna`);
    details.textContent = facts.join(' · ');
    identity.append(name, details, renderReadiness(profile));

    const actions = element('div', 'profiles-roster__actions');
    const edit = button(`Edit ${displayName(profile)}`, 'profiles-button profiles-button--secondary');
    edit.dataset.action = 'edit-profile';
    edit.addEventListener('click', () => controller.openEdit(profile.id));
    const remove = button(`Delete ${displayName(profile)}`, 'profiles-button profiles-button--quiet');
    remove.dataset.action = 'delete-profile';
    remove.addEventListener('click', () => {
      createConfirmDialog({
        title: `Delete ${displayName(profile)}?`,
        description: 'This removes the profile from this browser. This action cannot be undone.',
        confirmLabel: 'Delete profile',
        trigger: remove,
        onConfirm: () => {
          store.remove(profile.id);
          restoreFocus(root);
        },
      });
    });
    actions.append(edit, remove);
    item.append(identity, actions);
    return item;
  };

  const renderList = (): void => {
    const snapshot = store.getSnapshot();
    const fragment = document.createDocumentFragment();
    const heading = element('h1', 'profiles-title', 'Profiles');
    heading.id = 'profiles-title';
    heading.tabIndex = -1;
    const privacy = element(
      'p',
      'profiles-privacy',
      'Saved only in this browser. No account, cloud sync, or recovery. Clearing site data removes profiles.',
    );
    fragment.append(heading, privacy);
    const issue = renderIssue(snapshot);
    if (issue) fragment.append(issue);

    if (snapshot.profiles.length === 0) {
      const empty = element('section', 'profiles-empty');
      empty.setAttribute('aria-labelledby', 'profiles-empty-title');
      const emptyTitle = element('h2', 'profiles-empty__title', 'Save a person once');
      emptyTitle.id = 'profiles-empty-title';
      const emptyBody = element(
        'p',
        'profiles-empty__body',
        'Add a name and birth star to reuse them in Muhurtam and Daily Horoscope. You can complete missing details later.',
      );
      const create = button('Create profile', 'profiles-button profiles-button--primary');
      create.dataset.action = 'create-profile';
      create.addEventListener('click', () => controller.openCreate());
      empty.append(emptyTitle, emptyBody, create);
      fragment.append(empty);
      root.replaceChildren(fragment);
      return;
    }

    const rosterHeading = element(
      'h2',
      'profiles-roster__title',
      `${snapshot.profiles.length} of ${MAX_GUEST_PROFILES} profiles saved`,
    );
    rosterHeading.id = 'profiles-roster-title';
    const roster = element('ul', 'profiles-roster');
    roster.setAttribute('aria-labelledby', rosterHeading.id);
    for (const profile of snapshot.profiles) roster.append(renderProfile(profile));
    fragment.append(rosterHeading, roster);

    const footer = element('div', 'profiles-actions');
    const atLimit = snapshot.profiles.length >= MAX_GUEST_PROFILES;
    const create = button('Create another profile', 'profiles-button profiles-button--primary');
    create.dataset.action = 'create-profile';
    create.disabled = atLimit;
    if (atLimit) create.setAttribute('aria-describedby', 'profiles-limit-message');
    create.addEventListener('click', () => controller.openCreate());
    const clear = button('Clear all profiles', 'profiles-button profiles-button--quiet');
    clear.dataset.action = 'clear-profiles';
    clear.addEventListener('click', () => {
      createConfirmDialog({
        title: 'Clear all profiles?',
        description: 'This removes every saved profile from this browser. This action cannot be undone.',
        confirmLabel: 'Clear all profiles',
        trigger: clear,
        onConfirm: () => {
          store.clear();
          restoreFocus(root);
        },
      });
    });
    footer.append(create, clear);
    fragment.append(footer);
    if (atLimit) {
      const limit = element(
        'p',
        'profiles-limit',
        `You can save up to ${MAX_GUEST_PROFILES} profiles. Edit or delete one to add another.`,
      );
      limit.id = 'profiles-limit-message';
      fragment.append(limit);
    }
    root.replaceChildren(fragment);
  };

  const renderForm = (
    mode: 'create' | 'edit',
    context: ProfilesPanelContext,
    profile?: GuestProfile,
  ): void => {
    const fragment = document.createDocumentFragment();
    const heading = element('h1', 'profiles-title', mode === 'create' ? 'Create profile' : 'Edit profile');
    heading.id = 'profiles-title';
    heading.tabIndex = -1;
    let introText = 'Start with a name. Nakshatra makes the profile ready for Muhurtam; Padam may be needed to derive Janma Rashi for Daily Horoscope.';
    if (context.requiredFor === 'horoscope') {
      introText = 'Add the birth details needed for Daily Horoscope. Nakshatra is required; Padam is required only when the birth star spans two Rashis. Lagna remains optional.';
    }
    if (context.requiredFor === 'muhurta') {
      introText = 'Add a name and Nakshatra to use this profile in Muhurtam. Padam and Lagna are optional for this journey.';
    }
    const intro = element(
      'p',
      'profiles-form__intro',
      introText,
    );
    const privacy = element(
      'p',
      'profiles-privacy',
      'Saved only in this browser. No account, cloud sync, or recovery.',
    );
    fragment.append(heading, intro, privacy);
    const snapshot = store.getSnapshot();
    const issue = renderIssue(snapshot);
    if (issue) fragment.append(issue);

    if (mode === 'create' && (context.returnTo || context.requiredFor) && snapshot.profiles.length > 0) {
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
      for (const existingProfile of snapshot.profiles) {
        const item = element('li', 'profiles-form__existing-item');
        const name = element('span', 'profiles-form__existing-name', displayName(existingProfile));
        const readiness = element(
          'span',
          'profiles-form__existing-readiness',
          contextualReadinessText(existingProfile, context.requiredFor),
        );
        item.append(name, readiness);
        existingList.append(item);
      }
      existing.append(existingTitle, existingHint, existingList);
      fragment.append(existing);
    }

    const form = element('form', 'profiles-form');
    form.noValidate = true;

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
      context.requiredFor === 'horoscope'
        ? 'Required to derive Janma Rashi for Daily Horoscope.'
        : context.requiredFor === 'muhurta'
          ? 'Required for Muhurtam.'
          : 'Required for Muhurtam and for deriving Janma Rashi.',
    );
    nakshatraHelp.id = 'profile-nakshatra-help';
    const nakshatraError = element('p', 'profiles-field__error');
    nakshatraError.id = 'profile-nakshatra-error';
    nakshatraError.hidden = true;
    nakshatraGroup.append(nakshatraLabel, nakshatraSelect, nakshatraHelp, nakshatraError);

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

    const formError = element('p', 'profiles-form__error');
    formError.id = 'profile-form-error';
    formError.setAttribute('role', 'alert');
    formError.hidden = true;

    const actions = element('div', 'profiles-form__actions');
    const save = element('button', 'profiles-button profiles-button--primary', mode === 'create' ? 'Save profile' : 'Save changes');
    save.type = 'submit';
    const cancel = button('Cancel', 'profiles-button profiles-button--secondary');
    actions.append(save, cancel);
    form.append(nameGroup, nakshatraGroup, padaGroup, lagnaGroup, formError, actions);
    fragment.append(form);
    root.replaceChildren(fragment);

    const updateDuplicateWarning = (): void => {
      const candidate = normalizedName(nameInput.value);
      const duplicateProfile = candidate
        ? store.getSnapshot().profiles.find(existing =>
          existing.id !== profile?.id && normalizedName(existing.name) === candidate)
        : undefined;
      duplicate.hidden = !duplicateProfile;
      duplicate.textContent = duplicateProfile
        ? `A profile named ${displayName(duplicateProfile)} already exists. You can still save this profile.`
        : '';
    };
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
      view = { kind: 'list' };
      renderList();
      returnToOrigin(context);
    });

    form.addEventListener('submit', event => {
      event.preventDefault();
      const name = nameInput.value.trim();
      if (!name) {
        nameInput.setAttribute('aria-invalid', 'true');
        nameError.textContent = 'Enter a name for this profile.';
        nameError.hidden = false;
        nameInput.focus();
        return;
      }

      formError.hidden = true;
      formError.textContent = '';
      const draft = {
        name,
        nakshatra: nakshatraSelect.value,
        pada: padaSelect.value,
        lagna: lagnaSelect.value,
      };
      const padaValue = Number(padaSelect.value);
      const candidate: GuestProfile = {
        id: profile?.id || 'profile-preview',
        schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
        name,
        nakshatra: nakshatraSelect.value || null,
        pada: padaValue === 1 || padaValue === 2 || padaValue === 3 || padaValue === 4
          ? padaValue
          : null,
        lagna: lagnaSelect.value || null,
      };
      const readiness = guestProfileReadiness(candidate);
      if (context.requiredFor && !readiness.muhurta) {
        nakshatraSelect.setAttribute('aria-invalid', 'true');
        nakshatraError.textContent = context.requiredFor === 'horoscope'
          ? 'Add a Nakshatra to use this profile in Daily Horoscope.'
          : 'Add a Nakshatra to use this profile in Muhurtam.';
        nakshatraError.hidden = false;
        nakshatraSelect.focus();
        return;
      }
      if (context.requiredFor === 'horoscope' && readiness.missingForHoroscope === 'pada') {
        padaSelect.setAttribute('aria-invalid', 'true');
        padaError.textContent = `Select a Padam because ${nakshatraSelect.value} spans two Rashis.`;
        padaError.hidden = false;
        padaSelect.focus();
        return;
      }
      view = { kind: 'list' };
      try {
        let savedProfile: GuestProfile;
        if (mode === 'edit' && profile) {
          savedProfile = store.update(profile.id, draft);
        } else {
          savedProfile = store.create(draft);
        }
        renderList();
        returnToOrigin(context, savedProfile);
      } catch (error) {
        view = mode === 'edit' && profile
          ? { kind: 'edit', profileId: profile.id, context }
          : { kind: 'create', context };
        formError.hidden = false;
        if (error instanceof GuestProfileStoreError && error.code === 'profile-limit') {
          formError.textContent = `You can save up to ${MAX_GUEST_PROFILES} profiles. Delete one before adding another.`;
        } else if (error instanceof GuestProfileStoreError && error.code === 'profile-not-found') {
          formError.textContent = 'This profile is no longer available. Return to Profiles and try again.';
        } else {
          formError.textContent = 'The profile could not be saved. Check the details and try again.';
        }
      }
    });
    nameInput.focus();
  };

  const controller: ProfilesPanelController = {
    openCreate(context = {}) {
      if (store.getSnapshot().profiles.length >= MAX_GUEST_PROFILES) {
        view = { kind: 'list' };
        renderList();
        return;
      }
      view = { kind: 'create', context };
      renderForm('create', context);
    },
    openEdit(profileId, context = {}) {
      const profile = store.get(profileId);
      if (!profile) {
        view = { kind: 'list' };
        renderList();
        return;
      }
      view = { kind: 'edit', profileId, context };
      renderForm('edit', context, profile);
    },
    render() {
      if (view.kind === 'create') {
        renderForm('create', view.context);
        return;
      }
      if (view.kind === 'edit') {
        const profile = store.get(view.profileId);
        if (profile) {
          renderForm('edit', view.context, profile);
          return;
        }
        view = { kind: 'list' };
      }
      renderList();
    },
    destroy() {
      unsubscribe();
      root.replaceChildren();
    },
  };

  const unsubscribe = store.subscribe(() => controller.render());
  controller.render();
  return controller;
}
