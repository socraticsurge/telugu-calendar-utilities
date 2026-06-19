// Muhurta scoring helpers — ES module version of docs/muhurta-scorer.js.
// docs/muhurta-scorer.js is kept as-is for the Node tests in tests/js/.
// Logic must stay in sync between the two files.

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
