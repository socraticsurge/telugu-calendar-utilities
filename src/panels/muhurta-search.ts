import { selEl, inpEl } from '../lib/dom';
import { getSelection } from '../selection-store';
import { loadFeed } from '../lib/feed-loader';
import { stampOf } from '../lib/format';
import { htmlEsc } from '../lib/html';
import { loadLagna } from '../lib/lagna-loader';
import { CITY_LOCATIONS } from '../data/cities';
import activityContract from '../data/activity-rules.generated.json';
import { enrichElectionChartSlots } from '../scorer/election-chart-enrichment';
import { electionChartCalculationEnabled } from '../lib/remote-calculation-activation';
import { getLoadedEvents } from './today';
import {
  clearMuhurtaResult,
  hasMuhurtaResult,
  setMuhurtaResult,
} from './muhurta-result-state';
import {
  tbBorrowingPurpose,
  tbProfiles,
  tbRoleParticipant,
} from './tarabalam-profile-controller';
import { tbMode } from './tarabalam-journey';
import { renderMuhurta } from './muhurta-presentation';
import {
  createMuhurtaPipelineState,
  processMuhurtaDay,
} from './muhurta-day-pipeline';

const MU_ACTIVITY = activityContract.rules;
let MU_SEARCH_SEQUENCE = 0;
let MU_CHART_ABORT = null;

function muSetResultMessage(box, message, role = 'status') {
  box.innerHTML = `<p class="preview-error">${htmlEsc(message)}</p>`;
  const announcement = document.getElementById('mu-result-announcement');
  if (announcement) {
    announcement.setAttribute('role', role);
    announcement.textContent = message;
  }
}

/** Invalidate both pending and completed Muhurtam results after any scoring input changes. */
export function invalidateMuhurtaSearch(announce = true) {
  const hadResult = hasMuhurtaResult() || !!MU_CHART_ABORT;
  MU_SEARCH_SEQUENCE += 1;
  MU_CHART_ABORT?.abort();
  MU_CHART_ABORT = null;
  clearMuhurtaResult();
  const box = document.getElementById('mu-result');
  if (box) {
    box.setAttribute('aria-busy', 'false');
    if (announce && hadResult) {
      muSetResultMessage(box, 'Search inputs changed · find slots again.');
    }
  }
}

function muCurrentSearchFingerprint() {
  const selection = getSelection();
  const activity = selEl('mu-activity').value || 'any';
  const people = tbProfiles().map(person => ({
    id: person.id,
    name: person.name,
    nak: person.nak,
    rasi: person.rasi,
    lagna: person.lagna,
  }));
  const role = tbRoleParticipant(activity);
  const borrowingPurpose = activity === 'borrowing_money'
    ? tbBorrowingPurpose()
    : null;
  return JSON.stringify({
    activity,
    from: inpEl('tb-from').value || '',
    to: inpEl('tb-to').value || '',
    city: selection.city,
    system: selection.system,
    chandraMode: tbMode(),
    people,
    roleId: role?.id || null,
    borrowingPurpose,
  });
}

import {
  muActivityNeedsLagna,
  muRankCandidateSlots,
} from './muhurta-scoring';

function muSearchIsStale(searchSequence: number, fingerprint: string, box): boolean {
  if (searchSequence !== MU_SEARCH_SEQUENCE) return true;
  if (fingerprint === muCurrentSearchFingerprint()) return false;
  box.setAttribute('aria-busy', 'false');
  muSetResultMessage(box, 'Search inputs changed · find slots again.');
  return true;
}

function muSetShortlistProgress(box, slots): void {
  if (!slots.length) return;
  if (electionChartCalculationEnabled()) {
    muSetResultMessage(box, 'Shortlist ready · screening exact election charts…');
    return;
  }
  muSetResultMessage(
    box,
    'Shortlist ready · exact chart screening is not active in this build.',
  );
}

export function muUnavailableChartEnrichment(slots) {
  return {
    state: 'unavailable',
    slots: slots.slice(0, 10).map(slot => ({
      ...slot,
      tier: slot.tier === 'Excellent' ? 'Good' : slot.tier,
      dayDosha: slot.dayDosha || 'practitioner_review',
    })),
    screenedCount: 0,
    removedCount: 0,
    candidateLimitReached: false,
    chartRemovedCount: 0,
    chartRemovedRules: [],
    personalRemovedCount: 0,
    personalRemovedRules: [],
    boundaryReviewCount: 0,
    qualificationCappedCount: 0,
    reviewGatedCount: slots.length,
    overlappingDispositionCount: 0,
    message: 'Panchangam-ranked; exact chart screening is unavailable for this city.',
    engine: null,
  };
}

async function muEnrichCandidateSlots(options) {
  const {
    slots, activity, system, city, roleProfile,
    lagnaCityData, signal,
  } = options;
  const location = CITY_LOCATIONS[city];
  if (!location) return muUnavailableChartEnrichment(slots);
  return enrichElectionChartSlots(slots, {
    activity,
    system,
    location,
    personalParticipant: roleProfile ? {
      id: roleProfile.id,
      name: roleProfile.name,
      nakshatra: roleProfile.nak || null,
      janmaRashi: roleProfile.rasi || null,
      janmaLagna: roleProfile.lagna || null,
    } : null,
    boundarySupportAvailable: !!lagnaCityData
      && slots.every(slot => slot.chartBoundarySupported === true),
    signal,
  });
}

