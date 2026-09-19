import { expect, test } from 'vitest';
import cases from '../../../tests/fixtures/nitya-yoga-vocabulary.json';
import sharedTables from '../../data/shared-calendar-tables.generated.json';
import { muScoreNityaYoga } from '../muhurta-scoring';
import { canonicalYogaName } from '../../scorer/nitya-yoga-names';

function score(yoga: string, feedName = yoga, minute = 600, avoided = new Set<string>()) {
  return muScoreNityaYoga(
    { yoga }, { yoga: { name: feedName, start: '10:00', end: '14:00' } },
    new Set(), avoided, minute,
  );
}

test.each(cases)('canonical scoring identity at index $index: $canonical', entry => {
  expect(sharedTables.browserYogaNames[entry.index]).toBe(entry.browser);
  expect(canonicalYogaName(entry.browser)).toBe(entry.canonical);
  expect(canonicalYogaName(entry.canonical)).toBe(entry.canonical);
  expect(score(entry.browser, entry.canonical)?.score).toBe(entry.score);
  expect(score(entry.canonical, entry.browser)?.score).toBe(entry.score);
});

test.each(['Shula', 'Shoola'])('Shoola fact %s uses the same feed boundary', fact => {
  for (const feed of ['Shula', 'Shoola']) {
    expect(score(fact, feed, 720)?.score).toBe(-1);
    expect(score(fact, feed, 721)?.score).toBe(0);
  }
});

test('the next Shoola begins at the current feed Yoga end', () => {
  expect(score('Shula', 'Dhriti', 960)?.score).toBe(-1);
  expect(score('Shula', 'Dhriti', 961)?.score).toBe(0);
});

test.each(['Shula', 'Shoola'])('explicit exclusions recognize %s and its alias', avoided => {
  expect(score('Shula', 'Shoola', 600, new Set([avoided]))).toBeNull();
  expect(score('Shoola', 'Shula', 600, new Set([avoided]))).toBeNull();
});

test('reason labels preserve display spelling while applying canonical policy', () => {
  expect(score('Priti')).toEqual({ score: 1, reason: 'Priti yoga (+1)' });
  expect(score('Preeti')).toEqual({ score: 1, reason: 'Preeti yoga (+1)' });
  expect(score('Variyana')).toEqual({ score: 0, reason: null });
  expect(canonicalYogaName('future-name')).toBe('future-name');
});
