import { expect, test } from 'vitest';
import cases from '../../../tests/fixtures/tithi-karana-browser-vocabulary.json';
import sharedTables from '../../data/shared-calendar-tables.generated.json';
import { activityTithiNumber, muFactsAt } from '../muhurta-astronomy';
import { muTithiFamily } from '../../muhurta-scorer';

const families = ['Nanda', 'Bhadra', 'Jaya', 'Rikta', 'Purna'];

test.each(cases)('retains browser outputs for half-Tithi index $halfTithiIndex', entry => {
  expect(muFactsAt(new Date(entry.instant), 'Somavara')).toEqual(entry.facts);
  expect(sharedTables.tithiNames[Math.floor(entry.halfTithiIndex / 2)]).toBe(entry.facts.tithi);
  const index = entry.halfTithiIndex;
  const fixed = sharedTables.karanaFixed as Record<number, string>;
  expect(fixed[index] ?? sharedTables.karanaRepeating[(index - 1 + 7) % 7]).toBe(entry.facts.karana);
  const ordinal = Math.floor(index / 2) % 15 + 1;
  expect(activityTithiNumber(entry.facts.tithi)).toBe(ordinal);
  expect(muTithiFamily(entry.facts.tithi)).toBe(families[(ordinal - 1) % 5]);
});

test.each([
  ['Pratipada', 1], ['Prathama', 1], ['Shashti', 6], ['Amavasya', 15],
  ['Parama Ekadashi', 11], ['Padmini Ekadashi', 11], ['  Krishna Shashti  ', 6],
] as const)('retains input alias %s', (name, ordinal) => {
  expect(activityTithiNumber(name)).toBe(ordinal);
  expect(muTithiFamily(name)).toBe(families[(ordinal - 1) % 5]);
});

test('within-paksha vocabulary keeps all fifteen positions and rejects unknown input', () => {
  expect(sharedTables.tithiWithinPakshaNames).toHaveLength(15);
  sharedTables.tithiWithinPakshaNames.forEach((name, index) => {
    expect(activityTithiNumber(name)).toBe(index + 1);
    expect(muTithiFamily(name)).toBe(families[index % 5]);
  });
  expect(activityTithiNumber('unknown')).toBeNull();
  expect(muTithiFamily('unknown')).toBeNull();
});
