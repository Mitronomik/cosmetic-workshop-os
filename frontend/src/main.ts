type HealthStatus = 'checking' | 'online' | 'offline';
type OnboardingStatus = 'loading' | 'ready' | 'unavailable';

type OnboardingState = {
  has_started: boolean;
  is_completed: boolean;
  current_step: string;
  completed_steps: string[];
  available_steps: string[];
};

const navigationItems = ['Главная','Рецепты','Клиенты','Заказы','Запасы','Тара','Закупки','Производство','Импорт','Отчеты','Настройки','Помощь'];
const stepLabels: Record<string, string> = {
  welcome: 'Познакомиться с рабочим пространством',
  data_location: 'Понять, где хранятся локальные данные',
  first_ingredient: 'Подготовить первый компонент',
  first_recipe: 'Подготовить первый рецепт',
  first_client: 'Подготовить первую карточку клиента',
  first_order: 'Подготовить первый заказ',
  first_backup: 'Запланировать первую резервную копию',
};

let activeSection = 'Главная';
let healthStatus: HealthStatus = 'checking';
let onboardingStatus: OnboardingStatus = 'loading';
let onboardingState: OnboardingState | null = null;
let onboardingMessage = '';

function render() {
  const root = document.getElementById('root');
  if (!root) return;
  const healthLabel = { checking: 'Проверяем локальный API…', online: 'Локальный API доступен', offline: 'Локальный API пока недоступен' }[healthStatus];
  root.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar" aria-label="Основная навигация">
        <div class="brand" aria-label="Мастерская косметолога">
          <div class="brand-mark" aria-hidden="true">
            <span class="brand-fallback">МК</span>
            <img src="/brand/mch-logo.png" alt="" />
          </div>
          <div class="brand-copy">
            <p class="brand-kicker">Локальная система</p>
            <p class="brand-name">Мастерская косметолога</p>
          </div>
        </div>
        <nav class="navigation">${navigationItems.map((item) => `<button class="nav-item ${item === activeSection ? 'active' : ''}" type="button" data-section="${item}">${item}</button>`).join('')}</nav>
      </aside>
      <main class="content">
        <header class="topbar">
          <div><p class="eyebrow">Рабочее пространство</p><h1>${activeSection}</h1></div>
          <span class="status ${healthStatus}">${healthLabel}</span>
        </header>
        ${activeSection === 'Главная' ? dashboardPlaceholder() : sectionPlaceholder(activeSection)}
      </main>
    </div>`;
  bindEvents(root);
}

function bindEvents(root: HTMLElement) {
  root.querySelector<HTMLImageElement>('.brand-mark img')?.addEventListener('error', (event) => {
    const logo = event.currentTarget as HTMLImageElement;
    logo.hidden = true;
  });
  root.querySelectorAll<HTMLButtonElement>('.nav-item').forEach((button) => {
    button.addEventListener('click', () => { activeSection = button.dataset.section ?? 'Главная'; render(); });
  });
  root.querySelector<HTMLButtonElement>('[data-action="start-onboarding"]')?.addEventListener('click', () => updateOnboarding('/api/onboarding/start'));
  root.querySelector<HTMLButtonElement>('[data-action="complete-step"]')?.addEventListener('click', (event) => {
    const step = (event.currentTarget as HTMLButtonElement).dataset.step;
    if (step) updateOnboarding('/api/onboarding/complete-step', { step });
  });
  root.querySelector<HTMLButtonElement>('[data-action="complete-onboarding"]')?.addEventListener('click', () => updateOnboarding('/api/onboarding/complete'));
}

function dashboardPlaceholder() {
  return `
    ${onboardingCard()}
    <section class="card"><p class="card-kicker">Сегодня в мастерской</p><h2>Первые рабочие разделы появятся постепенно</h2><p>Здесь будет спокойная рабочая панель: активные заказы, предупреждения, закупки, производство и резервные копии.</p><p class="next-step">Начните с компонентов, затем рецептов, клиентов и заказов. Каждый раздел будет подключаться отдельным безопасным шагом.</p></section>`;
}

function onboardingCard() {
  if (onboardingStatus === 'loading') {
    return `<section class="card onboarding-card"><p class="card-kicker">Первый запуск</p><h2>Готовим рабочее пространство…</h2><p>Проверяем состояние первичной настройки.</p></section>`;
  }
  if (onboardingStatus === 'unavailable') {
    return `<section class="card onboarding-card"><p class="card-kicker">Первый запуск</p><h2>Добро пожаловать в Мастерскую косметолога</h2><p>Это локальная рабочая система. Даже если локальный API сейчас недоступен, вы можете осмотреть разделы приложения.</p><p class="next-step">Когда приложение будет запущено полностью, здесь появится чек-лист первичной настройки.</p></section>`;
  }
  if (onboardingState?.is_completed) {
    return `<section class="card onboarding-card"><p class="card-kicker">Настройка завершена</p><h2>Рабочее пространство готово к постепенному заполнению</h2><p>Компоненты, рецепты, клиенты и заказы будут добавляться пошагово по мере появления соответствующих разделов.</p></section>`;
  }
  const currentStep = onboardingState?.current_step ?? 'welcome';
  const started = onboardingState?.has_started ?? false;
  return `<section class="card onboarding-card"><p class="card-kicker">Первый запуск</p><h2>Добро пожаловать в Мастерскую косметолога</h2><p>Это локальная рабочая система для вашей косметической мастерской. Данные хранятся на этом компьютере, отдельно от кода приложения.</p><div class="onboarding-note"><strong>Что важно:</strong> регулярно делайте резервные копии, а компоненты, рецепты, клиентов и заказы заполняйте постепенно.</div>${onboardingMessage ? `<p class="inline-message">${onboardingMessage}</p>` : ''}<ol class="checklist">${(onboardingState?.available_steps ?? Object.keys(stepLabels)).map((step) => checklistItem(step, currentStep)).join('')}</ol><div class="actions">${started ? `<button class="primary-action" type="button" data-action="complete-step" data-step="${currentStep}">Отметить текущий шаг</button>` : '<button class="primary-action" type="button" data-action="start-onboarding">Начать настройку</button>'}<button class="secondary-action" type="button" data-action="complete-onboarding">Пропустить пока</button></div></section>`;
}

function checklistItem(step: string, currentStep: string) {
  const isDone = onboardingState?.completed_steps.includes(step);
  const isCurrent = step === currentStep && !isDone;
  const marker = isDone ? '✓' : isCurrent ? '•' : '○';
  return `<li class="${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}"><span>${marker}</span><div><strong>${stepLabels[step] ?? step}</strong><small>${stepHint(step)}</small></div></li>`;
}

function stepHint(step: string) {
  const hints: Record<string, string> = {
    welcome: 'Коротко понять назначение системы.',
    data_location: 'Данные остаются на этом компьютере; будущие резервные копии помогут защитить работу.',
    first_ingredient: 'Позже здесь появится добавление компонентов и плотностей.',
    first_recipe: 'Рецепты будут храниться версиями, без скрытого изменения истории.',
    first_client: 'Клиентские данные будут заполняться аккуратно и понятно.',
    first_order: 'Заказы и производство появятся отдельным roadmap-шагом.',
    first_backup: 'Резервные копии — обязательная привычка для локальной системы.',
  };
  return hints[step] ?? 'Шаг будет уточнен позже.';
}

function sectionPlaceholder(title: string) {
  const emptyStates: Record<string, string> = {
    Рецепты: 'Рецепты появятся здесь позже. Пока можно завершить первичную настройку на главной странице.',
    Клиенты: 'Клиенты появятся здесь позже. В будущих шагах здесь будут карточки клиентов и индивидуальные формулы.',
    Запасы: 'Сначала добавьте первый компонент. Полный учет партий и остатков появится отдельными PR.',
  };
  return `<section class="card"><p class="card-kicker">Раздел приложения</p><h2>${title}</h2><p>${emptyStates[title] ?? 'Этот раздел подготовлен как понятная навигационная заглушка. Формы и бизнес-функции будут добавляться в отдельных PR.'}</p><p class="next-step">Следующее действие: дождаться реализации соответствующего roadmap-шага.</p></section>`;
}

function loadOnboarding() {
  fetch('/api/onboarding')
    .then((response) => {
      if (!response.ok) throw new Error('Onboarding is unavailable');
      return response.json() as Promise<OnboardingState>;
    })
    .then((state) => { onboardingState = state; onboardingStatus = 'ready'; onboardingMessage = ''; render(); })
    .catch(() => { onboardingStatus = 'unavailable'; render(); });
}

function updateOnboarding(url: string, body?: Record<string, string>) {
  fetch(url, { method: 'POST', headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined })
    .then((response) => {
      if (!response.ok) throw new Error('Onboarding update failed');
      return response.json() as Promise<OnboardingState>;
    })
    .then((state) => { onboardingState = state; onboardingStatus = 'ready'; onboardingMessage = 'Сохранено в локальном рабочем пространстве.'; render(); })
    .catch(() => { onboardingStatus = 'unavailable'; onboardingMessage = ''; render(); });
}

render();
fetch('/api/health').then((response) => { healthStatus = response.ok ? 'online' : 'offline'; render(); }).catch(() => { healthStatus = 'offline'; render(); });
loadOnboarding();
