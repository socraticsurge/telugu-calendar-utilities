import { describe, expect, test } from 'vitest';

import {
  BORROWING_PURPOSES,
  borrowingPurposeContext,
  manualRowAppliesToBorrowingPurpose,
} from '../borrowing-context';
import { evaluatePersonalElectionRules, roleForActivity } from '../personal-election-screening';

describe('local Borrowing role and purpose context', () => {
  test('uses exactly one required primary borrower', () => {
    expect(roleForActivity('borrowing_money')).toMatchObject({
      role: 'primary_borrower', cardinality: 1, required: true,
      ruleIds: ['personal.borrowing.primary-borrower-janma-nakshatra'],
    });
  });

  test('uses only the minimum enum and fails closed for unknown values', () => {
    expect(BORROWING_PURPOSES).toEqual([
      'quick_domestic_or_personal', 'business', 'other_or_unknown',
    ]);
    expect(borrowingPurposeContext('business')).toEqual({
      purpose: 'business', status: 'selected',
    });
    expect(borrowingPurposeContext('mortgage for 25 lakh')).toEqual({
      purpose: 'other_or_unknown', status: 'unknown',
    });
    expect(borrowingPurposeContext(null).status).toBe('unknown');
  });

  test('shows only the active purpose row', () => {
    expect(manualRowAppliesToBorrowingPurpose('business', 'business')).toBe(true);
    expect(manualRowAppliesToBorrowingPurpose(
      'quick_domestic_or_personal', 'business',
    )).toBe(false);
    expect(manualRowAppliesToBorrowingPurpose(undefined, 'business')).toBe(true);
  });

  test('applies the Janma gate only to the selected borrower', () => {
    const base = {
      id: 'primary', name: 'Primary borrower', nakshatra: 'Rohini',
      janmaRashi: null, janmaLagna: null,
    };
    const rejected = evaluatePersonalElectionRules('borrowing_money', base, {
      nakshatra: 'Rohini', lunarRashi: 'Vrishabha', lagna: 'Mesha',
    });
    expect(rejected.rejected).toBe(true);

    const missing = evaluatePersonalElectionRules('borrowing_money', null, {
      nakshatra: 'Rohini', lunarRashi: 'Vrishabha', lagna: 'Mesha',
    });
    expect(missing).toMatchObject({ rejected: false, needsReview: true });
  });
});
