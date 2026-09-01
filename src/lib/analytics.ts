// Lightweight event tracking — no-op unless a trusted, first-party-compatible
// hook is deliberately supplied by the hosting page.

export function gcEvent(name: string): void {
  const gc = (window as any).goatcounter;
  if (gc && gc.count) gc.count({ path: name, title: name, event: true });
}
