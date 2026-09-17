import { describe, expect, test } from 'vitest';
import { usePanelFixture, type PanelFixture } from './muhurta-profile/fixtures';

let panel: PanelFixture['panel'];

usePanelFixture(fixture => {
  ({ panel } = fixture);
});

describe('Muhurtam result presentation and share privacy', () => {
  test('claims partial event clauses only after actual chart screening', () => {
    const completionCopy =
      'The event-specific clauses were computed, but the overall election-chart assessment remains partial/provisional until the shared baseline is complete.';

    expect(panel.muEventSpecificCompletionDisclosure('vidyarambha', {
      state: 'screened', screenedCount: 1,
    })).toBe(completionCopy);
    expect(panel.muEventSpecificCompletionDisclosure('vidyarambha', {
      state: 'unavailable', screenedCount: 3,
    })).toBe(completionCopy);

    for (const state of [
      'disabled', 'unsupported-system', 'not-run', 'manual-only',
    ]) {
      expect(panel.muEventSpecificCompletionDisclosure('vidyarambha', {
        state, screenedCount: 3,
      })).toBeNull();
    }
    expect(panel.muEventSpecificCompletionDisclosure('vidyarambha', {
      state: 'unavailable', screenedCount: 0,
    })).toBeNull();
    expect(panel.muEventSpecificCompletionDisclosure('vidyarambha', {
      state: 'screened', screenedCount: 0,
    })).toBeNull();
    expect(panel.muEventSpecificCompletionDisclosure('vehicle', {
      state: 'screened', screenedCount: 1,
    })).toBeNull();
    expect(panel.muEventSpecificCompletionDisclosure('vidyarambha', null))
      .toBeNull();
  });

  test('uses event-specific completion wording without closing baseline 284', () => {
    const resolved = {
      state: 'screened', candidateLimitReached: false,
      boundaryReviewCount: 0, reviewGatedCount: 0,
      qualificationCappedCount: 0,
    };
    expect(panel.muChartAssessorCanClaimComplete('annaprasana', resolved))
      .toBe(true);
    expect(panel.muChartAssessmentTitle('annaprasana', resolved)).toBe(
      'Annaprasana event-specific chart assessment complete');

    const bounded = { ...resolved, candidateLimitReached: true };
    expect(panel.muChartAssessorCanClaimComplete('annaprasana', bounded))
      .toBe(false);
    expect(panel.muChartAssessmentTitle('annaprasana', bounded)).toBe(
      'Chart screening applied to a bounded candidate set');
    expect(panel.muChartScreeningDisposition(bounded)).toBe('bounded');

    const boundary = { ...resolved, boundaryReviewCount: 1 };
    expect(panel.muChartAssessorCanClaimComplete('annaprasana', boundary))
      .toBe(false);
    expect(panel.muChartAssessmentTitle('annaprasana', boundary)).toBe(
      'Chart screening applied with boundary review');

    const unresolved = { ...resolved, reviewGatedCount: 1 };
    expect(panel.muChartAssessorCanClaimComplete('annaprasana', unresolved))
      .toBe(false);
    expect(panel.muChartAssessmentTitle('annaprasana', unresolved)).toBe(
      'Chart screening applied with unresolved facts');
  });

  test('describes partial chart screening without claiming it was skipped', () => {
    expect(panel.muChartShareScreeningLine({
      state: 'screened',
      screenedCount: 60,
      candidateLimitReached: true,
    })).toBe(
      'Exact chart screening reached its safety budget after 60 candidates; every shown survivor was screened, but lower-ranked candidates were not assessed.',
    );
    expect(panel.muChartShareScreeningLine({
      state: 'unavailable',
      screenedCount: 24,
    })).toBe(
      'Partial exact chart screening was applied to 24 candidates; only already-screened survivors are included, and unprocessed candidates were withheld.',
    );
    expect(panel.muChartShareScreeningLine({
      state: 'unavailable',
      screenedCount: 0,
    })).toBe('Panchangam-ranked; exact election-chart screening was not applied.');
    expect(panel.muChartShareIncludesRemainder({
      state: 'unavailable',
      screenedCount: 24,
    })).toBe(true);
    expect(panel.muChartShareIncludesRemainder({
      state: 'unavailable',
      screenedCount: 0,
    })).toBe(false);
  });

  test('keeps renderer status wording stable across every chart state', () => {
    const profile = { name: 'Private Ananya' };
    expect(panel.muRoleStatus(null, null)).toBe(
      'No participant selected · source-specific personal checks remain unknown',
    );
    expect(panel.muRoleStatus(profile, { state: 'screened', screenedCount: 1 })).toBe(
      'Private Ananya · evaluated locally against the source-specific personal rules',
    );
    expect(panel.muRoleStatus(profile, { state: 'unavailable', screenedCount: 1 })).toBe(
      'Private Ananya · evaluated locally against the source-specific personal rules',
    );
    expect(panel.muRoleStatus(profile, { state: 'unsupported-system', screenedCount: 0 })).toBe(
      'Private Ananya selected · source-specific personal checks were not run for this system',
    );
    expect(panel.muRoleStatus(profile, { state: 'not-run', screenedCount: 0 })).toBe(
      'Private Ananya selected · there was no shortlisted slot to evaluate',
    );
    expect(panel.muRoleStatus(profile, { state: 'disabled', screenedCount: 0 })).toBe(
      'Private Ananya selected · source-specific personal checks are not active in this build',
    );
    expect(panel.muRoleStatus(profile, { state: 'unavailable', screenedCount: 0 })).toBe(
      'Private Ananya selected · source-specific personal checks could not run without exact chart facts',
    );
  });

  test('keeps computed chart outcome labels stable', () => {
    const cases = [
      ['reject', 'pass', 'Required check passed'],
      ['reject', 'unknown', 'Required check could not be verified'],
      ['reject', 'fail', 'Removed by mandatory chart rule'],
      ['qualify', 'pass', 'Qualification met'],
      ['qualify', 'unknown', 'Indeterminate at calculation boundary · review needed'],
      ['qualify', 'fail', 'Condition not met · slot retained · raw score unchanged · maximum rating Good'],
      ['prefer', 'pass', 'Preference met · tie-break only'],
      ['prefer', 'unknown', 'Preference could not be verified'],
      ['prefer', 'fail', 'Preference not present · no penalty'],
      ['inform', 'pass', 'Information pattern present · no ranking effect'],
      ['inform', 'unknown', 'Information pattern could not be verified'],
      ['inform', 'fail', 'Information pattern not continuous · no adverse inference'],
    ];
    for (const [effect, status, label] of cases) {
      expect(panel.muChartOutcomeLabel({ effect, status })).toBe(label);
    }
  });

  test('keeps chart boundary explanations stable', () => {
    const base = {
      boundaryConventionUncertain: false,
      needsReview: false,
      stable: false,
      qualificationFailed: false,
    };
    expect(panel.muChartBoundaryMessage({ ...base, boundaryConventionUncertain: true }))
      .toBe('This window touches the five-minute Lagna convention guard at an edge. House-dependent checks remain unresolved; sign-based aspects are still evaluated.');
    expect(panel.muChartBoundaryMessage({ ...base, needsReview: true, stable: true }))
      .toBe('One or more event-specific facts are indeterminate at a calculation boundary. The slot is retained, its raw score is unchanged, and the maximum rating is Good pending review.');
    expect(panel.muChartBoundaryMessage({ ...base, needsReview: true }))
      .toBe('Sampled states changed within this window, and one or more event-specific facts are indeterminate. The slot is retained, its raw score is unchanged, and the maximum rating is Good pending review.');
    expect(panel.muChartBoundaryMessage({ ...base, qualificationFailed: true }))
      .toBe('At least one event-specific condition was conclusively not met. The slot is retained, its raw score is unchanged, and the maximum rating is Good; this is not an unknown or review result.');
    expect(panel.muChartBoundaryMessage({ ...base, stable: true }))
      .toBe('The result was stable across every sampled Lagna-stable state in this window.');
    expect(panel.muChartBoundaryMessage(base))
      .toBe('Sampled states changed, but every controlling outcome was resolved automatically.');
  });

  test('keeps daylight and profile-specific labels stable', () => {
    expect(panel.muDaylightOutcomeLabel('pass')).toBe('Required daylight check passed');
    expect(panel.muDaylightOutcomeLabel('fail')).toBe('Day removed by daylight rule');
    expect(panel.muDaylightOutcomeLabel('unknown'))
      .toBe('Boundary could not be verified · day removed');

    expect(panel.muPersonalOutcomeLabel({ effect: 'reject', status: 'pass' })).toBe('Passed');
    expect(panel.muPersonalOutcomeLabel({ effect: 'prefer', status: 'fail' }))
      .toBe('Preference not present');
    expect(panel.muPersonalOutcomeLabel({ effect: 'reject', status: 'unknown' }))
      .toBe('Could not verify');
    expect(panel.muPersonalOutcomeLabel({ effect: 'reject', status: 'fail' })).toBe('Not met');
  });

  test('preserves escaped removal and provenance fragments', () => {
    expect(panel.muPluralSuffix(1)).toBe('');
    expect(panel.muPluralSuffix(2)).toBe('s');
    expect(panel.muDroppedOutcomeLabel('pass')).toBe('passed');
    expect(panel.muDroppedOutcomeLabel('fail')).toBe('failed');
    expect(panel.muDroppedOutcomeLabel('unknown')).toBe('could not be verified');
    expect(panel.muChartRemovalRow({
      label: '<Vacant eighth>',
      count: 2,
      evidence: ['Mars & Saturn'],
    })).toBe(
      '<li><strong>&lt;Vacant eighth&gt;</strong> · 2 slots<small>Observed: Mars &amp; Saturn</small></li>',
    );
    expect(panel.muChartRemovalRow({ label: 'Required check', count: 1 }))
      .toBe('<li><strong>Required check</strong> · 1 slot</li>');
    const provenance = panel.muChartProvenanceParts(
      [{ claim: 'claim.one', locator: 'Source <one>' }],
      ['policy.one'],
      [{
        id: 'whole-sign',
        label: 'Whole <sign>',
        formula: 'house = sign & lagna',
        claims: ['method.one'],
      }],
    );
    expect(provenance.eventSourceSuffix).toBe('');
    expect(provenance.decisionPolicyHtml).toContain('Product ranking policy:');
    expect(provenance.conventionHtml).toContain('Whole &lt;sign&gt;');
    expect(provenance.rankingPolicyClaimsHtml).toContain('<code>policy.one</code>');
    expect(provenance.conventionClaimsHtml).toContain('<code>method.one</code>');
  });

  test('preserves day context and dropped outcome fragments', () => {
    const dayContext = panel.muDayContextHtml({
      tithi: 'Shukla Panchami',
      nakshatra: 'Rohini',
      yoga: 'Siddhi',
      sunrise: '6:10 AM',
      abhijit: '11:45 AM to 12:35 PM',
      rahu: '7:30 AM to 9:00 AM',
      auspicious: [{ name: 'Amrita Kalam', ranges: ['10:00 AM to 11:00 AM'] }],
      avoid: [{ name: 'Rahu Kalam', ranges: ['7:30 AM to 9:00 AM'] }],
    });
    expect(dayContext).toContain('🌙 Shukla Panchami');
    expect(dayContext).toContain('⭐ Rohini');
    expect(dayContext).toContain('🧘 Siddhi yoga');
    expect(dayContext).toContain('🌅 Sunrise 6:10 AM');
    expect(dayContext).toContain('<b>Amrita Kalam</b> 10:00 AM to 11:00 AM');
    expect(dayContext).toContain('<b>Rahu Kalam</b> 7:30 AM to 9:00 AM');
    expect(panel.muDayContextHtml(null)).toBe('');
    const droppedOutcomes = panel.muDroppedOutcomeHtml([{
      status: 'fail',
      label: '<Daylight rule>',
      evidence: ['Boundary & sunset'],
    }]);
    expect(droppedOutcomes).toContain('mu-dropped-daylight--fail');
    expect(droppedOutcomes).toContain('&lt;Daylight rule&gt;');
    expect(droppedOutcomes).toContain('Boundary &amp; sunset');
    expect(panel.muDroppedOutcomeHtml([])).toBe('');
  });

  test('preserves chart review and validation fragments', () => {
    expect(panel.muChartReviewDetail({ boundaryReviewCount: 1 }))
      .toBe(' · boundary-adjacent house checks held for review');
    expect(panel.muChartReviewDetail({ reviewGatedCount: 1 }))
      .toBe(' · unresolved chart facts held for review');
    expect(panel.muChartReviewDetail(null)).toBe('');
    expect(panel.muChartStatusDispositionClass('capped'))
      .toBe(' mu-chart-status--screened-capped');
    expect(panel.muChartStatusDispositionClass(null)).toBe('');
    expect(panel.muChartValidationItems(true, {
      chart_remainder: ['Remainder'],
      chart_validation: ['Validation'],
    })).toEqual(['Remainder']);
    expect(panel.muChartValidationItems(false, {
      chart_remainder: ['Remainder'],
      chart_validation: ['Validation'],
    })).toEqual(['Validation']);
    expect(panel.muChartDispositionHtml({ needsReview: true })).toContain('Review needed');
    expect(panel.muChartDispositionHtml({ qualificationFailed: true })).toContain('max Good');
    expect(panel.muChartDispositionHtml(null)).toBe('');
  });

  test('preserves safety, personal and timing labels', () => {
    expect(panel.muSafetyTitle('surgery')).toBe('Medical care overrides timing');
    expect(panel.muSafetyTitle('court')).toBe('Legal duties override timing');
    expect(panel.tbChandraVerdict(1)).toBe('good');
    expect(panel.tbChandraVerdict(2)).toBe('puja');
    expect(panel.tbChandraVerdict(4)).toBe('bad');
    expect(panel.tbChandraPresentation({
      good: true,
      chandra: { verdict: 'puja', pos: 2 },
    })).toEqual({ chandraTag: ' · ° 2nd', cls: 'good' });
    expect(panel.tbChandraPresentation({
      good: false,
      chandra: { verdict: 'bad', pos: 4 },
    })).toEqual({ chandraTag: ' · ☾ 4th', cls: 'bad' });
    expect(panel.tbChandraPresentation({
      good: true,
      chandra: { verdict: 'good', pos: 1 },
    })).toEqual({ chandraTag: '', cls: 'good' });
    expect(panel.muNatureBonus(true, 'inauspicious')).toBe(2);
    expect(panel.muNatureBonus(false, 'auspicious')).toBe(1);
    expect(panel.muNatureBonus(false, 'inauspicious')).toBe(-2);
    expect(panel.muAvoidKaranaWindows(
      'Bava 06:00 - 07:30 / Vishti 07:30 (+1) – 08:15 (+1)',
      new Set(['Vishti']),
    )).toEqual([[1890, 1935]]);
    expect(panel.muAvoidKaranaWindows(
      'Bava 06:00 - 07:30',
      new Set(['Vishti']),
    )).toEqual([]);
  });

  test('preserves event-specific disposition wording', () => {
    const dispositionBase = {
      state: 'screened',
      candidateLimitReached: false,
      boundaryReviewCount: 0,
      reviewGatedCount: 0,
      qualificationCappedCount: 0,
    };
    expect(panel.muChartScreeningDisposition({
      ...dispositionBase, state: 'unavailable',
    })).toBeNull();
    expect(panel.muChartScreeningDisposition({
      ...dispositionBase, reviewGatedCount: 1,
    })).toBe('review');
    expect(panel.muChartScreeningDisposition({
      ...dispositionBase, qualificationCappedCount: 1,
    })).toBe('capped');
    expect(panel.muChartScreeningDisposition(dispositionBase)).toBe('resolved');
    expect(panel.muChartAssessmentTitle('gold', dispositionBase))
      .toBe('Gold event-specific chart clauses resolved');
    expect(panel.muChartAssessmentTitle('karnavedha', dispositionBase))
      .toBe('Karnavedha event checks resolved');
    expect(panel.muChartAssessmentTitle('court', dispositionBase))
      .toBe('Court filing chart assessment complete');
    expect(panel.muChartAssessmentTitle('borrowing_money', dispositionBase))
      .toBe('Borrowing event-specific chart clause resolved');
    expect(panel.muChartAssessmentTitle('purchase', dispositionBase))
      .toBe('Exact chart screening applied');
    const borrowingScopeDetail = panel.muComplexityContracts
      .muResultScopeDetail as unknown as (
        activity: string, enrichment: unknown, partial: boolean,
      ) => string;
    expect(borrowingScopeDetail(
      'borrowing_money', dispositionBase, false,
    )).toContain('shared election baseline remain manual');
  });

  test('keeps profile identity and natal evidence out of Muhurtam shares', () => {
    expect(panel.muShareableMuhurtaReasons({
      reasons: ['Tarabalam favourable for Private Person (+1)'],
      reasonGroups: {
        slot_quality: ['Amrit Choghadiya (+3)'],
        day_quality: ['Siddhi Yoga (+1)'],
        activity_match: ['Thursday favoured (+1)'],
        group_fit: ['Tarabalam favourable for Private Person (+1)'],
        personal_source: ['Chandra differs from Private Person’s Janma Rashi'],
      },
    })).toEqual([
      'Amrit Choghadiya (+3)',
      'Siddhi Yoga (+1)',
      'Thursday favoured (+1)',
    ]);
  });

});
