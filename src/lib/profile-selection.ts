import {
  MAX_GUEST_PROFILES,
  guestProfileReadiness,
  type GuestProfile,
  type ProfilePersistence,
  type ProfileStorage,
} from './guest-profile-store';

export const GOCHARA_SELECTION_STORAGE_KEY = 'tc-go-view';
export const MUHURTAM_PROFILE_IDS_STORAGE_KEY = 'tc-mu-profile-ids';

export type GocharaSelectionValue = '' | `${number}` | `profile:${string}`;
export type GocharaSelectionKind = 'whole-sky' | 'rashi' | 'profile';
export type GocharaFallbackCode =
  | 'invalid-selection'
  | 'profile-deleted'
  | 'profile-not-horoscope-ready'
  | 'storage-unavailable';

export interface ProfileSelectionFallback {
  code: GocharaFallbackCode;
  message: string;
  missingField?: 'nakshatra' | 'pada';
}

/**
 * The deliberately small shape consumed by the existing Gochara and Muhurtam
 * panels. Profile identity stays stable while the legacy field names remain
 * available to the calculation code.
 */
export interface JourneyGuestProfile {
  id: string;
  name: string;
  nak: string;
  pada: 1 | 2 | 3 | 4 | null;
  rasi: string | null;
  lagna: string | null;
}

export interface GocharaSelectionResolution {
  requestedValue: string | null;
  value: GocharaSelectionValue;
  kind: GocharaSelectionKind;
  profile: JourneyGuestProfile | null;
  rasiIndex: number | null;
  legacySelectionDetected: boolean;
  migratedFromLegacy: boolean;
  fallback: ProfileSelectionFallback | null;
}

export interface LoadedGocharaSelection extends GocharaSelectionResolution {
  persistence: ProfilePersistence;
  storageIssue: 'storage-unavailable' | null;
}

export type MuhurtamDroppedReason =
  | 'deleted'
  | 'not-muhurta-ready'
  | 'selection-limit';
export type MuhurtamSelectionIssue =
  | 'selection-limit'
  | 'profile-deleted'
  | 'profile-not-muhurta-ready'
  | null;
export type SelectionStorageIssue =
  | 'malformed-storage'
  | 'storage-unavailable'
  | null;

export interface DroppedMuhurtamProfile {
  id: string;
  reason: MuhurtamDroppedReason;
}

export interface MuhurtamProfileSelection {
  selectedIds: string[];
  profiles: JourneyGuestProfile[];
  initializedFromProfiles: boolean;
  dropped: DroppedMuhurtamProfile[];
  selectionIssue: MuhurtamSelectionIssue;
  storageIssue: SelectionStorageIssue;
  persistence: ProfilePersistence;
  message: string | null;
}

interface ResolvedMuhurtamIds {
  selectedIds: string[];
  profiles: JourneyGuestProfile[];
  dropped: DroppedMuhurtamProfile[];
  selectionIssue: MuhurtamSelectionIssue;
}

const LEGACY_GOCHARA_SELECTION = /^p(\d+)(?:[rl])?$/;
const PROFILE_GOCHARA_SELECTION = /^profile:(.+)$/;
const ANY_RASI_SELECTION = /^(?:[0-9]|1[01])$/;

export function adaptGuestProfile(profile: GuestProfile): JourneyGuestProfile {
  return {
    id: profile.id,
    name: profile.name,
    nak: profile.nakshatra || '',
    pada: profile.pada,
    rasi: guestProfileReadiness(profile).janmaRasi,
    lagna: profile.lagna,
  };
}

export function gocharaProfileValue(id: string): `profile:${string}` {
  return `profile:${id}`;
}

function wholeSky(
  requestedValue: string | null,
  fallback: ProfileSelectionFallback | null = null,
  legacySelectionDetected = false,
): GocharaSelectionResolution {
  return {
    requestedValue,
    value: '',
    kind: 'whole-sky',
    profile: null,
    rasiIndex: null,
    legacySelectionDetected,
    migratedFromLegacy: false,
    fallback,
  };
}

function missingProfileFallback(): ProfileSelectionFallback {
  return {
    code: 'profile-deleted',
    message: 'That saved profile is no longer available. Showing whole-sky transits.',
  };
}

