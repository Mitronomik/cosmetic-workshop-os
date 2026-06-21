type HealthStatus = 'checking' | 'online' | 'offline';

const navigationItems = ['Главная','Рецепты','Клиенты','Заказы','Запасы','Тара','Закупки','Производство','Импорт','Отчеты','Настройки','Помощь'];
let activeSection = 'Главная';
let healthStatus: HealthStatus = 'checking';

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
  root.querySelector<HTMLImageElement>('.brand-mark img')?.addEventListener('error', (event) => {
    const logo = event.currentTarget as HTMLImageElement;
    logo.hidden = true;
  });
  root.querySelectorAll<HTMLButtonElement>('.nav-item').forEach((button) => {
    button.addEventListener('click', () => { activeSection = button.dataset.section ?? 'Главная'; render(); });
  });
}

function dashboardPlaceholder() {
  return `<section class="card"><p class="card-kicker">Сегодня в мастерской</p><h2>Мастерская косметолога</h2><p>Здесь будет спокойная рабочая панель: активные заказы, предупреждения, закупки, производство, onboarding и резервные копии.</p><p class="next-step">Следующий шаг разработки: постепенно подключать данные и функции только в отдельных roadmap-PR.</p></section>`;
}

function sectionPlaceholder(title: string) {
  return `<section class="card"><p class="card-kicker">Раздел приложения</p><h2>${title}</h2><p>Этот раздел подготовлен как понятная навигационная заглушка. Формы и бизнес-функции будут добавляться в отдельных PR.</p><p class="next-step">Следующее действие: дождаться реализации соответствующего roadmap-шага.</p></section>`;
}

render();
fetch('/api/health').then((response) => { healthStatus = response.ok ? 'online' : 'offline'; render(); }).catch(() => { healthStatus = 'offline'; render(); });
