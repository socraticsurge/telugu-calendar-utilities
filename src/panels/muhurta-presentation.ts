import { muScoreTier } from '../muhurta-scorer';
import { htmlEsc } from '../lib/html';
import { gcEvent } from '../lib/analytics';
import activityContract from '../data/activity-rules.generated.json';
import { roleForActivity } from '../scorer/personal-election-screening';
import {
  automatedRulesFor,
  chartAssessorCompleteFor,
  chartManualRemaindersFor,
} from '../scorer/election-chart-screening';
import {
  muClassifyManualChecks,
  muEventSpecificCompletionDisclosure,
  muManualCheckRows,
} from './muhurta-contracts';
import { getMuhurtaResult } from './muhurta-result-state';
import { muToT } from './muhurta-format';

const MU_ACTIVITY = activityContract.rules;

const MU_ACT_LABEL = {
  any: 'anything auspicious',
  travel: 'travel', purchase: 'a purchase',
  ceremony: 'a Shantika / Paushtika rite', beginning: 'a Dharma-kriya commencement',
  wedding: 'a wedding (Vivaha)',
  engagement: 'a mutual engagement (Kanya-Varavarana)',
  cremation: 'deferred funeral rites (Pretakriya)',
  naming: 'a naming ceremony', annaprasana: 'annaprasana (first feeding)',
  karnavedha: 'karnavedha (ear-piercing)', mundana: 'a mundana / chaula',
  upanayana: 'upanayana (sacred thread)',
  vidyarambha: 'Aksharabhyasa (first-letter writing)',
  seemantha: 'seemantha (prenatal ceremony)',
  gruhapravesha: 'gruhapravesha (home entry)',
  vehicle: 'a vehicle purchase', property: 'a land purchase for building',
  house_purchase: 'a completed house purchase',
  gold: 'a gold / jewelry purchase',
  business_inventory_purchase: 'a trade inventory purchase',
  borrowing_money: 'borrowing money / taking a loan',
  lending_money: 'lending money / giving a loan',
  bhumi_puja: 'bhumi puja (foundation laying)',
  well_digging: 'well digging',
  home_repair: 'a home repair / renovation start',
  business: 'a capital deployment / business investment', job: 'entering employment / starting service',
  yajna: 'a Homa offering (Homahuti)', pilgrimage: 'a pilgrimage',
  court: 'filing a lawsuit / court action', surgery: 'a surgery / medical procedure',
};

const MU_CHART_METHOD_URL = '/docs/reference/54-muhurtam-election-chart-screening';

type MuChartCompletionState = {
  state: string;
  candidateLimitReached: boolean;
  boundaryReviewCount: number;
  reviewGatedCount: number;
};

type MuChartDispositionState = MuChartCompletionState & {
  qualificationCappedCount: number;
};

type MuChartOutcomeState = {
  effect: string;
  status: string;
};

type MuChartBoundaryState = {
  boundaryConventionUncertain: boolean;
  needsReview: boolean;
  stable: boolean;
  qualificationFailed: boolean;
};

type MuRoleEnrichmentState = {
  state: string;
  screenedCount: number;
};

export function muPluralSuffix(count: number): string {
  return count === 1 ? '' : 's';
}

export function muChartOutcomeLabel(outcome: MuChartOutcomeState): string {
  if (outcome.effect === 'reject') {
    if (outcome.status === 'pass') return 'Required check passed';
    if (outcome.status === 'unknown') return 'Required check could not be verified';
    return 'Removed by mandatory chart rule';
  }
  if (outcome.effect === 'qualify') {
    if (outcome.status === 'pass') return 'Qualification met';
    if (outcome.status === 'unknown') {
      return 'Indeterminate at calculation boundary · review needed';
    }
    return 'Condition not met · slot retained · raw score unchanged · maximum rating Good';
  }
  if (outcome.effect === 'inform') {
    if (outcome.status === 'pass') return 'Information pattern present · no ranking effect';
    if (outcome.status === 'unknown') return 'Information pattern could not be verified';
    return 'Information pattern not continuous · no adverse inference';
  }
  if (outcome.status === 'pass') return 'Preference met · tie-break only';
  if (outcome.status === 'unknown') return 'Preference could not be verified';
  return 'Preference not present · no penalty';
}

export function muChartBoundaryMessage(screening: MuChartBoundaryState): string {
  if (screening.boundaryConventionUncertain) {
    return 'This window touches the five-minute Lagna convention guard at an edge. House-dependent checks remain unresolved; sign-based aspects are still evaluated.';
  }
  if (screening.needsReview) {
    if (screening.stable) {
      return 'One or more event-specific facts are indeterminate at a calculation boundary. The slot is retained, its raw score is unchanged, and the maximum rating is Good pending review.';
    }
    return 'Sampled states changed within this window, and one or more event-specific facts are indeterminate. The slot is retained, its raw score is unchanged, and the maximum rating is Good pending review.';
  }
  if (screening.qualificationFailed) {
    return 'At least one event-specific condition was conclusively not met. The slot is retained, its raw score is unchanged, and the maximum rating is Good; this is not an unknown or review result.';
  }
  if (screening.stable) {
    return 'The result was stable across every sampled Lagna-stable state in this window.';
  }
  return 'Sampled states changed, but every controlling outcome was resolved automatically.';
}

export function muDaylightOutcomeLabel(status: string): string {
  if (status === 'pass') return 'Required daylight check passed';
  if (status === 'fail') return 'Day removed by daylight rule';
  return 'Boundary could not be verified · day removed';
}

export function muPersonalOutcomeLabel(outcome: MuChartOutcomeState): string {
  if (outcome.status === 'pass') return 'Passed';
  if (outcome.effect === 'prefer' && outcome.status === 'fail') {
    return 'Preference not present';
  }
  if (outcome.status === 'unknown') return 'Could not verify';
  return 'Not met';
}

