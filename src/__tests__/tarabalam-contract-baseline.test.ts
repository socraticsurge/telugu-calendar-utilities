import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';

const sourcePath = resolve('src/panels/tarabalam.ts');
const source = readFileSync(sourcePath, 'utf8');

function exportedNames(text: string): string[] {
  const names = new Set(
    Array.from(
      text.matchAll(
        /export\s+(?:async\s+)?(?:function|const|class|interface|type)\s+(\w+)/g,
      ),
      match => match[1],
    ),
  );
  for (const block of text.matchAll(/export\s*\{([^}]+)\}/gs)) {
    for (const item of block[1].split(',')) {
      const name = item.trim().split(/\s+/)[0];
      if (name) names.add(name);
    }
  }
  return [...names].sort();
}

describe('Tarabalam extraction baseline', () => {
  test('pins the complete public source surface', () => {
    expect(exportedNames(source)).toEqual([
      'TarabalamProfileActions',
      'TarabalamProfilesController',
      'calcTarabalam',
      'findMuhurta',
      'initTarabalamPanel',
      'initTarabalamProfiles',
      'invalidateMuhurtaSearch',
      'muAvoidKaranaWindows',
      'muChartAssessmentTitle',
      'muChartAssessorCanClaimComplete',
      'muChartBoundaryMessage',
      'muChartBoundaryNeedsReview',
      'muChartCheckMinutes',
      'muChartDispositionHtml',
      'muChartLagnasForMinutes',
      'muChartOutcomeLabel',
      'muChartProvenanceParts',
      'muChartRemovalRow',
      'muChartReviewDetail',
      'muChartScreeningDisposition',
      'muChartShareIncludesRemainder',
      'muChartShareScreeningLine',
      'muChartStatusDispositionClass',
      'muChartValidationItems',
      'muClassifyManualChecks',
      'muComplexityContracts',
      'muDayContextHtml',
      'muDaylightOutcomeLabel',
      'muDroppedOutcomeHtml',
      'muDroppedOutcomeLabel',
      'muEventSpecificCompletionDisclosure',
      'muHasLast',
      'muNatureBonus',
      'muPersonalOutcomeLabel',
      'muPluralSuffix',
      'muRelevantManualChecks',
      'muRoleStatus',
      'muSafetyOverrideFor',
      'muSafetyTitle',
      'muScoreActivityLagna',
      'muScoreParticipantChandrabalam',
      'muScoreParticipantLagna',
      'muScoreParticipantTarabalam',
      'muShareableMuhurtaReasons',
      'muValidLagnaDayData',
      'renderMuhurta',
      'renderTarabalam',
      'shareMuhurtaOnWhatsApp',
      'shareTarabalamOnWhatsApp',
      'tbAddRow',
      'tbChandraPresentation',
      'tbChandraVerdict',
      'tbExtendTo',
      'tbHasDays',
      'tbProfiles',
      'tbRemoveRow',
      'tbRenderProfileInputs',
      'tbResetProfiles',
      'tbSaveProfiles',
      'tbSetMode',
      'tbToggleShowAll',
    ]);
  });

  test('pins browser state and persistence ownership', () => {
    for (const stateName of [
      'TB_DAYS',
      'TB_EVENTS',
      'TB_PROFILE_CONTROLLER',
      'TB_MANUAL_SEQUENCE',
      'TB_LEGACY_ROWS',
      'TB_SHOW_ALL',
      'TB_MODE',
      'MU_SEARCH_SEQUENCE',
      'MU_CHART_ABORT',
      'MU_LAST',
    ]) {
      expect(source).toMatch(new RegExp(`let ${stateName}(?:\\s|:)`));
    }
    for (const storageContract of [
      'GUEST_BIRTH_PROFILE_STORAGE_KEY',
      'GUEST_PROFILE_COMMIT_STORAGE_KEY',
      'GUEST_PROFILE_STORAGE_KEY',
      "'tc-tb-mode'",
    ]) {
      expect(source).toContain(storageContract);
    }
  });

  test('pins DOM roots, dynamic legacy fields and event types', () => {
    for (const id of [
      'tb-profiles',
      'tb-add-btn',
      'tb-from',
      'tb-to',
      'tb-result',
      'tb-summary',
      'tb-show-all',
      'tb-mode',
      'mu-activity',
      'mu-context',
      'mu-result',
      'mu-result-announcement',
      'tp-city',
    ]) {
      expect(source).toContain(`'${id}'`);
    }
    expect(source).toContain('`tb-${field}-${index}`');
    for (const eventType of ['click', 'change', 'input']) {
      expect(source).toContain(`addEventListener('${eventType}'`);
    }
  });

  test('pins high-risk status and share-output contracts', () => {
    for (const message of [
      'Pick at least one birth star.',
      'Pick a range of 1 to 60 days.',
      'Calculating…',
      'Searching…',
      'Search inputs changed · find slots again.',
      'Shortlist ready · screening exact election charts…',
      'Could not load the feed. Try again.',
      'profile details are intentionally omitted from this share.',
      'Every slot is clear of Rahu Kalam, Varjyam and all inauspicious windows.',
    ]) {
      expect(source).toContain(message);
    }
    expect(source.match(/https:\/\/wa\.me\/\?text=/g)).toHaveLength(2);
    expect(source.match(/gcEvent\('share-(?:tarabalam|slots)'\)/g)).toHaveLength(2);
    expect(source).toContain(
      "const MU_CHART_METHOD_URL = '/docs/reference/54-muhurtam-election-chart-screening'",
    );
  });
});
