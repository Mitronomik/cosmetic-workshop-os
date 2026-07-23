import type { LocalArtifactsReportsFeedbackLifecycle, LocalArtifactRouteKey, ReconciliationReason } from './local-artifacts-reports-feedback.js';

export type LocalArtifactReportPresentation = {
  route: LocalArtifactRouteKey;
  busy: boolean;
  readBusy: boolean;
  mutationBusy: boolean;
  canCreate: boolean;
  reconciliationRequired: boolean;
  reconciliationReason: ReconciliationReason;
  feedback: { neutral: string; success: string; warning: string; error: string };
  focusTargets: { retry: string; create: string; success: string; refresh: string; content: string };
};

const focusTargets: Record<LocalArtifactRouteKey, LocalArtifactReportPresentation['focusTargets']> = {
  backups: { retry: 'b3-backups-retry', create: 'b3-backups-create', success: 'b3-backups-last-created', refresh: 'b3-backups-refresh', content: 'b3-backups-content' },
  exports: { retry: 'b3-exports-retry', create: 'b3-exports-create', success: 'b3-exports-last-created', refresh: 'b3-exports-refresh', content: 'b3-exports-content' },
  reportDocuments: { retry: 'b3-report-documents-retry', create: 'b3-report-documents-create', success: 'b3-report-documents-last-created', refresh: 'b3-report-documents-refresh', content: 'b3-report-documents-content' },
  reports: { retry: 'b3-reports-retry', create: 'b3-reports-content', success: 'b3-reports-content', refresh: 'b3-reports-refresh', content: 'b3-reports-content' },
};

export function localArtifactReportPresentation<TRead, TCreated>(route: LocalArtifactRouteKey, lifecycle: LocalArtifactsReportsFeedbackLifecycle<TRead, TCreated>, createAvailable: boolean): LocalArtifactReportPresentation {
  const state = lifecycle.state;
  const mutationBusy = Boolean(state.mutation && !state.mutation.detached);
  const readBusy = Boolean(state.read);
  return {
    route,
    busy: readBusy || mutationBusy,
    readBusy,
    mutationBusy,
    canCreate: createAvailable && !readBusy && !mutationBusy && !state.reconciliationRequired,
    reconciliationRequired: state.reconciliationRequired,
    reconciliationReason: state.reconciliationReason,
    feedback: { neutral: state.feedback.neutral, success: state.feedback.success, warning: state.feedback.warning, error: state.feedback.error },
    focusTargets: focusTargets[route],
  };
}
