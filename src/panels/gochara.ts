// typing lands with the component rewrite, not the move.
//
// Gochara panel: transit chart, vedha screening, and the daily
// LLM/deterministic rasi phalalu reading.

import { htmlEsc } from '../lib/html';
import { gcEvent } from '../lib/analytics';
import { RASI_NAMES, rasiFromStar } from '../data/rasis';
import { MU_CHANDRA_GOOD, MU_CHANDRA_PUJA } from '../muhurta-scorer';
import { selEl } from '../lib/dom';
import { shaniConditionFromMoonHouse, shaniConditionLine } from '../shani-conditions';
import {
  canonicalLegacyGuestProfileLagna,
  guestProfileReadiness,
  readLegacyGuestProfileRows,
  type GuestProfile,
  type GuestProfileStore,
  type ProfileStorage,
} from '../lib/guest-profile-store';
import {
  GOCHARA_SELECTION_STORAGE_KEY,
  gocharaProfileValue,
  loadGocharaSelection,
  resolveGocharaSelection,
  type GocharaSelectionResolution,
} from '../lib/profile-selection';

// Chandrabalam house sets — same classical table the muhurta scorer pins.
const CHANDRA_GOOD = MU_CHANDRA_GOOD;
const CHANDRA_PUJA = MU_CHANDRA_PUJA;

const GO_FAV = { Surya:[3,6,10,11], Chandra:[1,3,6,7,10,11], Kuja:[3,6,11],
  Budha:[2,4,6,8,10,11], Guru:[2,5,7,9,11], Shukra:[1,2,3,4,5,8,9,11,12],
  Shani:[3,6,11], Rahu:[3,6,10,11], Ketu:[3,6,10,11] };
const GO_VEDHA = { Surya:{3:9,6:12,10:4,11:5}, Chandra:{1:5,3:9,6:12,7:2,10:4,11:8},
  Kuja:{3:12,6:9,11:5}, Budha:{2:5,4:3,6:9,8:1,10:8,11:12},
  Guru:{2:12,5:4,7:3,9:10,11:8}, Shukra:{1:8,2:7,3:1,4:10,5:9,8:5,9:11,11:6,12:3},
  Shani:{3:12,6:9,11:5} };
const GO_EXEMPT = new Set(['Surya|Shani','Shani|Surya','Chandra|Budha','Budha|Chandra']);
const GO_NODES = new Set(['Rahu','Ketu']);
let GO_DATA = null;
let LLM_PHALALU = null;

export interface GocharaProfileActions {
  createProfile(trigger: HTMLElement): void;
  editProfile(id: string, trigger: HTMLElement): void;
  manageProfiles(trigger: HTMLElement): void;
}

export interface GocharaProfilesController {
  refresh(): void;
  selectProfile(id: string): boolean;
  destroy(): void;
}

let gocharaProfileStore: GuestProfileStore | null = null;
let gocharaProfileActions: GocharaProfileActions | null = null;
let destroyGocharaProfiles: (() => void) | null = null;

const unavailableSelectionStorage: ProfileStorage = {
  getItem() { throw new Error('storage unavailable'); },
  setItem() { throw new Error('storage unavailable'); },
};

function goSelectionStorage(): ProfileStorage {
  try {
    return globalThis.localStorage || unavailableSelectionStorage;
  } catch {
    return unavailableSelectionStorage;
  }
}

function persistGocharaSelection(value: string): boolean {
  try {
    goSelectionStorage().setItem(GOCHARA_SELECTION_STORAGE_KEY, value);
    return true;
  } catch {
    return false;
  }
}

function profileDisplayName(profile: Readonly<GuestProfile>): string {
  return profile.name || 'Unnamed profile';
}

function option(
  value: string,
  label: string,
  disabled = false,
): HTMLOptionElement {
  const node = document.createElement('option');
  node.value = value;
  node.textContent = label;
  node.disabled = disabled;
  return node;
}

function stateAction(
  label: string,
  action: 'create' | 'edit' | 'manage',
  callback: (trigger: HTMLButtonElement) => void,
  primary = false,
  profileId: string | null = null,
): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = `go-profile-action go-profile-action--${primary ? 'primary' : 'secondary'}`;
  button.dataset.goProfileAction = action;
  button.dataset.goProfileFocus = profileId ? `${action}:${profileId}` : action;
  if (profileId) button.dataset.goProfileId = profileId;
  button.textContent = label;
  button.addEventListener('click', () => callback(button));
  return button;
}

function profileIdFromSelection(value: string | null): string | null {
  const match = value?.match(/^profile:(.+)$/);
  return match ? match[1] : null;
}

function appendProfileNotice(root: HTMLElement, message: string): void {
  const notice = document.createElement('p');
  notice.className = 'go-profile-notice';
  notice.setAttribute('role', 'status');
  notice.textContent = message;
  root.append(notice);
}

function appendProfileContext(root: HTMLElement, message: string): void {
  const context = document.createElement('p');
  context.className = 'go-profile-context';
  context.textContent = message;
  root.append(context);
}

