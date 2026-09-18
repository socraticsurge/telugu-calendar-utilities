import { expect, test } from 'vitest';

import cases from '../../../tests/fixtures/homa-election-reasons.json';
import { muHomaElection } from '../muhurta-astronomy';

test.each(cases)('matches the Python reason contract: $name', ({ facts, expected }) => {
  expect(muHomaElection(facts)).toEqual(expected);
});
