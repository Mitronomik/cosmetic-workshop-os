export type FeedbackTone = 'none' | 'success' | 'warning' | 'error';
export type AnnouncementKind = 'none' | 'polite' | 'assertive';
export type DashboardLoadKind = 'initial' | 'refresh';
export type OnboardingLoadKind = 'initial' | 'refresh';
export type OnboardingAction = 'start' | 'complete-step' | 'skip' | 'reset';

export type FinishResult = { accepted: boolean; announcement: AnnouncementKind; message: string; focusAllowed: boolean };
export type StartResult = { accepted: boolean; requestId: number; announceClear: boolean };
export type FocusCandidateKind = 'previous' | 'heading' | 'primary' | 'live-region';
export type FocusCandidate = { key: string; kind: FocusCandidateKind; enabled: boolean; attached: boolean };


export type ActionControl = { addEventListener: (type: 'click', listener: () => void) => void };
export type ActionControlRoot<TControl extends ActionControl = ActionControl> = { querySelectorAll: (selector: string) => Iterable<TControl> };

export function bindActionControls<TControl extends ActionControl>(root: ActionControlRoot<TControl>, selector: string, callback: () => void): number {
  const controls = Array.from(root.querySelectorAll(selector));
  controls.forEach((control) => control.addEventListener('click', callback));
  return controls.length;
}

export type FeedbackSnapshot<TData, TOnboarding> = {
  dashboard: {
    status: 'idle' | 'loading' | 'ready' | 'error';
    active: boolean;
    activeKind: DashboardLoadKind | null;
    hasLoadedSnapshot: boolean;
    data: TData | null;
    message: string;
    warning: string;
    error: string;
  };
  onboarding: {
    status: 'loading' | 'ready' | 'unavailable';
    mutationActive: boolean;
    loadActive: boolean;
    loadKind: OnboardingLoadKind | null;
    action: OnboardingAction | null;
    state: TOnboarding | null;
    message: string;
    warning: string;
    error: string;
  };
};

function finish(accepted: boolean, announcement: AnnouncementKind = 'none', message = '', focusAllowed = false): FinishResult {
  return { accepted, announcement, message, focusAllowed };
}

export class DashboardOnboardingFeedbackLifecycle<TDashboardData, TOnboardingState> {
  private dashboardRequestId = 0;
  private onboardingMutationId = 0;
  private onboardingRefreshId = 0;

