// Muhurta scoring helpers — pure functions, no DOM.
// Unit-tested by src/scorer/__tests__/muhurta-scorer.test.ts (Vitest);
// behaviour is pinned to the Python originals in telugu_panchangam/
// personal/{muhurta,lagna_position,chandrabalam}.py.

export const MU_RASHI_NAMES = ['Mesha','Vrishabha','Mithuna','Karka','Simha',
                        'Kanya','Tula','Vrischika','Dhanu','Makara',
                        'Kumbha','Meena'];

export const MU_LAGNA_KENDRA = new Set([1, 4, 7, 10]);
export const MU_LAGNA_TRIKONA = new Set([1, 5, 9]);

export const MU_LAGNA_CHARA = new Set(['Mesha', 'Karka', 'Tula', 'Makara']);
export const MU_LAGNA_STHIRA = new Set(['Vrishabha', 'Simha', 'Vrischika', 'Kumbha']);
export const MU_LAGNA_DVISVABHAVA = new Set(['Mithuna', 'Kanya', 'Dhanu', 'Meena']);
export const MU_LAGNA_CLASSES: Record<string, Set<string>> = {
  Chara: MU_LAGNA_CHARA,
  Sthira: MU_LAGNA_STHIRA,
  Dvisvabhava: MU_LAGNA_DVISVABHAVA,
};

export const MU_CHANDRA_GOOD = new Set([1, 3, 6, 7, 10, 11]);
export const MU_CHANDRA_PUJA = new Set([2, 5, 9]);

export const MU_TIER_NAMES = ['Avoid', 'Fair', 'Good', 'Excellent'];
export const MU_RELATIVE_BANDS = [0.75, 0.5, 0.25];

const MU_NAKSHATRA_ALIASES: Record<string, string> = {
  Ashwini: 'Ashvini',
  Moola: 'Mula',
};

export function muCanonicalNakshatra(name: string): string {
  return MU_NAKSHATRA_ALIASES[name] || name;
}

const MU_TITHI_NAMES = [
  'Pratipat', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
  'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
  'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Pournami',
];
const MU_TITHI_ALIASES: Record<string, number> = {
  Pratipada: 1, Prathama: 1, Shashti: 6, Amavasya: 15,
};
const MU_TITHI_FAMILIES: Record<number, string> = {
  1: 'Nanda', 6: 'Nanda', 11: 'Nanda',
  2: 'Bhadra', 7: 'Bhadra', 12: 'Bhadra',
  3: 'Jaya', 8: 'Jaya', 13: 'Jaya',
  4: 'Rikta', 9: 'Rikta', 14: 'Rikta',
  5: 'Purna', 10: 'Purna', 15: 'Purna',
};

export function muTithiFamily(name: string): string | null {
  if (!name) return null;
  const last = name.trim().split(/\s+/).pop() || '';
  const number = MU_TITHI_ALIASES[last] || MU_TITHI_NAMES.indexOf(last) + 1;
  return number > 0 ? MU_TITHI_FAMILIES[number] || null : null;
}

export function muScoreTithiClass(
  tithiName: string,
  preferTithiClass: string | null,
  activityLabel: string,
  nakshatra: string | null = null,
  specialYogas: string[] = [],
  avoidTithiClasses: string[] = [],
) {
  const family = muTithiFamily(tithiName);
  if (!family) return { bonus: 0, dayReason: null, activityReason: null, family };

  if (family === 'Rikta') {
    if (nakshatra === 'Pushya') {
      return {
        bonus: 0,
        dayReason: `${tithiName} (Rikta tithi) neutralised by Pushya nakshatra (0)`,
        activityReason: null,
        family,
      };
    }
    const siddhi = specialYogas.filter(
      yoga => yoga === 'Sarvartha Siddhi Yoga' || yoga === 'Amrita Siddhi Yoga');
    if (siddhi.length) {
      return {
        bonus: -1,
        dayReason: `${tithiName} (Rikta tithi) partially offset by ${siddhi.join(' + ')} (-1)`,
        activityReason: null,
        family,
      };
    }
    return {
      bonus: -2,
      dayReason: `${tithiName} (Rikta tithi) (-2)`,
      activityReason: null,
      family,
    };
  }
  if (tithiName.includes('Amavasya')) {
    return { bonus: -2, dayReason: `${tithiName} (-2)`, activityReason: null,
      family: 'Amavasya' };
  }
  if (preferTithiClass && family === preferTithiClass) {
    return {
      bonus: 1,
      dayReason: null,
      activityReason: `${tithiName} (${preferTithiClass} tithi) favoured for ${activityLabel} (+1)`,
      family,
    };
  }
  if (avoidTithiClasses.includes(family)) {
    return {
      bonus: -1,
      dayReason: null,
      activityReason: `${tithiName} (${family} tithi) inauspicious for ${activityLabel} (-1)`,
      family,
    };
  }
  return { bonus: 0, dayReason: null, activityReason: null, family };
}

