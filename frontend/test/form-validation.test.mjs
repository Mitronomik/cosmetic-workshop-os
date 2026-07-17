import test from 'node:test';
import assert from 'node:assert/strict';
import { clearFieldValidation, normalizeBackendValidation, reindexIndexedFieldValidation } from '../dist-tests/form-validation/form-validation.js';

const labels = { full_name: 'Имя клиента', email: 'Email', name: 'Название компонента', density_g_per_ml: 'Плотность' };

test('maps exact known field', () => {
  const state = normalizeBackendValidation({ detail: { field: 'email', message: 'Некорректный email' } }, labels);
  assert.deepEqual(state.formErrors, []);
  assert.deepEqual(state.fieldErrors.email, ['Email: Некорректный email']);
});

test('maps approved transport-prefixed field strings', () => {
  const state = normalizeBackendValidation({ detail: { field: 'body.email', message: 'Некорректный email' } }, labels);
  assert.deepEqual(state.fieldErrors.email, ['Email: Некорректный email']);
});

test('parses FastAPI detail array with known field and transport prefix', () => {
  const state = normalizeBackendValidation({ detail: [{ loc: ['body', 'email'], msg: 'Некорректный email', type: 'value_error' }] }, labels);
  assert.deepEqual(state.formErrors, []);
  assert.deepEqual(state.fieldErrors.email, ['Email: Некорректный email']);
});

test('parses project issues array with known field', () => {
  const state = normalizeBackendValidation({ issues: [{ field: 'full_name', message: 'Имя клиента обязательно.', code: 'required_field' }] }, labels);
  assert.deepEqual(state.fieldErrors.full_name, ['Имя клиента обязательно.']);
});

test('moves unknown field to form summary', () => {
  const state = normalizeBackendValidation({ detail: { field: 'unknown_field', message: 'Проверьте запись.' } }, labels);
  assert.deepEqual(state.fieldErrors, {});
  assert.deepEqual(state.formErrors, ['Проверьте запись.']);
});

test('moves unknown nested path ending in a known field to form summary', () => {
  const emailState = normalizeBackendValidation({ detail: { field: 'profile.email', message: 'Проверьте email.' } }, labels);
  const nameState = normalizeBackendValidation({ detail: { loc: ['metadata', 'name'], msg: 'Проверьте название.' } }, labels);
  assert.deepEqual(emailState.fieldErrors, {});
  assert.deepEqual(emailState.formErrors, ['Проверьте email.']);
  assert.deepEqual(nameState.fieldErrors, {});
  assert.deepEqual(nameState.formErrors, ['Проверьте название.']);
});

test('supports string and array field locations', () => {
  const stringState = normalizeBackendValidation({ detail: { field: 'query.email', message: 'Email неверный' } }, labels);
  const arrayState = normalizeBackendValidation({ detail: { loc: ['path', 'name'], msg: 'Название неверное' } }, labels);
  assert.deepEqual(stringState.fieldErrors.email, ['Email неверный']);
  assert.deepEqual(arrayState.fieldErrors.name, ['Название компонента: Название неверное']);
});

test('moves string detail to form summary', () => {
  const state = normalizeBackendValidation({ detail: 'Запрос не удалось сохранить.' }, labels);
  assert.deepEqual(state.formErrors, ['Запрос не удалось сохранить.']);
});

test('handles malformed null and HTML-like backend data safely', () => {
  assert.doesNotThrow(() => normalizeBackendValidation(null, labels));
  const state = normalizeBackendValidation({ detail: { field: 'name', message: '<img src=x onerror=alert(1)> Заполните название' } }, labels);
  assert.equal(state.fieldErrors.name[0], 'Название компонента: <img src=x onerror=alert(1)> Заполните название');
});

test('keeps multiple errors for one field', () => {
  const state = normalizeBackendValidation({ detail: [{ field: 'email', message: 'Первое' }, { loc: ['body', 'email'], msg: 'Второе' }] }, labels);
  assert.deepEqual(state.fieldErrors.email, ['Email: Первое', 'Email: Второе']);
});

test('does not throw for unexpected payload', () => {
  assert.doesNotThrow(() => normalizeBackendValidation({ detail: [{ loc: [1, null, 'email'], msg: 7 }, { x: Symbol('x') }] }, labels));
});

test('maps explicitly approved indexed recipe fields only and keeps non-control aggregate errors in summary', () => {
  const recipeLabels = { 'ingredients.0.amount_value': 'Строка 1: количество', 'ingredients.0.amount_unit': 'Строка 1: единица', title: 'Заголовок версии' };
  const state = normalizeBackendValidation({ detail: [
    { field: 'ingredients.0.amount_value', message: 'Укажите положительное количество.' },
    { loc: ['body', 'ingredients', 0, 'amount_unit'], msg: 'Единица неверная.' },
    { loc: ['body', 'title'], msg: 'Проверьте заголовок.' },
    { field: 'created_from_version_id', message: 'Исходная версия должна относиться к этому же рецепту.' },
    { field: 'ingredients', message: 'Добавьте хотя бы одну строку состава.' },
    { field: 'ingredients.0.unknown_field', message: 'Неизвестное вложенное поле.' },
  ] }, recipeLabels);
  assert.deepEqual(state.fieldErrors['ingredients.0.amount_value'], ['Строка 1: количество: Укажите положительное количество.']);
  assert.deepEqual(state.fieldErrors['ingredients.0.amount_unit'], ['Строка 1: единица: Единица неверная.']);
  assert.deepEqual(state.fieldErrors.title, ['Заголовок версии: Проверьте заголовок.']);
  assert.deepEqual(state.formErrors, ['Исходная версия должна относиться к этому же рецепту.', 'Добавьте хотя бы одну строку состава.', 'Неизвестное вложенное поле.']);
});

test('clears and reindexes indexed recipe line validation safely', () => {
  const state = {
    fieldErrors: {
      'ingredients.0.amount_value': ['Строка 1: количество'],
      'ingredients.1.amount_unit': ['Строка 2: единица'],
      title: ['Заголовок'],
    },
    formErrors: ['Сводка'],
  };
  const corrected = clearFieldValidation(state, 'ingredients.0.amount_value');
  assert.equal(corrected.fieldErrors['ingredients.0.amount_value'], undefined);
  assert.deepEqual(corrected.fieldErrors['ingredients.1.amount_unit'], ['Строка 2: единица']);
  const removedFirst = reindexIndexedFieldValidation(state, 'ingredients', 0);
  assert.equal(removedFirst.fieldErrors['ingredients.0.amount_value'], undefined);
  assert.deepEqual(removedFirst.fieldErrors['ingredients.0.amount_unit'], ['Строка 2: единица']);
  assert.deepEqual(removedFirst.fieldErrors.title, ['Заголовок']);
});
