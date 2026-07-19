import test from 'node:test';
import assert from 'node:assert/strict';
import { clearFieldValidation, clearIndexedCollectionValidation, normalizeBackendValidation } from '../dist-tests/form-validation/form-validation.js';

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

test('clears indexed recipe line validation on structural removal without moving stale row messages', () => {
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
  const removedFirst = clearIndexedCollectionValidation(state, 'ingredients');
  assert.equal(removedFirst.fieldErrors['ingredients.0.amount_value'], undefined);
  assert.equal(removedFirst.fieldErrors['ingredients.1.amount_unit'], undefined);
  assert.deepEqual(removedFirst.fieldErrors.title, ['Заголовок']);
  assert.deepEqual(removedFirst.formErrors, ['Сводка']);
});

test('client recipe create fields map inline while status remains summary', () => {
  const labels = {
    client_id: 'Клиент',
    source_recipe_version_id: 'Исходная версия рецепта',
    title: 'Название индивидуального рецепта',
    target_batch_size_value: 'Размер партии',
    target_batch_size_unit: 'Единица размера партии',
    personalization_notes: 'Персонализация',
    allergy_notes: 'Аллергии',
    preference_notes: 'Предпочтения',
    contraindication_notes: 'Противопоказания',
    notes: 'Заметки',
  };
  const state = normalizeBackendValidation({ detail: [
    { field: 'client_id', message: 'Выберите клиента.' },
    { field: 'body.source_recipe_version_id', message: 'Выберите версию.' },
    { field: 'title', message: 'Укажите название.' },
    { field: 'status', message: 'Статус недопустим.' },
  ] }, labels);
  assert.deepEqual(state.fieldErrors.client_id, ['Клиент: Выберите клиента.']);
  assert.deepEqual(state.fieldErrors.source_recipe_version_id, ['Исходная версия рецепта: Выберите версию.']);
  assert.deepEqual(state.fieldErrors.title, ['Название индивидуального рецепта: Укажите название.']);
  assert.deepEqual(state.formErrors, ['Статус недопустим.']);
});

test('client recipe composition maps exact approved indexed fields and keeps aggregate or hidden id in summary', () => {
  const labels = {
    'ingredients.0.ingredient_id': 'Строка 1: компонент',
    'ingredients.0.position': 'Строка 1: позиция',
    'ingredients.0.phase': 'Строка 1: фаза',
    'ingredients.0.amount_value': 'Строка 1: количество',
    'ingredients.0.amount_unit': 'Строка 1: единица',
    'ingredients.0.personalization_note': 'Строка 1: индивидуальное изменение',
    'ingredients.0.notes': 'Строка 1: заметки',
    'ingredients.1.amount_value': 'Строка 2: количество',
  };
  const state = normalizeBackendValidation({ detail: [
    { loc: ['body', 'ingredients', 1, 'amount_value'], msg: 'Количество должно быть больше нуля.' },
    { field: 'ingredients.0.ingredient_id', message: 'Выберите компонент.' },
    { field: 'ingredients.0.id', message: 'Скрытая строка не принадлежит рецепту.' },
    { field: 'ingredients', message: 'Добавьте строку.' },
    { field: 'position', message: 'Позиции повторяются.' },
    { field: 'id', message: 'Строка повторяется.' },
    { field: 'ingredients.amount_value', message: 'Путь malformed.' },
    { field: 'ingredients.0.unknown', message: 'Неизвестное поле.' },
  ] }, labels);
  assert.deepEqual(state.fieldErrors['ingredients.1.amount_value'], ['Строка 2: количество: Количество должно быть больше нуля.']);
  assert.deepEqual(state.fieldErrors['ingredients.0.ingredient_id'], ['Строка 1: компонент: Выберите компонент.']);
  assert.equal(state.fieldErrors['ingredients.0.id'], undefined);
  assert.deepEqual(state.formErrors, ['Скрытая строка не принадлежит рецепту.', 'Добавьте строку.', 'Позиции повторяются.', 'Строка повторяется.', 'Путь malformed.', 'Неизвестное поле.']);
});

test('client recipe composition field and collection clearing preserves unrelated errors', () => {
  const state = {
    fieldErrors: {
      title: ['top'],
      'ingredients.0.ingredient_id': ['row 1'],
      'ingredients.1.amount_value': ['row 2 amount'],
      'ingredients.1.amount_unit': ['row 2 unit'],
    },
    formErrors: ['summary'],
  };
  const corrected = clearFieldValidation(state, 'ingredients.1.amount_value');
  assert.equal(corrected.fieldErrors['ingredients.1.amount_value'], undefined);
  assert.deepEqual(corrected.fieldErrors['ingredients.0.ingredient_id'], ['row 1']);
  assert.deepEqual(corrected.fieldErrors['ingredients.1.amount_unit'], ['row 2 unit']);
  assert.deepEqual(corrected.formErrors, ['summary']);
  const structural = clearIndexedCollectionValidation(state, 'ingredients');
  assert.deepEqual(structural.fieldErrors, { title: ['top'] });
  assert.deepEqual(structural.formErrors, ['summary']);
});