export function muLagnaClassOf(rashi: string): string | null {
  for (const k of Object.keys(MU_LAGNA_CLASSES)) {
    if (MU_LAGNA_CLASSES[k].has(rashi)) return k;
  }
  return null;
}

export function muLagnasInClass(className: string): Set<string> | null {
  return MU_LAGNA_CLASSES[className] || null;
}

export function muLagnaPosition(janmaRashi: string, lagnaRashi: string): number | null {
  const j = MU_RASHI_NAMES.indexOf(janmaRashi);
  const l = MU_RASHI_NAMES.indexOf(lagnaRashi);
  if (j < 0 || l < 0) return null;
  return ((l - j) % 12 + 12) % 12 + 1;
}

export function muLagnaVerdict(pos: number): string {
  if (pos === 1) return 'own';
  if (pos === 8) return 'ashtama';
  if (MU_LAGNA_TRIKONA.has(pos)) return 'trikona';
  if (MU_LAGNA_KENDRA.has(pos)) return 'kendra';
  return 'neutral';
}

export function muIsFavourableLagna(pos: number): boolean {
  return MU_LAGNA_KENDRA.has(pos) || MU_LAGNA_TRIKONA.has(pos);
}

export function muIsAshtamaLagna(pos: number): boolean { return pos === 8; }

export function muLagnaAtMin(lagnaDayData: any, slotMin: number): string | null {
  if (!lagnaDayData) return null;
  const [srH, srM] = lagnaDayData.sunrise.split(':').map(Number);
  const sunriseMin = srH * 60 + srM;
  const offset = slotMin - sunriseMin;
  if (offset < 0) return null;
  const starts = [[0, lagnaDayData.lagna0], ...lagnaDayData.transitions];
  for (let i = 0; i < starts.length; i++) {
    const [startOff, rashiIdx] = starts[i];
    const endOff = (i + 1 < starts.length) ? starts[i + 1][0] : lagnaDayData.cycleEnd;
    if (startOff <= offset && offset < endOff) {
      return MU_RASHI_NAMES[rashiIdx];
    }
  }
  return null;
}

export function muScoreTier(score: number): string {
  if (score >= 7) return 'Excellent';
  if (score >= 4) return 'Good';
  if (score >= 1) return 'Fair';
  return 'Avoid';
}

export function muRelativeTier(score: number, ceiling: number, floor: number): string {
  const spread = ceiling - floor;
  if (spread <= 0) return muScoreTier(score);
  const rel = (score - floor) / spread;
  if (rel >= MU_RELATIVE_BANDS[0]) return 'Excellent';
  if (rel >= MU_RELATIVE_BANDS[1]) return 'Good';
  if (rel >= MU_RELATIVE_BANDS[2]) return 'Fair';
  return 'Avoid';
}

export function muEndsBySolarNoon(
  slotEndMin: number,
  sunriseMin: number,
  sunsetMin: number,
): boolean {
  return slotEndMin <= sunriseMin + (sunsetMin - sunriseMin) / 2;
}

export function muCombustionDropReason(
  lagnaDayData: any,
  requiredPlanets: string[],
  activityLabel: string,
): string | null {
  if (!requiredPlanets.length) return null;
  const fields: Record<string, string> = {
    Guru: 'guruCombust',
    Shukra: 'shukraCombust',
  };
  const unknown = requiredPlanets.filter(planet =>
    !fields[planet] || typeof lagnaDayData?.[fields[planet]] !== 'boolean');
  if (unknown.length) {
    return `${activityLabel} combustion screening unavailable (${unknown.join(', ')})`;
  }
  const combust = requiredPlanets.filter(planet => lagnaDayData[fields[planet]]);
  return combust.length
    ? `${combust.join(' and ')} Maudhya · ${activityLabel} deferred`
    : null;
}

export function computePersonalDosha({
  chandraAvoidNames = [] as string[],
  hasAshtamaChandra = false,
  ashtamaLagnaNames = [] as string[],
  chandraPujaNames = [] as string[],
  taraUnfavNames = [] as string[],
  siddhiYogas = [] as string[],
} = {}): string | null {
  if (chandraAvoidNames.length) {
    return hasAshtamaChandra ? 'ashtama_chandra' : 'chandra_avoid';
  }
  if (ashtamaLagnaNames.length) return 'ashtama_lagna';
  if (chandraPujaNames.length) return 'chandra_remedial';
  if (taraUnfavNames.length && !siddhiYogas.length) return 'tara_dosha';
  return null;
}

export function computeDayDosha({
  tithiFamily = null as string | null,
  isAmavasya = false,
  hasYogaPenalty = false,
  nityaHardAvoid = false,
} = {}): string | null {
  if (tithiFamily === 'Rikta') return 'rikta_tithi';
  if (isAmavasya) return 'amavasya';
  if (hasYogaPenalty) return 'visha_dagdha_yoga';
  if (nityaHardAvoid) return 'vyatipata_vaidhriti';
  return null;
}
