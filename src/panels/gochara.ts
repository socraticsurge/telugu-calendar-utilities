// typing lands with the component rewrite, not the move.
//
// Gochara panel: transit chart, vedha screening, and the daily
// LLM/deterministic rasi phalalu reading.

import { fmtT, fmtRange } from '../lib/format';
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
  const requestedProfileId = profileIdFromSelection(resolution.requestedValue);
  const requestedProfile = requestedProfileId
    ? profiles.find(profile => profile.id === requestedProfileId) || null
    : null;

  const addNotice = (message: string): void => {
    const notice = document.createElement('p');
    notice.className = 'go-profile-notice';
    notice.setAttribute('role', 'status');
    notice.textContent = message;
    root.append(notice);
  };
  const addContext = (message: string): void => {
    const context = document.createElement('p');
    context.className = 'go-profile-context';
    context.textContent = message;
    root.append(context);
  };
  const addActions = (...buttons: HTMLButtonElement[]): void => {
    if (!buttons.length) return;
    const actions = document.createElement('div');
    actions.className = 'go-profile-actions';
    actions.append(...buttons);
    root.append(actions);
  };
  const addIncompleteProfileActions = (excludeId: string | null = null): void => {
    if (!gocharaProfileActions) return;
    const buttons = profiles.flatMap(profile => {
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
    addActions(...buttons);
  };
  const restoreActionFocus = (): void => {
    if (!focusKey) return;
    const replacement = Array.from(
      root.querySelectorAll<HTMLElement>('[data-go-profile-focus]'),
    ).find(candidate => candidate.dataset.goProfileFocus === focusKey);
    replacement?.focus();
  };

  if (resolution.fallback) addNotice(resolution.fallback.message);
  if (
    !resolution.fallback &&
    (selectionStorageUnavailable || snapshot?.persistence === 'memory')
  ) {
    addNotice('Your horoscope choice works for this page, but this browser cannot save it.');
  }

  if (requestedProfile && resolution.fallback?.code === 'profile-not-horoscope-ready') {
    const missing = resolution.fallback.missingField === 'pada' ? 'Padam' : 'Nakshatra';
    addContext(`Add ${missing} to ${profileDisplayName(requestedProfile)} before using this profile here.`);
    if (gocharaProfileActions) {
      addActions(
        stateAction(
          `Complete ${profileDisplayName(requestedProfile)}`,
          'edit',
          trigger => gocharaProfileActions?.editProfile(requestedProfile.id, trigger),
          true,
          requestedProfile.id,
        ),
        stateAction('Manage profiles', 'manage', trigger => gocharaProfileActions?.manageProfiles(trigger)),
      );
    }
    addIncompleteProfileActions(requestedProfile.id);
    restoreActionFocus();
    return;
  }

  if (resolution.kind === 'profile' && resolution.profile) {
    addContext(`Using ${resolution.profile.name || 'this profile'}'s saved birth star for this Daily Horoscope.`);
    if (gocharaProfileActions) {
      addActions(
        stateAction(
          `Edit ${resolution.profile.name || 'profile'}`,
          'edit',
          trigger => gocharaProfileActions?.editProfile(resolution.profile!.id, trigger),
          false,
          resolution.profile.id,
        ),
        stateAction('Manage profiles', 'manage', trigger => gocharaProfileActions?.manageProfiles(trigger)),
      );
    }
    addIncompleteProfileActions();
    restoreActionFocus();
    return;
  }

  if (profiles.length === 0) {
    addContext('Create a profile to reuse a birth star here and in Muhurtam. It stays only in this browser.');
    if (gocharaProfileActions) {
      addActions(stateAction('Create profile', 'create', trigger => gocharaProfileActions?.createProfile(trigger), true));
    }
    restoreActionFocus();
    return;
  }

  if (resolution.kind === 'rashi') {
    addContext('This is a one-off Rashi view. Choose a saved profile above to return to a personal horoscope faster.');
  } else {
    addContext('Choose a saved profile above for a personal Daily Horoscope, or select any Rashi for a one-off view.');
  }
  if (gocharaProfileActions) {
    addActions(stateAction('Manage profiles', 'manage', trigger => gocharaProfileActions?.manageProfiles(trigger)));
  }
  addIncompleteProfileActions();
  restoreActionFocus();
}

async function loadGochara() {
  const firstLoad = !GO_DATA;
  if (firstLoad) {
    try {
      const r = await fetch('gochara.json', { cache: 'no-cache' });
      GO_DATA = await r.json();
    } catch (e) {
      document.getElementById('go-chart').innerHTML =
        '<p class="preview-error">Sky data unavailable — try again later.</p>';
      return;
    }
    // date input removed — always show today

    // Fetch today's LLM-generated phalalu — silently skip if unavailable
    try {
      const d = new Date();
      const todayISO = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      const pr = await fetch(`rasi_phalalu/${todayISO}.json`, { cache: 'no-cache' });
      if (pr.ok) LLM_PHALALU = await pr.json();
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
    if (!v || !v.nak) return null;
    const rasi = rasiFromStar(v.nak, Number(v.pada) || null);
    if (!rasi) return null;
    // Janma lagna is optional — only surfaced as a separate view
    // option when the user has filled it on the Tarabalam profile.
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
  let selectionStorageUnavailable = false;
  let resolution: GocharaSelectionResolution;

  if (preferredValue === undefined && !hadOptions) {
    const loaded = loadGocharaSelection(goSelectionStorage(), snapshot.profiles);
    resolution = loaded;
    selectionStorageUnavailable = loaded.storageIssue === 'storage-unavailable';
  } else {
    const requestedValue = preferredValue === undefined ? sel.value : preferredValue;
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
      const jl = resolved.profile.lagna
        ? RASI_NAMES.indexOf(resolved.profile.lagna)
        : null;
      const refLabel = resolved.profile.lagna
        ? `${resolved.profile.rasi} rashi + ${resolved.profile.lagna} lagna (${resolved.profile.name})`
        : `${resolved.profile.rasi} rashi (${resolved.profile.name})`;
      return { jr, jl, label: refLabel };
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
  // 'p<i>' — profile-keyed combined view. We carry BOTH the rashi
  // index (jr, used to lay out the chart and number houses) AND the
  // optional lagna index (jl, used as a second reference for graha
  // verdicts and the conditions banner).
  const profMatch = val.match(/^p(\d+)$/);
  if (profMatch) {
    const k = goSavedPeople()[Number(profMatch[1])];
    if (!k) return { jr: null, jl: null, label: null };
    const jr = RASI_NAMES.indexOf(k.rasi);
    const jl = k.lagna ? RASI_NAMES.indexOf(k.lagna) : null;
    const refLabel = k.lagna
      ? `${k.rasi} rashi + ${k.lagna} lagna (${k.name})`
      : `${k.rasi} rashi (${k.name})`;
    return { jr, jl, label: refLabel };
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

function renderGochara() {
  // A denied browser-storage write must never prevent the chart from rendering.
  persistGocharaSelection(selEl('go-view').value);
  if (!GO_DATA) return;
  const idx = goDateIndex();
  const row = GO_DATA.days[idx], retro = GO_DATA.retro[idx];
  const view = goCurrentView();
  const jr = view.jr;
  const jl = (typeof view.jl === 'number') ? view.jl : null;
  const dateShown = new Date(GO_DATA.start + 'T00:00:00');
  dateShown.setDate(dateShown.getDate() + idx);
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });

  // Per-graha verdicts using a chosen reference index (rashi index
  // 0..11). Works for both janma rashi and janma lagna — same
  // Janma-Chandra transit frame. Brihat Samhita 104.4 supports the seven
  // classical favourable-house sets; Vedha and node policy are separate.
  const houseFrom = (gi, ref) => ((row[gi] - ref + 12) % 12) + 1;
  const occupantsFor = (ref) => {
    const o = {};
    GO_DATA.grahas.forEach((g, gi) => {
      const h = houseFrom(gi, ref);
      (o[h] = o[h] || []).push(g);
    });
    return o;
  };
  const verdictFrom = (gi, ref, occ) => {
    const g = GO_DATA.grahas[gi], pos = houseFrom(gi, ref);
    if (!GO_FAV[g].includes(pos)) return 'bad';
    if (!GO_NODES.has(g)) {
      const vh = GO_VEDHA[g][pos];
      for (const other of (occ[vh] || [])) {
        if (other !== g && !GO_NODES.has(other) && !GO_EXEMPT.has(g + '|' + other)) return 'blocked';
      }
    }
    return 'good';
  };

  // Pre-compute occupants for each reference we'll use.
  const occRashi = (jr !== null) ? occupantsFor(jr) : null;
  const occLagna = (jl !== null) ? occupantsFor(jl) : null;

  // House numbering for the chart stays anchored to janma RASHI —
  // that's what users have always seen. The lagna lens is an extra
  // verdict layer, not a chart re-anchoring.
  const houseOf = gi => jr === null ? null : houseFrom(gi, jr);

  // Chart colour is anchored to the janma RASHI verdict — the
  // traditional Janma-Chandra gochara frame. The lagna lens is
  // surfaced separately (tooltip + prose) without judgement;
  // classical texts don't prescribe a single rule for merging the
  // two into one verdict, so we don't invent one.
  const verdictOf = gi => {
    if (jr === null) return null;
    return verdictFrom(gi, jr, occRashi);
  };
  const verdictsBoth = gi => {
    if (jr === null) return null;
    const vr = verdictFrom(gi, jr, occRashi);
    const vl = (jl !== null) ? verdictFrom(gi, jl, occLagna) : null;
    return { vr, vl };
  };

  // Named Shani conditions are reckoned only from Janma Chandra. Lagna can be
  // a useful second lens for ordinary gochara, but it does not define Sade Sati.
  const condBox = document.getElementById('go-conditions');
  const shaniIdx = GO_DATA.grahas.indexOf('Shani');
  const conds = [];
  if (jr !== null) {
    const condition = shaniConditionFromMoonHouse(houseFrom(shaniIdx, jr));
    if (condition) conds.push(`${condition} — from Moon sign`);
  }
  condBox.innerHTML = conds.length
    ? `<div class="go-cond">${conds.map(c => `<span class="chip">⚠️ ${htmlEsc(c)}</span>`).join('')}
       <div class="tb-sub" style="margin-top:0.25rem;">Running ${conds[0].split(' — ')[0].split(' (')[0]}? Personalised guidance:
       <a href="https://astrochaganti.com" target="_blank" rel="noopener" style="color:var(--indigo);font-weight:600;">astrochaganti.com</a></div></div>` : '';

  // chart
  const byRasi = {};
  GO_DATA.grahas.forEach((g, gi) => { (byRasi[row[gi]] = byRasi[row[gi]] || []).push(gi); });
  const ord = n => `${n}${['st','nd','rd'][n-1] || 'th'}`;
  const verdictLabel = v => v === 'good' ? 'favourable' : v === 'blocked' ? 'vedha' : 'adverse';
  let boxes = '';
  for (let r = 0; r < 12; r++) {
    const [gr, gc] = GO_LAYOUT[r];
    const grahas = (byRasi[r] || []).map(gi => {
      const v = verdictOf(gi);
      const both = verdictsBoth(gi);
      const t = goTill(idx, gi);
      // Tooltip surfaces BOTH references when lagna is set so the
      // user can see exactly why a combined verdict landed where it
      // did (e.g. "good from rashi · adverse from lagna" → adverse).
      let perRef = '';
      if (both) {
        const hr = houseFrom(gi, jr);
        const partR = `${ord(hr)} from rashi (${verdictLabel(both.vr)})`;
        if (both.vl !== null) {
          const hl = houseFrom(gi, jl);
          perRef = ` — ${partR} · ${ord(hl)} from lagna (${verdictLabel(both.vl)})`;
        } else {
          perRef = ` — ${partR}`;
        }
      }
      const tip = `${GO_DATA.grahas[gi]} in ${GO_DATA.rasis[r]}${perRef}` +
        (t ? ` · till ${t.date.toLocaleDateString('en-US',{month:'short',day:'numeric'})}` : '');
      return `<span class="go-g ${v || ''}" title="${htmlEsc(tip)}">${GO_DATA.grahas[gi]}${retro[gi] ? '<span class="go-retro">℞</span>' : ''}</span>`;
    }).join('');
    const house = jr !== null ? `<span class="house">${((r - jr + 12) % 12) + 1}</span>` : '';
    // Highlight both natal cells when known. When they coincide
    // (janma rashi == janma lagna) we render a single combined
    // label rather than 'janma · lagna' which would look odd.
    const isJanma = (jr === r);
    const isLagna = (jl !== null && jl === r);
    const classes = ['go-box'];
    if (isJanma) classes.push('janma');
    if (isLagna) classes.push('lagna');
    let label = '';
    if (isJanma && isLagna) label = ' · janma + lagna';
    else if (isJanma) label = ' · janma';
    else if (isLagna) label = ' · lagna';
    boxes += `<div class="${classes.join(' ')}" style="grid-row:${gr};grid-column:${gc};">
      <span class="rname">${GO_DATA.rasis[r]}${label}</span>${house}<br>${grahas}</div>`;
  }
  document.getElementById('go-note').innerHTML = '';
  const center = `<div class="go-center"><div class="d1">🪐 Gochara</div>
    <div class="d2">${fmtD(dateShown)}</div>
    <div class="d2">${jr !== null ? 'from ' + htmlEsc(view.label) : 'transits — choose a person or rashi above to personalise'}</div></div>`;
  document.getElementById('go-chart').innerHTML = boxes + center;

  // upcoming moves — fast planets only (Moon, Mercury, Sun change frequently enough to matter)
  const GO_FAST = new Set(['Chandra', 'Budha', 'Surya']);
  const moves = GO_DATA.grahas.map((g, gi) => ({ g, t: goTill(idx, gi) }))
    .filter(m => m.t && GO_FAST.has(m.g)).sort((a, b) => a.t.date - b.t.date);
  document.getElementById('go-moves').innerHTML = moves.length
    ? `<div class="go-moves"><b>Coming up:</b> ` + moves.map(m =>
        `<span class="go-move">${m.g} → ${m.t.next} <b>${m.t.date.toLocaleDateString('en-US',{month:'short',day:'numeric'})}</b></span>`)
        .join('<span class="go-move-sep"> &nbsp;·&nbsp; </span>') + `</div>` : '';

  // rasi phalalu
  const phBox = document.getElementById('go-phalalu');
  if (jr === null) { phBox.innerHTML = ''; }
  else {
    const ph = buildPhalalu(jr, jl, row, view, idx);
    const phShare = `<button class="wa-share-mini go-phalalu-share" title="Share this reading on WhatsApp" aria-label="Share on WhatsApp" onclick="shareGocharaOnWhatsApp()"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg></button>`;
    const llmRasiKey = view.label.replace(/ (rashi|lagna)$/i, '').trim();
    const llmEntry = LLM_PHALALU?.rashis?.[llmRasiKey];
    const llmForToday = !!llmEntry;
    const interpretationBoundary = llmForToday
      ? `<p style="font-size:0.72rem;color:#746B5E;margin-top:0.65rem;">AI-written interpretation: cited transit positions and verdicts are engine-checked; prose and guidance are interpretive, not independently scripturally verified.</p>`
      : '';
    const adviceBlock = llmForToday && llmEntry.advice
      ? `<div style="margin-top:0.65rem;padding:0.5rem 0.65rem;background:#FFF8ED;border-left:3px solid var(--amber);border-radius:0 6px 6px 0;">` +
        `<span style="font-size:0.68rem;color:#8B7355;text-transform:uppercase;letter-spacing:0.05em;font-weight:600;display:block;margin-bottom:0.2rem;">Today's guidance</span>` +
        `<span style="font-size:0.84rem;color:#44403c;line-height:1.5;">${htmlEsc(llmEntry.advice)}</span></div>`
      : '';
    phBox.innerHTML = `<div class="go-phalalu"><h4 class="go-phalalu-heading"><span class="go-phalalu-title">Rasi Phalalu — ${htmlEsc(view.label)}</span>
      <span class="go-quality ${ph.quality}">${ph.quality} day</span>${phShare}</h4>` +
      (llmForToday
        ? `<p>${htmlEsc(llmEntry.text)}</p>${adviceBlock}${interpretationBoundary}`
        : ph.lines.map(l => `<p>${l}</p>`).join('') +
          `<p style="font-size:0.72rem;color:#746B5E;">Every line above is rendered from the chart's computed verdicts — nothing is invented.</p>`) +
      `</div>`;
  }

  // legend
  document.getElementById('go-legend').innerHTML = jr === null ? '' :
    `<div class="tb-legend" style="margin-top:0.5rem;">
      <span class="tb-legend-item"><span class="go-g good">favourable</span></span>
      <span class="tb-legend-item"><span class="go-g blocked">blocked by vedha</span></span>
      <span class="tb-legend-item"><span class="go-g bad">adverse</span></span>
      <span class="tb-legend-item"><span class="go-g">℞ retrograde</span></span>
      </div>`;
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

function buildPhalalu(jr, jl, row, view, idx) {
  // Two independent verdicts per graha — one from each reference.
  // No "combine into one" judgement; classical Jyotisha doesn't
  // prescribe a merge rule, so we surface both lenses side by side
  // when janma lagna is set. Chart colour and the count tally
  // stay anchored to janma rashi (matches the chart visual).
  const houseFromRef = (gi, ref) => ((row[gi] - ref + 12) % 12) + 1;
  const occFor = (ref) => {
    const o = {};
    GO_DATA.grahas.forEach((g, gi) => {
      const h = houseFromRef(gi, ref);
      (o[h] = o[h] || []).push(g);
    });
    return o;
  };
  const verdictForRef = (gi, ref, occ) => {
    const g = GO_DATA.grahas[gi], pos = houseFromRef(gi, ref);
    if (!GO_FAV[g].includes(pos)) return { v: 'adverse' };
    if (!GO_NODES.has(g)) {
      const vh = GO_VEDHA[g][pos];
      for (const other of (occ[vh] || [])) {
        if (other !== g && !GO_NODES.has(other) && !GO_EXEMPT.has(g + '|' + other)) return { v: 'blocked', by: other };
      }
    }
    return { v: 'favourable' };
  };
  const occR = occFor(jr);
  const occL = (jl !== null) ? occFor(jl) : null;
  const houseOf = gi => houseFromRef(gi, jr);     // chart anchor stays rashi
  const moonPos = houseOf(GO_DATA.grahas.indexOf('Chandra'));
  const mv = CHANDRA_GOOD.has(moonPos) ? 'good' : (CHANDRA_PUJA.has(moonPos) ? 'puja' : 'bad');
  let fav = 0, blocked = 0;
  const detail = {};
  GO_DATA.grahas.forEach((g, gi) => {
    // Rashi verdict drives the tally (and the chart colours).
    const r = verdictForRef(gi, jr, occR);
    const l = (occL !== null) ? verdictForRef(gi, jl, occL) : null;
    detail[g] = { ...r, lagna: l, posR: houseOf(gi),
                  posL: (jl !== null) ? houseFromRef(gi, jl) : null };
    if (r.v === 'favourable') fav++; else if (r.v === 'blocked') blocked++;
  });
  const quality = (mv === 'good' && fav >= 4) ? 'good' : (mv === 'bad' && fav <= 2) ? 'difficult' : 'mixed';
  const lines = [PHALALU_OPENERS[mv]];

  // Named Shani conditions are Moon-sign constructs, even when the chart also
  // displays lagna as a secondary reference for ordinary transit verdicts.
  const shaniIdx = GO_DATA.grahas.indexOf('Shani');
  const condition = shaniConditionFromMoonHouse(houseFromRef(shaniIdx, jr));
  if (condition) lines.push(shaniConditionLine(condition));

  const verdictClause = (v, pos, m) => v === 'favourable' ? `favours ${m}`
    : v === 'blocked' ? `is under vedha — ${m} arrives with friction`
    : `tests ${m}; don't force matters there`;
  for (const g of PHALALU_ORDER) {
    const d = detail[g];
    if (d.lagna === null) {
      const m = HOUSE_MEANINGS[d.posR];
      lines.push(d.v === 'favourable' ? `${g} in your ${ordinal(d.posR)} house favours ${m}.`
        : d.v === 'blocked' ? `${g}'s good ${ordinal(d.posR)}-house transit is under vedha by ${d.by} — gains in ${m} may arrive with friction.`
        : `${g} in the ${ordinal(d.posR)} house tests ${m}; avoid forcing matters there.`);
      continue;
    }
    // Both lenses set. If they agree, one clean line. If they
    // differ, two clauses: "X from your rashi … and from your lagna …".
    const mR = HOUSE_MEANINGS[d.posR];
    const mL = HOUSE_MEANINGS[d.posL];
    if (d.v === d.lagna.v && d.posR === d.posL) {
      // Same house, same verdict → one line.
      lines.push(`${g} in your ${ordinal(d.posR)} house ${verdictClause(d.v, d.posR, mR)}.`);
    } else {
      lines.push(`${g}: from your rashi, ${ordinal(d.posR)} house — ${verdictClause(d.v, d.posR, mR)}; from your lagna, ${ordinal(d.posL)} house — ${verdictClause(d.lagna.v, d.posL, mL)}.`);
    }
  }
  lines.push(`${fav} of 9 grahas favour you today${blocked ? `, ${blocked} under vedha` : ''} (from your rashi).`);
  return { quality, lines };
}

function shareGocharaOnWhatsApp() {
  if (!GO_DATA) return;
  const view = goCurrentView();
  if (view.jr === null) return;
  const jr = view.jr;
  const jl = (typeof view.jl === 'number') ? view.jl : null;
  const idx = goDateIndex();
  const row = GO_DATA.days[idx], retro = GO_DATA.retro[idx];
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const ord = n => n + (['st','nd','rd'][n-1] || 'th');
  const ph = buildPhalalu(jr, jl, row, view, idx);
  const lines = [];
  const shown = new Date(GO_DATA.start + 'T00:00:00'); shown.setDate(shown.getDate() + idx);
  lines.push(`📜 *Rasi Phalalu — ${fmtD(shown)}*`);
  lines.push(`${view.label} · ${ph.quality} day`);
  lines.push('');
  ph.lines.forEach(l => lines.push('• ' + l));
  lines.push('');
  lines.push('Check your rashi:');
  lines.push('https://panchangam.astrochaganti.com/?src=share-phalalu#gochara');
  gcEvent('share-phalalu');
  window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
}

export { loadGochara, renderGochara, goBuildViewSelect, shareGocharaOnWhatsApp };
export function goHasData() { return !!GO_DATA; }