function incompleteProfileFallback(profile: GuestProfile): ProfileSelectionFallback {
  const readiness = guestProfileReadiness(profile);
  const missingField = readiness.missingForHoroscope || 'nakshatra';
  const requirement = missingField === 'pada'
    ? 'Padam is needed because this birth star spans two Rashis.'
    : 'A birth star is needed for a personal horoscope.';
  return {
    code: 'profile-not-horoscope-ready',
    missingField,
    message: `${requirement} Showing whole-sky transits.`,
  };
}

/**
 * Resolve a Gochara selection without touching storage or the DOM.
 *
 * Legacy pN/pNr/pNl values intentionally use the stored profile index once,
 * then callers persist the returned stable profile:<id> value. We do not bind
 * an old index to a different person when that exact row is incomplete.
 */
export function resolveGocharaSelection(
  rawValue: unknown,
  profiles: ReadonlyArray<Readonly<GuestProfile>>,
): GocharaSelectionResolution {
  const requestedValue = rawValue === null || rawValue === undefined
    ? null
    : String(rawValue);

  if (requestedValue === null || requestedValue === '') {
    return wholeSky(requestedValue);
  }

  if (ANY_RASI_SELECTION.test(requestedValue)) {
    return {
      requestedValue,
      value: requestedValue as `${number}`,
      kind: 'rashi',
      profile: null,
      rasiIndex: Number(requestedValue),
      legacySelectionDetected: false,
      migratedFromLegacy: false,
      fallback: null,
    };
  }

  const stableMatch = requestedValue.match(PROFILE_GOCHARA_SELECTION);
  if (stableMatch) {
    const profile = profiles.find(candidate => candidate.id === stableMatch[1]);
    if (!profile) return wholeSky(requestedValue, missingProfileFallback());
    if (!guestProfileReadiness(profile).horoscope) {
      return wholeSky(requestedValue, incompleteProfileFallback(profile));
    }
    return {
      requestedValue,
      value: gocharaProfileValue(profile.id),
      kind: 'profile',
      profile: adaptGuestProfile(profile),
      rasiIndex: null,
      legacySelectionDetected: false,
      migratedFromLegacy: false,
      fallback: null,
    };
  }

  const legacyMatch = requestedValue.match(LEGACY_GOCHARA_SELECTION);
  if (legacyMatch) {
    const profile = profiles[Number(legacyMatch[1])];
    if (!profile) {
      return wholeSky(requestedValue, missingProfileFallback(), true);
    }
    if (!guestProfileReadiness(profile).horoscope) {
      return wholeSky(requestedValue, incompleteProfileFallback(profile), true);
    }
    return {
      requestedValue,
      value: gocharaProfileValue(profile.id),
      kind: 'profile',
      profile: adaptGuestProfile(profile),
      rasiIndex: null,
      legacySelectionDetected: true,
      migratedFromLegacy: true,
      fallback: null,
    };
  }

  return wholeSky(requestedValue, {
    code: 'invalid-selection',
    message: 'The saved horoscope view could not be restored. Showing whole-sky transits.',
  });
}

/** Read, resolve, and one-time migrate the Gochara preference safely. */
export function loadGocharaSelection(
  storage: ProfileStorage,
  profiles: ReadonlyArray<Readonly<GuestProfile>>,
): LoadedGocharaSelection {
  let rawValue: string | null;
  try {
    rawValue = storage.getItem(GOCHARA_SELECTION_STORAGE_KEY);
  } catch {
    return {
      ...wholeSky(null, {
        code: 'storage-unavailable',
        message: 'Saved view preferences are unavailable. Showing whole-sky transits.',
      }),
      persistence: 'memory',
      storageIssue: 'storage-unavailable',
    };
  }

  const resolved = resolveGocharaSelection(rawValue, profiles);
  let persistence: ProfilePersistence = 'persistent';
  let storageIssue: LoadedGocharaSelection['storageIssue'] = null;

  // A successful legacy migration and every stale/invalid fallback are made
  // one-time by replacing the fragile value. A missing key stays missing.
  if (rawValue !== null && rawValue !== resolved.value) {
    try {
      storage.setItem(GOCHARA_SELECTION_STORAGE_KEY, resolved.value);
    } catch {
      persistence = 'memory';
      storageIssue = 'storage-unavailable';
    }
  }

  return { ...resolved, persistence, storageIssue };
}

