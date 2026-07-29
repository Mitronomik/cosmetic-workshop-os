/**
 * Request ownership and state for the `Журнал действий` workspace.
 *
 * Durable contract: `docs/audit-log.md` § 10.
 *
 * The screen has four distinct reads — initial load, refresh, filter change and
 * `Показать ещё` — and they must not be able to corrupt each other. Two rules
 * cover every case:
 *
 * * **One owner at a time.** Each accepted read takes a token; a settled read
 *   whose token is no longer the owner is discarded. That is what stops an older
 *   filter's slow response from overwriting a newer filter's result.
 * * **A failure never destroys accepted data.** Refresh and load-more failures
 *   keep the rows the user already has and report the problem inline; only a
 *   failed *initial* load, which has nothing to retain, shows the retry screen.
 *
 * Refresh and load-more are additionally blocked while any read is in flight, so
 * a double click cannot produce two requests. A filter change is the one kind
 * that always supersedes — the user changed what they are asking for, and the
 * in-flight answer is already stale.
 */

import {
  AUDIT_LOG_PAGE_SIZE,
  type AuditLogFilterOptions,
  type AuditLogFilters,
  type AuditLogItemDto,
  type AuditLogValidationIssue,
  EMPTY_AUDIT_LOG_FILTERS,
  EMPTY_AUDIT_LOG_FILTER_OPTIONS,
  appendAuditLogPage,
  auditLogAllRowsLoaded,
  auditLogListDtoIsValid,
  auditLogRequestUrl,
  auditLogValidationIssue,
} from './audit-log-contract.js';
import {
  AUDIT_LOG_FILTER_FAILURE,
  AUDIT_LOG_INITIAL_FAILURE,
  AUDIT_LOG_INVALID_RESPONSE,
  AUDIT_LOG_LOAD_MORE_FAILURE,
  AUDIT_LOG_REFRESHED,
  AUDIT_LOG_REFRESH_FAILURE,
} from './audit-log-presentation.js';

export type AuditLogReadKind = 'initial' | 'refresh' | 'filter' | 'load-more';

export type AuditLogFieldErrors = { createdFrom: string; createdBefore: string };

export type AuditLogState = {
  status: 'idle' | 'loading' | 'ready' | 'error';
  activeKind: AuditLogReadKind | null;
  items: AuditLogItemDto[];
  total: number;
  filterOptions: AuditLogFilterOptions;
  /** What the controls currently show — may be ahead of what was requested. */
  filters: AuditLogFilters;
  /** The filters the accepted list was actually produced with. */
  appliedFilters: AuditLogFilters;
  /** Whether a response has ever been accepted, which is what enables retry-free refresh. */
  loaded: boolean;
  initialError: string;
  refreshError: string;
  loadMoreError: string;
  fieldErrors: AuditLogFieldErrors;
};

export type AuditLogStartResult =
  | { accepted: true; kind: AuditLogReadKind; url: string }
  | { accepted: false; reason: 'busy' | 'already-loaded' | 'all-loaded' };

export type AuditLogWorkspaceDependencies = {
  read: (url: string) => Promise<unknown>;
  ownsRoute: () => boolean;
  render: () => void;
  announce: (message: string, kind: 'polite' | 'assertive') => void;
};

/** The date controls a structured backend rejection can be attached to. */
const DATE_FIELDS: Record<string, keyof AuditLogFieldErrors> = {
  created_from: 'createdFrom',
  created_before: 'createdBefore',
};

function emptyState(): AuditLogState {
  return {
    status: 'idle',
    activeKind: null,
    items: [],
    total: 0,
    filterOptions: EMPTY_AUDIT_LOG_FILTER_OPTIONS,
    filters: { ...EMPTY_AUDIT_LOG_FILTERS },
    appliedFilters: { ...EMPTY_AUDIT_LOG_FILTERS },
    loaded: false,
    initialError: '',
    refreshError: '',
    loadMoreError: '',
    fieldErrors: { createdFrom: '', createdBefore: '' },
  };
}

export class AuditLogWorkspaceRuntime {
  state: AuditLogState = emptyState();

  private token = 0;
  private owner: number | null = null;

  constructor(private readonly deps: AuditLogWorkspaceDependencies) {}

  /** Enter the route. Leaving discards any in-flight read rather than letting it land later. */
  enter() {
    this.owner = null;
  }

  leave() {
    this.owner = null;
    this.state.activeKind = null;
  }

  /** The first read of a visit. A second call while data is present is a no-op. */
  load(): AuditLogStartResult {
    if (this.state.loaded) return { accepted: false, reason: 'already-loaded' };
    return this.start('initial');
  }

  /** Retry after a failed initial load — the same read, deliberately re-armed. */
  retry(): AuditLogStartResult {
    return this.start('initial');
  }

  refresh(): AuditLogStartResult {
    return this.start('refresh');
  }

  /** Update one control without requesting anything; the user applies it explicitly. */
  setFilter<K extends keyof AuditLogFilters>(name: K, value: AuditLogFilters[K]) {
    this.state.filters = { ...this.state.filters, [name]: value };
    this.deps.render();
  }

