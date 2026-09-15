/** Pure ranking boundary: no DOM, storage, feed parsing or remote requests. */
import { MU_TIER_NAMES, muRelativeTier } from '../muhurta-scorer';

export interface TierCandidate {
  score: number;
  personalDosha?: string | null;
  dayDosha?: string | null;
  tier?: string;
}

export interface RankedCandidate extends TierCandidate {
  personalPreferencePasses?: number;
  d: Date | number;
  s0: number;
}

function scoreRange(slots: TierCandidate[]): [number, number] {
  let ceiling = -Infinity, floor = Infinity;
  for (const s of slots) {
    if (s.score > ceiling) ceiling = s.score;
    if (s.score < floor) floor = s.score;
  }
  return [ceiling, floor];
}

function cappedTier(slot: TierCandidate, tier: string): string {
  if (tier !== 'Excellent') return tier;
  return slot.personalDosha || slot.dayDosha ? 'Good' : tier;
}

export function muAssignTiers<T extends TierCandidate>(slots: T[]) {
  const [ceiling, floor] = scoreRange(slots);
  for (const slot of slots) {
    slot.tier = cappedTier(slot, muRelativeTier(slot.score, ceiling, floor));
  }
}

export function muRankCandidateSlots<T extends RankedCandidate>(slots: T[]): void {
  muAssignTiers(slots);
  slots.sort((a, b) => MU_TIER_NAMES.indexOf(b.tier ?? '') - MU_TIER_NAMES.indexOf(a.tier ?? '')
    || b.score - a.score
    || (b.personalPreferencePasses || 0) - (a.personalPreferencePasses || 0)
    || (Number(!!a.personalDosha) - Number(!!b.personalDosha))
    || Number(a.d) - Number(b.d)
    || a.s0 - b.s0);
}
