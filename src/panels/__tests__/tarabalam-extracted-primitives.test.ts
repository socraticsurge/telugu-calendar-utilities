import { describe, expect, test } from 'vitest';

import {
  muFactsAt,
  muHomaElection,
  muSpecialYogasAt,
} from '../muhurta-astronomy';
import { createMuhurtaPipelineState } from '../muhurta-day-pipeline';
import { muToT } from '../muhurta-format';
import {
  clearMuhurtaResult,
  getMuhurtaResult,
  hasMuhurtaResult,
  setMuhurtaResult,
} from '../muhurta-result-state';

describe('Tarabalam extracted primitives', () => {
  test('creates independent empty pipeline state', () => {
    const first = createMuhurtaPipelineState();
    const second = createMuhurtaPipelineState();

    expect(first).toEqual({
      slots: [],
      slotsPerDay: new Map(),
      droppedDays: [],
      droppedEclipseDays: 0,
      droppedModeSlots: 0,
    });
    expect(first.slots).not.toBe(second.slots);
    expect(first.slotsPerDay).not.toBe(second.slotsPerDay);
  });

  test('normalizes minute offsets before formatting them', () => {
    expect(muToT(0)).toMatch(/^(00:00|12:00am)$/);
    expect(muToT(1500)).toMatch(/^(01:00|1:00am)$/);
    expect(muToT(-60)).toMatch(/^(23:00|11:00pm)$/);
  });

  test('owns the last-result lifecycle', () => {
    clearMuhurtaResult();
    expect(getMuhurtaResult()).toBeNull();
    expect(hasMuhurtaResult()).toBe(false);

    const result = { slots: [{ score: 10 }] };
    setMuhurtaResult(result);
    expect(getMuhurtaResult()).toBe(result);
    expect(hasMuhurtaResult()).toBe(true);

    clearMuhurtaResult();
  });

  test('derives internally consistent slot-time astronomy facts', () => {
    const facts = muFactsAt(
      new Date('2026-07-18T06:30:00.000Z'),
      'Shanivaram',
    );

    expect(facts.vaaram).toBe('Shanivaram');
    expect(facts.nakshatra).toBeTruthy();
    expect(facts.solarNakshatra).toBeTruthy();
    expect(facts.tithi).toBeTruthy();
    expect(facts.specialYogas).toEqual(
      muSpecialYogasAt(facts.vaaram, facts.tithi, facts.nakshatra),
    );

    const election = muHomaElection(facts);
    expect(election).toEqual({
      admitted: expect.any(Boolean),
      reasons: [
        expect.stringContaining('Homahuti group'),
        expect.stringContaining('Agnivasa remainder'),
      ],
    });
  });
});
