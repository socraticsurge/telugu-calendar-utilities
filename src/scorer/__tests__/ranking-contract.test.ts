import { describe, expect, it } from 'vitest';
import contract from '../../../tests/fixtures/muhurta-ranking-contract.json';
import { muRelativeTier, muScoreTier } from '../../muhurta-scorer';
import { muAssignTiers } from '../ranking';

describe('shared, independently specified ranking contract', () => {
  it('pins absolute and relative boundaries', () => {
    for (const [score, expected] of contract.absolute) {
      expect(muScoreTier(Number(score))).toBe(expected);
    }
    for (const [score, ceiling, floor, expected] of contract.relative) {
      expect(muRelativeTier(Number(score), Number(ceiling), Number(floor))).toBe(expected);
    }
  });
  it('pins empty, equal-score and dosha-capped batches', () => {
    for (const c of contract.batches) {
      const slots = c.scores.map((score, i) => ({
        score, personalDosha: c.personal[i], dayDosha: c.day[i], tier: '',
      }));
      muAssignTiers(slots);
      expect(slots.map(s => s.tier)).toEqual(c.expected);
    }
  });
});
