export type ShaniCondition =
  | 'Sade Sati (rising phase)'
  | 'Sade Sati (peak phase)'
  | 'Sade Sati (setting phase)'
  | 'Ashtama Shani'
  | 'Ardhastama Shani';

/** Conventional headline label for Shani's house from Janma Chandra only. */
export function shaniConditionFromMoonHouse(house: number): ShaniCondition | null {
  if (house === 12) return 'Sade Sati (rising phase)';
  if (house === 1) return 'Sade Sati (peak phase)';
  if (house === 2) return 'Sade Sati (setting phase)';
  if (house === 8) return 'Ashtama Shani';
  if (house === 4) return 'Ardhastama Shani';
  return null;
}

export function shaniConditionLine(condition: ShaniCondition): string {
  return condition.startsWith('Sade Sati')
    ? `${condition} is running — Shani asks for patience, discipline and steady work.`
    : `${condition} is running — avoid risks and keep commitments minimal.`;
}