function appendProfileActions(root: HTMLElement, ...buttons: HTMLButtonElement[]): void {
  if (!buttons.length) return;
  const actions = document.createElement('div');
  actions.className = 'go-profile-actions';
  actions.append(...buttons);
  root.append(actions);
}

function incompleteProfileActions(
  profiles: readonly Readonly<GuestProfile>[],
  excludeId: string | null = null,
): HTMLButtonElement[] {
  if (!gocharaProfileActions) return [];
  return profiles.flatMap(profile => {
    if (profile.id === excludeId) return [];
    const readiness = guestProfileReadiness(profile);
    if (readiness.horoscope) return [];
    const missing = readiness.missingForHoroscope === 'pada' ? 'Padam' : 'Nakshatra';
    return [stateAction(
      `Complete ${profileDisplayName(profile)} · Needs ${missing}`,
      'edit',
      trigger => gocharaProfileActions?.editProfile(profile.id, trigger),
      false,
      profile.id,
    )];
  });
}

function restoreProfileActionFocus(root: HTMLElement, focusKey: string | null): void {
  if (!focusKey) return;
  const replacement = Array.from(
    root.querySelectorAll<HTMLElement>('[data-go-profile-focus]'),
  ).find(candidate => candidate.dataset.goProfileFocus === focusKey);
  replacement?.focus();
}

function renderIncompleteProfileState(
  root: HTMLElement,
  profile: Readonly<GuestProfile>,
  resolution: GocharaSelectionResolution,
  profiles: readonly Readonly<GuestProfile>[],
): void {
  const missing = resolution.fallback?.missingField === 'pada' ? 'Padam' : 'Nakshatra';
  appendProfileContext(
    root,
    `Add ${missing} to ${profileDisplayName(profile)} before using this profile here.`,
  );
  if (gocharaProfileActions) {
    appendProfileActions(
      root,
      stateAction(
        `Complete ${profileDisplayName(profile)}`,
        'edit',
        trigger => gocharaProfileActions?.editProfile(profile.id, trigger),
        true,
        profile.id,
      ),
      stateAction('Manage profiles', 'manage', trigger => gocharaProfileActions?.manageProfiles(trigger)),
    );
  }
  appendProfileActions(root, ...incompleteProfileActions(profiles, profile.id));
}

function renderSelectedProfileState(
  root: HTMLElement,
  resolution: GocharaSelectionResolution,
  profiles: readonly Readonly<GuestProfile>[],
): void {
  const profile = resolution.profile!;
  appendProfileContext(
    root,
    `Using ${profile.name || 'this profile'}'s saved birth star: ${profile.rasi} Janma Rashi. `
      + 'Daily Horoscope is Moon-sign based; Lagna stays with the profile for supported natal-chart details and Muhurtam.',
  );
  if (gocharaProfileActions) {
    appendProfileActions(
      root,
      stateAction(
        `Edit ${profile.name || 'profile'}`,
        'edit',
        trigger => gocharaProfileActions?.editProfile(profile.id, trigger),
        false,
        profile.id,
      ),
      stateAction('Manage profiles', 'manage', trigger => gocharaProfileActions?.manageProfiles(trigger)),
    );
  }
  appendProfileActions(root, ...incompleteProfileActions(profiles));
}

function renderSpecificGocharaProfileState(
  root: HTMLElement,
  resolution: GocharaSelectionResolution,
  profiles: readonly Readonly<GuestProfile>[],
): boolean {
  const requestedProfileId = profileIdFromSelection(resolution.requestedValue);
  const requestedProfile = requestedProfileId
    ? profiles.find(profile => profile.id === requestedProfileId) || null
    : null;
  if (requestedProfile && resolution.fallback?.code === 'profile-not-horoscope-ready') {
    renderIncompleteProfileState(root, requestedProfile, resolution, profiles);
    return true;
  }

  if (resolution.kind === 'profile' && resolution.profile) {
    renderSelectedProfileState(root, resolution, profiles);
    return true;
  }

  if (profiles.length === 0) {
    appendProfileContext(root, 'Create a profile to reuse a birth star here and in Muhurtam. It stays only in this browser.');
    if (gocharaProfileActions) {
      appendProfileActions(root, stateAction('Create profile', 'create', trigger => gocharaProfileActions?.createProfile(trigger), true));
    }
    return true;
  }
  return false;
}

