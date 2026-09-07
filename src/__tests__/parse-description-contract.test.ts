import { performance } from 'node:perf_hooks';
import { describe, expect, test } from 'vitest';

import { parseDescription } from '../lib/parse-description';

describe('parseDescription compatibility contract', () => {
  test('parses every supported line form without expanding the grammar', () => {
    const parsed = parseDescription([
      'Plava Samvatsara  ·  Chaitra Maasam  ·  Krishna Paksham  ·  Somavaram',
      'Ayanam: Uttarayanam  ·  Rituvu: Vasanta',
      'Sunrise 06:01  ·  Sunset 18:02  ·  Moonrise 19:03  ·  Moonset 07:04',
      'Solar sign: Mesha  ·  Lunar sign: Vrishabha',
      'Tithi:     Krishna Chaturdashi  01:02 (-1) - 03:04 (+1)',
      'Nakshatra: Rohini               05:06 – 07:08',
      'Yoga:      Siddhi               09:10 – 11:12',
      'Karana: Vishti 01:02–03:04',
      '─ Auspicious ─',
      '  Amrita Kalam  12:13 – 14:15 (+1)',
      '─ Inauspicious ─',
      '  Varjyam  16:17 (-1) – 18:19',
      '─ Choghadiya ─',
      '  20:21 – 22:23  Labh',
      '─ Night Choghadiya ─',
      '  23:24 – 00:25 (+1)  Amrit',
      '─ Eclipse ─',
      '  🌒 Solar Eclipse (Total) — not visible from this location',
      '  Window: 10:00 – 11:00',
      '  Sutak: 01:00 – 09:00',
      '⚡ Ekadashi — fasting day  ·  Pradosham',
    ].join('\n'));

    expect(parsed).toEqual({
      meta: 'Plava Nama Samvatsara · Chaitra Maasam · Krishna Paksham · Somavaram',
      samvatsara: 'Plava',
      maasam: 'Chaitra',
      paksham: 'Krishna',
      vaaram: 'Somavaram',
      ayanam: 'Uttarayanam',
      rituvu: 'Vasanta',
      sunrise: '06:01',
      sunset: '18:02',
      moonrise: '19:03',
      moonset: '07:04',
      solarSign: 'Mesha',
      lunarSign: 'Vrishabha',
      tithi: {
        name: 'Krishna Chaturdashi',
        start: '01:02',
        sflag: '-1',
        end: '03:04',
        eflag: '+1',
      },
      nakshatra: {
        name: 'Rohini',
        start: '05:06',
        sflag: null,
        end: '07:08',
        eflag: null,
      },
      yoga: {
        name: 'Siddhi',
        start: '09:10',
        sflag: null,
        end: '11:12',
        eflag: null,
      },
      karana: 'Vishti 01:02–03:04',
      auspicious: [{
        name: 'Amrita Kalam',
        start: '12:13',
        sflag: null,
        end: '14:15',
        eflag: '+1',
      }],
      inauspicious: [{
        name: 'Varjyam',
        start: '16:17',
        sflag: '-1',
        end: '18:19',
        eflag: null,
      }],
      choghadiya: [{ start: '20:21', end: '22:23', name: 'Labh' }],
      nightChoghadiya: [{ start: '23:24', end: '00:25', name: 'Amrit' }],
      eclipse: {
        kind: 'Solar',
        subtype: 'Total',
        visible: false,
        window: { start: '10:00', end: '11:00' },
        sutak: { start: '01:00', end: '09:00' },
      },
      yogas: [],
      special: ['Ekadashi — fasting day', 'Pradosham'],
    });
  });

  test('preserves new and legacy yoga/header compatibility forms', () => {
    const current = parseDescription([
      'Plava Nama Samvatsara  ·  Chaitra Maasam  ·  Shukla Paksham  ·  Mangalavaram',
      '─ Special Yogas ─',
      '  Sarvartha Siddhi Yoga',
      '  Dagdha Yoga',
    ].join('\n'));
    expect(current.samvatsara).toBe('Plava');
    expect(current.yogas).toEqual(['Sarvartha Siddhi Yoga', 'Dagdha Yoga']);

    const legacy = parseDescription([
      'Plava  ·  Chaitra Maasam  ·  Shukla Paksham  ·  Mangalavaram',
      'Yogas: Sarvartha Siddhi Yoga,   Dagdha Yoga',
    ].join('\n'));
    expect(legacy.samvatsara).toBe('Plava');
    expect(legacy.yogas).toEqual(['Sarvartha Siddhi Yoga', 'Dagdha Yoga']);
  });

  test('preserves the unindented eclipse-detail form accepted by the legacy parser', () => {
    const parsed = parseDescription([
      '─ Eclipse ─',
      '🌒 Lunar Eclipse (Partial) - visible from this location',
      '  Window: 21:00 - 22:00',
    ].join('\n'));

    expect(parsed.eclipse).toEqual({
      kind: 'Lunar',
      subtype: 'Partial',
      visible: true,
      window: { start: '21:00', end: '22:00' },
      sutak: null,
    });
  });

  test('ignores malformed lines and resets a section at blank lines', () => {
    const parsed = parseDescription([
      'Tithi: incomplete',
      'Sunrise 06:00 · Sunset missing',
      '─ Auspicious ─',
      '  Valid Window  01:00 – 02:00',
      '',
      '  Must Not Leak  03:00 – 04:00',
      '─ Eclipse ─',
      '  not-an-eclipse',
      '  Window: missing-end',
      'unknown',
    ].join('\n'));

    expect(parsed.auspicious).toEqual([{
      name: 'Valid Window',
      start: '01:00',
      sflag: null,
      end: '02:00',
      eflag: null,
    }]);
    expect(parsed.eclipse).toBeNull();
  });

  test('rejects malformed tokens without partially populating a result', () => {
    const malformedCommonLines = [
      'Tithi: Name  01:02 x 03:04',
      'Tithi: Name  invalid – 03:04',
      'Tithi: Name01:02 – 03:04',
      'Karana:',
      'Karana:value',
      'Dawn 06:01  ·  Sunset 18:02  ·  Moonrise 19:03  ·  Moonset 07:04',
      'Sunrise invalid  ·  Sunset 18:02  ·  Moonrise 19:03  ·  Moonset 07:04',
      'Plava· Chaitra Maasam  ·  Shukla Paksham  ·  Somavaram',
      'Plava ·Chaitra Maasam  ·  Shukla Paksham  ·  Somavaram',
      '⚡',
    ];
    for (const line of malformedCommonLines) {
      const parsed = parseDescription(line);
      expect(parsed.tithi).toBeNull();
      expect(parsed.karana).toBeNull();
      expect(parsed.sunrise).toBeNull();
      expect(parsed.special).toEqual([]);
    }

    const malformedWindows = [
      'No Indent  01:02 – 03:04',
      '  Name  invalid',
      '  Name01:02 – 03:04',
    ];
    for (const line of malformedWindows) {
      const parsed = parseDescription(`─ Auspicious ─\n${line}`);
      expect(parsed.auspicious).toEqual([]);
    }

    const malformedChoghadiya = [
      '01:02 – 03:04  Name',
      '  invalid – 03:04  Name',
      '  01:02 x 03:04  Name',
      '  01:02 – invalid  Name',
      '  01:02 – 03:04Name',
    ];
    for (const line of malformedChoghadiya) {
      const parsed = parseDescription(`─ Choghadiya ─\n${line}`);
      expect(parsed.choghadiya).toEqual([]);
    }

    const malformedEclipseLines = [
      '  🌒 Solar Eclipse (Total without-close',
      '  🌒 Solar Eclipse (Total) without-dash',
      '  🌒 Solar Eclipse () — visible',
    ];
    for (const line of malformedEclipseLines) {
      const parsed = parseDescription(`─ Eclipse ─\n${line}`);
      expect(parsed.eclipse).toBeNull();
    }

    const eclipseWithMalformedRanges = parseDescription([
      '─ Eclipse ─',
      '  🌒 Lunar Eclipse (Total) — visible',
      'Window: 01:00 – 02:00',
      '  Window: missing delimiter',
      '  Window: – 02:00',
      '  Sutak: 01:00 –',
      '  Other: 01:00 – 02:00',
    ].join('\n'));
    expect(eclipseWithMalformedRanges.eclipse).toEqual({
      kind: 'Lunar',
      subtype: 'Total',
      visible: true,
      window: null,
      sutak: null,
    });

    const malformedSpecialYoga = parseDescription(
      '─ Special Yogas ─\nNot indented',
    );
    expect(malformedSpecialYoga.yogas).toEqual([]);
  });

  test('handles adversarial long malformed lines within a bounded time', () => {
    const repeated = 'A'.repeat(20_000);
    const description = [
      `${repeated} · ${repeated} Maasam · ${repeated} Paksham · missing`,
      `Tithi: ${repeated} 12:34 – ${repeated}`,
      `  ${repeated}  12:34 – ${repeated}`,
      `  🌒 Solar Eclipse (${repeated}) without a separator`,
      `Yogas: ${repeated}, ${repeated}`,
    ].join('\n');

    const started = performance.now();
    const parsed = parseDescription(description);
    const elapsedMilliseconds = performance.now() - started;

    expect(parsed.tithi).toBeNull();
    expect(parsed.auspicious).toEqual([]);
    expect(parsed.eclipse).toBeNull();
    expect(parsed.yogas).toEqual([repeated, repeated]);
    expect(elapsedMilliseconds).toBeLessThan(1_000);
  });
});
