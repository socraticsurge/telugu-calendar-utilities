import {
  GuestProfileStore, GuestProfileStoreError, MAX_GUEST_PROFILES,
  type GuestProfile, type GuestProfileDraft,
} from '../../lib/guest-profile-store';
import type { PanelView, ResolvedProfilesPanelContext } from './contracts';

export function saveProfile(
  store: GuestProfileStore,
  mode: 'create' | 'edit',
  profile: GuestProfile | undefined,
  draft: GuestProfileDraft,
): GuestProfile {
  if (mode === 'edit' && profile) return store.update(profile.id, draft);
  return store.create(draft);
}

export function failedSaveView(
  mode: 'create' | 'edit',
  profile: GuestProfile | undefined,
  context: ResolvedProfilesPanelContext,
): PanelView {
  if (mode === 'edit' && profile) return { kind: 'edit', profileId: profile.id, context };
  return { kind: 'create', context };
}

export function saveErrorMessage(error: unknown): string {
  if (error instanceof GuestProfileStoreError && error.code === 'profile-limit') {
    return `You can save up to ${MAX_GUEST_PROFILES} profiles. Delete one before adding another.`;
  }
  if (error instanceof GuestProfileStoreError && error.code === 'profile-not-found') {
    return 'This profile is no longer available. Return to Profiles and try again.';
  }
  return 'The profile could not be saved. Check the details and try again.';
}