test('client wish visible fields map inline and protected fields remain summary', () => {
  const wishLabels = {
    title: 'Кратко о пожелании',
    description: 'Подробности',
    category: 'Категория',
    priority: 'Важность',
    client_recipe_id: 'Индивидуальный рецепт',
  };
  const state = normalizeBackendValidation({ detail: [
    { field: 'title', message: 'Укажите краткое пожелание.' },
    { field: 'body.description', message: 'Слишком длинное описание.' },
    { loc: ['body', 'category'], msg: 'Выберите категорию из списка.' },
    { field: 'priority', message: 'Выберите важность из списка.' },
    { field: 'body.client_recipe_id', message: 'Выбранный рецепт недоступен.' },
    { field: 'metadata.title', message: 'Вложенный заголовок не должен стать inline.' },
    { field: 'items.0.title', message: 'Строка списка не является полем формы.' },
    { field: 'client_id', message: 'Клиент не найден.' },
    { field: 'status', message: 'Статус нельзя менять при создании.' },
    { field: '__proto__.title', message: 'Небезопасный путь.' },
  ] }, wishLabels);
  assert.deepEqual(state.fieldErrors.title, ['Кратко о пожелании: Укажите краткое пожелание.']);
  assert.deepEqual(state.fieldErrors.description, ['Подробности: Слишком длинное описание.']);
  assert.deepEqual(state.fieldErrors.category, ['Категория: Выберите категорию из списка.']);
  assert.deepEqual(state.fieldErrors.priority, ['Важность: Выберите важность из списка.']);
  assert.deepEqual(state.fieldErrors.client_recipe_id, ['Индивидуальный рецепт: Выбранный рецепт недоступен.']);
  assert.deepEqual(state.formErrors, [
    'Вложенный заголовок не должен стать inline.',
    'Строка списка не является полем формы.',
    'Клиент не найден.',
    'Статус нельзя менять при создании.',
    'Небезопасный путь.',
  ]);
});

test('client feedback visible fields map inline and protected fields remain summary', () => {
  const labels = { feedback_type: 'Тип отзыва', sentiment: 'Настроение', rating: 'Оценка', text: 'Текст отзыва', follow_up_needed: 'Нужно учесть в следующий раз', follow_up_note: 'Что учесть', occurred_at: 'Дата отзыва', client_recipe_id: 'Индивидуальный рецепт' };
  const state = normalizeBackendValidation({ detail: { issues: [
    { field: 'text', message: 'Field required' },
    { loc: ['body', 'rating'], msg: 'Input should be 1-5' },
    { field: 'unknown', message: 'Unknown aggregate problem' },
    { field: 'client_id', message: 'Hidden client mismatch' },
  ] } }, labels);
  assert.ok(state.fieldErrors.text[0].includes('Текст отзыва'));
  assert.ok(state.fieldErrors.rating[0].includes('Оценка'));
  assert.ok(state.formErrors.includes('Unknown aggregate problem'));
  assert.ok(state.formErrors.includes('Hidden client mismatch'));
});

test('normalizes Order visible fields and keeps protected or nested paths in summary', async () => {
  const { normalizeBackendValidation } = await import('../dist-tests/form-validation/form-validation.js');
  const labels = { client_id: 'Клиент', source_type: 'Основа заказа', recipe_source: 'Основа заказа', recipe_version_id: 'Версия рецепта', client_recipe_id: 'Индивидуальная формула', product_name: 'Название продукта', target_batch_size_value: 'Размер партии', target_batch_size_unit: 'Единица партии', packaging_item_id: 'Тара', packaging_quantity: 'Количество тары', sale_price: 'Цена продажи', ordered_at: 'Дата заказа', planned_production_at: 'Плановая дата производства', notes: 'Заметки' };
  const payload = { detail: [
    { loc: ['body', 'client_id'], msg: 'нужно выбрать клиента' },
    { field: 'recipe_source', message: 'выберите основу' },
    { field: 'status', message: 'нельзя менять статус' },
    { loc: ['body', 'unknown', 'nested'], msg: '<b>не доверять HTML</b>' },
  ] };
  const state = normalizeBackendValidation(payload, labels);
  assert.equal(state.fieldErrors.client_id[0], 'Клиент: нужно выбрать клиента');
  assert.equal(state.fieldErrors.recipe_source[0], 'Основа заказа: выберите основу');
  assert.ok(state.formErrors.includes('нельзя менять статус'));
  assert.ok(state.formErrors.includes('<b>не доверять HTML</b>'));
});
