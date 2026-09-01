// Time formatting — reads the SelectionStore's timeFmt directly.
// Extracted verbatim from main.ts (one-shell decomposition); the only
// change is reading the store instead of a module-local TIME_FMT.

import { getSelection } from '../selection-store';

export function fmtT(t: string): string {
  if (getSelection().timeFmt === '24') return t;
  const m = t.match(/^(\d{2}):(\d{2})$/);
  if (!m) return t;
  const h = Number(m[1]);
  return `${h % 12 || 12}:${m[2]}${h < 12 ? 'am' : 'pm'}`;
}

// The feed marks times falling outside the event's date with (+1)/(-1);
// render those as superscripts. Old feeds without markers fall back to the
// end-reads-earlier-than-start heuristic for the +1 case.
export function dayMark(flag: string | null | undefined): string {
  if (!flag) return '';
  const title = flag === '+1' ? 'after midnight, on the next day' : 'on the previous day';
  return `<sup class="plus1" title="${title}" aria-label="${title}" tabindex="0">${flag === '+1' ? '+1' : '\u22121'}</sup>`;
}

export function fmtRange(start: string, end: string, sep?: string, sflag?: string | null, eflag?: string | null): string {
  if (!sflag && !eflag && end <= start) eflag = '+1';
  return `${fmtT(start)}${dayMark(sflag)}${sep || ' \u2013 '}${fmtT(end)}${dayMark(eflag)}`;
}

export function fmtPlain(t: string, flag?: string | null): string {
  return fmtT(t) + (flag === '+1' ? ' (next day)' : flag === '-1' ? ' (prev day)' : '');
}

// Date → feed key (YYYYMMDD)
export function stampOf(d: Date): string {
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
}
