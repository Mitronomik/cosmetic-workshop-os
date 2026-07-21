export type HelpArticle = { id: string; category: string; title: string; summary: string; body: string[]; relatedSections?: string[] };
export type HelpState = { search: string; category: string; selectedArticleId: string };
export function normalizeHelpSearch(value: string): string { return value.toLocaleLowerCase('ru-RU').trim(); }
export function filterHelpArticles(articles: HelpArticle[], state: HelpState): HelpArticle[] {
  const q = normalizeHelpSearch(state.search);
  return articles.filter((article) => (!state.category || article.category === state.category) && (!q || normalizeHelpSearch([article.title, article.category, article.summary, article.body.join(' ')].join(' ')).includes(q)));
}
export function selectHelpArticle(state: HelpState, id: string): HelpState { return { ...state, selectedArticleId: id }; }
export function resetHelpFilters(): HelpState { return { search: '', category: '', selectedArticleId: 'getting-started' }; }
export function helpRelatedNavigation(section: string): { section: string; mutates: false; ownsFeedback: false } { return { section, mutates: false, ownsFeedback: false }; }