export function muRoleStatus(
  roleProfile: { name: string } | null,
  chartEnrichment: MuRoleEnrichmentState | null,
): string {
  if (!roleProfile) {
    return 'No participant selected · source-specific personal checks remain unknown';
  }
  if (chartEnrichment?.state === 'screened' || chartEnrichment?.screenedCount) {
    return `${roleProfile.name} · evaluated locally against the source-specific personal rules`;
  }
  if (chartEnrichment?.state === 'unsupported-system') {
    return `${roleProfile.name} selected · source-specific personal checks were not run for this system`;
  }
  if (chartEnrichment?.state === 'not-run') {
    return `${roleProfile.name} selected · there was no shortlisted slot to evaluate`;
  }
  if (chartEnrichment?.state === 'disabled') {
    return `${roleProfile.name} selected · source-specific personal checks are not active in this build`;
  }
  return `${roleProfile.name} selected · source-specific personal checks could not run without exact chart facts`;
}

export function muDroppedOutcomeLabel(status: string): string {
  if (status === 'pass') return 'passed';
  if (status === 'fail') return 'failed';
  return 'could not be verified';
}

export function muChartRemovalRow(rule): string {
  let evidence = '';
  if (rule.evidence?.length) {
    evidence = `<small>Observed: ${htmlEsc(rule.evidence.join(' '))}</small>`;
  }
  return `<li><strong>${htmlEsc(rule.label)}</strong> · ${rule.count} slot${muPluralSuffix(rule.count)}${evidence}</li>`;
}

export function muChartProvenanceParts(
  sourceReferences,
  decisionPolicies,
  conventions,
) {
  const eventSourceSuffix = muPluralSuffix(sourceReferences.length);
  let decisionPolicyHtml = '';
  if (decisionPolicies.length) {
    decisionPolicyHtml = `<p class="mu-rule-reference mu-rule-policy">
                  <strong>Product ranking policy:</strong>
                  The source defines the chart condition. This project policy defines how a resolved failure or an unresolved fact changes removal, rating caps, or tie-break ordering.
                </p>`;
  }
  const conventionHtml = conventions.map(convention => (
    `<p class="mu-rule-reference mu-rule-convention">
                  <strong>Interpretation convention:</strong> ${htmlEsc(convention.label)}<br>
                  ${htmlEsc(convention.formula)}
                </p>`
  )).join('');
  let rankingPolicyClaimsHtml = '';
  if (decisionPolicies.length) {
    const claims = decisionPolicies.map(claim => `<code>${htmlEsc(claim)}</code>`).join(' · ');
    rankingPolicyClaimsHtml = `<p><strong>Ranking policy claim${muPluralSuffix(decisionPolicies.length)}:</strong> ${claims}</p>`;
  }
  const conventionClaimsHtml = conventions.map(convention => {
    let methodClaimsHtml = '';
    if (convention.claims.length) {
      const claims = convention.claims.map(claim => `<code>${htmlEsc(claim)}</code>`).join(' · ');
      methodClaimsHtml = `<br><strong>Method claims:</strong> ${claims}`;
    }
    return `<p><strong>Convention:</strong> <code>${htmlEsc(convention.id)}</code>${methodClaimsHtml}</p>`;
  }).join('');
  return {
    eventSourceSuffix,
    decisionPolicyHtml,
    conventionHtml,
    rankingPolicyClaimsHtml,
    conventionClaimsHtml,
  };
}

export function muDayContextHtml(dc): string {
  if (!dc) return '';
  const winList = wins => wins.map(w => (
    `<span class="mu-tim"><b>${w.name}</b> ${w.ranges.join(', ')}</span>`
  )).join('');
  const tithiHtml = dc.tithi ? `<span class="mu-angachip">🌙 ${dc.tithi}</span>` : '';
  const nakshatraHtml = dc.nakshatra ? `<span class="mu-angachip">⭐ ${dc.nakshatra}</span>` : '';
  const yogaHtml = dc.yoga ? `<span class="mu-angachip">🧘 ${dc.yoga} yoga</span>` : '';
  const sunriseHtml = dc.sunrise ? `<span>🌅 Sunrise ${dc.sunrise}</span>` : '';
  const abhijitHtml = dc.abhijit ? `<span class="mu-t-aus">✨ Abhijit ${dc.abhijit}</span>` : '';
  const rahuHtml = dc.rahu ? `<span class="mu-t-warn">⛔ Rahu Kalam ${dc.rahu}</span>` : '';
  let auspiciousHtml = '';
  if (dc.auspicious.length) {
    auspiciousHtml = `<div class="mu-tim-row">
                    <span class="mu-tim-lbl mu-t-aus">🟢 Auspicious</span>
                    <span class="mu-tim-wins mu-t-aus">${winList(dc.auspicious)}</span></div>`;
  }
  let avoidHtml = '';
  if (dc.avoid.length) {
    avoidHtml = `<div class="mu-tim-row">
                    <span class="mu-tim-lbl mu-t-warn">🔴 Avoid</span>
                    <span class="mu-tim-wins mu-t-warn">${winList(dc.avoid)}</span></div>`;
  }
  return `<div class="mu-dayctx">
              <div class="mu-anga">
                ${tithiHtml}
                ${nakshatraHtml}
                ${yogaHtml}
              </div>
              <details class="mu-timings-d">
                <summary class="mu-timings">
                  ${sunriseHtml}
                  ${abhijitHtml}
                  ${rahuHtml}
                  <span class="mu-tim-toggle">all timings</span>
                </summary>
                <div class="mu-timings-full">
                  ${auspiciousHtml}
                  ${avoidHtml}
                </div>
              </details>
            </div>`;
}

export function muDroppedOutcomeHtml(outcomes): string {
  if (!outcomes?.length) return '';
  return `<ul class="mu-dropped-daylight" aria-label="Karnavedha daylight rule outcomes">
         ${outcomes.map(outcome => {
           const evidence = outcome.evidence?.length
             ? `<small>${htmlEsc(outcome.evidence.join(' '))}</small>`
             : '';
           return `<li class="mu-dropped-daylight--${outcome.status}">
           <strong>${htmlEsc(outcome.label)}</strong> · ${htmlEsc(muDroppedOutcomeLabel(outcome.status))}
           ${evidence}
         </li>`;
         }).join('')}
       </ul>`;
}

