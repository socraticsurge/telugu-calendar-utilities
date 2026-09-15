import { describe, expect, it } from 'vitest';
import fixtures from '../../tests/fixtures/calendar-data-contract.json';
import { calendarEventDay, calendarEvents } from '../lib/calendar-data';
import { parseDescription } from '../lib/parse-description';

describe('structured calendar data', () => {
  it('matches all legacy fields across systems, cities, eclipses and date boundaries', () => {
    for (const fixture of fixtures) {
      const events = calendarEvents(fixture, fixture.city, fixture.system);
      expect(events, `${fixture.city}/${fixture.system}`).not.toBeNull();
      for (const [date, event] of events!) {
        expect(calendarEventDay(event), `${fixture.city}/${fixture.system}/${date}`)
          .toEqual(parseDescription(event.description));
        expect(calendarEventDay({ ...event, description: 'Wording may change freely.' }))
          .toEqual(event.day);
      }
    }
  });
  it('keeps legacy events usable', () => {
    const event = { summary: '', description: '' };
    expect(calendarEventDay(event)).toEqual(parseDescription(''));
  });
  it('rejects invalid identity, versions and nested fields', () => {
    const fixture = fixtures[0];
    for (const patch of [null, {}, { ...fixture, schemaVersion: 2 },
      { ...fixture, city: 'wrong' }, { ...fixture, system: 'wrong' },
      { ...fixture, timezone: 'invalid' }, { ...fixture, days: {} },
      { ...fixture, days: { bad: {} } }]) {
      expect(calendarEvents(patch, fixture.city, fixture.system)).toBeNull();
    }
    const key = Object.keys(fixture.days)[0];
    const event = Object.values(fixture.days)[0];
    for (const field of Object.keys(event.day)) {
      const days = { [key]: { ...event, day: { ...event.day, [field]: 42 } } };
      expect(calendarEvents({ ...fixture, days }, fixture.city, fixture.system), field).toBeNull();
    }
  });
});
