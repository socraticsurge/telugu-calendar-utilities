import { describe, expect, test } from 'vitest';
import { usePanelFixture, type PanelFixture } from './muhurta-profile/fixtures';
import type { Participant } from './muhurta-profile/types';

let panel: PanelFixture['panel'];

usePanelFixture(fixture => {
  ({ panel } = fixture);
});

describe('Muhurtam scoring and activity guidance', () => {
  test('keeps day admission and dropped-day contracts callable', () => {
    const call = (name: string, ...args: unknown[]): unknown => (
      panel.muComplexityContracts[name] as (...values: unknown[]) => unknown
    )(...args);
    const emptyRules = {};
    const day = {
      eclipse: null,
      special: [],
      maasam: 'Sravana',
      solarSign: 'Simha',
      vaaram: 'Somavaram',
      paksham: 'Shukla',
      inauspicious: [],
      karana: null,
      yogas: [],
      yoga: null,
      lunarSign: 'Mesha',
    };
    expect(call('muConfiguredDaylightPolicy', 'wedding', day, emptyRules)).toBeNull();
    expect(call(
      'muPrimaryDayDrop', { ...day, eclipse: { kind: 'Solar eclipse' } },
      emptyRules, 'Wedding', null, null, '2026-09-07',
    )).toEqual({
      eclipse: true,
      entry: { date: '2026-09-07', reason: 'Solar eclipse · auspicious activities deferred' },
    });
    expect(call('muCalendarDayDrop', day, emptyRules, 'Wedding', '2026-09-07')).toBeNull();
    expect(call('muSolarDayDrop', day, emptyRules, 'Wedding', '2026-09-07')).toBeNull();
    expect(call(
      'muDayDrop', { ...day, eclipse: { kind: 'Lunar eclipse' } },
      emptyRules, 'Wedding', null, null, '2026-09-07',
    )).toMatchObject({ eclipse: true });
    expect(call('muBadWindows', day, new Set())).toEqual([]);
    expect(call('muYogaDayDropReason', day, new Set(), 'Wedding')).toBeNull();
    expect(call('muChandraModeDayDropReason', day, [], 'strict')).toBeNull();
    expect(call('muNoSlotDayReason', day, new Set(), 'Wedding', [], 'strict')).toBeNull();
    const droppedDays: unknown[] = [];
    call('muRecordNoSlotDay', {
      slotsPerDay: new Set(['2026-09-07']), droppedDays,
      isoDate: '2026-09-07', data: day, skipYogas: new Set(),
      activityLabel: 'Wedding', people: [], chandraMode: 'strict',
    });
    expect(droppedDays).toEqual([]);
  });

  test('keeps slot scoring and election contracts callable', () => {
    const call = (name: string, ...args: unknown[]): unknown => (
      panel.muComplexityContracts[name] as (...values: unknown[]) => unknown
    )(...args);
    const day = {
      eclipse: null,
      special: [],
      maasam: 'Sravana',
      solarSign: 'Simha',
      vaaram: 'Somavaram',
      paksham: 'Shukla',
      inauspicious: [],
      karana: null,
      yogas: [],
      yoga: null,
      lunarSign: 'Mesha',
    };
    const facts = { tithi: 'Dwitiya', nakshatra: 'Rohini', specialYogas: [], yoga: 'Siddha' };
    expect(call(
      'muScoreSlotTithi', facts, null, 'Wedding', [], new Set(),
    )).toMatchObject({ score: 0 });
    expect(call('muScoreSpecialYogas', facts, new Set())).toEqual({ score: 0, reasons: [] });
    expect(call(
      'muScoreNityaYoga', facts, day, new Set(), new Set(), 600,
    )).toMatchObject({ score: 1 });
    expect(call('muScoreSlotPreferences', {
      facts, varaReason: null, preferNakshatras: new Set(), amrita: [],
      s0: 600, e0: 648, preferChog: null,
      choghadiya: { name: 'Rog' }, avoidKaranaNames: new Set(),
      activityLabel: 'Wedding',
    })).toEqual({ score: 0, slotReasons: [], activityReasons: [] });
    expect(call('muSlotDoctrinalNotes', {
      cautionLagnaSolar: false, lagnaCityData: null, slotLagna: null,
      solarSign: null, specialYogas: [], taraUnfavNames: [],
      chandraAvoidNames: [], tithiFamily: null,
    })).toEqual({ notes: [], siddhiYogas: [] });
    expect(call('muPersonalDosha', {
      chandraAvoidNames: [], hasAshtama: false, ashtamaLagnaNames: [],
      chandraPujaNames: [], taraUnfavNames: [], siddhiYogas: [],
    })).toBeNull();
    expect(call('muSlotDayDosha', {
      tithiFamily: null, facts, nityaYoga: 'Siddha', system: 'drik',
      effectiveChartRemainder: [], rules: {}, manualGuidance: { chart: [] },
      personal: { needsReview: false },
    })).toBeNull();
    expect(call('muDominantChoghadiya', [], 600, 648)).toEqual({
      block: null, straddle: null,
    });
    const restrictions = {
      allowedNakshatras: new Set(), avoidNakshatras: new Set(),
      avoidJanmaNakshatra: false, allowedTithiNumbers: new Set(),
      allowedTithiNames: new Set(), avoidTithiNumbers: new Set(),
      avoidVaraTithiNames: new Set(),
    };
    expect(call(
      'muSlotElectionReasons', facts, { require_homa_election: false },
      restrictions, day, [],
    )).toEqual([]);
  });

  test('keeps ranking and result-scope contracts callable', () => {
    const call = (name: string, ...args: unknown[]): unknown => (
      panel.muComplexityContracts[name] as (...values: unknown[]) => unknown
    )(...args);
    const emptyRules = {};
    expect(call('muActivityNeedsLagna', 'wedding', emptyRules)).toBe(true);
    const slots: unknown[] = [];
    call('muRankCandidateSlots', slots);
    expect(slots).toEqual([]);
    expect(call('muUnavailableChartEnrichment', [])).toMatchObject({
      state: 'unavailable', slots: [], screenedCount: 0,
    });
    expect(call('muResultScopeDetail', 'wedding', null, true)).toContain(
      'partial/provisional',
    );
    expect(call('muChartStatusFor', 'wedding', null, false, '')).toBeNull();
    expect(call(
      'muChartCompletionShareLines', 'wedding', {
        candidateLimitReached: false, screenedCount: 0,
      }, [], 0, 0,
    )).toEqual([
      'This event assessor is still partial/provisional; the event-specific clauses are computed, but they are not complete chart certification because the shared baseline remains unresolved.',
      'All disclosed event chart clauses were evaluated and resolved under the documented interpretation convention.',
    ]);
  });

  test('preserves Tarabalam group scoring and participant evidence', () => {
    const people: Participant[] = [
      { id: 'a', name: 'Anu', nak: 'Rohini', pada: 2, rasi: null, lagna: null },
      { id: 'b', name: 'Bala', nak: 'Mrigashira', pada: 1, rasi: null, lagna: null },
    ];

    expect(panel.muScoreParticipantTarabalam(people, 'Mrigashira')).toEqual({
      score: 0,
      reasons: [
        'Tarabalam favourable for #1 (Anu) (+1)',
        'Tarabalam avoid for #2 (Bala) Janma (-1)',
      ],
      unfavourableNames: ['#2 (Bala)'],
    });
  });

  test('preserves Chandrabalam modes, remedial evidence and Ashtama flags', () => {
    const people: Participant[] = [
      { id: 'a', name: 'Anu', nak: 'Rohini', pada: 2, rasi: 'Dhanu', lagna: null },
      { id: 'b', name: 'Bala', nak: 'Hasta', pada: 1, rasi: 'Vrischika', lagna: null },
      { id: 'c', name: 'Charu', nak: 'Ashwini', pada: 3, rasi: 'Vrishabha', lagna: null },
    ];

    expect(panel.muScoreParticipantChandrabalam(people, 'Dhanu', 'strict')).toEqual({
      score: 0,
      reasons: [
        'Chandrabalam favourable for #1 (Anu) (+1)',
        'Chandrabalam remedial for #2 (Bala) Moon@2 (puja recommended)',
        'Chandrabalam avoid for #3 (Charu) Ashtama Moon@8 (-1)',
      ],
      avoidNames: ['#3 (Charu)'],
      pujaNames: ['#2 (Bala)'],
      hasAshtama: true,
      drop: true,
    });
    expect(panel.muScoreParticipantChandrabalam(
      [people[1]], 'Dhanu', 'puja_ok',
    ).drop).toBe(false);
  });

  test('preserves dual natal-reference Lagna scoring', () => {
    const people: Participant[] = [
      { id: 'a', name: 'Anu', nak: 'Rohini', pada: 2, rasi: 'Kanya', lagna: 'Simha' },
      { id: 'b', name: 'Bala', nak: 'Hasta', pada: 1, rasi: 'Kumbha', lagna: null },
    ];

    expect(panel.muScoreParticipantLagna(people, 'Kanya')).toEqual({
      score: 0,
      reasons: [
        'Kanya lagna favourable for #1 (Anu) own@1 from Kanya (+1)',
        'Kanya lagna Ashtama for #2 (Bala) lagna@8 from Kumbha (-1)',
        'Kanya lagna neutral for #1 (Anu) 2nd from Simha lagna (no effect)',
      ],
      ashtamaNames: ['#2 (Bala)'],
    });
  });

  test('preserves required, admitted and preferred activity-Lagna gates', () => {
    expect(panel.muScoreActivityLagna(
      'Simha', 'Sthira', new Set(['Simha']), new Set(['Simha']),
      'Sthira', {}, 'Wedding',
    )).toEqual({
      score: 2,
      reasons: [
        'Simha lagna satisfies required Sthira class',
        'Simha lagna is admitted for Wedding',
        'Simha lagna specifically favoured for Wedding (+1)',
        'Simha lagna (Sthira) favoured for Wedding (+1)',
      ],
    });
    expect(panel.muScoreActivityLagna(
      'Mesha', 'Sthira', new Set(), new Set(), null, {}, 'Wedding',
    )).toBeNull();
    expect(panel.muScoreActivityLagna(
      'Vrishabha', null, new Set(['Mesha']), new Set(), null, {},
      'Filing a lawsuit / court action', true,
    )).toEqual({
      score: 0,
      reasons: [
        'Vrishabha lagna retained provisionally for exact Navamsa assessment',
      ],
    });
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

});
