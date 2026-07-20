# cosmetic-workshop-os — План доведения MVP до продуктовой готовности

Проект: `cosmetic-workshop-os`
Клиентское название: **Мастерская косметолога**
Целевой путь в репозитории: `docs/implementation-plan.md`
Тип документа: активный рабочий план ближайших окон реализации
Статус: **активен после merge и проверки PR #106**
Правило нумерации: идентификаторы slices ниже не являются номерами PR. Номер указывается только после фактического создания PR.

---

## 1. Назначение

Этот документ задаёт путь от текущего функционального MVP к локальному продукту, который можно передать нетехническому пользователю косметической мастерской.

Он объединяет:

- действующий `docs/roadmap.md`;
- фактическое состояние репозитория;
- результаты evidence-based UI/UX-аудита Hermes от 2026-07-12;
- незакрытые обязательства `docs/product-spec.md` и `docs/roadmap.md`;
- архитектурные ограничения, правила Codex и обязательный smoke после PR.

Документ **не заменяет** `docs/roadmap.md`.

- `docs/roadmap.md` хранит стратегическую последовательность и продуктовый scope.
- `docs/implementation-plan.md` управляет текущим окном из 3–5 небольших PR и следующими release gates.
- `state/` хранит текущий фактический статус, а не долгосрочный план.

---

## 2. Порядок источников истины

При расхождениях использовать следующий приоритет:

1. `AGENTS.md` и вложенные `AGENTS.md`;
2. `docs/architecture.md`;
3. `docs/product-spec.md` и `docs/domain-model.md`;
4. `docs/roadmap.md`;
5. `docs/ui-ux-contract.md` и профильные документы;
6. этот `docs/implementation-plan.md` для текущей последовательности;
7. `state/current-focus.md`, `state/progress.md`, `state/handoff.md` для фактического состояния ветки.

Аудит является источником доказательств, но не может сам менять архитектуру или scope проекта.

---

## 3. Текущая базовая точка

На момент активации плана:

- core MVP feature implementation is complete through PR98;
- PR99–PR101 относятся к документации и UI-governance;
- PR105 ввёл общий визуальный контракт действий и прошёл focused browser smoke;
- PR106 ввёл shared feedback и announcement semantics для `/settings`, `/exports`, `/report-documents`, `/imports`, `/demo-data`;
- PR106 уже merged и verified, merge commit: `bff2fae219640ded411abc3db08f0c1ba419cee3`;
- обязательный Hermes browser smoke завершён с verdict `PR106_DETERMINISTIC_SMOKE_PASS_WITH_NON_BLOCKING_FINDINGS`;
- canonical tested runtime head и merged verification зафиксированы в `state/progress.md` и `state/handoff.md`;
- PR #107 активирует этот implementation plan без изменения runtime behavior;
- следующий runtime slice: Slice A1 — очистка пользовательского технического текста.

---

## 4. Неизменяемые продуктовые правила

Каждый slice обязан сохранять:

- local-first работу без обязательного интернета;
- хранение пользовательских данных отдельно от кода и пакета;
- поставку продукта без Git, Python, Node.js, Docker и терминала для пользователя;
- API-first backend;
- backend-owned расчёты, импорт, списания, производство и миграции;
- неизменность исторических данных;
- версии рецептов и first-class индивидуальные рецепты;
- склад через партии и движения;
- transactional производство;
- импорт через draft → preview → validation → confirmation → apply;
- backup перед миграцией;
- различение mutation failure и refresh failure;
- человекопонятный UI без PR-лексики, raw JSON и непереведённых backend-полей;
- отсутствие cloud sync, OCR, полноценной бухгалтерии, ролей, multi-user и advanced analytics в MVP.

---

## 5. Статусы

- `IN PROGRESS` — выполняется или проверяется сейчас;
- `READY` — можно брать после предыдущего gate;
- `NEEDS EVIDENCE` — сначала воспроизвести и определить причину;
- `BLOCKED` — заблокировано предыдущим этапом;
- `DONE` — merged и проверено;
- `DEFERRED` — осознанно вне текущего MVP.

Если slice существенно меняет `frontend/src/main.ts`, одновременно должен выполняться только один такой runtime PR.

---

## 6. Решения по аудиту Hermes

### Принимаем как подтверждённые задачи

