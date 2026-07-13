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

Статус: `IN PROGRESS`

### Scope

Текущий focused runtime PR реализует Slice A1. Будущий PR number не назначен.

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

Статус: `BLOCKED` A1

### Первые маршруты

- `/clients` create/edit;
- `/ingredients` create/edit.

### Требования

- backend остаётся источником истины;
- `issues/detail` безопасно разбираются;
- technical field names переводятся на русские labels;
- ошибка показывается рядом с полем, где это возможно;
- общий summary используется для нераспределимых ошибок;
- введённые данные сохраняются;
- stale validation очищается после исправления или нового submit;
- backend text экранируется;
- mutation requests не retry автоматически;
- feedback не перехватывает focus.

### Проверки

- required field;
- invalid email;
- invalid category/unit;
- повторный успешный submit после исправления;
- keyboard/focus smoke.

### Acceptance

Пользователь понимает, что исправить, и не теряет введённые данные.

---

## Slice A3 — миграция validation contract на критические формы

Статус: `BLOCKED` A2

Разбивать на дополнительные PR, если scope становится большим.

Кандидаты:

- ingredient lots и stock movements;
- packaging и packaging movements;
- recipes и recipe versions;
- client recipes, wishes, feedback;
- orders и production confirmation;
- Settings profile;
- backup/export/report-document forms.

Import Apply сохраняет отдельный structured-error contract и не должен быть сплющен generic handler.

### Acceptance

Все основные create/edit сценарии дают видимую русскую recoverable validation feedback.

---

## Slice A4 — responsive table containment

Статус: `BLOCKED` A3, если есть overlap по активным frontend-областям

### Маршруты

- `/clients`;
- `/orders`;
- `/inventory`;
- `/packaging-items`;
- `/ingredient-lots`.

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
