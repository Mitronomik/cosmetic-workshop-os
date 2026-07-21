export type FeedbackTone = 'none' | 'success' | 'warning' | 'error';
export type AnnouncementKind = 'none' | 'polite' | 'assertive';
export type DashboardLoadKind = 'initial' | 'refresh';

export type FeedbackSnapshot<TData, TOnboarding> = {
  dashboard: {
    status: 'idle' | 'loading' | 'ready' | 'error';
    active: boolean;
    activeKind: DashboardLoadKind | null;
    data: TData | null;
    message: string;
    warning: string;
    error: string;
  };
  onboarding: {
    status: 'loading' | 'ready' | 'unavailable';
    active: boolean;
    action: OnboardingAction | null;
    state: TOnboarding | null;
    message: string;
    warning: string;
    error: string;
  };
};

export type StartResult = { accepted: boolean; requestId: number; announceClear: boolean };
export type FinishResult = { accepted: boolean; announcement: AnnouncementKind; message: string };
export type OnboardingAction = 'start' | 'complete-step' | 'skip' | 'reset';

export class DashboardOnboardingFeedbackLifecycle<TDashboardData, TOnboardingState> {
  private dashboardRequestId = 0;
  private onboardingMutationId = 0;
  private onboardingRefreshId = 0;

  readonly state: FeedbackSnapshot<TDashboardData, TOnboardingState> = {
    dashboard: { status: 'idle', active: false, activeKind: null, data: null, message: '', warning: '', error: '' },
    onboarding: { status: 'loading', active: false, action: null, state: null, message: '', warning: '', error: '' },
  };

  startDashboardLoad(kind: DashboardLoadKind): StartResult {
    if (this.state.dashboard.active) return { accepted: false, requestId: this.dashboardRequestId, announceClear: false };
    const requestId = ++this.dashboardRequestId;
    this.state.dashboard.status = 'loading';
    this.state.dashboard.active = true;
    this.state.dashboard.activeKind = kind;
    this.state.dashboard.message = '';
    this.state.dashboard.warning = '';
    this.state.dashboard.error = '';
    return { accepted: true, requestId, announceClear: kind === 'refresh' };
  }

  finishDashboardSuccess(requestId: number, data: TDashboardData): FinishResult {
    if (requestId !== this.dashboardRequestId) return { accepted: false, announcement: 'none', message: '' };
    const kind = this.state.dashboard.activeKind;
    this.state.dashboard.status = 'ready';
    this.state.dashboard.active = false;
    this.state.dashboard.activeKind = null;
    this.state.dashboard.data = data;
    this.state.dashboard.warning = '';
    this.state.dashboard.error = '';
    this.state.dashboard.message = kind === 'refresh' ? 'Обзор обновлён. Показаны свежие данные из локального приложения.' : '';
    return { accepted: true, announcement: kind === 'refresh' ? 'polite' : 'none', message: this.state.dashboard.message };
  }

  finishDashboardFailure(requestId: number): FinishResult {
    if (requestId !== this.dashboardRequestId) return { accepted: false, announcement: 'none', message: '' };
    const hasData = this.state.dashboard.data !== null;
    this.state.dashboard.status = 'error';
    this.state.dashboard.active = false;
    this.state.dashboard.activeKind = null;
    this.state.dashboard.message = '';
    this.state.dashboard.error = hasData ? '' : 'Не удалось загрузить обзор мастерской. Проверьте, что локальное приложение запущено, и попробуйте снова.';
    this.state.dashboard.warning = hasData ? 'Не удалось обновить обзор. Показываем ранее загруженные данные — они могут быть устаревшими.' : '';
    return { accepted: true, announcement: 'assertive', message: hasData ? this.state.dashboard.warning : this.state.dashboard.error };
  }

  startOnboardingLoad(): StartResult {
    const requestId = ++this.onboardingRefreshId;
    if (!this.state.onboarding.state) this.state.onboarding.status = 'loading';
    return { accepted: true, requestId, announceClear: false };
  }

  finishOnboardingLoadSuccess(requestId: number, state: TOnboardingState): FinishResult {
    if (requestId !== this.onboardingRefreshId) return { accepted: false, announcement: 'none', message: '' };
    this.state.onboarding.status = 'ready';
    this.state.onboarding.state = state;
    return { accepted: true, announcement: 'none', message: '' };
  }

  finishOnboardingLoadFailure(requestId: number, afterSuccessfulMutation = false): FinishResult {
    if (requestId !== this.onboardingRefreshId) return { accepted: false, announcement: 'none', message: '' };
    if (afterSuccessfulMutation && this.state.onboarding.state) {
      this.state.onboarding.warning = 'Действие сохранено, но не удалось перечитать список шагов. Показано последнее подтверждённое состояние.';
      this.state.onboarding.status = 'ready';
      return { accepted: true, announcement: 'assertive', message: this.state.onboarding.warning };
    }
    this.state.onboarding.status = 'unavailable';
    return { accepted: true, announcement: 'assertive', message: 'Список первых шагов временно недоступен.' };
  }

  startOnboardingMutation(action: OnboardingAction): StartResult {
    if (this.state.onboarding.active) return { accepted: false, requestId: this.onboardingMutationId, announceClear: false };
    const requestId = ++this.onboardingMutationId;
    this.state.onboarding.active = true;
    this.state.onboarding.action = action;
    this.state.onboarding.message = '';
    this.state.onboarding.error = '';
    this.state.onboarding.warning = '';
    return { accepted: true, requestId, announceClear: true };
  }

  finishOnboardingMutationSuccess(requestId: number, state: TOnboardingState, message: string): FinishResult {
    if (requestId !== this.onboardingMutationId) return { accepted: false, announcement: 'none', message: '' };
    this.state.onboarding.active = false;
    this.state.onboarding.action = null;
    this.state.onboarding.status = 'ready';
    this.state.onboarding.state = state;
    this.state.onboarding.message = message;
    this.state.onboarding.error = '';
    return { accepted: true, announcement: 'polite', message };
  }

  finishOnboardingMutationFailure(requestId: number, message: string): FinishResult {
    if (requestId !== this.onboardingMutationId) return { accepted: false, announcement: 'none', message: '' };
    this.state.onboarding.active = false;
    this.state.onboarding.action = null;
    this.state.onboarding.error = message;
    this.state.onboarding.message = '';
    this.state.onboarding.warning = '';
    return { accepted: true, announcement: 'assertive', message };
  }
}

export function onboardingSuccessMessage(action: OnboardingAction): string {
  return ({
    start: 'Настройка начата. Можно идти по шагам в удобном темпе.',
    'complete-step': 'Шаг отмечен выполненным. Список первых шагов обновлён.',
    skip: 'Список первых шагов скрыт. Вы сможете вернуться к нему позже.',
    reset: 'Список первых шагов снова открыт для проверки пути.',
  })[action];
}

export function onboardingFailureMessage(action: OnboardingAction): string {
  return ({
    start: 'Не удалось начать настройку. Данные мастерской не изменялись.',
    'complete-step': 'Не удалось отметить шаг. Предыдущее состояние списка сохранено.',
    skip: 'Не удалось пропустить настройку. Предыдущее состояние списка сохранено.',
    reset: 'Не удалось открыть список первых шагов заново. Предыдущее состояние сохранено.',
  })[action];
}