function renderGocharaProfileState(
  resolution: GocharaSelectionResolution,
  selectionStorageUnavailable = false,
): void {
  const root = document.getElementById('go-profile-state');
  if (!root) return;
  const active = document.activeElement;
  const focusKey = active instanceof HTMLElement && root.contains(active)
    ? active.dataset.goProfileFocus || null
    : null;
  root.replaceChildren();

  const snapshot = gocharaProfileStore?.getSnapshot();
  const profiles = snapshot?.profiles || [];
  if (resolution.fallback) appendProfileNotice(root, resolution.fallback.message);
  if (
    !resolution.fallback &&
    (selectionStorageUnavailable || snapshot?.persistence === 'memory')
  ) {
    appendProfileNotice(root, 'Your horoscope choice works for this page, but this browser cannot save it.');
  }

  if (renderSpecificGocharaProfileState(root, resolution, profiles)) {
    restoreProfileActionFocus(root, focusKey);
    return;
  }

  if (resolution.kind === 'rashi') {
    appendProfileContext(root, 'This is a one-off Rashi view. Choose a saved profile above to return to a personal horoscope faster.');
  } else {
    appendProfileContext(root, 'Choose a saved profile above for a personal Daily Horoscope, or select any Rashi for a one-off view.');
  }
  if (gocharaProfileActions) {
    appendProfileActions(root, stateAction('Manage profiles', 'manage', trigger => gocharaProfileActions?.manageProfiles(trigger)));
  }
  appendProfileActions(root, ...incompleteProfileActions(profiles));
  restoreProfileActionFocus(root, focusKey);
}

async function loadGochara() {
  const firstLoad = !GO_DATA;
  if (firstLoad) {
    try {
      const r = await fetch('gochara.json', { cache: 'no-cache' });
      GO_DATA = await r.json();
    } catch (error) {
      console.error('Unable to load Gochara sky data:', error);
      document.getElementById('go-chart').innerHTML =
        '<p class="preview-error">Sky data unavailable — try again later.</p>';
      return;
    }
    // date input removed — always show today

    // Fetch the stable latest artifact and use it only when it belongs to
    // today. Requesting a date-shaped path made the normal deterministic
    // fallback emit a browser 404 on every day without an interpretation.
    try {
      const d = new Date();
      const todayISO = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      const pr = await fetch('rasi_phalalu/latest.json', { cache: 'no-cache' });
      if (pr.ok) {
        const candidate = await pr.json();
        if (candidate?.date === todayISO) LLM_PHALALU = candidate;
      }
    } catch (_) { /* no LLM phalalu today — computed fallback will be used */ }
  }
  // Profiles may have changed elsewhere; rebuild from the subscribed store.
  goBuildViewSelect();
  renderGochara();
}

function goDateIndex() {
  const start = new Date(GO_DATA.start + 'T00:00:00');
  const today = new Date(new Date().setHours(0,0,0,0));
  const i = Math.round((today.getTime() - start.getTime()) / 86400000);
  return Math.max(0, Math.min(i, GO_DATA.days.length - 1));
}

function goTill(idx, gi) {
  const cur = GO_DATA.days[idx][gi];
  for (let j = idx + 1; j < GO_DATA.days.length; j++) {
    if (GO_DATA.days[j][gi] !== cur) {
      const d = new Date(GO_DATA.start + 'T00:00:00');
      d.setDate(d.getDate() + j);
      return { date: d, next: GO_DATA.rasis[GO_DATA.days[j][gi]] };
    }
  }
  return null;
}

function goSavedPeople() {
  let saved: ReturnType<typeof readLegacyGuestProfileRows>;
  try {
    // Keep the compatibility boundary explicit for corrupt legacy payloads;
    // the outer guard also covers browsers that deny the localStorage getter.
    saved = readLegacyGuestProfileRows(localStorage);
  } catch {
    saved = [];
  }
  return saved.map((v, i) => {
    if (!v?.nak) return null;
    const rasi = rasiFromStar(v.nak, Number(v.pada) || null);
    if (!rasi) return null;
    // Lagna remains a factual profile detail in the selector; the surrounding
    // context makes clear that Daily Horoscope itself uses Janma Rashi only.
    const lagna = canonicalLegacyGuestProfileLagna(v.lagna);
    return {
      name: (v.name || (i === 0 ? 'You' : `Person ${i+1}`)),
      rasi,
      lagna,
    };
  }).filter(Boolean);
}

function stableProfileOption(profile: Readonly<GuestProfile>): HTMLOptionElement {
  const readiness = guestProfileReadiness(profile);
  const name = profileDisplayName(profile);
  if (!readiness.horoscope) {
    const missing = readiness.missingForHoroscope === 'pada' ? 'Padam' : 'Nakshatra';
    return option(gocharaProfileValue(profile.id), `${name} · Needs ${missing}`, true);
  }
  const refs = profile.lagna
    ? `${readiness.janmaRasi} Rashi + ${profile.lagna} Lagna`
    : `${readiness.janmaRasi} Rashi`;
  return option(gocharaProfileValue(profile.id), `${name} · ${refs}`);
}