  readonly state: FeedbackSnapshot<TDashboardData, TOnboardingState> = {
    dashboard: { status: 'idle', active: false, activeKind: null, hasLoadedSnapshot: false, data: null, message: '', warning: '', error: '' },
    onboarding: { status: 'loading', mutationActive: false, loadActive: false, loadKind: null, action: null, state: null, message: '', warning: '', error: '' },
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

  finishDashboardSuccess(requestId: number, data: TDashboardData, ownsPresentation = true): FinishResult {
    if (requestId !== this.dashboardRequestId) return finish(false);
    const kind = this.state.dashboard.activeKind;
    this.state.dashboard.status = 'ready';
    this.state.dashboard.active = false;
    this.state.dashboard.activeKind = null;
    this.state.dashboard.hasLoadedSnapshot = true;
    this.state.dashboard.data = data;
    this.state.dashboard.warning = '';
    this.state.dashboard.error = '';
    this.state.dashboard.message = ownsPresentation && kind === 'refresh' ? 'Обзор обновлён. Показаны свежие данные из локального приложения.' : '';
    return finish(true, ownsPresentation && kind === 'refresh' ? 'polite' : 'none', this.state.dashboard.message);
  }

  finishDashboardFailure(requestId: number, ownsPresentation = true): FinishResult {
    if (requestId !== this.dashboardRequestId) return finish(false);
    const hasSnapshot = this.state.dashboard.hasLoadedSnapshot;
    this.state.dashboard.active = false;
    this.state.dashboard.activeKind = null;
    this.state.dashboard.message = '';
    if (!ownsPresentation) {
      this.state.dashboard.status = hasSnapshot ? 'ready' : 'idle';
      this.state.dashboard.warning = '';
      this.state.dashboard.error = '';
      return finish(true);
    }
    this.state.dashboard.status = hasSnapshot ? 'error' : 'error';
    this.state.dashboard.error = hasSnapshot ? '' : 'Не удалось загрузить обзор мастерской. Проверьте, что локальное приложение запущено, и попробуйте снова.';
    this.state.dashboard.warning = hasSnapshot ? 'Не удалось обновить обзор. Показываем ранее загруженные данные — они могут быть устаревшими.' : '';
    return finish(true, 'assertive', hasSnapshot ? this.state.dashboard.warning : this.state.dashboard.error);
  }

  clearDashboardTransientFeedback(): void {
    this.state.dashboard.message = '';
    this.state.dashboard.warning = '';
    this.state.dashboard.error = '';
    if (this.state.dashboard.status === 'error' && this.state.dashboard.hasLoadedSnapshot) this.state.dashboard.status = 'ready';
  }

  startOnboardingLoad(kind: OnboardingLoadKind): StartResult {
    if (this.state.onboarding.loadActive || this.state.onboarding.mutationActive) return { accepted: false, requestId: this.onboardingRefreshId, announceClear: false };
    const requestId = ++this.onboardingRefreshId;
    this.state.onboarding.loadActive = true;
    this.state.onboarding.loadKind = kind;
    if (!this.state.onboarding.state) this.state.onboarding.status = 'loading';
    if (kind === 'refresh') {
      this.state.onboarding.message = '';
      this.state.onboarding.warning = '';
      this.state.onboarding.error = '';
    } else if (!this.state.onboarding.state) {
      this.state.onboarding.message = '';
      this.state.onboarding.warning = '';
      this.state.onboarding.error = '';
    }
    return { accepted: true, requestId, announceClear: kind === 'refresh' };
  }

  finishOnboardingLoadSuccess(requestId: number, state: TOnboardingState, ownsPresentation = true): FinishResult {
    if (requestId !== this.onboardingRefreshId) return finish(false);
    const kind = this.state.onboarding.loadKind;
    this.state.onboarding.loadActive = false;
    this.state.onboarding.loadKind = null;
    this.state.onboarding.status = 'ready';
    this.state.onboarding.state = state;
    this.state.onboarding.error = '';
    this.state.onboarding.warning = '';
    this.state.onboarding.message = ownsPresentation && kind === 'refresh' ? 'Список первых шагов обновлён.' : '';
    return finish(true, ownsPresentation && kind === 'refresh' ? 'polite' : 'none', this.state.onboarding.message);
  }

  finishOnboardingLoadFailure(requestId: number, ownsPresentation = true): FinishResult {
    if (requestId !== this.onboardingRefreshId) return finish(false);
    const hasState = this.state.onboarding.state !== null;
    this.state.onboarding.loadActive = false;
    this.state.onboarding.loadKind = null;
    this.state.onboarding.message = '';
    if (!ownsPresentation) {
      this.state.onboarding.status = hasState ? 'ready' : 'unavailable';
      this.state.onboarding.warning = '';
      this.state.onboarding.error = '';
      return finish(true);
    }
    this.state.onboarding.status = hasState ? 'ready' : 'unavailable';
    this.state.onboarding.error = hasState ? '' : 'Список первых шагов временно недоступен.';
    this.state.onboarding.warning = hasState ? 'Не удалось обновить список первых шагов. Показано последнее успешно загруженное состояние.' : '';
    return finish(true, 'assertive', hasState ? this.state.onboarding.warning : this.state.onboarding.error);
  }

  startOnboardingMutation(action: OnboardingAction): StartResult {
    if (this.state.onboarding.mutationActive || this.state.onboarding.loadActive) return { accepted: false, requestId: this.onboardingMutationId, announceClear: false };
    const requestId = ++this.onboardingMutationId;
    this.state.onboarding.mutationActive = true;
    this.state.onboarding.action = action;
    this.state.onboarding.message = '';
    this.state.onboarding.error = '';
    this.state.onboarding.warning = '';
    return { accepted: true, requestId, announceClear: true };
  }

  invalidateOnboardingMutation(): number {
    this.state.onboarding.mutationActive = false;
    this.state.onboarding.action = null;
    return ++this.onboardingMutationId;
  }

  finishOnboardingMutationSuccess(requestId: number, state: TOnboardingState, message: string, ownsPresentation = true): FinishResult {
    if (requestId !== this.onboardingMutationId) return finish(false);
    this.state.onboarding.mutationActive = false;
    this.state.onboarding.action = null;
    this.state.onboarding.status = 'ready';
    this.state.onboarding.state = state;
    this.state.onboarding.error = '';
    this.state.onboarding.warning = '';
    this.state.onboarding.message = ownsPresentation ? message : '';
    return finish(true, ownsPresentation ? 'polite' : 'none', this.state.onboarding.message, ownsPresentation);
  }

  finishOnboardingMutationFailure(requestId: number, message: string, ownsPresentation = true): FinishResult {
    if (requestId !== this.onboardingMutationId) return finish(false);
    this.state.onboarding.mutationActive = false;
    this.state.onboarding.action = null;
    this.state.onboarding.warning = '';
    this.state.onboarding.message = '';
    this.state.onboarding.error = ownsPresentation ? message : '';
    return finish(true, ownsPresentation ? 'assertive' : 'none', this.state.onboarding.error, ownsPresentation);
  }

  clearOnboardingTransientFeedback(): void {
    this.state.onboarding.message = '';
    this.state.onboarding.warning = '';
    this.state.onboarding.error = '';
    if (this.state.onboarding.state) this.state.onboarding.status = 'ready';
  }
}

export function selectOnboardingFocusTarget(ownsPresentation: boolean, previousKey: string | null, candidates: FocusCandidate[]): string | null {
  if (!ownsPresentation) return null;
  const isUsable = (candidate: FocusCandidate | undefined) => Boolean(candidate && candidate.attached && candidate.enabled && candidate.kind !== 'live-region');
  const previous = previousKey ? candidates.find((candidate) => candidate.key === previousKey) : undefined;
  if (isUsable(previous)) return previous!.key;
  const heading = candidates.find((candidate) => candidate.kind === 'heading');
  if (isUsable(heading)) return heading!.key;
  const primary = candidates.find((candidate) => candidate.kind === 'primary');
  if (isUsable(primary)) return primary!.key;
  return null;
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
    skip: 'Не удалось пропустить настройку. Предыдущее состояние сохранено.',
    reset: 'Не удалось открыть список первых шагов заново. Предыдущее состояние сохранено.',
  })[action];
}