function resolveMuhurtamIds(
  requestedIds: readonly unknown[],
  profiles: ReadonlyArray<Readonly<GuestProfile>>,
): ResolvedMuhurtamIds {
  const profileById = new Map(profiles.map(profile => [profile.id, profile]));
  const selectedIds: string[] = [];
  const selectedProfiles: JourneyGuestProfile[] = [];
  const dropped: DroppedMuhurtamProfile[] = [];
  const seen = new Set<string>();
  let selectionIssue: MuhurtamSelectionIssue = null;

  for (const candidate of requestedIds) {
    if (typeof candidate !== 'string' || candidate === '' || seen.has(candidate)) continue;
    seen.add(candidate);
    const profile = profileById.get(candidate);
    if (!profile) {
      dropped.push({ id: candidate, reason: 'deleted' });
      if (!selectionIssue) selectionIssue = 'profile-deleted';
      continue;
    }
    if (!guestProfileReadiness(profile).muhurta) {
      dropped.push({ id: candidate, reason: 'not-muhurta-ready' });
      if (!selectionIssue) selectionIssue = 'profile-not-muhurta-ready';
      continue;
    }
    if (selectedIds.length >= MAX_GUEST_PROFILES) {
      dropped.push({ id: candidate, reason: 'selection-limit' });
      selectionIssue = 'selection-limit';
      continue;
    }
    selectedIds.push(candidate);
    selectedProfiles.push(adaptGuestProfile(profile));
  }

  return {
    selectedIds,
    profiles: selectedProfiles,
    dropped,
    selectionIssue,
  };
}

function selectionMessage(
  selectionIssue: MuhurtamSelectionIssue,
  storageIssue: SelectionStorageIssue,
  initializedFromProfiles: boolean,
): string | null {
  if (storageIssue === 'storage-unavailable') {
    return 'Profile choices work for this page, but this browser cannot save them.';
  }
  if (storageIssue === 'malformed-storage') {
    return 'Saved Muhurtam choices were unreadable and have been reset safely.';
  }
  if (selectionIssue === 'selection-limit') {
    return `Choose up to ${MAX_GUEST_PROFILES} profiles for one Muhurtam search.`;
  }
  if (selectionIssue === 'profile-deleted') {
    return 'A previously selected profile no longer exists and was removed from this search.';
  }
  if (selectionIssue === 'profile-not-muhurta-ready') {
    return 'A selected profile needs a birth star before it can be used for Muhurtam.';
  }
  if (initializedFromProfiles) {
    return 'Your existing Muhurtam-ready profiles have been selected for this search.';
  }
  return null;
}

function persistMuhurtamIds(
  storage: ProfileStorage,
  selectedIds: readonly string[],
): 'storage-unavailable' | null {
  try {
    storage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, JSON.stringify(selectedIds));
    return null;
  } catch {
    return 'storage-unavailable';
  }
}

function asMuhurtamSelection(
  resolved: ResolvedMuhurtamIds,
  initializedFromProfiles: boolean,
  storageIssue: SelectionStorageIssue,
): MuhurtamProfileSelection {
  return {
    ...resolved,
    initializedFromProfiles,
    storageIssue,
    persistence: storageIssue === 'storage-unavailable' ? 'memory' : 'persistent',
    message: selectionMessage(
      resolved.selectionIssue,
      storageIssue,
      initializedFromProfiles,
    ),
  };
}

/**
 * Load explicit Muhurtam profile IDs. When the key does not yet exist, all
 * existing Muhurtam-ready profiles are selected once and written as IDs. This
 * preserves the legacy returning-user behaviour without retaining array-index
 * coupling.
 */
