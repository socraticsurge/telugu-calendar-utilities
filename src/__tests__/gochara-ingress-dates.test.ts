// @vitest-environment jsdom
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { RASI_NAMES } from '../data/rasis';

beforeEach(() => {
  vi.resetModules();
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-07-16T12:00:00Z'));
  document.body.innerHTML = '<select id="go-view"></select>' +
    ['go-profile-state', 'go-conditions', 'go-chart', 'go-note', 'go-moves', 'go-phalalu', 'go-legend']
      .map(id => `<div id="${id}"></div>`).join('');
  vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
});
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

async function render(precise: boolean, missing = false) {
  const data = {
    start: '2026-07-16', grahas: ['Surya'], rasis: RASI_NAMES,
    days: [[2], [3]], retro: [[0], [0]],
    ...(precise ? { ingressTimeBasis: 'Asia/Kolkata', ingresses: [[missing ? null : ['2026-07-16', 3]], [['2026-08-17', 4]]] } : {}),
  };
  vi.stubGlobal('fetch', vi.fn(async input => ({
    ok: true,
    json: async () => String(input) === 'gochara.json' ? data : { rashis: {} },
  })));
  const panelPath = '../panels/gochara';
  const panel = await import(/* @vite-ignore */ panelPath);
  await panel.loadGochara();
  return document.getElementById('go-moves')!.textContent;
}

test('renders exact IST ingress day instead of the next changed sunrise', async () => {
  expect(await render(true)).toContain('Jul 16 (IST)');
  expect(document.querySelector('.go-g')!.getAttribute('title')).toContain('till Jul 16 (IST)');
});

test('legacy cached data remains readable with an honest sunrise-sample label', async () => {
  expect(await render(false)).toContain('Jul 17 (Hyderabad sunrise sample)');
});

test('an explicit missing exact ingress does not fall back to a guessed date', async () => {
  expect(await render(true, true)).toBe('');
});
