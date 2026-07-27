export type SettingsTaxRateBindingCallbacks = {
  submitTaxRate: (event: Event) => void;
  updateTaxRateDraft: (event: Event) => void;
  cancelTaxRateEdit: () => void;
  requestTaxRateClear: () => void;
  confirmTaxRateClear: () => void;
  cancelTaxRateClear: () => void;
  refreshTaxRate: () => void;
};

type Root = { querySelectorAll: <T = Element>(selector: string) => Iterable<T> };
type Target = { addEventListener: (type: string, listener: (event: Event) => void) => void };

const bind = (root: Root, selector: string, type: string, listener: (event: Event) => void): number => {
  let count = 0;
  for (const target of root.querySelectorAll<Target>(selector)) {
    target.addEventListener(type, listener);
    count += 1;
  }
  return count;
};

export function bindSettingsTaxRateControls(root: Root, callbacks: SettingsTaxRateBindingCallbacks) {
  return {
    form: bind(root, '[data-form="settings-tax-rate"]', 'submit', callbacks.submitTaxRate),
    input: bind(root, '[data-tax-rate-input]', 'input', callbacks.updateTaxRateDraft),
    cancel: bind(root, '[data-tax-rate-cancel]', 'click', () => callbacks.cancelTaxRateEdit()),
    clear: bind(root, '[data-tax-rate-clear]', 'click', () => callbacks.requestTaxRateClear()),
    clearAccept: bind(root, '[data-tax-rate-clear-accept]', 'click', () => callbacks.confirmTaxRateClear()),
    clearCancel: bind(root, '[data-tax-rate-clear-cancel]', 'click', () => callbacks.cancelTaxRateClear()),
    refresh: bind(root, '[data-tax-rate-refresh]', 'click', () => callbacks.refreshTaxRate()),
  };
}
