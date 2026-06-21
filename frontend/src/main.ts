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
        <div class="brand">Мастерская косметолога</div>
        <nav class="navigation">${navigationItems.map((item) => `<button class="nav-item ${item === activeSection ? 'active' : ''}" type="button" data-section="${item}">${item}</button>`).join('')}</nav>
      </aside>
      <main class="content">
        <header class="topbar">
          <div><p class="eyebrow">Локальная рабочая система</p><h1>${activeSection}</h1></div>
          <span class="status ${healthStatus}">${healthLabel}</span>
        </header>
        ${activeSection === 'Главная' ? dashboardPlaceholder() : sectionPlaceholder(activeSection)}
      </main>
    </div>`;
  root.querySelectorAll<HTMLButtonElement>('.nav-item').forEach((button) => {
    button.addEventListener('click', () => { activeSection = button.dataset.section ?? 'Главная'; render(); });
  });
}

function dashboardPlaceholder() {
  return `<section class="card"><h2>Мастерская косметолога</h2><p>Здесь будет рабочая панель: активные заказы, предупреждения, закупки, производство, onboarding и резервные копии.</p><p>Следующий шаг разработки: подключить базовую структуру приложения и затем постепенно добавлять данные без расширения текущего PR1 scope.</p></section>`;
}

function sectionPlaceholder(title: string) {
  return `<section class="card"><h2>${title}</h2><p>Этот раздел подготовлен как понятная навигационная заглушка. Формы и бизнес-функции будут добавляться в отдельных PR.</p><p class="next-step">Следующее действие: дождаться реализации соответствующего roadmap-шага.</p></section>`;
}

render();
fetch('/api/health').then((response) => { healthStatus = response.ok ? 'online' : 'offline'; render(); }).catch(() => { healthStatus = 'offline'; render(); });
