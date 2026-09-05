// @vitest-environment jsdom
// @ts-nocheck -- exercises the intentionally relaxed legacy panel at runtime.

import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { createGuestProfileStore } from '../lib/guest-profile-store';

const GRAHAS = [
  'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani', 'Rahu', 'Ketu',
];
const RASIS = [
  'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
  'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
];

function todayISO() {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

beforeEach(() => {
  vi.resetModules();
  document.body.innerHTML = `
    <select id="go-view"></select>
    <div id="go-profile-state"></div>
    <div id="go-conditions"></div>
    <div id="go-chart"></div>
    <div id="go-note"></div>
    <div id="go-moves"></div>
    <div id="go-phalalu"></div>
    <div id="go-legend"></div>
  `;
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
    },
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  delete globalThis.localStorage;
});

test('keeps deterministic Janma-Rashi evidence available when interpretive prose exists', async () => {
  const iso = todayISO();
  const fetchMock = vi.fn(async input => {
    const url = String(input);
    if (url === 'gochara.json') {
      return {
        ok: true,
        json: async () => ({
          start: iso,
          grahas: GRAHAS,
          rasis: RASIS,
          days: [[0, 1, 2, 3, 4, 5, 6, 7, 8]],
          retro: [[false, false, false, false, false, false, false, false, false]],
        }),
      };
    }
    if (url === 'rasi_phalalu/latest.json') {
      return {
        ok: true,
        json: async () => ({
          date: iso,
          rashis: {
            Mesha: {
              text: 'Interpretive overview for today.',
              advice: 'Keep the first decision small.',
            },
          },
        }),
      };
    }
    throw new Error(`Unexpected fetch: ${url}`);
  });
  vi.stubGlobal('fetch', fetchMock);

  const panelPath = '../panels/gochara';
  const panel = await import(/* @vite-ignore */ panelPath);
  await panel.loadGochara();
  expect(fetchMock).toHaveBeenCalledWith(
    'rasi_phalalu/latest.json',
    { cache: 'no-cache' },
  );
  const select = document.getElementById('go-view');
  select.value = '0';
  panel.renderGochara();

  const reading = document.getElementById('go-phalalu');
  expect(reading.textContent).toContain('Interpretive overview for today.');
  expect(reading.textContent).toContain('Janma-Rashi transit rules');
  expect(reading.textContent.toLowerCase()).not.toContain('from lagna');
  const details = reading.querySelector('.go-phalalu-details');
  expect(details).not.toBeNull();
  expect(details.open).toBe(false);
  expect(details.querySelectorAll('.go-phalalu-detail-lines p')).toHaveLength(8);
  const interpretation = reading.querySelector('.go-interpretation-details');
  expect(interpretation).not.toBeNull();
  expect(interpretation.open).toBe(false);
  expect(
    reading.querySelector('.go-phalalu-summary').compareDocumentPosition(interpretation)
      & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();

  const values = new Map();
  const store = createGuestProfileStore({
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  });
  const profile = store.create({
    name: 'Reference profile',
    nakshatra: 'Rohini',
    pada: 2,
    lagna: 'Kanya',
  });
  const controller = panel.initGocharaProfiles(store, {
    createProfile: vi.fn(),
    editProfile: vi.fn(),
    manageProfiles: vi.fn(),
  });
  expect(controller.selectProfile(profile.id)).toBe(true);

  expect(document.querySelectorAll('#go-chart .go-box.lagna')).toHaveLength(0);
  expect(document.getElementById('go-chart').textContent.toLowerCase())
    .not.toContain('lagna');
  expect(
    [...document.querySelectorAll('#go-chart [title]')]
      .map(node => node.getAttribute('title'))
      .join(' ')
      .toLowerCase(),
  ).not.toContain('lagna');
  expect(document.getElementById('go-phalalu').textContent.toLowerCase())
    .not.toContain('from lagna');

  const open = vi.spyOn(window, 'open').mockImplementation(() => null);
  panel.shareGocharaOnWhatsApp();
  const shareUrl = String(open.mock.calls[0]?.[0] || '');
  expect(decodeURIComponent(shareUrl).toLowerCase()).not.toContain('from lagna');
  expect(decodeURIComponent(shareUrl)).not.toContain('Reference profile');
  controller.destroy();
});

test('ignores a stale latest interpretation without losing computed guidance', async () => {
  const iso = todayISO();
  vi.stubGlobal('fetch', vi.fn(async input => {
    const url = String(input);
    if (url === 'gochara.json') {
      return {
        ok: true,
        json: async () => ({
          start: iso,
          grahas: GRAHAS,
          rasis: RASIS,
          days: [[0, 1, 2, 3, 4, 5, 6, 7, 8]],
          retro: [[false, false, false, false, false, false, false, false, false]],
        }),
      };
    }
    if (url === 'rasi_phalalu/latest.json') {
      return {
        ok: true,
        json: async () => ({
          date: '2000-01-01',
          rashis: { Mesha: { text: 'This stale interpretation must not render.' } },
        }),
      };
    }
    throw new Error(`Unexpected fetch: ${url}`);
  }));

  const panelPath = '../panels/gochara';
  const panel = await import(/* @vite-ignore */ panelPath);
  await panel.loadGochara();
  const select = document.getElementById('go-view');
  select.value = '0';
  panel.renderGochara();

  const reading = document.getElementById('go-phalalu');
  expect(reading.textContent).not.toContain('This stale interpretation must not render.');
  expect(reading.querySelector('.go-interpretation-details')).toBeNull();
  expect(reading.querySelector('.go-phalalu-details')).not.toBeNull();
});

test('renders fetched labels and interpretive prose as inert text', async () => {
  const iso = todayISO();
  const payload = `"><img src=x onerror=alert('x')>`;
  const hostileRasis = [...RASIS];
  hostileRasis[1] = payload;
  vi.stubGlobal('fetch', vi.fn(async input => {
    const url = String(input);
    if (url === 'gochara.json') {
      return {
        ok: true,
        json: async () => ({
          start: iso,
          grahas: GRAHAS,
          rasis: hostileRasis,
          days: [
            [0, 1, 2, 3, 4, 5, 6, 7, 8],
            [1, 1, 2, 3, 4, 5, 6, 7, 8],
          ],
          retro: [
            [false, false, false, false, false, false, false, false, false],
            [false, false, false, false, false, false, false, false, false],
          ],
        }),
      };
    }
    if (url === 'rasi_phalalu/latest.json') {
      return {
        ok: true,
        json: async () => ({
          date: iso,
          rashis: { Mesha: { text: payload, advice: payload } },
        }),
      };
    }
    throw new Error(`Unexpected fetch: ${url}`);
  }));

  const panelPath = '../panels/gochara';
  const panel = await import(/* @vite-ignore */ panelPath);
  await panel.loadGochara();
  const select = document.getElementById('go-view');
  select.value = '0';
  panel.renderGochara();

  expect(document.getElementById('go-chart').textContent).toContain(payload);
  expect(document.getElementById('go-moves').textContent).toContain(payload);
  expect(document.getElementById('go-phalalu').textContent).toContain(payload);
  expect(document.querySelector('img')).toBeNull();
  expect(document.querySelector('[onerror]')).toBeNull();
  const share = document.querySelector('.go-phalalu-share');
  expect(share.getAttribute('onclick')).toBeNull();
  const open = vi.spyOn(window, 'open').mockImplementation(() => null);
  share.click();
  expect(open).toHaveBeenCalledOnce();
});
