export type PrimitiveStatus = 'pass' | 'fail' | 'unknown';

export interface PrimitiveOutcome {
  status: PrimitiveStatus;
  evidence: string[];
}

export interface ElectionPrimitiveRule {
  kind?: string;
  planet?: string;
  planets?: string[];
  houses?: number[];
  avoid_houses?: number[];
  enemy_rashis?: string[];
  debilitation_rashi?: string;
  navamsa_debilitation_rashi?: string;
  aspectors?: string[];
  solar_clearance_degrees?: number;
  solar_clearance_guard_degrees?: number;
  house?: number;
  fixed_malefics?: string[];
  lunar_phase_guard_degrees?: number;
}

export interface PlanetPosition {
  name: string;
  rashi: string;
  degree: number;
  house: number;
  retrograde: boolean;
}

export const COMPLETE_GRAHA_FACTS_UNAVAILABLE = 'Complete graha facts are unavailable.';
