// @vitest-environment jsdom
// @ts-nocheck -- the legacy panel intentionally uses a relaxed DOM shape.

import { afterEach, beforeEach, expect, test, vi } from 'vitest';

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date(2026, 7, 29, 12, 0, 0));
  vi.resetModules();
  document.body.innerHTML = '<div id="upcoming-result"></div>';
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

test('leads the year list with the next observance and a Panchangam action', async () => {
  const panelPath = '../panels/today';
  const panel = await import(/* @vite-ignore */ panelPath);
  const events = new Map([
    ['20260828', {
      summary: '🪔 Previous festival',
      description: '⚡ Previous festival',
    }],
    ['20260831', {
      summary: '🪔 Sankashti Chaturthi',
      description: '⚡ Sankashti Chaturthi',
    }],
    ['20260902', {
      summary: '⚡ Aja Ekadashi',
      description: '⚡ Aja Ekadashi — fasting day',
    }],
  ]);

  panel.renderUpcoming(events);

  const next = document.querySelector('.upcoming-next');
  expect(next).not.toBeNull();
  expect(next.textContent).toContain('Next observance');
  expect(next.textContent).toContain('Mon, Aug 31');
  expect(next.textContent).toContain('Sankashti Chaturthi');
  expect(next.textContent).not.toContain('Previous festival');
  expect(next.querySelector('.upcoming-next-action').getAttribute('onclick'))
    .toBe("switchTool('today'); openFestivalDate('2026-08-31')");
  expect(document.querySelector('#upcoming-result').textContent)
    .toContain('Previous festival');
});
