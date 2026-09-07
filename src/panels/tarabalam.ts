// typing lands with the component rewrite, not the move.
//
// Tarabalam panel + the nested Muhurta finder: profiles, good-day
// calculation, slot search (client-side mirror of the Python scorer),
// rendering and WhatsApp shares.

import {
  MU_RASHI_NAMES,
  MU_CHANDRA_GOOD, MU_CHANDRA_PUJA,
  MU_TIER_NAMES,
  muLagnaPosition, muLagnaVerdict,
  muIsFavourableLagna, muLagnaAtMin,
  muLagnaClassOf, muLagnasInClass,
  muScoreTier, muRelativeTier, muCanonicalNakshatra, muScoreTithiClass,
  muEndsBySolarNoon, muCombustionDropReason,
  computeDayDosha,
} from '../muhurta-scorer';
import { selEl, inpEl } from '../lib/dom';
import { getSelection } from '../selection-store';
import { loadFeed } from '../lib/feed-loader';
import { parseDescription, TIME_PART } from '../lib/parse-description';
import { fmtT, stampOf } from '../lib/format';
import { htmlEsc } from '../lib/html';
import { gcEvent } from '../lib/analytics';
import { loadLagna, lagnaDayFor } from '../lib/lagna-loader';
import {
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_COMMIT_STORAGE_KEY,
  GUEST_PROFILE_STORAGE_KEY,
  MAX_GUEST_PROFILES,
  guestProfileReadiness,
  mergeLegacyGuestProfileRow,
  removeLegacyGuestProfileRow,
  readLegacyGuestProfileRows,
  writeLegacyGuestProfileRows,
  type GuestProfile,
  type GuestProfileSnapshot,
  type GuestProfileStore,
  type ProfileStorage,
} from '../lib/guest-profile-store';
import {
  loadMuhurtamRoleSelections,
  loadMuhurtamProfileSelection,
  saveMuhurtamRoleSelection,
  saveMuhurtamProfileSelection,
  toggleMuhurtamProfileSelection,
  type JourneyGuestProfile,
} from '../lib/profile-selection';
import { RASI_NAMES, NAKSHATRA_NAMES, rasiFromStar } from '../data/rasis';
import { CITY_LOCATIONS } from '../data/cities';
import { MUHURTA_DAY } from '../data/muhurtas';
import activityContract from '../data/activity-rules.generated.json';
import { roleForActivity } from '../scorer/personal-election-screening';
import { enrichElectionChartSlots } from '../scorer/election-chart-enrichment';
import {
  automatedRulesFor,
  chartAssessorCompleteFor,
  chartManualRemaindersFor,
} from '../scorer/election-chart-screening';
import { localWallTimeToInstant } from '../lib/election-chart-api';
import { electionChartCalculationEnabled } from '../lib/remote-calculation-activation';
import {
  evaluateConfiguredKarnavedhaDaylight,
  karnavedhaDaylightDropReason,
} from '../scorer/election-assessors/karnavedha-daylight';
import { getLoadedEvents } from './today';

// --- Tarabalam tool ---

const TB_NAKSHATRAS = NAKSHATRA_NAMES;
const TARA_NAMES = ['Janma','Sampat','Vipat','Kshema','Pratyak','Sadhana','Naidhana','Mitra','Parama Mitra'];
const TARA_GOOD = new Set([2,4,6,8,9]);
const TB_RASIS = RASI_NAMES;
const CHANDRA_GOOD = new Set([1,3,6,7,10,11]);
const CHANDRA_PUJA = new Set([2,5,9]);

type MuManualCheckRow = {
  id: string;
  source_index: number;
  source_text: string;
  text: string;
  class: string;
  display_section: 'chart' | 'information' | 'practical';
  applicable_varas?: string[];
  purpose?: string;
};

function muManualCheckRows(activity: string): MuManualCheckRow[] {
  const activities = activityContract.check_contract.activities as unknown as
    Record<string, { manual_checks: MuManualCheckRow[] }>;
  return activities[activity]?.manual_checks || [];
}

export function muRelevantManualChecks(activity: string, vaaram: string) {
  return muManualCheckRows(activity).filter(row =>
    !row.applicable_varas?.length || row.applicable_varas.includes(vaaram));
}

export function muClassifyManualChecks(
  activity: string,
  rows: MuManualCheckRow[] | null = null,
) {
  const result = { chart: [], information: [], practical: [] };
  for (const row of rows || muManualCheckRows(activity)) {
    result[row.display_section].push(row.text);
  }
  return result;
}

type MuChartScreeningProgress = {
  state: 'screened' | 'not-run' | 'manual-only' | 'unsupported-system'
    | 'disabled' | 'unavailable';
  screenedCount: number;
};

const MU_PARTIAL_ASSESSOR_DISCLOSURE =
  'The event-specific clauses were computed, but the overall election-chart assessment remains partial/provisional until the shared baseline is complete.';

/**
 * Describe a partial assessor as computed only after chart facts were actually
 * screened. A partially completed unavailable run may truthfully make the same
 * claim for its already-screened candidates; every zero-screen state stays
 * silent even if a malformed caller supplies a contradictory count.
 */
export function muEventSpecificCompletionDisclosure(
  activity: string,
  chartEnrichment: MuChartScreeningProgress | null,
): string | null {
  const partialAssessor = automatedRulesFor(activity).length > 0
    && !chartAssessorCompleteFor(activity);
  const screeningApplied = !!chartEnrichment
    && chartEnrichment.screenedCount > 0
    && (
      chartEnrichment.state === 'screened'
      || chartEnrichment.state === 'unavailable'
    );
  return partialAssessor && screeningApplied
    ? MU_PARTIAL_ASSESSOR_DISCLOSURE
    : null;
}