export function muChartReviewDetail(chartEnrichment): string {
  if (chartEnrichment?.boundaryReviewCount) {
    return ' · boundary-adjacent house checks held for review';
  }
  if (chartEnrichment?.reviewGatedCount) {
    return ' · unresolved chart facts held for review';
  }
  return '';
}

export function muChartStatusDispositionClass(disposition: string | null): string {
  return disposition ? ` mu-chart-status--screened-${disposition}` : '';
}

export function muChartValidationItems(screening, reasonGroups) {
  if (screening && Array.isArray(reasonGroups?.chart_remainder)) {
    return reasonGroups.chart_remainder;
  }
  return reasonGroups?.chart_validation;
}

export function muChartDispositionHtml(screening): string {
  if (screening?.needsReview) {
    return '<span class="mu-chart-disposition mu-chart-disposition--review">Review needed</span>';
  }
  if (screening?.qualificationFailed) {
    return '<span class="mu-chart-disposition mu-chart-disposition--capped">Condition not met · max Good</span>';
  }
  return '';
}

export function muSafetyTitle(activity: string): string {
  return activity === 'surgery'
    ? 'Medical care overrides timing'
    : 'Legal duties override timing';
}

export function muChartAssessorCanClaimComplete(
  activity: string,
  enrichment: MuChartCompletionState,
): boolean {
  return enrichment.state === 'screened'
    && !enrichment.candidateLimitReached
    && enrichment.boundaryReviewCount === 0
    && enrichment.reviewGatedCount === 0
    && chartAssessorCompleteFor(activity);
}

export function muChartScreeningDisposition(
  enrichment: MuChartDispositionState,
): 'review' | 'capped' | 'bounded' | 'resolved' | null {
  if (enrichment.state !== 'screened') return null;
  if (enrichment.reviewGatedCount || enrichment.boundaryReviewCount) {
    return 'review';
  }
  if (enrichment.qualificationCappedCount) return 'capped';
  if (enrichment.candidateLimitReached) return 'bounded';
  return 'resolved';
}

export function muChartAssessmentTitle(
  activity: string,
  enrichment: MuChartCompletionState,
): string {
  if (enrichment.boundaryReviewCount) {
    return 'Chart screening applied with boundary review';
  }
  if (enrichment.reviewGatedCount) {
    return 'Chart screening applied with unresolved facts';
  }
  if (enrichment.candidateLimitReached) {
    return 'Chart screening applied to a bounded candidate set';
  }
  if (muChartAssessorCanClaimComplete(activity, enrichment)) {
    if (activity === 'annaprasana') {
      return 'Annaprasana event-specific chart assessment complete';
    }
    if (activity === 'gold') return 'Gold event-specific chart clauses resolved';
    if (activity === 'court') return 'Court filing chart assessment complete';
    if (activity === 'borrowing_money') {
      return 'Borrowing event-specific chart clause resolved';
    }
  }
  if (activity === 'karnavedha') return 'Karnavedha event checks resolved';
  return 'Exact chart screening applied';
}

export function muSafetyOverrideFor(activity: string) {
  if (activity !== 'surgery' && activity !== 'court') return null;
  return muManualCheckRows(activity).find(
    row => row.purpose === 'safety_override',
  )?.text || null;
}

export function muResultScopeDetail(activity, chartEnrichment, partialAssessor: boolean): string {
  const hasScreeningReview = !!(
    chartEnrichment?.boundaryReviewCount
    || chartEnrichment?.reviewGatedCount
  );
  if (activity === 'gold') {
    return hasScreeningReview
      ? ' · all four Gold v1 event-specific clauses attempted; unresolved outcomes remain review-gated; the general election-chart baseline is not assessed'
      : ' · all four Gold v1 event-specific outcomes resolved; the general election-chart baseline is not assessed';
  }
  if (activity === 'annaprasana') {
    return muChartAssessorCanClaimComplete(activity, chartEnrichment)
      ? ' · all six Annaprasana event-specific clauses resolved; the general election-chart baseline #284 remains open'
      : ' · all six Annaprasana event-specific clauses attempted; unresolved or bounded outcomes remain review-gated; the general election-chart baseline #284 remains open';
  }
  if (activity === 'court') {
    return muChartAssessorCanClaimComplete(activity, chartEnrichment)
      ? ' · all five Court filing clauses resolved; two mandatory gates, two score-neutral preferences, and one non-ranking information pattern were evaluated'
      : ' · all five Court filing clauses attempted; unresolved, boundary-adjacent, or bounded outcomes remain visibly incomplete';
  }
  if (activity === 'borrowing_money') {
    return muChartAssessorCanClaimComplete(activity, chartEnrichment)
      ? ' · the Raman same-Rasi Chandra–Kuja/Shani prohibition resolved; purpose-specific qualitative judgment and the shared election baseline remain manual'
      : ' · the Raman same-Rasi Chandra–Kuja/Shani prohibition was attempted; unresolved or bounded outcomes remain review-gated, and the shared election baseline remains incomplete';
  }
  if (activity === 'karnavedha') {
    if (hasScreeningReview) {
      return ' · daylight Tithi and Nakshatra gates resolved; the vacant-8th chart gate has an unresolved fact; the general election-chart baseline is not assessed';
    }
    if (chartEnrichment?.candidateLimitReached) {
      return ' · daylight Tithi and Nakshatra gates resolved; the vacant-8th chart gate was attempted on a bounded candidate set; the general election-chart baseline is not assessed';
    }
    return ' · daylight Tithi, daylight Nakshatra and vacant-8th outcomes all resolved';
  }
  if (partialAssessor) {
    return ' · event-specific clauses computed; overall assessment remains partial/provisional because the shared baseline is not complete';
  }
  return hasScreeningReview ? '' : ' · every implemented event-specific outcome resolved';
}

