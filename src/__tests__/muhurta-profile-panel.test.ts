import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, test, vi, type Mock } from 'vitest';
import {
  GUEST_BIRTH_PROFILE_STORAGE_KEY,
  GUEST_PROFILE_COMMIT_STORAGE_KEY,
  GUEST_PROFILE_STORAGE_KEY,
  createGuestProfileStore,
  type GuestProfileStore,
  type ProfileStorage,
} from '../lib/guest-profile-store';
import {
  MUHURTAM_PROFILE_IDS_STORAGE_KEY,
  MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY,
} from '../lib/profile-selection';
import type {
  ElectionChartRequest,
  ElectionChartSnapshot,
} from '../lib/election-chart-api';
import {
  enrichElectionChartSlots,
  type EnrichableMuhurtamSlot,
} from '../scorer/election-chart-enrichment';

interface Participant {
  id: string;
  name: string;
  nak: string;
  pada: 1 | 2 | 3 | 4 | null;
  rasi: string | null;
  lagna: string | null;
}

interface ManualCheckRow {
  text: string;
  display_section: 'chart' | 'information' | 'practical';
  applicable_varas?: string[];
  purpose?: string;
}

interface ProfilesController {
  destroy(): void;
  getParticipants(): Participant[];
  getSelectedIds(): string[];
  getRoleParticipant(activity: string): Participant | null;
  selectProfile(id: string): boolean;
}

interface TarabalamPanelModule {
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
  muRelevantManualChecks(activity: string, vaaram: string): ManualCheckRow[];
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
}

class MemoryStorage implements ProfileStorage {
  readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

class BrowserMemoryStorage extends MemoryStorage implements Storage {
  get length(): number {
    return this.values.size;
  }

  clear(): void {
    this.values.clear();
  }

  key(index: number): string | null {
    return Array.from(this.values.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }
}

class DeniedStorage implements ProfileStorage {
  getItem(): string | null {
    throw new Error('read denied');
  }