function buildStableViewSelect(preferredValue?: string): GocharaSelectionResolution {
  const sel = selEl('go-view');
  const snapshot = gocharaProfileStore!.getSnapshot();
  const hadOptions = sel.options.length > 0;
  let selectionStorageUnavailable: boolean;
  let resolution: GocharaSelectionResolution;

  if (preferredValue === undefined && !hadOptions) {
    const loaded = loadGocharaSelection(goSelectionStorage(), snapshot.profiles);
    resolution = loaded;
    selectionStorageUnavailable = loaded.storageIssue === 'storage-unavailable';
  } else {
    const requestedValue = preferredValue ?? sel.value;
    resolution = resolveGocharaSelection(requestedValue, snapshot.profiles);
    selectionStorageUnavailable = !persistGocharaSelection(resolution.value);
  }

  const wholeSky = option('', 'Transits only — whole sky');
  const nodes: Array<HTMLOptionElement | HTMLOptGroupElement> = [wholeSky];
  if (snapshot.profiles.length) {
    const saved = document.createElement('optgroup');
    saved.label = 'Saved profiles';
    for (const profile of snapshot.profiles) saved.append(stableProfileOption(profile));
    nodes.push(saved);
  }
  const anyRashi = document.createElement('optgroup');
  anyRashi.label = 'Any Rashi';
  RASI_NAMES.forEach((rasi, index) => anyRashi.append(option(String(index), rasi)));
  nodes.push(anyRashi);
  sel.replaceChildren(...nodes);
  sel.value = [...sel.options].some(candidate => candidate.value === resolution.value)
    ? resolution.value
    : '';
  renderGocharaProfileState(resolution, selectionStorageUnavailable);
  return resolution;
}

function buildLegacyViewSelect(): void {
  const sel = selEl('go-view');
  const hadOptions = sel.options.length > 0;
  let keep = hadOptions ? sel.value : null;
  if (!hadOptions) {
    try {
      keep = goSelectionStorage().getItem(GOCHARA_SELECTION_STORAGE_KEY);
    } catch {
      keep = null;
    }
  }
  // An earlier iteration stored separate rashi/lagna suffixes. The combined
  // legacy option remains available until the profile store initializes.
  if (keep && /^p\d+[rl]$/.test(keep)) keep = keep.slice(0, -1);
  const people = goSavedPeople();
  const nodes: Array<HTMLOptionElement | HTMLOptGroupElement> = [
    option('', 'Transits only — whole sky'),
  ];
  if (people.length) {
    const saved = document.createElement('optgroup');
    saved.label = 'Your saved people';
    people.forEach((person, index) => {
      const refs = person.lagna
        ? `${person.rasi} Rashi + ${person.lagna} Lagna`
        : `${person.rasi} Rashi`;
      saved.append(option(`p${index}`, `${person.name} · ${refs}`));
    });
    nodes.push(saved);
  }
  const anyRashi = document.createElement('optgroup');
  anyRashi.label = 'Any Rashi';
  RASI_NAMES.forEach((rasi, index) => anyRashi.append(option(String(index), rasi)));
  nodes.push(anyRashi);
  sel.replaceChildren(...nodes);
  if (keep && [...sel.options].some(candidate => candidate.value === keep)) sel.value = keep;
}

function goBuildViewSelect(preferredValue?: string) {
  if (gocharaProfileStore) return buildStableViewSelect(preferredValue);
  buildLegacyViewSelect();
  return null;
}

/**
 * Connect the Daily Horoscope selector to the shared guest-profile store.
 * The subscription is intentionally owned here so profile edits made from
 * any journey update this panel without relying on Tarabalam to rebuild it.
 */
export function initGocharaProfiles(
  store: GuestProfileStore,
  actions: GocharaProfileActions,
): GocharaProfilesController {
  destroyGocharaProfiles?.();
  gocharaProfileStore = store;
  gocharaProfileActions = actions;

  const select = document.getElementById('go-view') as HTMLSelectElement | null;
  if (!select) throw new Error('Daily Horoscope selector #go-view was not found');
  let destroyed = false;

  const refresh = (): void => {
    if (destroyed) return;
    goBuildViewSelect();
    if (GO_DATA) renderGochara();
  };
  const handleChange = (): void => {
    if (destroyed) return;
    goBuildViewSelect(select.value);
    if (GO_DATA) renderGochara();
  };

  select.addEventListener('change', handleChange);
  const unsubscribe = store.subscribe(refresh);

  const selectProfile = (id: string): boolean => {
    if (destroyed) return false;
    const profile = store.get(id);
    if (!profile || !guestProfileReadiness(profile).horoscope) return false;
    const resolution = goBuildViewSelect(gocharaProfileValue(id));
    if (resolution?.kind !== 'profile' || resolution.profile?.id !== id) return false;
    if (GO_DATA) renderGochara();
    select.focus();
    return true;
  };

  const destroy = (): void => {
    if (destroyed) return;
    destroyed = true;
    select.removeEventListener('change', handleChange);
    unsubscribe();
    if (destroyGocharaProfiles === destroy) {
      destroyGocharaProfiles = null;
      gocharaProfileStore = null;
      gocharaProfileActions = null;
    }
  };
  destroyGocharaProfiles = destroy;

  const controller: GocharaProfilesController = { refresh, selectProfile, destroy };
  refresh();
  return controller;
}