1. Frontend не везде показывает структурированные backend validation errors.
2. Табличные маршруты создают page-level horizontal overflow; `/ingredient-lots` переполняется даже на desktop.
3. Runtime содержит технический и устаревший текст: PR-лексика, неверные capability statements, постоянный API indicator.
4. Пути к локальным файлам показываются слишком технически.
5. Часть navigation/status metadata не соответствует фактически работающим маршрутам.

### Требуют отдельной проверки после PR106

- одновременные success и error на `/demo-data`;
- duplicate/stale feedback на маршрутах, не входивших в focused PR106 smoke;
- broader legacy feedback outside the PR106 route group;
- incorrect polite/assertive announcements на маршрутах, не покрытых PR106 Hermes scenarios.

PR106 Hermes smoke подтвердил только scoped scenarios для Import Apply, refresh failure, structured mutation conflict, Settings, narrow viewport, keyboard reachability и persistent announcer placement. Он не является полной проверкой всех routes и audit findings.

### Сначала диагностируем, потом меняем код

- отсутствие алертов после установки demo data;
- отсутствие закупочных предложений;
- пустые или navigation-only dashboard blocks;
- persistence order detail между навигациями.

Перед исправлением нужно проверить явные команды regeneration и реальные условия demo fixture.

### Не принимаем как прямой MVP backlog

- автоматический retry/backoff для мутаций;
- постоянный health polling;
- переписывание SPA на другой framework;
- полный mobile-first redesign;
- browser download для каждого backup/export без продуктового решения;
- guided tour раньше базовой продуктовой готовности;
- cloud, OCR, AI/RAG, роли и advanced analytics.

---

## 7. Незакрытые обязательства исходного roadmap

| Обязательство | Фактический статус | Решение до MVP release |
|---|---|---|
| Финальный macOS package | Есть launcher foundation, но нет `.app`/`.dmg` и user-ready запуска | Обязательно |
| Безопасная установка обновления | Backup-before-migration реализован частично, но нет packaged update flow и полного smoke | Обязательно |
| User/remote install checklist | Есть частичные документы, финальный процесс не проверен | Обязательно |
| Restore | Backup создаётся, restore не реализован | Нужно выбрать и реализовать безопасный user/launcher-assisted или support-assisted путь без терминала для пользователя |
| Налоговая настройка | Calculation-sensitive Settings пока закрыты | Обязательно по product spec |
| Себестоимость, налог и маржа | Себестоимость доступна частично; налог и маржа остаются `null`/недоступны | Обязательно |
| AuditLog workspace | Логи пишутся, пользовательского read-only экрана нет | Обязательно либо нужен явный scope amendment |
| Полный release smoke | Есть focused smoke отдельных PR, но нет итогового release-candidate smoke | Обязательно |
| Актуальность документации | Ряд документов всё ещё описывает реализованные функции как будущие | Обязательно поддерживать синхронно |

Эти пункты не являются «полировкой аудита». Они закрывают исходный MVP-контракт.

---

# 8. Gate 0 — завершить PR106

Статус: `DONE`

## Результат

PR106 merged и verified. Hermes browser smoke завершён с verdict `PR106_DETERMINISTIC_SMOKE_PASS_WITH_NON_BLOCKING_FINDINGS`.

Проверено и зафиксировано в state documentation:

- mutation-vs-refresh behavior для Import Apply;
- structured conflict behavior без partial writes и duplicate records;
- Settings save/edit/cancel behavior;
- narrow viewport и keyboard reachability;
- persistent announcer placement outside `#root`.

Gate 0 закрыт. Следующий runtime slice может стартовать только как отдельный focused PR.

---

# 9. CURRENT WINDOW — доверие и ежедневная работа

Текущее окно должно состоять из отдельных последовательных PR.

## Slice A1 — очистка пользовательского технического текста

Статус: `DONE` — реализация и обязательная браузерная smoke-проверка завершены в PR #113.

### Scope

Slice A1 закрыт: опубликованный runtime head проверен, обязательная браузерная smoke-проверка прошла, блокирующих замечаний не осталось.

- убрать постоянный `Локальный API доступен` при нормальной работе;
- оставить понятную recovery-ошибку при недоступности локального приложения;
- убрать PR-лексику и roadmap-текст из runtime;
- исправить stale Import copy с учётом фактического Apply;
- перевести внутренние table names на `/demo-data`;
- исправить stale route/navigation readiness metadata;
- синхронизировать напрямую затронутую user/help документацию.

### Non-goals

- backend behavior;
- новые функции;
- dashboard redesign;
- polling;
- file browser;
- frontend refactor.

