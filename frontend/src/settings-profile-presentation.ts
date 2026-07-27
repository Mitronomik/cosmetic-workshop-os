export type WorkshopProfileFields = { workshop_name: string; master_name: string; workshop_contact_text: string; workshop_note: string };
export type WorkshopProfileViewState = {
  status: 'idle' | 'loading' | 'ready' | 'error';
  actionStatus: 'idle' | 'saving';
  profile: WorkshopProfileFields | null;
  draft: WorkshopProfileFields;
  error: string;
  message: string;
};

export type WorkshopProfileMarkupHelpers = {
  renderFeedback: (tone: 'neutral' | 'success' | 'warning' | 'error', message: string) => string;
  actionsMarkup: string;
};

export function isWorkshopProfileDirty(state: WorkshopProfileViewState): boolean {
  const { profile, draft } = state;
  return profile !== null && (draft.workshop_name !== profile.workshop_name || draft.master_name !== profile.master_name || draft.workshop_contact_text !== profile.workshop_contact_text || draft.workshop_note !== profile.workshop_note);
}

export function isWorkshopProfileFormAvailable(state: WorkshopProfileViewState): boolean {
  return state.status === 'ready' && state.profile !== null && state.actionStatus !== 'saving';
}

/** Workshop-profile card markup, extracted unchanged from the Settings route. */
export function workshopProfileCardMarkup(state: WorkshopProfileViewState, helpers: WorkshopProfileMarkupHelpers): string {
  const draft = state.draft;
  const saving = state.actionStatus === 'saving';
  const loading = state.status === 'loading';
  const available = isWorkshopProfileFormAvailable(state);
  const dirty = available && isWorkshopProfileDirty(state);
  const disabled = available ? '' : 'disabled';
  const actionDisabled = dirty ? '' : 'disabled';
  const retry = state.status === 'error' && state.profile === null ? '<div class="actions"><button class="secondary-action compact" type="button" data-action="reload-workshop-profile">Повторить загрузку</button></div>' : '';
  const message = state.message && state.status === 'ready' ? `<div data-workshop-profile-result>${helpers.renderFeedback('success', state.message)}</div>` : '';
  const error = state.error ? `<div data-workshop-profile-result>${helpers.renderFeedback('error', state.error)}</div>` : '';
  return `<section class="card data-card settings-card settings-profile-card"><h2>Профиль мастерской</h2><p>Эти данные добавляются в новые Markdown- и PDF-документы «Сводка мастерской», которые создаются в разделе «Документы отчётов».</p><p class="next-step">Ранее созданные документы не меняются автоматически.</p><div class="actions">${helpers.actionsMarkup}</div>${loading ? '<p class="muted-text">Загружаем профиль мастерской…</p>' : ''}${error}${retry}${message}<div data-workshop-profile-dirty-notice ${dirty ? '' : 'hidden'}>${helpers.renderFeedback('neutral', 'Есть несохранённые изменения.')}</div><form class="ingredient-form" data-form="workshop-profile" aria-busy="${saving ? 'true' : 'false'}"><div class="form-grid settings-profile-form"><label>Название мастерской<input data-workshop-profile-field="workshop_name" value="${escapeHtml(draft.workshop_name)}" maxlength="120" placeholder="Например, Мастерская Анны" ${disabled} /></label><label>Имя мастера / косметолога<input data-workshop-profile-field="master_name" value="${escapeHtml(draft.master_name)}" maxlength="120" placeholder="Например, Анна Иванова" ${disabled} /></label><label class="full-span">Контактная информация<textarea data-workshop-profile-field="workshop_contact_text" maxlength="500" rows="4" placeholder="Телефон, почта или удобный способ связи" ${disabled}>${escapeHtml(draft.workshop_contact_text)}</textarea></label><label class="full-span">Краткое описание / примечание<textarea data-workshop-profile-field="workshop_note" maxlength="500" rows="4" placeholder="Коротко о мастерской для новых сводок" ${disabled}>${escapeHtml(draft.workshop_note)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit" data-workshop-profile-save ${actionDisabled}>${saving ? 'Сохраняем…' : 'Сохранить профиль'}</button><button class="secondary-action" type="button" data-action="cancel-workshop-profile" ${actionDisabled}>Отменить изменения</button></div></form></section>`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char] ?? char));
}
