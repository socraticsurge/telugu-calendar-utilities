// @vitest-environment jsdom
// @ts-nocheck -- imports the intentionally relaxed legacy panel at runtime.

import { beforeAll, beforeEach, expect, test, vi } from 'vitest';
import dayFixture from './fixtures/hyderabad-2026-07-18-drik.json';

const harness = vi.hoisted(() => ({
  selection: { city: 'Slow City', system: 'drik', timeFmt: '12' },
  loadFeed: vi.fn(),
  loadLagna: vi.fn(),
}));

vi.mock('../selection-store', () => ({
  getSelection: () => harness.selection,
}));

vi.mock('../lib/feed-loader', () => ({
  FEED_BASE_URL: 'https://example.invalid/feeds/',
  loadFeed: harness.loadFeed,
  slug: value => value.toLowerCase().replace(/\s+/g, '-'),
}));

vi.mock('../lib/lagna-loader', () => ({
  loadLagna: harness.loadLagna,
  lagnaDayFor: (data, isoDate) => (
    data?.days?.find(day => day.date === isoDate) || null
  ),
}));

let initTodayPanel;
let loadPreview;
let shareTodayOnWhatsApp;

beforeAll(async () => {
  // Keep the relaxed panel out of the strict core TypeScript graph while
  // still exercising its real runtime implementation in Vitest.
  const module = await import('../panels/' + 'today');
  initTodayPanel = module.initTodayPanel;
  loadPreview = module.loadPreview;
  shareTodayOnWhatsApp = module.shareTodayOnWhatsApp;
});

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function dayEvents(label) {
  return new Map([
    ['20260829', {
      summary: label,
      description: `${label} Nama Samvatsara · Chaitra Maasam · Shukla Paksham · Shanivaram`,
    }],
  ]);
}

function lagnaData(rashi) {
  return {
    start: '2026-08-29',
    days: [{
      date: '2026-08-29',
      sunrise: '06:00',
      lagna0: rashi,
      transitions: [[60, (rashi + 1) % 12]],
      cycleEnd: 1440,
    }],
  };
}

beforeEach(() => {
  document.body.innerHTML = `
    <select id="tp-city"><option selected>Hyderabad</option></select>
    <select id="tp-system"><option selected>Drik</option></select>
    <div id="tp-result" aria-busy="false"></div>
    <div id="upcoming-result"></div>
  `;
  harness.selection.city = 'Slow City';
  harness.selection.system = 'drik';
  harness.selection.timeFmt = '12';
  harness.loadFeed.mockReset();
  harness.loadLagna.mockReset();
  initTodayPanel('2026-08-29');
});

test('only the latest feed and lagna requests may paint the daily surface', async () => {
  const slowFeed = deferred();
  const fastFeed = deferred();
  const newestFeed = deferred();
  const fastLagna = deferred();
  const newestLagna = deferred();

  harness.loadFeed.mockImplementation(city => {
    if (city === 'Slow City') return slowFeed.promise;
    if (city === 'Fast City') return fastFeed.promise;
    return newestFeed.promise;
  });
  harness.loadLagna.mockImplementation(city => (
    city === 'Fast City' ? fastLagna.promise : newestLagna.promise
  ));

  const slowRequest = loadPreview();
  harness.selection.city = 'Fast City';
  const fastRequest = loadPreview();

  fastFeed.resolve(dayEvents('Fast Winner'));
  await fastRequest;
  expect(document.getElementById('tp-result')?.textContent).toContain('Fast Winner');
  expect(document.getElementById('tp-result')?.getAttribute('aria-busy')).toBe('false');

  slowFeed.resolve(dayEvents('Stale Loser'));
  await slowRequest;
  expect(document.getElementById('tp-result')?.textContent).toContain('Fast Winner');
  expect(document.getElementById('tp-result')?.textContent).not.toContain('Stale Loser');

  harness.selection.city = 'Newest City';
  const newestRequest = loadPreview();
  newestFeed.resolve(dayEvents('Newest Winner'));
  await newestRequest;
  expect(document.getElementById('tp-result')?.textContent).toContain('Newest Winner');

  fastLagna.resolve(lagnaData(0));
  await Promise.resolve();
  expect(document.getElementById('lagna-ribbon')?.textContent).not.toContain('Mesha');

  newestLagna.resolve(lagnaData(1));
  await Promise.resolve();
  expect(document.getElementById('lagna-ribbon')?.textContent).toContain('Vrishabha');
});

test('announces only the active request failure and clears busy state', async () => {
  harness.loadFeed.mockRejectedValue(new Error('offline'));

  await loadPreview();

  expect(document.querySelector('#tp-result [role="status"]')?.textContent)
    .toContain('Preview unavailable');
  expect(document.querySelector('#upcoming-result [role="status"]')?.textContent)
    .toContain('Unavailable');
  expect(document.getElementById('tp-result')?.getAttribute('aria-busy')).toBe('false');
  expect(document.getElementById('upcoming-result')?.getAttribute('aria-busy')).toBe('false');
});

test('preserves the complete daily card and WhatsApp share contract', async () => {
  harness.selection.city = 'Hyderabad';
  harness.loadFeed.mockResolvedValue(new Map([
    ['20260829', {
      summary: `🪔 Sample Festival — ${dayFixture.summary}`,
      description: dayFixture.description,
    }],
    ['20260830', {
      summary: 'Tomorrow',
      description: 'Sunrise 05:51',
    }],
  ]));
  harness.loadLagna.mockResolvedValue(null);

  await loadPreview();

  const card = document.querySelector('.preview-card');
  expect(card?.textContent).toContain('Parabhava Nama Samvatsara');
  expect(card?.textContent).toContain('Sunrise5:50am');
  expect(card?.textContent).toContain('Shukla Panchami');
  expect(card?.textContent).toContain('Bava');
  expect(document.querySelectorAll('.anga-cell')).toHaveLength(4);
  expect(document.querySelectorAll('.win-grid')).toHaveLength(2);
  expect(document.querySelectorAll('.chog-grid .chog-cell')).toHaveLength(16);
  expect(document.querySelectorAll('.hora-grid .hora-cell')).toHaveLength(24);
  expect(card?.textContent).toContain('At sunrise · Kaal Choghadiya · Saturn Hora');

  const open = vi.spyOn(window, 'open').mockImplementation(() => null);
  shareTodayOnWhatsApp();
  const shareUrl = open.mock.calls[0][0] as string;
  const shareText = decodeURIComponent(shareUrl.split('text=')[1]);
  expect(shareText).toContain('🪔 *Sample Festival*');
  expect(shareText).toContain('*Tithi:* Shukla Panchami');
  expect(shareText).toContain('*Karana:* Bava 4:43am–4:07pm / Balava 4:07pm–3:43am (next day)');
  expect(shareText).toContain('⚠️ *Avoid:*');
  expect(shareText).toContain('• Gulika Kalam 5:50am–7:28am');
  expect(shareText).toContain('https://panchangam.astrochaganti.com/?src=share-today');
});
