import { type ProfilesPanelContext, type ResolvedProfilesPanelContext } from './contracts';
import { type GuestProfile } from '../../lib/guest-profile-store';

export function restoreFocus(node: HTMLElement | null): void {
  if (node?.isConnected) {
    node.focus();
    if (document.activeElement === node) return;
  }
  const heading = document.querySelector<HTMLElement>('#profiles-title');
  heading?.focus();
}

export function replacementScopeId(target: HTMLElement): string | null {
  if (target.closest('#profiles-root')) return 'profiles-root';
  if (target.closest('#tb-profiles')) return 'tb-profiles';
  return null;
}

export function replacementFocusResolver(
  target: HTMLElement | null | undefined,
): (() => HTMLElement | null) | undefined {
  if (!target) return undefined;

  const gocharaKey = target.dataset.goProfileFocus;
  if (gocharaKey) {
    return () => Array.from(
      document.querySelectorAll<HTMLElement>('[data-go-profile-focus]'),
    ).find(candidate => candidate.dataset.goProfileFocus === gocharaKey) || null;
  }

  const action = target.dataset.action;
  const profileId = target.closest<HTMLElement>('[data-profile-id]')?.dataset.profileId;
  const scopeId = replacementScopeId(target);
  if (!action || !scopeId) return undefined;

  return () => {
    const scope = document.getElementById(scopeId);
    if (!scope) return null;
    return Array.from(scope.querySelectorAll<HTMLElement>('[data-action]')).find(candidate => {
      if (candidate.dataset.action !== action) return false;
      if (!profileId) return true;
      return candidate.closest<HTMLElement>('[data-profile-id]')?.dataset.profileId === profileId;
    }) || null;
  };
}
export function resolvePanelContext(
  context: ProfilesPanelContext,
): ResolvedProfilesPanelContext {
  return {
    ...context,
    resolveFocusTarget: replacementFocusResolver(context.focusTarget),
  };
}
export function focusUsableElement(target: HTMLElement | null | undefined): boolean {
  if (!target) return false;
  if (target instanceof HTMLButtonElement && target.disabled) return false;
  target.focus();
  return document.activeElement === target;
}

export function focusSavedJourney(
  context: ResolvedProfilesPanelContext,
  savedProfile: GuestProfile,
): boolean {
  if (context.returnTo === 'gochara') {
    document.getElementById('go-view')?.focus();
    return true;
  }
  if (context.returnTo !== 'tarabalam') return false;
  const selectedProfile = Array.from(
    document.querySelectorAll<HTMLInputElement>('[data-profile-selection]'),
  ).find(candidate => candidate.dataset.profileSelection === savedProfile.id);
  return focusUsableElement(selectedProfile);
}

export function focusOriginFallback(context: ResolvedProfilesPanelContext): boolean {
  if (context.returnTo === 'gochara') {
    document.getElementById('go-view')?.focus();
    return true;
  }
  if (context.returnTo !== 'tarabalam') return false;
  document.querySelector<HTMLElement>('#tb-profiles [data-action]')?.focus();
  return true;
}

export function focusSavedEdit(root: HTMLElement, profileId: string): boolean {
  const savedEdit = Array.from(
    root.querySelectorAll<HTMLElement>('[data-profile-id] [data-action="edit-profile"]'),
  ).find(candidate => (
    candidate.closest<HTMLElement>('[data-profile-id]')?.dataset.profileId === profileId
  ));
  return focusUsableElement(savedEdit);
}

/** Saved journeys win over stale edit triggers; then fall back to the origin. */
export function restoreOriginFocus(
  root: HTMLElement,
  context: ResolvedProfilesPanelContext,
  savedProfile?: GuestProfile,
): void {
  if (savedProfile && focusSavedJourney(context, savedProfile)) return;
  if (focusUsableElement(originFocusTarget(context))) return;
  if (focusOriginFallback(context)) return;
  if (savedProfile && focusSavedEdit(root, savedProfile.id)) return;
  restoreFocus(null);
}

export function originFocusTarget(context: ResolvedProfilesPanelContext): HTMLElement | null | undefined {
  if (context.focusTarget?.isConnected) return context.focusTarget;
  return context.resolveFocusTarget?.();
}
