import type { GuestProfile } from '../../lib/guest-profile-store';
import { type ResolvedProfilesPanelContext, type ProfilePanelHost } from './contracts';
import { element, button } from './elements';
import { restoreFocus, replacementFocusResolver } from './navigation';
import { displayName } from './form-view';
import { savedNatalDetails } from './natal-view';
import {
  profileFactsSection, savedAstrologySection, journeyReadinessSection,
  natalChartSection, renderReadiness,
} from './detail-sections';

const renderDetailFacts = (
  rows: ReadonlyArray<readonly [string, string]>,
): HTMLDListElement => {
  const facts = element('dl', 'profiles-detail__facts');
  for (const [label, value] of rows) {
    const item = element('div', 'profiles-detail__fact');
    item.append(
      element('dt', 'profiles-detail__fact-label', label),
      element('dd', 'profiles-detail__fact-value', value),
    );
    facts.append(item);
  }
  return facts;
};

export const renderDetail = (
  host: ProfilePanelHost,
  profileId: string,
  context: ResolvedProfilesPanelContext,
  focusHeading = false,
): void => {
  const { root, store, renderList } = host;
  const resolveActiveElement = focusHeading ? undefined : currentFocusResolver();
  const profile = store.get(profileId);
  if (!profile) {
    host.setView({ kind: 'list' });
    renderList();
    restoreFocus(context.resolveFocusTarget?.() || null);
    return;
  }

  const { detail, heading } = buildDetailContent(host, profile, context);

  root.replaceChildren(detail);
  if (focusHeading) {
    heading.focus();
  } else {
    resolveActiveElement?.()?.focus();
  }
};

function buildDetailToolbar(host: ProfilePanelHost, profile: GuestProfile, context: ResolvedProfilesPanelContext): HTMLElement {
  const { birthCalculationActive, controller, renderList } = host;
  const toolbar = element('div', 'profiles-detail__toolbar');
  const back = button('Back to profiles', 'profiles-button profiles-button--quiet');
  back.dataset.action = 'view-profile';
  back.addEventListener('click', () => {
    host.setView({ kind: 'list' });
    renderList();
    const originalTarget = context.focusTarget;
    const focusTarget = originalTarget?.isConnected
      ? originalTarget
      : context.resolveFocusTarget?.() || null;
    restoreFocus(focusTarget);
  });
  const edit = button('Edit profile', 'profiles-button profiles-button--secondary');
  edit.dataset.action = 'edit-profile';
  if (profile.source === 'birth-details' && !birthCalculationActive) {
    edit.disabled = true;
    edit.setAttribute('aria-describedby', 'profile-calculation-disabled-message');
  }
  edit.addEventListener('click', event => controller.openEdit(profile.id, {
    focusTarget: event.currentTarget as HTMLElement,
  }));
  toolbar.append(back, edit);

  return toolbar;
}

function buildDetailContent(host: ProfilePanelHost, profile: GuestProfile, context: ResolvedProfilesPanelContext) {
  const { store, options, birthCalculationActive, renderIssue } = host;
  const detail = element('article', 'profiles-detail');
  detail.dataset.profileId = profile.id;

  const toolbar = buildDetailToolbar(host, profile, context);

  const header = element('header', 'profiles-detail__header');
  const source = element(
    'p',
    'profiles-detail__source',
    profile.source === 'birth-details'
      ? 'Calculated from birth details'
      : 'Entered manually',
  );
  const heading = element('h1', 'profiles-title profiles-detail__title', displayName(profile));
  heading.id = 'profiles-title';
  heading.tabIndex = -1;
  const privacy = element(
    'p',
    'profiles-privacy profiles-detail__privacy',
    'This profile is saved only in this browser. Viewing it does not send or recalculate any details.',
  );
  header.append(source, heading, privacy);
  detail.append(header, toolbar);
  const issue = renderIssue(store.getSnapshot());
  if (issue) detail.append(issue);
  if (profile.source === 'birth-details' && !birthCalculationActive) {
    const calculationNotice = element(
      'p',
      'profiles-notice profiles-notice--warning',
      'Birth-detail calculation is not active in this public build. Your saved calculation remains available to view and use, but recalculation and editing are temporarily disabled.',
    );
    calculationNotice.id = 'profile-calculation-disabled-message';
    detail.append(calculationNotice);
  }

  detail.append(profileFactsSection(profile, renderDetailFacts));

  const natalDetails = savedNatalDetails(profile);
  const astrologySection = savedAstrologySection(natalDetails);
  if (astrologySection) detail.append(astrologySection);
  detail.append(
    journeyReadinessSection(profile, renderReadiness, options),
    natalChartSection(natalDetails),
  );

  return { detail, heading };
}

function currentFocusResolver() {
  const active = document.activeElement;
  return replacementFocusResolver(active instanceof HTMLElement ? active : null);
}