function muOrdinal(value) {
  const mod100 = value % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${value}th`;
  return `${value}${({ 1: 'st', 2: 'nd', 3: 'rd' })[value % 10] || 'th'}`;
}
let TB_DAYS = null;    // last computed result rows
let TB_EVENTS = null;  // feed events used for the last calculation

function taraOf(janmaName, dayName) {
  const j = TB_NAKSHATRAS.indexOf(janmaName), d = TB_NAKSHATRAS.indexOf(dayName);
  if (j < 0 || d < 0) return null;
  return ((d - j + 27) % 27) % 9 + 1;
}

export function tbChandraVerdict(pos: number): string {
  if (CHANDRA_GOOD.has(pos)) return 'good';
  if (CHANDRA_PUJA.has(pos)) return 'puja';
  return 'bad';
}

function chandraOf(janmaRasi, dayRasi) {
  const j = TB_RASIS.indexOf(janmaRasi), d = TB_RASIS.indexOf(dayRasi);
  if (j < 0 || d < 0) return null;
  const pos = ((d - j + 12) % 12) + 1;
  return { pos, verdict: tbChandraVerdict(pos) };
}

type TarabalamPada = 1 | 2 | 3 | 4;

export interface TarabalamProfileActions {
  createProfile(trigger: HTMLElement): void;
  editProfile(id: string, trigger: HTMLElement): void;
  manageProfiles(trigger: HTMLElement): void;
}

export interface TarabalamProfilesController {
  render(): void;
  destroy(): void;
  getParticipants(): JourneyGuestProfile[];
  getSelectedIds(): string[];
  getRoleParticipant(activity: string): JourneyGuestProfile | null;
  selectProfile(id: string): boolean;
}

interface ManualParticipant {
  id: string;
  name: string;
  nak: string;
  pada: TarabalamPada | null;
  lagna: string | null;
}

interface InternalTarabalamProfilesController extends TarabalamProfilesController {
  addManualParticipant(): void;
  removeManualParticipant(index: number): void;
  clearParticipants(): void;
}

let TB_PROFILE_CONTROLLER: InternalTarabalamProfilesController | null = null;
let TB_MANUAL_SEQUENCE = 0;
let TB_LEGACY_ROWS = 1;

function tbNode<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function tbButton(text: string, className = 'tb-add'): HTMLButtonElement {
  const node = tbNode('button', className, text);
  node.type = 'button';
  return node;
}

function tbAppendOption(select: HTMLSelectElement, value: string, label: string): void {
  const option = tbNode('option', undefined, label);
  option.value = value;
  select.append(option);
}

function tbDisplayName(profile: Readonly<GuestProfile>): string {
  return profile.name || 'Unnamed profile';
}

function tbSelectionStorage(): ProfileStorage {
  try {
    return globalThis.localStorage;
  } catch {
    return {
      getItem: () => { throw new Error('storage unavailable'); },
      setItem: () => { throw new Error('storage unavailable'); },
    };
  }
}

function tbProfileStoreIssue(snapshot: GuestProfileSnapshot): string | null {
  if (snapshot.issue === 'malformed-storage') {
    return 'Saved profile data was unreadable and has been reset safely.';
  }
  if (snapshot.issue === 'uncommitted-birth-storage') {
    return 'A saved birth calculation could not be verified. Manual profile details remain available.';
  }
  if (snapshot.issue === 'unsupported-storage-version') {
    return 'These profiles use a newer or unrecognized format. They are available for this session, but changes cannot be saved here.';
  }
  if (snapshot.persistence === 'memory' || snapshot.issue === 'storage-unavailable') {
    return 'Browser storage is unavailable. Profile choices work for this page only.';
  }
  return null;
}

function tbManualProfile(
  participant: ManualParticipant,
  index: number,
): JourneyGuestProfile | null {
  if (!participant.nak) return null;
  return {
    id: participant.id,
    name: participant.name.trim() || `Person ${index + 1}`,
    nak: participant.nak,
    pada: participant.pada,
    rasi: rasiFromStar(participant.nak, participant.pada),
    lagna: participant.lagna,
  };
}

function tbKnownProfileValue(rawValue, values): string | null {
  return typeof rawValue === 'string' && values.includes(rawValue)
    ? rawValue
    : null;
}

function tbLegacyPada(rawValue): TarabalamPada | null {
  const value = Number(rawValue);
  return ([1, 2, 3, 4] as const).includes(value as TarabalamPada)
    ? value as TarabalamPada
    : null;
}

function tbLegacyName(rawValue, index: number): string {
  if (typeof rawValue === 'string' && rawValue.trim()) return rawValue.trim();
  return index === 0 ? 'You' : `Person ${index + 1}`;
}

function tbLegacyParticipant(previous, index: number): JourneyGuestProfile | null {
  const valueOf = (field: string, fallback) => {
    const input = document.getElementById(`tb-${field}-${index}`) as HTMLInputElement | null;
    return input?.value ?? fallback;
  };
  const nakshatra = tbKnownProfileValue(
    valueOf('nak', previous.nak),
    TB_NAKSHATRAS,
  );
  if (!nakshatra) return null;
  const pada = tbLegacyPada(valueOf('pada', previous.pada));
  return {
    id: typeof previous.id === 'string' ? previous.id : `legacy_${index}`,
    name: tbLegacyName(valueOf('name', previous.name), index),
    nak: nakshatra,
    pada,
    rasi: rasiFromStar(nakshatra, pada),
    lagna: tbKnownProfileValue(valueOf('lagna', previous.lagna), TB_RASIS),
  };
}

/** The exact participant adapter consumed by Tarabalam and findMuhurta. */
export function tbProfiles(): JourneyGuestProfile[] {
  if (TB_PROFILE_CONTROLLER) return TB_PROFILE_CONTROLLER.getParticipants();

  // A controller is installed during normal application startup. Keep the
  // former inline form usable for older embed/bootstrap entry points without
  // making it the owner of stable profile records again.
  const saved = readLegacyGuestProfileRows(localStorage);
  const participants: JourneyGuestProfile[] = [];
  for (let index = 0; index < TB_LEGACY_ROWS; index += 1) {
    const participant = tbLegacyParticipant(saved[index] || {}, index);
    if (participant) participants.push(participant);
  }
  return participants;
}

/**
 * Bind stable local guest profiles to the existing Muhurtam participant root.
 * Saved-profile choices persist by ID; one-off participants live only in this
 * controller and are deliberately never written to the profile store.
 */
export function initTarabalamProfiles(
  store: GuestProfileStore,
  actions: TarabalamProfileActions,
): TarabalamProfilesController {
  TB_PROFILE_CONTROLLER?.destroy();

  const root = document.querySelector<HTMLElement>('#tb-profiles');
  if (!root) throw new Error('Muhurtam profile root #tb-profiles was not found');

  const section = root.closest<HTMLElement>('.tb-section');
  const legacyAddButton = section?.querySelector<HTMLButtonElement>('#tb-add-btn') || null;
  const clearButton = section?.querySelector<HTMLButtonElement>('.tb-reset') || null;
  const activitySelect = document.querySelector<HTMLSelectElement>('#mu-activity');
  const selectionStorage = tbSelectionStorage();
  let snapshot = store.getSnapshot();
  let selection = loadMuhurtamProfileSelection(selectionStorage, snapshot.profiles);
  let manualParticipants: ManualParticipant[] = [];
  let transientIssue: string | null = null;
  let roleSelectionState = loadMuhurtamRoleSelections(
    selectionStorage,
    snapshot.profiles,
  );
  const roleSelections = new Map<string, string>(
    Object.entries(roleSelectionState.selections),
  );

  const persistRoleSelection = (activity: string, profileId: string): void => {
    const savedId = snapshot.profiles.some(profile => profile.id === profileId)
      ? profileId
      : null;
    if ((roleSelectionState.selections[activity] || null) === savedId) return;
    roleSelectionState = saveMuhurtamRoleSelection(
      selectionStorage,
      roleSelectionState.selections,
      activity,
      savedId,
      snapshot.profiles,
    );
  };

  const participantCount = (): number =>
    selection.profiles.length + manualParticipants.filter((manual, index) =>
      Boolean(tbManualProfile(manual, index))).length;

  const occupiedSlots = (): number => selection.selectedIds.length + manualParticipants.length;

  const currentParticipants = (): JourneyGuestProfile[] => {
    const saved = selection.profiles.map(profile => ({ ...profile }));
    const manual = manualParticipants
      .map((participant, index) => tbManualProfile(participant, index))
      .filter((profile): profile is JourneyGuestProfile => profile !== null);
    return [...saved, ...manual].slice(0, MAX_GUEST_PROFILES);
  };

  const restoreProfileSelectionFocus = (profileId: string): void => {
    const target = Array.from(
      root.querySelectorAll<HTMLInputElement>('input[data-profile-selection]'),
    ).find(candidate => candidate.dataset.profileSelection === profileId);
    target?.focus();
  };

  const restoreManualFieldFocus = (participantId: string, field: string): void => {
    const target = Array.from(
      root.querySelectorAll<HTMLElement>('[data-manual-participant][data-manual-field]'),
    ).find(candidate =>
      candidate.dataset.manualParticipant === participantId &&
      candidate.dataset.manualField === field);
    target?.focus();
  };

  const selectionSummary = (): string => {
    const saved = selection.profiles.length;
    const manual = manualParticipants.filter((candidate, index) =>
      Boolean(tbManualProfile(candidate, index))).length;
    const total = saved + manual;
    if (!total) return 'No participant screening is selected. Slots will use general Muhurtam rules.';
    const parts: string[] = [];
    if (saved) parts.push(`${saved} saved`);
    if (manual) parts.push(`${manual} just for this search`);
    return `${total} ${total === 1 ? 'participant' : 'participants'} selected · ${parts.join(', ')}.`;
  };

  const renderSavedProfile = (profile: Readonly<GuestProfile>): HTMLLIElement => {
    const readiness = guestProfileReadiness(profile);
    const item = tbNode('li', 'muhurta-profile-option');
    item.dataset.profileId = profile.id;

    const label = tbNode('label', 'muhurta-profile-option__label');
    const checkbox = tbNode('input') as HTMLInputElement;
    checkbox.type = 'checkbox';
    checkbox.value = profile.id;
    checkbox.checked = selection.selectedIds.includes(profile.id);
    checkbox.disabled = !readiness.muhurta ||
      (!checkbox.checked && occupiedSlots() >= MAX_GUEST_PROFILES);
    checkbox.dataset.profileSelection = profile.id;

    const identity = tbNode('span', 'muhurta-profile-option__identity');
    const name = tbNode('strong', 'muhurta-profile-option__name', tbDisplayName(profile));
    const details: string[] = [];
    if (!readiness.muhurta) {
      details.push('Needs Nakshatra before Muhurtam');
    } else {
      details.push(
        profile.pada
          ? `${profile.nakshatra}, Padam ${profile.pada}`
          : String(profile.nakshatra),
        readiness.janmaRasi
          ? `${readiness.janmaRasi} Janma Rashi`
          : 'Add Padam to derive Janma Rashi',
      );
      if (profile.lagna) details.push(`${profile.lagna} Lagna`);
    }
    const detail = tbNode('span', 'muhurta-profile-option__details', details.join(' · '));
    identity.append(name, detail);
    label.append(checkbox, identity);

    const edit = tbButton(
      readiness.muhurta ? 'Edit' : 'Complete profile',
      'tb-reset muhurta-profile-option__edit',
    );
    edit.setAttribute(
      'aria-label',
      readiness.muhurta
        ? `Edit ${tbDisplayName(profile)}`
        : `Complete ${tbDisplayName(profile)} profile`,
    );
    edit.dataset.action = 'edit-profile';
    edit.addEventListener('click', event => {
      actions.editProfile(profile.id, event.currentTarget as HTMLElement);
    });
    item.append(label, edit);

    checkbox.addEventListener('change', () => {
      invalidateMuhurtaSearch();
      const shouldRestoreFocus = document.activeElement === checkbox;
      if (checkbox.checked && occupiedSlots() >= MAX_GUEST_PROFILES) {
        transientIssue = `Choose up to ${MAX_GUEST_PROFILES} participants for one Muhurtam search.`;
      } else {
        transientIssue = null;
        selection = toggleMuhurtamProfileSelection(
          selectionStorage,
          selection.selectedIds,
          profile.id,
          checkbox.checked,
          snapshot.profiles,
        );
      }
      controller.render();
      if (shouldRestoreFocus) restoreProfileSelectionFocus(profile.id);
    });

    return item;
  };

  const labelledSelect = (
    labelText: string,
    value: string,
    values: ReadonlyArray<readonly [string, string]>,
    onChange: (value: string) => void,
    participantId: string,
    field: string,
  ): HTMLLabelElement => {
    const label = tbNode('label', 'muhurta-manual-field');
    const text = tbNode('span', 'muhurta-manual-field__label', labelText);
    const select = tbNode('select') as HTMLSelectElement;
    for (const [optionValue, optionLabel] of values) {
      tbAppendOption(select, optionValue, optionLabel);
    }
    select.value = value;
    select.dataset.manualParticipant = participantId;
    select.dataset.manualField = field;
    select.addEventListener('change', () => {
      invalidateMuhurtaSearch();
      const shouldRestoreFocus = document.activeElement === select;
      onChange(select.value);
      controller.render();
      if (shouldRestoreFocus) restoreManualFieldFocus(participantId, field);
    });
    label.append(text, select);
    return label;
  };

  const renderManualParticipant = (
    participant: ManualParticipant,
    index: number,
  ): HTMLFieldSetElement => {
    const fields = tbNode('fieldset', 'tb-profile-row muhurta-manual-profile');
    fields.dataset.manualId = participant.id;
    const legend = tbNode('legend', 'muhurta-manual-profile__legend', `Person ${index + 1} · just for this search`);

    const nameLabel = tbNode('label', 'muhurta-manual-field');
    const nameText = tbNode('span', 'muhurta-manual-field__label', 'Name');
    const nameInput = tbNode('input') as HTMLInputElement;
    nameInput.type = 'text';
    nameInput.value = participant.name;
    nameInput.placeholder = 'Optional';
    nameInput.autocomplete = 'off';
    nameInput.dataset.manualParticipant = participant.id;
    nameInput.dataset.manualField = 'name';
    nameInput.addEventListener('input', () => {
      invalidateMuhurtaSearch();
      participant.name = nameInput.value;
      const summary = root.querySelector<HTMLElement>('[data-muhurta-selection-summary]');
      if (summary) summary.textContent = selectionSummary();
    });
    nameLabel.append(nameText, nameInput);

    const nakshatra = labelledSelect(
      'Birth star',
      participant.nak,
      [['', 'Choose Nakshatra'], ...TB_NAKSHATRAS.map(value => [value, value] as const)],
      value => {
        participant.nak = value;
        if (!value) participant.pada = null;
        transientIssue = null;
      },
      participant.id,
      'nakshatra',
    );
    const padam = labelledSelect(
      'Padam',
      participant.pada ? String(participant.pada) : '',
      [['', 'Not known'], ['1', '1'], ['2', '2'], ['3', '3'], ['4', '4']],
      value => {
        participant.pada = value ? Number(value) as TarabalamPada : null;
      },
      participant.id,
      'pada',
    );
    const lagna = labelledSelect(
      'Lagna',
      participant.lagna || '',
      [['', 'Not known'], ...TB_RASIS.map(value => [value, value] as const)],
      value => {
        participant.lagna = value || null;
      },
      participant.id,
      'lagna',
    );

    const adapted = tbManualProfile(participant, index);
    let readinessText = 'Add a birth star to include this person in the search.';
    if (adapted) {
      const facts = ['Ready for Muhurtam'];
      facts.push(adapted.rasi
        ? `${adapted.rasi} Janma Rashi`
        : 'Add Padam to derive Janma Rashi');
      if (adapted.lagna) facts.push(`${adapted.lagna} Lagna`);
      readinessText = facts.join(' · ');
    }
    const readiness = tbNode('p', 'muhurta-manual-profile__readiness', readinessText);
    readiness.setAttribute('aria-live', 'polite');

    const remove = tbButton(`Remove person ${index + 1}`, 'tb-remove');
    remove.dataset.action = 'remove-manual';
    remove.addEventListener('click', () => controller.removeManualParticipant(index));
    fields.append(legend, nameLabel, nakshatra, padam, lagna, readiness, remove);
    return fields;
  };

  const addManualParticipant = (): void => {
    invalidateMuhurtaSearch();
    if (occupiedSlots() >= MAX_GUEST_PROFILES) {
      transientIssue = `Choose up to ${MAX_GUEST_PROFILES} participants for one Muhurtam search.`;
      controller.render();
      return;
    }
    TB_MANUAL_SEQUENCE += 1;
    manualParticipants.push({
      id: `manual_${TB_MANUAL_SEQUENCE}`,
      name: '',
      nak: '',
      pada: null,
      lagna: null,
    });
    transientIssue = null;
    controller.render();
  };

  const clearParticipants = (): void => {
    invalidateMuhurtaSearch(false);
    selection = saveMuhurtamProfileSelection(selectionStorage, [], snapshot.profiles);
    manualParticipants = [];
    transientIssue = null;
    TB_DAYS = null;
    TB_EVENTS = null;
    for (const id of ['tb-summary', 'tb-result', 'mu-context', 'mu-result']) {
      const target = document.getElementById(id);
      if (target) target.replaceChildren();
    }
    controller.render();
  };

  const onLegacyAdd = (event: Event): void => {
    event.preventDefault();
    addManualParticipant();
  };
  const onClear = (event: Event): void => {
    event.preventDefault();
    clearParticipants();
  };

  // The old inline controls remain in the HTML for compatibility while the
  // panel markup is being migrated. Their behaviour is now session-scoped.
  if (legacyAddButton) {
    legacyAddButton.removeAttribute('onclick');
    legacyAddButton.hidden = true;
    legacyAddButton.addEventListener('click', onLegacyAdd);
  }
  if (clearButton) {
    clearButton.removeAttribute('onclick');
    clearButton.textContent = 'clear selection';
    clearButton.title = 'Clear participants from this search';
    clearButton.addEventListener('click', onClear);
  }

  const renderNotices = (): void => {
    const storeIssue = tbProfileStoreIssue(snapshot);
    let roleStorageIssue: string | null = null;
    if (roleSelectionState.storageIssue === 'storage-unavailable') {
      roleStorageIssue = 'Role choices work for this page, but this browser cannot save them.';
    } else if (roleSelectionState.storageIssue === 'malformed-storage') {
      roleStorageIssue = 'Saved role choices were unreadable and have been reset safely.';
    }
    for (const message of [
      storeIssue, selection.message, roleStorageIssue, transientIssue,
    ].filter(Boolean)) {
      const notice = tbNode('p', 'preview-error muhurta-profile-notice', message as string);
      notice.setAttribute('role', 'status');
      root.append(notice);
    }
  };

  const renderSavedProfiles = (): void => {
    if (!snapshot.profiles.length) {
      root.append(tbNode(
        'p',
        'muhurta-profile-empty',
        'No saved profiles yet. You can still search without personal screening or add someone for this search.',
      ));
      return;
    }
    const fieldset = tbNode('fieldset', 'muhurta-saved-profiles');
    const legend = tbNode('legend', 'muhurta-saved-profiles__legend', 'Saved profiles');
    const list = tbNode('ul', 'muhurta-saved-profiles__list');
    for (const profile of snapshot.profiles) list.append(renderSavedProfile(profile));
    fieldset.append(legend, list);
    root.append(fieldset);
  };

  const renderManualProfiles = (): void => {
    if (!manualParticipants.length) return;
    const manual = tbNode('div', 'muhurta-manual-profiles');
    const heading = tbNode('h3', 'muhurta-manual-profiles__title', 'Just for this search');
    manual.append(heading);
    manualParticipants.forEach((participant, index) => {
      manual.append(renderManualParticipant(participant, index));
    });
    root.append(manual);
  };

  const renderProfileActions = (): void => {
    const actionsRow = tbNode('div', 'muhurta-profile-actions');
    const addManual = tbButton('Add someone for this search');
    addManual.dataset.action = 'add-manual';
    addManual.disabled = occupiedSlots() >= MAX_GUEST_PROFILES;
    addManual.addEventListener('click', addManualParticipant);
    const create = tbButton('Create saved profile', 'tb-add muhurta-profile-create');
    create.dataset.action = 'create-profile';
    create.disabled = snapshot.profiles.length >= MAX_GUEST_PROFILES;
    create.addEventListener('click', event => {
      actions.createProfile(event.currentTarget as HTMLElement);
    });
    const manage = tbButton('Manage profiles', 'tb-reset muhurta-profile-manage');
    manage.dataset.action = 'manage-profiles';
    manage.addEventListener('click', event => {
      actions.manageProfiles(event.currentTarget as HTMLElement);
    });
    actionsRow.append(addManual, create, manage);
    root.append(actionsRow);
  };

  const renderRoleSelection = (): void => {
    const activity = activitySelect?.value || 'any';
    const role = roleForActivity(activity);
    if (!role) return;
    const participants = currentParticipants();
    const roleBlock = tbNode('div', 'muhurta-role-selection');
    const prompt = tbNode('p', 'muhurta-role-selection__prompt', role.prompt);
    const label = tbNode('label', 'muhurta-role-selection__field');
    const labelText = tbNode('span', 'muhurta-role-selection__label', role.label);
    const roleSelect = tbNode('select') as HTMLSelectElement;
    roleSelect.dataset.muhurtaRole = role.role;
    if (!participants.length) {
      tbAppendOption(roleSelect, '', 'Select or add a participant first');
      roleSelect.disabled = true;
    } else {
      for (const participant of participants) {
        tbAppendOption(roleSelect, participant.id, participant.name);
      }
      const requested = roleSelections.get(activity);
      const selected = participants.some(participant => participant.id === requested)
        ? requested as string
        : participants[0].id;
      roleSelections.set(activity, selected);
      if (roleSelectionState.selections[activity] !== selected) {
        persistRoleSelection(activity, selected);
      }
      roleSelect.value = selected;
      roleSelect.addEventListener('change', () => {
        invalidateMuhurtaSearch();
        roleSelections.set(activity, roleSelect.value);
        persistRoleSelection(activity, roleSelect.value);
      });
    }
    label.append(labelText, roleSelect);
    roleBlock.append(prompt, label);
    root.append(roleBlock);
  };

  const controller: InternalTarabalamProfilesController = {
    render(): void {
      snapshot = store.getSnapshot();
      root.replaceChildren();

      const intro = tbNode(
        'p',
        'muhurta-profile-intro',
        'Choose saved profiles, or add someone just for this search. Saved profiles stay only in this browser.',
      );
      const summary = tbNode('p', 'muhurta-profile-summary', selectionSummary());
      summary.dataset.muhurtaSelectionSummary = '';
      summary.setAttribute('aria-live', 'polite');
      root.append(intro, summary);
      renderNotices();
      renderSavedProfiles();
      renderManualProfiles();
      renderProfileActions();
      renderRoleSelection();
      root.dataset.selectedCount = String(participantCount());
    },
    destroy(): void {
      unsubscribe();
      legacyAddButton?.removeEventListener('click', onLegacyAdd);
      clearButton?.removeEventListener('click', onClear);
      activitySelect?.removeEventListener('change', onActivityChange);
      if (TB_PROFILE_CONTROLLER === controller) TB_PROFILE_CONTROLLER = null;
    },
    getParticipants(): JourneyGuestProfile[] {
      return currentParticipants();
    },
    getSelectedIds(): string[] {
      return [...selection.selectedIds];
    },
    getRoleParticipant(activity: string): JourneyGuestProfile | null {
      if (!roleForActivity(activity)) return null;
      const participants = currentParticipants();
      const selectedId = roleSelections.get(activity);
      return participants.find(participant => participant.id === selectedId)
        || participants[0]
        || null;
    },
    selectProfile(id: string): boolean {
      invalidateMuhurtaSearch();
      snapshot = store.getSnapshot();
      const profile = snapshot.profiles.find(candidate => candidate.id === id);
      if (!profile) {
        transientIssue = 'That saved profile is no longer available.';
        controller.render();
        return false;
      }
      if (!guestProfileReadiness(profile).muhurta) {
        transientIssue = 'Complete this profile with a birth star before using it for Muhurtam.';
        controller.render();
        return false;
      }
      if (selection.selectedIds.includes(id)) {
        transientIssue = null;
        controller.render();
        return true;
      }
      if (occupiedSlots() >= MAX_GUEST_PROFILES) {
        transientIssue = `Choose up to ${MAX_GUEST_PROFILES} participants for one Muhurtam search.`;
        controller.render();
        return false;
      }

      selection = toggleMuhurtamProfileSelection(
        selectionStorage,
        selection.selectedIds,
        id,
        true,
        snapshot.profiles,
      );
      const selected = selection.selectedIds.includes(id);
      transientIssue = selected
        ? null
        : selection.message || 'That profile could not be added to this Muhurtam search.';
      controller.render();
      if (selected) restoreProfileSelectionFocus(id);
      return selected;
    },
    addManualParticipant,
    removeManualParticipant(index: number): void {
      if (index < 0 || index >= manualParticipants.length) return;
      invalidateMuhurtaSearch();
      manualParticipants.splice(index, 1);
      transientIssue = null;
      controller.render();
    },
    clearParticipants,
  };

  const onActivityChange = (): void => {
    invalidateMuhurtaSearch();
    controller.render();
  };
  activitySelect?.addEventListener('change', onActivityChange);

  const unsubscribe = store.subscribe(nextSnapshot => {
    invalidateMuhurtaSearch();
    snapshot = nextSnapshot;
    selection = loadMuhurtamProfileSelection(selectionStorage, snapshot.profiles);
    const manualRoles = [...roleSelections.entries()].filter(([, id]) =>
      manualParticipants.some(participant => participant.id === id));
    roleSelectionState = loadMuhurtamRoleSelections(
      selectionStorage,
      snapshot.profiles,
    );
    roleSelections.clear();
    for (const entry of Object.entries(roleSelectionState.selections)) {
      roleSelections.set(...entry);
    }
    for (const [activity, id] of manualRoles) roleSelections.set(activity, id);
    const availableManualSlots = Math.max(0, MAX_GUEST_PROFILES - selection.selectedIds.length);
    if (manualParticipants.length > availableManualSlots) {
      manualParticipants = manualParticipants.slice(0, availableManualSlots);
      transientIssue = `Choose up to ${MAX_GUEST_PROFILES} participants for one Muhurtam search.`;
    }
    controller.render();
  });

  TB_PROFILE_CONTROLLER = controller;
  controller.render();
  return controller;
}

// Compatibility exports for the existing main.ts globals while the static
// inline form is retired. Normal startup delegates to the stable-ID
// controller; a narrowly scoped fallback keeps older bootstrap entry points
// functional without rewriting hidden or future-schema legacy rows.
function tbRenderProfileInputs(): void {
  if (TB_PROFILE_CONTROLLER) {
    TB_PROFILE_CONTROLLER.render();
    return;
  }

  const saved = readLegacyGuestProfileRows(localStorage);
  TB_LEGACY_ROWS = Math.max(
    TB_LEGACY_ROWS,
    Math.min(MAX_GUEST_PROFILES, saved.filter(value => value && (value.nak || value.name)).length || 1),
  );
  const root = document.getElementById('tb-profiles');
  if (!root) return;
  let html = '';
  for (let index = 0; index < TB_LEGACY_ROWS; index += 1) {
    const v = saved[index] || { name: '', nak: '', pada: '', lagna: '' };
    const nakshatraOptions = ['<option value="">birth star</option>']
      .concat(TB_NAKSHATRAS.map(value =>
        `<option value="${value}" ${value === v.nak ? 'selected' : ''}>${value}</option>`))
      .join('');
    const padaOptions = ['<option value="">padam?</option>']
      .concat([1, 2, 3, 4].map(value =>
        `<option value="${value}" ${String(value) === String(v.pada) ? 'selected' : ''}>${value}</option>`))
      .join('');
    const lagnaOptions = ['<option value="">lagna? (optional)</option>']
      .concat(TB_RASIS.map(value =>
        `<option value="${value}" ${value === v.lagna ? 'selected' : ''}>${value}</option>`))
      .join('');
    html += `<div class="tb-profile-row">
      <input type="text" id="tb-name-${index}" placeholder="${index === 0 ? 'Your name (optional)' : 'Name (optional)'}" value="${htmlEsc(v.name || '')}" onchange="tbSaveProfiles()">
      <select id="tb-nak-${index}" onchange="tbSaveProfiles(); tbRenderProfileInputs();">${nakshatraOptions}</select>
      <select id="tb-pada-${index}" title="Padam (quarter) of the birth star" onchange="tbSaveProfiles(); tbRenderProfileInputs();">${padaOptions}</select>
      <select id="tb-lagna-${index}" title="Janma Lagna (optional)" onchange="tbSaveProfiles();">${lagnaOptions}</select>
      ${index === 0 ? '' : `<button type="button" class="tb-remove" title="Remove" onclick="tbRemoveRow(${index})">Remove</button>`}
    </div>`;
  }
  root.innerHTML = html;
  const addButton = document.getElementById('tb-add-btn');
  if (addButton) addButton.style.display = TB_LEGACY_ROWS < MAX_GUEST_PROFILES ? '' : 'none';
}

function tbSaveProfiles(): boolean {
  if (TB_PROFILE_CONTROLLER) return true;

  if (tbHasBirthProfileStorage()) return false;

  const existing = readLegacyGuestProfileRows(localStorage);
  const fields = [];
  for (let index = 0; index < TB_LEGACY_ROWS; index += 1) {
    const previous = existing[index] || {};
    const lagnaInput = document.getElementById(`tb-lagna-${index}`) as HTMLSelectElement | null;
    const row = mergeLegacyGuestProfileRow(previous, {
      name: (document.getElementById(`tb-name-${index}`) as HTMLInputElement | null)?.value || '',
      nak: (document.getElementById(`tb-nak-${index}`) as HTMLSelectElement | null)?.value || '',
      pada: (document.getElementById(`tb-pada-${index}`) as HTMLSelectElement | null)?.value || '',
      lagna: lagnaInput?.value || '',
    });
    fields.push({
      name: row.name || '',
      nak: row.nak || '',
      pada: row.pada || '',
      lagna: row.lagna || '',
    });
  }
  writeLegacyGuestProfileRows(localStorage, fields);
  return true;
}

function tbHasBirthProfileStorage(): boolean {
  try {
    return localStorage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY) !== null
      || localStorage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY) !== null;
  } catch {
    return true;
  }
}

function tbResetProfiles(): void {
  if (TB_PROFILE_CONTROLLER) {
    TB_PROFILE_CONTROLLER.clearParticipants();
    return;
  }
  localStorage.removeItem(GUEST_BIRTH_PROFILE_STORAGE_KEY);
  localStorage.removeItem(GUEST_PROFILE_COMMIT_STORAGE_KEY);
  localStorage.removeItem(GUEST_PROFILE_STORAGE_KEY);
  TB_LEGACY_ROWS = 1;
  TB_DAYS = null;
  TB_EVENTS = null;
  MU_LAST = null;
  tbRenderProfileInputs();
  for (const id of ['tb-summary', 'tb-result', 'mu-context', 'mu-result']) {
    document.getElementById(id)?.replaceChildren();
  }
}

function tbAddRow(): void {
  if (TB_PROFILE_CONTROLLER) {
    TB_PROFILE_CONTROLLER.addManualParticipant();
    return;
  }
  if (!tbSaveProfiles()) return;
  TB_LEGACY_ROWS = Math.min(MAX_GUEST_PROFILES, TB_LEGACY_ROWS + 1);
  tbRenderProfileInputs();
}

function tbRemoveRow(index: number): void {
  if (TB_PROFILE_CONTROLLER) {
    TB_PROFILE_CONTROLLER.removeManualParticipant(index);
    return;
  }
  const saved = readLegacyGuestProfileRows(localStorage);
  if (index < 0 || index >= saved.length) return;
  if (tbHasBirthProfileStorage()) return;
  removeLegacyGuestProfileRow(localStorage, index);
  TB_LEGACY_ROWS = Math.max(1, TB_LEGACY_ROWS - 1);
  tbRenderProfileInputs();
}

async function calcTarabalam() {
  const profiles = tbProfiles();
  const resBox = document.getElementById('tb-result');
  if (!profiles.length) {
    resBox.innerHTML = '<p class="preview-error">Pick at least one birth star.</p>';
    return;
  }
  const from = new Date(inpEl('tb-from').value + 'T00:00:00');
  const to = new Date(inpEl('tb-to').value + 'T00:00:00');
  const span = Math.round((to.getTime() - from.getTime()) / 86400000) + 1;
  if (!(span >= 1 && span <= 60)) {
    resBox.innerHTML = '<p class="preview-error">Pick a range of 1 to 60 days.</p>';
    return;
  }
  resBox.innerHTML = '<p class="preview-error">Calculating…</p>';
  try {
    const city = getSelection().city;
    const system = getSelection().system;
    const events = getLoadedEvents() || await loadFeed(city, system);
    TB_EVENTS = events;
    TB_DAYS = [];
    for (let i = 0; i < span; i++) {
      const d = new Date(from); d.setDate(d.getDate() + i);
      const ev = events.get(stampOf(d));
      if (!ev) continue;
      const data = parseDescription(ev.description);
      const nak = data.nakshatra ? data.nakshatra.name : null;
      if (!nak) continue;
      const taras = profiles.map(pr => {
        const t = taraOf(pr.nak, nak);
        const entry: {
          who: string;
          tara: number;
          label: string;
          good: boolean;
          chandra?: ReturnType<typeof chandraOf>;
        } =
          { who: pr.name, tara: t, label: TARA_NAMES[t-1], good: TARA_GOOD.has(t) };
        if (pr.rasi && data.lunarSign) entry.chandra = chandraOf(pr.rasi, data.lunarSign);
        return entry;
      });
      TB_DAYS.push({ date: new Date(d), nak, nakUntil: data.nakshatra.end, nakEflag: data.nakshatra.eflag,
                     moonRasi: data.lunarSign || '', tithi: data.tithi ? data.tithi.name : '', taras });
    }
    renderTarabalam(profiles);
  } catch {
    // Feed details are intentionally withheld; the user gets a stable retry message.
    resBox.innerHTML = '<p class="preview-error">Could not load the feed. Try again.</p>';
  }
}

let TB_SHOW_ALL = false;  // default: only favourable days
let TB_MODE = (() => {
  try {
    return typeof window === 'undefined'
      ? 'stars'
      : window.localStorage?.getItem('tc-tb-mode') || 'stars';
  } catch {
    return 'stars';
  }
})();

function tbSetMode(m) {
  invalidateMuhurtaSearch();
  TB_MODE = m;
  try { window.localStorage?.setItem('tc-tb-mode', m); } catch { /* session only */ }
  if (TB_DAYS) renderTarabalam();
}

function tbPersonGood(t) {
  if (!t.good) return false;
  if (!t.chandra) return true;
  if (TB_MODE === 'strict') return t.chandra.verdict === 'good';
  if (TB_MODE === 'puja_ok') return t.chandra.verdict !== 'bad';
  return true;  // stars: chandra annotates, never blocks
}

export function tbChandraPresentation(t): { chandraTag: string; cls: string } {
  const passes = tbPersonGood(t);
  let caveat = t.chandra?.verdict || null;
  if (caveat === 'good') caveat = null;
  const ord = n => n + (['st','nd','rd'][n-1] || 'th');
  let chandraTag = '';
  if (caveat === 'puja') chandraTag = ` · ° ${ord(t.chandra.pos)}`;
  else if (caveat) chandraTag = ` · ☾ ${ord(t.chandra.pos)}`;
  let cls = 'good';
  if (!passes) cls = 'bad';
  else if (TB_MODE === 'puja_ok' && caveat === 'puja') cls = 'puja';
  return { chandraTag, cls };
}

function tbToggleShowAll() {
  TB_SHOW_ALL = inpEl('tb-show-all').checked;
  renderTarabalam();
}

function tbCycleHasGoodDay(profiles) {
  // Tarabalam repeats every 27 nakshatras. When rashis are also set the
  // real cycle is nakshatra x rashi, so only declare impossibility on the
  // star check alone — the look-ahead handles the rest.
  return TB_NAKSHATRAS.some(n =>
    profiles.every(pr => TARA_GOOD.has(taraOf(pr.nak, n))));
}

function tbDayGoodForAll(profiles, nak, moonRasi) {
  return profiles.every(pr => {
    if (!TARA_GOOD.has(taraOf(pr.nak, nak))) return false;
    if (TB_MODE !== 'stars' && pr.rasi && moonRasi) {
      const c = chandraOf(pr.rasi, moonRasi);
      if (c?.verdict === 'bad') return false;
      if (c?.verdict !== undefined && TB_MODE === 'strict' && c.verdict !== 'good') return false;
    }
    return true;
  });
}

function tbNextGoodBeyondRange(profiles) {
  if (!TB_EVENTS || !TB_DAYS.length) return null;
  const after = new Date(TB_DAYS[TB_DAYS.length - 1].date);
  for (let i = 1; i <= 365; i++) {
    const d = new Date(after); d.setDate(d.getDate() + i);
    const ev = TB_EVENTS.get(stampOf(d));
    if (!ev) return null;  // feed horizon reached
    const data = parseDescription(ev.description);
    const nak = data.nakshatra?.name;
    if (nak && tbDayGoodForAll(profiles, nak, data.lunarSign)) return d;
  }
  return null;
}

function tbExtendTo(iso) {
  inpEl('tb-to').value = iso;
  calcTarabalam();
}

function tbTarabalamProfileHeader(profile): string {
  const parts = [htmlEsc(profile.nak)];
  if (profile.rasi) parts.push(`${htmlEsc(profile.rasi)} rashi`);
  if (profile.lagna) parts.push(`${htmlEsc(profile.lagna)} lagna`);
  return `<th>${htmlEsc(profile.name)}<div class="tb-sub">${parts.join(' · ')}</div></th>`;
}

function tbTarabalamChip(tara, row): string {
  const { chandraTag, cls } = tbChandraPresentation(tara);
  let chandraDetail = '';
  if (tara.chandra) {
    const verdict = tara.chandra.verdict === 'puja'
      ? 'needs puja'
      : tara.chandra.verdict;
    chandraDetail = ` · Chandra: ${tara.chandra.pos}${['st','nd','rd'][tara.chandra.pos-1] || 'th'} from rashi (${verdict})`;
  }
  const moonDetail = row.moonRasi ? ` · Moon in ${row.moonRasi}` : '';
  const detail = `Tara: ${tara.tara} ${tara.label} (${tara.good ? 'good' : 'avoid'})`
    + chandraDetail + moonDetail;
  return `<td><span class="tara-chip ${cls}" title="${detail}">${tara.tara} ${tara.label}${chandraTag}</span></td>`;
}

function tbTarabalamDesktopRow(row, profiles): string {
  const dlabel = row.date.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });
  const chips = row.taras.map(tara => tbTarabalamChip(tara, row)).join('');
  let all = '';
  if (profiles.length > 1) {
    const allGood = row.allGood ? '<span class="tb-star">✦</span>' : '';
    all = `<td>${allGood}</td>`;
  }
  return `<tr class="${row.allGood && profiles.length > 1 ? 'tb-all' : ''}">
      <td class="tb-date-cell">${dlabel}</td>
      <td>${row.nak}<div class="tb-sub">till ${fmtT(row.nakUntil)}${row.nakEflag === '+1' ? ' +1' : ''}</div></td>
      <td>${row.tithi}</td>${chips}${all}</tr>`;
}

function tbTarabalamLegend(rows, group: boolean): string {
  const hasPuja = rows.some(row => row.taras.some(tara => tara.chandra?.verdict === 'puja'));
  const hasMoonBad = rows.some(row => row.taras.some(tara => tara.chandra?.verdict === 'bad'));
  const modeLabel = {
    stars: 'Stars only (classic)',
    puja_ok: 'Stars + Moon, puja ok',
    strict: 'Stars + Moon, strict',
  }[TB_MODE];
  let legend = `<div class="tb-readme"><div class="tb-readme-title">How to read this table</div>
    <div><span class="tara-chip good">green</span> a good day for that person, under your standard (<em>${modeLabel}</em>).</div>
    <div><span class="tara-chip bad">red</span> not suitable for that person.</div>`;
  if (TB_MODE === 'puja_ok' && hasPuja) {
    legend += `<div><span class="tara-chip puja">amber</span> good: a small remedial puja is advised (°).</div>`;
  } else if (hasPuja) {
    legend += `<div><strong>°</strong> a small remedial puja is advised for the Moon's position.</div>`;
  }
  if (hasMoonBad) {
    legend += `<div><strong>☾</strong> the Moon's position is unfavourable that day.</div>`;
  }
  if (group) {
    legend += `<div><span class="tb-star">✦</span> the day is favourable for <strong>everyone</strong>, under your standard.</div>`;
  }
  return `${legend}</div>`;
}

