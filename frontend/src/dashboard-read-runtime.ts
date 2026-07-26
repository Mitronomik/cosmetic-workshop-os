export const DASHBOARD_READ_TIMEOUT_MS = 8_000;

export const DASHBOARD_READ_SOURCE_KEYS = [
  'orders',
  'clients',
  'alerts',
  'purchaseSuggestions',
  'productionBatches',
] as const;

export type DashboardReadSourceKey = (typeof DASHBOARD_READ_SOURCE_KEYS)[number];
export type DashboardReadResponses = Record<DashboardReadSourceKey, unknown>;

export type DashboardReadSource<TResponse> = {
  read: (signal: AbortSignal) => Promise<TResponse>;
  validate: (response: unknown) => response is TResponse;
};

export type DashboardReadSources<TResponses extends DashboardReadResponses> = {
  [TKey in DashboardReadSourceKey]: DashboardReadSource<TResponses[TKey]>;
};

export type DashboardReadScheduler = {
  setTimeout: (callback: () => void, delayMs: number) => unknown;
  clearTimeout: (handle: unknown) => void;
};

export type DashboardReadOutcome<TData> =
  | { generation: number; kind: 'success'; data: TData }
  | { generation: number; kind: 'timeout' | 'failure' | 'invalid-response' | 'route-detached' | 'superseded' };

type ActiveDashboardRead<TData> = {
  generation: number;
  controller: AbortController;
  timeoutHandle: unknown;
  settled: boolean;
  onOutcome: (outcome: DashboardReadOutcome<TData>) => void;
};

export type DashboardReadCoordinatorDependencies<TResponses extends DashboardReadResponses, TData> = {
  sources: DashboardReadSources<TResponses>;
  buildCandidate: (responses: TResponses) => TData;
  scheduler?: DashboardReadScheduler;
  timeoutMs?: number;
  createAbortController?: () => AbortController;
};

class InvalidDashboardReadResponse extends Error {}

const defaultScheduler: DashboardReadScheduler = {
  setTimeout: (callback, delayMs) => globalThis.setTimeout(callback, delayMs),
  clearTimeout: (handle) => globalThis.clearTimeout(handle as ReturnType<typeof globalThis.setTimeout>),
};

export class DashboardReadCoordinator<TResponses extends DashboardReadResponses, TData> {
  private active: ActiveDashboardRead<TData> | null = null;
  private readonly scheduler: DashboardReadScheduler;
  private readonly timeoutMs: number;
  private readonly createAbortController: () => AbortController;

  constructor(private readonly dependencies: DashboardReadCoordinatorDependencies<TResponses, TData>) {
    this.scheduler = dependencies.scheduler ?? defaultScheduler;
    this.timeoutMs = dependencies.timeoutMs ?? DASHBOARD_READ_TIMEOUT_MS;
    this.createAbortController = dependencies.createAbortController ?? (() => new AbortController());
  }

  start(generation: number, onOutcome: (outcome: DashboardReadOutcome<TData>) => void): { accepted: boolean; generation: number } {
    if (this.active) return { accepted: false, generation: this.active.generation };

    const controller = this.createAbortController();
    const operation: ActiveDashboardRead<TData> = {
      generation,
      controller,
      timeoutHandle: null,
      settled: false,
      onOutcome,
    };
    this.active = operation;
    operation.timeoutHandle = this.scheduler.setTimeout(
      () => this.settle(operation, { generation, kind: 'timeout' }, true),
      this.timeoutMs,
    );

    const reads = DASHBOARD_READ_SOURCE_KEYS.map((key) =>
      Promise.resolve()
        .then(() => this.dependencies.sources[key].read(controller.signal))
        .then((response) => {
          if (!this.dependencies.sources[key].validate(response)) throw new InvalidDashboardReadResponse();
          return [key, response] as const;
        }),
    );

    Promise.all(reads)
      .then((entries) => {
        const responses = Object.fromEntries(entries) as TResponses;
        const candidate = this.dependencies.buildCandidate(responses);
        this.settle(operation, { generation, kind: 'success', data: candidate }, false);
      })
      .catch((error: unknown) => {
        if (!this.isCurrent(operation)) return;
        this.settle(
          operation,
          { generation, kind: error instanceof InvalidDashboardReadResponse ? 'invalid-response' : 'failure' },
          true,
        );
      });

    return { accepted: true, generation };
  }

  cancelActive(kind: 'route-detached' | 'superseded'): boolean {
    const operation = this.active;
    if (!operation) return false;
    return this.settle(operation, { generation: operation.generation, kind }, true);
  }

  activeGeneration(): number | null {
    return this.active?.generation ?? null;
  }

  private isCurrent(operation: ActiveDashboardRead<TData>): boolean {
    return this.active === operation && !operation.settled;
  }

  private settle(operation: ActiveDashboardRead<TData>, outcome: DashboardReadOutcome<TData>, abort: boolean): boolean {
    if (!this.isCurrent(operation)) return false;
    operation.settled = true;
    this.scheduler.clearTimeout(operation.timeoutHandle);
    this.active = null;
    if (abort && !operation.controller.signal.aborted) operation.controller.abort();
    operation.onOutcome(outcome);
    return true;
  }
}
