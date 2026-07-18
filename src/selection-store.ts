// SelectionStore — the one source of truth for the global viewing
// selection: city, calculation system, and time format.
//
// Pure module: no DOM, no localStorage. main.ts owns the edges
// (reading persisted values at boot, writing them on change, mirroring
// the <select> elements). Components subscribe instead of reaching
// into each other's DOM — and a future deep-link feature becomes a
// URL↔store sync instead of a scavenger hunt.
//
// Unit-tested by src/__tests__/selection-store.test.ts (Vitest).

export type TimeFmt = '12' | '24';

export interface Selection {
  city: string;
  system: string;
  timeFmt: TimeFmt;
}

export type SelectionKey = keyof Selection;
export type SelectionListener = (sel: Selection, changed: SelectionKey[]) => void;

const DEFAULTS: Selection = { city: 'Hyderabad', system: 'drik', timeFmt: '12' };

let state: Selection = { ...DEFAULTS };
const listeners: SelectionListener[] = [];

/** Boot-time seed: set values without notifying subscribers. */
export function initSelection(partial: Partial<Selection>): void {
  state = { ...state, ...partial };
}

export function getSelection(): Selection {
  return { ...state };
}

/**
 * Apply a partial update. Subscribers are notified once, with the list
 * of keys that actually changed; a patch that changes nothing is a
 * silent no-op.
 */
export function setSelection(patch: Partial<Selection>): void {
  const changed = (Object.keys(patch) as SelectionKey[])
    .filter(k => patch[k] !== undefined && patch[k] !== state[k]);
  if (!changed.length) return;
  const next = { ...state };
  for (const k of changed) (next[k] as Selection[SelectionKey]) = patch[k]!;
  state = next;
  const snapshot = { ...state };
  for (const fn of [...listeners]) fn(snapshot, changed);
}

/** Subscribe to changes. Returns an unsubscribe function. */
export function subscribeSelection(fn: SelectionListener): () => void {
  listeners.push(fn);
  return () => {
    const i = listeners.indexOf(fn);
    if (i >= 0) listeners.splice(i, 1);
  };
}

/** Test helper: reset to defaults and drop all subscribers. */
export function resetSelectionForTests(): void {
  state = { ...DEFAULTS };
  listeners.length = 0;
}
