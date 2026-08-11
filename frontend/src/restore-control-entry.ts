import { RESTORE_ROUTE, type RestoreBootstrapCapture, captureRestoreBootstrap } from './restore-control-contract.js';
import { RestoreControlRuntime } from './restore-control-runtime.js';
import { restoreControlMarkup, restoreEntryButtonMarkup } from './restore-control-presentation.js';

let bootstrapCapture: RestoreBootstrapCapture = captureRestoreBootstrap(window.location, window.history);
const runtime = new RestoreControlRuntime({
  fetch: (input, init) => window.fetch(input, init),
  sessionStorage: window.sessionStorage,
  history: window.history,
  crypto: window.crypto,
  setInterval: (handler, milliseconds) => window.setInterval(handler, milliseconds),
  clearInterval: (handle) => window.clearInterval(handle),
  setTimeout: (handler, milliseconds) => window.setTimeout(handler, milliseconds),
  clearTimeout: (handle) => window.clearTimeout(handle),
});

let syncQueued = false;
let currentView = runtime.view;
let confirmationGeneration: number | null = null;
let focusConfirmationTriggerAfterRender = false;

function confirmationMatchesCurrentView(): boolean {
  return confirmationGeneration !== null
    && currentView.availability === 'ready'
    && currentView.hasSession
    && currentView.protocolSafe
    && currentView.pending === null
    && currentView.snapshot?.state === 'accepted'
    && currentView.snapshot.generation === confirmationGeneration;
}

function queueDomSync(): void {
  if (syncQueued) return;
  syncQueued = true;
  queueMicrotask(() => {
    syncQueued = false;
    syncDom();
  });
}

function syncDom(): void {
  runtime.syncReplayToHistory();
  if (window.location.pathname === RESTORE_ROUTE) {
    const content = document.querySelector<HTMLElement>('.content');
    const page = content?.querySelector<HTMLElement>('.page-grid');
    if (!content || !page) return;
    const confirmationOpen = confirmationMatchesCurrentView();
    const signature = JSON.stringify({ view: currentView, confirmationOpen });
    if (!page.hasAttribute('data-restore-control-page') || page.dataset.restoreRenderKey !== signature) {
      const restoreFocusOwned = page.contains(document.activeElement);
      page.outerHTML = restoreControlMarkup(currentView, { confirmationOpen });
      const rendered = content.querySelector<HTMLElement>('[data-restore-control-page]');
      if (rendered) {
        rendered.dataset.restoreRenderKey = signature;
        if (restoreFocusOwned && !confirmationOpen && !focusConfirmationTriggerAfterRender) rendered.focus();
      }
    }
    const heading = content.querySelector<HTMLElement>('.topbar h1');
    if (heading && heading.textContent !== 'Восстановление') heading.textContent = 'Восстановление';

    if (confirmationOpen) {
      const dialog = content.querySelector<HTMLDialogElement>('dialog[data-restore-confirmation]');
      if (dialog && !dialog.open) {
        dialog.showModal();
        dialog.querySelector<HTMLElement>('[data-restore-action="confirm-dismiss"]')?.focus();
      }
    } else if (focusConfirmationTriggerAfterRender) {
      focusConfirmationTriggerAfterRender = false;
      content.querySelector<HTMLElement>('[data-restore-action="confirm-open"]')?.focus();
    }
    return;
  }

  confirmationGeneration = null;
  focusConfirmationTriggerAfterRender = false;

  if (window.location.pathname === '/backups') {
    const actions = document.querySelector<HTMLElement>('.backup-page .dashboard-hero .actions');
    if (actions && !actions.querySelector('[data-restore-action="open"]')) {
      actions.insertAdjacentHTML('beforeend', restoreEntryButtonMarkup());
    }
  }
}

function navigate(path: string): void {
  confirmationGeneration = null;
  focusConfirmationTriggerAfterRender = false;
  runtime.syncReplayToHistory();
  const state = window.history.state;
  window.history.pushState(state, '', path);
  window.dispatchEvent(new PopStateEvent('popstate', { state }));
  window.setTimeout(() => {
    document.querySelector<HTMLElement>('[data-restore-focus]')?.focus();
  }, 0);
}

function openConfirmation(): void {
  const snapshot = currentView.snapshot;
  if (
    currentView.availability !== 'ready'
    || !currentView.hasSession
    || !currentView.protocolSafe
    || currentView.pending
    || snapshot?.state !== 'accepted'
    || !Number.isInteger(snapshot.generation)
    || snapshot.generation < 1
  ) return;
  confirmationGeneration = snapshot.generation;
  focusConfirmationTriggerAfterRender = false;
  queueDomSync();
}

function dismissConfirmation(returnFocus = true): void {
  if (confirmationGeneration === null) return;
  confirmationGeneration = null;
  focusConfirmationTriggerAfterRender = returnFocus;
  queueDomSync();
}

function executeConfirmedRestore(): void {
  if (!confirmationMatchesCurrentView()) {
    dismissConfirmation(false);
    return;
  }
  confirmationGeneration = null;
  focusConfirmationTriggerAfterRender = false;
  queueDomSync();
  void runtime.execute();
}

document.addEventListener('click', (event) => {
  const target = event.target instanceof Element ? event.target.closest<HTMLElement>('[data-restore-action]') : null;
  if (!target) return;
  const action = target.dataset.restoreAction;
  if (!action) return;
  event.preventDefault();
  if (action === 'open') { navigate(RESTORE_ROUTE); return; }
  if (action === 'back') { navigate('/backups'); return; }
  if (action === 'select') { void runtime.select(); return; }
  if (action === 'cancel') { void runtime.cancel(); return; }
  if (action === 'retry') { void runtime.retryPending(); return; }
  if (action === 'refresh') { void runtime.refresh(); return; }
  if (action === 'confirm-open') { openConfirmation(); return; }
  if (action === 'confirm-dismiss') { dismissConfirmation(); return; }
  if (action === 'confirm-execute') { executeConfirmedRestore(); }
});

document.addEventListener('cancel', (event) => {
  const dialog = event.target instanceof HTMLDialogElement && event.target.matches('[data-restore-confirmation]') ? event.target : null;
  if (!dialog) return;
  event.preventDefault();
  dismissConfirmation();
}, { capture: true });

window.addEventListener('popstate', () => {
  confirmationGeneration = null;
  focusConfirmationTriggerAfterRender = false;
  queueDomSync();
});
window.addEventListener('pageshow', queueDomSync);
window.addEventListener('beforeunload', () => runtime.dispose(), { once: true });

const observer = new MutationObserver(queueDomSync);
observer.observe(document.documentElement, { childList: true, subtree: true });

runtime.subscribe((view) => {
  currentView = view;
  if (confirmationGeneration !== null && !confirmationMatchesCurrentView()) {
    confirmationGeneration = null;
    focusConfirmationTriggerAfterRender = false;
  }
  queueDomSync();
});

const startup = runtime.start(bootstrapCapture);
bootstrapCapture = { kind: 'none' };
void startup;
