import activityContract from '../data/activity-rules.generated.json';
import { manualRowAppliesToBorrowingPurpose, type BorrowingPurpose } from '../scorer/borrowing-context';
import { automatedRulesFor, chartAssessorCompleteFor } from '../scorer/election-chart-screening';

type MuManualCheckRow = {
  id: string;
  source_index: number;
  source_text: string;
  text: string;
  class: string;
  display_section: 'chart' | 'information' | 'practical';
  applicable_varas?: string[];
  purpose?: string;
};

export function muManualCheckRows(activity: string): MuManualCheckRow[] {
  const activities = activityContract.check_contract.activities as unknown as
    Record<string, { manual_checks: MuManualCheckRow[] }>;
  return activities[activity]?.manual_checks || [];
}

export function muRelevantManualChecks(
  activity: string,
  vaaram: string,
  borrowingPurpose: BorrowingPurpose = 'other_or_unknown',
) {
  return muManualCheckRows(activity).filter(row =>
    (!row.applicable_varas?.length || row.applicable_varas.includes(vaaram))
    && (activity !== 'borrowing_money'
      || manualRowAppliesToBorrowingPurpose(row.purpose, borrowingPurpose)));
}

export function muClassifyManualChecks(
  activity: string,
  rows: MuManualCheckRow[] | null = null,
) {
  const result = { chart: [], information: [], practical: [] };
  for (const row of rows || muManualCheckRows(activity)) {
    result[row.display_section].push(row.text);
  }
  return result;
}

type MuChartScreeningProgress = {
  state: 'screened' | 'not-run' | 'manual-only' | 'unsupported-system'
    | 'disabled' | 'unavailable';
  screenedCount: number;
};

export const MU_PARTIAL_ASSESSOR_DISCLOSURE =
  'The event-specific clauses were computed, but the overall election-chart assessment remains partial/provisional until the shared baseline is complete.';

/**
 * Describe a partial assessor as computed only after chart facts were actually
 * screened. A partially completed unavailable run may truthfully make the same
 * claim for its already-screened candidates; every zero-screen state stays
 * silent even if a malformed caller supplies a contradictory count.
 */
export function muEventSpecificCompletionDisclosure(
  activity: string,
  chartEnrichment: MuChartScreeningProgress | null,
): string | null {
  const partialAssessor = automatedRulesFor(activity).length > 0
    && !chartAssessorCompleteFor(activity);
  const screeningApplied = !!chartEnrichment
    && chartEnrichment.screenedCount > 0
    && (
      chartEnrichment.state === 'screened'
      || chartEnrichment.state === 'unavailable'
    );
  return partialAssessor && screeningApplied
    ? MU_PARTIAL_ASSESSOR_DISCLOSURE
    : null;
}