### Smoke

`/imports`, `/backups`, `/exports`, `/demo-data`, topbar/offline state; 1440×900 и 390×844.

### Acceptance

Пользователь видит язык продукта, а не репозитория и внутренней архитектуры.

---

## Slice A2 — foundation структурированных ошибок форм

Статус: `DONE — verified and merged in PR #114`

### Реализованные маршруты

- `/clients` create/edit;
- `/ingredients` create/edit.

### Реализованный контракт

- backend остаётся источником истины для validation и бизнес-правил;
- `issues` и `detail` безопасно разбираются;
- technical field names известных полей переводятся на понятные русские labels;
- inline-ошибки показываются рядом с соответствующим полем;
- общий summary используется для нераспределимых и неизвестных ошибок;
- неизвестные вложенные пути не сопоставляются с полями по последнему сегменту;
- введённые данные сохраняются после отклонённого submit;
- stale validation очищается после исправления поля, нового submit, отмены или смены записи;
- backend text обрабатывается как недоверенный текст и экранируется при выводе;
- mutation requests не повторяются автоматически;
- mutation failure отделён от post-save list refresh failure;
- устаревшие ответы не перезаписывают новый контекст формы;
- feedback не перехватывает focus;
- исходный input DOM node, caret и selection сохраняются при отображении validation;
- submit, cancel и переключение записи защищены во время выполняющейся mutation.

### Проверки

- required field;
- invalid email;
- invalid category/unit;
- неизвестный nested field path;
- повторный успешный submit после исправления;
- сохранение введённых значений после validation failure;
- отсутствие duplicate submit;
- mutation success с последующей ошибкой обновления списка;
- сохранение focus, caret и исходного DOM node;
- Clients create/edit;
- Ingredients create/edit;
- dependency-free parser tests: `11/11 PASS`;
- targeted validation DOM tests: `4/4 PASS`;
- одновременный запуск frontend test scripts: `PASS`;
- frontend build: `PASS`;
- targeted backend tests: `29/29 PASS`;
- real Firefox validation smoke: `PASS`;
- JavaScript exceptions: `0`;
- console errors: `0`.

### Acceptance

Пользователь понимает, что исправить, не теряет введённые данные и может продолжить работу с формой без повторного выбора поля.

Проверенный runtime commit:

`8eb5d0c2c116c83d4162d10895268375e0bc1e1e`

---

## Slice A3 — миграция validation contract на критические формы

Статус: `DONE — completed through PR #124 / A3.9 based on product-owner confirmed tests and smoke verification`

A3.1 `/ingredient-lots` create/edit structured validation is DONE: merged in PR #115 at merge commit `8b3ea5f7ab2b880d901250d111f6f5dca369c4b4`.

A3.2 inventory structured validation is DONE: PR #116 merged at `79286f076292645b3e83dfedfccb366dee1777f6`, closed, and browser-smoke verified.

A3.3 Recipe Template and immutable Recipe Version structured validation is DONE: PR #117 merged at `cce60e73670171717d9bfd619cd79e1c0b960fe9`, closed, and browser-smoke verified. Recipe Version edit/delete remains prohibited.

A3.4 Client Recipe structured validation is DONE: PR #118 merged at `1489b0f99602ef08fc1a11ab67549a954f80335d`; exact published head `1a5dcce9a919e2ad2fb803dacdc1608b7ff24a25` passed local exact-head full automated smoke. It covered Client Recipe create and composition update on `/client-recipes` with shared structured backend validation, indexed composition paths, structural row-error invalidation, duplicate-submit protection, create refresh-failure separation, and authoritative composition `PUT` responses.

A3.5 Client Wishes structured validation is DONE: PR #119 merged at `e53e7852c8b384915fb77b59345170c43671151c`; verified runtime head `e19229df1afa74f4470864071e91a0e94a5631cd`; exact-head smoke PASS. It covered Client Wish creation inside the client card only.

A3.6 Client Feedback structured validation is DONE: PR #120 / `A3.6 — Client Feedback structured validation` merged at `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`; published head `e148220ac9ad08a0fd952482a0b293f1f2d22bad`; exact-head smoke verdict `PASS — FULL AUTOMATED SMOKE PASSED`. Scope was Client Feedback create-only inside the client card. Client Feedback remains append-only: this slice added no edit, delete, or historical feedback mutation path.

