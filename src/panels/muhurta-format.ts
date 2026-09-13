import { fmtT } from '../lib/format';

export function muToT(minutes: number): string {
  const normalized = ((minutes % 1440) + 1440) % 1440;
  const hour = String(Math.floor(normalized / 60)).padStart(2, '0');
  const minute = String(normalized % 60).padStart(2, '0');
  return fmtT(`${hour}:${minute}`);
}
