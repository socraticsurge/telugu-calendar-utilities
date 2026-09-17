import { ElectionChartApiError } from './remote-api/contracts';

function wallEpochFor(isoDate: string, minuteOfDay: number): number {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate);
  const validMinute = Number.isInteger(minuteOfDay) && minuteOfDay >= 0 && minuteOfDay < 2880;
  if (!match || !validMinute) {
    throw new ElectionChartApiError('invalid-request', 'The local chart time is invalid.');
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const calendarDate = new Date(Date.UTC(year, month - 1, day));
  if (!validCalendarDate(calendarDate, { year, month, day })) {
    throw new ElectionChartApiError('invalid-request', 'The local chart date is invalid.');
  }
  return calendarDate.getTime() + minuteOfDay * 60_000;
}

interface CivilDate { year: number; month: number; day: number }
interface CivilMinute extends CivilDate { hour: number; minute: number }

function validCalendarDate(date: Date, target: CivilDate): boolean {
  if (target.year < 100 || target.year > 9999) return false;
  return date.getUTCFullYear() === target.year
    && date.getUTCMonth() + 1 === target.month && date.getUTCDate() === target.day;
}

function zonedFormatter(timeZone: string): Intl.DateTimeFormat {
  try {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hourCycle: 'h23',
    });
  } catch {
    throw new ElectionChartApiError('invalid-request', 'The selected time zone is invalid.');
  }
}

function zonedParts(formatter: Intl.DateTimeFormat, epoch: number): Record<string, number> {
  const values: Record<string, number> = {};
  for (const part of formatter.formatToParts(new Date(epoch))) {
    if (part.type !== 'literal') values[part.type] = Number(part.value);
  }
  return values;
}

function nearbyOffsets(formatter: Intl.DateTimeFormat, wallEpoch: number): Set<number> {
  const offsets = new Set<number>();
  for (let deltaHours = -36; deltaHours <= 36; deltaHours += 6) {
    const probe = wallEpoch + deltaHours * 60 * 60 * 1000;
    const parts = zonedParts(formatter, probe);
    const represented = Date.UTC(
      parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second,
    );
    offsets.add(represented - probe);
  }
  return offsets;
}

function matchesCivilMinute(parts: Record<string, number>, target: CivilMinute): boolean {
  const dateMatches = parts.year === target.year && parts.month === target.month && parts.day === target.day;
  return dateMatches && parts.hour === target.hour && parts.minute === target.minute;
}

function matchingInstants(formatter: Intl.DateTimeFormat, wallEpoch: number): Set<number> {
  const wall = new Date(wallEpoch);
  const target = {
    year: wall.getUTCFullYear(), month: wall.getUTCMonth() + 1, day: wall.getUTCDate(),
    hour: wall.getUTCHours(), minute: wall.getUTCMinutes(),
  };
  const candidates = new Set<number>();
  // Preserve the existing offset search and reject DST folds/gaps by round-trip.
  for (const offset of nearbyOffsets(formatter, wallEpoch)) {
    const candidate = wallEpoch - offset;
    if (matchesCivilMinute(zonedParts(formatter, candidate), target)) candidates.add(candidate);
  }
  return candidates;
}

/** Convert a city-local date/minute pair into an exact UTC ISO instant. */
export function localWallTimeToInstant(isoDate: string, minuteOfDay: number, timeZone: string): string {
  const wallEpoch = wallEpochFor(isoDate, minuteOfDay);
  const candidates = matchingInstants(zonedFormatter(timeZone), wallEpoch);
  if (candidates.size !== 1) {
    throw new ElectionChartApiError(
      'invalid-request',
      candidates.size
        ? 'That local time is ambiguous in the selected time zone.'
        : 'That local time does not exist in the selected time zone.',
    );
  }
  return new Date([...candidates][0]).toISOString();
}
