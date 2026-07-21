export type HelpArticleShape = { id: string; category: string; title: string; summary: string; body: string[]; relatedSections?: readonly string[]; warning?: string | null };
export type HelpState = { search: string; category: string; selectedArticleId: string };
export type PassiveNavigation = { section: string; mutates: false; ownsFeedback: false; clearsRouteAnnouncements: true };
export function normalizeHelpSearch(value: string): string { return value.toLocaleLowerCase('ru-RU').trim(); }
export function filterHelpArticles<TArticle extends HelpArticleShape>(articles: TArticle[], state: HelpState): TArticle[] {
  const q = normalizeHelpSearch(state.search);
  return articles.filter((article) => (!state.category || article.category === state.category) && (!q || normalizeHelpSearch([article.title, article.category, article.summary, article.body.join(' '), article.warning ?? ''].join(' ')).includes(q)));
}
export function selectHelpArticle<TState extends HelpState>(state: TState, id: string): TState { return { ...state, selectedArticleId: id }; }
export function resetHelpFilters(): HelpState { return { search: '', category: '', selectedArticleId: 'getting-started' }; }
export function helpRelatedNavigation(section: string): PassiveNavigation { return { section, mutates: false, ownsFeedback: false, clearsRouteAnnouncements: true }; }