function muBeginSearch() {
  const searchSequence = ++MU_SEARCH_SEQUENCE;
  MU_CHART_ABORT?.abort();
  const chartAbort = new AbortController();
  MU_CHART_ABORT = chartAbort;
  const box = document.getElementById('mu-result');
  box.setAttribute('aria-busy', 'true');
  muSetResultMessage(box, 'Searching…');
  const activity = selEl('mu-activity').value;
  const from = new Date(inpEl('tb-from').value + 'T00:00:00');
  const to = new Date(inpEl('tb-to').value + 'T00:00:00');
  const nDays = Math.min(60, Math.max(1, Math.round((to.getTime() - from.getTime()) / 86400000) + 1));
  const people = tbProfiles();
  const roleProfile = tbRoleParticipant(activity);
  const borrowingPurpose = activity === 'borrowing_money'
    ? tbBorrowingPurpose()
    : 'other_or_unknown';
  const searchFingerprint = muCurrentSearchFingerprint();
  const chandraMode = tbMode();  // 'stars' | 'puja_ok' | 'strict' — filters only, never scores
  return {
    searchSequence,
    chartAbort,
    box,
    activity,
    from,
    nDays,
    people,
    roleProfile,
    borrowingPurpose,
    searchFingerprint,
    chandraMode,
  };
}

function muSearchContextHtml(search) {
  const { people } = search;
  return people.length
    ? `Searching <strong>${inpEl('tb-from').value}</strong> to <strong>${inpEl('tb-to').value}</strong>, screened by the stars of <strong>${people.map(p => htmlEsc(p.name)).join(', ')}</strong> (set above).`
    : `Searching <strong>${inpEl('tb-from').value}</strong> to <strong>${inpEl('tb-to').value}</strong> · no people set above, so no star screening.`;
}

async function muLoadSearchData(search) {
  const { city, system } = getSelection();
  const citySelect = selEl('tp-city');
  const context = {
    city,
    cityLabel: citySelect.options[citySelect.selectedIndex]?.textContent || city,
    system,
    fromIso: inpEl('tb-from').value,
    toIso: inpEl('tb-to').value,
    fingerprint: search.searchFingerprint,
  };
  const events = getLoadedEvents() || await loadFeed(city, system);
  const activityRules = MU_ACTIVITY[search.activity] || MU_ACTIVITY.any;
  const activityNeedsLagna = muActivityNeedsLagna(search.activity, activityRules);
  const lagnaCityData = (search.people.length || activityNeedsLagna)
    ? await loadLagna(city) : null;
  return { city, system, context, events, lagnaCityData };
}

function muCollectCandidates(search, loaded) {
  const pipelineState = createMuhurtaPipelineState();
  const pipelineContext = {
    activity: search.activity,
    system: loaded.system,
    chartLocation: CITY_LOCATIONS[loaded.city] || null,
    lagnaCityData: loaded.lagnaCityData,
    people: search.people,
    chandraMode: search.chandraMode,
    borrowingPurpose: search.borrowingPurpose,
  };
  for (let i = 0; i < search.nDays; i++) {
    const day = new Date(search.from);
    day.setDate(day.getDate() + i);
    const event = loaded.events.get(stampOf(day));
    if (event) processMuhurtaDay(pipelineContext, pipelineState, day, event);
  }
  muRankCandidateSlots(pipelineState.slots);
  return pipelineState;
}

async function muExecuteSearch(search) {
  const loaded = await muLoadSearchData(search);
  const pipelineState = muCollectCandidates(search, loaded);
  const { slots } = pipelineState;
  if (muSearchIsStale(
    search.searchSequence, search.searchFingerprint, search.box,
  )) return;
  muSetShortlistProgress(search.box, slots);
  const chartEnrichment = await muEnrichCandidateSlots({
    slots,
    activity: search.activity,
    system: loaded.system,
    city: loaded.city,
    roleProfile: search.roleProfile,
    lagnaCityData: loaded.lagnaCityData,
    signal: search.chartAbort.signal,
  });
  if (muSearchIsStale(
    search.searchSequence, search.searchFingerprint, search.box,
  )) return;
  setMuhurtaResult({
    top: chartEnrichment.slots,
    chartEnrichment,
    droppedEclipseDays: pipelineState.droppedEclipseDays,
    droppedModeDays: pipelineState.droppedModeSlots,
    droppedDays: pipelineState.droppedDays,
    droppedPersonalRules: chartEnrichment.personalRemovedRules,
    activity: search.activity,
    people: search.people,
    chandraMode: search.chandraMode,
    roleProfile: search.roleProfile,
    borrowingPurpose: search.borrowingPurpose,
    context: loaded.context,
  });
  renderMuhurta();
}

function muHandleSearchError(search) {
  if (search.chartAbort.signal.aborted
      || search.searchSequence !== MU_SEARCH_SEQUENCE) return;
    // Internal feed or chart details stay private; expose one stable recovery action.
  muSetResultMessage(search.box, 'Could not load the feed. Try again.', 'alert');
}

function muFinishSearch(search) {
  if (MU_CHART_ABORT !== search.chartAbort
      || search.searchSequence !== MU_SEARCH_SEQUENCE) return;
  search.box.setAttribute('aria-busy', 'false');
  MU_CHART_ABORT = null;
}

export async function findMuhurta() {
  const search = muBeginSearch();
  document.getElementById('mu-context').innerHTML = muSearchContextHtml(search);
  try {
    await muExecuteSearch(search);
  } catch {
    muHandleSearchError(search);
  } finally {
    muFinishSearch(search);
  }
}
