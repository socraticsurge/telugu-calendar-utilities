import { afterAll, afterEach, beforeAll, beforeEach, vi } from 'vitest';

import { createGuestProfileStore, type ProfileStorage } from '../../lib/guest-profile-store';

import type { TarabalamPanelModule } from './types';

export class MemoryStorage implements ProfileStorage {
  readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

export class BrowserMemoryStorage extends MemoryStorage implements Storage {
  get length(): number {
    return this.values.size;
  }

  clear(): void {
    this.values.clear();
  }

  key(index: number): string | null {
    return Array.from(this.values.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }
}

export class DeniedStorage implements ProfileStorage {
  getItem(): string | null {
    throw new Error('read denied');
  }

  setItem(): void {
    throw new Error('write denied');
  }
}

export function ids(...values: string[]): () => string {
  let index = 0;
  return () => values[index++] || `guest_generated_${index}`;
}

export function renderPanelFixture(): void {
  document.body.innerHTML = `
    <section class="tb-section">
      <header><button class="tb-reset" onclick="tbResetProfiles()">clear all</button></header>
      <div id="tb-profiles"></div>
      <button id="tb-add-btn" class="tb-add" onclick="tbAddRow()">add</button>
    </section>
    <div id="tb-summary">old summary</div>
    <div id="tb-result">old result</div>
    <div id="mu-context">old context</div>
    <div id="mu-result">old slots</div>
    <input id="tb-from" value="2026-08-28">
    <input id="tb-to" value="2026-09-04">
    <select id="mu-activity">
      <option value="wedding" selected>Wedding</option>
      <option value="gold">Gold</option>
      <option value="travel">Travel</option>
      <option value="gruhapravesha">Gruhapravesha</option>
      <option value="seemantha">Seemantha</option>
      <option value="surgery">Surgery</option>
      <option value="borrowing_money">Borrowing money</option>
    </select>
  `;
}

export function changeCheckbox(id: string, checked: boolean): void {
  const checkbox = document.querySelector<HTMLInputElement>(
    `input[data-profile-selection="${id}"]`,
  );
  if (!checkbox) throw new Error(`Missing profile checkbox ${id}`);
  checkbox.checked = checked;
  checkbox.dispatchEvent(new Event('change', { bubbles: true }));
}

export function clickAction(action: string): HTMLButtonElement {
  const button = document.querySelector<HTMLButtonElement>(`button[data-action="${action}"]`);
  if (!button) throw new Error(`Missing action ${action}`);
  button.click();
  return button;
}

export function chooseManualValues(values: {
  name?: string;
  nakshatra?: string;
  pada?: string;
  lagna?: string;
}): void {
  let row = document.querySelector<HTMLElement>('[data-manual-id]');
  if (!row) throw new Error('Missing manual participant');
  if (values.name !== undefined) {
    const input = row.querySelector<HTMLInputElement>('input[type="text"]')!;
    input.value = values.name;
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }
  if (values.nakshatra !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[0];
    select.value = values.nakshatra;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
  row = document.querySelector<HTMLElement>('[data-manual-id]')!;
  if (values.pada !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[1];
    select.value = values.pada;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
  row = document.querySelector<HTMLElement>('[data-manual-id]')!;
  if (values.lagna !== undefined) {
    const select = row.querySelectorAll<HTMLSelectElement>('select')[2];
    select.value = values.lagna;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }
}

function createPanelFixture(panel: TarabalamPanelModule) {
  const browserStorage = new BrowserMemoryStorage();
  vi.stubGlobal('localStorage', browserStorage);
  renderPanelFixture();
  const profileStorage = new MemoryStorage();
  return {
    panel, browserStorage, profileStorage,
    store: createGuestProfileStore(profileStorage),
    createProfile: vi.fn<(trigger: HTMLElement) => void>(),
    editProfile: vi.fn<(id: string, trigger: HTMLElement) => void>(),
    manageProfiles: vi.fn<(trigger: HTMLElement) => void>(),
  };
}

export type PanelFixture = ReturnType<typeof createPanelFixture>;

/** Each suite owns its module instance, controller, storage, mocks and cleanup. */
export function usePanelFixture(
  assign: (fixture: PanelFixture) => void,
  destroyController: () => void = () => {},
): void {
  let panel: TarabalamPanelModule;
  beforeAll(async () => {
    // Retain the original runtime import without widening the strict core graph.
    const panelPath = '../../panels/' + 'tarabalam';
    panel = await import(panelPath) as TarabalamPanelModule;
  });
  beforeEach(() => { assign(createPanelFixture(panel)); });
  afterEach(() => {
    destroyController();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });
  afterAll(() => { vi.unstubAllGlobals(); });
}