function goCurrentView() {
  const val = selEl('go-view').value;
  if (val === '') return { jr: null, jl: null, label: null };
  if (gocharaProfileStore) {
    const resolved = resolveGocharaSelection(
      val,
      gocharaProfileStore.getSnapshot().profiles,
    );
    if (resolved.kind === 'profile' && resolved.profile?.rasi) {
      const jr = RASI_NAMES.indexOf(resolved.profile.rasi);
      return {
        jr,
        jl: null,
        label: `${resolved.profile.rasi} Janma Rashi (${resolved.profile.name})`,
      };
    }
    if (resolved.kind === 'rashi' && resolved.rasiIndex !== null) {
      return {
        jr: resolved.rasiIndex,
        jl: null,
        label: `${RASI_NAMES[resolved.rasiIndex]} rashi`,
      };
    }
    return { jr: null, jl: null, label: null };
  }
  // 'p<i>' — legacy profile-keyed view. Daily Horoscope is deliberately
  // anchored only to Janma Rashi; a saved Lagna remains a profile fact for
  // the natal chart and Muhurtam, not a second Gochara reference.
  const profMatch = /^p(\d+)$/.exec(val);
  if (profMatch) {
    const k = goSavedPeople()[Number(profMatch[1])];
    if (!k) return { jr: null, jl: null, label: null };
    const jr = RASI_NAMES.indexOf(k.rasi);
    return { jr, jl: null, label: `${k.rasi} Janma Rashi (${k.name})` };
  }
  // Bare rashi-index option from the "Any rashi" group.
  const rasiIndex = Number(val);
  return {
    jr: rasiIndex,
    jl: null,
    label: `${RASI_NAMES[rasiIndex]} rashi`,
  };
}

// South Indian chart: fixed rasi positions on a 4x4 grid (row, col)
const GO_LAYOUT = { 11:[1,1], 0:[1,2], 1:[1,3], 2:[1,4], 3:[2,4], 4:[3,4],
                    5:[4,4], 6:[4,3], 7:[4,2], 8:[4,1], 9:[3,1], 10:[2,1] };

function goElement(tag: string, className = '', text: string | number | null = null): HTMLElement {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== null) node.textContent = String(text);
  return node;
}

function goPhalaluShareButton(): HTMLButtonElement {
  const button = goElement(
    'button',
    'wa-share-mini go-phalalu-share',
  ) as HTMLButtonElement;
  button.type = 'button';
  button.title = 'Share this reading on WhatsApp';
  button.setAttribute('aria-label', 'Share on WhatsApp');
  button.addEventListener('click', shareGocharaOnWhatsApp);

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('width', '14');
  svg.setAttribute('height', '14');
  svg.setAttribute('fill', 'currentColor');
  svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute(
    'd',
    'M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z',
  );
  svg.append(path);
  button.append(svg);
  return button;
}

function goHouseFrom(row, grahaIndex, reference) {
  return ((row[grahaIndex] - reference + 12) % 12) + 1;
}

function goOccupants(row, reference) {
  const occupants = {};
  GO_DATA.grahas.forEach((graha, grahaIndex) => {
    const house = goHouseFrom(row, grahaIndex, reference);
    const houseOccupants = occupants[house] ?? [];
    houseOccupants.push(graha);
    occupants[house] = houseOccupants;
  });
  return occupants;
}

function goVerdict(row, grahaIndex, reference, occupants) {
  const graha = GO_DATA.grahas[grahaIndex];
  const position = goHouseFrom(row, grahaIndex, reference);
  if (!GO_FAV[graha].includes(position)) return 'bad';
  if (GO_NODES.has(graha)) return 'good';
  const vedhaHouse = GO_VEDHA[graha][position];
  for (const other of (occupants[vedhaHouse] || [])) {
    const isVedha = other !== graha
      && !GO_NODES.has(other)
      && !GO_EXEMPT.has(`${graha}|${other}`);
    if (isVedha) return 'blocked';
  }
  return 'good';
}

function renderShaniCondition(row, janmaRasi) {
  const conditionRoot = document.getElementById('go-conditions');
  if (janmaRasi === null) {
    conditionRoot.replaceChildren();
    return;
  }
  const shaniIdx = GO_DATA.grahas.indexOf('Shani');
  const houseFrom = (grahaIndex, reference) => goHouseFrom(row, grahaIndex, reference);
  const jr = janmaRasi;
  const condition = shaniConditionFromMoonHouse(houseFrom(shaniIdx, jr));
  if (!condition) {
    conditionRoot.replaceChildren();
    return;
  }
  const conditionLabel = `${condition} — from Moon sign`;
  const runningLabel = conditionLabel.split(' — ')[0].split(' (')[0];
  conditionRoot.innerHTML = `<div class="go-cond"><span class="chip">⚠️ ${htmlEsc(conditionLabel)}</span>
       <div class="tb-sub" style="margin-top:0.25rem;">Running ${runningLabel}? Personalised guidance:
       <a href="https://astrochaganti.com" target="_blank" rel="noopener" style="color:var(--indigo);font-weight:600;">astrochaganti.com</a></div></div>`;
}

