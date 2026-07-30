/**
 * Targeted DOM updates and the render focus boundary for `Журнал действий`.
 *
 * Durable contract: `docs/audit-log.md` § 10.
 *
 * The application shell renders by replacing `root.innerHTML`. That is fine for
 * a navigation or a settled request, but it destroys and recreates every
 * control — so doing it while someone is operating a `<select>` with the
 * keyboard throws their focus back to `<body>` and restarts tab order. This
 * module exists so the workspace never has to choose between staying correct
 * and staying usable:
 *
 * * `syncAuditLogFilterState` applies the few things a *draft* filter edit
 *   changes — the pending hint, the load-more control, a stale error on the
 *   edited field — directly, with no render at all.
 * * `renderAuditLogWithFocus` wraps the renders that genuinely must happen,
 *   capturing the focused control by its stable `data-focus-key` and restoring
 *   it afterwards.
 *
 * Both are deliberately narrow: they touch the AuditLog workspace and nothing
 * else, and they never move focus that the user has already moved themselves.
 */

import type { AuditLogFilterSync } from './audit-log-workspace.js';

/** The workspace container, used as the predictable focus fallback. */
const WORKSPACE_KEY = 'audit-log-workspace';

/** The date controls, keyed by the `data-audit-log-field-error` value they own. */
const DATE_FILTER_ERRORS = [
  { filter: 'created-from', field: 'createdFrom' },
  { filter: 'created-before', field: 'createdBefore' },
] as const;

type FocusSnapshot = { key: string; selectionStart: number | null; selectionEnd: number | null } | null;

function workspace(root: ParentNode): Element | null {
  return root.querySelector('[data-page="audit-log"]');
}

/**
 * Apply a draft-filter change in place.
 *
 * Nothing here replaces an element, so whatever the user is focused on stays
 * focused and keeps its caret position.
 */
export function syncAuditLogFilterState(root: ParentNode, sync: AuditLogFilterSync): void {
  const page = workspace(root);
  if (!page) return;

  const hint = page.querySelector('[data-state="audit-log-filters-pending"]');
  if (hint) toggleHidden(hint, !sync.filtersDirty);

  const loadMore = page.querySelector<HTMLButtonElement>('[data-action="load-more-audit-log"]');
  if (loadMore) loadMore.disabled = !sync.canLoadMore;

  page
    .querySelectorAll<HTMLButtonElement>('[data-action="clear-audit-log-filters"]')
    .forEach((button) => {
      button.disabled = !sync.canClearFilters;
    });

  for (const { filter, field } of DATE_FILTER_ERRORS) {
    const message = sync.fieldErrors[field];
    const error = page.querySelector(`[data-audit-log-field-error="${filter}"]`);
    if (error) {
      error.textContent = message;
      toggleHidden(error, !message);
    }
    const control = page.querySelector(`[data-audit-log-filter="${filter}"]`);
    if (control) control.setAttribute('aria-invalid', message ? 'true' : 'false');
  }
}

function toggleHidden(element: Element, hidden: boolean): void {
  if (hidden) element.setAttribute('hidden', '');
  else element.removeAttribute('hidden');
}

/**
 * Run a render that must happen, preserving the user's place in the workspace.
 *
 * Focus is captured only when it currently sits inside the AuditLog workspace,
 * so a render triggered while the user is somewhere else never steals it. If the
 * captured control is gone or unusable afterwards, focus lands on the workspace
 * container rather than at an accidental document position.
 */
export function renderAuditLogWithFocus(root: ParentNode, render: () => void): void {
  const snapshot = captureFocus(root);
  render();
  if (snapshot) restoreFocus(root, snapshot);
}

function captureFocus(root: ParentNode): FocusSnapshot {
  const active = typeof document === 'undefined' ? null : document.activeElement;
  if (!active) return null;
  const page = workspace(root);
  if (!page || !page.contains(active)) return null;
  const key = active.getAttribute('data-focus-key');
  if (!key) return null;
  const text = active as HTMLInputElement;
  // Only text-like inputs expose a selection; reading it elsewhere throws.
  const selectable = text.tagName === 'INPUT' && typeof text.selectionStart === 'number';
  return {
    key,
    selectionStart: selectable ? text.selectionStart : null,
    selectionEnd: selectable ? text.selectionEnd : null,
  };
}

function restoreFocus(root: ParentNode, snapshot: NonNullable<FocusSnapshot>): void {
  const page = workspace(root);
  // The route is gone — the user navigated away mid-request. Restoring focus
  // into markup that no longer exists would be worse than doing nothing.
  if (!page) return;

  const target = focusable(page, snapshot.key) ?? focusable(page, WORKSPACE_KEY);
  if (!target) return;
  target.focus();
  if (snapshot.selectionStart === null) return;
  const input = target as HTMLInputElement;
  try {
    input.setSelectionRange(snapshot.selectionStart, snapshot.selectionEnd ?? snapshot.selectionStart);
  } catch {
    // A control whose type forbids a selection range keeps plain focus.
  }
}

/**
 * The focusable element carrying `key`, searching the container itself too.
 *
 * `querySelector` only ever matches descendants, so the workspace container —
 * which is both the search root and the fallback focus target — has to be
 * checked explicitly or the fallback could never fire.
 */
function focusable(page: Element, key: string): HTMLElement | null {
  const element = page.getAttribute('data-focus-key') === key
    ? (page as HTMLElement)
    : page.querySelector<HTMLElement>(`[data-focus-key="${key}"]`);
  if (!element) return null;
  if ((element as HTMLButtonElement).disabled) return null;
  return typeof element.focus === 'function' ? element : null;
}
