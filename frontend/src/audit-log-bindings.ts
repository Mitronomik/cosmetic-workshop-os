/**
 * DOM wiring for the `Журнал действий` workspace.
 *
 * Durable contract: `docs/audit-log.md` § 10.
 *
 * Controls are native `button`, `label`, `fieldset`, `input` and `select`
 * elements, so keyboard operation, focus order and accessible names come from
 * the platform rather than from custom handlers. This module only routes events
 * — every decision about whether a request may start belongs to the runtime.
 */

import type { AuditLogFilters } from './audit-log-contract.js';

export type AuditLogWorkspaceControls = {
  refresh: () => unknown;
  retry: () => unknown;
  applyFilters: () => unknown;
  clearFilters: () => unknown;
  loadMore: () => unknown;
  setFilter: (name: keyof AuditLogFilters, value: string) => unknown;
};

/** The `data-audit-log-filter` attribute values, mapped to filter state keys. */
const FILTER_NAMES: Record<string, keyof AuditLogFilters> = {
  'created-from': 'createdFrom',
  'created-before': 'createdBefore',
  action: 'action',
  'entity-type': 'entityType',
  'actor-type': 'actorType',
};

export function bindAuditLogWorkspaceControls(root: ParentNode, controls: AuditLogWorkspaceControls) {
  root.querySelector<HTMLButtonElement>('[data-action="refresh-audit-log"]')?.addEventListener('click', () => controls.refresh());
  root.querySelector<HTMLButtonElement>('[data-action="retry-audit-log"]')?.addEventListener('click', () => controls.retry());
  root.querySelector<HTMLButtonElement>('[data-action="load-more-audit-log"]')?.addEventListener('click', () => controls.loadMore());
  // Clear appears both in the filter bar and in the filtered-empty state, so
  // both instances are wired rather than only the first.
  root.querySelectorAll<HTMLButtonElement>('[data-action="clear-audit-log-filters"]').forEach((button) => {
    button.addEventListener('click', () => controls.clearFilters());
  });
  // Submitting the filter form is the keyboard path: Enter inside any control
  // applies the filters exactly as the button does.
  root.querySelector<HTMLFormElement>('[data-form="audit-log-filters"]')?.addEventListener('submit', (event) => {
    event.preventDefault();
    controls.applyFilters();
  });
  root.querySelectorAll<HTMLInputElement | HTMLSelectElement>('[data-audit-log-filter]').forEach((control) => {
    const name = FILTER_NAMES[control.dataset.auditLogFilter ?? ''];
    if (!name) return;
    control.addEventListener('change', () => controls.setFilter(name, control.value));
  });
}
