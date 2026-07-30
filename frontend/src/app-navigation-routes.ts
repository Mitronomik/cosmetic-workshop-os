/**
 * Path-to-section resolution for the application shell.
 *
 * Extracted from `frontend/src/main.ts` by `C3-I`, because `/settings/audit-log`
 * is the first **nested** route in the app: every other path is a single
 * segment, and route resolution now has to be exercised directly by tests rather
 * than only through a live browser.
 *
 * This is the route table only. Navigation groups, their labels, ordering and
 * rendering are untouched and still live in `main.ts`.
 */

/** Every canonical path the shell resolves, including the nested `C3-I` route. */
export const NAVIGATION_ROUTE_SECTIONS: Record<string, string> = {
  '/alerts': 'Алерты',
  '/backups': 'Резервные копии',
  '/exports': 'Экспорт',
  '/report-documents': 'Документы отчетов',
  '/imports': 'Импорт',
  '/demo-data': 'Демо-данные',
  '/inventory': 'Склад',
  '/ingredients': 'Компоненты',
  '/ingredient-lots': 'Партии',
  '/stock-movements': 'Движения сырья',
  '/recipes': 'Рецепты',
  '/clients': 'Клиенты',
  '/client-recipes': 'Индивидуальные рецепты',
  '/orders': 'Заказы',
  '/production': 'Производство',
  '/packaging-items': 'Тара',
  '/purchase-suggestions': 'Закупки',
  '/reports': 'Отчеты',
  '/settings': 'Настройки',
  '/settings/audit-log': 'Журнал действий',
  '/help': 'Помощь',
};

/** Legacy hash entry points kept working for links that predate real paths. */
export const PLACEHOLDER_HASH_SECTIONS: Record<string, string> = {
  '#purchases': 'Закупки',
  '#help': 'Помощь',
};

export const DEFAULT_SECTION = 'Главная';

/**
 * Drop a trailing slash so `/settings/audit-log/` resolves like its canonical
 * form. A nested path is far likelier to be typed or shared with one, and
 * resolving it to the dashboard instead would look like a broken link.
 */
function canonicalPath(pathname: string): string {
  if (pathname.length > 1 && pathname.endsWith('/')) return pathname.slice(0, -1);
  return pathname;
}

/**
 * The section that owns a location.
 *
 * Exact-match only. An unknown path falls back to the dashboard rather than
 * guessing from a path prefix — `/settings/audit-log` must never be mistaken for
 * `/settings`, and vice versa.
 */
export function sectionForLocation(pathname: string, hash = ''): string {
  return NAVIGATION_ROUTE_SECTIONS[canonicalPath(pathname)] ?? PLACEHOLDER_HASH_SECTIONS[hash] ?? DEFAULT_SECTION;
}
