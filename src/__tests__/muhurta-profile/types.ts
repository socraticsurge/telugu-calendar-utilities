import type { GuestProfileStore } from '../../lib/guest-profile-store';

import type { BorrowingPurpose } from '../../scorer/borrowing-context';

export interface Participant {
  id: string;
  name: string;
  nak: string;
  pada: 1 | 2 | 3 | 4 | null;
  rasi: string | null;
  lagna: string | null;
}

export interface ManualCheckRow {
  text: string;
  display_section: 'chart' | 'information' | 'practical';
  applicable_varas?: string[];
  purpose?: string;
}

export interface ProfilesController {
  destroy(): void;
  getParticipants(): Participant[];
  getSelectedIds(): string[];
  getRoleParticipant(activity: string): Participant | null;
  getBorrowingPurpose(): BorrowingPurpose;
  selectProfile(id: string): boolean;
}

export interface TarabalamPanelModule {
  muComplexityContracts: Record<string, (...args: never[]) => unknown>;
  initTarabalamProfiles(
    store: GuestProfileStore,
    actions: {
      createProfile(trigger: HTMLElement): void;
      editProfile(id: string, trigger: HTMLElement): void;
      manageProfiles(trigger: HTMLElement): void;
    },
  ): ProfilesController;
  tbAddRow(): void;
  tbProfiles(): Participant[];
  tbRenderProfileInputs(): void;
  tbRemoveRow(index: number): void;
  tbSaveProfiles(): void;
  tbResetProfiles(): void;
  muRelevantManualChecks(
    activity: string, vaaram: string, borrowingPurpose?: BorrowingPurpose,
  ): ManualCheckRow[];
  muClassifyManualChecks(activity: string, rows?: ManualCheckRow[] | null): {
    chart: string[];
    information: string[];
    practical: string[];
  };
  muSafetyOverrideFor(activity: string): string | null;
  muChartCheckMinutes(
    lagnaDay: unknown, startMinute: number, endMinute: number,
  ): number[];
  muChartLagnasForMinutes(lagnaDay: unknown, minutes: number[]): string[] | null;
  muChartBoundaryNeedsReview(
    lagnaDay: unknown, startMinute: number, endMinute: number,
  ): boolean;
  muValidLagnaDayData(lagnaDay: unknown): boolean;
  muChartAssessorCanClaimComplete(
    activity: string,
    enrichment: {
      state: string;
      candidateLimitReached: boolean;
      boundaryReviewCount: number;
      reviewGatedCount: number;
    },
  ): boolean;
  muChartAssessmentTitle(
    activity: string,
    enrichment: {
      state: string;
      candidateLimitReached: boolean;
      boundaryReviewCount: number;
      reviewGatedCount: number;
    },
  ): string;
  muChartOutcomeLabel(outcome: { effect: string; status: string }): string;
  muChartBoundaryMessage(screening: {
    boundaryConventionUncertain: boolean;
    needsReview: boolean;
    stable: boolean;
    qualificationFailed: boolean;
  }): string;
  muDaylightOutcomeLabel(status: string): string;
  muPersonalOutcomeLabel(outcome: { effect: string; status: string }): string;
  muPluralSuffix(count: number): string;
  muDroppedOutcomeLabel(status: string): string;
  muChartRemovalRow(rule: {
    label: string;
    count: number;
    evidence?: string[];
  }): string;
  muChartProvenanceParts(
    sourceReferences: Array<{ claim: string; locator: string }>,
    decisionPolicies: string[],
    conventions: Array<{
      id: string;
      label: string;
      formula: string;
      claims: string[];
    }>,
  ): {
    eventSourceSuffix: string;
    decisionPolicyHtml: string;
    conventionHtml: string;
    rankingPolicyClaimsHtml: string;
    conventionClaimsHtml: string;
  };
  muDayContextHtml(dayContext: unknown): string;
  muDroppedOutcomeHtml(outcomes: unknown): string;
  muChartReviewDetail(chartEnrichment: unknown): string;
  muChartStatusDispositionClass(disposition: string | null): string;
  muChartValidationItems(screening: unknown, reasonGroups: unknown): unknown;
  muChartDispositionHtml(screening: unknown): string;
  muSafetyTitle(activity: string): string;
  tbChandraVerdict(position: number): string;
  tbChandraPresentation(tara: {
    good: boolean;
    chandra?: { verdict: string; pos: number };
  }): { chandraTag: string; cls: string };
  muNatureBonus(isAbhijit: boolean, nature: string): number;
  muAvoidKaranaWindows(karana: string, avoidNames: Set<unknown>): number[][];
  muRoleStatus(
    roleProfile: { name: string } | null,
    chartEnrichment: { state: string; screenedCount: number } | null,
  ): string;
  muChartScreeningDisposition(enrichment: {
    state: string;
    candidateLimitReached: boolean;
    boundaryReviewCount: number;
    reviewGatedCount: number;
    qualificationCappedCount: number;
  }): 'review' | 'capped' | 'bounded' | 'resolved' | null;
  muShareableMuhurtaReasons(slot: unknown): string[];
  muChartShareScreeningLine(chartEnrichment: unknown): string;
  muChartShareIncludesRemainder(chartEnrichment: unknown): boolean;
  muEventSpecificCompletionDisclosure(
    activity: string,
    chartEnrichment: { state: string; screenedCount: number } | null,
  ): string | null;
  muScoreParticipantTarabalam(
    people: Participant[], nakshatra: string,
  ): { score: number; reasons: string[]; unfavourableNames: string[] };
  muScoreParticipantChandrabalam(
    people: Participant[], lunarSign: string, chandraMode: string,
  ): {
    score: number;
    reasons: string[];
    avoidNames: string[];
    pujaNames: string[];
    hasAshtama: boolean;
    drop: boolean;
  };
  muScoreParticipantLagna(
    people: Participant[], slotLagna: string,
  ): { score: number; reasons: string[]; ashtamaNames: string[] };
  muScoreActivityLagna(
    slotLagna: string | null,
    requiredLagnaClass: string | null,
    allowedLagnas: Set<string>,
    preferLagnas: Set<string>,
    preferLagnaClass: string | null,
    lagnaCityData: unknown,
    activityLabel: string,
    allowConditionalAdmission?: boolean,
  ): { score: number; reasons: string[] } | null;
}
