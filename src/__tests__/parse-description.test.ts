// Golden-fixture test for parseDescription — the highest-risk regex
// surface in the site (phase-3 plan called for exactly this guard
// before any consumer moves).
//
// The fixture is REAL engine output: DrikGanitaEngine + ICSGenerator
// for Hyderabad, 2026-07-18, captured via tests-equivalent Python
// (see the fixture's sibling README note in the JSON). If the feed
// format and this parser ever drift, this test fails first.

import { test, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseDescription } from '../lib/parse-description';
import { parseEvents, unfoldICS } from '../lib/ics';

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURE = JSON.parse(
  readFileSync(join(HERE, 'fixtures', 'hyderabad-2026-07-18-drik.json'), 'utf8'),
) as { summary: string; description: string };

const day = parseDescription(FIXTURE.description);

test('header line: samvatsara, maasam, paksham, vaaram', () => {
  expect(day.samvatsara).toBe('Parabhava');
  expect(day.maasam).toBe('Ashadha');
  expect(day.paksham).toBe('Shukla');
  expect(day.vaaram).toBe('Shanivaram');
  expect(day.ayanam).toBe('Dakshinayanam');
  expect(day.rituvu).toBe('Varsha');
});

test('sky markers', () => {
  expect(day.sunrise).toBe('05:50');
  expect(day.sunset).toBe('18:53');
  expect(day.moonrise).toBe('09:34');
  expect(day.moonset).toBe('22:02');
  expect(day.solarSign).toBe('Karka');
  expect(day.lunarSign).toBe('Simha');
});

test('anga rows with day-offset flags', () => {
  expect(day.tithi).toMatchObject({ name: 'Shukla Panchami', start: '04:43', end: '03:43', eflag: '+1' });
  expect(day.nakshatra).toMatchObject({ name: 'Purva Phalguni', start: '18:35', sflag: '-1', end: '18:00' });
  expect(day.yoga).toMatchObject({ name: 'Variyan', start: '22:46', sflag: '-1', end: '20:45' });
  expect(day.karana).toBe('Bava 04:43–16:07  /  Balava 16:07–03:43 (+1)');
});

test('auspicious and inauspicious windows', () => {
  const names = (list: Array<{ name: string }>) => list.map(w => w.name);
  expect(names(day.auspicious)).toEqual(['Brahma Muhurta', 'Abhijit Muhurta', 'Amrita Kalam']);
  expect(names(day.inauspicious)).toEqual([
    'Rahu Kalam', 'Gulika Kalam', 'Yamagandam', 'Varjyam', 'Durmuhurtham', 'Durmuhurtham',
  ]);
  expect(day.inauspicious[0]).toMatchObject({ start: '09:06', end: '10:44' });
  // Varjyam spills past midnight — both flags must survive parsing
  const varjyam = day.inauspicious.find((w: any) => w.name === 'Varjyam');
  expect(varjyam).toMatchObject({ start: '01:16', sflag: '+1', end: '02:52', eflag: '+1' });
});

test('day and night choghadiya: 8 blocks each, night crosses midnight', () => {
  expect(day.choghadiya).toHaveLength(8);
  expect(day.nightChoghadiya).toHaveLength(8);
  expect(day.choghadiya[0]).toMatchObject({ start: '05:50', name: 'Kaal' });
  expect(day.choghadiya[7]).toMatchObject({ end: '18:53', name: 'Kaal' });
  // NOTE: choghadiya rows deliberately drop the (+1) day-offset flags
  // (windows keep theirs) — pinning that as current behavior.
  const lastNight = day.nightChoghadiya[7];
  expect(lastNight).toEqual({ start: '04:29', end: '05:51', name: 'Labh' });
});

test('no eclipse on a plain day', () => {
  expect(day.eclipse).toBeNull();
});

test('ics: unfold + parseEvents round-trips a minimal feed', () => {
  const ics = [
    'BEGIN:VCALENDAR',
    'BEGIN:VEVENT',
    'DTSTART;VALUE=DATE:20260718',
    'SUMMARY:Shukla Panchami · Purva',
    ' Phalguni · Variyan',
    'DESCRIPTION:line one\\nline two\\, with comma',
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n');
  expect(unfoldICS(ics)).toContain('SUMMARY:Shukla Panchami · PurvaPhalguni · Variyan');
  const events = parseEvents(ics);
  const ev = events.get('20260718')!;
  expect(ev.summary).toBe('Shukla Panchami · PurvaPhalguni · Variyan');
  expect(ev.description).toBe('line one\nline two, with comma');
});
