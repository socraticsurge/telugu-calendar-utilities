import { RASI_NAMES } from '../../data/rasis';
import {
  COMPLETE_GRAHA_FACTS_UNAVAILABLE,
  type ElectionPrimitiveRule,
  type PlanetPosition,
  type PrimitiveOutcome,
} from './contracts';

const NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES = 0.02;
const BOUNDARY_EPSILON = 1e-9;

function longitude(position: PlanetPosition): number {
  return RASI_NAMES.indexOf(position.rashi) * 30 + position.degree;
}

export function evaluateHouseFreeOfNaturalMalefics(
  rule: ElectionPrimitiveRule,
  positions: ReadonlyMap<string, PlanetPosition> | null,
  options: { houseFrameUncertain?: boolean } = {},
): PrimitiveOutcome {
  if (!positions) {
    return { status: 'unknown', evidence: [COMPLETE_GRAHA_FACTS_UNAVAILABLE] };
  }
  if (options.houseFrameUncertain) {
    return { status: 'unknown', evidence: ['The local-Lagna house frame is uncertain.'] };
  }

  const fixed = (rule.fixed_malefics || []).filter(
    name => positions.get(name)?.house === rule.house,
  );
  if (fixed.length) {
    return {
      status: 'fail',
      evidence: [`Natural malefics in Lagna: ${fixed.join(', ')}.`],
    };
  }

  const chandra = positions.get('Chandra');
  const surya = positions.get('Surya');
  if (!chandra || !surya) {
    return { status: 'unknown', evidence: [COMPLETE_GRAHA_FACTS_UNAVAILABLE] };
  }
  if (chandra.house !== rule.house) {
    return {
      status: 'pass',
      evidence: ['Natural malefics in Lagna: none; Chandra is outside Lagna.'],
    };
  }

  const elongation = ((longitude(chandra) - longitude(surya)) % 360 + 360) % 360;
  const guard = rule.lunar_phase_guard_degrees
    ?? NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES;
  const boundaryDistance = Math.min(
    elongation, 360 - elongation, Math.abs(elongation - 180),
  );
  if (boundaryDistance <= guard + BOUNDARY_EPSILON) {
    return {
      status: 'unknown',
      evidence: [
        `Chandra occupies Lagna at ${elongation.toFixed(2)}° solar elongation, inside the disclosed ±${guard.toFixed(2)}° phase boundary guard.`,
      ],
    };
  }
  if (elongation > 180) {
    return {
      status: 'fail',
      evidence: [
        `Natural malefics in Lagna: waning Chandra (${elongation.toFixed(2)}° solar elongation).`,
      ],
    };
  }
  return {
    status: 'pass',
    evidence: [
      `Natural malefics in Lagna: none; waxing Chandra (${elongation.toFixed(2)}° solar elongation) is not malefic under this convention.`,
    ],
  };
}
