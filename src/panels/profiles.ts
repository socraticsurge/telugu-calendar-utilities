import {
  GuestProfileStore, MAX_GUEST_PROFILES, GUEST_PROFILE_STORAGE_KEY,
  GUEST_BIRTH_PROFILE_STORAGE_KEY, GUEST_PROFILE_COMMIT_STORAGE_KEY, type GuestProfile,
} from '../lib/guest-profile-store';
import { birthProfileCalculationEnabled } from '../lib/remote-calculation-activation';
import {
  type ProfilesPanelOptions, type ProfilesPanelController, type ResolvedProfilesPanelContext,
  type PanelView, type ProfilePanelHost,
} from './profiles/contracts';
import { restoreFocus, resolvePanelContext, restoreOriginFocus } from './profiles/navigation';
import { renderList as drawList } from './profiles/list-view';
import { renderDetail as drawDetail } from './profiles/detail-view';
import { renderManualForm as drawManualForm } from './profiles/manual-form';
import { renderBirthForm as drawBirthForm } from './profiles/birth-form';
import { renderIssue as drawIssue } from './profiles/notices';
export type { ProfilesPanelContext, ProfilesPanelOptions, ProfilesPanelController } from './profiles/contracts';

export function listenForGuestProfileStorageChanges(
  store: Pick<GuestProfileStore, 'reload'>,
  target: Window = window,
): () => void {
  const onStorage = (event: StorageEvent): void => {
    const relevantKeys = [null, GUEST_PROFILE_STORAGE_KEY, GUEST_BIRTH_PROFILE_STORAGE_KEY, GUEST_PROFILE_COMMIT_STORAGE_KEY];
    if (!relevantKeys.includes(event.key)) return;
    store.reload();
  };
  target.addEventListener('storage', onStorage);
  return () => target.removeEventListener('storage', onStorage);
}

export function initProfilesPanel(
  store: GuestProfileStore,
  options: ProfilesPanelOptions,
): ProfilesPanelController {
  const root = options.root || document.querySelector<HTMLElement>('#profiles-root');
  if (!root) throw new Error('Profiles panel root #profiles-root was not found');
  const birthCalculationActive = options.birthCalculationEnabled
    ?? birthProfileCalculationEnabled();

  let view: PanelView = { kind: 'list' };

  const returnToOrigin = (
    context: ResolvedProfilesPanelContext,
    savedProfile?: GuestProfile,
  ): void => {
    if (context.returnTo) options.navigate(context.returnTo);
    // Select and focus only after the origin is visible again. Hidden controls
    // cannot reliably receive focus in real browsers.
    if (savedProfile) context.onSaved?.(savedProfile);

    restoreOriginFocus(root, context, savedProfile);
  };

  let activeFormMethod: 'birth-details' | 'manual' = birthCalculationActive
    ? 'birth-details'
    : 'manual';

  const renderList = (): void => drawList(host);
  const renderDetail = (id: string, context: ResolvedProfilesPanelContext, focus = false): void =>
    drawDetail(host, id, context, focus);
  const renderManualForm = (mode: 'create' | 'edit', context: ResolvedProfilesPanelContext, profile?: GuestProfile): void =>
    drawManualForm(host, mode, context, profile);
  const renderBirthForm = (mode: 'create' | 'edit', context: ResolvedProfilesPanelContext, profile?: GuestProfile): void =>
    drawBirthForm(host, mode, context, profile);

  const renderActiveForm = (mode: 'create' | 'edit', context: ResolvedProfilesPanelContext, profile?: GuestProfile): void => {
    if (!birthCalculationActive || activeFormMethod === 'manual') renderManualForm(mode, context, profile);
    else renderBirthForm(mode, context, profile);
  };

  const renderEdit = (editing: Extract<PanelView, { kind: 'edit' }>): void => {
    const profile = store.get(editing.profileId);
    if (!profile) {
      view = { kind: 'list' };
      renderList();
      return;
    }
    if (profile.source === 'birth-details' && !birthCalculationActive) {
      view = { kind: 'detail', profileId: profile.id, context: editing.context };
      renderDetail(profile.id, editing.context);
      return;
    }
    renderActiveForm('edit', editing.context, profile);
  };

  const controller: ProfilesPanelController = {
    openCreate(context = {}) {
      const resolvedContext = resolvePanelContext(context);
      if (store.getSnapshot().profiles.length >= MAX_GUEST_PROFILES) {
        view = { kind: 'list' };
        renderList();
        return;
      }
      view = { kind: 'create', context: resolvedContext };
      activeFormMethod = birthCalculationActive ? 'birth-details' : 'manual';
      if (birthCalculationActive) {
        renderBirthForm('create', resolvedContext);
      } else {
        renderManualForm('create', resolvedContext);
      }
    },
    openView(profileId, context = {}) {
      const resolvedContext = resolvePanelContext(context);
      const profile = store.get(profileId);
      if (!profile) {
        view = { kind: 'list' };
        renderList();
        restoreFocus(null);
        return;
      }
      view = { kind: 'detail', profileId, context: resolvedContext };
      renderDetail(profileId, resolvedContext, true);
    },
    openEdit(profileId, context = {}) {
      const resolvedContext = resolvePanelContext(context);
      const profile = store.get(profileId);
      if (!profile) {
        view = { kind: 'list' };
        renderList();
        return;
      }
      if (profile.source === 'birth-details' && !birthCalculationActive) {
        view = { kind: 'detail', profileId, context: resolvedContext };
        renderDetail(profileId, resolvedContext, true);
        return;
      }
      view = { kind: 'edit', profileId, context: resolvedContext };
      activeFormMethod = profile.source;
      if (activeFormMethod === 'birth-details') {
        renderBirthForm('edit', resolvedContext, profile);
      } else {
        renderManualForm('edit', resolvedContext, profile);
      }
    },
    render() {
      if (view.kind === 'detail') {
        renderDetail(view.profileId, view.context);
        return;
      }
      if (view.kind === 'create') {
        renderActiveForm('create', view.context);
        return;
      }
      if (view.kind === 'edit') {
        renderEdit(view);
        return;
      }
      renderList();
    },
    destroy() {
      unsubscribe();
      root.replaceChildren();
    },
  };

  const host: ProfilePanelHost = {
    root, store, options, birthCalculationActive, controller,
    setView(next) { view = next; },
    setFormMethod(method) { activeFormMethod = method; },
    renderList, renderDetail, renderManualForm, renderBirthForm, returnToOrigin,
    renderIssue: snapshot => drawIssue(host, snapshot),
  };

  const unsubscribe = store.subscribe(() => {
    // An external tab may change persistence while this form is open. Keep the
    // guest's unsaved fields and focus intact; Cancel or Save reconciles against
    // the already-refreshed store snapshot.
    if (view.kind === 'list' || view.kind === 'detail') controller.render();
  });
  controller.render();
  return controller;
}