A3.7 Orders structured validation is DONE: PR #122 merged at `8c4a092d055fd221cb18da901cee9e90106b33a4`; verified runtime head `b44b80bd875ec184bbccfc376f1562ddf25fbb46`; user-provided external smoke verdict `PASS — FULL AUTOMATED SMOKE PASSED`. The smoke verdict is external evidence and must not be described as GitHub Actions evidence.

A3.8 Production Readiness feedback and lifecycle is DONE in PR #123. A3.9 Production Confirmation structured errors and mutation safety is DONE in PR #124 and is the completed A3 implementation baseline based on the product owner's confirmed tests and smoke verification.

Slice A3 is complete. Slice A4 is now the active responsive-table containment stage.

Разбивать на дополнительные PR, если scope становится большим.

Import Apply сохраняет отдельный structured-error contract и не должен быть сплющен generic handler.

### Acceptance

Все основные create/edit сценарии дают видимую русскую recoverable validation feedback.

## Slice A4 — responsive table containment

Статус: `ACTIVE — A4.4b /packaging-items responsive workspace containment`

### Маршруты

- `/clients`;
- `/orders`;
- `/inventory`;
- `/packaging-items`;
- `/ingredient-lots` — A4.1 current focused route.

A4.1 must not change `/orders`, `/clients`, `/inventory`, or `/packaging-items` route implementations. Those routes remain separate A4 follow-ups except for unavoidable passive effects from a shared CSS containment correction, which must be inspected and reported.

A4.1 is DONE via PR #125 (merge commit `50c44ff0919401d51c165d6ebec1266c688bfb08`; runtime head `effb5ee270c9fbddc777e57c41ad0b53acd77f9d`). PR #126 / A4.2 is DONE (merge commit `4487e4044d89d88538226c5b36543e6009f279f9`; runtime head `010bd1bf3791dd6a6d754ea2ed0efdcd2ab564d3`) with product-owner manual responsive verification passed at `1440×900`, `1024×768`, `768×900`, and `390×844`. PR #127 / A4.3 is DONE (merge commit `255703d26d9e166f00f2c9ba3030cf4bc41fe044`; runtime head `1f6930d8f2e3367372a384a51e7d04a3a7c96bee`) with product-owner manual exact-head smoke passed. PR #128 / A4.4a `/inventory` is DONE (merge commit `b89a40f2651f3e2ae7174cfdb7989ddf03a6221e`; runtime head `4a39c815ac8fdb73bc0c7dd5f88d0779e9eb6dd5`) with exact-head responsive smoke passed. PR #129 is merged as a test-only baseline repair. A4.4b `/packaging-items` is the active focused runtime slice. The final cross-route responsive regression remains a separate gate after A4.4b; do not mark Slice A4 DONE.

### Требования

- overflow таблицы ограничен локальным scroll-container;
- вся страница не шире viewport;
- identity/status/actions остаются доступны;
- вторичные колонки можно скрывать только по общей priority policy;
- keyboard actions доступны;
- focus outline не обрезается;
- использовать общий CSS contract;
- не переводить всё в карточки без доказанной необходимости.

### Viewports

- 1440×900;
- 1024×768;
- 768×900;
- 390×844.

### Acceptance

Нет page-level horizontal overflow, включая `/ingredient-lots` на desktop; действия доступны мышью и клавиатурой.

---

## Slice A5 — человекопонятное представление локальных файлов

Статус: `BLOCKED` A4

### Маршруты

- `/backups`;
- `/exports`;
- `/report-documents`;
- `/settings`.

### Основной UI показывает

- имя файла;
- дату и причину/тип;
- `Сохранено локально`;
- понятное название папки приложения;
- уже существующие безопасные open/download actions.

Полный абсолютный путь допускается только во вторичных технических сведениях, если он реально нужен поддержке.

### Non-goals

- arbitrary file browser;
- unrestricted filesystem access;
- cloud upload;
- restore;
- обязательный browser download backup-файлов.

### Acceptance

Пользователь понимает, что файл локальный и где его искать, но не сталкивается с `/tmp`, путями репозитория и внутренними каталогами как с основным содержанием.

---

# 10. NEXT WINDOW — runtime truth и resilience

Детализировать после завершения Current Window.

## B1 — Demo state и operational fixture

Статус: `NEEDS EVIDENCE`

Сначала:

- повторно проверить dual feedback после PR106;
- явно regenerate alerts и purchases;
- проверить fixture на low stock, expiration и order shortage;
- определить: UI copy, fixture или backend rules.

Только после доказательства:

- исправить dual state;
- заменить install form на стабильное installed state;
- улучшить demo fixture, если он не демонстрирует MVP;
- не запускать скрытые mutations при page load.

## B2 — Dashboard operational truth

Статус: `NEEDS EVIDENCE`

Разрешены только:

- active orders;
- critical alerts;
- open purchases;
- recent production;
- backup reminder;
- onboarding/next action.

Без charts, forecasting, analytics и скрытого regeneration.

## B3 — миграция shared feedback на остальные маршруты

Статус: `READY` после PR106 и Current Window

Мигрировать небольшими группами, не одним системным PR:

- dashboard/onboarding/help;
- alerts/purchases;
- backups/reports;
- recipes/clients;
- stock/catalog;
- orders/production history.

Для каждого batch: success, mutation failure, refresh failure, busy, stale-result clearing, keyboard focus.

## B4 — безопасная frontend resilience foundation

Статус: `READY` после validation/feedback foundation

- timeout прежде всего для safe GET;
- без automatic retry non-idempotent mutations;
- render/runtime fallback;
- safe `unhandledrejection` diagnostics без чувствительных данных;
- явный recovery action;
- сохранение stale readable data при failed refresh, где безопасно.

Без health polling и framework migration.

---

# 11. ROADMAP COMPLETION WINDOW

## C1 — calculation-sensitive Settings

Статус: `READY` после пользовательского hardening

Минимум:

- backend-owned tax rate;
- Decimal validation;
- Settings UI;
- audit изменений;
- явное решение по effective date/snapshot;
- отсутствие silent recalculation истории.

Без полноценной бухгалтерии, tax filing и invoices.

## C2 — себестоимость, налог и маржа

Статус: `BLOCKED` C1

- backend domain services;
- readiness estimates с limitations;
- immutable production snapshots;
- reports используют snapshots;
- старые production records не пересчитываются текущими ценами/настройками;
- missing data остаётся `Недоступно`, без выдуманных значений;
- Decimal, migration и backward-compatibility tests обязательны.

## C3 — AuditLog workspace

Статус: `READY` после C2 или раньше, если полностью изолирован

- read-only история;
- русские action labels;
- дата, сущность, safe summary, source/type;
- полезные фильтры;
- без raw JSON, table names, stack traces и sensitive client data;
- без edit/delete.

## C4 — Restore и recovery

Статус: `NEEDS PRODUCT DECISION`

Выбрать:

1. safe user-facing restore в приложении/launcher; либо
2. support-assisted restore без терминала для конечного пользователя.

Обязательно:

- lock/close database;
- валидация backup;
- pre-restore safety copy;
- schema compatibility;
- rollback/recovery;
- явное подтверждение;
- isolated end-to-end smoke.

Без cloud backup, scheduler и arbitrary file access.

---

# 12. DELIVERY WINDOW

## D1 — финальный macOS package

- packaged frontend/backend/runtime;
- localhost-only;
- user data вне package;
- один пользовательский запуск;
- понятная startup failure;
- clean shutdown;
- без терминала и developer paths;
- smoke на чистом Mac user profile.

## D2 — update safety

Обязательный поток:

```text
закрыть старую версию
→ сохранить user-data directory
→ установить новую версию
→ определить pending migration
→ создать before-migration backup
→ выполнить migration
→ записать результат
→ открыть приложение
→ проверить критичные данные
```

Проверить update без migration, с migration и с migration failure.

## D3 — user/remote install

Обновить и проверить:

- `docs/user-install.md`;
- `docs/remote-install-checklist.md`;
- `docs/update-guide.md`;
- `docs/backup-and-restore.md`;
- support checklist для install, first launch, data path, backup, update, recovery и logs.

Конечному пользователю нельзя предлагать Git, terminal, Python или Node.js.

---

# 13. MVP RELEASE GATE

MVP release candidate допускается только после выполнения обязательных условий.

## Функционально

Пользователь без разработчика может:

- открыть packaged app;
- пройти first-run;
- создать и найти backup;
- вести компоненты, партии, тару, рецепты, версии, клиентов, индивидуальные рецепты, пожелания, feedback и заказы;
- проверить readiness;
- выполнить transactional production и увидеть списания/history;
- увидеть себестоимость, налог и маржу;
- использовать alerts и purchases;
- импортировать CSV/XLSX через draft/preview/validation/confirmation/apply;
- экспортировать данные;
- открыть human-readable AuditLog;
- восстановиться через утверждённый MVP restore path;
- обновить приложение без потери данных.

