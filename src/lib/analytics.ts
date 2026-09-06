// Lightweight event tracking — no-op unless a trusted, first-party-compatible
// hook is deliberately supplied by the hosting page.

interface GoatCounterWindow extends Window {
  goatcounter?: {
    count?: (event: { path: string; title: string; event: boolean }) => void;
  };
}

export function gcEvent(name: string): void {
  const gc = (window as GoatCounterWindow).goatcounter;
  if (gc && gc.count) gc.count({ path: name, title: name, event: true });
}
