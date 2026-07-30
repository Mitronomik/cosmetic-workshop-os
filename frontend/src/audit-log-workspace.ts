/**
 * Route lifecycle, request ownership and state for the `Журнал действий` workspace.
 *
 * Durable contract: `docs/audit-log.md` § 10.
 *
 * The screen has five distinct reads — initial load, re-entry refresh, manual
 * refresh, filter change and `Показать ещё` — and they must not be able to
 * corrupt each other. Four rules cover every case:
 *
 * * **One owner at a time.** Each accepted read takes a token; a settled read
 *   whose token is no longer the owner is discarded. That is what stops an older
 *   filter's slow response from overwriting a newer filter's result, and what
 *   stops a request left behind by a previous visit from settling the new one.
 * * **The runtime owns the entry decision.** `enter()` decides by itself whether
 *   arriving at the route means a first load, a refresh of data already held, or
 *   nothing at all because an equivalent request is already running. The caller
 *   never has to know which.
 * * **Draft filters are not applied filters.** What the controls show and what
 *   produced the visible rows are separate values, and only an explicit apply or
 *   clear moves one into the other. `Обновить` therefore refreshes what the user
 *   is actually looking at, never a filter they typed but never applied.
 * * **A failure never destroys accepted data.** Refresh, filter and load-more
 *   failures keep the rows the user already has; only a failed *initial* load,
 *   which has nothing to retain, shows the retry screen.
 */

import {
  AUDIT_LOG_PAGE_SIZE,
  type AuditLogDateFieldErrors,
  type AuditLogFilterOptions,
  type AuditLogFilters,
  type AuditLogItemDto,
  type AuditLogValidationIssue,
  EMPTY_AUDIT_LOG_FILTERS,
  EMPTY_AUDIT_LOG_FILTER_OPTIONS,
  NO_AUDIT_LOG_FIELD_ERRORS,
  appendAuditLogPage,
  auditLogAllRowsLoaded,
  auditLogFiltersActive,
  auditLogFiltersEqual,
  auditLogListDtoIsValid,
  auditLogRequestPlan,
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

export type AuditLogFieldErrors = AuditLogDateFieldErrors;

export type AuditLogState = {
  status: 'idle' | 'loading' | 'ready' | 'error';
  activeKind: AuditLogReadKind | null;
  items: AuditLogItemDto[];
  total: number;
  filterOptions: AuditLogFilterOptions;
  /** What the controls currently show. Editing a control changes only this. */
  draftFilters: AuditLogFilters;
  /** The exact filters that produced the currently accepted list. */
  appliedFilters: AuditLogFilters;
  /** Whether a response has ever been accepted, which is what makes re-entry a refresh. */
  loaded: boolean;
  /** Whether the user is currently on the route. */
  onRoute: boolean;
  initialError: string;
  refreshError: string;
  loadMoreError: string;
  fieldErrors: AuditLogFieldErrors;
};

export type AuditLogStartResult =
  | { accepted: true; kind: AuditLogReadKind; url: string }
  | { accepted: false; reason: 'busy' | 'all-loaded' | 'filters-pending' | 'invalid-local-time' };

/**
 * A snapshot of everything the workspace can update without a full render.
 *
 * Recording a draft filter change must not replace the DOM — that would destroy
 * keyboard focus on the very control the user is using — so the pieces of the
 * screen that legitimately react to a draft edit are handed over as data and
 * applied in place instead.
 */
export type AuditLogFilterSync = {
  filtersDirty: boolean;
  fieldErrors: AuditLogFieldErrors;
  canLoadMore: boolean;
  canClearFilters: boolean;
};

export type AuditLogWorkspaceDependencies = {
  read: (url: string) => Promise<unknown>;
  ownsRoute: () => boolean;
  render: () => void;
  announce: (message: string, kind: 'polite' | 'assertive') => void;
  /** Apply a draft-filter change in place, without a full render. */
  syncFilters?: (sync: AuditLogFilterSync) => void;
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
    draftFilters: { ...EMPTY_AUDIT_LOG_FILTERS },
    appliedFilters: { ...EMPTY_AUDIT_LOG_FILTERS },
    loaded: false,
    onRoute: false,
    initialError: '',
    refreshError: '',
    loadMoreError: '',
    fieldErrors: { ...NO_AUDIT_LOG_FIELD_ERRORS },
  };
}

export class AuditLogWorkspaceRuntime {
  state: AuditLogState = emptyState();

  private token = 0;
  private owner: number | null = null;

  constructor(private readonly deps: AuditLogWorkspaceDependencies) {}

  /**
   * Arrive at the route and start whatever read that implies.
   *
   * With no accepted data this is an initial load; with data already held it is
   * a refresh of the *applied* filters, so returning from Orders after creating
   * one shows the new event without the user pressing `Обновить`. The rows stay
   * on screen throughout, and an entry that lands while an equivalent request is
   * already running does nothing rather than issuing a second one.
   */
  enter(): AuditLogStartResult {
    this.state.onRoute = true;
    if (this.owner !== null) return { accepted: false, reason: 'busy' };
    return this.start(this.state.loaded ? 'refresh' : 'initial');
  }

