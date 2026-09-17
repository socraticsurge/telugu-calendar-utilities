import { restoreFocus } from './navigation';

export function element<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function button(text: string, className: string): HTMLButtonElement {
  const node = element('button', className, text);
  node.type = 'button';
  return node;
}

export function appendOption(
  select: HTMLSelectElement,
  value: string,
  label: string,
): void {
  const option = element('option');
  option.value = value;
  option.textContent = label;
  select.append(option);
}
export function showNativeDialog(dialog: HTMLDialogElement): void {
  if (typeof dialog.showModal === 'function') {
    dialog.showModal();
  } else {
    // jsdom and older embedded browsers do not expose the method, but retaining
    // the native element and open state preserves semantics and testability.
    dialog.setAttribute('open', '');
  }
}

export function closeNativeDialog(dialog: HTMLDialogElement): void {
  if (typeof dialog.close === 'function') {
    dialog.close();
  } else {
    dialog.removeAttribute('open');
  }
  dialog.remove();
}

let confirmDialogSequence = 0;

export function createConfirmDialog(config: {
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => void;
  trigger: HTMLElement;
}): HTMLDialogElement {
  const dialog = element('dialog', 'profiles-dialog');
  confirmDialogSequence += 1;
  const id = `profiles-dialog-${confirmDialogSequence}`;
  const title = element('h2', 'profiles-dialog__title', config.title);
  title.id = `${id}-title`;
  const description = element('p', 'profiles-dialog__description', config.description);
  description.id = `${id}-description`;
  dialog.setAttribute('aria-labelledby', title.id);
  dialog.setAttribute('aria-describedby', description.id);

  const actions = element('div', 'profiles-dialog__actions');
  const cancel = button('Cancel', 'profiles-button profiles-button--secondary');
  const confirm = button(config.confirmLabel, 'profiles-button profiles-button--danger');
  actions.append(cancel, confirm);
  dialog.append(title, description, actions);

  const cancelAndRestore = (): void => {
    closeNativeDialog(dialog);
    restoreFocus(config.trigger);
  };
  cancel.addEventListener('click', cancelAndRestore);
  dialog.addEventListener('cancel', event => {
    event.preventDefault();
    cancelAndRestore();
  });
  confirm.addEventListener('click', () => {
    closeNativeDialog(dialog);
    config.onConfirm();
  });
  document.body.append(dialog);
  showNativeDialog(dialog);
  cancel.focus();
  return dialog;
}