export function muChartStatusFor(
  activity,
  chartEnrichment,
  hasManualChartGuidance: boolean,
  scopeDetail: string,
) {
  if (!chartEnrichment) return null;
  return {
    screened: {
      title: muChartAssessmentTitle(activity, chartEnrichment),
      detail: chartEnrichment.engine
        ? `${chartEnrichment.engine.name} ${chartEnrichment.engine.version} · ${chartEnrichment.engine.ayanamsha} · ${chartEnrichment.engine.ephemeris} planetary positions · ${chartEnrichment.engine.nodeConvention} lunar nodes · local Drik/Lahiri Lagna frame · whole-sign houses${muChartReviewDetail(chartEnrichment)}${scopeDetail}`
        : 'Every sampled Lagna-stable state checked',
    },
    'not-run': {
      title: 'Chart screening not run',
      detail: 'There was no Panchangam-shortlisted slot to send for chart projection.',
    },
    'manual-only': {
      title: hasManualChartGuidance
        ? 'Panchangam shortlist complete; chart review remains manual'
        : 'Panchangam shortlist complete',
      detail: hasManualChartGuidance
        ? 'This activity’s source guidance is qualitative and stays with a practitioner.'
        : 'No source-specific election-chart condition is defined for this general search.',
    },
    'unsupported-system': {
      title: 'Selected system kept separate',
      detail: 'Exact chart screening currently uses Drik/Lahiri, so it was not blended into this result.',
    },
    disabled: {
      title: 'Panchangam shortlist shown · review needed',
      detail: 'Exact chart screening is intentionally not active in this public build; no slot is presented as chart-screened.',
    },
    unavailable: {
      title: chartEnrichment.screenedCount
        ? 'Partial exact chart screening applied'
        : 'Panchangam shortlist shown',
      detail: chartEnrichment.screenedCount
        ? 'Only already-screened survivors are shown; every unprocessed candidate was withheld.'
        : 'Exact chart screening could not be reached; no slot is presented as chart-screened.',
    },
  }[chartEnrichment.state];
}

function muChartStatusHtml(
  activity,
  chartEnrichment,
  chartStatus,
  sourceScope,
  partialAssessorDisclosure,
): string {
  if (!chartEnrichment || !chartStatus) return '';
  const disposition = muChartScreeningDisposition(chartEnrichment);
  const message = roleForActivity(activity)
    ? chartEnrichment.message
    : chartEnrichment.message.replace('chart or profile facts', 'chart facts');
  return `<section class="mu-chart-status mu-chart-status--${chartEnrichment.state}${muChartStatusDispositionClass(disposition)}" aria-label="Election-chart assessment status">
              <strong>${htmlEsc(chartStatus.title)}</strong>
              <span>${htmlEsc(message)}</span>
              <small>${htmlEsc(chartStatus.detail)}</small>
              ${sourceScope ? `<small class="mu-chart-source-scope"><b>Source scope:</b> ${htmlEsc(sourceScope)}</small>` : ''}
              ${partialAssessorDisclosure ? `<small class="mu-chart-assessment-boundary"><b>Assessment boundary:</b> ${htmlEsc(partialAssessorDisclosure)}</small>` : ''}
              <a href="${MU_CHART_METHOD_URL}">Verify the method and sources</a>
            </section>`;
}

function muNoSlotsResultHtml(options) {
  const {
    droppedEclipseDays, droppedModeDays, chartEnrichment,
    personalRemovalCount, droppedDays, safetyHtml, chartStatusHtml,
    personalRoleHtml, chartRemovalHtml, personalRemovalHtml, droppedHtml,
  } = options;
  const notes = [];
  if (droppedEclipseDays) notes.push(`${droppedEclipseDays} eclipse day(s) deferred`);
  if (droppedModeDays) notes.push(`${droppedModeDays} slot(s) filtered by chandra mode`);
  if (chartEnrichment?.chartRemovedCount) {
    notes.push(`${chartEnrichment.chartRemovedCount} shortlisted slot(s) failed an exact chart requirement`);
  }
  if (personalRemovalCount) {
    notes.push(`${personalRemovalCount} candidate slot(s) failed a profile-specific source rule`);
  }
  const daylightDropped = droppedDays.filter(
    day => Array.isArray(day.daylightOutcomes) && day.daylightOutcomes.length,
  );
  if (daylightDropped.length) {
    notes.push(
      `${daylightDropped.length} Karnavedha day(s) filtered: ${daylightDropped[0].reason}`,
    );
  }
  const suffix = notes.length ? ` · ${notes.join(', ')}` : '';
  const message = `No clear slots found${suffix}. Try more days, relax the standard, or clear the people above.`;
  return {
    message,
    html: `${safetyHtml}${chartStatusHtml}${personalRoleHtml}<p class="preview-error">${htmlEsc(message)}</p>${chartRemovalHtml}${personalRemovalHtml}${droppedHtml}`,
  };
}

function muAnnounceResult(top, chartEnrichment, chartStatus): void {
  const announcement = document.getElementById('mu-result-announcement');
  if (!announcement) return;
  const cappedCount = chartEnrichment?.qualificationCappedCount || 0;
  const reviewCount = chartEnrichment?.reviewGatedCount || 0;
  const overlapCount = chartEnrichment?.overlappingDispositionCount || 0;
  const chartCounts = chartEnrichment?.state === 'screened' ? (
    ` ${cappedCount} retained slot${muPluralSuffix(cappedCount)} capped by a conclusive miss; `
    + `${reviewCount} retained slot${muPluralSuffix(reviewCount)} review-gated by an unknown; `
    + `${overlapCount} included in both counts.`
  ) : '';
  announcement.textContent = `${top.length} slot${muPluralSuffix(top.length)} found. ${chartStatus?.title || 'Search complete'}.${chartCounts}`;
}

