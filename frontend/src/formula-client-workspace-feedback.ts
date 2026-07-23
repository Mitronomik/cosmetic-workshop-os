import { CoreWorkspaceFeedbackLifecycle, type WorkspaceRouteMessages } from './core-workspace-feedback.js';

export type FormulaClientRoute = 'recipes' | 'clients' | 'clientRecipes';
export type FormulaClientRead =
  | 'recipe-list'
  | 'recipe-references'
  | 'recipe-template-detail'
  | 'recipe-version-list'
  | 'recipe-version-detail'
  | 'recipe-calculation'
  | 'client-list'
  | 'client-related'
  | 'client-recipe-list'
  | 'client-recipe-references'
  | 'client-recipe-detail'
  | 'client-wishes'
  | 'client-feedback';
export type FormulaClientMutation =
  | 'recipe-template-create'
  | 'recipe-version-create'
  | 'recipe-category-create'
  | 'recipe-tag-create'
  | 'recipe-category-assign'
  | 'recipe-tags-assign'
  | 'client-create'
  | 'client-update'
  | 'client-deactivate'
  | 'client-recipe-create'
  | 'client-recipe-composition'
  | 'client-recipe-deactivate'
  | 'client-recipe-restore'
  | 'wish-create'
  | 'wish-status'
  | 'wish-archive'
  | 'feedback-create';

const messages = (subject: string): WorkspaceRouteMessages => ({
  loading: `Загружаем ${subject}…`,
  refreshing: `Обновляем ${subject}…`,
  refreshSuccess: `${subject[0].toUpperCase()}${subject.slice(1)} обновлены.`,
  initialError: `Не удалось загрузить ${subject}. Проверьте, что локальное приложение запущено, и попробуйте снова.`,
  refreshError: `Не удалось обновить ${subject}. Ранее загруженные данные оставлены на экране.`,
  mutationBusy: 'Сохраняем изменения…',
  mutationError: 'Не удалось сохранить изменения. Проверьте поля и попробуйте ещё раз.',
  mutationAmbiguous: 'Не удалось подтвердить результат сохранения. Перед повтором обновите данные: изменение могло сохраниться.',
  invalidResponse: 'Локальное приложение вернуло неполный ответ. Обновите данные перед повторной попыткой.',
  reconciliationFailed: 'Не удалось подтвердить результат. Обновите данные вручную перед повторным сохранением.',
});

export class FormulaClientWorkspaceFeedbackLifecycle extends CoreWorkspaceFeedbackLifecycle<
  FormulaClientRoute,
  FormulaClientRead,
  FormulaClientMutation
> {
  constructor() {
    super(
      {
        recipes: messages('рецепты'),
        clients: messages('клиентов'),
        clientRecipes: messages('индивидуальные рецепты'),
      },
      {
        recipes: { retry: 'core-recipes-retry', refresh: 'core-recipes-refresh', mutation: 'core-recipes-form', success: 'core-recipes-content' },
        clients: { retry: 'core-clients-retry', refresh: 'core-clients-refresh', mutation: 'core-clients-form', success: 'core-clients-content' },
        clientRecipes: { retry: 'core-client-recipes-retry', refresh: 'core-client-recipes-refresh', mutation: 'core-client-recipes-form', success: 'core-client-recipes-content' },
      },
    );
  }
}

export const FORMULA_CLIENT_UNSUPPORTED_OPERATIONS = Object.freeze([
  'recipe-template-update',
  'recipe-version-update',
  'recipe-version-delete',
  'recipe-version-archive',
  'recipe-ingredient-row-crud',
  'client-recipe-calculation',
  'client-feedback-update',
  'client-feedback-archive',
  'client-feedback-delete',
] as const);

export function isEntityDto(value: unknown): value is { id: number } {
  return Boolean(value && typeof value === 'object' && Number.isInteger(Number((value as { id?: unknown }).id)) && Number((value as { id?: unknown }).id) > 0);
}

export function isRecipeVersionDetailDto(value: unknown): boolean {
  if (!value || typeof value !== 'object') return false;
  const detail = value as { version?: unknown; ingredients?: unknown };
  return isEntityDto(detail.version) && Array.isArray(detail.ingredients);
}

export function containsSensitiveClientText(message: string, submittedText: string[]): boolean {
  const normalized = message.toLocaleLowerCase('ru-RU');
  return submittedText.some((text) => text.trim().length > 0 && normalized.includes(text.trim().toLocaleLowerCase('ru-RU')));
}