function grahasByRasi(row) {
  const grouped = {};
  GO_DATA.grahas.forEach((_graha, grahaIndex) => {
    const rasi = row[grahaIndex];
    const grahas = grouped[rasi] ?? [];
    grahas.push(grahaIndex);
    grouped[rasi] = grahas;
  });
  return grouped;
}

function goOrdinal(value) {
  return `${value}${['st', 'nd', 'rd'][value - 1] || 'th'}`;
}

function goVerdictLabel(verdict) {
  if (verdict === 'good') return 'favourable';
  if (verdict === 'blocked') return 'vedha';
  return 'adverse';
}

function transitTitle(row, grahaIndex, rasi, janmaRasi, verdict, transition) {
  let title = `${GO_DATA.grahas[grahaIndex]} in ${GO_DATA.rasis[rasi]}`;
  if (janmaRasi !== null) {
    const house = goHouseFrom(row, grahaIndex, janmaRasi);
    title += ` — ${goOrdinal(house)} from Janma Rashi (${goVerdictLabel(verdict)})`;
  }
  if (transition) {
    const date = transition.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    title += ` · till ${date}`;
  }
  return title;
}

function grahaNode(row, grahaIndex, rasi, janmaRasi, verdict, retrograde, dateIndex) {
  const transition = goTill(dateIndex, grahaIndex);
  const className = verdict ? `go-g ${verdict}` : 'go-g';
  const graha = goElement('span', className, GO_DATA.grahas[grahaIndex]);
  graha.title = transitTitle(row, grahaIndex, rasi, janmaRasi, verdict, transition);
  if (retrograde) graha.append(goElement('span', 'go-retro', '℞'));
  return graha;
}

function rasiBox(row, retrograde, grouped, rasi, janmaRasi, verdictOf, dateIndex) {
  const [gridRow, gridColumn] = GO_LAYOUT[rasi];
  const isJanma = janmaRasi === rasi;
  const className = isJanma ? 'go-box janma' : 'go-box';
  const box = goElement('div', className);
  box.style.gridRow = String(gridRow);
  box.style.gridColumn = String(gridColumn);
  const janmaLabel = isJanma ? ' · janma' : '';
  box.append(goElement('span', 'rname', `${GO_DATA.rasis[rasi]}${janmaLabel}`));
  if (janmaRasi !== null) {
    box.append(goElement('span', 'house', ((rasi - janmaRasi + 12) % 12) + 1));
  }
  box.append(document.createElement('br'));
  for (const grahaIndex of (grouped[rasi] || [])) {
    box.append(grahaNode(
      row,
      grahaIndex,
      rasi,
      janmaRasi,
      verdictOf(grahaIndex),
      retrograde[grahaIndex],
      dateIndex,
    ));
  }
  return box;
}

