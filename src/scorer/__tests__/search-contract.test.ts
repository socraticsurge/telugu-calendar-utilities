import { expect, it } from 'vitest';
import { browserSearchWindow, searchFingerprint } from '../search-contract';

it('preserves browser limits independently of the 14-day MCP request limit', () => {
  expect(browserSearchWindow('2026-01-01', '2026-12-31').nDays).toBe(60);
  expect(browserSearchWindow('2026-01-02', '2026-01-01').nDays).toBe(1);
  expect(browserSearchWindow('2026-03-07', '2026-03-09').nDays).toBe(3);
  expect(browserSearchWindow('2026-01-01', '2026-01-01').from.getHours()).toBe(0);
});

it('fingerprints all inputs used for stale-result detection without mutation', () => {
  const request = { activity: 'any', from: '2026-07-18', to: '2026-07-19',
    city: 'Hyderabad', system: 'drik', chandraMode: 'stars', people: [],
    roleId: null, borrowingPurpose: null };
  expect(searchFingerprint(request)).toBe(JSON.stringify(request));
  expect(searchFingerprint({ ...request, city: 'New York' })).not.toBe(searchFingerprint(request));
});
