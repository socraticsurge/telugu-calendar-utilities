import { expect, test } from 'vitest';
import * as rules from '../../scorer/tara-chandra';
import * as journey from '../tarabalam-journey';

test.each(['tbTaraOf', 'tbTaraIsGood', 'tbTaraLabel', 'tbChandraOf', 'tbChandraVerdict'] as const)(
  'legacy %s export retains the same implementation', name => {
    expect(journey[name]).toBe(rules[name]);
  },
);
