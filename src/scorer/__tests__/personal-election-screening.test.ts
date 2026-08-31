import { describe, expect, test } from 'vitest';
import parityFixtures from '../../../tests/fixtures/personal-election-parity.json';

import {
  evaluatePersonalElectionRules,
  evaluatePersonalElectionWindow,
  roleForActivity,
  type PersonalElectionParticipant,
} from '../personal-election-screening';

const person: PersonalElectionParticipant = {
  id: 'profile-1',
  name: 'Lakshmi',
  nakshatra: 'Rohini',
  janmaRashi: 'Vrishabha',
  janmaLagna: 'Mesha',
};

describe('activity-specific personal precedence', () => {
  test('requires an explicit primary role for supported activities', () => {
    expect(roleForActivity('travel')?.role).toBe('traveller');
    expect(roleForActivity('gruhapravesha')?.role).toBe('homeowner');
    expect(roleForActivity('seemantha')?.role).toBe('mother');
    expect(roleForActivity('surgery')?.role).toBe('patient');
    expect(roleForActivity('surgery')).toMatchObject({ cardinality: 1, required: true });
    expect(roleForActivity('gold')).toBeNull();
  });

  test('Travel rejects Lagna 1, 5, 7 or 9 from the traveller natal Lagna', () => {
    const result = evaluatePersonalElectionRules('travel', person, {
      nakshatra: 'Hasta',
      lunarRashi: 'Kanya',
      lagna: 'Simha',
    });
    expect(result.rejected).toBe(true);
    expect(result.evidence.join(' ')).toMatch(/5th from Lakshmi.*Janma Lagna/);
  });

  test('Gruhapravesha treats the owner own Nakshatra as positive source precedence', () => {
    const result = evaluatePersonalElectionRules('gruhapravesha', person, {
      nakshatra: 'Rohini',
      lunarRashi: 'Mithuna',
      lagna: 'Kanya',
    });
    expect(result.rejected).toBe(false);
    expect(result.preferencePasses).toBe(1);
  });

  test('Seemantha rejects the 3rd, 7th, 8th, 10th and 22nd stars from the mother', () => {
    const result = evaluatePersonalElectionRules('seemantha', person, {
      nakshatra: 'Ardra',
      lunarRashi: 'Mithuna',
      lagna: 'Kanya',
    });
    expect(result.rejected).toBe(true);
    expect(result.evidence.join(' ')).toMatch(/3rd Nakshatra/);
  });

  test('Surgery rejects Chandra in the patient Janma Rashi', () => {
    const result = evaluatePersonalElectionRules('surgery', person, {
      nakshatra: 'Mrigashira',
      lunarRashi: 'Vrishabha',
      lagna: 'Kanya',
    });
    expect(result.rejected).toBe(true);
  });

  test('missing role facts are explicit unknowns instead of silent passes', () => {
    const result = evaluatePersonalElectionRules('surgery', {
      ...person,
      janmaRashi: null,
    }, {
      nakshatra: 'Mrigashira',
      lunarRashi: 'Vrishabha',
      lagna: 'Kanya',
    });
    expect(result.needsReview).toBe(true);
    expect(result.rejected).toBe(false);
    expect(result.outcomes[0]).toMatchObject({
      ruleId: 'personal.surgery.chandra-outside-janma-rashi',
      sourceClaim: 'muhurta.surgery',
      status: 'unknown',
    });

    const window = evaluatePersonalElectionWindow(
      'surgery',
      { ...person, janmaRashi: null },
      { nakshatra: 'Mrigashira', lunarRashi: 'Vrishabha', lagna: 'Kanya' },
      { nakshatra: 'Ardra', lunarRashi: 'Mithuna', lagna: 'Tula' },
    );
    expect(window.evidence.join(' ')).toContain("Lakshmi's Janma Rashi");
    expect(window.evidence.join(' ')).not.toContain('Could not verify');
  });

  test('a missing primary role remains actionable across the whole window', () => {
    const result = evaluatePersonalElectionWindow(
      'surgery', null,
      { nakshatra: 'Mrigashira', lunarRashi: 'Vrishabha', lagna: 'Kanya' },
      { nakshatra: 'Ardra', lunarRashi: 'Mithuna', lagna: 'Tula' },
    );
    expect(result.needsReview).toBe(true);
    expect(result.evidence).toEqual([
      expect.stringContaining('Choose the patient'),
    ]);
  });

  test('source-specific rules remain an overlay on the existing generic score', () => {
    const seemantha = evaluatePersonalElectionRules('seemantha', person, {
      nakshatra: 'Rohini', lunarRashi: 'Vrishabha', lagna: 'Kanya',
    });
    expect(seemantha.rejected).toBe(false);

    const surgery = evaluatePersonalElectionRules('surgery', person, {
      nakshatra: 'Magha', lunarRashi: 'Simha', lagna: 'Kanya',
    });
    expect(surgery.rejected).toBe(false);
  });

  test('requires prohibitions to pass and preferences to persist across the sampled window', () => {
    const result = evaluatePersonalElectionWindow(
      'surgery',
      person,
      { nakshatra: 'Magha', lunarRashi: 'Simha', lagna: 'Kanya' },
      { nakshatra: 'Rohini', lunarRashi: 'Vrishabha', lagna: 'Tula' },
    );
    expect(result.rejected).toBe(true);
    expect(result.stable).toBe(false);
    expect(result.outcomes[0].inputs).toHaveProperty('start');
    expect(result.outcomes[0].inputs).toHaveProperty('end');
  });

  test('matches the shared Python/TypeScript parity fixtures', () => {
    for (const fixture of parityFixtures) {
      const participant = fixture.participant ? {
        id: fixture.participant.id,
        name: fixture.participant.name,
        nakshatra: fixture.participant.nakshatra,
        janmaRashi: fixture.participant.janma_rashi,
        janmaLagna: fixture.participant.janma_lagna,
      } : null;
      const adaptFacts = (facts: typeof fixture.start) => ({
        nakshatra: facts.nakshatra,
        lunarRashi: facts.lunar_rashi,
        lagna: facts.lagna,
      });
      const result = evaluatePersonalElectionWindow(
        fixture.activity,
        participant,
        adaptFacts(fixture.start),
        adaptFacts(fixture.end),
      );
      expect({
        rejected: result.rejected,
        needs_review: result.needsReview,
        preference_passes: result.preferencePasses,
        stable: result.stable,
        statuses: result.outcomes.map(outcome => outcome.status),
      }, fixture.label).toEqual(fixture.expected);
    }
  });
});