export function renderMuhurta() {
  const result = getMuhurtaResult();
  if (!result) return;
  const box = document.getElementById('mu-result');
  const {
    top,
    chartEnrichment,
    activity,
    roleProfile = null,
    droppedEclipseDays = 0,
    droppedModeDays = 0,
    droppedDays = [],
    droppedPersonalRules = [],
  } = result;
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const fmtIso = iso => {
    const [y, mo, da] = iso.split('-').map(Number);
    return new Date(y, mo - 1, da).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };
  const droppedHtml = droppedDays.length
    ? `<details class="mu-dropped"><summary>${droppedDays.length} day${muPluralSuffix(droppedDays.length)} filtered · see why</summary>
         <ul>${droppedDays.map(dd => `<li><span class="dd-date">${fmtIso(dd.date)}</span> · ${htmlEsc(dd.reason)}${muDroppedOutcomeHtml(dd.daylightOutcomes)}</li>`).join('')}</ul>
       </details>`
    : '';
  const partialAssessor = automatedRulesFor(activity).length > 0
    && !chartAssessorCompleteFor(activity);
  const hasManualChartGuidance = muClassifyManualChecks(activity).chart.length > 0
    || partialAssessor;
  const sourceScope = (MU_ACTIVITY[activity] as { source_scope?: string })
    ?.source_scope || null;
  const partialAssessorDisclosure = muEventSpecificCompletionDisclosure(
    activity,
    chartEnrichment,
  );
  const scopeDetail = muResultScopeDetail(activity, chartEnrichment, partialAssessor);
  const chartStatus = muChartStatusFor(
    activity, chartEnrichment, hasManualChartGuidance, scopeDetail,
  );
  const chartStatusHtml = muChartStatusHtml(
    activity, chartEnrichment, chartStatus, sourceScope, partialAssessorDisclosure,
  );
  const roleRequirement = roleForActivity(activity);
  const roleStatus = muRoleStatus(roleProfile, chartEnrichment);
  const personalRoleHtml = roleRequirement
    ? `<div class="mu-personal-role">
         <strong>${htmlEsc(roleRequirement.label)}</strong>
         <span>${htmlEsc(roleStatus)}</span>
       </div>`
    : '';
  const personalRemovalCount = chartEnrichment?.personalRemovedCount
    ?? droppedPersonalRules.reduce((total, rule) => total + rule.count, 0);
  const personalRemovalHtml = personalRemovalCount
    ? `<details class="mu-personal-removals">
         <summary>${personalRemovalCount} candidate slot${muPluralSuffix(personalRemovalCount)} removed by profile-specific source rules</summary>
         <ul>${droppedPersonalRules.map(rule => `<li>${htmlEsc(rule.label)} · ${rule.count} slot${muPluralSuffix(rule.count)}</li>`).join('')}</ul>
       </details>`
    : '';
  const chartRemovedRules = chartEnrichment?.chartRemovedRules || [];
  const chartRemovalHtml = chartEnrichment?.chartRemovedCount
    ? `<details class="mu-chart-removals">
         <summary>${chartEnrichment.chartRemovedCount} candidate slot${muPluralSuffix(chartEnrichment.chartRemovedCount)} removed by exact event-chart rules</summary>
         <ul>${chartRemovedRules.map(rule => muChartRemovalRow(rule)).join('')}</ul>
       </details>`
    : '';
  const safetyOverride = muSafetyOverrideFor(activity);
  const safetyHtml = safetyOverride
    ? `<aside class="mu-safety-override" role="note">
         <strong>${muSafetyTitle(activity)}</strong>
         <span>${htmlEsc(safetyOverride)}</span>
       </aside>`
    : '';
  if (!top.length) {
    const noSlots = muNoSlotsResultHtml({
      droppedEclipseDays, droppedModeDays, chartEnrichment,
      personalRemovalCount, droppedDays, safetyHtml, chartStatusHtml,
      personalRoleHtml, chartRemovalHtml, personalRemovalHtml, droppedHtml,
    });
    box.innerHTML = noSlots.html;
    const announcement = document.getElementById('mu-result-announcement');
    if (announcement) announcement.textContent = noSlots.message;
    return;
  }
  const share = `<button class="wa-share-mini" style="position:static;width:28px;height:28px;flex:none;margin-left:auto;" title="Share these slots on WhatsApp" aria-label="Share on WhatsApp" onclick="shareMuhurtaOnWhatsApp()"><svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg></button>`;
  const muLineClass = (item) => {
    if (/\(\+\d+\)\s*$/.test(item)) return 'mu-pos';
    if (/\(-\d+\)\s*$/.test(item)) return 'mu-neg';
    if (/rectifies/i.test(item)) return 'mu-pos';
    if (/not rectified|remains a personal caution|puja recommended/i.test(item)) return 'mu-caution';
    return '';
  };
  const muCapitalize = (item) => item.charAt(0).toUpperCase() + item.slice(1);
  const renderGroup = (label, items, extraClass = '') => {
    if (!items?.length) return '';
    const lis = items.map(it => `<li class="${muLineClass(it)}">${htmlEsc(muCapitalize(it))}</li>`).join('');
    return `<div class="mu-rg ${extraClass}">
              <span class="mu-rg-label">${htmlEsc(label)}</span>
              <ul class="mu-rg-items">${lis}</ul>
            </div>`;
  };
  const renderChartValidation = items => {
    if (!items?.length) return '';
    const lis = items.map(it => `<li>${htmlEsc(muCapitalize(it))}</li>`).join('');
    return `<div class="mu-rg mu-rg-validation">
              <span class="mu-rg-label">Still needs practitioner review</span>
              <div class="mu-rg-content">
                <p>The source also gives broader chart guidance that is not a complete deterministic algorithm. Automated clauses appear above; a practitioner must interpret what remains:</p>
                <ul class="mu-rg-items">${lis}</ul>
              </div>
            </div>`;
  };
  const renderComputedChart = screening => {
    if (!screening?.outcomes?.length) return '';
    const lis = screening.outcomes.map(outcome => {
      const label = muChartOutcomeLabel(outcome);
      const evidence = Array.isArray(outcome.evidence) && outcome.evidence.length
        ? `<small>Observed: ${htmlEsc(outcome.evidence.join(' '))}</small>`
        : '';
      return `<li class="mu-chart-rule mu-chart-rule--${outcome.effect} mu-chart-rule--${outcome.status}">
                <span>${htmlEsc(muCapitalize(outcome.label))}</span>
                <b>${label}</b>
                ${evidence}
              </li>`;
    }).join('');
    const boundary = muChartBoundaryMessage(screening);
    const sourceReferences = Array.from(new Map<string, { claim: string; locator: string }>(
      screening.outcomes.map(outcome => [
        outcome.sourceClaim,
        { claim: outcome.sourceClaim, locator: outcome.sourceLocator },
      ]),
    ).values());
    const decisionPolicies = [...new Set(
      screening.outcomes
        .map(outcome => outcome.decisionPolicyClaim)
        .filter((claim): claim is string => !!claim),
    )];
    const conventions = Array.from(new Map<string, {
      id: string; label: string; formula: string; claims: string[];
    }>(screening.outcomes
      .filter(outcome => outcome.conventionId)
      .map(outcome => [outcome.conventionId, {
        id: outcome.conventionId,
        label: outcome.conventionLabel || outcome.conventionId,
        formula: outcome.formula || '',
        claims: outcome.methodClaims || [],
      }])).values());
    const {
      eventSourceSuffix,
      decisionPolicyHtml,
      conventionHtml,
      rankingPolicyClaimsHtml,
      conventionClaimsHtml,
    } = muChartProvenanceParts(sourceReferences, decisionPolicies, conventions);
    return `<section class="mu-rg mu-rg-computed" aria-label="Computed election-chart checks">
              <h4 class="mu-rg-label">Computed chart checks</h4>
              <div class="mu-rg-content">
                <ul class="mu-rg-items">${lis}</ul>
                <p class="mu-chart-boundary">${boundary}</p>
                <p class="mu-rule-reference"><strong>Event source${eventSourceSuffix}:</strong>
                  ${sourceReferences.map(reference => htmlEsc(reference.locator)).join('<br>')}
                </p>
                ${decisionPolicyHtml}
                ${conventionHtml}
                <details class="mu-technical-provenance">
                  <summary>Technical provenance</summary>
                  <p><strong>Event claim${eventSourceSuffix}:</strong> ${sourceReferences.map(reference => `<code>${htmlEsc(reference.claim)}</code>`).join(' · ')}</p>
                  ${rankingPolicyClaimsHtml}
                  ${conventionClaimsHtml}
                </details>
                <p class="mu-rule-reference"><a href="${MU_CHART_METHOD_URL}">Method, formulas, assumptions and exact references</a></p>
              </div>
            </section>`;
  };
  const renderComputedDaylight = outcomes => {
    if (!outcomes?.length) return '';
    const lis = outcomes.map(outcome => {
      const label = muDaylightOutcomeLabel(outcome.status);
      const evidence = Array.isArray(outcome.evidence) && outcome.evidence.length
        ? `<small>Observed: ${htmlEsc(outcome.evidence.join(' '))}</small>`
        : '';
      return `<li class="mu-chart-rule mu-chart-rule--reject mu-chart-rule--${outcome.status}">
                <span>${htmlEsc(muCapitalize(outcome.label))}</span>
                <b>${label}</b>
                ${evidence}
              </li>`;
    }).join('');
    const first = outcomes[0];
    return `<section class="mu-rg mu-rg-computed mu-rg-daylight" aria-label="Computed Karnavedha daylight checks">
              <h4 class="mu-rg-label">Computed daylight checks</h4>
              <div class="mu-rg-content">
                <ul class="mu-rg-items">${lis}</ul>
                <p class="mu-chart-boundary">Evaluated once for this day over the half-open interval [local sunrise, local sunset), using the feed's published Tithi and Nakshatra transition boundaries rather than candidate-window samples. A same-minute sunset boundary stays unknown.</p>
                <p class="mu-rule-reference"><strong>Event source:</strong> ${htmlEsc(first.sourceLocator)}</p>
                <details class="mu-technical-provenance">
                  <summary>Technical provenance</summary>
                  <p><strong>Event claim:</strong> <code>${htmlEsc(first.sourceClaim)}</code><br><strong>Named policy:</strong> <code>${htmlEsc(first.policyId)}</code><br><strong>Policy claim:</strong> <code>${htmlEsc(first.decisionPolicyClaim)}</code></p>
                </details>
                <p class="mu-rule-reference"><a href="${MU_CHART_METHOD_URL}">Method, boundary semantics and source crosswalk</a></p>
              </div>
            </section>`;
  };
  const renderPersonalChecks = (outcomes, evidence) => {
    if (!outcomes?.length) return renderGroup(
      'Profile-specific check', evidence, 'mu-rg-personal');
    const lis = outcomes.map((outcome, index) => {
      const label = muPersonalOutcomeLabel(outcome);
      return `<li class="mu-personal-rule mu-personal-rule--${outcome.status}">
                <span>${htmlEsc(muCapitalize(outcome.label))}</span>
                <b>${label}</b>
                ${evidence?.[index] ? `<small>${htmlEsc(evidence[index])}</small>` : ''}
                <span class="mu-rule-claim">Source record <code>${htmlEsc(outcome.sourceClaim)}</code></span>
              </li>`;
    }).join('');
    const sourceLocator = outcomes.find(outcome => outcome.sourceLocator)?.sourceLocator;
    return `<div class="mu-rg mu-rg-personal-computed">
              <span class="mu-rg-label">Profile-specific checks</span>
              <div class="mu-rg-content">
                <ul class="mu-rg-items">${lis}</ul>
                ${sourceLocator ? `<p class="mu-rule-reference">Reference: ${htmlEsc(sourceLocator)} · <a href="${MU_CHART_METHOD_URL}">method and source crosswalk</a></p>` : ''}
              </div>
            </div>`;
  };
  const renderSlot = (s) => {
    const rg = s.reasonGroups;
    const groupsHtml = rg
      ? `<details class="mu-reason-details">
           <summary>Why this slot earned its ${s.tier || muScoreTier(s.score)} rating</summary>
           <div class="mu-rgroups">
             ${renderGroup('Slot quality', rg.slot_quality)}
             ${renderGroup('Day quality', rg.day_quality)}
             ${renderGroup('Group fit', rg.group_fit)}
             ${renderPersonalChecks(rg.personal_outcomes, rg.personal_source)}
             ${renderGroup('Activity', rg.activity_match)}
             ${renderComputedDaylight(rg.day_source_outcomes)}
             ${renderComputedChart(s.chartScreening)}
             ${renderChartValidation(muChartValidationItems(s.chartScreening, rg))}
             ${renderGroup('About this election', rg.information, 'mu-rg-information')}
             ${renderGroup('Practical checks', rg.practical, 'mu-rg-practical')}
             ${renderGroup('Important nuance', rg.notes, 'mu-rg-notes')}
           </div>
         </details>`
      : `<details class="mu-reason-details"><summary>Why this slot ranked here</summary><span class="mu-reasons">${s.reasons.map(reason => htmlEsc(reason)).join(' · ')}</span></details>`;
    const tier = s.tier || muScoreTier(s.score);
    const tierClass = `mu-tier-${tier.toLowerCase()}`;
    const chartDisposition = muChartDispositionHtml(s.chartScreening);
    const dayCtxHtml = muDayContextHtml(s.dayCtx);
    return `<div class="mu-slot">
              <span class="mu-when">${fmtD(s.d)} · ${muToT(s.s0)} to ${muToT(s.e0)}</span>
              <span class="mu-tier ${tierClass}">${tier}</span>
              <span class="mu-score">score ${s.score}</span>
              ${chartDisposition}
              ${dayCtxHtml}
              ${groupsHtml}
            </div>`;
  };
  box.innerHTML =
    `<div class="tb-summary"><span class="count">${top.length}</span>&nbsp;slot${muPluralSuffix(top.length)} found · ranked by tier, then score, then source preference${share}</div>`
    + safetyHtml
    + chartStatusHtml
    + personalRoleHtml
    + chartRemovalHtml
    + personalRemovalHtml
    + `<p class="mu-ranking-note">Excellent slots appear before Good ones. Mandatory chart failures remove a slot. A conclusive event-specific qualification miss retains the slot, leaves its raw score unchanged, and sets Good as its maximum rating. A calculation-boundary unknown also retains the slot and sets the same maximum pending review. Source preferences only break ties; they do not inflate the Panchangam score. Informational patterns do not change ranking and do not support an adverse prediction when absent.</p>`
    + top.map(renderSlot).join('')
    + droppedHtml
    + `<p class="preview-note" style="margin-top:0.5rem;">Each slot's score is the sum of the (+n)/(-n) bonuses across
       Slot quality (choghadiya, Abhijit/Amrita overlap), Day quality (Siddhi yogas, Nitya yoga, Rikta tithi),
       Group fit (per-person tarabalam and chandrabalam), and Activity match (preferred tithi class / vara).
       Being clear of every inauspicious window is a requirement, not a bonus. The tier reflects this score's
       rank within this search, capped below Excellent whenever a named dosha or unresolved review is present.
       Exact event-specific election-chart checks are evaluated at both sides of every known Lagna transition in each window; a failed
       mandatory rule removes the slot, a conclusive qualification miss retains it with unchanged raw score and a maximum Good rating, and a source preference only breaks ties. Houses use the same local Drik/Lahiri
       Lagna frame as the shortlist. A window touching the five-minute transition-convention guard at either edge remains
       review-gated.</p>`;
  muAnnounceResult(top, chartEnrichment, chartStatus);
}