  setItem(): void {
    throw new Error('write denied');
  }
}

function ids(...values: string[]): () => string {
  let index = 0;
  return () => values[index++] || `guest_generated_${index}`;
}

function renderPanelFixture(): void {
  document.body.innerHTML = `
    <section class="tb-section">
      <header><button class="tb-reset" onclick="tbResetProfiles()">clear all</button></header>
      <div id="tb-profiles"></div>
      <button id="tb-add-btn" class="tb-add" onclick="tbAddRow()">add</button>
    </section>
    <div id="tb-summary">old summary</div>
    <div id="tb-result">old result</div>
    <div id="mu-context">old context</div>
    <div id="mu-result">old slots</div>
    <input id="tb-from" value="2026-08-28">
    <input id="tb-to" value="2026-09-04">
    <select id="mu-activity">
      <option value="wedding" selected>Wedding</option>
      <option value="gold">Gold</option>
      <option value="travel">Travel</option>
      <option value="gruhapravesha">Gruhapravesha</option>
      <option value="seemantha">Seemantha</option>
      <option value="surgery">Surgery</option>
    </select>
  `;
}

function changeCheckbox(id: string, checked: boolean): void {
  const checkbox = document.querySelector<HTMLInputElement>(
    `input[data-profile-selection="${id}"]`,
  );
  if (!checkbox) throw new Error(`Missing profile checkbox ${id}`);
  checkbox.checked = checked;
  checkbox.dispatchEvent(new Event('change', { bubbles: true }));
}

function clickAction(action: string): HTMLButtonElement {
  const button = document.querySelector<HTMLButtonElement>(`button[data-action="${action}"]`);
  if (!button) throw new Error(`Missing action ${action}`);
  button.click();
  return button;
}

function chooseManualValues(values: {
  name?: string;
  nakshatra?: string;
  pada?: string;
  lagna?: string;
}): void {
  let row = document.querySelector<HTMLElement>('[data-manual-id]');
  if (!row) throw new Error('Missing manual participant');
  if (values.name !== undefined) {
    const input = row.querySelector<HTMLInputElement>('input[type="text"]')!;
    input.value = values.name;
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }
  if (values.nakshatra !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[0];
    select.value = values.nakshatra;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
  row = document.querySelector<HTMLElement>('[data-manual-id]')!;
  if (values.pada !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[1];
    select.value = values.pada;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
  row = document.querySelector<HTMLElement>('[data-manual-id]')!;
  if (values.lagna !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[2];
    select.value = values.lagna;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
}

let panel: TarabalamPanelModule;
let controller: ProfilesController | null = null;
let profileStorage: MemoryStorage;
let browserStorage: BrowserMemoryStorage;
let store: GuestProfileStore;
let createProfile: Mock<(trigger: HTMLElement) => void>;
let editProfile: Mock<(id: string, trigger: HTMLElement) => void>;
let manageProfiles: Mock<(trigger: HTMLElement) => void>;

function initialize(): ProfilesController {
  controller = panel.initTarabalamProfiles(
    store,
    { createProfile, editProfile, manageProfiles },
  );
  return controller;
}

beforeAll(async () => {
  // Keep the deliberately relaxed, DOM-heavy legacy panel out of the strict
  // core TypeScript graph while still exercising its real runtime module.
  const panelPath = '../panels/' + 'tarabalam';
  panel = await import(panelPath) as TarabalamPanelModule;
});

beforeEach(() => {
  browserStorage = new BrowserMemoryStorage();
  vi.stubGlobal('localStorage', browserStorage);
  renderPanelFixture();
  profileStorage = new MemoryStorage();
  store = createGuestProfileStore(profileStorage);
  createProfile = vi.fn<(trigger: HTMLElement) => void>();
  editProfile = vi.fn<(id: string, trigger: HTMLElement) => void>();
  manageProfiles = vi.fn<(trigger: HTMLElement) => void>();
});

afterEach(() => {
  controller?.destroy();
  controller = null;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

afterAll(() => {
  vi.unstubAllGlobals();
});

describe('Muhurtam saved-profile participants', () => {
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
    expect(panel.muChartOutcomeLabel({ effect: 'reject', status: 'pass' }))
      .toBe('Required check passed');
    expect(panel.muChartOutcomeLabel({ effect: 'reject', status: 'unknown' }))
      .toBe('Required check could not be verified');
    expect(panel.muChartOutcomeLabel({ effect: 'reject', status: 'fail' }))
      .toBe('Removed by mandatory chart rule');
    expect(panel.muChartOutcomeLabel({ effect: 'qualify', status: 'pass' }))
      .toBe('Qualification met');
    expect(panel.muChartOutcomeLabel({ effect: 'qualify', status: 'unknown' }))
      .toBe('Indeterminate at calculation boundary · review needed');
    expect(panel.muChartOutcomeLabel({ effect: 'qualify', status: 'fail' }))
      .toBe('Condition not met · slot retained · raw score unchanged · maximum rating Good');
    expect(panel.muChartOutcomeLabel({ effect: 'prefer', status: 'pass' }))
      .toBe('Preference met · tie-break only');
    expect(panel.muChartOutcomeLabel({ effect: 'prefer', status: 'unknown' }))
      .toBe('Preference could not be verified');
    expect(panel.muChartOutcomeLabel({ effect: 'prefer', status: 'fail' }))
      .toBe('Preference not present · no penalty');
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

  test('keeps extracted result fragments text- and markup-equivalent', () => {
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
    expect(panel.muSafetyTitle('surgery')).toBe('Medical care overrides timing');
    expect(panel.muSafetyTitle('court')).toBe('Legal duties override timing');
    expect(panel.tbChandraVerdict(1)).toBe('good');
    expect(panel.tbChandraVerdict(2)).toBe('puja');
    expect(panel.tbChandraVerdict(4)).toBe('bad');
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
    expect(panel.muChartAssessmentTitle('purchase', dispositionBase))
      .toBe('Exact chart screening applied');
  });

  test('samples both sides of every Lagna transition inside a slot', () => {
    const day = {
      sunrise: '06:00',
      lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [70, 6],
        [95, 7], [200, 8], [300, 9], [400, 10], [500, 11], [600, 0],
      ],
      cycleEnd: 1440,
    };
    const minutes = panel.muChartCheckMinutes(day, 420, 470);
    expect(minutes).toEqual([
      420, 429, 430, 431, 440, 450, 454, 455, 456, 460, 469,
    ]);
    expect(panel.muChartLagnasForMinutes(day, minutes)).toEqual([
      'Kanya', 'Kanya', 'Tula', 'Tula', 'Tula',
      'Tula', 'Tula', 'Vrischika', 'Vrischika', 'Vrischika', 'Vrischika',
    ]);
    expect(panel.muChartBoundaryNeedsReview(day, 420, 470)).toBe(false);
    expect(panel.muChartBoundaryNeedsReview(day, 430, 470)).toBe(true);
    expect(panel.muChartBoundaryNeedsReview(day, 420, 430)).toBe(true);
  });

  test('feeds the canonical Sydney boundary plan into conservative chart decisions', async () => {
    const hyderabadDay = {
      sunrise: '06:49',
      lagna0: 10,
      transitions: Array.from({ length: 12 }, (_, index) => [
        210 + index * 100,
        (11 + index) % 12,
      ]),
      cycleEnd: 1440,
    };
    const hyderabadMinutes = panel.muChartCheckMinutes(hyderabadDay, 619, 620);
    expect(hyderabadMinutes).toEqual([619]);
    expect(panel.muChartLagnasForMinutes(hyderabadDay, hyderabadMinutes))
      .toEqual(['Meena']);
    expect(panel.muChartBoundaryNeedsReview(hyderabadDay, 619, 620)).toBe(true);

    const day = {
      sunrise: '06:49',
      lagna0: 5,
      transitions: Array.from({ length: 12 }, (_, index) => [
        466 + index * 80,
        (6 + index) % 12,
      ]),
      cycleEnd: 1440,
    };
    const buildSlot = (
      startMinute: number,
      endMinute: number,
    ): EnrichableMuhurtamSlot => {
      const minutes = panel.muChartCheckMinutes(day, startMinute, endMinute);
      return {
        isoDate: '2026-05-28',
        s0: startMinute,
        e0: endMinute,
        score: 12,
        tier: 'Excellent',
        dayDosha: null,
        reasonGroups: {},
        chartCheckMinutes: minutes,
        chartCheckLagnas: panel.muChartLagnasForMinutes(day, minutes),
        chartBoundarySupported: panel.muValidLagnaDayData(day),
        chartBoundaryNeedsReview: panel.muChartBoundaryNeedsReview(
          day, startMinute, endMinute,
        ),
      };
    };
    const planets = [
      'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
      'Shukra', 'Shani', 'Rahu', 'Ketu',
    ];
    const derive = vi.fn(async (request: ElectionChartRequest) => ({
      contractVersion: '1.0' as const,
      engine: {
        name: 'DashaFlow', version: '1.1.0', ayanamsha: 'Lahiri',
        ephemeris: 'swiss' as const, nodeConvention: 'mean' as const,
      },
      houseSystem: 'whole_sign' as const,
      location: request.location,
      charts: request.instants.map((instant, index): ElectionChartSnapshot => ({
        instant,
        // The sidecar changes two minutes after the canonical 14:35 boundary.
        lagna: { rashi: index < request.instants.length - 1 ? 'Kanya' : 'Tula', degree: 29.5 },
        planets: planets.map((name, planetIndex) => ({
          name,
          rashi: name === 'Kuja' ? 'Vrishabha' : 'Kanya',
          degree: planetIndex + 0.25,
          house: 12,
          retrograde: name === 'Rahu' || name === 'Ketu',
        })),
      })),
    }));

    const edge = buildSlot(875, 876);
    expect(edge.chartCheckLagnas).toEqual(['Tula']);
    expect(edge.chartBoundaryNeedsReview).toBe(true);
    const edgeResult = await enrichElectionChartSlots([edge], {
      activity: 'wedding', system: 'drik',
      location: { latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
      derive,
    });
    expect(edgeResult.slots).toHaveLength(1);
    expect(edgeResult.slots[0].tier).toBe('Good');
    expect(edgeResult.slots[0].chartScreening).toEqual(expect.objectContaining({
      boundaryConventionUncertain: true,
      rejected: false,
      needsReview: true,
    }));

    const fullBand = buildSlot(869, 882);
    expect(fullBand.chartBoundaryNeedsReview).toBe(false);
    expect(new Set(fullBand.chartCheckLagnas)).toEqual(new Set(['Kanya', 'Tula']));
    const fullResult = await enrichElectionChartSlots([fullBand], {
      activity: 'wedding', system: 'drik',
      location: { latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
      derive,
    });
    expect(fullResult.slots).toEqual([]);
    expect(fullResult.chartRemovedCount).toBe(1);
  });

  test.each([
    null,
    { sunrise: '06:00', lagna0: 0, transitions: [], cycleEnd: 1440 },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [105, 0],
      ],
      cycleEnd: 1440,
    },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 2],
      ],
      cycleEnd: 1440,
    },
  ])('rejects malformed Lagna day evidence %#', malformed => {
    expect(panel.muValidLagnaDayData(malformed)).toBe(false);
    expect(panel.muChartCheckMinutes(malformed, 420, 470)).toEqual([420, 469]);
    expect(panel.muChartLagnasForMinutes(malformed, [420, 469])).toBeNull();
    expect(panel.muChartBoundaryNeedsReview(malformed, 420, 470)).toBe(true);
  });

  test('accepts a validated second-cycle tail from current generated data', () => {
    const extended = {
      sunrise: '06:00',
      lagna0: 3,
      transitions: Array.from({ length: 24 }, (_, index) => [
        (index + 1) * 55,
        (4 + index) % 12,
      ]),
      cycleEnd: 2880,
    };
    expect(panel.muValidLagnaDayData(extended)).toBe(true);
  });

  test('accepts the published Hyderabad terminal transition at exclusive cycle end', () => {
    const publishedHyderabadDay = {
      date: '2026-09-17',
      sunrise: '06:04',
      guruCombust: false,
      shukraCombust: false,
      lagna0: 4,
      transitions: [
        [4, 5], [129, 6], [259, 7], [393, 8], [519, 9],
        [630, 10], [728, 11], [823, 0], [928, 1], [1049, 2],
        [1181, 3], [1313, 4], [1440, 5],
      ],
      cycleEnd: 1440,
    };

    expect(panel.muValidLagnaDayData(publishedHyderabadDay)).toBe(true);
    expect(panel.muChartLagnasForMinutes(publishedHyderabadDay, [364, 367, 368]))
      .toEqual(['Simha', 'Simha', 'Kanya']);
    const cycleEndMinute = 364 + publishedHyderabadDay.cycleEnd;
    expect(panel.muChartLagnasForMinutes(
      publishedHyderabadDay, [cycleEndMinute - 10, cycleEndMinute - 1],
    )).toEqual(['Simha', 'Simha']);
    expect(panel.muChartLagnasForMinutes(
      publishedHyderabadDay, [cycleEndMinute],
    )).toBeNull();
    expect(panel.muChartLagnasForMinutes(
      publishedHyderabadDay, [cycleEndMinute - 1, cycleEndMinute],
    )).toBeNull();
    expect(panel.muChartCheckMinutes(
      publishedHyderabadDay, cycleEndMinute - 10, cycleEndMinute,
    )).toEqual([cycleEndMinute - 10, cycleEndMinute - 1]);
    expect(panel.muChartBoundaryNeedsReview(
      publishedHyderabadDay, cycleEndMinute - 10, cycleEndMinute,
    )).toBe(true);
  });

  test('accepts a published Sydney second-cycle terminal transition', () => {
    const transitionOffsets = [
      5, 84, 174, 286, 422, 567, 710, 853, 997, 1139, 1261, 1359,
      1441, 1520, 1610, 1723, 1859, 2003, 2146, 2289, 2433, 2575,
      2697, 2795, 2877,
    ];
    const publishedSydneyDay = {
      date: '2026-09-17',
      sunrise: '05:52',
      lagna0: 4,
      transitions: transitionOffsets.map((offset, index) => [
        offset, (5 + index) % 12,
      ]),
      cycleEnd: 2877,
    };

    expect(panel.muValidLagnaDayData(publishedSydneyDay)).toBe(true);
  });

  test.each([
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 0],
        [1440, 1], [1441, 2],
      ],
      cycleEnd: 1440,
    },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 0],
        [1440, 3],
      ],
      cycleEnd: 1440,
    },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [20, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 0],
        [1441, 1],
      ],
      cycleEnd: 1440,
    },
    {
      sunrise: '06:00', lagna0: 0,
      transitions: [
        [10, 1], [0, 2], [30, 3], [40, 4], [50, 5], [60, 6],
        [70, 7], [80, 8], [90, 9], [100, 10], [110, 11], [120, 0],
      ],
      cycleEnd: 1440,
    },
  ])('rejects invalid terminal or post-cycle Lagna transitions %#', malformed => {
    expect(panel.muValidLagnaDayData(malformed)).toBe(false);
  });

  test('accepts a first transition rounded to the sunrise minute', () => {
    const roundedAtSunrise = {
      sunrise: '06:00',
      lagna0: 3,
      transitions: Array.from({ length: 13 }, (_, index) => [
        index * 60,
        (4 + index) % 12,
      ]),
      cycleEnd: 1440,
    };
    expect(panel.muValidLagnaDayData(roundedAtSunrise)).toBe(true);
    expect(panel.muChartCheckMinutes(roundedAtSunrise, 360, 390)).toEqual([
      360, 361, 370, 380, 389,
    ]);
    expect(panel.muChartBoundaryNeedsReview(roundedAtSunrise, 360, 390)).toBe(true);
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

  test('uses the generated contract instead of presentation-time regex inference', () => {
    const surgery = panel.muClassifyManualChecks('surgery');
    expect(surgery.practical.join(' ')).toMatch(/Medical urgency.*clinician/i);
    expect(surgery.chart.join(' ')).toMatch(/Mangala.*8th house/i);

    const home = panel.muClassifyManualChecks('gruhapravesha');
    expect(home.chart).toContain(
      'The owner’s Janma Rasi, Nakshatra or Lagna may strengthen the election.',
    );
    expect(home.information).toContain('Complete worship and Bhootabali before entry.');

    const karnavedha = panel.muClassifyManualChecks('karnavedha');
    expect(karnavedha.chart).toContain(
      'Election chart: leave the 8th house unoccupied.',
    );
  });

  test('filters only manual rows with explicit Vara applicability', () => {
    const guidance = (activity: string, vaaram: string) =>
      panel.muClassifyManualChecks(
        activity,
        panel.muRelevantManualChecks(activity, vaaram),
      );

    expect(guidance('upanayana', 'Budhavaram').chart.join(' '))
      .toContain('Reject Wednesday when Budha is combust.');
    expect(guidance('upanayana', 'Guruvaram').chart.join(' '))
      .not.toContain('Reject Wednesday when Budha is combust.');

    for (const vaaram of ['Somavaram', 'Shukravaram']) {
      expect(guidance('home_repair', vaaram).chart.join(' '))
        .toContain('Weekday-Lagna condition');
    }
    expect(guidance('home_repair', 'Budhavaram').chart.join(' '))
      .not.toContain('Weekday-Lagna condition');

    expect(guidance('business_inventory_purchase', 'Shanivaram').information)
      .toContain('Saturday is described as passable, not preferred.');
    expect(guidance('business_inventory_purchase', 'Somavaram').information)
      .not.toContain('Saturday is described as passable, not preferred.');
  });

  test('keeps purchase and lineage rows visible regardless of weekday text', () => {
    const mondayPurchase = panel.muClassifyManualChecks(
      'purchase',
      panel.muRelevantManualChecks('purchase', 'Somavaram'),
    );
    expect(mondayPurchase.chart.join(' ')).toContain(
      'Marketplace check from verse 17: avoid Rikta Tithis, Tuesday',
    );

    for (const activity of ['lending_money', 'wedding', 'gruhapravesha']) {
      const monday = panel.muClassifyManualChecks(
        activity,
        panel.muRelevantManualChecks(activity, 'Somavaram'),
      );
      expect(monday.information.join(' ')).toMatch(/Lineage warning:/);
    }
  });

  test('selects safety overrides by structured purpose', () => {
    expect(panel.muSafetyOverrideFor('surgery')).toMatch(
      /^Medical urgency.*clinician/s,
    );
    expect(panel.muSafetyOverrideFor('court')).toMatch(
      /^Legal deadlines, court rules/s,
    );
    expect(panel.muSafetyOverrideFor('purchase')).toBeNull();
  });

  test('feeds only checked, ready stable-ID adapters to the existing calculation seam', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo', 'guest_incomplete'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta', lagna: 'Karka' });
    store.create({ name: 'Needs star' });
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '["guest_alpha"]');

    initialize();

    expect(panel.tbProfiles()).toEqual([{
      id: 'guest_alpha', name: 'Alpha', nak: 'Rohini', pada: null,
      rasi: 'Vrishabha', lagna: null,
    }]);
    expect(document.querySelector<HTMLInputElement>(
      'input[data-profile-selection="guest_incomplete"]',
    )?.disabled).toBe(true);
    const incompleteRow = Array.from(
      document.querySelectorAll<HTMLElement>('[data-profile-id]'),
    ).find(row => row.dataset.profileId === 'guest_incomplete');
    expect(incompleteRow?.querySelector<HTMLButtonElement>(
      'button[data-action="edit-profile"]',
    )?.textContent).toBe('Complete profile');

    changeCheckbox('guest_bravo', true);
    changeCheckbox('guest_alpha', false);

    expect(panel.tbProfiles()).toEqual([{
      id: 'guest_bravo', name: 'Bravo', nak: 'Hasta', pada: null,
      rasi: 'Kanya', lagna: 'Karka',
    }]);
    expect(controller?.getSelectedIds()).toEqual(['guest_bravo']);
  });

  test('contextually selects a ready profile without disturbing the current search', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta' });
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '["guest_bravo"]');
    localStorage.setItem('tc-go-view', 'profile:guest_bravo');
    localStorage.setItem('unrelated-preference', 'keep');
    const active = initialize();
    clickAction('add-manual');
    chooseManualValues({ name: 'One-off', nakshatra: 'Revati', pada: '3' });
    const manualId = panel.tbProfiles().find(profile => profile.id.startsWith('manual_'))?.id;
    const profileRowsBefore = profileStorage.getItem(GUEST_PROFILE_STORAGE_KEY);
    const write = vi.spyOn(browserStorage, 'setItem');
    write.mockClear();

    expect(active.selectProfile('guest_alpha')).toBe(true);

    expect(active.getSelectedIds()).toEqual(['guest_bravo', 'guest_alpha']);
    expect(panel.tbProfiles().map(profile => profile.id)).toEqual([
      'guest_bravo',
      'guest_alpha',
      manualId,
    ]);
    expect(write).toHaveBeenCalledOnce();
    expect(write).toHaveBeenCalledWith(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_bravo","guest_alpha"]',
    );
    expect(localStorage.getItem('tc-go-view')).toBe('profile:guest_bravo');
    expect(localStorage.getItem('unrelated-preference')).toBe('keep');
    expect(profileStorage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(profileRowsBefore);
    expect((document.querySelector('#tb-from') as HTMLInputElement).value).toBe('2026-08-28');
    expect((document.querySelector('#tb-to') as HTMLInputElement).value).toBe('2026-09-04');
    expect((document.querySelector('#mu-activity') as HTMLSelectElement).value).toBe('wedding');
  });

  test('asks for the source-specific primary role and restores its stable saved ID', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta' });
    localStorage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_alpha","guest_bravo"]',
    );
    const active = initialize();
    const activity = document.querySelector<HTMLSelectElement>('#mu-activity')!;
    activity.value = 'surgery';
    activity.dispatchEvent(new Event('change', { bubbles: true }));

    const role = document.querySelector<HTMLSelectElement>('[data-muhurta-role]')!;
    expect(role).toBeTruthy();
    expect(role.closest('label')?.textContent).toContain('Patient');
    expect(active.getRoleParticipant('surgery')?.id).toBe('guest_alpha');

    role.value = 'guest_bravo';
    role.dispatchEvent(new Event('change', { bubbles: true }));
    expect(active.getRoleParticipant('surgery')?.id).toBe('guest_bravo');
    expect(JSON.parse(
      localStorage.getItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY) || '{}',
    )).toEqual({ version: 1, roles: { surgery: 'guest_bravo' } });

    store.update('guest_bravo', { name: 'Bravo edited' });
    expect(active.getRoleParticipant('surgery')).toMatchObject({
      id: 'guest_bravo', name: 'Bravo edited',
    });

    controller?.destroy();
    controller = null;
    renderPanelFixture();
    const activityAfterReload = document.querySelector<HTMLSelectElement>('#mu-activity')!;
    activityAfterReload.value = 'surgery';
    const restored = initialize();
    expect(restored.getRoleParticipant('surgery')).toMatchObject({
      id: 'guest_bravo', name: 'Bravo edited',
    });

    store.remove('guest_bravo');
    expect(restored.getRoleParticipant('surgery')?.id).toBe('guest_alpha');
    expect(JSON.parse(
      localStorage.getItem(MUHURTAM_ROLE_SELECTIONS_STORAGE_KEY) || '{}',
    )).toEqual({ version: 1, roles: { surgery: 'guest_alpha' } });

    activityAfterReload.value = 'gold';
    activityAfterReload.dispatchEvent(new Event('change', { bubbles: true }));
    expect(document.querySelector('[data-muhurta-role]')).toBeNull();
  });

  test('refuses missing and incomplete contextual profiles without persisting a choice', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_incomplete'),
    });
    store.create({ name: 'Needs star' });
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    const active = initialize();
    const write = vi.spyOn(browserStorage, 'setItem');
    write.mockClear();

    expect(active.selectProfile('guest_missing')).toBe(false);
    expect(active.selectProfile('guest_incomplete')).toBe(false);

    expect(active.getSelectedIds()).toEqual([]);
    expect(write).not.toHaveBeenCalled();
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'Complete this profile with a birth star',
    );
  });

  test('enforces the aggregate four-person limit during contextual selection', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_one', 'guest_two', 'guest_three', 'guest_four'),
    });
    for (const name of ['One', 'Two', 'Three', 'Four']) {
      store.create({ name, nakshatra: 'Rohini' });
    }
    localStorage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_one","guest_two","guest_three"]',
    );
    const active = initialize();
    clickAction('add-manual');
    const write = vi.spyOn(browserStorage, 'setItem');
    write.mockClear();

    expect(active.selectProfile('guest_four')).toBe(false);

    expect(active.getSelectedIds()).toEqual(['guest_one', 'guest_two', 'guest_three']);
    expect(document.querySelectorAll('[data-manual-id]')).toHaveLength(1);
    expect(localStorage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe(
      '["guest_one","guest_two","guest_three"]',
    );
    expect(write).not.toHaveBeenCalled();
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'Choose up to 4 participants',
    );
  });

  test('restores keyboard focus after saved and manual selection rerenders', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    initialize();

    const checkbox = document.querySelector<HTMLInputElement>(
      'input[data-profile-selection="guest_alpha"]',
    )!;
    checkbox.focus();
    changeCheckbox('guest_alpha', true);
    expect(document.activeElement).toBe(document.querySelector(
      'input[data-profile-selection="guest_alpha"]',
    ));

    clickAction('add-manual');
    for (const [field, value] of [
      ['nakshatra', 'Hasta'],
      ['pada', '2'],
      ['lagna', 'Karka'],
    ] as const) {
      const select = document.querySelector<HTMLSelectElement>(
        `select[data-manual-field="${field}"]`,
      )!;
      select.focus();
      select.value = value;
      select.dispatchEvent(new Event('change', { bubbles: true }));
      expect(document.activeElement).toBe(document.querySelector(
        `select[data-manual-field="${field}"]`,
      ));
    }
  });

  test('keeps the no-profile path and supports a labelled, session-only person', () => {
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    initialize();

    expect(panel.tbProfiles()).toEqual([]);
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'No participant screening is selected',
    );

    clickAction('add-manual');
    const labels = Array.from(document.querySelectorAll(
      '[data-manual-id] .muhurta-manual-field__label',
    ))
      .map(label => label.textContent);
    expect(labels).toEqual(expect.arrayContaining(['Name', 'Birth star', 'Padam', 'Lagna']));
    chooseManualValues({
      name: 'One-off guest', nakshatra: 'Krittika', pada: '2', lagna: 'Karka',
    });

    expect(panel.tbProfiles()).toEqual([{
      id: expect.stringMatching(/^manual_/),
      name: 'One-off guest', nak: 'Krittika', pada: 2,
      rasi: 'Vrishabha', lagna: 'Karka',
    }]);
    expect(store.getSnapshot().profiles).toEqual([]);
    expect(profileStorage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBeNull();
  });

  test('caps saved and manual participants at four in total', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_one', 'guest_two', 'guest_three', 'guest_four'),
    });
    for (const name of ['One', 'Two', 'Three', 'Four']) {
      store.create({ name, nakshatra: 'Rohini' });
    }
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');
    initialize();

    clickAction('add-manual');
    chooseManualValues({ nakshatra: 'Hasta' });
    for (const id of ['guest_one', 'guest_two', 'guest_three']) changeCheckbox(id, true);

    expect(panel.tbProfiles()).toHaveLength(4);
    expect(document.querySelector<HTMLInputElement>(
      'input[data-profile-selection="guest_four"]',
    )?.disabled).toBe(true);
    expect(document.querySelector<HTMLButtonElement>(
      'button[data-action="add-manual"]',
    )?.disabled).toBe(true);

    panel.tbAddRow();
    expect(document.querySelectorAll('[data-manual-id]')).toHaveLength(1);
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'Choose up to 4 participants',
    );
  });

  test('survives reorder and edits, then removes only a deleted stable ID', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_alpha', 'guest_bravo', 'guest_charlie'),
    });
    store.create({ name: 'Alpha', nakshatra: 'Rohini' });
    store.create({ name: 'Bravo', nakshatra: 'Hasta' });
    store.create({ name: 'Charlie', nakshatra: 'Revati' });
    localStorage.setItem(
      MUHURTAM_PROFILE_IDS_STORAGE_KEY,
      '["guest_alpha","guest_charlie"]',
    );
    initialize();

    store.update('guest_charlie', { name: 'Charlie edited', lagna: 'Simha' });
    const rows = JSON.parse(profileStorage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
    profileStorage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify([
      rows[2], rows[1], rows[0],
    ]));
    store.reload();

    expect(panel.tbProfiles().map(profile => [profile.id, profile.name])).toEqual([
      ['guest_alpha', 'Alpha'],
      ['guest_charlie', 'Charlie edited'],
    ]);

    store.remove('guest_alpha');

    expect(panel.tbProfiles().map(profile => profile.id)).toEqual(['guest_charlie']);
    expect(localStorage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe(
      '["guest_charlie"]',
    );
  });

  test('surfaces storage failure while keeping current-page participants usable', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_available'),
    });
    store.create({ name: 'Available', nakshatra: 'Rohini' });
    vi.stubGlobal('localStorage', {
      getItem: () => { throw new Error('denied'); },
      setItem: () => { throw new Error('denied'); },
    });

    initialize();

    expect(panel.tbProfiles().map(profile => profile.id)).toEqual(['guest_available']);
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'this browser cannot save them',
    );
  });

  test('surfaces unavailable profile storage without crashing the no-profile path', () => {
    store = createGuestProfileStore(new DeniedStorage());
    localStorage.setItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY, '[]');

    initialize();

    expect(panel.tbProfiles()).toEqual([]);
    expect(document.querySelector('#tb-profiles')?.textContent).toContain(
      'Browser storage is unavailable',
    );
  });

  test('renders hostile saved names as inert text and wires contextual actions', () => {
    const hostile = `"><img src=x onerror=alert('x')>`;
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_hostile'),
    });
    store.create({ name: hostile, nakshatra: 'Rohini' });

    initialize();

    const root = document.querySelector('#tb-profiles')!;
    expect(root.querySelector('img')).toBeNull();
    expect(root.textContent).toContain(hostile);

    const editTrigger = clickAction('edit-profile');
    const createTrigger = clickAction('create-profile');
    const manageTrigger = clickAction('manage-profiles');
    expect(editProfile).toHaveBeenCalledWith('guest_hostile', editTrigger);
    expect(createProfile).toHaveBeenCalledWith(createTrigger);
    expect(manageProfiles).toHaveBeenCalledWith(manageTrigger);
  });

  test('clear selection never deletes profiles or Gochara preferences', () => {
    store = createGuestProfileStore(profileStorage, {
      idFactory: ids('guest_keep'),
    });
    store.create({ name: 'Keep me', nakshatra: 'Rohini' });
    localStorage.setItem('tc-go-view', 'profile:guest_keep');
    localStorage.setItem('tc-go-rasi', '4');
    initialize();
    clickAction('add-manual');

    panel.tbResetProfiles();

    expect(store.get('guest_keep')).not.toBeNull();
    expect(localStorage.getItem('tc-go-view')).toBe('profile:guest_keep');
    expect(localStorage.getItem('tc-go-rasi')).toBe('4');
    expect(localStorage.getItem(MUHURTAM_PROFILE_IDS_STORAGE_KEY)).toBe('[]');
    expect(panel.tbProfiles()).toEqual([]);
    expect(document.querySelectorAll('[data-manual-id]')).toHaveLength(0);
    for (const id of ['tb-summary', 'tb-result', 'mu-context', 'mu-result']) {
      expect(document.getElementById(id)?.textContent).toBe('');
    }
  });

  test('keeps the controller-absent compatibility form additive and inert', () => {
    const hostileName = `Alpha"><img src=x onerror=alert('x')>`;
    const stored = [
      {
        id: 'guest_alpha', schemaVersion: 1, name: hostileName,
        nak: 'Rohini', pada: 2, lagna: 'Karka', futureField: { keep: true },
      },
      {
        id: 'guest_hidden', schemaVersion: 99, name: '', nak: '',
        pada: '', lagna: 'Simha', futureOnly: 'keep-hidden',
      },
      'opaque-future-row',
    ];
    localStorage.setItem(GUEST_PROFILE_STORAGE_KEY, JSON.stringify(stored));

    panel.tbRenderProfileInputs();

    expect(document.querySelector('#tb-profiles img')).toBeNull();
    const input = document.querySelector<HTMLInputElement>('#tb-name-0')!;
    expect(input.value).toBe(hostileName);
    input.value = 'Alpha updated';
    panel.tbSaveProfiles();

    const after = JSON.parse(localStorage.getItem(GUEST_PROFILE_STORAGE_KEY) || '[]');
    expect(after[0]).toMatchObject({
      id: 'guest_alpha', schemaVersion: 1, name: 'Alpha updated',
      futureField: { keep: true },
    });
    expect(after[1]).toEqual(stored[1]);
    expect(after[2]).toBe('opaque-future-row');
    expect(panel.tbProfiles()).toEqual([{
      id: 'guest_alpha', name: 'Alpha updated', nak: 'Rohini', pada: 2,
      rasi: 'Vrishabha', lagna: 'Karka',
    }]);
  });

  test('fails closed for controller-absent mutations and reserves deletion for reset all', () => {
    const base = JSON.stringify([{
      id: 'guest_fallback_birth', schemaVersion: 1, name: 'Anu',
      nak: 'Rohini', pada: 2, lagna: 'Karka',
    }]);
    const birthBytes = '{"sensitive":{"opaque":"keep-exactly"}}';
    const commitBytes = '{"committed":{"opaque":"keep-exactly"}}';
    localStorage.setItem(GUEST_PROFILE_STORAGE_KEY, base);
    localStorage.setItem(GUEST_BIRTH_PROFILE_STORAGE_KEY, birthBytes);
    localStorage.setItem(GUEST_PROFILE_COMMIT_STORAGE_KEY, commitBytes);
    panel.tbRenderProfileInputs();
    document.querySelector<HTMLInputElement>('#tb-name-0')!.value = 'Edited';
    const originalRows = document.querySelectorAll('.tb-profile-row').length;

    panel.tbSaveProfiles();
    panel.tbAddRow();
    panel.tbRemoveRow(0);
    expect(localStorage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBe(base);
    expect(localStorage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBe(birthBytes);
    expect(localStorage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBe(commitBytes);
    expect(document.querySelectorAll('.tb-profile-row')).toHaveLength(originalRows);

    const removeItem = vi.spyOn(browserStorage, 'removeItem');
    panel.tbResetProfiles();
    expect(removeItem.mock.calls).toEqual([
      [GUEST_BIRTH_PROFILE_STORAGE_KEY],
      [GUEST_PROFILE_COMMIT_STORAGE_KEY],
      [GUEST_PROFILE_STORAGE_KEY],
    ]);
    expect(localStorage.getItem(GUEST_BIRTH_PROFILE_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem(GUEST_PROFILE_COMMIT_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem(GUEST_PROFILE_STORAGE_KEY)).toBeNull();
  });

  test('keeps controller-absent mutation inert when storage reads are denied', () => {
    const setItem = vi.fn();
    const removeItem = vi.fn();
    vi.stubGlobal('localStorage', {
      getItem: () => { throw new DOMException('denied', 'SecurityError'); },
      setItem,
      removeItem,
    });
    const originalRows = document.querySelectorAll('.tb-profile-row').length;

    expect(() => panel.tbSaveProfiles()).not.toThrow();
    expect(() => panel.tbAddRow()).not.toThrow();
    expect(() => panel.tbRemoveRow(0)).not.toThrow();
    expect(setItem).not.toHaveBeenCalled();
    expect(removeItem).not.toHaveBeenCalled();
    expect(document.querySelectorAll('.tb-profile-row')).toHaveLength(originalRows);
  });
});
