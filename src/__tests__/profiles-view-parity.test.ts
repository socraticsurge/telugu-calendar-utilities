// @vitest-environment jsdom

import { createHash } from 'node:crypto';
import { afterEach, expect, test, vi } from 'vitest';
import { createGuestProfileStore } from '../lib/guest-profile-store';
import { initProfilesPanel } from '../panels/profiles';

// Fingerprints were captured from c7377284 before the refactor, not regenerated
// from the extracted implementation; they cover DOM, controls, focus and data.

afterEach(() => { vi.useRealTimers(); });

function setup(count: number, active: boolean) {
  document.body.innerHTML = '<main id="profiles-root"></main>';
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-09-17T00:00:00Z'));
  let sequence = 0;
  const values = new Map<string, string>();
  const store = createGuestProfileStore({
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => { values.set(key, value); },
    removeItem: key => { values.delete(key); },
  }, { idFactory: () => 'parity-' + ++sequence });
  for (let index = 0; index < count; index += 1) {
    store.create({ name: 'Person ' + index, nakshatra: 'Rohini', pada: 2, lagna: 'Karka' });
  }
  const controller = initProfilesPanel(store, {
    navigate: vi.fn(), birthCalculationEnabled: active,
  });
  return { controller, store };
}

const cases = [false, true].flatMap(active => [0, 1, 4].flatMap(count =>
  ['list', 'create', 'view', 'edit'].map(view => ({ active, count, view }))));

test.each(cases)('baseline markup: $active / $count profiles / $view', ({ active, count, view }) => {
  const { controller, store } = setup(count, active);
  if (view === 'create') controller.openCreate({ requiredFor: 'horoscope', returnTo: 'gochara' });
  if (view === 'view') controller.openView('parity-1');
  if (view === 'edit') controller.openEdit('parity-1', { requiredFor: 'muhurta', returnTo: 'tarabalam' });
  const root = document.querySelector<HTMLElement>('#profiles-root')!;
  const controls = Array.from(root.querySelectorAll<HTMLInputElement | HTMLSelectElement>('input,select'))
    .map(control => ({ id: control.id, value: control.value, disabled: control.disabled }));
  const fingerprint = createHash('sha256').update(JSON.stringify({
    markup: root.innerHTML, controls, focused: document.activeElement?.id,
    profiles: store.getSnapshot().profiles,
  })).digest('hex');
  expect(fingerprint).toMatchSnapshot();
  controller.destroy();
});
