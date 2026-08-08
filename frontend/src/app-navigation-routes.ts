/**
 * Path-to-section resolution for the application shell.
 *
 * Extracted from `frontend/src/main.ts` by `C3-I`, because `/settings/audit-log`
 * is the first **nested** route in the app: every other path is a single
 * segment, and route resolution now has to be exercised directly by tests rather
 * than only through a live browser.
 *
 * C4-II-A4 adds `/backups/restore` as another nested route. It remains owned by
 * the human-readable `Резервные копии` shell section while the A4 entry module
 * renders the bounded non-destructive Restore workspace.
 */

/** Every canonical path the shell resolves, including approved nested routes. */
export const NAVIGATION_ROUTE_SECTIONS: Record<string, string> = {
  '/alerts': 'Алерты',
  '/backups': 'Резервные копии',
  '/backups/restore': 'Резервные копии',
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

/** Drop a trailing slash so nested canonical routes also accept one trailing slash. */
function canonicalPath(pathname: string): string {
  if (pathname.length > 1 && pathname.endsWith('/')) return pathname.slice(0, -1);
  return pathname;
}

/** Resolve only exact approved routes; unknown paths fall back to the dashboard. */
export function sectionForLocation(pathname: string, hash = ''): string {
  return NAVIGATION_ROUTE_SECTIONS[canonicalPath(pathname)] ?? PLACEHOLDER_HASH_SECTIONS[hash] ?? DEFAULT_SECTION;
}
