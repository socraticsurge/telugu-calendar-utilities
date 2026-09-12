import { RASI_NAMES } from '../../data/rasis';
import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import { classifyNaturalGrahaNatures } from './graha-nature';
import { CLASSICAL_RASI_LORDS } from './lordship';
import type { PrimitiveOutcome } from './contracts';

export const BENEFIC_RASI_CONVENTION_ID =
  'benefic-rasi-by-resolved-natural-lord-v1' as const;

/** Classify a Rasi through its classical lord's resolved natural nature. */
export function evaluateBeneficRasi(
  chart: ElectionChartSnapshot,
  rashi: string,
): PrimitiveOutcome {
  if (!RASI_NAMES.includes(rashi)) {
    return { status: 'unknown', evidence: ['The target Rasi is invalid.'] };
  }
  const result = classifyNaturalGrahaNatures(chart);
  const lord = CLASSICAL_RASI_LORDS[rashi as keyof typeof CLASSICAL_RASI_LORDS];
  if (!result.complete) return { status: 'unknown', evidence: result.evidence };
  const nature = result.natures[lord];
  const evidence = `${rashi} is owned by ${lord}; the registered natural-nature classifier resolves the lord as ${nature}.`;
  if (nature === 'unknown') {
    return { status: 'unknown', evidence: [evidence, ...result.evidence] };
  }
  return { status: nature === 'benefic' ? 'pass' : 'fail', evidence: [evidence] };
}
