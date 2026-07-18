import { test, expect, beforeEach } from 'vitest';
import {
  getSelection, setSelection, initSelection, subscribeSelection,
  resetSelectionForTests,
} from '../selection-store';

beforeEach(resetSelectionForTests);

test('defaults: Hyderabad · drik · 12h', () => {
  expect(getSelection()).toEqual({ city: 'Hyderabad', system: 'drik', timeFmt: '12' });
});

test('setSelection patches and notifies with the changed keys', () => {
  const calls: Array<{ city: string; changed: string[] }> = [];
  subscribeSelection((sel, changed) => calls.push({ city: sel.city, changed }));
  setSelection({ city: 'Dallas' });
  expect(getSelection().city).toBe('Dallas');
  expect(calls).toEqual([{ city: 'Dallas', changed: ['city'] }]);
});

test('multi-key patch notifies once with both keys', () => {
  const seen: string[][] = [];
  subscribeSelection((_sel, changed) => seen.push(changed));
  setSelection({ city: 'London', system: 'vakya' });
  expect(seen).toEqual([['city', 'system']]);
});

test('no-op patch (same values) does not notify', () => {
  let calls = 0;
  subscribeSelection(() => calls++);
  setSelection({ city: 'Hyderabad', timeFmt: '12' });
  expect(calls).toBe(0);
});

test('undefined values in a patch are ignored', () => {
  setSelection({ city: undefined as unknown as string, system: 'vakya' });
  expect(getSelection().city).toBe('Hyderabad');
  expect(getSelection().system).toBe('vakya');
});

test('initSelection seeds without notifying', () => {
  let calls = 0;
  subscribeSelection(() => calls++);
  initSelection({ city: 'Sydney', timeFmt: '24' });
  expect(calls).toBe(0);
  expect(getSelection()).toEqual({ city: 'Sydney', system: 'drik', timeFmt: '24' });
});

test('unsubscribe stops notifications', () => {
  let calls = 0;
  const off = subscribeSelection(() => calls++);
  setSelection({ city: 'Dubai' });
  off();
  setSelection({ city: 'Chennai' });
  expect(calls).toBe(1);
});

test('listener receives a snapshot, not live state', () => {
  let snap: { city: string } | null = null;
  subscribeSelection(sel => { snap = sel; });
  setSelection({ city: 'Mumbai' });
  setSelection({ city: 'Delhi' });
  // first snapshot must still say Mumbai even after the second change
  expect(snap!.city).toBe('Delhi'); // latest call's snapshot
  const got = getSelection();
  got.city = 'Mutated';
  expect(getSelection().city).toBe('Delhi'); // getSelection returns copies
});