  /**
   * Apply the current controls as a brand-new authoritative request.
   *
   * Offset returns to `0` and the loaded page is dropped, because rows fetched
   * under the previous filters are not part of this answer.
   */
  applyFilters(): AuditLogStartResult {
    return this.start('filter');
  }

  clearFilters(): AuditLogStartResult {
    this.state.filters = { ...EMPTY_AUDIT_LOG_FILTERS };
    this.state.fieldErrors = { createdFrom: '', createdBefore: '' };
    return this.start('filter');
  }

  loadMore(): AuditLogStartResult {
    if (auditLogAllRowsLoaded(this.state.items.length, this.state.total)) return { accepted: false, reason: 'all-loaded' };
    return this.start('load-more');
  }

  private start(kind: AuditLogReadKind): AuditLogStartResult {
    // A filter change supersedes anything in flight; every other kind waits, so
    // a double click on Обновить or Показать ещё cannot issue a second request.
    if (this.owner !== null && kind !== 'filter') return { accepted: false, reason: 'busy' };

    const offset = kind === 'load-more' ? this.state.items.length : 0;
    const filters = kind === 'load-more' ? this.state.appliedFilters : { ...this.state.filters };
    const url = auditLogRequestUrl(filters, { limit: AUDIT_LOG_PAGE_SIZE, offset });

    this.token += 1;
    const owner = this.token;
    this.owner = owner;
    this.state.activeKind = kind;
    if (kind === 'initial') this.state.status = 'loading';
    if (kind !== 'load-more') this.state.fieldErrors = { createdFrom: '', createdBefore: '' };
    if (kind === 'refresh' || kind === 'filter') this.state.refreshError = '';
    if (kind === 'load-more') this.state.loadMoreError = '';
    if (kind === 'initial') this.state.initialError = '';
    this.deps.render();

    let request: Promise<unknown>;
    try {
      request = this.deps.read(url);
    } catch (error) {
      request = Promise.reject(error);
    }
    request.then(
      (payload) => this.settleSuccess(owner, kind, filters, payload),
      (error) => this.settleFailure(owner, kind, error),
    );
    return { accepted: true, kind, url };
  }

  private settleSuccess(owner: number, kind: AuditLogReadKind, filters: AuditLogFilters, payload: unknown) {
    if (owner !== this.owner) return;
    // A response that carries a field the contract excludes, or is missing one it
    // requires, takes the failure path — it is a damaged backend, not data.
    if (!auditLogListDtoIsValid(payload)) {
      this.settleFailure(owner, kind, new Error(AUDIT_LOG_INVALID_RESPONSE));
      return;
    }
    this.owner = null;
    this.state.activeKind = null;
    this.state.status = 'ready';
    this.state.loaded = true;
    this.state.total = payload.total;
    this.state.filterOptions = payload.filter_options;
    this.state.appliedFilters = filters;
    this.state.items = kind === 'load-more' ? appendAuditLogPage(this.state.items, payload.items) : payload.items;
    this.state.initialError = '';
    this.state.refreshError = '';
    this.state.loadMoreError = '';
    this.present(kind === 'refresh' ? { message: AUDIT_LOG_REFRESHED, tone: 'polite' } : null);
  }

  private settleFailure(owner: number, kind: AuditLogReadKind, error: unknown) {
    if (owner !== this.owner) return;
    this.owner = null;
    this.state.activeKind = null;

    const issue = auditLogValidationIssue(error);
    const fieldError = this.applyFieldError(issue);
    const message = issue && !fieldError ? issue.message : '';

    if (kind === 'initial' && !this.state.loaded) {
      this.state.status = 'error';
      this.state.initialError = message || AUDIT_LOG_INITIAL_FAILURE;
    } else if (kind === 'load-more') {
      this.state.loadMoreError = message || AUDIT_LOG_LOAD_MORE_FAILURE;
    } else {
      // Refresh, filter change, and a retried load over an already accepted list
      // all keep the rows the user has; only the inline notice changes.
      this.state.status = 'ready';
      this.state.refreshError = fieldError
        ? ''
        : message || (kind === 'filter' ? AUDIT_LOG_FILTER_FAILURE : AUDIT_LOG_REFRESH_FAILURE);
    }
    this.present({ message: fieldError || this.currentFailureMessage(kind), tone: 'assertive' });
  }

  /**
   * Attach a structured rejection to the control the user can act on.
   *
   * The date-range conflict names `created_before`, so it lands on the end-date
   * field rather than in a detached banner.
   */
  private applyFieldError(issue: AuditLogValidationIssue | null): string {
    if (!issue) return '';
    const target = DATE_FIELDS[issue.field];
    if (!target) return '';
    const text = issue.nextAction ? `${issue.message} ${issue.nextAction}` : issue.message;
    this.state.fieldErrors = { ...this.state.fieldErrors, [target]: text };
    return text;
  }

  private currentFailureMessage(kind: AuditLogReadKind): string {
    if (kind === 'load-more') return this.state.loadMoreError;
    return this.state.status === 'error' ? this.state.initialError : this.state.refreshError;
  }

  private present(announcement: { message: string; tone: 'polite' | 'assertive' } | null) {
    if (!this.deps.ownsRoute()) return;
    this.deps.render();
    if (announcement && announcement.message) this.deps.announce(announcement.message, announcement.tone);
  }
}
