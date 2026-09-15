import sharedTables from '../data/shared-calendar-tables.generated.json';
import { MU_RASHI_NAMES, muLagnaAtMin } from '../muhurta-scorer';
import { TIME_PART } from '../lib/parse-description';
import { NAKSHATRA_NAMES, RASI_NAMES } from '../data/rasis';

export function muMin(t, flag?) {
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
function muValidLagnaHeader(lagnaDayData): boolean {
  if (!lagnaDayData || typeof lagnaDayData !== 'object') return false;
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(lagnaDayData.sunrise || '')) return false;
  if (!Number.isInteger(lagnaDayData.lagna0)
      || lagnaDayData.lagna0 < 0 || lagnaDayData.lagna0 > 11) return false;
  if (!Number.isInteger(lagnaDayData.cycleEnd)
      || lagnaDayData.cycleEnd < 1430 || lagnaDayData.cycleEnd > 2890) return false;
  if (!Array.isArray(lagnaDayData.transitions)
      || lagnaDayData.transitions.length < 12
      || lagnaDayData.transitions.length > 25) return false;
  return true;
}

function muValidLagnaTransition(
  transition,
  index: number,
  lagnaDayData,
  previousOffset: number,
  previousRashi: number,
): boolean {
  if (!Array.isArray(transition) || transition.length !== 2) return false;
  const [offset, rashi] = transition;
  const terminalBoundary = index === lagnaDayData.transitions.length - 1
    && offset === lagnaDayData.cycleEnd;
  if (!Number.isInteger(offset) || offset <= previousOffset
      || offset > lagnaDayData.cycleEnd
      || (offset === lagnaDayData.cycleEnd && !terminalBoundary)) return false;
  return Number.isInteger(rashi) && rashi === (previousRashi + 1) % 12;
}

export function muValidLagnaDayData(lagnaDayData) {
  if (!muValidLagnaHeader(lagnaDayData)) return false;

  // The generator rounds transition offsets to minutes. A boundary that
  // lands within the first half-minute can therefore be represented as zero;
  // only the first transition may use that value.
  let previousOffset = -1;
  let previousRashi = lagnaDayData.lagna0;
  const visited = new Set([previousRashi]);
  for (const [index, transition] of lagnaDayData.transitions.entries()) {
    if (!muValidLagnaTransition(
      transition, index, lagnaDayData, previousOffset, previousRashi,
    )) return false;
    const [offset, rashi] = transition;
    // cycleEnd is exclusive. Older generated artifacts can independently
    // round a sub-minute final window's start and end to that exact minute,
    // leaving a zero-width terminal sentinel. It is boundary evidence, not an
    // interior interval; equality is valid only for the final sequential row.
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

const MU_NAKSHATRA_LIST = NAKSHATRA_NAMES;

const MU_TITHI_LIST_FULL = (() => {
  const last = ['Pratipat','Dwitiya','Tritiya','Chaturthi','Panchami',
                'Shashthi','Saptami','Ashtami','Navami','Dashami',
                'Ekadashi','Dwadashi','Trayodashi','Chaturdashi','Pournami'];
  const shukla = last.slice(0, 14).map(n => `Shukla ${n}`).concat(['Pournami']);
  const krishna = last.slice(0, 14).map(n => `Krishna ${n}`).concat(['Amavasya']);
  return shukla.concat(krishna);
})();

const MU_YOGA_NAMES_27 = sharedTables.browserYogaNames;

const MU_KARANA_REPEATING = ['Bava','Balava','Kaulava','Taitila','Garaja','Vanija','Vishti'];
const MU_KARANA_FIXED = { 0: 'Kinstughna', 57: 'Shakuni', 58: 'Chatushpada', 59: 'Naga' };

// Special yogas — mirror telugu_panchangam/special_yogas.py
const MU_SARVARTHA = Object.fromEntries(Object.entries(sharedTables.specialYoga.sarvartha).map(([day, names]) => [day, new Set(names)]));
const MU_AMRITA_SIDDHI = sharedTables.specialYoga.amrita;
const MU_VISHA_TITHI = sharedTables.specialYoga.visha;
const MU_DAGDHA_TITHI = Object.fromEntries(Object.entries(sharedTables.specialYoga.dagdha).map(([day, numbers]) => [day, new Set(numbers)]));
const MU_PUSHKARA_VARAS = new Set(sharedTables.specialYoga.pushkaraVaras);
const MU_DVI_TITHIS = new Set(sharedTables.specialYoga.dviTithis);
const MU_DVI_NAKS = new Set(sharedTables.specialYoga.dviNakshatras);
const MU_TRI_TITHIS = new Set(sharedTables.specialYoga.triTithis);
const MU_TRI_NAKS = new Set(sharedTables.specialYoga.triNakshatras);

export function muSpecialYogasAt(vaaram, tithiName, nakshatraName) {
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
export function muFactsAt(dt, vaaram) {
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
  const lunarSign = RASI_NAMES[rashiIdx];
  const specialYogas = muSpecialYogasAt(vaaram, tithi, nakshatra);
  const solarNakshatra = MU_NAKSHATRA_LIST[Math.floor(sun / nakSize) % 27];
  return { nakshatra, solarNakshatra, tithi, yoga, karana, lunarSign, vaaram, specialYogas };
}

const MU_HOMAHUTI_LORDS = sharedTables.homaLords;
const MU_HOMAHUTI_BENEFICS = new Set(sharedTables.homaBenefics);
const MU_VAARAM_LIST = sharedTables.varaNames;

export function muHomaElection(facts) {
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
export function activityTithiNumber(name) {
  if (!name) return null;
  const last = name.trim().split(/\s+/).pop();
  if (TITHI_ALIASES[last]) return TITHI_ALIASES[last];
  const idx = TITHI_NAMES_ORDER.indexOf(last);
  return idx >= 0 ? idx + 1 : null;
}
