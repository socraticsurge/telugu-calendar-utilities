import sharedTables from './data/shared-calendar-tables.generated.json';
export type ShaniCondition =
  | 'Sade Sati (rising phase)'
  | 'Sade Sati (peak phase)'
  | 'Sade Sati (setting phase)'
  | 'Ashtama Shani'
  | 'Ardhastama Shani';

/** Conventional headline label for Shani's house from Janma Chandra only. */
export function shaniConditionFromMoonHouse(house: number): ShaniCondition | null {
  return (sharedTables.shaniConditions[house - 1] as ShaniCondition | undefined) ?? null;
}

export function shaniConditionLine(condition: ShaniCondition): string {
  return condition.startsWith('Sade Sati')
    ? `${condition} is running — Shani asks for patience, discipline and steady work.`
    : `${condition} is running — avoid risks and keep commitments minimal.`;
}
