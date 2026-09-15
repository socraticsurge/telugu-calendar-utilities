/** Validated structured day data, with the legacy parser isolated at one boundary. */
import { parseDescription, type ParsedDescription } from './parse-description';

export interface CalendarEvent {
  summary: string;
  description: string;
  day?: ParsedDescription;
}

function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function text(value: unknown): value is string {
  return typeof value === 'string';
}
function nullableText(value: unknown): boolean {
  return value === null || text(value);
}
function clock(value: unknown): boolean {
  return text(value) && /^([01]\d|2[0-3]):[0-5]\d$/.test(value);
}
function flag(value: unknown): boolean {
  return value === null || value === '+1' || value === '-1';
}
function window(value: unknown): boolean {
  return record(value) && text(value.name) && clock(value.start) && clock(value.end);
}
function timedEntry(value: unknown): boolean {
  return record(value) && window(value) && flag(value.sflag) && flag(value.eflag);
}
function list(value: unknown, check: (item: unknown) => boolean): boolean {
  return Array.isArray(value) && value.every(check);
}
function range(value: unknown): boolean {
  return value === null || (record(value) && text(value.start) && text(value.end));
}
function eclipse(value: unknown): boolean {
  return value === null || (record(value) && text(value.kind) && text(value.subtype)
    && typeof value.visible === 'boolean' && range(value.window) && range(value.sutak));
}

export function isCalendarDay(value: unknown): value is ParsedDescription {
  if (!record(value)) return false;
  const labels = ['meta', 'samvatsara', 'maasam', 'paksham', 'vaaram', 'ayanam',
    'rituvu', 'solarSign', 'lunarSign'];
  return [
    labels.every(key => text(value[key])),
    ['sunrise', 'sunset', 'moonrise', 'moonset'].every(key => clock(value[key])),
    ['tithi', 'nakshatra', 'yoga'].every(key => timedEntry(value[key])),
    nullableText(value.karana),
    ['auspicious', 'inauspicious'].every(key => list(value[key], timedEntry)),
    ['choghadiya', 'nightChoghadiya'].every(key => list(value[key], window)),
    ['yogas', 'special'].every(key => list(value[key], text)),
    eclipse(value.eclipse),
  ].every(Boolean);
}

function validTimezone(value: unknown): boolean {
  if (!text(value)) return false;
  try { new Intl.DateTimeFormat('en', { timeZone: value }); } catch { return false; }
  return true;
}

function matchesFeed(payload: Record<string, unknown>, city: string, system: string): boolean {
  return [payload.schemaVersion === 1, payload.city === city,
    payload.system === system.replaceAll('-', '_'), validTimezone(payload.timezone)].every(Boolean);
}

function calendarEvent(value: unknown): CalendarEvent | null {
  if (!record(value)) return null;
  if (!text(value.summary)) return null;
  if (!text(value.description)) return null;
  if (!isCalendarDay(value.day)) return null;
  return { summary: value.summary, description: value.description, day: value.day };
}

export function calendarEvents(payload: unknown, city: string, system: string): Map<string, CalendarEvent> | null {
  if (!record(payload)) return null;
  if (!matchesFeed(payload, city, system)) return null;
  if (!record(payload.days)) return null;
  const result = new Map<string, CalendarEvent>();
  for (const [key, value] of Object.entries(payload.days)) {
    if (!/^\d{8}$/.test(key)) return null;
    const event = calendarEvent(value);
    if (!event) return null;
    result.set(key, event);
  }
  return result.size ? result : null;
}

export function calendarEventDay(event: CalendarEvent): ParsedDescription {
  return event.day ?? parseDescription(event.description);
}
