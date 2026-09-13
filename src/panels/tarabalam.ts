// typing lands with the component rewrite, not the move.
//
// Tarabalam panel + the nested Muhurta finder: profiles, good-day
// calculation, slot search (client-side mirror of the Python scorer),
// rendering and WhatsApp shares.

import { inpEl } from '../lib/dom';
import { type GuestProfileStore } from '../lib/guest-profile-store';
import {
  clearMuhurtaResult,
  hasMuhurtaResult,
} from './muhurta-result-state';

// --- Tarabalam tool ---

import {
  calcTarabalam,
  clearTarabalamJourney,
  renderTarabalam,
  shareTarabalamOnWhatsApp,
  tbChandraPresentation,
  tbChandraVerdict,
  tbExtendTo,
  tbHasDays,
  tbSetMode as setTarabalamMode,
  tbToggleShowAll,
} from './tarabalam-journey';

function tbSetMode(mode): void {
  setTarabalamMode(mode, invalidateMuhurtaSearch);
}


import {
  muClassifyManualChecks,
  muEventSpecificCompletionDisclosure,
  muRelevantManualChecks,
} from './muhurta-contracts';

import {
  initTarabalamProfiles as initTarabalamProfilesController,
  tbAddRow,
  tbProfiles,
  tbRemoveRow,
  tbRenderProfileInputs,
  tbSaveProfiles,
  type TarabalamProfileActions,
  type TarabalamProfilesController,
} from './tarabalam-profile-controller';
import { tbResetProfiles as resetTarabalamProfiles } from './tarabalam-profile-controller';
export type {
  TarabalamProfileActions,
  TarabalamProfilesController,
} from './tarabalam-profile-controller';

export function initTarabalamProfiles(
  store: GuestProfileStore,
  actions: TarabalamProfileActions,
): TarabalamProfilesController {
  return initTarabalamProfilesController(store, actions, {
    invalidateMuhurtaSearch,
    clearResults: clearTarabalamResults,
  });
}

function clearTarabalamResults(): void {
  clearTarabalamJourney();
  clearMuhurtaResult();
  for (const id of ['tb-summary', 'tb-result', 'mu-context', 'mu-result']) {
    document.getElementById(id)?.replaceChildren();
  }
}

function tbResetProfiles(): void {
  resetTarabalamProfiles({
    invalidateMuhurtaSearch,
    clearResults: clearTarabalamResults,
  });
}



// --- Muhurta finder (client-side, from the already-loaded feed) ---


import {
  muAvoidKaranaWindows,
  muChartBoundaryNeedsReview,
  muChartCheckMinutes,
  muChartLagnasForMinutes,
  muNatureBonus,
  muValidLagnaDayData,
} from './muhurta-astronomy';

// Activity rules — mirror telugu_panchangam/personal/muhurta.py
// ACTIVITY_RULES. Only the fields the JS scorer consumes are duplicated
// here (label, prefer_tithi_class, prefer_vara). skip_on_yoga and
// avoid_karana are still enforced by the engine; the JS reads
// parsed-feed yogas and karanas to mirror behaviour for activities the
// user picks via the in-page dropdown.
import {
  findMuhurta,
  invalidateMuhurtaSearch,
  muUnavailableChartEnrichment,
} from './muhurta-search';
import {
  muBadWindows,
  muCalendarDayDrop,
  muChandraModeDayDropReason,
  muConfiguredDaylightPolicy,
  muDayDrop,
  muNoSlotDayReason,
  muPrimaryDayDrop,
  muRecordNoSlotDay,
  muSolarDayDrop,
  muYogaDayDropReason,
} from './muhurta-day-rules';
import {
  muActivityNeedsLagna,
  muDominantChoghadiya,
  muPersonalDosha,
  muRankCandidateSlots,
  muScoreActivityLagna,
  muScoreNityaYoga,
  muScoreParticipantChandrabalam,
  muScoreParticipantLagna,
  muScoreParticipantTarabalam,
  muScoreSlotPreferences,
  muScoreSlotTithi,
  muScoreSpecialYogas,
  muSlotDayDosha,
  muSlotDoctrinalNotes,
  muSlotElectionReasons,
} from './muhurta-scoring';