function tbTarabalamPersonCard(tara, profile): string {
  const { chandraTag, cls } = tbChandraPresentation(tara);
  let subText = '';
  if (profile) {
    const extras = [htmlEsc(profile.nak)];
    if (profile.rasi) extras.push(`${htmlEsc(profile.rasi)} rashi`);
    if (profile.lagna) extras.push(`${htmlEsc(profile.lagna)} lagna`);
    subText = `<span class="tb-sub">${htmlEsc(profile.name)}<span style="color:#DDD2BC"> · ${extras.join(' · ')}</span></span>`;
  }
  return `<div class="tb-card-row">${subText}<span class="tara-chip ${cls}">${tara.tara} ${tara.label}${chandraTag}</span></div>`;
}

function tbTarabalamMobileCard(row, profiles): string {
  const dlabel = row.date.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });
  const personRows = row.taras
    .map((tara, index) => tbTarabalamPersonCard(tara, profiles[index]))
    .join('');
  const goodForEveryone = row.allGood && profiles.length > 1;
  const star = goodForEveryone
    ? '<span class="tb-star">✦</span> good for everyone'
    : '&nbsp;';
  return `<div class="tb-card ${goodForEveryone ? 'tb-all' : ''}">
      <div class="tb-card-head">
        <span class="tb-date-cell">${dlabel}</span>
        <span class="tb-card-flag">${star}</span>
      </div>
      <div class="tb-card-sub">${row.nak} till ${fmtT(row.nakUntil)}${row.nakEflag === '+1' ? ' +1' : ''} · ${row.tithi}</div>
      ${personRows}
    </div>`;
}

function tbRenderNoFavourableRows(profiles, group: boolean, who: string): void {
  const result = document.getElementById('tb-result');
  if (!tbCycleHasGoodDay(profiles)) {
    result.innerHTML =
      `<p class="preview-error">This combination of birth stars never aligns; tarabalam repeats over the
         27 nakshatras, and no day is favourable for ${group ? 'all ' + profiles.length + ' people' : htmlEsc(who)} at once.
         Tick "show all days" to plan by individual taras, or consult your purohit.</p>`;
    return;
  }
  const nextGood = tbNextGoodBeyondRange(profiles);
  if (!nextGood) {
    result.innerHTML =
      `<p class="preview-error">No favourable days for ${htmlEsc(who)} in this range, and none found in the months ahead.
         Tick "show all days" to plan by individual taras.</p>`;
    return;
  }
  const iso = `${nextGood.getFullYear()}-${String(nextGood.getMonth()+1).padStart(2,'0')}-${String(nextGood.getDate()).padStart(2,'0')}`;
  const label = nextGood.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });
  result.innerHTML =
    `<p class="preview-error">No favourable days for ${htmlEsc(who)} in this range.
         The next one is <strong>${label}</strong>:
         <button class="read-more" style="color:var(--indigo);" onclick="tbExtendTo('${iso}')">extend the range to include it</button>,
         or tick "show all days".</p>`;
}

function tbRenderSummary(goodDays, profiles, group: boolean, who: string): void {
  const next = goodDays[0];
  let summary = `<span class="count">${goodDays.length} of ${TB_DAYS.length}</span>&nbsp;days are favourable for ${htmlEsc(who)}`;
  if (next) {
    summary += ` · next: <span class="count">${next.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>`;
  }
  const share = goodDays.length
    ? `<button class="wa-share-mini" style="position:static;width:28px;height:28px;flex:none;" title="Share these good days on WhatsApp" aria-label="Share on WhatsApp" onclick="shareTarabalamOnWhatsApp()"><svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg></button>`
    : '';
  const toggle = `<label class="tb-toggle"><input type="checkbox" id="tb-show-all" ${TB_SHOW_ALL ? 'checked' : ''} onchange="tbToggleShowAll()"> show all days</label>${share}`;
  document.getElementById('tb-summary').innerHTML =
    `<div class="tb-summary">${group ? '<span class="tb-star">✦</span>' : '🟢'} ${summary}${toggle}</div>`;
}

function renderTarabalam(profiles?) {
  if (!TB_DAYS) return;
  const participants = profiles || tbProfiles();
  const group = participants.length > 1;
  const who = group ? 'everyone' : participants[0]?.name || 'you';
  TB_DAYS.forEach(row => { row.allGood = row.taras.every(tbPersonGood); });
  selEl('tb-mode').value = TB_MODE;
  const goodDays = TB_DAYS.filter(row => row.allGood);
  tbRenderSummary(goodDays, participants, group, who);
  const rows = TB_DAYS.filter(row => TB_SHOW_ALL || row.allGood);
  if (!rows.length) {
    tbRenderNoFavourableRows(participants, group, who);
    return;
  }
  const head = `<tr><th>Date</th><th>Moon in</th><th>Tithi</th>${participants.map(tbTarabalamProfileHeader).join('')}${group ? '<th title="Auspicious for everyone selected">All ✦</th>' : ''}</tr>`;
  const body = rows.map(row => tbTarabalamDesktopRow(row, participants)).join('');
  const cards = rows.map(row => tbTarabalamMobileCard(row, participants)).join('');
  const legend = tbTarabalamLegend(rows, group);
  document.getElementById('tb-result').innerHTML =
    `<div class="tb-table-wrap"><table class="tb-table">${head}${body}</table></div>` +
    `<div class="tb-cards">${cards}</div>${legend}`;
}

function shareTarabalamOnWhatsApp() {
  if (!TB_DAYS) return;
  const profiles = tbProfiles();
  const group = profiles.length > 1;
  TB_DAYS.forEach(r => { r.allGood = r.taras.every(tbPersonGood); });
  selEl('tb-mode').value = TB_MODE;
  TB_DAYS.forEach(r => { r.allGood = r.taras.every(tbPersonGood); });
  const goodDays = TB_DAYS.filter(r => r.allGood);
  if (!goodDays.length) return;
  const citySel = selEl('tp-city');
  const cityLabel = citySel.options[citySel.selectedIndex].textContent;
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const lines = [];
  const anyRasi = profiles.some(pr => pr.rasi);
  lines.push(
    `✦ *Good days ${group ? 'for all of us' : 'for me'} (${anyRasi ? 'Tarabalam · Chandrabalam' : 'Tarabalam'})*`,
    `📍 ${cityLabel} · ${fmtD(TB_DAYS[0].date)} to ${fmtD(TB_DAYS[TB_DAYS.length-1].date)}`,
    'Saved profile names and birth-star details are intentionally omitted from this share.',
    `Standard: ${{ stars: 'Stars only (classic)', puja_ok: 'Stars + Moon, puja ok', strict: 'Stars + Moon, strict' }[TB_MODE]}`,
    '',
  );
  goodDays.forEach(r => lines.push(`✅ ${fmtD(r.date)} · ${r.nak} · ${r.tithi}`));
  lines.push(
    '',
    'Check your own birth star:',
    'https://panchangam.astrochaganti.com/?src=share-tarabalam#tarabalam',
  );
  gcEvent('share-tarabalam');
  window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
}

// --- Gochara tool ---


// --- Muhurta finder (client-side, from the already-loaded feed) ---

const MU_GOOD_CHOG = { Amrit: 3, Shubh: 2, Labh: 2, Char: 1 };
const MU_YOGA_BONUS = { 'Sarvartha Siddhi Yoga': 2, 'Amrita Siddhi Yoga': 2,
                        'Dvipushkara Yoga': 1, 'Tripushkara Yoga': 1 };
const MU_YOGA_PENALTY = { 'Visha Yoga': -2, 'Dagdha Yoga': -2 };

// MU_TIER_NAMES, muScoreTier, muRelativeTier — imported from
// src/muhurta-scorer.ts (see the import block at the top of this
// file).
// Tier each slot relative to the min/max score in this batch — mirror
// telugu_panchangam/personal/muhurta.assign_tiers. "Excellent" means
// the best of what turned up in this search, not a fixed bar.
function muAssignTiers(slots) {
  if (!slots.length) return;
  let ceiling = -Infinity, floor = Infinity;
  for (const s of slots) {
    if (s.score > ceiling) ceiling = s.score;
    if (s.score < floor) floor = s.score;
  }
  for (const s of slots) {
    let tier = muRelativeTier(s.score, ceiling, floor);
    if ((s.personalDosha || s.dayDosha) && tier === 'Excellent') tier = 'Good';
    s.tier = tier;
  }
}

// Nitya Yoga scoring — mirror telugu_panchangam/personal/nitya_yoga.py
const MU_NITYA_HARD_AVOID = new Set(['Vyatipata', 'Vaidhriti']);
const MU_NITYA_HARD_PENALTY = -2;
const MU_NITYA_PARTIAL_WINDOW_MIN = {  // dosha-window minutes from yoga start
  'Vishkambha': 3 * 24, 'Atiganda': 6 * 24, 'Shoola': 5 * 24,
  'Ganda': 6 * 24, 'Vyaghata': 9 * 24, 'Parigha': 5 * 24,
};
const MU_NITYA_PARTIAL_PENALTY = -1;
const MU_NITYA_AUSPICIOUS = new Set([
  'Preeti', 'Ayushman', 'Saubhagya', 'Shobhana',
  'Sukarma', 'Dhriti', 'Vriddhi', 'Dhruva',
  'Harshana', 'Siddhi', 'Shiva', 'Siddha',
  'Sadhya', 'Shubha', 'Shukla', 'Brahma', 'Indra',
]);
const MU_NITYA_AUSPICIOUS_BONUS = 1;

function muMin(t, flag?) {
  const [h, m] = t.split(':').map(Number);
  let offset = 0;
  if (flag === '+1') offset = 1440;
  else if (flag === '-1') offset = -1440;
  return h * 60 + m + offset;
}

export function muNatureBonus(isAbhijit: boolean, nature: string): number {
  if (isAbhijit) return 2;
  if (nature === 'auspicious') return 1;
  return -2;
}

export function muAvoidKaranaWindows(
  karana: string,
  avoidKaranaNames: Set<unknown>,
): number[][] {
  const windows: number[][] = [];
  const karanaWindowPattern = new RegExp(
    String.raw`^(.*?)\s+${TIME_PART}\s*[–-]\s*${TIME_PART}$`,
  );
  for (const rawKarana of karana.split('/')) {
    const match = karanaWindowPattern.exec(rawKarana.trim());
    if (match && avoidKaranaNames.has(match[1].trim())) {
      windows.push([muMin(match[2], match[3]), muMin(match[4], match[5])]);
    }
  }
  return windows;
}

/**
 * Validate the complete precomputed Drik Lagna day before treating its
 * transition map as screening evidence. A valid map visits all 12 signs in
 * zodiac order during its first civil-day cycle. Current generated artifacts
 * may contain a second-cycle tail, so that tail is validated but not mistaken
 * for a requirement that every file end after exactly one cycle.
 */
export function muValidLagnaDayData(lagnaDayData) {
  if (!lagnaDayData || typeof lagnaDayData !== 'object') return false;
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(lagnaDayData.sunrise || '')) return false;
  if (!Number.isInteger(lagnaDayData.lagna0)
      || lagnaDayData.lagna0 < 0 || lagnaDayData.lagna0 > 11) return false;
  if (!Number.isInteger(lagnaDayData.cycleEnd)
      || lagnaDayData.cycleEnd < 1430 || lagnaDayData.cycleEnd > 2890) return false;
  if (!Array.isArray(lagnaDayData.transitions)
      || lagnaDayData.transitions.length < 12
      || lagnaDayData.transitions.length > 25) return false;

  // The generator rounds transition offsets to minutes. A boundary that
  // lands within the first half-minute can therefore be represented as zero;
  // only the first transition may use that value.
  let previousOffset = -1;
  let previousRashi = lagnaDayData.lagna0;
  const visited = new Set([previousRashi]);
  for (const [index, transition] of lagnaDayData.transitions.entries()) {
    if (!Array.isArray(transition) || transition.length !== 2) return false;
    const [offset, rashi] = transition;
    // cycleEnd is exclusive. Older generated artifacts can independently
    // round a sub-minute final window's start and end to that exact minute,
    // leaving a zero-width terminal sentinel. It is boundary evidence, not an
    // interior interval; equality is valid only for the final sequential row.
    const terminalBoundary = index === lagnaDayData.transitions.length - 1
      && offset === lagnaDayData.cycleEnd;
    if (!Number.isInteger(offset) || offset <= previousOffset
        || offset > lagnaDayData.cycleEnd
        || (offset === lagnaDayData.cycleEnd && !terminalBoundary)) return false;
    if (!Number.isInteger(rashi) || rashi !== (previousRashi + 1) % 12) return false;
    previousOffset = offset;
    previousRashi = rashi;
    visited.add(rashi);
  }
  return visited.size === 12 && lagnaDayData.transitions[11][0] <= 1450;
}

/** Sample both sides of every verified precomputed Drik Lagna transition. */
export function muChartCheckMinutes(lagnaDayData, startMinute, endMinute) {
  const lastMinute = Math.max(startMinute, endMinute - 1);
  if (!muValidLagnaDayData(lagnaDayData)) {
    return [startMinute, lastMinute];
  }
  const [srH, srM] = lagnaDayData.sunrise.split(':').map(Number);
  const sunriseMinute = srH * 60 + srM;
  const minutes = [startMinute, lastMinute];
  // DashaFlow and the frozen Drik feed agree on Lagna signs in external
  // comparisons but can place the exact degree/boundary a few minutes apart.
  // A fixed cadence prevents boundary-edge sampling from depending solely on
  // one implementation's transition minute.
  for (let minute = startMinute + 10; minute < lastMinute; minute += 10) {
    minutes.push(minute);
  }
  for (const transition of lagnaDayData.transitions) {
    if (!Array.isArray(transition) || !Number.isFinite(transition[0])) continue;
    const transitionMinute = sunriseMinute + Math.round(transition[0]);
    for (const minute of [transitionMinute - 1, transitionMinute, transitionMinute + 1]) {
      if (minute >= startMinute && minute <= lastMinute) minutes.push(minute);
    }
  }
  return [...new Set(minutes)].sort((left, right) => left - right);
}

/** Resolve the application's validated Drik/Lahiri Lagna frame for each sample. */
export function muChartLagnasForMinutes(lagnaDayData, minutes) {
  if (!muValidLagnaDayData(lagnaDayData) || !Array.isArray(minutes)) return null;
  const lagnas = minutes.map(minute => muLagnaAtMin(lagnaDayData, minute));
  return lagnas.every(lagna => MU_RASHI_NAMES.includes(lagna)) ? lagnas : null;
}

/**
 * Drik Panchang and Swiss/Lahiri calculations can place the same Lagna
 * transition on different civil minutes even when their interior chart signs
 * agree. A window is safe for automated Whole Sign decisions only when it is
 * either outside the transition uncertainty band or contains the complete
 * band on both sides. Edge-adjacent windows remain visible, but their
 * Lagna-dependent checks are held for practitioner review.
 */
export function muChartBoundaryNeedsReview(
  lagnaDayData,
  startMinute,
  endMinute,
  guardMinutes = 5,
) {
  if (!muValidLagnaDayData(lagnaDayData)) return true;
  const lastMinute = Math.max(startMinute, endMinute - 1);
  if (!Number.isInteger(guardMinutes) || guardMinutes < 1) return true;
  const [srH, srM] = lagnaDayData.sunrise.split(':').map(Number);
  const sunriseMinute = srH * 60 + srM;
  return lagnaDayData.transitions.some(transition => {
    const transitionMinute = sunriseMinute + Math.round(transition[0]);
    const bandStart = transitionMinute - guardMinutes;
    const bandEnd = transitionMinute + guardMinutes;
    const touchesBand = startMinute <= bandEnd && lastMinute >= bandStart;
    if (!touchesBand) return false;
    return startMinute >= bandStart || lastMinute <= bandEnd;
  });
}

