import { NAKSHATRA_NAMES, RASI_NAMES } from '../data/rasis';
import {
  BirthProfileApiError,
  deriveBirthProfile,
  searchBirthPlaces,
  type BirthPlaceCandidate,
  type BirthProfileDerivation,
} from '../lib/birth-profile-api';
import {
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_SCHEMA_VERSION,
  GUEST_PROFILE_STORAGE_KEY,
  MAX_GUEST_PROFILES,
  GuestProfileStore,
  GuestProfileStoreError,
  guestProfileReadiness,
  type GuestProfile,
  type GuestProfileDraft,
  type GuestProfileSnapshot,
} from '../lib/guest-profile-store';
import { birthProfileCalculationEnabled } from '../lib/remote-calculation-activation';

export interface ProfilesPanelContext {
  returnTo?: string;
  onSaved?: (profile: GuestProfile) => void;
  focusTarget?: HTMLElement | null;
  requiredFor?: 'horoscope' | 'muhurta';
}

interface ResolvedProfilesPanelContext extends ProfilesPanelContext {
  resolveFocusTarget?: () => HTMLElement | null;
}

export interface ProfilesPanelOptions {
  navigate: (tool: string) => void;
  onViewDailyHoroscope?: (profileId: string) => void;
  onFindMuhurtam?: (profileId: string) => void;
  root?: HTMLElement;
  searchPlaces?: typeof searchBirthPlaces;
  deriveProfile?: typeof deriveBirthProfile;
  birthCalculationEnabled?: boolean;
}

export interface ProfilesPanelController {
  openCreate(context?: ProfilesPanelContext): void;
  openView(profileId: string, context?: ProfilesPanelContext): void;
  openEdit(profileId: string, context?: ProfilesPanelContext): void;
  render(): void;
  destroy(): void;
}

/**
 * Refresh guest profiles changed by another tab. Other browser preferences do
 * not cause profile work; a null key represents localStorage.clear().
 */
export function listenForGuestProfileStorageChanges(
  store: Pick<GuestProfileStore, 'reload'>,
  target: Window = window,
): () => void {
  const onStorage = (event: StorageEvent): void => {
    if (
      event.key !== null
      && event.key !== GUEST_PROFILE_STORAGE_KEY
      && event.key !== GUEST_BIRTH_PROFILE_STORAGE_KEY
    ) return;
    store.reload();
  };
  target.addEventListener('storage', onStorage);
  return () => target.removeEventListener('storage', onStorage);
}

