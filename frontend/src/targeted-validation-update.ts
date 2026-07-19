import { type FormValidationState } from './form-validation.js';

export function applyValidationToClientForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="client"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'client', 'Проверьте форму клиента');
}

export function applyValidationToIngredientForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="ingredient"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'ingredient', 'Проверьте форму компонента');
}

export function applyValidationToIngredientLotForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="ingredient-lot"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'ingredient-lot', 'Проверьте форму партии');
}

export function applyValidationToStockMovementForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="stock-movement"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'stock-movement', 'Проверьте движение склада');
}

export function applyValidationToPackagingItemForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="packaging-item"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'packaging-item', 'Проверьте форму тары');
}

export function applyValidationToRecipeTemplateForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="recipe-template"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'recipe-template', 'Проверьте рецепт');
}

export function applyValidationToRecipeVersionForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="recipe-version"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'recipe-version', 'Проверьте версию рецепта');
}

export function applyValidationToClientRecipeCreateForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="client-recipe"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'client-recipe', 'Проверьте индивидуальный рецепт');
}

export function applyValidationToClientRecipeCompositionForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="client-recipe-composition"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'client-recipe-composition', 'Проверьте состав индивидуального рецепта');
}

export function applyValidationToClientWishForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="client-wish"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'client-wish', 'Проверьте пожелание клиента');
}

export function applyValidationToClientFeedbackForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="client-feedback"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'client-feedback', 'Проверьте отзыв клиента');
}

export function applyValidationToOrderForm(validation: FormValidationState): void {
  const form = document.querySelector<HTMLFormElement>('[data-form="order"]');
  if (!form) return;
  applyValidationToForm(form, validation, 'order', 'Проверьте заказ');
}

function applyValidationToForm(
  form: HTMLFormElement,
  validation: FormValidationState,
  prefix: string,
  summaryTitle: string,
): void {
  updateValidationSummary(form, validation, summaryTitle);
  applyFieldValidationState(form, validation, prefix);
}

function updateValidationSummary(
  form: HTMLFormElement,
  validation: FormValidationState,
  summaryTitle: string,
): void {
  const existing = form.querySelector(':scope > .form-error-summary');
  if (validation.formErrors.length === 0) {
    existing?.remove();
    return;
  }

  const summary = document.createElement('div');
  summary.className = 'form-error-summary';
  const strong = document.createElement('strong');
  strong.textContent = summaryTitle;
  summary.appendChild(strong);

  const ul = document.createElement('ul');
  for (const message of validation.formErrors) {
    const li = document.createElement('li');
    li.textContent = message;
    ul.appendChild(li);
  }
  summary.appendChild(ul);

  if (existing) {
    existing.replaceWith(summary);
  } else {
    form.insertBefore(summary, form.firstChild);
  }
}

function applyFieldValidationState(
  form: HTMLFormElement,
  validation: FormValidationState,
  prefix: string,
): void {
  const fieldNames = new Set<string>();
  form.querySelectorAll('[name]').forEach((el) => {
    const name = (el as HTMLElement).getAttribute('name');
    if (name) fieldNames.add(name);
  });

  for (const field of fieldNames) {
    const messages = validation.fieldErrors[field] ?? [];
    const errorId = `${prefix}-${field}-error`;
    const input = form.querySelector<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(
      `[name="${CSS.escape(field)}"]`,
    );

    if (messages.length > 0) {
      const errorDiv = document.createElement('div');
      errorDiv.className = 'field-error';
      errorDiv.id = errorId;
      for (const message of messages) {
        const p = document.createElement('p');
        p.textContent = message;
        errorDiv.appendChild(p);
      }

      const existing = document.getElementById(errorId);
      if (existing) {
        existing.replaceWith(errorDiv);
      } else {
        const formField = input?.closest('.form-field');
        if (formField) formField.appendChild(errorDiv);
      }

      if (input) {
        input.setAttribute('aria-invalid', 'true');
        input.setAttribute('aria-describedby', errorId);
      }
    } else {
      const errorDiv = document.getElementById(errorId);
      errorDiv?.remove();
      input?.removeAttribute('aria-invalid');
      if (input?.getAttribute('aria-describedby') === errorId) {
        input.removeAttribute('aria-describedby');
      }
    }
  }
}