import {
  muChartAssessmentTitle,
  muChartAssessorCanClaimComplete,
  muChartBoundaryMessage,
  muChartCompletionShareLines,
  muChartDispositionHtml,
  muChartOutcomeLabel,
  muChartProvenanceParts,
  muChartRemovalRow,
  muChartReviewDetail,
  muChartStatusFor,
  muChartScreeningDisposition,
  muChartShareIncludesRemainder,
  muChartShareScreeningLine,
  muChartStatusDispositionClass,
  muChartValidationItems,
  muDayContextHtml,
  muDaylightOutcomeLabel,
  muDroppedOutcomeHtml,
  muDroppedOutcomeLabel,
  muPersonalOutcomeLabel,
  muPluralSuffix,
  muResultScopeDetail,
  muRoleStatus,
  muSafetyOverrideFor,
  muSafetyTitle,
  muShareableMuhurtaReasons,
  renderMuhurta,
  shareMuhurtaOnWhatsApp,
} from './muhurta-presentation';

// Narrow test seam for the orchestration helpers extracted from the legacy
// panel. The browser-smoke suite covers their integrated paths; Vitest calls
// these boundaries directly so a structural refactor cannot create hidden
// function-coverage debt.
export const muComplexityContracts = {
  muConfiguredDaylightPolicy,
  muPrimaryDayDrop,
  muCalendarDayDrop,
  muSolarDayDrop,
  muDayDrop,
  muBadWindows,
  muYogaDayDropReason,
  muChandraModeDayDropReason,
  muNoSlotDayReason,
  muRecordNoSlotDay,
  muScoreSlotTithi,
  muScoreSpecialYogas,
  muScoreNityaYoga,
  muScoreSlotPreferences,
  muSlotDoctrinalNotes,
  muPersonalDosha,
  muSlotDayDosha,
  muDominantChoghadiya,
  muSlotElectionReasons,
  muActivityNeedsLagna,
  muRankCandidateSlots,
  muUnavailableChartEnrichment,
  muResultScopeDetail,
  muChartStatusFor,
  muChartCompletionShareLines,
};

export {
  calcTarabalam, renderTarabalam, tbRenderProfileInputs,
  tbAddRow, tbProfiles, tbRemoveRow, tbResetProfiles, tbSaveProfiles,
  tbChandraPresentation, tbChandraVerdict, tbExtendTo, tbHasDays,
  tbSetMode, tbToggleShowAll,
  findMuhurta, invalidateMuhurtaSearch, renderMuhurta,
  shareTarabalamOnWhatsApp, shareMuhurtaOnWhatsApp,
};

export {
  muChartAssessmentTitle,
  muChartAssessorCanClaimComplete,
  muChartBoundaryMessage,
  muChartBoundaryNeedsReview,
  muChartCheckMinutes,
  muChartDispositionHtml,
  muChartLagnasForMinutes,
  muChartOutcomeLabel,
  muChartProvenanceParts,
  muChartRemovalRow,
  muChartReviewDetail,
  muChartScreeningDisposition,
  muChartShareIncludesRemainder,
  muChartShareScreeningLine,
  muChartStatusDispositionClass,
  muChartValidationItems,
  muClassifyManualChecks,
  muDayContextHtml,
  muDaylightOutcomeLabel,
  muDroppedOutcomeHtml,
  muDroppedOutcomeLabel,
  muEventSpecificCompletionDisclosure,
  muNatureBonus,
  muPersonalOutcomeLabel,
  muPluralSuffix,
  muRelevantManualChecks,
  muRoleStatus,
  muSafetyOverrideFor,
  muSafetyTitle,
  muScoreActivityLagna,
  muScoreParticipantChandrabalam,
  muScoreParticipantLagna,
  muScoreParticipantTarabalam,
  muShareableMuhurtaReasons,
  muValidLagnaDayData,
  muAvoidKaranaWindows,
};

export function muHasLast() { return hasMuhurtaResult(); }

/** Wire panel-internal seeds; called once from Init. */
export function initTarabalamPanel(todayISO) {
  tbRenderProfileInputs();
  inpEl('tb-from').value = todayISO;
  const t2 = new Date(); t2.setDate(t2.getDate() + 13);
  inpEl('tb-to').value =
    `${t2.getFullYear()}-${String(t2.getMonth() + 1).padStart(2, '0')}-${String(t2.getDate()).padStart(2, '0')}`;
  for (const id of ['tb-from', 'tb-to']) {
    inpEl(id).addEventListener('change', () => invalidateMuhurtaSearch());
  }
}
