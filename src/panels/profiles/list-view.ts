import { type ProfilePanelHost } from './contracts';
import { element, button, createConfirmDialog } from './elements';
import { restoreFocus } from './navigation';
import { displayName } from './form-view';
import { renderReadiness } from './detail-sections';
import { MAX_GUEST_PROFILES, type GuestProfile } from '../../lib/guest-profile-store';

const renderProfile = (host: ProfilePanelHost, profile: Readonly<GuestProfile>): HTMLLIElement => {
  const { store, birthCalculationActive, controller, root } = host;
  const item = element('li', 'profiles-roster__item');
  item.dataset.profileId = profile.id;
  const identity = element('div', 'profiles-roster__identity');
  const name = element('h3', 'profiles-roster__name', displayName(profile));
  if (profile.source === 'birth-details') {
    const source = element('span', 'profiles-roster__source', 'Calculated from birth details');
    identity.append(name, source);
  } else {
    identity.append(name);
  }
  const details = element('p', 'profiles-roster__details');
  details.textContent = rosterFacts(profile).join(' · ');
  identity.append(details, renderReadiness(profile));

  const actions = element('div', 'profiles-roster__actions');
  const viewProfile = button('View', 'profiles-button profiles-button--secondary');
  viewProfile.setAttribute('aria-label', `View ${displayName(profile)}`);
  viewProfile.dataset.action = 'view-profile';
  viewProfile.addEventListener('click', event => controller.openView(profile.id, {
    focusTarget: event.currentTarget as HTMLElement,
  }));
  const edit = button('Edit', 'profiles-button profiles-button--secondary');
  edit.setAttribute('aria-label', `Edit ${displayName(profile)}`);
  edit.dataset.action = 'edit-profile';
  if (profile.source === 'birth-details' && !birthCalculationActive) {
    edit.disabled = true;
    edit.setAttribute('aria-describedby', 'profile-calculation-disabled-message');
  }
  edit.addEventListener('click', event => controller.openEdit(profile.id, {
    focusTarget: event.currentTarget as HTMLElement,
  }));
  const remove = button('Delete', 'profiles-button profiles-button--quiet');
  remove.setAttribute('aria-label', `Delete ${displayName(profile)}`);
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
  actions.append(viewProfile, edit, remove);
  item.append(identity, actions);
  return item;
};

export const renderList = (
  host: ProfilePanelHost,): void => {
  const { root, store, birthCalculationActive, renderIssue, controller } = host;
  const snapshot = store.getSnapshot();
  const fragment = document.createDocumentFragment();
  const heading = element('h1', 'profiles-title', 'Profiles');
  heading.id = 'profiles-title';
  heading.tabIndex = -1;
  const privacy = element(
    'p',
    'profiles-privacy',
    birthCalculationActive
      ? 'Profiles are saved only in this browser. Birth details leave the browser only when you ask us to calculate. No account, cloud sync, or recovery.'
      : 'Profiles are saved only in this browser. Remote birth-detail calculation is not active in this public build. No account, cloud sync, or recovery.',
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
      birthCalculationActive
        ? 'Enter the details people usually know—name, date, time, and birthplace. We will calculate the astrology details for reuse in Muhurtam and Daily Horoscope.'
        : 'Save a name and the astrology details you already know for reuse in Muhurtam and Daily Horoscope. Birth-detail calculation will appear here only after the public service is activated.',
    );
    const create = button('Create profile', 'profiles-button profiles-button--primary');
    create.dataset.action = 'create-profile';
    create.addEventListener('click', event => controller.openCreate({
      focusTarget: event.currentTarget as HTMLElement,
    }));
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
  for (const profile of snapshot.profiles) roster.append(renderProfile(host, profile));
  if (!birthCalculationActive && snapshot.profiles.some(profile => profile.source === 'birth-details')) {
    const calculationNotice = element(
      'p',
      'profiles-notice profiles-notice--warning',
      'Birth-detail calculation is not active in this public build. Existing calculated profiles remain viewable and usable, but recalculation and editing are temporarily disabled.',
    );
    calculationNotice.id = 'profile-calculation-disabled-message';
    fragment.append(calculationNotice);
  }
  fragment.append(rosterHeading, roster);

  appendListActions(host, fragment, snapshot.profiles.length);
  root.replaceChildren(fragment);
};

function rosterFacts(profile: Readonly<GuestProfile>): string[] {
  const facts: string[] = [];
  if (profile.nakshatra) {
    facts.push(profile.pada
      ? `${profile.nakshatra}, Padam ${profile.pada}`
      : profile.nakshatra);
  } else {
    facts.push('Birth star not added');
  }
  if (profile.lagna) facts.push(`${profile.lagna} Lagna`);
  if (profile.janmaRasi) facts.push(`${profile.janmaRasi} Janma Rashi`);
  if (profile.birthDetails) facts.push(profile.birthDetails.placeLabel);
  return facts;
}

function appendListActions(host: ProfilePanelHost, fragment: DocumentFragment, profileCount: number): void {
  const { store, root, controller } = host;
  const footer = element('div', 'profiles-actions');
  const atLimit = profileCount >= MAX_GUEST_PROFILES;
  const create = button(
    'Create another profile',
    `profiles-button ${atLimit ? 'profiles-button--secondary' : 'profiles-button--primary'}`,
  );
  create.dataset.action = 'create-profile';
  create.disabled = atLimit;
  if (atLimit) create.setAttribute('aria-describedby', 'profiles-limit-message');
  create.addEventListener('click', event => controller.openCreate({
    focusTarget: event.currentTarget as HTMLElement,
  }));
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
}
