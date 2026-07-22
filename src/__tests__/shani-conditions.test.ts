import { describe, expect, it } from 'vitest';

import {
  shaniConditionFromMoonHouse,
  shaniConditionLine,
} from '../shani-conditions';

describe('named Shani conditions', () => {
  it.each([
    [12, 'Sade Sati (rising phase)'],
    [1, 'Sade Sati (peak phase)'],
    [2, 'Sade Sati (setting phase)'],
    [8, 'Ashtama Shani'],
    [4, 'Ardhastama Shani'],
  ])('maps Moon house %i to %s', (house, expected) => {
    expect(shaniConditionFromMoonHouse(house)).toBe(expected);
  });

  it('does not invent a headline for other Shani houses', () => {
    for (const house of [3, 5, 6, 7, 9, 10, 11]) {
      expect(shaniConditionFromMoonHouse(house)).toBeNull();
    }
  });

  it('renders deterministic advice without adding another reference frame', () => {
    expect(shaniConditionLine('Ashtama Shani')).toBe(
      'Ashtama Shani is running — avoid risks and keep commitments minimal.',
    );
  });
});