// ---------- Slot-time astronomy (Batch F2) ----------------------------
//
// Meeus low-precision Sun/Moon longitudes + Lahiri ayanamsa. Lets us
// recompute the panchangam anga (nakshatra, tithi, yoga, karana, moon
// rashi, special yogas) at any datetime — matching the Python engine's
// facts_at() so the in-page muhurta finder gets slot-time precision
// instead of just the sunrise snapshot from the feed.
//
// Accuracy: Sun ~0.01°, Moon ~0.1-0.3°. Nakshatra boundaries are
// 13.33° wide and tithi boundaries 12° wide, so this is comfortably
// sufficient for slot-time scoring.

const MU_NAKSHATRA_LIST = TB_NAKSHATRAS;     // already defined above

const MU_TITHI_LIST_FULL = (() => {
  const last = ['Pratipat','Dwitiya','Tritiya','Chaturthi','Panchami',
                'Shashthi','Saptami','Ashtami','Navami','Dashami',
                'Ekadashi','Dwadashi','Trayodashi','Chaturdashi','Pournami'];
  const shukla = last.slice(0, 14).map(n => `Shukla ${n}`).concat(['Pournami']);
  const krishna = last.slice(0, 14).map(n => `Krishna ${n}`).concat(['Amavasya']);
  return shukla.concat(krishna);
})();

const MU_YOGA_NAMES_27 = [
  'Vishkambha','Priti','Ayushman','Saubhagya','Shobhana','Atiganda',
  'Sukarma','Dhriti','Shula','Ganda','Vriddhi','Dhruva','Vyaghata',
  'Harshana','Vajra','Siddhi','Vyatipata','Variyana','Parigha','Shiva',
  'Siddha','Sadhya','Shubha','Shukla','Brahma','Indra','Vaidhriti',
];

const MU_KARANA_REPEATING = ['Bava','Balava','Kaulava','Taitila','Garaja','Vanija','Vishti'];
const MU_KARANA_FIXED = { 0: 'Kinstughna', 57: 'Shakuni', 58: 'Chatushpada', 59: 'Naga' };

// Special yogas — mirror telugu_panchangam/special_yogas.py
const MU_SARVARTHA = {
  Adivaram:    new Set(['Hasta','Mula','Pushya','Ashvini','Punarvasu','Anuradha','Shravana','Revati']),
  Somavaram:   new Set(['Shravana','Rohini','Mrigashira','Pushya','Anuradha']),
  Mangalavaram:new Set(['Ashvini','Krittika','Ashlesha','Uttara Ashadha','Uttara Phalguni','Uttara Bhadrapada']),
  Budhavaram:  new Set(['Krittika','Rohini','Hasta','Anuradha','Mrigashira']),
  Guruvaram:   new Set(['Ashvini','Punarvasu','Anuradha','Revati','Pushya','Swati']),
  Shukravaram: new Set(['Revati','Anuradha','Ashvini','Pushya','Shravana','Punarvasu']),
  Shanivaram:  new Set(['Swati','Rohini','Shravana']),
};
const MU_AMRITA_SIDDHI = {
  Adivaram:'Hasta', Somavaram:'Mrigashira', Mangalavaram:'Ashvini',
  Budhavaram:'Anuradha', Guruvaram:'Pushya', Shukravaram:'Revati', Shanivaram:'Rohini',
};
const MU_VISHA_TITHI = { Adivaram:5, Somavaram:6, Mangalavaram:7, Budhavaram:8,
                         Guruvaram:9, Shukravaram:10, Shanivaram:11 };
const MU_DAGDHA_TITHI = { Adivaram:new Set([12]), Somavaram:new Set([11]),
                          Mangalavaram:new Set([5]), Budhavaram:new Set([2,3]),
                          Guruvaram:new Set([6]), Shukravaram:new Set([8]), Shanivaram:new Set([9]) };
const MU_PUSHKARA_VARAS = new Set(['Adivaram','Mangalavaram','Shanivaram']);
const MU_DVI_TITHIS = new Set([2,7,12]);
const MU_DVI_NAKS   = new Set(['Mrigashira','Chitra','Dhanishtha']);
const MU_TRI_TITHIS = new Set([2,7,12]);
const MU_TRI_NAKS   = new Set(['Krittika','Punarvasu','Uttara Phalguni',
                                'Vishakha','Uttara Ashadha','Purva Bhadrapada']);

function muSpecialYogasAt(vaaram, tithiName, nakshatraName) {
  const yogas = [];
  if (MU_SARVARTHA[vaaram]?.has(nakshatraName))
    yogas.push('Sarvartha Siddhi Yoga');
  if (MU_AMRITA_SIDDHI[vaaram] === nakshatraName)
    yogas.push('Amrita Siddhi Yoga');
  const tithiBase = MU_TITHI_LIST_FULL.indexOf(tithiName) % 15 + 1;
  if (tithiBase === MU_VISHA_TITHI[vaaram]) yogas.push('Visha Yoga');
  if (MU_DAGDHA_TITHI[vaaram]?.has(tithiBase))
    yogas.push('Dagdha Yoga');
  if (MU_PUSHKARA_VARAS.has(vaaram)) {
    if (MU_DVI_TITHIS.has(tithiBase) && MU_DVI_NAKS.has(nakshatraName))
      yogas.push('Dvipushkara Yoga');
    if (MU_TRI_TITHIS.has(tithiBase) && MU_TRI_NAKS.has(nakshatraName))
      yogas.push('Tripushkara Yoga');
  }
  return yogas;
}

// Julian Day from a JS Date (UTC)
function muJD(dt) { return dt.getTime() / 86400000 + 2440587.5; }

// Lahiri ayanamsa (linear approximation; ~0.01° accuracy in the
// current era — good enough for nakshatra/tithi boundaries).
function muLahiri(jd) {
  return 23.85 + ((jd - 2451545.0) / 365.25) * 0.01397;
}

// Sun apparent longitude, sidereal (Lahiri). Meeus low-precision.
function muSunLong(jd) {
  const T = (jd - 2451545.0) / 36525;
  const L = ((280.460 + 36000.770 * T) % 360 + 360) % 360;
  const g = ((357.528 + 35999.050 * T) % 360 + 360) % 360;
  const gr = g * Math.PI / 180;
  const tropical = L + 1.915 * Math.sin(gr) + 0.020 * Math.sin(2 * gr);
  return ((tropical - muLahiri(jd)) % 360 + 360) % 360;
}

// Moon apparent longitude, sidereal (Lahiri). Meeus 12 leading terms.
function muMoonLong(jd) {
  const T = (jd - 2451545.0) / 36525;
  const d2r = Math.PI / 180;
  const Lp = ((218.3164477 + 481267.88123421 * T) % 360 + 360) % 360;
  const D  = ((297.8501921 + 445267.1114034 * T) % 360 + 360) % 360;
  const M  = ((357.5291092 + 35999.0502909 * T) % 360 + 360) % 360;
  const Mp = ((134.9633964 + 477198.8675055 * T) % 360 + 360) % 360;
  const F  = (( 93.2720950 + 483202.0175233 * T) % 360 + 360) % 360;
  const s  = a => Math.sin(a * d2r);
  const tropical = Lp
    + 6.288774 * s(Mp)
    + 1.274027 * s(2*D - Mp)
    + 0.658314 * s(2*D)
    + 0.213618 * s(2*Mp)
    - 0.185116 * s(M)
    - 0.114332 * s(2*F)
    + 0.058793 * s(2*D - 2*Mp)
    + 0.057066 * s(2*D - M - Mp)
    + 0.053322 * s(2*D + Mp)
    + 0.045758 * s(2*D - M)
    - 0.040923 * s(M - Mp)
    - 0.034720 * s(D);
  return ((tropical - muLahiri(jd)) % 360 + 360) % 360;
}

// factsAt(dt, vaaram) — slot-time anga, mirroring Python engine.facts_at.
function muFactsAt(dt, vaaram) {
  const jd = muJD(dt);
  const sun = muSunLong(jd);
  const moon = muMoonLong(jd);
  const elong = ((moon - sun) % 360 + 360) % 360;
  const nakSize = 360 / 27;
  const nakIdx = Math.floor(moon / nakSize) % 27;
  const nakshatra = MU_NAKSHATRA_LIST[nakIdx];
  const tithiIdx = Math.floor(elong / 12) % 30;
  const tithi = MU_TITHI_LIST_FULL[tithiIdx];
  const yogaIdx = Math.floor(((sun + moon) % 360) / nakSize) % 27;
  const yoga = MU_YOGA_NAMES_27[yogaIdx];
  const htIdx = Math.floor(elong / 6) % 60;
  const karana = MU_KARANA_FIXED[htIdx] !== undefined
    ? MU_KARANA_FIXED[htIdx]
    : MU_KARANA_REPEATING[(htIdx - 1 + 7) % 7];
  const rashiIdx = Math.floor(moon / 30) % 12;
  const lunarSign = TB_RASIS[rashiIdx];
  const specialYogas = muSpecialYogasAt(vaaram, tithi, nakshatra);
  const solarNakshatra = MU_NAKSHATRA_LIST[Math.floor(sun / nakSize) % 27];
  return { nakshatra, solarNakshatra, tithi, yoga, karana, lunarSign, vaaram, specialYogas };
}

const MU_HOMAHUTI_LORDS = [
  'Surya', 'Budha', 'Shukra', 'Shani', 'Chandra',
  'Mangala', 'Guru', 'Rahu', 'Ketu'];
const MU_HOMAHUTI_BENEFICS = new Set(['Budha', 'Shukra', 'Chandra', 'Guru']);
const MU_VAARAM_LIST = [
  'Adivaram', 'Somavaram', 'Mangalavaram', 'Budhavaram',
  'Guruvaram', 'Shukravaram', 'Shanivaram'];

function muHomaElection(facts) {
  const sunIdx = MU_NAKSHATRA_LIST.indexOf(facts.solarNakshatra);
  const moonIdx = MU_NAKSHATRA_LIST.indexOf(facts.nakshatra);
  const group = Math.floor(((moonIdx - sunIdx + 27) % 27) / 3);
  const lord = MU_HOMAHUTI_LORDS[group];
  const tithiOrdinal = MU_TITHI_LIST_FULL.indexOf(facts.tithi) + 1;
  const varaOrdinal = MU_VAARAM_LIST.indexOf(facts.vaaram) + 1;
  const remainder = (tithiOrdinal + 1 + varaOrdinal) % 4;
  return {
    admitted: MU_HOMAHUTI_BENEFICS.has(lord) && (remainder === 0 || remainder === 3),
    reasons: [
      `Homahuti group ${group + 1}: ${facts.solarNakshatra} to ${facts.nakshatra} falls to ${lord}`,
      `Agnivasa remainder ${remainder}: Agni resides on earth`],
  };
}

// MU_CHANDRA_GOOD/MU_CHANDRA_PUJA, MU_LAGNA_KENDRA/MU_LAGNA_TRIKONA,
// MU_RASHI_NAMES, muLagnaPosition, muLagnaVerdict, muIsFavourableLagna,
// muLagnaAtMin — all live in src/muhurta-scorer.ts (imported at the
// top of this file) so they can be unit-tested under Vitest.
// CHANDRA bad = {4, 8, 12} (the complement).

// Tithi family — mirror telugu_panchangam/personal/tithi_class.py
const TITHI_NAMES_ORDER = [
  'Pratipat', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
  'Shashthi', 'Saptami', 'Ashtami', 'Navami',    'Dashami',
  'Ekadashi', 'Dwadashi','Trayodashi','Chaturdashi','Pournami',
];
const TITHI_ALIASES = { Pratipada: 1, Prathama: 1, Shashti: 6, Amavasya: 15 };
function activityTithiNumber(name) {
  if (!name) return null;
  const last = name.trim().split(/\s+/).pop();
  if (TITHI_ALIASES[last]) return TITHI_ALIASES[last];
  const idx = TITHI_NAMES_ORDER.indexOf(last);
  return idx >= 0 ? idx + 1 : null;
}

// Activity rules — mirror telugu_panchangam/personal/muhurta.py
// ACTIVITY_RULES. Only the fields the JS scorer consumes are duplicated
// here (label, prefer_tithi_class, prefer_vara). skip_on_yoga and
// avoid_karana are still enforced by the engine; the JS reads
// parsed-feed yogas and karanas to mirror behaviour for activities the
// user picks via the in-page dropdown.
const MU_ACTIVITY = activityContract.rules;
let MU_SEARCH_SEQUENCE = 0;
let MU_CHART_ABORT = null;

function muSetResultMessage(box, message, role = 'status') {
  box.innerHTML = `<p class="preview-error">${htmlEsc(message)}</p>`;
  const announcement = document.getElementById('mu-result-announcement');
  if (announcement) {
    announcement.setAttribute('role', role);
    announcement.textContent = message;
  }
}

/** Invalidate both pending and completed Muhurtam results after any scoring input changes. */
export function invalidateMuhurtaSearch(announce = true) {
  const hadResult = !!MU_LAST || !!MU_CHART_ABORT;
  MU_SEARCH_SEQUENCE += 1;
  MU_CHART_ABORT?.abort();
  MU_CHART_ABORT = null;
  MU_LAST = null;
  const box = document.getElementById('mu-result');
  if (box) {
    box.setAttribute('aria-busy', 'false');
    if (announce && hadResult) {
      muSetResultMessage(box, 'Search inputs changed · find slots again.');
    }
  }
}

function muCurrentSearchFingerprint() {
  const selection = getSelection();
  const activity = selEl('mu-activity').value || 'any';
  const people = tbProfiles().map(person => ({
    id: person.id,
    name: person.name,
    nak: person.nak,
    rasi: person.rasi,
    lagna: person.lagna,
  }));
  const role = TB_PROFILE_CONTROLLER?.getRoleParticipant(activity) || null;
  return JSON.stringify({
    activity,
    from: inpEl('tb-from').value || '',
    to: inpEl('tb-to').value || '',
    city: selection.city,
    system: selection.system,
    chandraMode: TB_MODE,
    people,
    roleId: role?.id || null,
  });
}

function muConfiguredDaylightPolicy(activity, data, rules) {
  return activity === 'karnavedha'
    ? evaluateConfiguredKarnavedhaDaylight(
      data,
      rules.require_single_daylight_tithi,
      rules.require_single_daylight_nakshatra,
    )
    : null;
}

function muPrimaryDayDrop(
  data,
  rules,
  activityLabel: string,
  daylightPolicy,
  lagnaCityData,
  isoDate: string,
) {
  if (data.eclipse) {
    const kind = data.eclipse.kind || 'Eclipse';
    return {
      eclipse: true,
      entry: { date: isoDate, reason: `${kind} · auspicious activities deferred` },
    };
  }
  if (daylightPolicy && !daylightPolicy.admissible) {
    return {
      eclipse: false,
      entry: {
        date: isoDate,
        reason: karnavedhaDaylightDropReason(daylightPolicy),
        daylightOutcomes: daylightPolicy.outcomes,
      },
    };
  }
  if (rules.skip_on_sankramana && data.special.some(
      item => /Sankraman/i.test(item))) {
    return {
      eclipse: false,
      entry: {
        date: isoDate,
        reason: `Sankramana · ${activityLabel} source profile avoids this day`,
      },
    };
  }
  const combustionReason = muCombustionDropReason(
    lagnaCityData ? lagnaDayFor(lagnaCityData, isoDate) : null,
    rules.skip_on_combust || [], activityLabel,
  );
  return combustionReason
    ? { eclipse: false, entry: { date: isoDate, reason: combustionReason } }
    : null;
}

function muCalendarDayDrop(data, rules, activityLabel: string, isoDate: string) {
  const normalizedMaasam = (data.maasam || '').replace(/^(?:Nija|Adhika)\s+/, '');
  const maasaSolarAdmitted = (rules.allowed_maasa_solar_pairs || []).some(pair =>
    pair[0] === normalizedMaasam && pair[1] === data.solarSign);
  if ((rules.allowed_maasams?.length || rules.allowed_maasa_solar_pairs?.length) &&
      !rules.allowed_maasams?.includes(normalizedMaasam) && !maasaSolarAdmitted) {
    return { date: isoDate,
      reason: `${data.maasam} Maasa · ${activityLabel} source profile does not admit this lunar month` };
  }
  if (rules.allowed_varas?.length && !rules.allowed_varas.includes(data.vaaram)) {
    return { date: isoDate,
      reason: `${data.vaaram} · ${activityLabel} source profile does not admit this weekday` };
  }
  if (rules.allowed_pakshams?.length && !rules.allowed_pakshams.includes(data.paksham)) {
    return { date: isoDate,
      reason: `${data.paksham} Paksha · ${activityLabel} source profile does not admit this lunar fortnight` };
  }
  if ((rules.avoid_vara_paksha || []).some(pair =>
    pair[0] === data.vaaram && pair[1] === data.paksham)) {
    return { date: isoDate,
      reason: `${data.vaaram} during ${data.paksham} Paksha · ${activityLabel} source profile rejects this combination` };
  }
  return null;
}

function muSolarDayDrop(data, rules, activityLabel: string, isoDate: string) {
  const solarClass = data.solarSign ? muLagnaClassOf(data.solarSign) : null;
  if (rules.allowed_solar_classes?.length &&
      (!solarClass || !rules.allowed_solar_classes.includes(solarClass))) {
    return { date: isoDate,
      reason: `Surya in ${data.solarSign} (${solarClass}) · ${activityLabel} source profile does not admit this Rasi class` };
  }
  if (rules.allowed_solar_signs?.length &&
      !rules.allowed_solar_signs.includes(data.solarSign)) {
    return { date: isoDate,
      reason: `Surya in ${data.solarSign} · ${activityLabel} source profile does not admit this solar Rasi` };
  }
  return null;
}

function muDayDrop(
  data,
  rules,
  activityLabel: string,
  daylightPolicy,
  lagnaCityData,
  isoDate: string,
) {
  const primary = muPrimaryDayDrop(
    data, rules, activityLabel, daylightPolicy, lagnaCityData, isoDate,
  );
  if (primary) return primary;
  const entry = muCalendarDayDrop(data, rules, activityLabel, isoDate)
    || muSolarDayDrop(data, rules, activityLabel, isoDate);
  return entry ? { eclipse: false, entry } : null;
}

function muBadWindows(data, avoidKaranaNames) {
  const windows = data.inauspicious.map(
    window => [muMin(window.start, window.sflag), muMin(window.end, window.eflag)],
  );
  if (avoidKaranaNames.size && data.karana) {
    windows.push(...muAvoidKaranaWindows(data.karana, avoidKaranaNames));
  }
  return windows;
}

function muYogaDayDropReason(data, skipYogas, activityLabel: string): string | null {
  for (const yoga of data.yogas) {
    if (skipYogas.has(yoga)) {
      return `${yoga} · ${activityLabel} traditionally avoids this day`;
    }
  }
  if (skipYogas.size && data.yoga && MU_NITYA_HARD_AVOID.has(data.yoga.name)) {
    return `${data.yoga.name} yoga · samskaras traditionally defer`;
  }
  return null;
}

function muChandraModeDayDropReason(data, people, chandraMode): string | null {
  if (!people.length || chandraMode === 'stars' || !data.lunarSign) return null;
  let hasAvoid = false;
  let hasRemedial = false;
  for (const person of people) {
    if (!person.rasi) continue;
    const chandra = chandraOf(person.rasi, data.lunarSign);
    if (!chandra) continue;
    if (!MU_CHANDRA_GOOD.has(chandra.pos) && !MU_CHANDRA_PUJA.has(chandra.pos)) {
      hasAvoid = true;
    } else if (MU_CHANDRA_PUJA.has(chandra.pos)) {
      hasRemedial = true;
    }
  }
  if (chandraMode === 'strict' && (hasAvoid || hasRemedial)) {
    return 'chandra_mode=strict · Moon at sunrise fails for at least one person';
  }
  return chandraMode === 'puja_ok' && hasAvoid
    ? 'chandra_mode=puja_ok · someone has Moon-avoid (4/8/12)'
    : null;
}

function muNoSlotDayReason(data, skipYogas, activityLabel, people, chandraMode) {
  return muYogaDayDropReason(data, skipYogas, activityLabel)
    || muChandraModeDayDropReason(data, people, chandraMode);
}

function muRecordNoSlotDay(options): void {
  const {
    slotsPerDay, droppedDays, isoDate, data, skipYogas,
    activityLabel, people, chandraMode,
  } = options;
  if (slotsPerDay.has(isoDate)) return;
  const reason = muNoSlotDayReason(
    data, skipYogas, activityLabel, people, chandraMode,
  );
  if (reason) droppedDays.push({ date: isoDate, reason });
}

function muParticipantLabel(person, index: number): string {
  return `#${index + 1} (${person.name || person.nak})`;
}