/** Select only non-personal result evidence for the public share payload. */
export function muShareableMuhurtaReasons(slot) {
  const groups = slot?.reasonGroups || {};
  return [
    ...(groups.slot_quality || []),
    ...(groups.day_quality || []),
    ...(groups.activity_match || []),
  ].filter(reason => reason !== 'clear of all inauspicious windows').slice(0, 3);
}

export function muChartShareScreeningLine(chartEnrichment) {
  if (chartEnrichment?.state === 'screened') {
    if (chartEnrichment.candidateLimitReached) {
      return `Exact chart screening reached its safety budget after ${chartEnrichment.screenedCount} candidate${chartEnrichment.screenedCount === 1 ? '' : 's'}; every shown survivor was screened, but lower-ranked candidates were not assessed.`;
    }
    return 'The automated, source-backed election-chart subset was checked across every sampled Lagna-stable state.';
  }
  if (chartEnrichment?.state === 'unavailable' && chartEnrichment.screenedCount > 0) {
    return `Partial exact chart screening was applied to ${chartEnrichment.screenedCount} candidate${chartEnrichment.screenedCount === 1 ? '' : 's'}; only already-screened survivors are included, and unprocessed candidates were withheld.`;
  }
  return 'Panchangam-ranked; exact election-chart screening was not applied.';
}

