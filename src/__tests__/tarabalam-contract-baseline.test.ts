import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';

const sourcePath = resolve('src/panels/tarabalam.ts');
const source = readFileSync(sourcePath, 'utf8');
const implementationSource = [
  source,
  readFileSync(resolve('src/panels/tarabalam-profile-controller.ts'), 'utf8'),
  readFileSync(resolve('src/panels/tarabalam-journey.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-contracts.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-presentation.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-result-state.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-astronomy.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-day-rules.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-scoring.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-day-pipeline.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-format.ts'), 'utf8'),
  readFileSync(resolve('src/panels/muhurta-search.ts'), 'utf8'),
].join('\n');

const extractedModules = [
  'tarabalam-profile-controller.ts',
  'tarabalam-journey.ts',
  'muhurta-contracts.ts',
  'muhurta-presentation.ts',
  'muhurta-result-state.ts',
  'muhurta-astronomy.ts',
  'muhurta-day-rules.ts',
  'muhurta-scoring.ts',
  'muhurta-day-pipeline.ts',
  'muhurta-format.ts',
  'muhurta-search.ts',
];

function exportedNames(text: string): string[] {
  const names = new Set(
    Array.from(
      text.matchAll(
        /export\s+(?:async\s+)?(?:function|const|class|interface|type)\s+(\w+)/g,
      ),
      match => match[1],
    ),
  );
  for (const block of text.matchAll(/export\s*(?:type\s*)?\{([^}]+)\}/gs)) {
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
      'lastMuhurtaResult',
    ]) {
      expect(implementationSource).toMatch(
        new RegExp(`let ${stateName}(?:\\s|:)`),
      );
    }
    for (const storageContract of [
      'GUEST_BIRTH_PROFILE_STORAGE_KEY',
      'GUEST_PROFILE_COMMIT_STORAGE_KEY',
      'GUEST_PROFILE_STORAGE_KEY',
      "'tc-tb-mode'",
    ]) {
      expect(implementationSource).toContain(storageContract);
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
      expect(implementationSource).toContain(`'${id}'`);
    }
    expect(implementationSource).toContain('`tb-${field}-${index}`');
    for (const eventType of ['click', 'change', 'input']) {
      expect(implementationSource).toContain(`addEventListener('${eventType}'`);
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
      expect(implementationSource).toContain(message);
    }
    expect(implementationSource.match(/https:\/\/wa\.me\/\?text=/g)).toHaveLength(2);
    expect(implementationSource.match(/gcEvent\('share-(?:tarabalam|slots)'\)/g)).toHaveLength(2);
    expect(implementationSource).toContain(
      "const MU_CHART_METHOD_URL = '/docs/reference/54-muhurtam-election-chart-screening'",
    );
  });

  test('keeps extracted modules independent of the composition facade', () => {
    for (const moduleName of extractedModules) {
      const moduleSource = readFileSync(resolve('src/panels', moduleName), 'utf8');
      expect(moduleSource, moduleName).not.toMatch(/from ['"]\.\/tarabalam['"]/);
    }
  });

  test('keeps the day pipeline free of UI and infrastructure dependencies', () => {
    const pipeline = readFileSync(
      resolve('src/panels/muhurta-day-pipeline.ts'),
      'utf8',
    );
    for (const prohibited of [
      './muhurta-presentation',
      '../lib/dom',
      'localStorage',
      '../lib/analytics',
      '../lib/feed-loader',
      '../lib/lagna-loader',
    ]) {
      expect(pipeline).not.toContain(prohibited);
    }
  });
});