export function muScoreParticipantTarabalam(people, nakshatra) {
  const favourable = [];
  const unfavourable = [];
  const unfavourableNames = [];
  let score = 0;
  people.forEach((person, index) => {
    const tara = taroOf_safe(person.nak, nakshatra);
    const label = muParticipantLabel(person, index);
    if (TARA_GOOD.has(tara)) {
      favourable.push(label);
      score += 1;
    } else {
      unfavourable.push(`${label} ${TARA_NAMES[tara - 1]}`);
      unfavourableNames.push(label);
      score -= 1;
    }
  });
  const reasons = [];
  if (favourable.length) {
    reasons.push(`Tarabalam favourable for ${favourable.join(', ')} (+${favourable.length})`);
  }
  if (unfavourable.length) {
    reasons.push(`Tarabalam avoid for ${unfavourable.join(', ')} (-${unfavourable.length})`);
  }
  return { score, reasons, unfavourableNames };
}

function muParticipantChandraResult(person, index: number, lunarSign) {
  if (!person.rasi) return null;
  const chandra = chandraOf(person.rasi, lunarSign);
  if (!chandra) return null;
  const label = muParticipantLabel(person, index);
  if (MU_CHANDRA_GOOD.has(chandra.pos)) return { kind: 'good', label, score: 1 };
  if (MU_CHANDRA_PUJA.has(chandra.pos)) {
    return { kind: 'puja', label, text: `${label} Moon@${chandra.pos}`, score: 0 };
  }
  const ashtama = chandra.pos === 8;
  return {
    kind: 'avoid', label, ashtama,
    text: `${label}${ashtama ? ' Ashtama' : ''} Moon@${chandra.pos}`,
    score: -1,
  };
}

export function muScoreParticipantChandrabalam(people, lunarSign, chandraMode) {
  const good = [];
  const puja = [];
  const avoid = [];
  const avoidNames = [];
  const pujaNames = [];
  let hasAshtama = false;
  let score = 0;
  people.forEach((person, index) => {
    const result = muParticipantChandraResult(person, index, lunarSign);
    if (!result) return;
    score += result.score;
    if (result.kind === 'good') good.push(result.label);
    if (result.kind === 'puja') {
      puja.push(result.text);
      pujaNames.push(result.label);
    }
    if (result.kind === 'avoid') {
      avoid.push(result.text);
      avoidNames.push(result.label);
      hasAshtama ||= result.ashtama;
    }
  });
  const reasons = [];
  if (good.length) reasons.push(`Chandrabalam favourable for ${good.join(', ')} (+${good.length})`);
  if (puja.length) reasons.push(`Chandrabalam remedial for ${puja.join(', ')} (puja recommended)`);
  if (avoid.length) reasons.push(`Chandrabalam avoid for ${avoid.join(', ')} (-${avoid.length})`);
  const drop = (
    chandraMode === 'strict' && (puja.length > 0 || avoid.length > 0)
  ) || (
    chandraMode === 'puja_ok' && avoid.length > 0
  );
  return { score, reasons, avoidNames, pujaNames, hasAshtama, drop };
}

function muLagnaReferenceOutcome(
  label: string,
  reference,
  slotLagna,
  suffix: string,
  includeNeutral: boolean,
) {
  if (!reference) return null;
  const position = muLagnaPosition(reference, slotLagna);
  if (position === 8) {
    return { kind: 'ashtama', label, score: -1, text: `${label} lagna@8 from ${reference}${suffix}` };
  }
  if (position && muIsFavourableLagna(position)) {
    return {
      kind: 'favourable', label, score: 1,
      text: `${label} ${muLagnaVerdict(position)}@${position} from ${reference}${suffix}`,
    };
  }
  return includeNeutral && position
    ? { kind: 'neutral', label, score: 0, text: `${label} ${muOrdinal(position)} from ${reference}${suffix}` }
    : null;
}

export function muScoreParticipantLagna(people, slotLagna) {
  const groups = {
    favourableRashi: [], favourableLagna: [],
    ashtamaRashi: [], ashtamaLagna: [],
    neutralRashi: [], neutralLagna: [],
  };
  const ashtamaNames = [];
  let score = 0;
  people.forEach((person, index) => {
    const label = muParticipantLabel(person, index);
    const outcomes: Array<[
      string,
      ReturnType<typeof muLagnaReferenceOutcome>,
    ]> = [
      ['Rashi', muLagnaReferenceOutcome(label, person.rasi, slotLagna, '', !!person.lagna)],
      ['Lagna', muLagnaReferenceOutcome(label, person.lagna, slotLagna, ' lagna', true)],
    ];
    for (const [source, outcome] of outcomes) {
      if (!outcome) continue;
      score += outcome.score;
      groups[`${outcome.kind}${source}`].push(outcome.text);
      if (outcome.kind === 'ashtama' && !ashtamaNames.includes(label)) {
        ashtamaNames.push(label);
      }
    }
  });
  const reasons = [];
  for (const [key, label] of [
    ['favourableRashi', 'favourable'], ['favourableLagna', 'favourable'],
    ['ashtamaRashi', 'Ashtama'], ['ashtamaLagna', 'Ashtama'],
    ['neutralRashi', 'neutral'], ['neutralLagna', 'neutral'],
  ]) {
    const entries = groups[key];
    if (!entries.length) continue;
    let suffix = ` (+${entries.length})`;
    if (key.startsWith('ashtama')) suffix = ` (-${entries.length})`;
    if (key.startsWith('neutral')) suffix = ' (no effect)';
    reasons.push(`${slotLagna} lagna ${label} for ${entries.join(', ')}${suffix}`);
  }
  return { score, reasons, ashtamaNames };
}

export function muScoreActivityLagna(
  slotLagna,
  requiredLagnaClass,
  allowedLagnas,
  preferLagnas,
  preferLagnaClass,
  lagnaCityData,
  activityLabel: string,
) {
  const reasons = [];
  let score = 0;
  if (requiredLagnaClass) {
    const required = muLagnasInClass(requiredLagnaClass);
    if (!slotLagna || !required?.has(slotLagna)) return null;
    reasons.push(`${slotLagna} lagna satisfies required ${requiredLagnaClass} class`);
  }
  if (allowedLagnas.size) {
    if (!slotLagna || !allowedLagnas.has(slotLagna)) return null;
    reasons.push(`${slotLagna} lagna is admitted for ${activityLabel}`);
  }
  if (slotLagna && preferLagnas.has(slotLagna)) {
    score += 1;
    reasons.push(`${slotLagna} lagna specifically favoured for ${activityLabel} (+1)`);
  }
  if (preferLagnaClass && lagnaCityData) {
    const favoured = muLagnasInClass(preferLagnaClass);
    if (slotLagna && favoured?.has(slotLagna)) {
      score += 1;
      reasons.push(`${slotLagna} lagna (${preferLagnaClass}) favoured for ${activityLabel} (+1)`);
    }
  }
  return { score, reasons };
}

function muScoreSlotTithi(
  facts,
  preferTithiClass,
  activityLabel: string,
  avoidTithiClasses,
  preferTithiNumbers,
) {
  const result = muScoreTithiClass(
    facts.tithi, preferTithiClass, activityLabel, facts.nakshatra,
    facts.specialYogas, avoidTithiClasses,
  );
  const dayReasons = result.dayReason ? [result.dayReason] : [];
  const activityReasons = result.activityReason ? [result.activityReason] : [];
  let score = result.bonus;
  const tithiNumber = activityTithiNumber(facts.tithi);
  if (tithiNumber && preferTithiNumbers.has(tithiNumber)) {
    score += 1;
    activityReasons.push(`${facts.tithi} specifically favoured for ${activityLabel} (+1)`);
  }
  return { score, family: result.family, dayReasons, activityReasons };
}

function muScoreSpecialYogas(facts, skipYogas) {
  let score = 0;
  const reasons = [];
  for (const yoga of facts.specialYogas) {
    if (MU_YOGA_BONUS[yoga]) {
      score += MU_YOGA_BONUS[yoga];
      reasons.push(`${yoga} day (+${MU_YOGA_BONUS[yoga]})`);
    }
    if (MU_YOGA_PENALTY[yoga] === undefined) continue;
    if (skipYogas.has(yoga)) return null;
    score += MU_YOGA_PENALTY[yoga];
    reasons.push(`${yoga} day (${MU_YOGA_PENALTY[yoga]})`);
  }
  return { score, reasons };
}

function muScoreNityaYoga(facts, data, skipYogas, avoidNityaYogas, startMinute: number) {
  const yoga = facts.yoga;
  if (avoidNityaYogas.has(yoga)) return null;
  if (MU_NITYA_HARD_AVOID.has(yoga)) {
    if (skipYogas.size) return null;
    return { score: MU_NITYA_HARD_PENALTY, reason: `${yoga} yoga (${MU_NITYA_HARD_PENALTY})` };
  }
  if (MU_NITYA_PARTIAL_WINDOW_MIN[yoga] !== undefined && data.yoga) {
    const windowMin = MU_NITYA_PARTIAL_WINDOW_MIN[yoga];
    const yogaStartMin = yoga === data.yoga.name
      ? muMin(data.yoga.start, data.yoga.sflag)
      : muMin(data.yoga.end, data.yoga.eflag);
    return startMinute - yogaStartMin <= windowMin
      ? { score: MU_NITYA_PARTIAL_PENALTY, reason: `${yoga} yoga dosha-window (${MU_NITYA_PARTIAL_PENALTY})` }
      : { score: 0, reason: null };
  }
  return MU_NITYA_AUSPICIOUS.has(yoga)
    ? { score: MU_NITYA_AUSPICIOUS_BONUS, reason: `${yoga} yoga (+${MU_NITYA_AUSPICIOUS_BONUS})` }
    : { score: 0, reason: null };
}

function muScoreSlotPreferences(options) {
  const {
    facts, varaReason, preferNakshatras, amrita, s0, e0,
    preferChog, choghadiya, avoidKaranaNames, activityLabel,
  } = options;
  const slotReasons = [];
  const activityReasons = [];
  let score = 0;
  if (varaReason) {
    score += 1;
    activityReasons.push(varaReason);
  }
  if (preferNakshatras.has(facts.nakshatra)) {
    score += 1;
    activityReasons.push(`${facts.nakshatra} specifically favoured for ${activityLabel} (+1)`);
  }
  if (amrita.some(window =>
    s0 < muMin(window.end, window.eflag)
    && muMin(window.start, window.sflag) < e0)) {
    score += 2;
    slotReasons.push('overlaps Amrita Kalam (+2)');
  }
  if (preferChog?.[0] === choghadiya.name) {
    score += preferChog[1];
    activityReasons.push(`${choghadiya.name} favoured for ${activityLabel} (+${preferChog[1]})`);
  }
  for (const karana of avoidKaranaNames) {
    activityReasons.push(`${karana} karana avoided`);
  }
  return { score, slotReasons, activityReasons };
}

function muSlotDoctrinalNotes(options): { notes: string[]; siddhiYogas: string[] } {
  const {
    cautionLagnaSolar, lagnaCityData, slotLagna, solarSign,
    specialYogas, taraUnfavNames, chandraAvoidNames, tithiFamily,
  } = options;
  const notes = [];
  if (cautionLagnaSolar && lagnaCityData && slotLagna === solarSign) {
    notes.push(`Source caution · ${slotLagna} Lagna is occupied by Surya; ` +
      'Raman associates this with delay from hard rock.');
  }
  const siddhiYogas = specialYogas.filter(yoga =>
    yoga === 'Sarvartha Siddhi Yoga' || yoga === 'Amrita Siddhi Yoga');
  const hasPushkara = specialYogas.some(yoga =>
    yoga === 'Dvipushkara Yoga' || yoga === 'Tripushkara Yoga');
  if (siddhiYogas.length && taraUnfavNames.length) {
    notes.push(`${siddhiYogas.join(' + ')} traditionally rectifies tara dosha ` +
      `(Muhurta Chintamani) · ${taraUnfavNames.join(', ')} mitigated.`);
  }
  if (siddhiYogas.length && chandraAvoidNames.length) {
    notes.push('Chandra dosha is not rectified by Siddhi yogas · ' +
      `${chandraAvoidNames.join(', ')} remains a personal caution.`);
  }
  if (hasPushkara && tithiFamily === 'Rikta') {
    notes.push(`Pushkara amplifies the day's nature; combined with Rikta tithi, ` +
      'even small inauspicious factors magnify.');
  }
  return { notes, siddhiYogas };
}

function muPersonalDosha(options): string | null {
  const {
    chandraAvoidNames, hasAshtama, ashtamaLagnaNames,
    chandraPujaNames, taraUnfavNames, siddhiYogas,
  } = options;
  if (chandraAvoidNames.length) {
    return hasAshtama ? 'ashtama_chandra' : 'chandra_avoid';
  }
  if (ashtamaLagnaNames.length) return 'ashtama_lagna';
  if (chandraPujaNames.length) return 'chandra_remedial';
  return taraUnfavNames.length && !siddhiYogas.length ? 'tara_dosha' : null;
}

function muSlotDayDosha(options) {
  const {
    tithiFamily, facts, nityaYoga, system, effectiveChartRemainder,
    rules, manualGuidance, personal,
  } = options;
  const computed = computeDayDosha({
    tithiFamily,
    isAmavasya: /Amavasya/i.test(facts.tithi),
    hasYogaPenalty: facts.specialYogas.some(
      yoga => MU_YOGA_PENALTY[yoga] !== undefined),
    nityaHardAvoid: MU_NITYA_HARD_AVOID.has(nityaYoga),
  });
  const unresolvedSourcePrerequisite = (
    system === 'drik' && effectiveChartRemainder !== null
      ? effectiveChartRemainder.length > 0
      : !!rules.manual_prerequisites || manualGuidance.chart.length > 0
  );
  return computed || (unresolvedSourcePrerequisite || personal.needsReview
    ? 'practitioner_review'
    : null);
}

function muDominantChoghadiya(choghadiya, startMinute: number, endMinute: number) {
  let best = null;
  let bestOverlap = 0;
  const touched = [];
  for (const block of choghadiya) {
    const blockStart = muMin(block.start);
    const blockEnd = muMin(block.end);
    const overlap = Math.min(endMinute, blockEnd) - Math.max(startMinute, blockStart);
    if (overlap <= 0) continue;
    touched.push(block.name);
    if (overlap > bestOverlap) {
      best = block;
      bestOverlap = overlap;
    }
  }
  return {
    block: best,
    straddle: best ? touched.find(name => name !== best.name) || null : null,
  };
}

function muSlotTimeFoundation(options) {
  const {
    mi, srMin, ssMin, muLen, rules, bad, data, abhijit,
    chartLocation, isoDate, date, lagnaCityData, system, activity,
  } = options;
  const s0 = Math.round(srMin + mi * muLen);
  const e0 = Math.round(srMin + (mi + 1) * muLen);
  if (rules.forenoon_only && !muEndsBySolarNoon(e0, srMin, ssMin)) return null;
  if (bad.some(([start, end]) => s0 < end && start < e0)) return null;
  const dominant = muDominantChoghadiya(data.choghadiya, s0, e0);
  if (!dominant.block) return null;
  const slotStart = chartLocation
    ? new Date(localWallTimeToInstant(isoDate, s0, chartLocation.timezone))
    : new Date(date.getTime() + s0 * 60000);
  const facts = muFactsAt(slotStart, data.vaaram);
  const lagnaDay = lagnaCityData ? lagnaDayFor(lagnaCityData, isoDate) : null;
  return {
    s0,
    e0,
    dominant,
    choghadiya: dominant.block,
    base: MU_GOOD_CHOG[dominant.block.name] || 0,
    muRow: MUHURTA_DAY[mi],
    isAbhijit: mi === 7 && !!abhijit,
    facts,
    lagnaDay,
    slotLagna: lagnaDay ? muLagnaAtMin(lagnaDay, s0) : null,
    personal: {
      rejected: false,
      needsReview: system !== 'drik' && !!roleForActivity(activity),
      preferencePasses: 0,
      evidence: system !== 'drik' && roleForActivity(activity)
        ? ['Source-specific personal screening is currently limited to Drik/Lahiri.']
        : [],
      outcomes: [],
      stable: true,
    },
  };
}

function muSlotElectionReasons(facts, rules, restrictions, data, people) {
  let reasons = [];
  if (rules.require_homa_election) {
    const election = muHomaElection(facts);
    if (!election.admitted) return null;
    reasons = election.reasons;
  }
  if (restrictions.allowedNakshatras.size &&
      !restrictions.allowedNakshatras.has(facts.nakshatra)) return null;
  if (restrictions.avoidNakshatras.has(facts.nakshatra)) return null;
  if (restrictions.avoidJanmaNakshatra && people.some(
    person => muCanonicalNakshatra(person.nak) === facts.nakshatra)) return null;
  const tithiNumber = activityTithiNumber(facts.tithi);
  if (restrictions.allowedTithiNumbers.size &&
      !restrictions.allowedTithiNumbers.has(tithiNumber)) return null;
  if (restrictions.allowedTithiNames.size &&
      !restrictions.allowedTithiNames.has(facts.tithi)) return null;
  if (restrictions.avoidTithiNumbers.has(tithiNumber)) return null;
  return restrictions.avoidVaraTithiNames.has(`${data.vaaram}|${facts.tithi}`)
    ? null
    : reasons;
}

function muInitialSlotScore(foundation, electionReasons) {
  const { base, muRow, isAbhijit, dominant, choghadiya } = foundation;
  const natureBonus = muNatureBonus(isAbhijit, muRow[2]);
  const muLabel = muRow[0] + (isAbhijit ? ' (Abhijit)' : '');
  const muDeity = muRow[1] ? ` · ${muRow[1]}` : '';
  const straddleDescription = dominant.straddle
    ? ` (spans ${dominant.straddle})`
    : '';
  const chogDescription = `${choghadiya.name} choghadiya${straddleDescription}`;
  const chogLine = base ? `${chogDescription} (+${base})` : chogDescription;
  return {
    score: base + natureBonus,
    slotQuality: [
      `${muLabel} muhurta${muDeity} · ${muRow[2]} (${natureBonus >= 0 ? '+' : ''}${natureBonus})`,
      chogLine,
    ],
    dayQuality: [],
    groupFit: [],
    activityMatch: [...electionReasons],
  };
}

function muActivityNeedsLagna(activity: string, rules): boolean {
  return Boolean(
    rules.prefer_lagna_class
    || rules.required_lagna_class
    || rules.allowed_lagnas?.length
    || rules.skip_on_combust?.length
    || automatedRulesFor(activity).length
  );
}

function muRankCandidateSlots(slots): void {
  muAssignTiers(slots);
  slots.sort((a, b) => MU_TIER_NAMES.indexOf(b.tier) - MU_TIER_NAMES.indexOf(a.tier)
    || b.score - a.score
    || (b.personalPreferencePasses || 0) - (a.personalPreferencePasses || 0)
    || (Number(!!a.personalDosha) - Number(!!b.personalDosha))
    || a.d - b.d
    || a.s0 - b.s0);
}

function muSearchIsStale(searchSequence: number, fingerprint: string, box): boolean {
  if (searchSequence !== MU_SEARCH_SEQUENCE) return true;
  if (fingerprint === muCurrentSearchFingerprint()) return false;
  box.setAttribute('aria-busy', 'false');
  muSetResultMessage(box, 'Search inputs changed · find slots again.');
  return true;
}

function muSetShortlistProgress(box, slots): void {
  if (!slots.length) return;
  if (electionChartCalculationEnabled()) {
    muSetResultMessage(box, 'Shortlist ready · screening exact election charts…');
    return;
  }
  muSetResultMessage(
    box,
    'Shortlist ready · exact chart screening is not active in this build.',
  );
}

function muUnavailableChartEnrichment(slots) {
  return {
    state: 'unavailable',
    slots: slots.slice(0, 10).map(slot => ({
      ...slot,
      tier: slot.tier === 'Excellent' ? 'Good' : slot.tier,
      dayDosha: slot.dayDosha || 'practitioner_review',
    })),
    screenedCount: 0,
    removedCount: 0,
    candidateLimitReached: false,
    chartRemovedCount: 0,
    chartRemovedRules: [],
    personalRemovedCount: 0,
    personalRemovedRules: [],
    boundaryReviewCount: 0,
    qualificationCappedCount: 0,
    reviewGatedCount: slots.length,
    overlappingDispositionCount: 0,
    message: 'Panchangam-ranked; exact chart screening is unavailable for this city.',
    engine: null,
  };
}

async function muEnrichCandidateSlots(options) {
  const {
    slots, activity, system, city, roleProfile,
    lagnaCityData, signal,
  } = options;
  const location = CITY_LOCATIONS[city];
  if (!location) return muUnavailableChartEnrichment(slots);
  return enrichElectionChartSlots(slots, {
    activity,
    system,
    location,
    personalParticipant: roleProfile ? {
      id: roleProfile.id,
      name: roleProfile.name,
      nakshatra: roleProfile.nak || null,
      janmaRashi: roleProfile.rasi || null,
      janmaLagna: roleProfile.lagna || null,
    } : null,
    boundarySupportAvailable: !!lagnaCityData
      && slots.every(slot => slot.chartBoundarySupported === true),
    signal,
  });
}