export function loadMuhurtamProfileSelection(
  storage: ProfileStorage,
  profiles: ReadonlyArray<Readonly<GuestProfile>>,
): MuhurtamProfileSelection {
  let rawText: string | null;
  try {
    rawText = storage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY);
  } catch {
    const defaults = profiles
      .filter(profile => guestProfileReadiness(profile).muhurta)
      .map(profile => profile.id);
    return asMuhurtamSelection(
      resolveMuhurtamIds(defaults, profiles),
      defaults.length > 0,
      'storage-unavailable',
    );
  }

  if (rawText === null) {
    const defaults = profiles
      .filter(profile => guestProfileReadiness(profile).muhurta)
      .map(profile => profile.id);
    const resolved = resolveMuhurtamIds(defaults, profiles);
    const initialized = resolved.selectedIds.length > 0;
    // Persist even the empty initial state. Otherwise the first profile later
    // created from Daily Horoscope would look like a legacy Muhurtam startup
    // and be auto-selected in the wrong journey.
    const storageIssue = persistMuhurtamIds(storage, resolved.selectedIds);
    return asMuhurtamSelection(resolved, initialized, storageIssue);
  }

  let requestedIds: unknown[];
  let storageIssue: SelectionStorageIssue = null;
  try {
    const parsed: unknown = JSON.parse(rawText);
    if (!Array.isArray(parsed)) throw new Error('selection is not an array');
    requestedIds = parsed;
  } catch {
    requestedIds = [];
    storageIssue = 'malformed-storage';
  }

  const resolved = resolveMuhurtamIds(requestedIds, profiles);
  const normalizedText = JSON.stringify(resolved.selectedIds);
  if (normalizedText !== rawText) {
    const writeIssue = persistMuhurtamIds(storage, resolved.selectedIds);
    if (writeIssue) storageIssue = writeIssue;
  }
  return asMuhurtamSelection(resolved, false, storageIssue);
}

/** Persist an explicit, order-stable list of ready profile IDs. */
export function saveMuhurtamProfileSelection(
  storage: ProfileStorage,
  requestedIds: readonly string[],
  profiles: ReadonlyArray<Readonly<GuestProfile>>,
): MuhurtamProfileSelection {
  const resolved = resolveMuhurtamIds(requestedIds, profiles);
  const storageIssue = persistMuhurtamIds(storage, resolved.selectedIds);
  return asMuhurtamSelection(resolved, false, storageIssue);
}

/**
 * Add or remove one Muhurtam participant. A fifth add is rejected without
 * disturbing the four active stable IDs.
 */
export function toggleMuhurtamProfileSelection(
  storage: ProfileStorage,
  currentIds: readonly string[],
  profileId: string,
  selected: boolean,
  profiles: ReadonlyArray<Readonly<GuestProfile>>,
): MuhurtamProfileSelection {
  const current = resolveMuhurtamIds(currentIds, profiles);
  if (!selected) {
    return saveMuhurtamProfileSelection(
      storage,
      current.selectedIds.filter(id => id !== profileId),
      profiles,
    );
  }

  if (current.selectedIds.includes(profileId)) {
    return saveMuhurtamProfileSelection(storage, current.selectedIds, profiles);
  }

  const candidate = profiles.find(profile => profile.id === profileId);
  if (!candidate) {
    const result = { ...current, selectionIssue: 'profile-deleted' as const };
    const storageIssue = persistMuhurtamIds(storage, result.selectedIds);
    return asMuhurtamSelection(result, false, storageIssue);
  }
  if (!guestProfileReadiness(candidate).muhurta) {
    const result = { ...current, selectionIssue: 'profile-not-muhurta-ready' as const };
    const storageIssue = persistMuhurtamIds(storage, result.selectedIds);
    return asMuhurtamSelection(result, false, storageIssue);
  }
  if (current.selectedIds.length >= MAX_GUEST_PROFILES) {
    const result: ResolvedMuhurtamIds = {
      ...current,
      dropped: [...current.dropped, { id: profileId, reason: 'selection-limit' }],
      selectionIssue: 'selection-limit',
    };
    const storageIssue = persistMuhurtamIds(storage, result.selectedIds);
    return asMuhurtamSelection(result, false, storageIssue);
  }

  return saveMuhurtamProfileSelection(
    storage,
    [...current.selectedIds, profileId],
    profiles,
  );
}