  /**
   * Leave the route, detaching any request still in flight.
   *
   * Ownership is dropped rather than the request cancelled, so the response can
   * still arrive but can no longer settle anything. Rows, draft filters and
   * applied filters are all preserved for the next visit.
   */
  leave() {
    this.state.onRoute = false;
    this.owner = null;
    this.state.activeKind = null;
  }

  /** Retry after a failed initial load — the same read, deliberately re-armed. */
  retry(): AuditLogStartResult {
    return this.start('initial');
  }

  /** Refresh the accepted list. Uses applied filters, never unapplied drafts. */
  refresh(): AuditLogStartResult {
    return this.start(this.state.loaded ? 'refresh' : 'initial');
  }

  /**
   * Record a control edit. Deliberately starts no request and does not render.
   *
   * The native control already shows its new value, so replacing the DOM here
   * would achieve nothing except moving keyboard focus off the control the user
   * is operating. Only the few parts of the screen that must react — the pending
   * hint, the load-more control, and a stale error on this field — are updated
   * in place.
   */
  setFilter<K extends keyof AuditLogFilters>(name: K, value: AuditLogFilters[K]) {
    this.state.draftFilters = { ...this.state.draftFilters, [name]: value };
    if (name === 'createdFrom' || name === 'createdBefore') {
      this.state.fieldErrors = { ...this.state.fieldErrors, [name]: '' };
    }
    this.deps.syncFilters?.(this.filterSync());
  }

  /** Apply the current controls as a brand-new authoritative request. */
  applyFilters(): AuditLogStartResult {
    return this.start('filter');
  }

  /** Clear every control and immediately request the unfiltered history. */
  clearFilters(): AuditLogStartResult {
    this.state.draftFilters = { ...EMPTY_AUDIT_LOG_FILTERS };
    this.state.fieldErrors = { ...NO_AUDIT_LOG_FIELD_ERRORS };
    return this.start('filter');
  }

  loadMore(): AuditLogStartResult {
    // Appending rows produced by the applied filters while the controls show
    // something else would present one list as the answer to two questions.
    if (this.filtersDirty()) return { accepted: false, reason: 'filters-pending' };
    if (auditLogAllRowsLoaded(this.state.items.length, this.state.total)) return { accepted: false, reason: 'all-loaded' };
    return this.start('load-more');
  }

  /** Whether the controls have moved away from what produced the visible rows. */
  filtersDirty(): boolean {
    return !auditLogFiltersEqual(this.state.draftFilters, this.state.appliedFilters);
  }

  filterSync(): AuditLogFilterSync {
    const dirty = this.filtersDirty();
    const idle = this.state.activeKind === null;
    return {
      filtersDirty: dirty,
      fieldErrors: this.state.fieldErrors,
      canLoadMore:
        !dirty &&
        idle &&
        this.state.items.length > 0 &&
        !auditLogAllRowsLoaded(this.state.items.length, this.state.total),
      canClearFilters:
        idle &&
        (auditLogFiltersActive(this.state.draftFilters) || auditLogFiltersActive(this.state.appliedFilters)),
    };
  }

  private start(kind: AuditLogReadKind): AuditLogStartResult {
    // A filter change supersedes anything in flight; every other kind waits, so
    // a double click on Обновить or Показать ещё cannot issue a second request.
    if (this.owner !== null && kind !== 'filter') return { accepted: false, reason: 'busy' };

    // `docs/audit-log.md` § 10 request matrix: only refresh and load more read
    // the applied filters; everything the user triggered explicitly uses the
    // drafts they are looking at.
    const usesApplied = kind === 'refresh' || kind === 'load-more';
    const filters = usesApplied ? { ...this.state.appliedFilters } : { ...this.state.draftFilters };
    const offset = kind === 'load-more' ? this.state.items.length : 0;

    const plan = auditLogRequestPlan(filters, { limit: AUDIT_LOG_PAGE_SIZE, offset });
    if (!plan.ok) {
      // A locally impossible date never becomes a request. Rows, applied filters
      // and the user's drafts all stay exactly as they were.
      this.state.fieldErrors = plan.fieldErrors;
      const message = plan.fieldErrors.createdBefore || plan.fieldErrors.createdFrom;
      this.present({ message, tone: 'assertive' });
      return { accepted: false, reason: 'invalid-local-time' };
    }

    this.token += 1;
    const owner = this.token;
    this.owner = owner;
    this.state.activeKind = kind;
    if (kind === 'initial') {
      this.state.status = 'loading';
      this.state.initialError = '';
    }
    if (kind !== 'load-more') this.state.fieldErrors = { ...NO_AUDIT_LOG_FIELD_ERRORS };
    if (kind === 'refresh' || kind === 'filter') this.state.refreshError = '';
    if (kind === 'load-more') this.state.loadMoreError = '';
    this.deps.render();

    let request: Promise<unknown>;
    try {
      request = this.deps.read(plan.url);
    } catch (error) {
      request = Promise.reject(error);
    }
    request.then(
      (payload) => this.settleSuccess(owner, kind, filters, payload),
      (error) => this.settleFailure(owner, kind, error),
    );
    return { accepted: true, kind, url: plan.url };
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
    // Applied filters become exactly the snapshot this response answers, so the
    // dirty comparison is against what the user can actually see.
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
      // all keep the rows and the applied filters the user has; only the inline
      // notice changes, so `Обновить` still refreshes the previous result.
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