async function findMuhurta() {
  const searchSequence = ++MU_SEARCH_SEQUENCE;
  MU_CHART_ABORT?.abort();
  const chartAbort = new AbortController();
  MU_CHART_ABORT = chartAbort;
  const box = document.getElementById('mu-result');
  box.setAttribute('aria-busy', 'true');
  muSetResultMessage(box, 'Searching…');
  const activity = selEl('mu-activity').value;
  const from = new Date(inpEl('tb-from').value + 'T00:00:00');
  const to = new Date(inpEl('tb-to').value + 'T00:00:00');
  const nDays = Math.min(60, Math.max(1, Math.round((to.getTime() - from.getTime()) / 86400000) + 1));
  const people = tbProfiles();
  const roleProfile = TB_PROFILE_CONTROLLER?.getRoleParticipant(activity) || null;
  const searchFingerprint = muCurrentSearchFingerprint();
  const chandraMode = TB_MODE;  // 'stars' | 'puja_ok' | 'strict' — filters only, never scores
  document.getElementById('mu-context').innerHTML = people.length
    ? `Searching <strong>${inpEl('tb-from').value}</strong> to <strong>${inpEl('tb-to').value}</strong>, screened by the stars of <strong>${people.map(p => htmlEsc(p.name)).join(', ')}</strong> (set above).`
    : `Searching <strong>${inpEl('tb-from').value}</strong> to <strong>${inpEl('tb-to').value}</strong> · no people set above, so no star screening.`;
  try {
    const city = getSelection().city;
    const system = getSelection().system;
    const chartLocation = CITY_LOCATIONS[city] || null;
    const citySelect = selEl('tp-city');
    const searchContext = {
      city,
      cityLabel: citySelect.options[citySelect.selectedIndex]?.textContent || city,
      system,
      fromIso: inpEl('tb-from').value,
      toIso: inpEl('tb-to').value,
      fingerprint: searchFingerprint,
    };
    const events = getLoadedEvents() || await loadFeed(city, system);
    // Lagna data is needed when (a) people are set — for the
    // per-person kendra/trikona/Ashtama check — OR (b) the chosen
    // activity has a preferred lagna class (Sthira/Chara/...).
    // Cached per session, shared with the day-card's lagna ribbon.
    const activityRules = MU_ACTIVITY[activity] || MU_ACTIVITY.any;
    const activityNeedsLagna = muActivityNeedsLagna(activity, activityRules);
    const lagnaCityData = (people.length || activityNeedsLagna)
      ? await loadLagna(city) : null;
    const slots = [];
    let droppedEclipseDays = 0;
    let droppedModeDays = 0;
    let droppedModeSlots = 0;
    const droppedDays = [];
    const slotsPerDay = new Map();   // YYYY-MM-DD → count
    const processDay = (d, ev): void => {
      const data = parseDescription(ev.description);
      const isoDate = stampOf(d).replace(/^(\d{4})(\d{2})(\d{2})$/, '$1-$2-$3');

      const rules = MU_ACTIVITY[activity] || MU_ACTIVITY.any;
      const skipYogas = new Set(rules.skip_on_yoga || []);
      const preferChog = rules.prefer_choghadiya || null;     // ['Block', bonus]
      const avoidKaranaNames = new Set(rules.avoid_karana || []);
      const preferTithiClass = rules.prefer_tithi_class || null;
      const avoidTithiClasses = rules.avoid_tithi_class || [];
      const preferVaras = new Set(rules.prefer_vara || []);
      const preferLagnaClass = rules.prefer_lagna_class || null;
      const requiredLagnaClass = rules.required_lagna_class || null;
      const allowedLagnas = new Set(rules.allowed_lagnas || []);
      const preferLagnas = new Set(rules.prefer_lagnas || []);
      const cautionLagnaSolar = !!rules.caution_lagna_solar;
      const allowedNakshatras = new Set(
        (rules.allowed_nakshatras || []).map(muCanonicalNakshatra));
      const avoidNakshatras = new Set(
        (rules.avoid_nakshatras || []).map(muCanonicalNakshatra));
      const avoidJanmaNakshatra = !!rules.avoid_janma_nakshatra;
      const preferNakshatras = new Set(
        (rules.prefer_nakshatras || []).map(muCanonicalNakshatra));
      const allowedTithiNumbers = new Set(rules.allowed_tithi_numbers || []);
      const preferTithiNumbers = new Set(rules.prefer_tithi_numbers || []);
      const allowedTithiNames = new Set(rules.allowed_tithi_names || []);
      const avoidTithiNumbers = new Set(rules.avoid_tithi_numbers || []);
      const avoidVaraTithiNames = new Set(
        (rules.avoid_vara_tithi_names || []).map(pair => `${pair[0]}|${pair[1]}`));
      const avoidNityaYogas = new Set(rules.avoid_nitya_yogas || []);
      const manualChecks = muRelevantManualChecks(activity, data.vaaram);
      const manualGuidance = muClassifyManualChecks(activity, manualChecks);
      const chartManualRemainder = chartManualRemaindersFor(activity);
      const effectiveChartRemainder = (
        chartManualRemainder !== null
        && !chartAssessorCompleteFor(activity)
        && chartManualRemainder.length === 0
        && automatedRulesFor(activity).length > 0
      )
        ? [MU_PARTIAL_ASSESSOR_DISCLOSURE]
        : chartManualRemainder;
      const activityLabel = rules.label;
      const daylightPolicy = muConfiguredDaylightPolicy(activity, data, rules);
      const dayDrop = muDayDrop(
        data, rules, activityLabel, daylightPolicy, lagnaCityData, isoDate,
      );
      if (dayDrop) {
        if (dayDrop.eclipse) droppedEclipseDays++;
        droppedDays.push(dayDrop.entry);
        return;
      }

      // Vara is sunrise-anchored — compute once per day.
      const varaBonus = (data.vaaram && preferVaras.has(data.vaaram)) ? 1 : 0;
      const varaReason = varaBonus
        ? `${data.vaaram} favoured for ${activityLabel} (+1)` : null;

      const bad = muBadWindows(data, avoidKaranaNames);
      const abhijit = data.auspicious.find(w => w.name === 'Abhijit Muhurta');
      const amrita = data.auspicious.filter(w => w.name === 'Amrita Kalam');

      // Day-context strip shown on every slot card for this day: the
      // sunrise-anchored anga (matches the Panchangam tab), a visible teaser
      // of the timings people cross-check most (Sunrise, Abhijit, Rahu
      // Kalam), and the full Panchangam auspicious/avoid window lists behind
      // an expand. Display only; computed once per day, shared by its slots.
      const fmtRange = (w) => `${muToT(muMin(w.start, w.sflag))} to ${muToT(muMin(w.end, w.eflag))}`;
      // Group by window name so multi-segment windows (e.g. two Durmuhurtham
      // spells) read as one entry with both ranges.
      const groupWins = (arr) => {
        const m = new Map();
        for (const w of arr) {
          if (!m.has(w.name)) m.set(w.name, []);
          m.get(w.name).push(fmtRange(w));
        }
        return [...m.entries()].map(([name, ranges]) => ({ name, ranges }));
      };
      const rahuWin = data.inauspicious.find(w => /Rahu/i.test(w.name));
      const dayCtx = {
        tithi: data.tithi?.name || null,
        nakshatra: data.nakshatra?.name || null,
        yoga: data.yoga?.name || null,
        sunrise: data.sunrise ? muToT(muMin(data.sunrise)) : null,
        abhijit: abhijit ? fmtRange(abhijit) : null,
        rahu: rahuWin ? fmtRange(rahuWin) : null,
        auspicious: groupWins(data.auspicious),
        avoid: groupWins(data.inauspicious),
      };

      const srMin = muMin(data.sunrise);
      const ssMin = muMin(data.sunset);
      const muLen = (ssMin - srMin) / 15;
      // Iterate the 15 named daytime muhurtas (sunrise->sunset /15). Mirrors
      // Python day_slots: exclude a muhurta overlapping any inauspicious
      // window, else score it by nature + dominant choghadiya + all factors.
      const processSlot = (mi: number): void => {
          const foundation = muSlotTimeFoundation({
            mi, srMin, ssMin, muLen, rules, bad, data, abhijit,
            chartLocation, isoDate, date: d, lagnaCityData, system, activity,
          });
          if (!foundation) return;
          const {
            s0, e0, facts, lagnaDay, slotLagna, personal,
            choghadiya: c,
          } = foundation;
          const electionReasons = muSlotElectionReasons(
            facts,
            rules,
            {
              allowedNakshatras, avoidNakshatras, avoidJanmaNakshatra,
              allowedTithiNumbers, allowedTithiNames,
              avoidTithiNumbers, avoidVaraTithiNames,
            },
            data,
            people,
          );
          if (!electionReasons) return;

          // Build reason groups as we score — slot_quality, day_quality,
          // group_fit, activity_match, notes — mirroring Python's
          // day_slots() reason_groups field.
          const initial = muInitialSlotScore(foundation, electionReasons);
          let { score } = initial;
          const { slotQuality, dayQuality, groupFit, activityMatch } = initial;
          const tarabalam = muScoreParticipantTarabalam(people, facts.nakshatra);
          score += tarabalam.score;
          groupFit.push(...tarabalam.reasons);
          const taraUnfavNames = tarabalam.unfavourableNames;

          const chandrabalam = muScoreParticipantChandrabalam(
            people, facts.lunarSign, chandraMode,
          );
          score += chandrabalam.score;
          groupFit.push(...chandrabalam.reasons);
          const chandraAvoidNames = chandrabalam.avoidNames;
          const chandraPujaNames = chandrabalam.pujaNames;
          const hasAshtama = chandrabalam.hasAshtama;
          if (chandrabalam.drop) { droppedModeSlots++; return; }

          const lagnaScore = people.length && lagnaCityData && slotLagna
            ? muScoreParticipantLagna(people, slotLagna)
            : { score: 0, reasons: [], ashtamaNames: [] };
          score += lagnaScore.score;
          groupFit.push(...lagnaScore.reasons);
          const ashtamaLagnaNames = lagnaScore.ashtamaNames;

          const activityLagna = muScoreActivityLagna(
            slotLagna, requiredLagnaClass, allowedLagnas, preferLagnas,
            preferLagnaClass, lagnaCityData, activityLabel,
          );
          if (!activityLagna) return;
          score += activityLagna.score;
          activityMatch.push(...activityLagna.reasons);

          // Tithi family — slot-time tithi (Rikta → day_quality penalty;
          // activity class match → activity_match bonus)
          const tithiScore = muScoreSlotTithi(
            facts, preferTithiClass, activityLabel,
            avoidTithiClasses, preferTithiNumbers,
          );
          const tFam = tithiScore.family;
          score += tithiScore.score;
          dayQuality.push(...tithiScore.dayReasons);
          activityMatch.push(...tithiScore.activityReasons);

          // Special yogas — slot-time
          const specialYogaScore = muScoreSpecialYogas(facts, skipYogas);
          if (!specialYogaScore) return;
          score += specialYogaScore.score;
          dayQuality.push(...specialYogaScore.reasons);

          // Nitya yoga — slot-time (samskara skip on Vyatipata/Vaidhriti)
          const ny = facts.yoga;
          const nityaYogaScore = muScoreNityaYoga(
            facts, data, skipYogas, avoidNityaYogas, s0,
          );
          if (!nityaYogaScore) return;
          score += nityaYogaScore.score;
          if (nityaYogaScore.reason) dayQuality.push(nityaYogaScore.reason);

          const preferenceScore = muScoreSlotPreferences({
            facts, varaReason, preferNakshatras, amrita, s0, e0,
            preferChog, choghadiya: c, avoidKaranaNames, activityLabel,
          });
          score += preferenceScore.score;
          slotQuality.push(...preferenceScore.slotReasons);
          activityMatch.push(...preferenceScore.activityReasons);

          // Doctrinal notes — explanatory, no score effect
          const { notes, siddhiYogas } = muSlotDoctrinalNotes({
            cautionLagnaSolar, lagnaCityData, slotLagna,
            solarSign: data.solarSign, specialYogas: facts.specialYogas,
            taraUnfavNames, chandraAvoidNames, tithiFamily: tFam,
          });

          const reasonGroups = {
            slot_quality: slotQuality, day_quality: dayQuality,
            group_fit: groupFit, activity_match: activityMatch,
            personal_source: personal.evidence,
            personal_outcomes: personal.outcomes,
            day_source_outcomes: daylightPolicy?.outcomes || [],
            notes,
            chart_validation: manualGuidance.chart,
            chart_remainder: effectiveChartRemainder,
            information: manualGuidance.information,
            practical: manualGuidance.practical,
          };
          const reasons = [...slotQuality, ...groupFit, ...dayQuality, ...activityMatch];

          // Personal (chandra) dosha is never fully rectified by
          // group-level yogas — cap the tier below Excellent and flag
          // it so equally-scored clean slots sort first.
          const personalDosha = muPersonalDosha({
            chandraAvoidNames, hasAshtama, ashtamaLagnaNames,
            chandraPujaNames, taraUnfavNames, siddhiYogas,
          });

          // Day-level dosha (Rikta tithi, Visha/Dagdha yoga, Vyatipata/
          // Vaidhriti) — same "can't be Excellent" treatment as a
          // personal chandra dosha.
          const dayDosha = muSlotDayDosha({
            tithiFamily: tFam, facts, nityaYoga: ny,
            system, effectiveChartRemainder, rules, manualGuidance, personal,
          });

          const chartCheckMinutes = muChartCheckMinutes(lagnaDay, s0, e0);

          slots.push({
            d: new Date(d), isoDate, s0, e0, score, reasons, reasonGroups,
            personalDosha, dayDosha, dayCtx,
            personalPreferencePasses: personal.preferencePasses,
            chartCheckMinutes,
            chartCheckLagnas: muChartLagnasForMinutes(lagnaDay, chartCheckMinutes),
            chartBoundarySupported: muValidLagnaDayData(lagnaDay),
            chartBoundaryNeedsReview: muChartBoundaryNeedsReview(lagnaDay, s0, e0),
          });
          slotsPerDay.set(isoDate, (slotsPerDay.get(isoDate) || 0) + 1);
      };
      for (let mi = 0; mi < 15; mi++) processSlot(mi);
      // Diagnose: if the day produced no slots and it wasn't an eclipse,
      // record the most likely reason (samskara skip, mode filter, etc.).
      muRecordNoSlotDay({
        slotsPerDay, droppedDays, isoDate, data, skipYogas,
        activityLabel, people, chandraMode,
      });
    };
    for (let i = 0; i < nDays; i++) {
      const d = new Date(from); d.setDate(d.getDate() + i);
      const ev = events.get(stampOf(d));
      if (ev) processDay(d, ev);
    }
    droppedModeDays = droppedModeSlots;
    // "Excellent" means the best result across the full requested range.
    muRankCandidateSlots(slots);
    if (muSearchIsStale(searchSequence, searchFingerprint, box)) return;
    muSetShortlistProgress(box, slots);
    const chartEnrichment = await muEnrichCandidateSlots({
      slots, activity, system, city, roleProfile,
      lagnaCityData, signal: chartAbort.signal,
    });
    if (muSearchIsStale(searchSequence, searchFingerprint, box)) return;
    MU_LAST = {
      top: chartEnrichment.slots,
      chartEnrichment,
      droppedEclipseDays,
      droppedModeDays,
      droppedDays,
      droppedPersonalRules: chartEnrichment.personalRemovedRules,
      activity,
      people,
      chandraMode,
      roleProfile,
      context: searchContext,
    };
    renderMuhurta();
  } catch {
    if (chartAbort.signal.aborted || searchSequence !== MU_SEARCH_SEQUENCE) return;
    // Internal feed or chart details stay private; expose one stable recovery action.
    muSetResultMessage(box, 'Could not load the feed. Try again.', 'alert');
  } finally {
    if (MU_CHART_ABORT === chartAbort && searchSequence === MU_SEARCH_SEQUENCE) {
      box.setAttribute('aria-busy', 'false');
      MU_CHART_ABORT = null;
    }
  }
}

// taroOf-safe: gracefully handle the case where parseDescription returns
// a nakshatra string that's not in our table (shouldn't happen on canonical
// feeds, but defensive — return Janma (1) so the day reads as avoid).
function taroOf_safe(janma, dayNak) {
  try { return taraOf(janma, dayNak); } catch (_e) { return 1; }
}

let MU_LAST = null;
const MU_ACT_LABEL = {
  any: 'anything auspicious',
  travel: 'travel', purchase: 'a purchase',
  ceremony: 'a Shantika / Paushtika rite', beginning: 'a Dharma-kriya commencement',
  wedding: 'a wedding (Vivaha)',
  engagement: 'a mutual engagement (Kanya-Varavarana)',
  cremation: 'deferred funeral rites (Pretakriya)',
  naming: 'a naming ceremony', annaprasana: 'annaprasana (first feeding)',
  karnavedha: 'karnavedha (ear-piercing)', mundana: 'a mundana / chaula',
  upanayana: 'upanayana (sacred thread)',
  vidyarambha: 'Aksharabhyasa (first-letter writing)',
  seemantha: 'seemantha (prenatal ceremony)',
  gruhapravesha: 'gruhapravesha (home entry)',
  vehicle: 'a vehicle purchase', property: 'a land purchase for building',
  house_purchase: 'a completed house purchase',
  gold: 'a gold / jewelry purchase',
  business_inventory_purchase: 'a trade inventory purchase',
  borrowing_money: 'borrowing money / taking a loan',
  lending_money: 'lending money / giving a loan',
  bhumi_puja: 'bhumi puja (foundation laying)',
  well_digging: 'well digging',
  home_repair: 'a home repair / renovation start',
  business: 'a capital deployment / business investment', job: 'entering employment / starting service',
  yajna: 'a Homa offering (Homahuti)', pilgrimage: 'a pilgrimage',
  court: 'filing a lawsuit / court action', surgery: 'a surgery / medical procedure',
};

const MU_CHART_METHOD_URL = '/docs/reference/54-muhurtam-election-chart-screening';

type MuChartCompletionState = {
  state: string;
  candidateLimitReached: boolean;
  boundaryReviewCount: number;
  reviewGatedCount: number;
};

type MuChartDispositionState = MuChartCompletionState & {
  qualificationCappedCount: number;
};

type MuChartOutcomeState = {
  effect: string;
  status: string;
};

type MuChartBoundaryState = {
  boundaryConventionUncertain: boolean;
  needsReview: boolean;
  stable: boolean;
  qualificationFailed: boolean;
};

type MuRoleEnrichmentState = {
  state: string;
  screenedCount: number;
};

export function muPluralSuffix(count: number): string {
  return count === 1 ? '' : 's';
}

export function muChartOutcomeLabel(outcome: MuChartOutcomeState): string {
  if (outcome.effect === 'reject') {
    if (outcome.status === 'pass') return 'Required check passed';
    if (outcome.status === 'unknown') return 'Required check could not be verified';
    return 'Removed by mandatory chart rule';
  }
  if (outcome.effect === 'qualify') {
    if (outcome.status === 'pass') return 'Qualification met';
    if (outcome.status === 'unknown') {
      return 'Indeterminate at calculation boundary · review needed';
    }
    return 'Condition not met · slot retained · raw score unchanged · maximum rating Good';
  }
  if (outcome.status === 'pass') return 'Preference met · tie-break only';
  if (outcome.status === 'unknown') return 'Preference could not be verified';
  return 'Preference not present · no penalty';
}

export function muChartBoundaryMessage(screening: MuChartBoundaryState): string {
  if (screening.boundaryConventionUncertain) {
    return 'This window touches the five-minute Lagna convention guard at an edge. House-dependent checks remain unresolved; sign-based aspects are still evaluated.';
  }
  if (screening.needsReview) {
    if (screening.stable) {
      return 'One or more event-specific facts are indeterminate at a calculation boundary. The slot is retained, its raw score is unchanged, and the maximum rating is Good pending review.';
    }
    return 'Sampled states changed within this window, and one or more event-specific facts are indeterminate. The slot is retained, its raw score is unchanged, and the maximum rating is Good pending review.';
  }
  if (screening.qualificationFailed) {
    return 'At least one event-specific condition was conclusively not met. The slot is retained, its raw score is unchanged, and the maximum rating is Good; this is not an unknown or review result.';
  }
  if (screening.stable) {
    return 'The result was stable across every sampled Lagna-stable state in this window.';
  }
  return 'Sampled states changed, but every controlling outcome was resolved automatically.';
}

export function muDaylightOutcomeLabel(status: string): string {
  if (status === 'pass') return 'Required daylight check passed';
  if (status === 'fail') return 'Day removed by daylight rule';
  return 'Boundary could not be verified · day removed';
}

