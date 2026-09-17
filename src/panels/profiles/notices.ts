import { type ProfilePanelHost } from './contracts';
import { element, button, createConfirmDialog } from './elements';
import { restoreFocus } from './navigation';
import { type GuestProfileSnapshot } from '../../lib/guest-profile-store';

export function issueMessage(snapshot: GuestProfileSnapshot): string | null {
  if (snapshot.issue === 'malformed-storage') {
    return 'Saved profile data was damaged and has been reset. You can create profiles again.';
  }
  if (snapshot.issue === 'malformed-birth-storage') {
    return 'Saved birth calculations were damaged and have been removed. Your names and manual astrology details are still available.';
  }
  if (snapshot.issue === 'uncommitted-birth-storage') {
    return 'A saved birth calculation could not be verified and was not attached. Your manual profile details remain available; your saved browser data was not overwritten.';
  }
  if (snapshot.issue === 'unsupported-storage-version') {
    return 'These profiles use a newer or unrecognized format. Changes on this page last only for this session; your saved browser data was not overwritten.';
  }
  if (snapshot.persistence === 'memory' || snapshot.issue === 'storage-unavailable') {
    return 'Browser storage is unavailable. Profiles created now last only for this session.';
  }
  return null;
}
export const renderIssue = (
  host: ProfilePanelHost,snapshot: GuestProfileSnapshot): HTMLElement | null => {
  const { root, store } = host;
  const message = issueMessage(snapshot);
  if (!message) return null;
  const notice = element('div', 'profiles-notice profiles-notice--warning', message);
  notice.setAttribute('role', 'alert');
  notice.dataset.profileIssue = snapshot.issue || snapshot.persistence;
  if (
    snapshot.issue === 'uncommitted-birth-storage'
    && store.canDiscardUncommittedStorage()
  ) {
    const discard = button(
      'Remove incomplete saved data',
      'profiles-button profiles-button--quiet',
    );
    discard.dataset.action = 'discard-uncommitted-storage';
    discard.addEventListener('click', () => {
      createConfirmDialog({
        title: 'Remove incomplete saved data?',
        description: 'This removes the incomplete local profile transaction so you can save profiles in this browser again. This action cannot be undone.',
        confirmLabel: 'Remove incomplete data',
        trigger: discard,
        onConfirm: () => {
          store.discardUncommittedStorage();
          restoreFocus(root);
        },
      });
    });
    notice.append(discard);
  }
  return notice;
};
