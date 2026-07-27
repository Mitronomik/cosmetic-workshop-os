import type { TaxRatePayload } from './settings-tax-contract.js';
import {
  SettingsTaxRateFeedbackLifecycle,
  type TaxRateMutationOwner,
  type TaxRateReadKind,
  type TaxRateSettled,
} from './settings-tax-feedback.js';
import { settingsTaxRatePresentation, type TaxRatePresentation } from './settings-tax-presentation.js';

export type SettingsTaxRateRuntimeDependencies = {
  lifecycle?: SettingsTaxRateFeedbackLifecycle;
  read: () => Promise<unknown>;
  save: (payload: TaxRatePayload) => Promise<unknown>;
  ownsRoute: () => boolean;
  render: () => void;
  announce: (message: string, kind: 'polite' | 'assertive') => void;
  fieldErrorFromFailure?: (error: unknown) => string;
};

/** Owns tax-setting request lifecycle so stale callbacks never present or mutate. */
export class SettingsTaxRateRuntime {
  readonly lifecycle: SettingsTaxRateFeedbackLifecycle;

  constructor(private readonly deps: SettingsTaxRateRuntimeDependencies) {
    this.lifecycle = deps.lifecycle ?? new SettingsTaxRateFeedbackLifecycle();
  }

  enter() {
    this.lifecycle.enterRoute();
  }

  leave() {
    this.lifecycle.leaveRoute();
  }

  load(kind: TaxRateReadKind = 'initial') {
    if (kind === 'initial' && this.lifecycle.state.confirmed !== null) return null;
    return this.startRead(kind);
  }

  refresh() {
    return this.startRead('refresh');
  }

  updateDraft(text: string) {
    this.lifecycle.setDraft(text);
    this.deps.render();
  }

  cancelEdit() {
    this.present(this.lifecycle.cancelEdit());
  }

  requestClear() {
    const started = this.lifecycle.requestClearConfirmation();
    if (started.accepted) this.deps.render();
    return started;
  }

  cancelClear() {
    this.lifecycle.cancelClearConfirmation();
    this.deps.render();
  }

  submit() {
    const started = this.lifecycle.startSave();
    if (!started.accepted) {
      if (started.reason === 'invalid-input') this.present({ accepted: true, announcement: 'assertive', message: this.lifecycle.state.fieldError });
      return started;
    }
    this.runMutation(started.owner, { tax_rate_percent: started.payload ?? null });
    return started;
  }

  confirmClear() {
    const started = this.lifecycle.startClear();
    if (!started.accepted) return started;
    this.runMutation(started.owner, { tax_rate_percent: null });
    return started;
  }

  presentation(): TaxRatePresentation {
    return settingsTaxRatePresentation(this.lifecycle.state);
  }

  private startRead(kind: TaxRateReadKind) {
    const started = this.lifecycle.startRead(kind);
    if (!started.accepted) return started;
    this.deps.render();
    this.deps.read().then(
      (value) => this.present(this.lifecycle.finishReadSuccess(started.owner, value)),
      () => this.present(this.lifecycle.finishReadFailure(started.owner)),
    );
    return started;
  }

  private runMutation(owner: TaxRateMutationOwner, payload: TaxRatePayload) {
    this.deps.render();
    let request: Promise<unknown>;
    try {
      request = this.deps.save(payload);
    } catch (error) {
      request = Promise.reject(error);
    }
    request.then(
      (value) => {
        const settled = this.lifecycle.finishMutationSuccess(owner, value);
        this.present(settled);
        if (settled.knownSuccess) this.startRead('mutation-refresh');
      },
      (error) => this.present(this.lifecycle.finishMutationFailure(owner, this.deps.fieldErrorFromFailure?.(error) ?? '')),
    );
  }

  private present(settled: TaxRateSettled) {
    if (!settled.accepted || !this.deps.ownsRoute()) return;
    this.deps.render();
    if (settled.announcement !== 'none' && settled.message) this.deps.announce(settled.message, settled.announcement);
  }
}
