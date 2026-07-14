import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeBackendValidation } from '../dist-tests/form-validation.js';

const labels = { full_name: 'Имя клиента', email: 'Email', name: 'Название компонента', density_g_per_ml: 'Плотность' };

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
  const state = normalizeBackendValidation({ detail: { field: 'body.internal_id', message: 'Проверьте запись.' } }, labels);
  assert.deepEqual(state.fieldErrors, {});
  assert.deepEqual(state.formErrors, ['Проверьте запись.']);
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
