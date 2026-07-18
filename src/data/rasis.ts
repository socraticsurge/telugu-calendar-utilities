// The 12 rasis in order — shared by tarabalam, gochara and muhurta UI.

export const RASI_NAMES = ['Mesha','Vrishabha','Mithuna','Karka','Simha','Kanya','Tula','Vrischika','Dhanu','Makara','Kumbha','Meena'];

export const NAKSHATRA_NAMES = ['Ashvini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha','Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'];

/**
 * Janma rasi from birth star (+ optional padam). Each nakshatra spans
 * four padams; nine padams span a rasi. Straddler stars (spanning two
 * rasis) return null without a padam.
 */
export function rasiFromStar(nakName: string, pada: number | null): string | null {
  const k = NAKSHATRA_NAMES.indexOf(nakName);
  if (k < 0) return null;
  if (pada) return RASI_NAMES[Math.floor((k * 4 + pada - 1) / 9)];
  const first = Math.floor((k * 4) / 9), last = Math.floor((k * 4 + 3) / 9);
  return first === last ? RASI_NAMES[first] : null;  // straddler needs padam
}