## UI

- нет PR/repository planning language;
- raw paths не являются основным содержанием;
- нет page-level overflow на критических маршрутах;
- core forms показывают recoverable validation;
- feedback/busy semantics согласованы;
- keyboard focus видим и логичен;
- successful mutation не выглядит failed из-за refresh;
- нет duplicate mutation requests;
- Help и onboarding соответствуют runtime.

## Safety

- user data вне package;
- backup до migration;
- import и production transactional;
- история не мутирует silently;
- restore делает safety copy;
- smoke использует isolated data;
- cloud/OCR/multi-user scope не добавлен.

## Итоговый smoke

- clean install и first launch;
- existing-user launch;
- backup и recovery/restore;
- update с migration и без неё;
- полный recipe/client/order/production flow;
- normal и failed Import Apply;
- alerts/purchases generation;
- export/report documents;
- Settings calculations;
- AuditLog read-only;
- desktop/narrow/keyboard;
- restart и data persistence;
- cleanup процессов.

---

## 14. Как поддерживать документ

### `docs/implementation-plan.md`

Содержит подробно только текущее окно из 3–5 slices. После его завершения Current Window переписывается, а не превращается в исторический журнал.

### `docs/roadmap.md`

Остаётся стратегическим документом. Добавить короткую ссылку на `docs/implementation-plan.md`. Менять roadmap только при изменении scope или архитектурного решения.

### `state/current-focus.md`

Только один текущий slice:

- goal;
- allowed scope/files;
- non-goals;
- tests;
- acceptance.

### `state/progress.md`

После merge записывать:

- выполненное;
- реально запущенные tests/smoke;
- known limitations;
- следующий ready slice.

### `state/handoff.md`

Хранить последний verified repo state, published SHA, pending evidence и next task.

### `state/change-requests.md`

Новые пожелания сначала попадают сюда и не добавляются скрыто в активный PR.

---

## 15. Правила задач для Codex

Каждый slice оформляется отдельным английским Codex prompt со стандартными разделами:

- Context;
- Goal;
- Scope;
- Non-goals;
- Architecture constraints;
- Backend requirements;
- Frontend requirements;
- Data model/migrations;
- Tests;
- Documentation;
- Acceptance criteria;
- Required checks;
- PR summary format.

Обязательно:

- не назначать будущий номер PR заранее;
- не объединять несвязанные findings;
- не менять unrelated routes/files;
- не прятать architecture decisions в коде;
- обновлять ADR/architecture при реальном решении;
- запускать backend tests и frontend build;
- выполнять smoke соответствующего уровня;
- различать mutation и refresh failure;
- честно фиксировать недоступные проверки;
- не заявлять browser/keyboard/responsive/migration/restore/package PASS без фактического запуска.

---

## 16. Первое действие после добавления документа

1. Завершить и смержить текущий documentation-only implementation-plan PR.
2. Подготовить английский Codex prompt только для Slice A1.
3. Создать Slice A1 как отдельный focused runtime PR.
4. Не смешивать A1 с validation errors, responsive tables, dashboard, tax/margin, restore или packaging.

## 2026-07-18 — A3.6 Client Feedback structured validation

- Baseline: PR #119 / A3.5 merged at `e53e7852c8b384915fb77b59345170c43671151c`.
- Verified runtime head for PR #119: `e19229df1afa74f4470864071e91a0e94a5631cd`; complete external exact-head smoke: PASS.
- A3.5: DONE.
- A3.6 Client Feedback structured validation: DONE in PR #120; published head `e148220ac9ad08a0fd952482a0b293f1f2d22bad`, merge commit `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`, exact-head smoke PASS.
- Scope was Client Feedback create only; no edit/delete, no migration, no Orders or Production changes.


### A3.9 current runtime slice

Base SHA: `c6d87df635a5cf7d063b43ffc16dc02d64e08103`. PR #123 / A3.8 is merged with accepted runtime head `34eeaf11dbe7fbfabb3bd36ad8aa79b9469892f5`; final A3.8 exact-head smoke was `PASS — FULL AUTOMATED SMOKE PASSED` as external local evidence, not GitHub Actions. A3.9 hardens Production Confirmation structured errors, transactional rollback evidence, duplicate/stale/wrong-order frontend ownership, and success-with-refresh-failure handling. A3.9 is not DONE until human review, exact-head production smoke, and merge. A4 remains separate.