export function muPersonalOutcomeLabel(outcome: MuChartOutcomeState): string {
  if (outcome.status === 'pass') return 'Passed';
  if (outcome.effect === 'prefer' && outcome.status === 'fail') {
    return 'Preference not present';
  }
  if (outcome.status === 'unknown') return 'Could not verify';
  return 'Not met';
}

export function muRoleStatus(
  roleProfile: { name: string } | null,
  chartEnrichment: MuRoleEnrichmentState | null,
): string {
  if (!roleProfile) {
    return 'No participant selected · source-specific personal checks remain unknown';
  }
  if (chartEnrichment?.state === 'screened' || chartEnrichment?.screenedCount) {
    return `${roleProfile.name} · evaluated locally against the source-specific personal rules`;
  }
  if (chartEnrichment?.state === 'unsupported-system') {
    return `${roleProfile.name} selected · source-specific personal checks were not run for this system`;
  }
  if (chartEnrichment?.state === 'not-run') {
    return `${roleProfile.name} selected · there was no shortlisted slot to evaluate`;
  }
  if (chartEnrichment?.state === 'disabled') {
    return `${roleProfile.name} selected · source-specific personal checks are not active in this build`;
  }
  return `${roleProfile.name} selected · source-specific personal checks could not run without exact chart facts`;
}

export function muDroppedOutcomeLabel(status: string): string {
  if (status === 'pass') return 'passed';
  if (status === 'fail') return 'failed';
  return 'could not be verified';
}

export function muChartRemovalRow(rule): string {
  let evidence = '';
  if (rule.evidence?.length) {
    evidence = `<small>Observed: ${htmlEsc(rule.evidence.join(' '))}</small>`;
  }
  return `<li><strong>${htmlEsc(rule.label)}</strong> · ${rule.count} slot${muPluralSuffix(rule.count)}${evidence}</li>`;
}

export function muChartProvenanceParts(
  sourceReferences,
  decisionPolicies,
  conventions,
) {
  const eventSourceSuffix = muPluralSuffix(sourceReferences.length);
  let decisionPolicyHtml = '';
  if (decisionPolicies.length) {
    decisionPolicyHtml = `<p class="mu-rule-reference mu-rule-policy">
                  <strong>Product ranking policy:</strong>
                  The source defines the chart condition. This project policy defines how a resolved failure or an unresolved fact changes removal, rating caps, or tie-break ordering.
                </p>`;
  }
  const conventionHtml = conventions.map(convention => (
    `<p class="mu-rule-reference mu-rule-convention">
                  <strong>Interpretation convention:</strong> ${htmlEsc(convention.label)}<br>
                  ${htmlEsc(convention.formula)}
                </p>`
  )).join('');
  let rankingPolicyClaimsHtml = '';
  if (decisionPolicies.length) {
    const claims = decisionPolicies.map(claim => `<code>${htmlEsc(claim)}</code>`).join(' · ');
    rankingPolicyClaimsHtml = `<p><strong>Ranking policy claim${muPluralSuffix(decisionPolicies.length)}:</strong> ${claims}</p>`;
  }
  const conventionClaimsHtml = conventions.map(convention => {
    let methodClaimsHtml = '';
    if (convention.claims.length) {
      const claims = convention.claims.map(claim => `<code>${htmlEsc(claim)}</code>`).join(' · ');
      methodClaimsHtml = `<br><strong>Method claims:</strong> ${claims}`;
    }
    return `<p><strong>Convention:</strong> <code>${htmlEsc(convention.id)}</code>${methodClaimsHtml}</p>`;
  }).join('');
  return {
    eventSourceSuffix,
    decisionPolicyHtml,
    conventionHtml,
    rankingPolicyClaimsHtml,
    conventionClaimsHtml,
  };
}

export function muDayContextHtml(dc): string {
  if (!dc) return '';
  const winList = wins => wins.map(w => (
    `<span class="mu-tim"><b>${w.name}</b> ${w.ranges.join(', ')}</span>`
  )).join('');
  const tithiHtml = dc.tithi ? `<span class="mu-angachip">🌙 ${dc.tithi}</span>` : '';
  const nakshatraHtml = dc.nakshatra ? `<span class="mu-angachip">⭐ ${dc.nakshatra}</span>` : '';
  const yogaHtml = dc.yoga ? `<span class="mu-angachip">🧘 ${dc.yoga} yoga</span>` : '';
  const sunriseHtml = dc.sunrise ? `<span>🌅 Sunrise ${dc.sunrise}</span>` : '';
  const abhijitHtml = dc.abhijit ? `<span class="mu-t-aus">✨ Abhijit ${dc.abhijit}</span>` : '';
  const rahuHtml = dc.rahu ? `<span class="mu-t-warn">⛔ Rahu Kalam ${dc.rahu}</span>` : '';
  let auspiciousHtml = '';
  if (dc.auspicious.length) {
    auspiciousHtml = `<div class="mu-tim-row">
                    <span class="mu-tim-lbl mu-t-aus">🟢 Auspicious</span>
                    <span class="mu-tim-wins mu-t-aus">${winList(dc.auspicious)}</span></div>`;
  }
  let avoidHtml = '';
  if (dc.avoid.length) {
    avoidHtml = `<div class="mu-tim-row">
                    <span class="mu-tim-lbl mu-t-warn">🔴 Avoid</span>
                    <span class="mu-tim-wins mu-t-warn">${winList(dc.avoid)}</span></div>`;
  }
  return `<div class="mu-dayctx">
              <div class="mu-anga">
                ${tithiHtml}
                ${nakshatraHtml}
                ${yogaHtml}
              </div>
              <details class="mu-timings-d">
                <summary class="mu-timings">
                  ${sunriseHtml}
                  ${abhijitHtml}
                  ${rahuHtml}
                  <span class="mu-tim-toggle">all timings</span>
                </summary>
                <div class="mu-timings-full">
                  ${auspiciousHtml}
                  ${avoidHtml}
                </div>
              </details>
            </div>`;
}

export function muDroppedOutcomeHtml(outcomes): string {
  if (!outcomes?.length) return '';
  return `<ul class="mu-dropped-daylight" aria-label="Karnavedha daylight rule outcomes">
         ${outcomes.map(outcome => {
           const evidence = outcome.evidence?.length
             ? `<small>${htmlEsc(outcome.evidence.join(' '))}</small>`
             : '';
           return `<li class="mu-dropped-daylight--${outcome.status}">
           <strong>${htmlEsc(outcome.label)}</strong> · ${htmlEsc(muDroppedOutcomeLabel(outcome.status))}
           ${evidence}
         </li>`;
         }).join('')}
       </ul>`;
}

export function muChartReviewDetail(chartEnrichment): string {
  if (chartEnrichment?.boundaryReviewCount) {
    return ' · boundary-adjacent house checks held for review';
  }
  if (chartEnrichment?.reviewGatedCount) {
    return ' · unresolved chart facts held for review';
  }
  return '';
}

export function muChartStatusDispositionClass(disposition: string | null): string {
  return disposition ? ` mu-chart-status--screened-${disposition}` : '';
}

export function muChartValidationItems(screening, reasonGroups) {
  if (screening && Array.isArray(reasonGroups?.chart_remainder)) {
    return reasonGroups.chart_remainder;
  }
  return reasonGroups?.chart_validation;
}

export function muChartDispositionHtml(screening): string {
  if (screening?.needsReview) {
    return '<span class="mu-chart-disposition mu-chart-disposition--review">Review needed</span>';
  }
  if (screening?.qualificationFailed) {
    return '<span class="mu-chart-disposition mu-chart-disposition--capped">Condition not met · max Good</span>';
  }
  return '';
}

export function muSafetyTitle(activity: string): string {
  return activity === 'surgery'
    ? 'Medical care overrides timing'
    : 'Legal duties override timing';
}

export function muChartAssessorCanClaimComplete(
  activity: string,
  enrichment: MuChartCompletionState,
): boolean {
  return enrichment.state === 'screened'
    && !enrichment.candidateLimitReached
    && enrichment.boundaryReviewCount === 0
    && enrichment.reviewGatedCount === 0
    && chartAssessorCompleteFor(activity);
}

export function muChartScreeningDisposition(
  enrichment: MuChartDispositionState,
): 'review' | 'capped' | 'bounded' | 'resolved' | null {
  if (enrichment.state !== 'screened') return null;
  if (enrichment.reviewGatedCount || enrichment.boundaryReviewCount) {
    return 'review';
  }
  if (enrichment.qualificationCappedCount) return 'capped';
  if (enrichment.candidateLimitReached) return 'bounded';
  return 'resolved';
}

export function muChartAssessmentTitle(
  activity: string,
  enrichment: MuChartCompletionState,
): string {
  if (enrichment.boundaryReviewCount) {
    return 'Chart screening applied with boundary review';
  }
  if (enrichment.reviewGatedCount) {
    return 'Chart screening applied with unresolved facts';
  }
  if (enrichment.candidateLimitReached) {
    return 'Chart screening applied to a bounded candidate set';
  }
  if (muChartAssessorCanClaimComplete(activity, enrichment)) {
    if (activity === 'annaprasana') {
      return 'Annaprasana event-specific chart assessment complete';
    }
    if (activity === 'gold') return 'Gold event-specific chart clauses resolved';
  }
  if (activity === 'karnavedha') return 'Karnavedha event checks resolved';
  return 'Exact chart screening applied';
}

export function muSafetyOverrideFor(activity: string) {
  if (activity !== 'surgery' && activity !== 'court') return null;
  return muManualCheckRows(activity).find(
    row => row.purpose === 'safety_override',
  )?.text || null;
}

function muToT(mm) {
  const m = ((mm % 1440) + 1440) % 1440;
  return fmtT(`${String(Math.floor(m / 60)).padStart(2,'0')}:${String(m % 60).padStart(2,'0')}`);
}

function muResultScopeDetail(activity, chartEnrichment, partialAssessor: boolean): string {
  const hasScreeningReview = !!(
    chartEnrichment?.boundaryReviewCount
    || chartEnrichment?.reviewGatedCount
  );
  if (activity === 'gold') {
    return hasScreeningReview
      ? ' · all four Gold v1 event-specific clauses attempted; unresolved outcomes remain review-gated; the general election-chart baseline is not assessed'
      : ' · all four Gold v1 event-specific outcomes resolved; the general election-chart baseline is not assessed';
  }
  if (activity === 'annaprasana') {
    return muChartAssessorCanClaimComplete(activity, chartEnrichment)
      ? ' · all six Annaprasana event-specific clauses resolved; the general election-chart baseline #284 remains open'
      : ' · all six Annaprasana event-specific clauses attempted; unresolved or bounded outcomes remain review-gated; the general election-chart baseline #284 remains open';
  }
  if (activity === 'karnavedha') {
    if (hasScreeningReview) {
      return ' · daylight Tithi and Nakshatra gates resolved; the vacant-8th chart gate has an unresolved fact; the general election-chart baseline is not assessed';
    }
    if (chartEnrichment?.candidateLimitReached) {
      return ' · daylight Tithi and Nakshatra gates resolved; the vacant-8th chart gate was attempted on a bounded candidate set; the general election-chart baseline is not assessed';
    }
    return ' · daylight Tithi, daylight Nakshatra and vacant-8th outcomes all resolved';
  }
  if (partialAssessor) {
    return ' · event-specific clauses computed; overall assessment remains partial/provisional because the shared baseline is not complete';
  }
  return hasScreeningReview ? '' : ' · every implemented event-specific outcome resolved';
}

function muChartStatusFor(
  activity,
  chartEnrichment,
  hasManualChartGuidance: boolean,
  scopeDetail: string,
) {
  if (!chartEnrichment) return null;
  return {
    screened: {
      title: muChartAssessmentTitle(activity, chartEnrichment),
      detail: chartEnrichment.engine
        ? `${chartEnrichment.engine.name} ${chartEnrichment.engine.version} · ${chartEnrichment.engine.ayanamsha} · ${chartEnrichment.engine.ephemeris} planetary positions · ${chartEnrichment.engine.nodeConvention} lunar nodes · local Drik/Lahiri Lagna frame · whole-sign houses${muChartReviewDetail(chartEnrichment)}${scopeDetail}`
        : 'Every sampled Lagna-stable state checked',
    },
    'not-run': {
      title: 'Chart screening not run',
      detail: 'There was no Panchangam-shortlisted slot to send for chart projection.',
    },
    'manual-only': {
      title: hasManualChartGuidance
        ? 'Panchangam shortlist complete; chart review remains manual'
        : 'Panchangam shortlist complete',
      detail: hasManualChartGuidance
        ? 'This activity’s source guidance is qualitative and stays with a practitioner.'
        : 'No source-specific election-chart condition is defined for this general search.',
    },
    'unsupported-system': {
      title: 'Selected system kept separate',
      detail: 'Exact chart screening currently uses Drik/Lahiri, so it was not blended into this result.',
    },
    disabled: {
      title: 'Panchangam shortlist shown · review needed',
      detail: 'Exact chart screening is intentionally not active in this public build; no slot is presented as chart-screened.',
    },
    unavailable: {
      title: chartEnrichment.screenedCount
        ? 'Partial exact chart screening applied'
        : 'Panchangam shortlist shown',
      detail: chartEnrichment.screenedCount
        ? 'Only already-screened survivors are shown; every unprocessed candidate was withheld.'
        : 'Exact chart screening could not be reached; no slot is presented as chart-screened.',
    },
  }[chartEnrichment.state];
}

function muChartStatusHtml(
  activity,
  chartEnrichment,
  chartStatus,
  sourceScope,
  partialAssessorDisclosure,
): string {
  if (!chartEnrichment || !chartStatus) return '';
  const disposition = muChartScreeningDisposition(chartEnrichment);
  const message = roleForActivity(activity)
    ? chartEnrichment.message
    : chartEnrichment.message.replace('chart or profile facts', 'chart facts');
  return `<section class="mu-chart-status mu-chart-status--${chartEnrichment.state}${muChartStatusDispositionClass(disposition)}" aria-label="Election-chart assessment status">
              <strong>${htmlEsc(chartStatus.title)}</strong>
              <span>${htmlEsc(message)}</span>
              <small>${htmlEsc(chartStatus.detail)}</small>
              ${sourceScope ? `<small class="mu-chart-source-scope"><b>Source scope:</b> ${htmlEsc(sourceScope)}</small>` : ''}
              ${partialAssessorDisclosure ? `<small class="mu-chart-assessment-boundary"><b>Assessment boundary:</b> ${htmlEsc(partialAssessorDisclosure)}</small>` : ''}
              <a href="${MU_CHART_METHOD_URL}">Verify the method and sources</a>
            </section>`;
}

function muNoSlotsResultHtml(options) {
  const {
    droppedEclipseDays, droppedModeDays, chartEnrichment,
    personalRemovalCount, droppedDays, safetyHtml, chartStatusHtml,
    personalRoleHtml, chartRemovalHtml, personalRemovalHtml, droppedHtml,
  } = options;
  const notes = [];
  if (droppedEclipseDays) notes.push(`${droppedEclipseDays} eclipse day(s) deferred`);
  if (droppedModeDays) notes.push(`${droppedModeDays} slot(s) filtered by chandra mode`);
  if (chartEnrichment?.chartRemovedCount) {
    notes.push(`${chartEnrichment.chartRemovedCount} shortlisted slot(s) failed an exact chart requirement`);
  }
  if (personalRemovalCount) {
    notes.push(`${personalRemovalCount} candidate slot(s) failed a profile-specific source rule`);
  }
  const daylightDropped = droppedDays.filter(
    day => Array.isArray(day.daylightOutcomes) && day.daylightOutcomes.length,
  );
  if (daylightDropped.length) {
    notes.push(
      `${daylightDropped.length} Karnavedha day(s) filtered: ${daylightDropped[0].reason}`,
    );
  }
  const suffix = notes.length ? ` · ${notes.join(', ')}` : '';
  const message = `No clear slots found${suffix}. Try more days, relax the standard, or clear the people above.`;
  return {
    message,
    html: `${safetyHtml}${chartStatusHtml}${personalRoleHtml}<p class="preview-error">${htmlEsc(message)}</p>${chartRemovalHtml}${personalRemovalHtml}${droppedHtml}`,
  };
}

function muAnnounceResult(top, chartEnrichment, chartStatus): void {
  const announcement = document.getElementById('mu-result-announcement');
  if (!announcement) return;
  const cappedCount = chartEnrichment?.qualificationCappedCount || 0;
  const reviewCount = chartEnrichment?.reviewGatedCount || 0;
  const overlapCount = chartEnrichment?.overlappingDispositionCount || 0;
  const chartCounts = chartEnrichment?.state === 'screened' ? (
    ` ${cappedCount} retained slot${muPluralSuffix(cappedCount)} capped by a conclusive miss; `
    + `${reviewCount} retained slot${muPluralSuffix(reviewCount)} review-gated by an unknown; `
    + `${overlapCount} included in both counts.`
  ) : '';
  announcement.textContent = `${top.length} slot${muPluralSuffix(top.length)} found. ${chartStatus?.title || 'Search complete'}.${chartCounts}`;
}

