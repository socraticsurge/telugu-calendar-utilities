/** Browser request boundary; surface-specific limits remain explicit. */
export interface SearchParticipant {
  id?: string;
  name?: string;
  nak?: string | null;
  rasi?: string | null;
  lagna?: string | null;
}

export interface BrowserSearchInput {
  activity: string;
  from: string;
  to: string;
  city: string;
  system: string;
  chandraMode: string;
  people: SearchParticipant[];
  roleId: string | null;
  borrowingPurpose: string | null;
}

export function searchFingerprint(input: BrowserSearchInput): string {
  return JSON.stringify(input);
}

export function browserSearchWindow(fromIso: string, toIso: string) {
  const from = new Date(fromIso + 'T00:00:00');
  const to = new Date(toIso + 'T00:00:00');
  // Preserve civil-date anchoring and the existing rounded interval convention.
  const nDays = Math.min(60, Math.max(1, Math.round((to.getTime() - from.getTime()) / 86400000) + 1));
  return { from, nDays };
}
