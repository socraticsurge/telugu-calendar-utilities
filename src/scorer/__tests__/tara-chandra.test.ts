// @vitest-environment node
import { describe, expect, test } from 'vitest';
import {
  tbTaraOf, tbTaraLabel, tbTaraIsGood, tbChandraOf, tbChandraVerdict,
} from '../tara-chandra';

// Independent compatibility expectations, not imported production tables.
const stars = ['Ashvini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
  'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula',
  'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishtha', 'Shatabhisha',
  'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'];
const signs = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
  'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'];
const labels = ['Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak', 'Sadhana',
  'Naidhana', 'Mitra', 'Parama Mitra'];
const taraCycle = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9];
const goodTaras = [false, true, false, true, false, true, false, true, true];
const verdicts = ['good', 'puja', 'good', 'bad', 'puja', 'good', 'good', 'bad', 'puja', 'good', 'good', 'bad'];

const starPairs = stars.flatMap((birth, index) =>
  [...stars.slice(index), ...stars.slice(0, index)].map((day, offset) =>
    ({ birth, day, tara: taraCycle[offset] })));
const signPairs = signs.flatMap((birth, index) =>
  [...signs.slice(index), ...signs.slice(0, index)].map((day, offset) =>
    ({ birth, day, pos: offset + 1, verdict: verdicts[offset] })));

describe('browser Tara/Chandra compatibility', () => {
  test.each(starPairs)('$birth → $day retains its Tara classification', ({ birth, day, tara }) => {
    expect(tbTaraOf(birth, day)).toBe(tara);
    expect(tbTaraLabel(tara)).toBe(labels[tara - 1]);
    expect(tbTaraIsGood(tara)).toBe(goodTaras[tara - 1]);
  });

  test.each(signPairs)('$birth → $day retains its Chandra classification', ({ birth, day, pos, verdict }) => {
    expect(tbChandraOf(birth, day)).toEqual({ pos, verdict });
    expect(tbChandraVerdict(pos)).toBe(verdict);
  });

  test.each(['', 'unknown', 'ashvini', ' Ashvini', 'Vrishchika', null, undefined, 1, {}, ['Ashvini']])(
    'invalid names remain unmatched: %j', value => {
      expect(tbTaraOf(value, 'Ashvini')).toBeNull();
      expect(tbTaraOf('Ashvini', value)).toBeNull();
      expect(tbChandraOf(value, 'Mesha')).toBeNull();
      expect(tbChandraOf('Mesha', value)).toBeNull();
    },
  );

  test.each([0, -1, 10, 100, 1.5, Number.NaN, Number.POSITIVE_INFINITY])(
    'out-of-range Tara keeps its previous result: %s', value => {
      expect(tbTaraIsGood(value)).toBe(false);
      expect(tbTaraLabel(value)).toBeUndefined();
    },
  );

  test.each([0, -1, 13, 100, 1.5, Number.NaN, Number.POSITIVE_INFINITY])(
    'out-of-range Chandra position remains bad: %s', value => {
      expect(tbChandraVerdict(value)).toBe('bad');
    },
  );
});
