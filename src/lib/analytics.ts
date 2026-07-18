// Lightweight event tracking — no-ops when GoatCounter is blocked or offline.

export function gcEvent(name: string): void {
  const gc = (window as any).goatcounter;
  if (gc && gc.count) gc.count({ path: name, title: name, event: true });
}
