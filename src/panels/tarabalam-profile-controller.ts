import { htmlEsc } from '../lib/html';
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
import { NAKSHATRA_NAMES, RASI_NAMES, rasiFromStar } from '../data/rasis';
import { roleForActivity } from '../scorer/personal-election-screening';
import {
  borrowingPurposeContext,
  borrowingPurposeLabel,
  type BorrowingPurpose,
} from '../scorer/borrowing-context';

const TB_NAKSHATRAS = NAKSHATRA_NAMES;
const TB_RASIS = RASI_NAMES;

export interface TarabalamProfileRuntime {
  invalidateMuhurtaSearch(announce?: boolean): void;
  clearResults(): void;
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
  getBorrowingPurpose(): BorrowingPurpose;
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

export function tbRoleParticipant(activity: string): JourneyGuestProfile | null {
  return TB_PROFILE_CONTROLLER?.getRoleParticipant(activity) || null;
}

export function tbBorrowingPurpose(): BorrowingPurpose {
  return TB_PROFILE_CONTROLLER?.getBorrowingPurpose() || 'other_or_unknown';
}

/**
 * Bind stable local guest profiles to the existing Muhurtam participant root.
 * Saved-profile choices persist by ID; one-off participants live only in this
 * controller and are deliberately never written to the profile store.
 */
export function initTarabalamProfiles(
  store: GuestProfileStore,
  actions: TarabalamProfileActions,
  runtime: TarabalamProfileRuntime,
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
  let borrowingPurpose: BorrowingPurpose = 'other_or_unknown';

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
    if (!total) {
      const role = roleForActivity(activitySelect?.value || 'any');
      if (role?.required) {
        return `No ${role.label.toLowerCase()} is selected. The source-specific personal check will remain unresolved.`;
      }
      return 'No participant screening is selected. Slots will use general Muhurtam rules.';
    }
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
      runtime.invalidateMuhurtaSearch();
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
      runtime.invalidateMuhurtaSearch();
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
      runtime.invalidateMuhurtaSearch();
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
    runtime.invalidateMuhurtaSearch();
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
    runtime.invalidateMuhurtaSearch(false);
    selection = saveMuhurtamProfileSelection(selectionStorage, [], snapshot.profiles);
    manualParticipants = [];
    transientIssue = null;
    runtime.clearResults();
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
      const role = roleForActivity(activitySelect?.value || 'any');
      root.append(tbNode(
        'p',
        'muhurta-profile-empty',
        role?.required
          ? `No saved profiles yet. Add someone for this search or create a saved profile; the required ${role.label.toLowerCase()} check otherwise remains unresolved.`
          : 'No saved profiles yet. You can still search without personal screening or add someone for this search.',
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
        runtime.invalidateMuhurtaSearch();
        roleSelections.set(activity, roleSelect.value);
        persistRoleSelection(activity, roleSelect.value);
      });
    }
    label.append(labelText, roleSelect);
    roleBlock.append(prompt, label);
    root.append(roleBlock);
  };

  const renderBorrowingPurposeSelection = (): void => {
    const activity = activitySelect?.value || 'any';
    if (activity !== 'borrowing_money') return;
    const context = borrowingPurposeContext(borrowingPurpose);
    const block = tbNode('div', 'muhurta-role-selection muhurta-borrowing-purpose');
    const prompt = tbNode(
      'p',
      'muhurta-role-selection__prompt',
      'Choose only the broad purpose needed to show the applicable source guidance. Do not enter financial details.',
    );
    const label = tbNode('label', 'muhurta-role-selection__field');
    const labelText = tbNode('span', 'muhurta-role-selection__label', 'Borrowing purpose');
    const select = tbNode('select') as HTMLSelectElement;
    select.dataset.borrowingPurpose = '';
    for (const purpose of [
      'quick_domestic_or_personal', 'business', 'other_or_unknown',
    ] as const) {
      tbAppendOption(select, purpose, borrowingPurposeLabel(purpose));
    }
    select.value = context.purpose;
    select.addEventListener('change', () => {
      borrowingPurpose = borrowingPurposeContext(select.value).purpose;
      runtime.invalidateMuhurtaSearch();
    });
    label.append(labelText, select);
    block.append(prompt, label);
    root.append(block);
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
      renderBorrowingPurposeSelection();
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
    getBorrowingPurpose(): BorrowingPurpose {
      return borrowingPurpose;
    },
    selectProfile(id: string): boolean {
      runtime.invalidateMuhurtaSearch();
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
      runtime.invalidateMuhurtaSearch();
      manualParticipants.splice(index, 1);
      transientIssue = null;
      controller.render();
    },
    clearParticipants,
  };

  const onActivityChange = (): void => {
    runtime.invalidateMuhurtaSearch();
    controller.render();
  };
  activitySelect?.addEventListener('change', onActivityChange);

  const unsubscribe = store.subscribe(nextSnapshot => {
    runtime.invalidateMuhurtaSearch();
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
export function tbRenderProfileInputs(): void {
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

export function tbSaveProfiles(): boolean {
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

export function tbResetProfiles(runtime: TarabalamProfileRuntime): void {
  if (TB_PROFILE_CONTROLLER) {
    TB_PROFILE_CONTROLLER.clearParticipants();
    return;
  }
  localStorage.removeItem(GUEST_BIRTH_PROFILE_STORAGE_KEY);
  localStorage.removeItem(GUEST_PROFILE_COMMIT_STORAGE_KEY);
  localStorage.removeItem(GUEST_PROFILE_STORAGE_KEY);
  TB_LEGACY_ROWS = 1;
  runtime.clearResults();
  tbRenderProfileInputs();
  for (const id of ['tb-summary', 'tb-result', 'mu-context', 'mu-result']) {
    document.getElementById(id)?.replaceChildren();
  }
}

export function tbAddRow(): void {
  if (TB_PROFILE_CONTROLLER) {
    TB_PROFILE_CONTROLLER.addManualParticipant();
    return;
  }
  if (!tbSaveProfiles()) return;
  TB_LEGACY_ROWS = Math.min(MAX_GUEST_PROFILES, TB_LEGACY_ROWS + 1);
  tbRenderProfileInputs();
}

export function tbRemoveRow(index: number): void {
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
