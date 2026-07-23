export type LocalArtifactsReportsBindingCallbacks = {
  reloadBackups: () => void;
  submitBackup: (event?: Event) => void;
  reloadExports: () => void;
  submitExport: (event?: Event) => void;
  reloadReportDocuments: () => void;
  submitReportDocument: (event: Event) => void;
  updateReportDocumentReason: (value: string) => void;
  navigateReportDocumentsRelated: (section: string | undefined) => void;
  reloadReports: () => void;
  selectReportTab: (tab: string | undefined) => void;
  navigateReportRelated: (section: string | undefined) => void;
};

type BindableRoot = {
  querySelectorAll: <T = Element>(selector: string) => Iterable<T>;
  querySelector: <T = Element>(selector: string) => T | null;
};
type ListenerTarget = { addEventListener: (type: string, listener: (event: Event) => void) => void };
type DataTarget = ListenerTarget & { dataset?: Record<string, string | undefined>; value?: string };

const bindAll = <T extends ListenerTarget>(root: BindableRoot, selector: string, type: string, listener: (event: Event, element: T) => void) => {
  let count = 0;
  for (const element of root.querySelectorAll<T>(selector)) {
    element.addEventListener(type, (event) => listener(event, element));
    count += 1;
  }
  return count;
};
const bindOne = <T extends ListenerTarget>(root: BindableRoot, selector: string, type: string, listener: (event: Event, element: T) => void) => {
  const element = root.querySelector<T>(selector);
  if (!element) return 0;
  element.addEventListener(type, (event) => listener(event, element));
  return 1;
};

export function bindLocalArtifactsReportsControls(root: BindableRoot, callbacks: LocalArtifactsReportsBindingCallbacks) {
  return {
    backupReload: bindAll(root, '[data-action="reload-backups"]', 'click', () => callbacks.reloadBackups()),
    backupForm: bindOne(root, '[data-form="backup-create"]', 'submit', (event) => callbacks.submitBackup(event)),
    backupCreate: bindOne(root, '[data-action="create-backup"]', 'click', (event) => callbacks.submitBackup(event)),
    exportReload: bindAll(root, '[data-action="reload-exports"]', 'click', () => callbacks.reloadExports()),
    exportForm: bindOne(root, '[data-form="export-create"]', 'submit', (event) => callbacks.submitExport(event)),
    exportCreate: bindOne(root, '[data-action="create-export"]', 'click', (event) => callbacks.submitExport(event)),
    reportDocumentsReload: bindAll(root, '[data-action="reload-report-documents"]', 'click', () => callbacks.reloadReportDocuments()),
    reportDocumentsForm: bindOne(root, '[data-form="report-document-create"]', 'submit', (event) => callbacks.submitReportDocument(event)),
    reportDocumentReason: bindOne<DataTarget>(root, '[data-action="report-document-reason"]', 'input', (_event, element) => callbacks.updateReportDocumentReason((element.value ?? '').slice(0, 80))),
    reportDocumentsRelated: bindAll<DataTarget>(root, '[data-action="navigate-report-documents-related"]', 'click', (_event, element) => callbacks.navigateReportDocumentsRelated(element.dataset?.section)),
    reportsReload: bindAll(root, '[data-action="reload-reports"]', 'click', () => callbacks.reloadReports()),
    reportsTabs: bindAll<DataTarget>(root, '[data-action="select-report-tab"]', 'click', (_event, element) => callbacks.selectReportTab(element.dataset?.report)),
    reportsRelated: bindAll<DataTarget>(root, '[data-action="navigate-report-related"]', 'click', (_event, element) => callbacks.navigateReportRelated(element.dataset?.section)),
  };
}