function renderMuhurta() {
  if (!MU_LAST) return;
  const box = document.getElementById('mu-result');
  const {
    top,
    chartEnrichment,
    activity,
    roleProfile = null,
    droppedEclipseDays = 0,
    droppedModeDays = 0,
    droppedDays = [],
    droppedPersonalRules = [],
  } = MU_LAST;
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const fmtIso = iso => {
    const [y, mo, da] = iso.split('-').map(Number);
    return new Date(y, mo - 1, da).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };
  const droppedHtml = droppedDays.length
    ? `<details class="mu-dropped"><summary>${droppedDays.length} day${muPluralSuffix(droppedDays.length)} filtered · see why</summary>
         <ul>${droppedDays.map(dd => `<li><span class="dd-date">${fmtIso(dd.date)}</span> · ${htmlEsc(dd.reason)}${muDroppedOutcomeHtml(dd.daylightOutcomes)}</li>`).join('')}</ul>
       </details>`
    : '';
  const partialAssessor = automatedRulesFor(activity).length > 0
    && !chartAssessorCompleteFor(activity);
  const hasManualChartGuidance = muClassifyManualChecks(activity).chart.length > 0
    || partialAssessor;
  const sourceScope = (MU_ACTIVITY[activity] as { source_scope?: string })
    ?.source_scope || null;
  const partialAssessorDisclosure = muEventSpecificCompletionDisclosure(
    activity,
    chartEnrichment,
  );
  const scopeDetail = muResultScopeDetail(activity, chartEnrichment, partialAssessor);
  const chartStatus = muChartStatusFor(
    activity, chartEnrichment, hasManualChartGuidance, scopeDetail,
  );
  const chartStatusHtml = muChartStatusHtml(
    activity, chartEnrichment, chartStatus, sourceScope, partialAssessorDisclosure,
  );
  const roleRequirement = roleForActivity(activity);
  const roleStatus = muRoleStatus(roleProfile, chartEnrichment);
  const personalRoleHtml = roleRequirement
    ? `<div class="mu-personal-role">
         <strong>${htmlEsc(roleRequirement.label)}</strong>
         <span>${htmlEsc(roleStatus)}</span>
       </div>`
    : '';
  const personalRemovalCount = chartEnrichment?.personalRemovedCount
    ?? droppedPersonalRules.reduce((total, rule) => total + rule.count, 0);
  const personalRemovalHtml = personalRemovalCount
    ? `<details class="mu-personal-removals">
         <summary>${personalRemovalCount} candidate slot${muPluralSuffix(personalRemovalCount)} removed by profile-specific source rules</summary>
         <ul>${droppedPersonalRules.map(rule => `<li>${htmlEsc(rule.label)} · ${rule.count} slot${muPluralSuffix(rule.count)}</li>`).join('')}</ul>
       </details>`
    : '';
  const chartRemovedRules = chartEnrichment?.chartRemovedRules || [];
  const chartRemovalHtml = chartEnrichment?.chartRemovedCount
    ? `<details class="mu-chart-removals">
         <summary>${chartEnrichment.chartRemovedCount} candidate slot${muPluralSuffix(chartEnrichment.chartRemovedCount)} removed by exact event-chart rules</summary>
         <ul>${chartRemovedRules.map(rule => muChartRemovalRow(rule)).join('')}</ul>
       </details>`
    : '';
  const safetyOverride = muSafetyOverrideFor(activity);
  const safetyHtml = safetyOverride
    ? `<aside class="mu-safety-override" role="note">
         <strong>${muSafetyTitle(activity)}</strong>
         <span>${htmlEsc(safetyOverride)}</span>
       </aside>`
    : '';
  if (!top.length) {
    const noSlots = muNoSlotsResultHtml({
      droppedEclipseDays, droppedModeDays, chartEnrichment,
      personalRemovalCount, droppedDays, safetyHtml, chartStatusHtml,
      personalRoleHtml, chartRemovalHtml, personalRemovalHtml, droppedHtml,
    });
    box.innerHTML = noSlots.html;
    const announcement = document.getElementById('mu-result-announcement');
    if (announcement) announcement.textContent = noSlots.message;
    return;
  }
  const share = `<button class="wa-share-mini" style="position:static;width:28px;height:28px;flex:none;margin-left:auto;" title="Share these slots on WhatsApp" aria-label="Share on WhatsApp" onclick="shareMuhurtaOnWhatsApp()"><svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg></button>`;
  const muLineClass = (item) => {
    if (/\(\+\d+\)\s*$/.test(item)) return 'mu-pos';
    if (/\(-\d+\)\s*$/.test(item)) return 'mu-neg';
    if (/rectifies/i.test(item)) return 'mu-pos';
    if (/not rectified|remains a personal caution|puja recommended/i.test(item)) return 'mu-caution';
    return '';
  };
  const muCapitalize = (item) => item.charAt(0).toUpperCase() + item.slice(1);
  const renderGroup = (label, items, extraClass = '') => {
    if (!items?.length) return '';
    const lis = items.map(it => `<li class="${muLineClass(it)}">${htmlEsc(muCapitalize(it))}</li>`).join('');
    return `<div class="mu-rg ${extraClass}">
              <span class="mu-rg-label">${htmlEsc(label)}</span>
              <ul class="mu-rg-items">${lis}</ul>
            </div>`;
  };
  const renderChartValidation = items => {
    if (!items?.length) return '';
    const lis = items.map(it => `<li>${htmlEsc(muCapitalize(it))}</li>`).join('');
    return `<div class="mu-rg mu-rg-validation">
              <span class="mu-rg-label">Still needs practitioner review</span>
              <div class="mu-rg-content">
                <p>The source also gives broader chart guidance that is not a complete deterministic algorithm. Automated clauses appear above; a practitioner must interpret what remains:</p>
                <ul class="mu-rg-items">${lis}</ul>
              </div>
            </div>`;
  };
  const renderComputedChart = screening => {
    if (!screening?.outcomes?.length) return '';
    const lis = screening.outcomes.map(outcome => {
      const label = muChartOutcomeLabel(outcome);
      const evidence = Array.isArray(outcome.evidence) && outcome.evidence.length
        ? `<small>Observed: ${htmlEsc(outcome.evidence.join(' '))}</small>`
        : '';
      return `<li class="mu-chart-rule mu-chart-rule--${outcome.effect} mu-chart-rule--${outcome.status}">
                <span>${htmlEsc(muCapitalize(outcome.label))}</span>
                <b>${label}</b>
                ${evidence}
              </li>`;
    }).join('');
    const boundary = muChartBoundaryMessage(screening);
    const sourceReferences = Array.from(new Map<string, { claim: string; locator: string }>(
      screening.outcomes.map(outcome => [
        outcome.sourceClaim,
        { claim: outcome.sourceClaim, locator: outcome.sourceLocator },
      ]),
    ).values());
    const decisionPolicies = [...new Set(
      screening.outcomes
        .map(outcome => outcome.decisionPolicyClaim)
        .filter((claim): claim is string => !!claim),
    )];
    const conventions = Array.from(new Map<string, {
      id: string; label: string; formula: string; claims: string[];
    }>(screening.outcomes
      .filter(outcome => outcome.conventionId)
      .map(outcome => [outcome.conventionId, {
        id: outcome.conventionId,
        label: outcome.conventionLabel || outcome.conventionId,
        formula: outcome.formula || '',
        claims: outcome.methodClaims || [],
      }])).values());
    const {
      eventSourceSuffix,
      decisionPolicyHtml,
      conventionHtml,
      rankingPolicyClaimsHtml,
      conventionClaimsHtml,
    } = muChartProvenanceParts(sourceReferences, decisionPolicies, conventions);
    return `<section class="mu-rg mu-rg-computed" aria-label="Computed election-chart checks">
              <h4 class="mu-rg-label">Computed chart checks</h4>
              <div class="mu-rg-content">
                <ul class="mu-rg-items">${lis}</ul>
                <p class="mu-chart-boundary">${boundary}</p>
                <p class="mu-rule-reference"><strong>Event source${eventSourceSuffix}:</strong>
                  ${sourceReferences.map(reference => htmlEsc(reference.locator)).join('<br>')}
                </p>
                ${decisionPolicyHtml}
                ${conventionHtml}
                <details class="mu-technical-provenance">
                  <summary>Technical provenance</summary>
                  <p><strong>Event claim${eventSourceSuffix}:</strong> ${sourceReferences.map(reference => `<code>${htmlEsc(reference.claim)}</code>`).join(' · ')}</p>
                  ${rankingPolicyClaimsHtml}
                  ${conventionClaimsHtml}
                </details>
                <p class="mu-rule-reference"><a href="${MU_CHART_METHOD_URL}">Method, formulas, assumptions and exact references</a></p>
              </div>
            </section>`;
  };
  const renderComputedDaylight = outcomes => {
    if (!outcomes?.length) return '';
    const lis = outcomes.map(outcome => {
      const label = muDaylightOutcomeLabel(outcome.status);
      const evidence = Array.isArray(outcome.evidence) && outcome.evidence.length
        ? `<small>Observed: ${htmlEsc(outcome.evidence.join(' '))}</small>`
        : '';
      return `<li class="mu-chart-rule mu-chart-rule--reject mu-chart-rule--${outcome.status}">
                <span>${htmlEsc(muCapitalize(outcome.label))}</span>
                <b>${label}</b>
                ${evidence}
              </li>`;
    }).join('');
    const first = outcomes[0];
    return `<section class="mu-rg mu-rg-computed mu-rg-daylight" aria-label="Computed Karnavedha daylight checks">
              <h4 class="mu-rg-label">Computed daylight checks</h4>
              <div class="mu-rg-content">
                <ul class="mu-rg-items">${lis}</ul>
                <p class="mu-chart-boundary">Evaluated once for this day over the half-open interval [local sunrise, local sunset), using the feed's published Tithi and Nakshatra transition boundaries rather than candidate-window samples. A same-minute sunset boundary stays unknown.</p>
                <p class="mu-rule-reference"><strong>Event source:</strong> ${htmlEsc(first.sourceLocator)}</p>
                <details class="mu-technical-provenance">
                  <summary>Technical provenance</summary>
                  <p><strong>Event claim:</strong> <code>${htmlEsc(first.sourceClaim)}</code><br><strong>Named policy:</strong> <code>${htmlEsc(first.policyId)}</code><br><strong>Policy claim:</strong> <code>${htmlEsc(first.decisionPolicyClaim)}</code></p>
                </details>
                <p class="mu-rule-reference"><a href="${MU_CHART_METHOD_URL}">Method, boundary semantics and source crosswalk</a></p>
              </div>
            </section>`;
  };
  const renderPersonalChecks = (outcomes, evidence) => {
    if (!outcomes?.length) return renderGroup(
      'Profile-specific check', evidence, 'mu-rg-personal');
    const lis = outcomes.map((outcome, index) => {
      const label = muPersonalOutcomeLabel(outcome);
      return `<li class="mu-personal-rule mu-personal-rule--${outcome.status}">
                <span>${htmlEsc(muCapitalize(outcome.label))}</span>
                <b>${label}</b>
                ${evidence?.[index] ? `<small>${htmlEsc(evidence[index])}</small>` : ''}
                <span class="mu-rule-claim">Source record <code>${htmlEsc(outcome.sourceClaim)}</code></span>
              </li>`;
    }).join('');
    const sourceLocator = outcomes.find(outcome => outcome.sourceLocator)?.sourceLocator;
    return `<div class="mu-rg mu-rg-personal-computed">
              <span class="mu-rg-label">Profile-specific checks</span>
              <div class="mu-rg-content">
                <ul class="mu-rg-items">${lis}</ul>
                ${sourceLocator ? `<p class="mu-rule-reference">Reference: ${htmlEsc(sourceLocator)} · <a href="${MU_CHART_METHOD_URL}">method and source crosswalk</a></p>` : ''}
              </div>
            </div>`;
  };
  const renderSlot = (s) => {
    const rg = s.reasonGroups;
    const groupsHtml = rg
      ? `<details class="mu-reason-details">
           <summary>Why this slot earned its ${s.tier || muScoreTier(s.score)} rating</summary>
           <div class="mu-rgroups">
             ${renderGroup('Slot quality', rg.slot_quality)}
             ${renderGroup('Day quality', rg.day_quality)}
             ${renderGroup('Group fit', rg.group_fit)}
             ${renderPersonalChecks(rg.personal_outcomes, rg.personal_source)}
             ${renderGroup('Activity', rg.activity_match)}
             ${renderComputedDaylight(rg.day_source_outcomes)}
             ${renderComputedChart(s.chartScreening)}
             ${renderChartValidation(muChartValidationItems(s.chartScreening, rg))}
             ${renderGroup('About this election', rg.information, 'mu-rg-information')}
             ${renderGroup('Practical checks', rg.practical, 'mu-rg-practical')}
             ${renderGroup('Important nuance', rg.notes, 'mu-rg-notes')}
           </div>
         </details>`
      : `<details class="mu-reason-details"><summary>Why this slot ranked here</summary><span class="mu-reasons">${s.reasons.map(reason => htmlEsc(reason)).join(' · ')}</span></details>`;
    const tier = s.tier || muScoreTier(s.score);
    const tierClass = `mu-tier-${tier.toLowerCase()}`;
    const chartDisposition = muChartDispositionHtml(s.chartScreening);
    const dayCtxHtml = muDayContextHtml(s.dayCtx);
    return `<div class="mu-slot">
              <span class="mu-when">${fmtD(s.d)} · ${muToT(s.s0)} to ${muToT(s.e0)}</span>
              <span class="mu-tier ${tierClass}">${tier}</span>
              <span class="mu-score">score ${s.score}</span>
              ${chartDisposition}
              ${dayCtxHtml}
              ${groupsHtml}
            </div>`;
  };
  box.innerHTML =
    `<div class="tb-summary"><span class="count">${top.length}</span>&nbsp;slot${muPluralSuffix(top.length)} found · ranked by tier, then score, then source preference${share}</div>`
    + safetyHtml
    + chartStatusHtml
    + personalRoleHtml
    + chartRemovalHtml
    + personalRemovalHtml
    + `<p class="mu-ranking-note">Excellent slots appear before Good ones. Mandatory chart failures remove a slot. A conclusive event-specific qualification miss retains the slot, leaves its raw score unchanged, and sets Good as its maximum rating. A calculation-boundary unknown also retains the slot and sets the same maximum pending review. Source preferences only break ties; they do not inflate the Panchangam score.</p>`
    + top.map(renderSlot).join('')
    + droppedHtml
    + `<p class="preview-note" style="margin-top:0.5rem;">Each slot's score is the sum of the (+n)/(-n) bonuses across
       Slot quality (choghadiya, Abhijit/Amrita overlap), Day quality (Siddhi yogas, Nitya yoga, Rikta tithi),
       Group fit (per-person tarabalam and chandrabalam), and Activity match (preferred tithi class / vara).
       Being clear of every inauspicious window is a requirement, not a bonus. The tier reflects this score's
       rank within this search, capped below Excellent whenever a named dosha or unresolved review is present.
       Exact event-specific election-chart checks are evaluated at both sides of every known Lagna transition in each window; a failed
       mandatory rule removes the slot, a conclusive qualification miss retains it with unchanged raw score and a maximum Good rating, and a source preference only breaks ties. Houses use the same local Drik/Lahiri
       Lagna frame as the shortlist. A window touching the five-minute transition-convention guard at either edge remains
       review-gated.</p>`;
  muAnnounceResult(top, chartEnrichment, chartStatus);
}

/** Select only non-personal result evidence for the public share payload. */
export function muShareableMuhurtaReasons(slot) {
  const groups = slot?.reasonGroups || {};
  return [
    ...(groups.slot_quality || []),
    ...(groups.day_quality || []),
    ...(groups.activity_match || []),
  ].filter(reason => reason !== 'clear of all inauspicious windows').slice(0, 3);
}

export function muChartShareScreeningLine(chartEnrichment) {
  if (chartEnrichment?.state === 'screened') {
    if (chartEnrichment.candidateLimitReached) {
      return `Exact chart screening reached its safety budget after ${chartEnrichment.screenedCount} candidate${chartEnrichment.screenedCount === 1 ? '' : 's'}; every shown survivor was screened, but lower-ranked candidates were not assessed.`;
    }
    return 'The automated, source-backed election-chart subset was checked across every sampled Lagna-stable state.';
  }
  if (chartEnrichment?.state === 'unavailable' && chartEnrichment.screenedCount > 0) {
    return `Partial exact chart screening was applied to ${chartEnrichment.screenedCount} candidate${chartEnrichment.screenedCount === 1 ? '' : 's'}; only already-screened survivors are included, and unprocessed candidates were withheld.`;
  }
  return 'Panchangam-ranked; exact election-chart screening was not applied.';
}

export function muChartShareIncludesRemainder(chartEnrichment) {
  return chartEnrichment?.state === 'screened'
    || (chartEnrichment?.state === 'unavailable' && chartEnrichment.screenedCount > 0);
}

function muShownSlotNeedsReview(slot): boolean {
  return Boolean(slot.chartScreening?.needsReview) || (
    Array.isArray(slot.reasonGroups?.personal_outcomes)
    && slot.reasonGroups.personal_outcomes.some(
      outcome => outcome?.status === 'unknown')
  );
}

function muEventShareScopeLine(activity: string): string | null {
  if (activity === 'gold') {
    return 'Gold v1 assesses four event-specific clauses; the general election-chart baseline is not assessed.';
  }
  if (activity === 'annaprasana') {
    return 'Annaprasana v1 assesses six event-specific chart clauses; the general election-chart baseline #284 remains open.';
  }
  if (activity === 'karnavedha') {
    return 'Karnavedha v1 assesses two daylight-limb gates and the vacant-eighth chart clause; the general election-chart baseline is not assessed.';
  }
  return null;
}

function muChartCompletionShareLines(
  activity,
  chartEnrichment,
  remainder,
  qualificationCapped: number,
  reviewGated: number,
): string[] {
  const lines: string[] = [];
  const assessorPartial = automatedRulesFor(activity).length > 0
    && !chartAssessorCompleteFor(activity);
  if (assessorPartial) {
    lines.push('This event assessor is still partial/provisional; the event-specific clauses are computed, but they are not complete chart certification because the shared baseline remains unresolved.');
  }
  if (chartEnrichment.candidateLimitReached) {
    lines.push(`The chart-search safety budget was reached after ${chartEnrichment.screenedCount} candidate${chartEnrichment.screenedCount === 1 ? '' : 's'}; every shown slot was screened, but lower-ranked candidates were not assessed.`);
    return lines;
  }
  if (activity === 'annaprasana' && !remainder.length) {
    lines.push(reviewGated
      ? 'All six Annaprasana event-specific chart clauses were attempted; unresolved facts still require review.'
      : 'All six Annaprasana event-specific chart clauses were evaluated and resolved.');
    return lines;
  }
  if (!remainder.length) {
    if (reviewGated) {
      lines.push('All disclosed event chart clauses were attempted; unresolved facts still require review.');
    } else if (qualificationCapped) {
      lines.push('All disclosed event chart clauses were evaluated; one or more qualifications were not met and the affected ratings were capped.');
    } else {
      lines.push('All disclosed event chart clauses were evaluated and resolved under the documented interpretation convention.');
    }
    return lines;
  }
  lines.push(
    'The automated, source-backed election-chart clauses were checked across every sampled Lagna-stable state.',
    'Qualitative chart or ritual checks still require practitioner review; see the result details.',
  );
  return lines;
}

function muChartCountShareLines(
  qualificationCapped: number,
  reviewGated: number,
  overlapping: number,
): string[] {
  const lines: string[] = [];
  if (qualificationCapped) {
    lines.push(`${qualificationCapped} shown slot${qualificationCapped === 1 ? '' : 's'} had a conclusive event-specific condition miss; ${qualificationCapped === 1 ? 'it was' : 'they were'} retained with unchanged raw score and a maximum Good rating.`);
  }
  if (reviewGated) {
    lines.push(`${reviewGated} shown slot${reviewGated === 1 ? '' : 's'} ${reviewGated === 1 ? 'is' : 'are'} indeterminate at a calculation boundary or missing fact and ${reviewGated === 1 ? 'remains' : 'remain'} review-gated.`);
  }
  if (overlapping) {
    lines.push(`${overlapping} shown slot${overlapping === 1 ? ' is' : 's are'} included in both counts because a conclusive miss and a separate unknown coexist.`);
  }
  return lines;
}

function muChartShareDetailLines(top, activity, chartEnrichment): string[] {
  const remainder = chartManualRemaindersFor(activity) || [];
  const qualificationCapped = top.filter(
    slot => slot.chartScreening?.qualificationFailed).length;
  const reviewGated = top.filter(muShownSlotNeedsReview).length;
  const overlapping = top.filter(
    slot => slot.chartScreening?.qualificationFailed
      && muShownSlotNeedsReview(slot)).length;
  const scopeLine = muEventShareScopeLine(activity);
  return [
    ...(scopeLine ? [scopeLine] : []),
    ...muChartCompletionShareLines(
      activity, chartEnrichment, remainder, qualificationCapped, reviewGated,
    ),
    ...muChartCountShareLines(qualificationCapped, reviewGated, overlapping),
    `Method: https://panchangam.astrochaganti.com${MU_CHART_METHOD_URL}`,
  ];
}

// Narrow test seam for the orchestration helpers extracted from the legacy
// panel. The browser-smoke suite covers their integrated paths; Vitest calls
// these boundaries directly so a structural refactor cannot create hidden
// function-coverage debt.
export const muComplexityContracts = {
  muConfiguredDaylightPolicy,
  muPrimaryDayDrop,
  muCalendarDayDrop,
  muSolarDayDrop,
  muDayDrop,
  muBadWindows,
  muYogaDayDropReason,
  muChandraModeDayDropReason,
  muNoSlotDayReason,
  muRecordNoSlotDay,
  muScoreSlotTithi,
  muScoreSpecialYogas,
  muScoreNityaYoga,
  muScoreSlotPreferences,
  muSlotDoctrinalNotes,
  muPersonalDosha,
  muSlotDayDosha,
  muDominantChoghadiya,
  muSlotElectionReasons,
  muActivityNeedsLagna,
  muRankCandidateSlots,
  muUnavailableChartEnrichment,
  muResultScopeDetail,
  muChartStatusFor,
  muChartCompletionShareLines,
};

function shareMuhurtaOnWhatsApp() {
  if (!MU_LAST?.top.length) return;
  const { top, activity, chartEnrichment, context } = MU_LAST;
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const lines = [];
  lines.push(
    `⏱ *Good time slots · ${MU_ACT_LABEL[activity]}*`,
    `📍 ${context.cityLabel} · ${context.fromIso} to ${context.toIso}`,
  );
  if (roleForActivity(activity)) {
    lines.push('Source-specific personal checks were applied locally when possible; profile details are intentionally omitted from this share.');
  }
  lines.push(muChartShareScreeningLine(chartEnrichment));
  if (muChartShareIncludesRemainder(chartEnrichment)) {
    lines.push(...muChartShareDetailLines(top, activity, chartEnrichment));
  }
  lines.push('');
  top.slice(0, 5).forEach(s => {
    lines.push(`• ${s.tier || muScoreTier(s.score)} · ${fmtD(s.d)} · ${muToT(s.s0)} to ${muToT(s.e0)}`);
    const shareableReasons = muShareableMuhurtaReasons(s);
    if (shareableReasons.length) lines.push(`   ${shareableReasons.join(' · ')}`);
  });
  lines.push(
    '',
    'Every slot is clear of Rahu Kalam, Varjyam and all inauspicious windows.',
    'Find your own: https://panchangam.astrochaganti.com/?src=share-slots#tarabalam',
  );
  gcEvent('share-slots');
  window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
}


export {
  calcTarabalam, renderTarabalam, tbRenderProfileInputs,
  tbAddRow, tbRemoveRow, tbResetProfiles, tbSaveProfiles,
  tbSetMode, tbToggleShowAll, tbExtendTo,
  findMuhurta, renderMuhurta,
  shareTarabalamOnWhatsApp, shareMuhurtaOnWhatsApp,
};

export function tbHasDays() { return !!TB_DAYS; }
export function muHasLast() { return Boolean(MU_LAST); }

/** Wire panel-internal seeds; called once from Init. */
export function initTarabalamPanel(todayISO) {
  tbRenderProfileInputs();
  inpEl('tb-from').value = todayISO;
  const t2 = new Date(); t2.setDate(t2.getDate() + 13);
  inpEl('tb-to').value =
    `${t2.getFullYear()}-${String(t2.getMonth() + 1).padStart(2, '0')}-${String(t2.getDate()).padStart(2, '0')}`;
  for (const id of ['tb-from', 'tb-to']) {
    inpEl(id).addEventListener('change', () => invalidateMuhurtaSearch());
  }
}
