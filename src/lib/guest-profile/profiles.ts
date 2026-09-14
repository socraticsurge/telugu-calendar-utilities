import { NAKSHATRA_NAMES, RASI_NAMES, rasiFromStar } from '../../data/rasis';
import { fixedGrahaFactsMatch, roundedMoonMatchesBirthFacts, wholeSignHousesMatch } from '../birth-profile-api';
import { normalizeBirthDetails, normalizeCalculation, normalizeNatalChart } from './birth-normalization';
import {
  GUEST_PROFILE_SCHEMA_VERSION,
  type GuestProfile,
  type GuestProfileDraft,
  type GuestProfileReadiness,
  type StoredBirthProfileRecord,
  type StoredProfileRecord,
} from './types';
import {
  canonical,
  exactCanonical,
  exactPada,
  pada,
  text,
} from './values';


export function clone(profile: GuestProfile): GuestProfile {
  return {
    ...profile,
    birthDetails: profile.birthDetails ? { ...profile.birthDetails } : null,
    natalChart: profile.natalChart
      ? { ...profile.natalChart, planets: profile.natalChart.planets.map(planet => ({ ...planet })) }
      : null,
    calculation: profile.calculation
      ? { ...profile.calculation, engine: { ...profile.calculation.engine } }
      : null,
  };
}

export function toStored(profile: GuestProfile): StoredProfileRecord {
  return {
    id: profile.id,
    schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
    name: profile.name,
    nak: profile.nakshatra || '',
    pada: profile.pada || '',
    lagna: profile.lagna || '',
  };
}

export function toStoredBirthProfile(profile: GuestProfile): StoredBirthProfileRecord | null {
  if (
    profile.source !== 'birth-details' || !profile.birthDetails || !profile.janmaRasi
    || !profile.natalChart || !profile.calculation
  ) return null;
  return {
    source: 'birth-details',
    nakshatra: profile.nakshatra!,
    pada: profile.pada!,
    lagna: profile.lagna!,
    birthDetails: { ...profile.birthDetails },
    janmaRasi: profile.janmaRasi,
    natalChart: {
      lagnaDegree: profile.natalChart.lagnaDegree,
      planets: profile.natalChart.planets.map(planet => ({ ...planet })),
    },
    calculation: {
      contractVersion: profile.calculation.contractVersion,
      engine: { ...profile.calculation.engine },
    },
  };
}

export function guestProfileReadiness(profile: GuestProfile): GuestProfileReadiness {
  const janmaRasi = profile.nakshatra
    ? rasiFromStar(profile.nakshatra, profile.pada)
    : null;
  let missingForHoroscope: GuestProfileReadiness['missingForHoroscope'] = null;
  if (profile.nakshatra === null) {
    missingForHoroscope = 'nakshatra';
  } else if (janmaRasi === null) {
    missingForHoroscope = 'pada';
  }
  return {
    muhurta: profile.nakshatra !== null,
    horoscope: janmaRasi !== null,
    janmaRasi,
    missingForHoroscope,
  };
}

export function hasContent(profile: GuestProfile): boolean {
  return Boolean(profile.name || profile.nakshatra || profile.lagna);
}

/** Undefined means keep the saved field; an explicit null still clears it. */
export function mergeProfileDraft(current: GuestProfile, patch: GuestProfileDraft): GuestProfileDraft {
  return {
    source: patch.source === undefined ? current.source : patch.source,
    name: patch.name === undefined ? current.name : patch.name,
    nakshatra: patch.nakshatra === undefined ? current.nakshatra : patch.nakshatra,
    pada: patch.pada === undefined ? current.pada : patch.pada,
    lagna: patch.lagna === undefined ? current.lagna : patch.lagna,
    janmaRasi: patch.janmaRasi === undefined ? current.janmaRasi : patch.janmaRasi,
    birthDetails: patch.birthDetails === undefined ? current.birthDetails : patch.birthDetails,
    natalChart: patch.natalChart === undefined ? current.natalChart : patch.natalChart,
    calculation: patch.calculation === undefined ? current.calculation : patch.calculation,
  };
}

function normalizedProfileFacts(draft: GuestProfileDraft) {
  const nakshatra = canonical(draft.nakshatra, NAKSHATRA_NAMES);
  const padaValue = nakshatra ? pada(draft.pada) : null;
  const lagna = canonical(draft.lagna, RASI_NAMES);
  const birthDetails = normalizeBirthDetails(draft.birthDetails);
  const natalChart = normalizeNatalChart(draft.natalChart);
  const calculation = normalizeCalculation(draft.calculation);
  const suppliedRasi = canonical(draft.janmaRasi, RASI_NAMES);
  const derivedRasi = nakshatra ? rasiFromStar(nakshatra, padaValue) : null;
  const exactBirthNakshatra = exactCanonical(draft.nakshatra, NAKSHATRA_NAMES);
  const exactBirthPada = exactPada(draft.pada);
  const exactBirthLagna = exactCanonical(draft.lagna, RASI_NAMES);
  const exactBirthRasi = exactCanonical(draft.janmaRasi, RASI_NAMES);
  return {
    nakshatra, padaValue, lagna, birthDetails, natalChart, calculation,
    suppliedRasi, derivedRasi, exactBirthNakshatra, exactBirthPada,
    exactBirthLagna, exactBirthRasi,
  };
}

type NormalizedProfileFacts = ReturnType<typeof normalizedProfileFacts>;

function exactBirthFactsMatch(facts: NormalizedProfileFacts): boolean {
  return facts.suppliedRasi === facts.derivedRasi
    && facts.exactBirthNakshatra === facts.nakshatra
    && facts.exactBirthPada === facts.padaValue
    && facts.exactBirthLagna === facts.lagna
    && facts.exactBirthRasi === facts.suppliedRasi;
}

function coherentBirthProfile(facts: NormalizedProfileFacts): boolean {
  const { birthDetails, natalChart, calculation, suppliedRasi, nakshatra, padaValue, lagna } = facts;
  if (!birthDetails || !natalChart || !calculation || !suppliedRasi) return false;
  if (!exactBirthFactsMatch(facts)) return false;
  if (!nakshatra || !padaValue || !lagna) return false;
  return wholeSignHousesMatch(lagna, natalChart.planets)
    && fixedGrahaFactsMatch(natalChart.planets)
    && roundedMoonMatchesBirthFacts(nakshatra, padaValue, suppliedRasi, natalChart.planets[1]);
}

export function normalizeProfile(draft: GuestProfileDraft, id: string): GuestProfile {
  const facts = normalizedProfileFacts(draft);
  const { nakshatra, padaValue, lagna, birthDetails, natalChart, calculation, suppliedRasi, derivedRasi } = facts;
  const isBirthDerived = draft.source === 'birth-details' && coherentBirthProfile(facts);
  return {
    id,
    schemaVersion: GUEST_PROFILE_SCHEMA_VERSION,
    source: isBirthDerived ? 'birth-details' : 'manual',
    name: text(draft.name),
    nakshatra,
    pada: padaValue,
    lagna,
    janmaRasi: isBirthDerived ? suppliedRasi : derivedRasi,
    birthDetails: isBirthDerived ? birthDetails : null,
    natalChart: isBirthDerived ? natalChart : null,
    calculation: isBirthDerived ? calculation : null,
  };
}