export function muChartShareIncludesRemainder(chartEnrichment) {
  return chartEnrichment?.state === 'screened'
    || (chartEnrichment?.state === 'unavailable' && chartEnrichment.screenedCount > 0);
}

function muShownSlotNeedsReview(slot): boolean {
  return Boolean(slot.chartScreening?.needsReview) || (
    Array.isArray(slot.reasonGroups?.personal_outcomes)
    && slot.reasonGroups.personal_outcomes.some(
      outcome => outcome?.status === 'unknown')
  );
}

function muEventShareScopeLine(activity: string): string | null {
  if (activity === 'gold') {
    return 'Gold v1 assesses four event-specific clauses; the general election-chart baseline is not assessed.';
  }
  if (activity === 'annaprasana') {
    return 'Annaprasana v1 assesses six event-specific chart clauses; the general election-chart baseline #284 remains open.';
  }
  if (activity === 'karnavedha') {
      return 'Karnavedha v1 assesses two daylight-limb gates and the vacant-eighth chart clause; the general election-chart baseline is not assessed.';
  }
  if (activity === 'court') {
    return 'Court filing v1 assesses five Raman clauses: two mandatory gates, two score-neutral preferences, and one non-ranking information pattern. It does not predict a legal outcome.';
  }
  if (activity === 'borrowing_money') {
    return 'Borrowing v1 applies the primary borrower Janma-star gate locally and assesses Raman’s same-Rasi Chandra–Kuja/Shani prohibition. Purpose-specific qualitative judgment and the shared election baseline remain manual.';
  }
  return null;
}

