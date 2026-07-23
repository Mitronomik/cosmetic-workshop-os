import {
  FormulaClientWorkspaceFeedbackLifecycle,
  type FormulaClientMutation,
  type FormulaClientRead,
  type FormulaClientRoute,
} from './formula-client-workspace-feedback.js';
import type { WorkspaceFinishResult, WorkspaceReadKind, WorkspaceStartReason } from './core-workspace-feedback.js';

export type FormulaClientRuntimeDependencies = {
  lifecycle?: FormulaClientWorkspaceFeedbackLifecycle;
  ownsRoute: (route: FormulaClientRoute) => boolean;
  render: () => void;
  announce: (message: string, kind: 'polite' | 'assertive') => void;
  focus: (key: string) => void;
};

export class FormulaClientWorkspaceRuntime {
  readonly lifecycle: FormulaClientWorkspaceFeedbackLifecycle;

  constructor(private readonly deps: FormulaClientRuntimeDependencies) {
    this.lifecycle = deps.lifecycle ?? new FormulaClientWorkspaceFeedbackLifecycle();
  }

  read<T>(options: {
    route: FormulaClientRoute;
    operation: FormulaClientRead;
    kind: WorkspaceReadKind;
    contextKey?: string;
    ownsContext?: () => boolean;
    request: () => Promise<T>;
    validate?: (value: T) => boolean;
    apply: (value: T) => void;
    failed?: (retainedSnapshot: boolean) => void;
    rejected?: (reason: WorkspaceStartReason) => void;
  }) {
    const started = this.lifecycle.startRead(options.route, options.operation, options.kind, options.contextKey);
    if (!started.accepted) {
      options.rejected?.(started.reason);
      return started;
    }
    this.deps.render();
    options.request().then((value) => {
      if (options.ownsContext && !options.ownsContext()) {
        this.lifecycle.discardRead(started.owner);
        return;
      }
      const result = this.lifecycle.finishReadSuccess(started.owner, value, options.validate);
      if (result.canApply && this.deps.ownsRoute(options.route)) options.apply(value);
      if (result.accepted && this.deps.ownsRoute(options.route)) {
        this.deps.render();
        this.complete(result);
      }
    }).catch(() => {
      if (options.ownsContext && !options.ownsContext()) {
        this.lifecycle.discardRead(started.owner);
        return;
      }
      const result = this.lifecycle.finishReadFailure(started.owner);
      if (result.accepted && this.deps.ownsRoute(options.route)) {
        options.failed?.(this.lifecycle.hasSnapshot(options.route));
        this.deps.render();
        this.complete(result);
      }
    });
    return started;
  }

  mutate<T>(options: {
    route: FormulaClientRoute;
    operation: FormulaClientMutation;
    contextKey?: string;
    ownsContext?: () => boolean;
    request: () => Promise<T>;
    validate: (value: T) => boolean;
    successMessage: string;
    apply: (value: T) => void;
    failed?: (error: unknown, ambiguous: boolean) => void;
    rejected?: (reason: WorkspaceStartReason) => void;
  }) {
    const started = this.lifecycle.startMutation(options.route, options.operation, options.contextKey);
    if (!started.accepted) {
      options.rejected?.(started.reason);
      return started;
    }
    this.deps.render();
    options.request().then((value) => {
      if (options.ownsContext && !options.ownsContext()) {
        this.lifecycle.settleMutationObsolete(started.owner);
        return;
      }
      const result = this.lifecycle.finishMutationSuccess(started.owner, value, options.validate, options.successMessage);
      if (result.knownSuccess && result.canApply && this.deps.ownsRoute(options.route)) options.apply(value);
      if (result.accepted && !result.knownSuccess && result.reconciliationRequired && this.deps.ownsRoute(options.route)) {
        options.failed?.(new Error('invalid-authoritative-mutation-response'), true);
      }
      if (result.accepted && this.deps.ownsRoute(options.route)) {
        this.deps.render();
        this.complete(result);
      }
    }).catch((error) => {
      if (options.ownsContext && !options.ownsContext()) {
        this.lifecycle.settleMutationObsolete(started.owner);
        return;
      }
      const result = this.lifecycle.finishMutationFailure(started.owner, error);
      if (result.accepted && this.deps.ownsRoute(options.route)) {
        options.failed?.(error, result.reconciliationRequired);
        this.deps.render();
        this.complete(result);
      }
    });
    return started;
  }

  private complete(result: WorkspaceFinishResult): void {
    if (this.lifecycle.shouldAnnounce(result) && result.announcement !== 'none') {
      this.deps.announce(result.message, result.announcement);
    }
    if (result.focusKey) this.deps.focus(result.focusKey);
  }
}