function renderTransitChart(row, retrograde, view, dateShown, verdictOf, dateIndex) {
  const grouped = grahasByRasi(row);
  const chartNodes = Array.from(
    { length: 12 },
    (_unused, rasi) => rasiBox(row, retrograde, grouped, rasi, view.jr, verdictOf, dateIndex),
  );
  document.getElementById('go-note').replaceChildren();
  const centerContext = view.jr !== null
    ? `from ${view.label}`
    : 'transits — choose a person or rashi above to personalise';
  const dateLabel = dateShown.toLocaleDateString(
    'en-US',
    { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' },
  );
  const center = goElement('div', 'go-center');
  center.append(
    goElement('div', 'd1', '🪐 Gochara'),
    goElement('div', 'd2', dateLabel),
    goElement('div', 'd2', centerContext),
  );
  document.getElementById('go-chart').replaceChildren(...chartNodes, center);
}

function renderUpcomingMoves(index) {
  const fastGrahas = new Set(['Chandra', 'Budha', 'Surya']);
  const moves = GO_DATA.grahas
    .map((graha, grahaIndex) => ({ graha, transition: goTill(index, grahaIndex) }))
    .filter(move => move.transition && fastGrahas.has(move.graha))
    .sort((left, right) => left.transition.date - right.transition.date);
  const root = document.getElementById('go-moves');
  if (!moves.length) {
    root.replaceChildren();
    return;
  }
  const movesBox = goElement('div', 'go-moves');
  movesBox.append(goElement('b', '', 'Coming up:'), ' ');
  moves.forEach((move, moveIndex) => {
    if (moveIndex) movesBox.append(goElement('span', 'go-move-sep', '  ·  '));
    const item = goElement('span', 'go-move', `${move.graha} → ${move.transition.next} `);
    const date = move.transition.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    item.append(goElement('b', '', date));
    movesBox.append(item);
  });
  root.replaceChildren(movesBox);
}

function interpretationDetails(entry) {
  const details = goElement('details', 'go-interpretation-details');
  details.append(goElement('summary', '', "Read today's interpretive guidance"));
  const interpretation = goElement('div', 'go-interpretation-content');
  interpretation.append(goElement('p', '', entry.text));
  if (entry.advice) {
    const advice = goElement('div');
    advice.style.cssText = 'margin-top:0.65rem;padding:0.5rem 0.65rem;background:#FFF8ED;border-left:3px solid var(--amber);border-radius:0 6px 6px 0;';
    const label = goElement('span', 'go-guidance-label', "Today's guidance");
    label.style.cssText = 'font-size:0.68rem;text-transform:uppercase;letter-spacing:0.05em;font-weight:600;display:block;margin-bottom:0.2rem;';
    const guidance = goElement('span', '', entry.advice);
    guidance.style.cssText = 'font-size:0.84rem;color:#44403c;line-height:1.5;';
    advice.append(label, guidance);
    interpretation.append(advice);
  }
  const boundary = goElement(
    'p',
    '',
    'AI-written interpretation: cited transit positions and verdicts are engine-checked; prose and guidance are interpretive, not independently scripturally verified.',
  );
  boundary.style.cssText = 'font-size:0.72rem;color:#746B5E;margin-top:0.65rem;';
  interpretation.append(boundary);
  details.append(interpretation);
  return details;
}

function renderPhalalu(janmaRasi, row, view) {
  const root = document.getElementById('go-phalalu');
  if (janmaRasi === null) {
    root.replaceChildren();
    return;
  }
  const phalalu = buildPhalalu(janmaRasi, row);
  const llmEntry = LLM_PHALALU?.rashis?.[RASI_NAMES[janmaRasi]];
  const reading = goElement('div', 'go-phalalu');
  const heading = goElement('h4', 'go-phalalu-heading');
  heading.append(
    goElement('span', 'go-phalalu-title', `Rasi Phalalu — ${view.label}`),
    goElement('span', `go-quality ${phalalu.quality}`, `${phalalu.quality} day`),
    goPhalaluShareButton(),
  );
  reading.append(heading, goElement('p', 'go-phalalu-opener', phalalu.opener));
  if (phalalu.condition) {
    reading.append(goElement('p', 'go-phalalu-condition', phalalu.condition));
  }
  reading.append(goElement('p', 'go-phalalu-summary', phalalu.summary));
  const computedDetails = goElement('details', 'go-phalalu-details');
  computedDetails.append(goElement(
    'summary',
    '',
    `Why this guidance? View ${phalalu.detailLines.length} computed transit checks`,
  ));
  const detailLines = goElement('div', 'go-phalalu-detail-lines');
  phalalu.detailLines.forEach(line => detailLines.append(goElement('p', '', line)));
  computedDetails.append(detailLines);
  reading.append(computedDetails);
  if (llmEntry) reading.append(interpretationDetails(llmEntry));
  reading.append(goElement(
    'p',
    'go-phalalu-boundary',
    'The detailed checks are deterministic outputs from the documented Janma-Rashi transit rules.',
  ));
  root.replaceChildren(reading);
}

function renderGocharaLegend(janmaRasi) {
  document.getElementById('go-legend').innerHTML = janmaRasi === null ? '' :
    `<div class="tb-legend" style="margin-top:0.5rem;">
      <span class="tb-legend-item"><span class="go-g good">favourable</span></span>
      <span class="tb-legend-item"><span class="go-g blocked">blocked by vedha</span></span>
      <span class="tb-legend-item"><span class="go-g bad">adverse</span></span>
      <span class="tb-legend-item"><span class="go-g">℞ retrograde</span></span>
      </div>`;
}

function renderGochara() {
  // A denied browser-storage write must never prevent the chart from rendering.
  persistGocharaSelection(selEl('go-view').value);
  if (!GO_DATA) return;
  const idx = goDateIndex();
  const row = GO_DATA.days[idx], retro = GO_DATA.retro[idx];
  const view = goCurrentView();
  const jr = view.jr;
  const dateShown = new Date(GO_DATA.start + 'T00:00:00');
  dateShown.setDate(dateShown.getDate() + idx);
  const occupants = jr !== null ? goOccupants(row, jr) : null;
  const verdictOf = gi => {
    if (jr === null) return null;
    return goVerdict(row, gi, jr, occupants);
  };
  renderShaniCondition(row, jr);
  renderTransitChart(row, retro, view, dateShown, verdictOf, idx);

  renderUpcomingMoves(idx);

  renderPhalalu(jr, row, view);
  renderGocharaLegend(jr);
}

const HOUSE_MEANINGS = { 1:'self and health', 2:'wealth and family', 3:'courage and effort',
  4:'home and comfort', 5:'children and learning', 6:'health and rivals', 7:'partnerships',
  8:'obstacles', 9:'fortune and dharma', 10:'career and standing', 11:'gains and income', 12:'expenses and rest' };
const PHALALU_OPENERS = {
  good: 'The Moon stands well for your rashi today — a day that supports initiative.',
  puja: "The Moon's position asks for a small remedial prayer; proceed gently after it.",
  bad: 'The Moon sits heavily for your rashi today — keep the day light and routine.' };
const PHALALU_ORDER = ['Shani','Guru','Rahu','Ketu','Kuja','Surya','Shukra','Budha'];
const ordinal = n => n + (['st','nd','rd'][n-1] || 'th');

function detailedVerdict(row, grahaIndex, reference, occupants) {
  const graha = GO_DATA.grahas[grahaIndex];
  const position = goHouseFrom(row, grahaIndex, reference);
  if (!GO_FAV[graha].includes(position)) return { v: 'adverse' };
  if (GO_NODES.has(graha)) return { v: 'favourable' };
  const vedhaHouse = GO_VEDHA[graha][position];
  for (const other of (occupants[vedhaHouse] || [])) {
    const isVedha = other !== graha
      && !GO_NODES.has(other)
      && !GO_EXEMPT.has(`${graha}|${other}`);
    if (isVedha) return { v: 'blocked', by: other };
  }
  return { v: 'favourable' };
}

function moonVerdict(moonPosition) {
  if (CHANDRA_GOOD.has(moonPosition)) return 'good';
  if (CHANDRA_PUJA.has(moonPosition)) return 'puja';
  return 'bad';
}

function phalaluQuality(moon, favourableCount) {
  if (moon === 'good' && favourableCount >= 4) return 'good';
  if (moon === 'bad' && favourableCount <= 2) return 'difficult';
  return 'mixed';
}

function phalaluDetailLine(graha, detail) {
  const meaning = HOUSE_MEANINGS[detail.posR];
  if (detail.v === 'favourable') {
    return `${graha} in your ${ordinal(detail.posR)} house favours ${meaning}.`;
  }
  if (detail.v === 'blocked') {
    return `${graha}'s good ${ordinal(detail.posR)}-house transit is under vedha by ${detail.by} — ${meaning} may face friction.`;
  }
  return `${graha} in the ${ordinal(detail.posR)} house tests ${meaning}; avoid forcing matters there.`;
}

function buildPhalalu(jr, row) {
  // Daily Horoscope is a single-reference Janma-Rashi computation.
  const occupants = goOccupants(row, jr);
  const houseFromRef = (grahaIndex, reference) => goHouseFrom(row, grahaIndex, reference);
  const houseOf = gi => houseFromRef(gi, jr);
  const moonPos = houseOf(GO_DATA.grahas.indexOf('Chandra'));
  const mv = moonVerdict(moonPos);
  let fav = 0, blocked = 0;
  const detail = {};
  GO_DATA.grahas.forEach((g, gi) => {
    const r = detailedVerdict(row, gi, jr, occupants);
    detail[g] = { ...r, posR: houseOf(gi) };
    if (r.v === 'favourable') fav++; else if (r.v === 'blocked') blocked++;
  });
  const quality = phalaluQuality(mv, fav);
  const opener = PHALALU_OPENERS[mv];

  // Named Shani conditions are Moon-sign constructs.
  const shaniIdx = GO_DATA.grahas.indexOf('Shani');
  const condition = shaniConditionFromMoonHouse(houseFromRef(shaniIdx, jr));
  const conditionLine = condition ? shaniConditionLine(condition) : null;
  const detailLines = PHALALU_ORDER.map(graha => phalaluDetailLine(graha, detail[graha]));
  const blockedSummary = blocked ? `, ${blocked} under vedha` : '';
  const summary = `${fav} of 9 grahas favour you today${blockedSummary} (from your Janma Rashi).`;
  return {
    quality,
    opener,
    condition: conditionLine,
    detailLines,
    summary,
    lines: [opener, ...(conditionLine ? [conditionLine] : []), ...detailLines, summary],
  };
}

function gocharaShareIdentity(jr, ph) {
  const lines = [];
  // Saved profile names and birth details are intentionally omitted.
  lines.push(`${RASI_NAMES[jr]} Janma Rashi · ${ph.quality} day`);
  return lines;
}

function shareGocharaOnWhatsApp() {
  if (!GO_DATA) return;
  const view = goCurrentView();
  if (view.jr === null) return;
  const jr = view.jr;
  const idx = goDateIndex();
  const row = GO_DATA.days[idx];
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const ph = buildPhalalu(jr, row);
  const shown = new Date(GO_DATA.start + 'T00:00:00'); shown.setDate(shown.getDate() + idx);
  const lines = [
    `📜 *Rasi Phalalu — ${fmtD(shown)}*`,
    ...gocharaShareIdentity(jr, ph),
    '',
    ...ph.lines.map(line => `• ${line}`),
    '',
    'Check your rashi:',
    'https://panchangam.astrochaganti.com/?src=share-phalalu#gochara',
  ];
  gcEvent('share-phalalu');
  window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
}

export { loadGochara, renderGochara, goBuildViewSelect, shareGocharaOnWhatsApp };
export function goHasData() { return !!GO_DATA; }
