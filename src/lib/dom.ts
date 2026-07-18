// Typed DOM lookup helpers for the panels.
//
// The panels read form-control properties (.value/.options/.selectedIndex/
// .checked) off elements fetched by id. getElementById returns the generic
// HTMLElement, so those accesses need a type. selEl/inpEl name the intent
// at the call site; the cast erases at runtime (zero behavior change) while
// keeping genuine typos on these elements a compile error.

export function selEl(id: string): HTMLSelectElement {
  return document.getElementById(id) as HTMLSelectElement;
}

export function inpEl(id: string): HTMLInputElement {
  return document.getElementById(id) as HTMLInputElement;
}