type PanelView =
  | { kind: 'list' }
  | { kind: 'detail'; profileId: string; context: ResolvedProfilesPanelContext }
  | { kind: 'create'; context: ResolvedProfilesPanelContext }
  | { kind: 'edit'; profileId: string; context: ResolvedProfilesPanelContext };

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
  if (snapshot.issue === 'malformed-birth-storage') {
    return 'Saved birth calculations were damaged and have been removed. Your names and manual astrology details are still available.';
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

function replacementFocusResolver(
  target: HTMLElement | null | undefined,
): (() => HTMLElement | null) | undefined {
  if (!target) return undefined;

  const gocharaKey = target.dataset.goProfileFocus;
  if (gocharaKey) {
    return () => Array.from(
      document.querySelectorAll<HTMLElement>('[data-go-profile-focus]'),
    ).find(candidate => candidate.dataset.goProfileFocus === gocharaKey) || null;
  }

  const action = target.dataset.action;
  const profileId = target.closest<HTMLElement>('[data-profile-id]')?.dataset.profileId;
  const scopeId = target.closest('#profiles-root')
    ? 'profiles-root'
    : target.closest('#tb-profiles')
      ? 'tb-profiles'
      : null;
  if (!action || !scopeId) return undefined;

  return () => {
    const scope = document.getElementById(scopeId);
    if (!scope) return null;
    return Array.from(scope.querySelectorAll<HTMLElement>('[data-action]')).find(candidate => {
      if (candidate.dataset.action !== action) return false;
      if (!profileId) return true;
      return candidate.closest<HTMLElement>('[data-profile-id]')?.dataset.profileId === profileId;
    }) || null;
  };
}

function resolvePanelContext(
  context: ProfilesPanelContext,
): ResolvedProfilesPanelContext {
  return {
    ...context,
    resolveFocusTarget: replacementFocusResolver(context.focusTarget),
  };
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

function birthApiMessage(error: unknown): string {
  if (!(error instanceof BirthProfileApiError)) {
    return 'We could not calculate this profile. Check the details and try again.';
  }
  if (error.code === 'rate-limited' && error.retryAfterSeconds) {
    return `Too many requests. Try again in about ${error.retryAfterSeconds} seconds.`;
  }
  return error.message;
}

function birthDraft(
  name: string,
  place: BirthPlaceCandidate,
  dateOfBirth: string,
  timeOfBirth: string,
  result: BirthProfileDerivation,
): GuestProfileDraft {
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

const SOUTH_INDIAN_RASHI_GRID = [
  'Meena', 'Mesha', 'Vrishabha', 'Mithuna',
  'Kumbha', null, null, 'Karka',
  'Makara', null, null, 'Simha',
  'Dhanu', 'Vrischika', 'Tula', 'Kanya',
] as const;

interface NatalProfileDetails {
  contractVersion: string;
  engine: BirthProfileDerivation['engine'];
  nakshatra: string;
  pada: 1 | 2 | 3 | 4;
  janmaRashi: string;
  lagna: string;
  lagnaDegree: number;
  planets: BirthProfileDerivation['planets'];
}

interface NatalDetailsPresentation {
  titleId: string;
  eyebrow: string;
  title: string;
  intro: string;
}

function savedNatalDetails(profile: Readonly<GuestProfile>): NatalProfileDetails | null {
  if (
    profile.source !== 'birth-details'
    || !profile.nakshatra
    || !profile.pada
    || !profile.janmaRasi
    || !profile.lagna
    || !profile.natalChart
    || !profile.calculation
  ) return null;

  return {
    contractVersion: profile.calculation.contractVersion,
    engine: { ...profile.calculation.engine },
    nakshatra: profile.nakshatra,
    pada: profile.pada,
    janmaRashi: profile.janmaRasi,
    lagna: profile.lagna,
    lagnaDegree: profile.natalChart.lagnaDegree,
    planets: profile.natalChart.planets.map(planet => ({ ...planet })),
  };
}

function renderNatalFacts(result: NatalProfileDetails): HTMLDListElement {
  const facts = element('dl', 'profiles-birth-facts');
  const factRows: Array<[string, string]> = [
    ['Nakshatra', result.nakshatra],
    ['Padam', String(result.pada)],
    ['Janma Rashi', result.janmaRashi],
    ['Lagna', `${result.lagna} · ${result.lagnaDegree.toFixed(2)}°`],
  ];
  for (const [label, value] of factRows) {
    const group = element('div', 'profiles-birth-facts__item');
    group.append(
      element('dt', 'profiles-birth-facts__label', label),
      element('dd', 'profiles-birth-facts__value', value),
    );
    facts.append(group);
  }
  return facts;
}

function renderNatalChartContent(result: NatalProfileDetails): DocumentFragment {
  const fragment = document.createDocumentFragment();
  const chart = element('div', 'profiles-chart');
  chart.setAttribute('role', 'img');
  chart.setAttribute('aria-label', 'South Indian D1 Rashi chart. A complete accessible table follows.');
  for (const rashi of SOUTH_INDIAN_RASHI_GRID) {
    if (!rashi) {
      const center = element('div', 'profiles-chart__center');
      center.setAttribute('aria-hidden', 'true');
      chart.append(center);
      continue;
    }
    const cell = element('div', 'profiles-chart__cell');
    cell.dataset.rashi = rashi;
    cell.append(element('span', 'profiles-chart__rashi', rashi));
    const occupants = result.planets
      .filter(planet => planet.rashi === rashi)
      .map(planet => `${planet.name}${planet.retrograde ? ' ℞' : ''}`);
    if (result.lagna === rashi) occupants.unshift('Lagna');
    cell.append(element('span', 'profiles-chart__occupants', occupants.join(' · ') || '—'));
    chart.append(cell);
  }

  const tableWrap = element('div', 'profiles-chart-table-wrap');
  const scrollHint = element(
    'p',
    'profiles-chart-table__hint',
    'Scroll sideways to view every column on a small screen.',
  );
  scrollHint.id = 'profiles-chart-table-hint';
  const table = element('table', 'profiles-chart-table');
  table.setAttribute('aria-describedby', scrollHint.id);
  const caption = element('caption', 'profiles-chart-table__caption', 'Planet positions in the D1 Rashi chart');
  const head = element('thead');
  const headRow = element('tr');
  for (const label of ['Graha', 'Rashi', 'Degree', 'House']) {
    const cell = element('th', undefined, label);
    cell.scope = 'col';
    headRow.append(cell);
  }
  head.append(headRow);
  const body = element('tbody');
  for (const planet of result.planets) {
    const row = element('tr');
    const values = [
      `${planet.name}${planet.retrograde ? ' (retrograde)' : ''}`,
      planet.rashi,
      `${planet.degree.toFixed(2)}°`,
      String(planet.house),
    ];
    values.forEach(value => row.append(element('td', undefined, value)));
    body.append(row);
  }
  table.append(caption, head, body);
  tableWrap.append(scrollHint, table);

  const method = element(
    'p',
    'profiles-birth-review__method',
    `${result.engine.name} ${result.engine.version} · ${result.engine.ayanamsha} ayanamsha · ${result.engine.ephemeris} ephemeris · contract ${result.contractVersion}`,
  );
  const reference = element(
    'a',
    'profiles-birth-review__reference',
    'How this is calculated and verified',
  );
  reference.href = '/docs/reference/53-birth-profile-calculation';
  fragment.append(chart, tableWrap, method, reference);
  return fragment;
}

function renderNatalDetails(
  result: NatalProfileDetails,
  presentation: NatalDetailsPresentation,
): HTMLElement {
  const section = element('section', 'profiles-birth-review');
  section.setAttribute('aria-labelledby', presentation.titleId);
  const eyebrow = element('p', 'profiles-birth-review__eyebrow', presentation.eyebrow);
  const title = element('h2', 'profiles-birth-review__title', presentation.title);
  title.id = presentation.titleId;
  title.tabIndex = -1;
  const intro = element(
    'p',
    'profiles-birth-review__intro',
    presentation.intro,
  );
  const facts = renderNatalFacts(result);
  const chartTitle = element('h3', 'profiles-chart__title', 'D1 Rashi chart');
  section.append(eyebrow, title, intro, facts, chartTitle, renderNatalChartContent(result));
  return section;
}

function renderNatalReview(result: BirthProfileDerivation): HTMLElement {
  return renderNatalDetails(result, {
    titleId: 'profile-review-title',
    eyebrow: 'Calculated profile',
    title: 'Review before saving',
    intro: 'These facts will power Daily Horoscope and Muhurtam. Confirm that the birth details above are correct before saving.',
  });
}

export function initProfilesPanel(
  store: GuestProfileStore,
  options: ProfilesPanelOptions,
): ProfilesPanelController {
  const root = options.root || document.querySelector<HTMLElement>('#profiles-root');
  if (!root) throw new Error('Profiles panel root #profiles-root was not found');
  const birthCalculationActive = options.birthCalculationEnabled
    ?? birthProfileCalculationEnabled();

  let view: PanelView = { kind: 'list' };

  const returnToOrigin = (
    context: ResolvedProfilesPanelContext,
    savedProfile?: GuestProfile,
  ): void => {
    if (context.returnTo) options.navigate(context.returnTo);
    // Select and focus only after the origin is visible again. Hidden controls
    // cannot reliably receive focus in real browsers.
    if (savedProfile) context.onSaved?.(savedProfile);

    // A completed contextual save changes the task state. Focus the selected
    // result control instead of the now-stale creation/edit trigger.
    if (savedProfile && context.returnTo === 'gochara') {
      document.getElementById('go-view')?.focus();
      return;
    }
    if (savedProfile && context.returnTo === 'tarabalam') {
      const selectedProfile = Array.from(
        document.querySelectorAll<HTMLInputElement>('[data-profile-selection]'),
      ).find(candidate => candidate.dataset.profileSelection === savedProfile.id);
      if (selectedProfile) {
        selectedProfile.focus();
        return;
      }
    }

    const originalTarget = context.focusTarget;
    const focusTarget = originalTarget?.isConnected
      ? originalTarget
      : context.resolveFocusTarget?.();
    if (focusTarget && !(focusTarget instanceof HTMLButtonElement && focusTarget.disabled)) {
      focusTarget.focus();
      if (document.activeElement === focusTarget) return;
    }

    if (context.returnTo === 'gochara') {
      document.getElementById('go-view')?.focus();
      return;
    }
    if (context.returnTo === 'tarabalam') {
      document.querySelector<HTMLElement>('#tb-profiles [data-action]')?.focus();
      return;
    }

    if (savedProfile) {
      const savedEdit = Array.from(
        root.querySelectorAll<HTMLElement>('[data-profile-id] [data-action="edit-profile"]'),
      ).find(candidate =>
        candidate.closest<HTMLElement>('[data-profile-id]')?.dataset.profileId === savedProfile.id);
      if (savedEdit) {
        savedEdit.focus();
        return;
      }
    }
    restoreFocus(null);
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

  const renderDetail = (
    profileId: string,
    context: ResolvedProfilesPanelContext,
    focusHeading = false,
  ): void => {
    const activeElement = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    const resolveActiveElement = focusHeading
      ? undefined
      : replacementFocusResolver(activeElement);
    const profile = store.get(profileId);
    if (!profile) {
      view = { kind: 'list' };
      renderList();
      restoreFocus(context.resolveFocusTarget?.() || null);
      return;
    }

    const detail = element('article', 'profiles-detail');
    detail.dataset.profileId = profile.id;

    const toolbar = element('div', 'profiles-detail__toolbar');
    const back = button('Back to profiles', 'profiles-button profiles-button--quiet');
    back.dataset.action = 'view-profile';
    back.addEventListener('click', () => {
      view = { kind: 'list' };
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

    if (profile.birthDetails) {
      const birthSection = element('section', 'profiles-detail__section');
      birthSection.setAttribute('aria-labelledby', 'profile-detail-birth-title');
      const birthTitle = element('h2', 'profiles-detail__section-title', 'Saved birth details');
      birthTitle.id = 'profile-detail-birth-title';
      birthSection.append(
        birthTitle,
        renderDetailFacts([
          ['Date of birth', profile.birthDetails.dateOfBirth],
          ['Time of birth', profile.birthDetails.timeOfBirth],
          ['Place of birth', profile.birthDetails.placeLabel],
          ['Time zone', profile.birthDetails.timezone],
        ]),
      );
      detail.append(birthSection);
    } else {
      const factsSection = element('section', 'profiles-detail__section');
      factsSection.setAttribute('aria-labelledby', 'profile-detail-facts-title');
      const factsTitle = element('h2', 'profiles-detail__section-title', 'Saved astrology details');
      factsTitle.id = 'profile-detail-facts-title';
      factsSection.append(
        factsTitle,
        renderDetailFacts([
          ['Nakshatra', profile.nakshatra || 'Not added'],
          ['Padam', profile.pada ? String(profile.pada) : 'Not added'],
          ['Janma Rashi', profile.janmaRasi || 'Not available'],
          ['Lagna', profile.lagna || 'Not added'],
        ]),
      );
      detail.append(factsSection);
    }

    const natalDetails = savedNatalDetails(profile);
    if (natalDetails) {
      const astrologySection = element(
        'section',
        'profiles-birth-review profiles-detail__natal',
      );
      astrologySection.setAttribute('aria-labelledby', 'profile-detail-astrology-title');
      const astrologyEyebrow = element(
        'p',
        'profiles-birth-review__eyebrow',
        'Saved calculation',
      );
      const astrologyTitle = element(
        'h2',
        'profiles-birth-review__title',
        'Astrology details',
      );
      astrologyTitle.id = 'profile-detail-astrology-title';
      const astrologyIntro = element(
        'p',
        'profiles-birth-review__intro',
        'These results were saved from the birth calculation. The original inputs remain visible above so you can verify them before reviewing the chart.',
      );
      astrologySection.append(
        astrologyEyebrow,
        astrologyTitle,
        astrologyIntro,
        renderNatalFacts(natalDetails),
      );
      detail.append(astrologySection);
    }

    const readinessSection = element('section', 'profiles-detail__section profiles-detail__readiness');
    readinessSection.setAttribute('aria-labelledby', 'profile-detail-readiness-title');
    const readinessTitle = element('h2', 'profiles-detail__section-title', 'Ready to use');
    readinessTitle.id = 'profile-detail-readiness-title';
    const readinessIntro = element(
      'p',
      'profiles-detail__section-copy',
      'These checks show which personalized journeys can use the saved details as they are.',
    );
    readinessSection.append(readinessTitle, readinessIntro, renderReadiness(profile));

    const readiness = guestProfileReadiness(profile);
    const journeyActions = element('div', 'profiles-form__actions');
    if (readiness.horoscope) {
      const horoscope = button(
        'View Daily Horoscope',
        'profiles-button profiles-button--primary',
      );
      horoscope.dataset.action = 'view-daily-horoscope';
      horoscope.addEventListener('click', () => {
        if (options.onViewDailyHoroscope) {
          options.onViewDailyHoroscope(profile.id);
        } else {
          options.navigate('gochara');
        }
      });
      journeyActions.append(horoscope);
    }
    if (readiness.muhurta) {
      const muhurta = button(
        'Find Muhurtam',
        'profiles-button profiles-button--secondary',
      );
      muhurta.dataset.action = 'find-muhurtam';
      muhurta.addEventListener('click', () => {
        if (options.onFindMuhurtam) {
          options.onFindMuhurtam(profile.id);
        } else {
          options.navigate('tarabalam');
        }
      });
      journeyActions.append(muhurta);
    }
    if (journeyActions.childElementCount > 0) readinessSection.append(journeyActions);
    detail.append(readinessSection);

    if (natalDetails) {
      const chartSection = element('section', 'profiles-detail__section profiles-detail__chart');
      chartSection.setAttribute('aria-labelledby', 'profile-detail-chart-title');
      const chartTitle = element('h2', 'profiles-detail__section-title', 'D1 Rashi chart');
      chartTitle.id = 'profile-detail-chart-title';
      const chartIntro = element(
        'p',
        'profiles-detail__section-copy',
        'The South Indian chart and accessible planet table below are the saved result; opening this page does not calculate them again.',
      );
      chartSection.append(
        chartTitle,
        chartIntro,
        renderNatalChartContent(natalDetails),
      );
      detail.append(chartSection);
    } else {
      const unavailable = element('section', 'profiles-detail__section profiles-detail__unavailable');
      unavailable.setAttribute('aria-labelledby', 'profile-detail-chart-title');
      const unavailableTitle = element(
        'h2',
        'profiles-detail__section-title',
        'Natal chart and calculation',
      );
      unavailableTitle.id = 'profile-detail-chart-title';
      const unavailableCopy = element(
        'p',
        'profiles-detail__section-copy',
        'Natal chart and calculation details are available only for profiles calculated from birth details.',
      );
      unavailable.append(unavailableTitle, unavailableCopy);
      detail.append(unavailable);
    }

    root.replaceChildren(detail);
    if (focusHeading) {
      heading.focus();
    } else {
      resolveActiveElement?.()?.focus();
    }
  };

  const renderProfile = (profile: Readonly<GuestProfile>): HTMLLIElement => {
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
    details.textContent = facts.join(' · ');
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

  const renderList = (): void => {
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
    for (const profile of snapshot.profiles) roster.append(renderProfile(profile));
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

    const footer = element('div', 'profiles-actions');
    const atLimit = snapshot.profiles.length >= MAX_GUEST_PROFILES;
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
    root.replaceChildren(fragment);
  };

  let activeFormMethod: 'birth-details' | 'manual' = birthCalculationActive
    ? 'birth-details'
    : 'manual';
  let renderBirthForm: (
    mode: 'create' | 'edit',
    context: ResolvedProfilesPanelContext,
    profile?: GuestProfile,
  ) => void;

  const renderManualForm = (
    mode: 'create' | 'edit',
    context: ResolvedProfilesPanelContext,
    profile?: GuestProfile,
  ): void => {
    activeFormMethod = 'manual';
    const fragment = document.createDocumentFragment();
    const heading = element('h1', 'profiles-title', mode === 'create' ? 'Create profile manually' : 'Edit profile manually');
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
      'Saved only in this browser. Manual details are never sent to a server. No account, cloud sync, or recovery.',
    );
    fragment.append(heading, intro, privacy);

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
      fragment.append(methods);
    }
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
        source: 'manual',
        name,
        nakshatra: nakshatraSelect.value || null,
        pada: padaValue === 1 || padaValue === 2 || padaValue === 3 || padaValue === 4
          ? padaValue
          : null,
        lagna: lagnaSelect.value || null,
        janmaRasi: null,
        birthDetails: null,
        natalChart: null,
        calculation: null,
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

  renderBirthForm = (
    mode: 'create' | 'edit',
    context: ResolvedProfilesPanelContext,
    profile?: GuestProfile,
  ): void => {
    if (!birthCalculationActive) {
      renderManualForm(mode, context, profile);
      return;
    }
    activeFormMethod = 'birth-details';
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
    }

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
    fragment.append(methods);

    const form = element('form', 'profiles-form profiles-birth-form');
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
    dateInput.max = new Date().toISOString().slice(0, 10);
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
    selectedPlaceText.hidden = !selectedPlace;
    const placeError = element('p', 'profiles-field__error');
    placeError.id = 'profile-birth-place-error';
    placeError.hidden = true;
    const placeStatus = element('p', 'profiles-place-status');
    placeStatus.id = 'profile-place-status';
    placeStatus.setAttribute('role', 'status');
    placeStatus.setAttribute('aria-live', 'polite');
    const placeResults = element('ul', 'profiles-place-results');
    placeResults.setAttribute('aria-label', 'Matching birthplaces');
    placeGroup.append(
      placeLabel,
      placeSearchRow,
      placeHelp,
      selectedPlaceText,
      placeError,
      placeStatus,
      placeResults,
    );
    knownDetails.append(knownLegend, dateTimeGrid, placeGroup);

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

    const reviewHost = element('div', 'profiles-birth-review-host');
    const formError = element('p', 'profiles-form__error');
    formError.id = 'profile-form-error';
    formError.setAttribute('role', 'alert');
    formError.hidden = true;

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
    actions.append(save, cancel);

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

    const updateSelectedPlace = (): void => {
      selectedPlaceText.hidden = !selectedPlace;
      selectedPlaceText.textContent = selectedPlace
        ? `Selected: ${selectedPlace.label} · ${selectedPlace.timezone}`
        : '';
    };
    const updateReview = (): void => {
      reviewHost.replaceChildren();
      if (calculated) reviewHost.append(renderNatalReview(calculated));
      save.disabled = !calculated;
      saveHelp.textContent = calculated
        ? 'Review complete. Saving keeps these details only in this browser.'
        : 'Calculate and review the astrology details before saving.';
      calculateButton.textContent = calculated ? 'Recalculate details' : 'Calculate details';
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
    const showPlaceResults = (
      results: BirthPlaceCandidate[],
      attribution: string,
    ): void => {
      placeResults.replaceChildren();
      if (results.length === 0) {
        placeStatus.textContent = 'No matching places found. Try a nearby city or add a state or country.';
        return;
      }
      placeStatus.textContent = `${results.length} ${results.length === 1 ? 'place' : 'places'} found. ${attribution}`;
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
      placeResults.replaceChildren();
      try {
        const response = await (options.searchPlaces || searchBirthPlaces)(query);
        if (sequence !== placeSearchSequence) return;
        showPlaceResults(response.results, response.attribution);
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
      if (!selectedPlace || placeInput.value.trim() !== selectedPlace.label) {
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
      let invalid: HTMLElement | null = null;
      if (!dateInput.value || dateInput.value > dateInput.max) {
        dateInput.setAttribute('aria-invalid', 'true');
        dateError.textContent = 'Enter a valid birth date that is not in the future.';
        dateError.hidden = false;
        invalid ||= dateInput;
      }
      if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(timeInput.value)) {
        timeInput.setAttribute('aria-invalid', 'true');
        timeError.textContent = 'Enter the recorded local birth time.';
        timeError.hidden = false;
        invalid ||= timeInput;
      }
      if (!selectedPlace) {
        placeInput.setAttribute('aria-invalid', 'true');
        placeError.textContent = 'Find and select a birthplace from the results.';
        placeError.hidden = false;
        invalid ||= placeInput;
      }
      if (invalid || !selectedPlace) {
        invalid?.focus();
        return;
      }

      const sequence = ++calculationSequence;
      const calculationPlace = selectedPlace;
      calculateButton.disabled = true;
      calculateButton.setAttribute('aria-busy', 'true');
      calculationError.hidden = true;
      calculationError.textContent = '';
      calculationStatus.textContent = 'Calculating the birth chart…';
      try {
        const nextResult = await (options.deriveProfile || deriveBirthProfile)({
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
      if (!selectedPlace || !calculated) {
        calculationError.textContent = 'Calculate and review the astrology details before saving.';
        calculationError.hidden = false;
        calculateButton.focus();
        return;
      }

      formError.hidden = true;
      formError.textContent = '';
      const draft = birthDraft(
        name,
        selectedPlace,
        dateInput.value,
        timeInput.value,
        calculated,
      );
      view = { kind: 'list' };
      try {
        const savedProfile = mode === 'edit' && profile
          ? store.update(profile.id, draft)
          : store.create(draft);
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

    updateSelectedPlace();
    updateDuplicateWarning();
    updateReview();
    nameInput.focus();
  };

  const controller: ProfilesPanelController = {
    openCreate(context = {}) {
      const resolvedContext = resolvePanelContext(context);
      if (store.getSnapshot().profiles.length >= MAX_GUEST_PROFILES) {
        view = { kind: 'list' };
        renderList();
        return;
      }
      view = { kind: 'create', context: resolvedContext };
      activeFormMethod = birthCalculationActive ? 'birth-details' : 'manual';
      if (birthCalculationActive) {
        renderBirthForm('create', resolvedContext);
      } else {
        renderManualForm('create', resolvedContext);
      }
    },
    openView(profileId, context = {}) {
      const resolvedContext = resolvePanelContext(context);
      const profile = store.get(profileId);
      if (!profile) {
        view = { kind: 'list' };
        renderList();
        restoreFocus(null);
        return;
      }
      view = { kind: 'detail', profileId, context: resolvedContext };
      renderDetail(profileId, resolvedContext, true);
    },
    openEdit(profileId, context = {}) {
      const resolvedContext = resolvePanelContext(context);
      const profile = store.get(profileId);
      if (!profile) {
        view = { kind: 'list' };
        renderList();
        return;
      }
      if (profile.source === 'birth-details' && !birthCalculationActive) {
        view = { kind: 'detail', profileId, context: resolvedContext };
        renderDetail(profileId, resolvedContext, true);
        return;
      }
      view = { kind: 'edit', profileId, context: resolvedContext };
      activeFormMethod = profile.source;
      if (activeFormMethod === 'birth-details') {
        renderBirthForm('edit', resolvedContext, profile);
      } else {
        renderManualForm('edit', resolvedContext, profile);
      }
    },
    render() {
      if (view.kind === 'detail') {
        renderDetail(view.profileId, view.context);
        return;
      }
      if (view.kind === 'create') {
        if (!birthCalculationActive || activeFormMethod === 'manual') {
          renderManualForm('create', view.context);
        } else {
          renderBirthForm('create', view.context);
        }
        return;
      }
      if (view.kind === 'edit') {
        const profile = store.get(view.profileId);
        if (profile) {
          if (profile.source === 'birth-details' && !birthCalculationActive) {
            view = { kind: 'detail', profileId: profile.id, context: view.context };
            renderDetail(profile.id, view.context);
          } else if (activeFormMethod === 'manual') {
            renderManualForm('edit', view.context, profile);
          } else {
            renderBirthForm('edit', view.context, profile);
          }
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

  const unsubscribe = store.subscribe(() => {
    // An external tab may change persistence while this form is open. Keep the
    // guest's unsaved fields and focus intact; Cancel or Save reconciles against
    // the already-refreshed store snapshot.
    if (view.kind === 'list' || view.kind === 'detail') controller.render();
  });
  controller.render();
  return controller;
}
