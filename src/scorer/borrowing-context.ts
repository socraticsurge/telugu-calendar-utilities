export const BORROWING_PURPOSES = [
  'quick_domestic_or_personal',
  'business',
  'other_or_unknown',
] as const;

export type BorrowingPurpose = typeof BORROWING_PURPOSES[number];

export interface BorrowingPurposeContext {
  purpose: BorrowingPurpose;
  status: 'selected' | 'unknown';
}

/** Normalize the minimum non-financial context without accepting free text. */
export function borrowingPurposeContext(value: unknown): BorrowingPurposeContext {
  const purpose = BORROWING_PURPOSES.includes(value as BorrowingPurpose)
    ? value as BorrowingPurpose
    : 'other_or_unknown';
  return {
    purpose,
    status: purpose === 'other_or_unknown' ? 'unknown' : 'selected',
  };
}

export function borrowingPurposeLabel(purpose: BorrowingPurpose): string {
  if (purpose === 'quick_domestic_or_personal') return 'Quick domestic or personal use';
  if (purpose === 'business') return 'Business use';
  return 'Other or not yet known';
}

export function manualRowAppliesToBorrowingPurpose(
  rowPurpose: string | undefined,
  purpose: BorrowingPurpose,
): boolean {
  return !rowPurpose
    || rowPurpose === 'safety_override'
    || rowPurpose === purpose;
}