export function muChartCompletionShareLines(
  activity,
  chartEnrichment,
  remainder,
  qualificationCapped: number,
  reviewGated: number,
): string[] {
  const lines: string[] = [];
  const assessorPartial = automatedRulesFor(activity).length > 0
    && !chartAssessorCompleteFor(activity);
  if (assessorPartial) {
    lines.push('This event assessor is still partial/provisional; the event-specific clauses are computed, but they are not complete chart certification because the shared baseline remains unresolved.');
  }
  if (chartEnrichment.candidateLimitReached) {
    lines.push(`The chart-search safety budget was reached after ${chartEnrichment.screenedCount} candidate${chartEnrichment.screenedCount === 1 ? '' : 's'}; every shown slot was screened, but lower-ranked candidates were not assessed.`);
    return lines;
  }
  if (activity === 'annaprasana' && !remainder.length) {
    lines.push(reviewGated
      ? 'All six Annaprasana event-specific chart clauses were attempted; unresolved facts still require review.'
      : 'All six Annaprasana event-specific chart clauses were evaluated and resolved.');
    return lines;
  }
  if (!remainder.length) {
    if (reviewGated) {
      lines.push('All disclosed event chart clauses were attempted; unresolved facts still require review.');
    } else if (qualificationCapped) {
      lines.push('All disclosed event chart clauses were evaluated; one or more qualifications were not met and the affected ratings were capped.');
    } else {
      lines.push('All disclosed event chart clauses were evaluated and resolved under the documented interpretation convention.');
    }
    return lines;
  }
  lines.push(
    'The automated, source-backed election-chart clauses were checked across every sampled Lagna-stable state.',
    'Qualitative chart or ritual checks still require practitioner review; see the result details.',
  );
  return lines;
}

function muChartCountShareLines(
  qualificationCapped: number,
  reviewGated: number,
  overlapping: number,
): string[] {
  const lines: string[] = [];
  if (qualificationCapped) {
    lines.push(`${qualificationCapped} shown slot${qualificationCapped === 1 ? '' : 's'} had a conclusive event-specific condition miss; ${qualificationCapped === 1 ? 'it was' : 'they were'} retained with unchanged raw score and a maximum Good rating.`);
  }
  if (reviewGated) {
    lines.push(`${reviewGated} shown slot${reviewGated === 1 ? '' : 's'} ${reviewGated === 1 ? 'is' : 'are'} indeterminate at a calculation boundary or missing fact and ${reviewGated === 1 ? 'remains' : 'remain'} review-gated.`);
  }
  if (overlapping) {
    lines.push(`${overlapping} shown slot${overlapping === 1 ? ' is' : 's are'} included in both counts because a conclusive miss and a separate unknown coexist.`);
  }
  return lines;
}

function muChartShareDetailLines(top, activity, chartEnrichment): string[] {
  const remainder = chartManualRemaindersFor(activity) || [];
  const qualificationCapped = top.filter(
    slot => slot.chartScreening?.qualificationFailed).length;
  const reviewGated = top.filter(muShownSlotNeedsReview).length;
  const overlapping = top.filter(
    slot => slot.chartScreening?.qualificationFailed
      && muShownSlotNeedsReview(slot)).length;
  const scopeLine = muEventShareScopeLine(activity);
  return [
    ...(scopeLine ? [scopeLine] : []),
    ...muChartCompletionShareLines(
      activity, chartEnrichment, remainder, qualificationCapped, reviewGated,
    ),
    ...muChartCountShareLines(qualificationCapped, reviewGated, overlapping),
    `Method: https://panchangam.astrochaganti.com${MU_CHART_METHOD_URL}`,
  ];
}


export function shareMuhurtaOnWhatsApp() {
  const result = getMuhurtaResult();
  if (!result?.top.length) return;
  const { top, activity, chartEnrichment, context } = result;
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const lines = [];
  lines.push(
    `⏱ *Good time slots · ${MU_ACT_LABEL[activity]}*`,
    `📍 ${context.cityLabel} · ${context.fromIso} to ${context.toIso}`,
  );
  if (roleForActivity(activity)) {
    lines.push('Source-specific personal checks were applied locally when possible; profile details are intentionally omitted from this share.');
  }
  lines.push(muChartShareScreeningLine(chartEnrichment));
  if (muChartShareIncludesRemainder(chartEnrichment)) {
    lines.push(...muChartShareDetailLines(top, activity, chartEnrichment));
  }
  lines.push('');
  top.slice(0, 5).forEach(s => {
    lines.push(`• ${s.tier || muScoreTier(s.score)} · ${fmtD(s.d)} · ${muToT(s.s0)} to ${muToT(s.e0)}`);
    const shareableReasons = muShareableMuhurtaReasons(s);
    if (shareableReasons.length) lines.push(`   ${shareableReasons.join(' · ')}`);
  });
  lines.push(
    '',
    'Every slot is clear of Rahu Kalam, Varjyam and all inauspicious windows.',
    'Find your own: https://panchangam.astrochaganti.com/?src=share-slots#tarabalam',
  );
  gcEvent('share-slots');
  window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
}
