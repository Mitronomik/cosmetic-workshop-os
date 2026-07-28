# cosmetic-workshop-os — План доведения MVP до продуктовой готовности

Проект: `cosmetic-workshop-os`
Клиентское название: **Мастерская косметолога**
Целевой путь в репозитории: `docs/implementation-plan.md`
Тип документа: активный рабочий план ближайших окон реализации
Статус: **активен после закрытия Block B и merge PR #141**
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

### Current baseline

- **Current baseline `origin/main`: `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`** (VERIFIED FROM REPOSITORY / GITHUB). This is the **PR #149 merge commit** — the `C1-I` merged baseline — and it is the verified current `origin/main` at the start of PR #150.
- PR #149 — `C1-I — Implement backend-owned tax-rate setting`, state `MERGED`: final reviewed head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`; merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`; merged `2026-07-27T19:44:53Z`.
- Merged `main` backend baseline: `671 collected, 671 passed, 0 failed, 0 skipped`, with all 562 previously merged node IDs still collected (VERIFIED FROM MERGED PR EVIDENCE).
- Accepted `C1-I` frontend evidence: focused tax-setting suite `52 passed, 0 failed, 0 skipped`; all 13 focused frontend suites `568 passed, 0 failed, 0 skipped`; production build `PASS`; exact-head `/settings` smoke `PASS — 146 checks / 0 failures` (VERIFIED FROM MERGED PR EVIDENCE).
- `frontend/src/main.ts` on merged `main`: `6399` lines.

### Current implementation state

`C2-I` merged as PR #151, `C2-II` merged as PR #152 and `C2-III-A` merged as PR #154; all three are `DONE — MERGED AND EXACT-HEAD VERIFIED`. `C2-III-B — snapshot-backed reports and report documents` is `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED` and is the only remaining C2 runtime slice. No implementation PR number is assigned to `C2-III-B`.

`CR-006` remains a `needs evidence` row and is not activated. `CR-004` remains inactive. C3 and C4 remain inactive. Product release readiness is not claimed.

### HISTORICAL RECORD — Block B closure baseline

Retained for traceability. These values described the repository at Block B closure on 2026-07-26 and are **not** the current baseline; the current baseline is `ff7afe6b0778ab2b348229a4df34acf3e3fc0001` above.

**Block B is complete.** B4.1 was the last runtime slice of Block B and is merged.

- Block B closure baseline `origin/main`: `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` — the PR #141 merge commit, merged `2026-07-26` (VERIFIED FROM REPOSITORY / GITHUB).
- PR #141 — `B4.1 — Dashboard safe GET timeout and recovery`: final reviewed head `d0cde127355b146f101ddf3769d76d0226c71ec0`; merge commit `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` (VERIFIED FROM REPOSITORY / GITHUB).
- Accepted Dashboard/Onboarding focused suite for the final reviewed head: `42/42` (SUPPLIED TASK BASELINE).
- Accepted frontend production build: `PASS` (SUPPLIED TASK BASELINE).
- Accepted PR #141 backend branch-only failure delta: `0` (SUPPLIED TASK BASELINE).
- Accepted browser, keyboard, responsive, network, and exact-head smoke: `PASS` — SUPPLIED TASK BASELINE — product-owner-verified exact-head smoke of PR #141 on 2026-07-26.
- Complete backend baseline at that point: `496 collected, 492 passed, 4 failed, 0 skipped` — re-executed from `backend/` in the Block B closure task with zero drift.

The four backend baseline failures were not regressions from PR #141 and were handled by an explicit gate rather than carried as loose findings. The **Pre-release hardening — backend baseline correction gate** window (section 10a) is **DONE**: `R3`, `R2`, and `R4` are all merged, and the backend baseline at that point was green at `562 collected, 562 passed, 0 failed, 0 skipped`. The `C1` window then completed on top of it, taking the baseline to `671 / 671 / 0 / 0`.

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
| Налоговая настройка (`default_tax_rate`) | **ЗАКРЫТО.** Настройка реализована и редактируема: `GET`/`PUT /api/settings/tax-rate`, ключ `default_tax_rate`, merged `C1-I` / PR #149. C1 завершён. Это **единственная** редактируемая calculation-sensitive настройка; остальные (валюта, целевая маржа, порог остатка, дни предупреждения о сроке, единицы измерения) по-прежнему закрыты и требуют отдельно принятых backend-правил | Выполнено — `CR-007` / `C1-I`, PR #149 merged `2026-07-27` |
| Себестоимость, налог и маржа (расчёты и снапшоты) | **ЧАСТИЧНО.** Оценка готовности считает налог, маржу и процент маржи (`C2-I`, PR #151); неизменяемые снапшоты `ProductionBatch` персистятся в транзакции подтверждения производства (`C2-II`, PR #152); финансовое представление в UI заказов и `ProductionBatch` влито (`C2-III-A`, PR #154). Отчёты снапшоты пока не читают | Обязательно — контракт принят как `CR-008`; `C2-I`, `C2-II` и `C2-III-A` влиты; `C2-III-B` (отчёты) авторизован после влития документационного PR закрытия и не реализован |
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

# 9. COMPLETED WINDOW — доверие и ежедневная работа

Это окно было выполнено отдельными последовательными PR.

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

Статус: `DONE`

### Маршруты

- `/clients`;
- `/orders`;
- `/inventory`;
- `/packaging-items`;
- `/ingredient-lots` — A4.1 current focused route.

A4.1 must not change `/orders`, `/clients`, `/inventory`, or `/packaging-items` route implementations. Those routes remain separate A4 follow-ups except for unavoidable passive effects from a shared CSS containment correction, which must be inspected and reported.

A4.1–A4.4 are complete. The final B3 integration smoke also passed the desktop, narrow-width, and keyboard scenario after the Backups-specific blocker was closed by PR #139.

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

Статус: `DONE`

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

# 10. COMPLETED WINDOW — runtime truth и resilience (Block B)

Статус: `DONE`

Это окно закрыто полностью: B1, B2, B3 и B4 завершены. Активное окно теперь — section 10a, backend baseline correction gate.

## B1 — Demo state и operational fixture

Статус: `DONE — diagnostic gate closed; no correction PR required`

Accepted diagnostic outcome:

- demo-data installation is explicit;
- duplicate installation is safely rejected;
- alert and purchase-suggestion regeneration is stable;
- the operational fixture is meaningful;
- passive reads do not mutate the database;
- no separate fixture/backend correction PR was required.

Any later newly discovered Demo Data product request must enter through `state/change-requests.md`; it does not silently reopen B1.

## B2 — Dashboard operational truth

Статус: `DONE — diagnostic gate closed; no backend read-model correction required`

Accepted diagnostic and verification outcome:

- the Dashboard backend read-model diagnostic gate is complete;
- no backend read-model correction PR was required;
- the accepted B3.1 exact-head smoke subsequently verified Dashboard initial load, manual refresh, stale-data preservation, initial-load failure, explicit retry, route ownership, keyboard focus, and responsive browser behavior;
- the final B3 integration smoke also passed its Dashboard, onboarding, Help Center, and route-matrix scenario;
- charts, forecasting, advanced analytics, hidden regeneration, and hidden mutations remain outside scope.

## B3 — миграция shared feedback на остальные маршруты

Статус: `DONE`

Completed in bounded groups:

- dashboard/onboarding/help;
- alerts/purchases;
- backups/reports;
- recipes/clients;
- stock/catalog;
- orders/production history.

For each batch, success, mutation failure, refresh failure, busy state, stale-result clearing, and keyboard focus were covered. B3.1–B3.6 are complete through PR #138. The Backups narrow-width blocker found during the first full-smoke attempt was fixed by PR #139, and the final integration smoke for the implemented B3 scope passed on exact published head `9ee94810f4dddbc03faf8c7cdbe188faa43a4e72`.

B3 implementation and its deferred full integration-smoke gate are complete.

## B4 — безопасная frontend resilience foundation

Статус: `DONE`

### B4 limitation — deliberately deferred scope

B4 is closed with the Dashboard safe-GET pilot only. Safe GET timeout and recovery coverage for the remaining read routes, including but not limited to Alerts, Purchases, Orders, Reports, Backups, Exports, and Report Documents, was deliberately deferred and was not delivered. Any future expansion requires a separately authorized slice and a change request. Closing B4 does not imply that those routes are protected against an indefinitely hanging local GET.

B4.1 was the only approved B4 runtime slice. **No approved B4.2 contract exists, no B4.2 section exists, and no B4.2 slice is authorized.**

### B4.1 — Safe GET timeout and recovery foundation

Статус: `DONE`

- PR #141 — `B4.1 — Dashboard safe GET timeout and recovery` — merged `2026-07-26`.
- Final reviewed head: `d0cde127355b146f101ddf3769d76d0226c71ec0`.
- Merge commit: `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa`.
- Accepted Dashboard/Onboarding focused suite: `42/42` (SUPPLIED TASK BASELINE).
- Accepted frontend production build: `PASS` (SUPPLIED TASK BASELINE).
- Accepted backend branch-only failure delta: `0` (SUPPLIED TASK BASELINE).
- Accepted exact-head smoke: `PASS` — SUPPLIED TASK BASELINE — product-owner-verified exact-head smoke of PR #141 on 2026-07-26; not re-run in this documentation task.

Delivered: a bounded timeout and recovery contract for explicitly selected safe frontend GET/read operations without changing backend business rules or introducing mutation retries.

Initial bounded pilot:

- Dashboard initial read;
- Dashboard manual refresh;
- one composed Dashboard read owner/request generation for all required source GET requests;
- atomic snapshot commit only after every required source result for the same generation validates successfully;
- no partial or mixed new snapshot when any required source times out or fails;
- explicit timeout feedback and manual retry/refresh;
- preservation of the previous coherent Dashboard snapshot after failed/timed-out refresh where safe;
- explicit recoverable initial-load failure when no previous snapshot exists;
- rejection of stale and late individual-source results after timeout, supersession, route leave, or a newer request;
- no late individual-source success or failure may mutate Dashboard state, feedback, announcements, focus, or busy state;
- route/context ownership;
- reuse and extension of the existing `DashboardOnboardingFeedbackLifecycle` and current API client boundary rather than a second lifecycle system or global fetch rewrite.

Manual retry creates a clean new composed read generation. Duplicate starts remain rejected, busy state settles exactly once, and no timeout authorizes an automatic retry.

The B4.1 runtime uses one explicit `8_000 ms` deadline for the complete composed Dashboard read. All five required GET requests start concurrently with one opt-in `AbortSignal`; the deadline does not multiply by source count. The coordinator commits only one fully validated candidate snapshot and releases its timer/controller ownership exactly once. The launcher completes database initialization before starting the backend, then waits one second and checks that the process remains alive before opening the browser; it does not perform a health-readiness poll. The eight-second localhost deadline therefore also bounds that small remaining startup-readiness gap without creating polling or a global timeout.

Required runtime evidence:

- focused timeout/lifecycle tests for one required source timing out while the other source reads succeed;
- one required source failing while the other source reads succeed;
- no partial or mixed snapshot;
- previous coherent snapshot retained after refresh timeout;
- initial timeout without previous data;
- late individual-source callback rejection;
- retry creating a clean new request generation;
- timeout and busy settlement exactly once;
- explicit recovery, no automatic retry, and route/context change;
- proof that mutation request paths are not wrapped or retried;
- existing Dashboard/Onboarding regressions;
- frontend production build;
- exact-head Dashboard browser smoke at desktop and narrow widths, including keyboard focus, intentional delay fault injection, manual recovery, retained snapshot, late-result rejection, and zero unexpected browser/network failures.

No source timeout may authorize an automatic retry, and no mutation path may use the safe-GET timeout primitive.

Non-goals: onboarding mutations, Alerts mutations, Purchases mutations, production, Import Apply, stock movement creation, backup/export/report generation, other mutation flows, health polling, hidden polling, automatic mutation retry, global request rewrite, cloud/offline sync, framework migration, backend/API/schema/migration changes, and new dependencies.

---

# 10a. CLOSED WINDOW — Pre-release hardening: backend baseline correction gate

Статус: `DONE`

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with the documented date-normalization contract`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED / DECIDED / IMPLEMENTED**; decision PR #145 merged 2026-07-27 at merge commit `bef36822e50c245b72f813dad0afbffc7f772588` from final reviewed head `7d68b45bee1f223b67f105c30e3acbb89dc8d41d`
- `R4 — Canonical backup/export filename reason normalization`: **DONE**; PR #146 merged 2026-07-27 at merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453` from final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`
- Backend baseline correction gate: **DONE** — all four accepted gate failures are closed on `main`
- Merged `main` backend baseline: **GREEN** — `562 collected, 562 passed, 0 failed, 0 skipped`
- **No active runtime implementation slice at the time this window closed.** *(Superseded: the `C1` window then ran and completed — `CR-007` merged as PR #148 and `C1-I` merged as PR #149. The current implementation state is section 3: no runtime implementation is active in PR #150, and `C2-I` becomes the only authorized runtime slice after PR #150 merges.)* No future PR number is assigned.
- `CR-006 — Investigate export create-response fallback confirmation semantics`: **`needs evidence`**, non-blocking, **not activated** — see the `CR-006` subsection below

## R3 closure record

`R3` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB).

- PR #143 `R3 — Repair purchase-suggestions API smoke seeding`, state `MERGED`.
- Final reviewed head: `c5fc27059a7aea0435c84535d2d15e6a0fc58428`.
- Merge commit: `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`.
- Merged at: `2026-07-27T04:01:23Z`.
- Accepted `R3` backend result: `496 collected, 493 passed, 3 failed, 0 skipped`.
- No production code changed in `R3`; the slice was test-only, one changed value on one line.

`R3` is no longer active. Exactly one slice is active and it is `R2`.

## R2 implementation record

`R2` is implemented on its own PR branch, from starting `origin/main` `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`, and is **not merged and not DONE**.

- Exact runtime/test change: one assertion block inside `backend/app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`:

```diff
-    assert body["draft"]["error_count"] >= 4
+    assert body["draft"]["error_count"] == 3
+    assert body["draft"]["warning_count"] == 1
+    assert body["draft"]["apply_readiness"]["can_apply"] is False
     assert {issue["code"] for issue in body["issues"]} >= {"missing_required_column"}
     row_codes = {issue["code"] for issue in body["preview_rows"][0]["issues"]}
-    assert {"invalid_decimal", "invalid_unit", "invalid_date"} <= row_codes
+    assert row_codes == {
+        "invalid_decimal",
+        "invalid_unit",
+        "date_format_normalized",
+    }
```

- The response status assertion, the request payload, the CSV data, the date `05.07.2026`, the target type, and the global `missing_required_column` assertion are unchanged. The corrected assertions are strictly more specific than the ones they replace: an exact `error_count`, an exact `warning_count`, an explicit blocked-apply assertion, and an exact row-code set instead of a subset.
- No production file changed. `_normalize_date_value`, readiness calculation, issue counting, required-column behavior, `missing_required_value`, import Apply, and the import preview/confirmation flow are untouched, and `docs/import-format.md` was not modified.
- Executed backend evidence, run from `backend/` with Python `3.12.13`, pytest `8.4.2`, rootdir `backend/`, configfile `pyproject.toml`, in a temporary environment outside the repository, removed and verified absent afterwards:
  - pre-change complete suite `496 collected, 493 passed, 3 failed, 0 skipped`, failing exactly the three accepted post-`R3` gate nodes;
  - pre-change isolated target node returned `201` and failed at `assert 3 >= 4` at `backend/app/tests/test_imports_api.py:107`, with observed `error_count` `3`, `warning_count` `1`, readiness `blocked`, `can_apply` `false`;
  - post-change isolated target node `PASSED` twice;
  - post-change `app/tests/test_imports_api.py` `7 passed`;
  - post-change `app/tests/test_import_parsing.py` `16 passed`, proving `date_format_normalized` still works and genuinely invalid dates still emit `invalid_date`;
  - post-change complete suite `496 collected, 494 passed, 2 failed, 0 skipped`.
- Expected remaining failures, exactly two and no others:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

- The backups and exports filename nodes remain blocked on the `CR-005` product decision and still have no slice. **The filename implementation is not authorized here**, and it must not be started from the unmerged `R2` branch.
- `CR-004` remains a separate `needs evidence` row and is not activated.
- C1, C2, C3, and C4 remain inactive.
- Packaging smoke and release smoke remain blocked. Product release readiness is not claimed.

## R2 closure record

`R2` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB).

- PR #144 `R2 — Align import draft baseline test with date normalization`, state `MERGED`.
- Final reviewed head: `52e2c64fc601b458cfd60e8b86a778efabd65671`.
- Merge commit: `8efbdc5c85b5932f4aeef51045542c207cf4635c`.
- Merged at: `2026-07-27T04:21:16Z`.
- Accepted `R2` backend result: `496 collected, 494 passed, 2 failed, 0 skipped` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — not re-executed).
- No production code changed in `R2`; the slice was test-only.

The pre-merge `R2` implementation record above is preserved unchanged and is superseded by this closure record, not edited. Nodes 3 and 4 are closed. The two remaining backend failures are exactly the filename-reason nodes:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

## CR-005 — accepted product decision

`CR-005 — Decide the backup/export filename normalization and hyphen round-trip contract` is **accepted** (RECORDED PRODUCT-OWNER DECISION, 2026-07-27). The durable contract lives in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`. Summary:

**Two representations.** The *human reason* is the normalized user text, `text = (reason or "manual").strip() or "manual"`. The *filename reason segment* is a canonical, path-safe, unambiguous slug derived from it. They must not be silently conflated.

**Canonical algorithm** for newly created backups and exports: preserve Unicode alphanumerics exactly; treat underscore and every non-alphanumeric character as a separator, including whitespace, hyphen, dot, slash, backslash, punctuation, and symbols; collapse each maximal run of separators to one underscore; strip leading and trailing underscores; use `manual` when the result is empty; prefix a digits-only result with `reason_`; preserve letter case; no lowercasing, no transliteration, and no new length limit.

| Input | Canonical segment |
|---|---|
| `before/update ../unsafe` | `before_update_unsafe` |
| `before-import` | `before_import` |
| `___before---import___` | `before_import` |
| `перед обновлением` | `перед_обновлением` |
| `123` | `reason_123` |
| whitespace only | `manual` |
| punctuation only | `manual` |

**Hyphen.** Literal hyphens are not allowed inside a newly generated filename reason segment and normalize to underscore, because the hyphen is already a structural filename separator, backup metadata parsing splits on it, allowing it makes the round trip ambiguous, and the uniqueness suffix is also a hyphen plus a number. Hyphens remain allowed in the human reason and in the export manifest reason.

**Numeric-only.** A filename reason segment is never purely numeric; a numeric-only human reason receives the `reason_` prefix, so a reason such as `123` cannot be confused with the numeric uniqueness suffix `-1`, `-2`, `-3`.

**Grammar preserved.** No new filename version, marker, sidecar format, or migration. New names remain conceptually `{timestamp}-{safe_source_stem}-{canonical_reason}[-N].{sqlite_suffix}` and `{timestamp}-cosmetic_workshop-export-{canonical_reason}[-N].json`, with `-N` reserved solely for uniqueness and existing non-overwrite behavior unchanged.

**Round trip.** For newly generated artifacts the create, list, and status reasons are all the same canonical segment, the visible UI reason resolves from that same segment, and the uniqueness suffix is never part of the reported reason. The source database stem keeps its own separate sanitization and may still contain hyphens; the implementation must prove a hyphenated stem does not break canonical reason parsing.

**Displayed reason.** Filename-derived, taken from the existing API `reason` field. No database metadata table, sidecar metadata file, new API field, frontend-only reconstruction rule, or hidden persistent metadata. The contract has two layers and both are preserved: the **backend/API `reason` is the canonical slug** and the single source of truth, and the **frontend consumes that slug without reconstructing, sanitizing, or normalizing it**, presenting **known system slugs** through the **existing localized Russian display labels** and rendering **custom or unmapped slugs verbatim**. The visible label is therefore not always literally the canonical slug — canonical `before_import` renders as `Перед импортом`, canonical `before_update_unsafe` renders verbatim. Exact per-screen mappings: `docs/backup-and-restore.md` and `docs/export.md`. No Russian label is added, removed, or reworded by this decision.

**Export manifest.** Continues to preserve the normalized human reason, not the filename slug. The export schema version does not change.

**Legacy compatibility.** Existing artifacts are not renamed, rewritten, or deleted; no database or filesystem migration. Legacy listing stays best-effort and must preserve filename, path, created-timestamp fallback, size, and list availability. Exact round-trip recovery is not claimed for legacy ambiguous filenames.

**Shared helper boundary.** One shared backend helper — recommended `normalize_artifact_reason_segment(value: str | None) -> str` in `backend/app/services/local_artifact_filenames.py`. An equivalently named narrowly scoped module is permitted only where repository conventions strongly require it, and the implementation PR must explain the choice. The helper applies only to backup and export filename reason segments — never to backup source database stems, report-document reasons or filenames, arbitrary uploaded filenames, recipe names, client names, or any unrelated domain value. `backend/app/services/report_documents.py` has a deliberately different contract and is **not** unified into it.

## Post-decision classification of the two remaining nodes

The original diagnostic evidence and its classification at diagnosis time are preserved unchanged in `docs/backend-baseline-failure-triage.md` §5, §6, and §9. The decision supersedes, but does not rewrite, that history.

| Node | Post-decision classification | Severity | Impact |
|---|---|---|---|
| Node 1 — backups filename reason | **PRODUCT DEFECT — CONTRACT MISMATCH** | MEDIUM | user-visible filename/reason-label mismatch; ambiguous round-trip for hyphenated reasons; backend baseline failure; no proven data loss; no source database mutation; no overwrite regression |
| Node 2 — exports filename reason | **PRODUCT DEFECT — CONTRACT MISMATCH** | MEDIUM | user-visible filename/reason-label mismatch; filename slug inconsistent with the decided contract; backend baseline failure; export manifest remains readable; no proven data loss; no overwrite regression |

Shared root cause: duplicated one-character-at-a-time sanitizers that both preserve the hyphen in the reason segment and both lack the decided run-collapse and numeric-disambiguation rules. The two nodes now share one decided contract and are corrected in **one** bounded slice.

## R4 — Canonical backup/export filename reason normalization

Статус: `DONE`

### R4 lifecycle closure

`R4` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). Nothing in this closure subsection was executed in the documentation task that wrote it.

- PR #146 `R4 — Canonical backup/export filename reason normalization`, state `MERGED`.
- Final reviewed head: `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`.
- Merge commit: `127191feb182ccf68a4d7b9f2be28f6aa5b42453`.
- Merged at: `2026-07-27T08:51:06Z`.
- `origin/main` equals that merge commit; both the final head and the merge commit were verified as ancestors of `origin/main`.

Accepted merged evidence:

| Check | Accepted result |
|---|---|
| Backend complete suite | `562 collected, 562 passed, 0 failed, 0 skipped` |
| Frontend focused suite | `40 passed, 0 failed, 0 skipped` |
| Frontend production build | `PASS` |
| Focused exact-published-head `/backups` and `/exports` browser smoke | `PASS — FULL AUTOMATED SMOKE PASSED` |
| Exact smoke-tested head | `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb` |

The merged slice involved no frontend production change, no database migration, no filesystem migration, and no existing artifact renamed, rewritten, or deleted.

**The backend baseline correction gate is DONE.** All four accepted gate failures are closed on `main`, and the two filename-reason nodes were the last open ones. The merged `main` backend baseline is **green**. `CR-005` remains accepted and is now implemented; neither `CR-005` nor `R4` is reopened.

**No active runtime implementation slice is selected here.** Selecting the next slice requires a separate authorized task. No future PR number is assigned.

### CR-006 — export create-response fallback — NEEDS EVIDENCE, not authorized

`CR-006 — Investigate export create-response fallback confirmation semantics` is recorded as a **`needs evidence`** row in `state/change-requests.md`. It is **non-blocking**, is **not an active implementation slice**, and **its implementation is not authorized**.

Exact current behavior in `backend/app/api/exports.py::create_export`: after `create_json_export` writes an export, the endpoint attempts to find the exact created file through `list_export_files`; when the exact file is found, the response uses parsed filename metadata and therefore returns the canonical filename-derived reason; when the exact file is **not** found, the defensive fallback constructs an `ExportFile` using `ExportResult.reason`, which is the normalized **human** reason preserved in the export manifest. The fallback may therefore return a human reason where the API contract normally expects the canonical filename-derived slug.

This is **not** a confirmed product defect. No user-visible failure has been reproduced, no data loss, overwrite, incorrect file content, or unsafe mutation is proven, fallback reachability is not established, **no severity is assigned**, and **no correction design is authorized**. A future diagnostic must first establish reachability — artifact disappearance after write, a filesystem race, a permission or `stat` failure, a list/read failure, or mocked or injected repository/service behavior — and then establish the desired contract: return a canonical reason, fail explicitly because the created artifact cannot be confirmed, or another documented outcome. Do not prescribe an implementation before both are established.

`CR-006` is not part of `CR-004`, is not a reason to reopen `CR-005`, is not a reason to reopen `R4`, and is not a fifth backend baseline failure. Evidence: `docs/backend-baseline-failure-triage.md` §17.

### Remaining open work after R4

None of these is activated here.

- `CR-004` — SQLite backup transaction-consistency investigation — remains a separate `needs evidence` row.
- Restore product decision and implementation remains **open**.
- Final macOS packaging and user-ready launch remains **open**.
- Installation verification remains **open**.
- Packaged update flow and update smoke remain **open**.
- Full release-candidate smoke remains **open**.
- C1, C2, C3, and C4 remain **inactive**.
- Continuing documentation accuracy remains an ongoing obligation. The durable `CR-005` contract documents `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md` record the merged `R4` implementation status and agree with merged `main`.

**Product release readiness is not claimed.**

### R4 pre-merge branch record — historical, superseded by the closure above

The record below describes the state at the time `R4` was implemented on its branch. It is preserved unchanged as history and is superseded, not edited, by the closure subsection above.

The `CR-005` decision pull request #145 is **merged** (final reviewed head `7d68b45bee1f223b67f105c30e3acbb89dc8d41d`, merge commit `bef36822e50c245b72f813dad0afbffc7f772588`), which was the precondition for starting `R4`. `R4` is implemented on branch `claude/r4-canonical-artifact-reason-normalization`, created directly from `origin/main` at `bef36822e50c245b72f813dad0afbffc7f772588`.

**`R4` is not DONE.** It is not merged and not reviewed. The backend correction gate stays open until `R4` is reviewed and merged. The final pre-merge gate is the focused `/backups` and `/exports` browser smoke against the exact published pull-request head; a passing smoke is invalidated by any later commit.

Completed on the branch at the time this record was written:

- backend: the complete suite from `backend/` gives `562 collected, 562 passed, 0 failed, 0 skipped` (pre-change baseline `496 collected, 494 passed, 2 failed, 0 skipped`); both former baseline nodes pass; all 496 previously collected node IDs are still collected;
- frontend: `npm run test:local-artifacts-reports-feedback` gives `40 pass, 0 fail, 0 skipped` and `npm run build` succeeds; no frontend production file changed;
- browser smoke: **not executed at commit time** — it runs only after publication, against the exact published head.

`CR-004` remains separate and unresolved. C1, C2, C3, and C4 remain inactive. Packaging and release-candidate smoke remain blocked, and product release readiness is not claimed.

### Scope

- add one narrowly scoped shared backend reason-segment helper;
- use it for newly generated backup reason segments;
- use it for newly generated export reason segments;
- preserve backup source-stem behavior;
- preserve the existing filename grammar;
- preserve uniqueness behavior;
- make create/list/status metadata round-trip match the decided contract;
- add focused regression coverage;
- close both remaining backend failures.

### Non-goals

No database schema or migration; no artifact rename or migration; no sidecar metadata; no new API field; no API response-shape change; no export schema-version change; no frontend redesign; no report-document sanitizer change; no restore implementation; no SQLite backup transaction-consistency investigation; no `CR-004` work; no cloud sync; no OCR; no roles or multi-user support; no accounting expansion; no C1, C2, C3, or C4 work; no packaging or release work.

### Architecture constraints

- the backend owns filename normalization;
- the frontend must not independently reconstruct, sanitize, or normalize the slug; it may only present it, mapping known system slugs to the existing Russian labels and rendering unmapped slugs verbatim;
- one shared helper owns the backup/export reason-segment contract;
- source database stem sanitization remains separate;
- report-document behavior remains separate;
- existing artifacts remain untouched;
- non-overwrite guarantees remain intact;
- API response schemas remain intact;
- the export manifest keeps the normalized human reason;
- new backup/export API reason values are canonical filename-derived segments.

### Backend requirements

The implementation should normally be bounded to:

```text
backend/app/services/local_artifact_filenames.py
backend/app/services/backup.py
backend/app/services/export.py
```

A parser change **inside those same service modules** is allowed only where required for the exact new-file round-trip contract. No other production surface is authorized without explicit evidence and an updated contract. A filename-format migration must not be authorized merely to simplify parsing.

### Frontend requirements

**No frontend production change is expected.** `R4` is nevertheless allowed to make **focused frontend test-only changes**, because the canonical-reason display contract is not currently proven by any runnable suite.

Current state, verified from the repository:

- `npm run test:local-artifacts-reports-feedback` is runnable and its tsconfig already compiles `src/local-artifact-presentation.ts`, but the suite uses `reason: 'manual'` only as fixture data and asserts nothing about reason presentation;
- `frontend/test/local-artifact-presentation.test.mjs` exists but is **not runnable**: it imports from `dist-tests/local-artifact-presentation/`, and no tsconfig emits to that path and no npm script invokes it;
- the Russian display mapping itself lives in `backupReasonLabelRaw` / `exportReasonLabelRaw` in `frontend/src/main.ts`, which is not included in any focused test tsconfig.

`R4` must therefore do **one** of the following:

- **Preferred** — add focused reason-presentation assertions to the existing runnable `frontend/test/local-artifacts-reports-feedback.test.mjs` suite.
- **Alternative** — make the standalone local-artifact-presentation suite runnable through an exact tsconfig and npm script, **without adding dependencies**.

The `R4` frontend tests must prove:

1. an unmapped canonical slug such as `before_update_unsafe` is rendered **verbatim**;
2. a known canonical system slug uses the **existing localized Russian display mapping**;
3. the frontend does **not** reconstruct, sanitize, or normalize the slug;
4. no frontend production behavior changes unless implementation evidence proves such a change is required **and the contract is updated first**.

Point 2 is the one to scope carefully: the mapping functions are currently in `frontend/src/main.ts` and are not reachable from a focused suite. If proving point 2 turns out to require a production change — for example extracting the existing mapping into a testable module — that change is **not** pre-authorized. `R4` must first record the implementation evidence and update this contract, per point 4. Existing Russian label text must not be introduced, removed, or reworded.

The frontend production build requirement stands: `cd frontend && npm run build`.

### Tests

The two existing failing tests must be preserved and made to pass **without being weakened**. Focused coverage must be added for at least:

1. unsafe run collapse — `before/update ../unsafe` → `before_update_unsafe`;
2. hyphen normalization — `before-import` → `before_import`;
3. mixed separator collapse — `___before---import___` → `before_import`;
4. Unicode — `перед обновлением` → `перед_обновлением`;
5. numeric-only — `123` → `reason_123`;
6. empty and unsafe-only fallback — `manual`;
7. backup create/list/status round-trip;
8. export create/list/status round-trip;
9. duplicate filename suffix excluded from the metadata reason;
10. backup source stem containing hyphens;
11. export manifest preserving the normalized human reason;
12. existing artifact non-overwrite behavior;
13. legacy artifact listing without rename, deletion, or crash;
14. current default `manual` behavior.

No existing test may be deleted, renamed, skipped, `xfail`-ed, or weakened. The complete backend suite must be run from `backend/`. Because new tests are added, the old collection count of `496` is **not** required to stay exact.

### Smoke

Focused browser smoke against the final published implementation head, using an isolated temporary user-data directory, an isolated temporary SQLite database, an isolated browser profile, no real user data, and evidence kept outside Git.

Create one backup and one export through the backend/API using a reason such as `before-update ../unsafe`, then verify:

The smoke reason is chosen deliberately: `before_update_unsafe` is an **unmapped** canonical slug, so its visible label must be the slug rendered verbatim.

**`/backups`** — the route loads; the created artifact appears; the filename contains `before_update_unsafe`; the visible reason label equals exactly `before_update_unsafe`; the value stays correct after route reload or refetch; the uniqueness suffix is not part of the reason; no unrelated file is overwritten.

**`/exports`** — the route loads; the created artifact appears; the filename contains `before_update_unsafe`; the visible reason label equals exactly `before_update_unsafe`; the value stays correct after route reload or refetch; the export manifest still contains the normalized human reason `before-update ../unsafe`; no unrelated file is overwritten.

**Browser evidence** — desktop viewport `1440 × 900`; zero unexpected console errors; zero unexpected console warnings; zero page errors; zero unexpected HTTP failures; zero unexpected request failures; no horizontal page overflow caused by the rendered filename or reason; no production data beyond the intended temporary artifacts.

Full release smoke must not be claimed.

### Acceptance criteria

- every collected backend test passes;
- `0 failed`;
- `0 skipped`;
- neither of the two former baseline nodes remains failing;
- no existing test is removed;
- the decided canonical contract holds for collapse, hyphen, numeric-only, fallback, case, and Unicode;
- create/list/status reasons are the canonical filename-derived segment and exclude the uniqueness suffix, and the UI label resolves from that segment — verbatim when unmapped, through the existing Russian mapping when it is a known system slug;
- the focused frontend tests prove verbatim rendering of an unmapped slug, the existing mapping for a known system slug, and that the frontend does not reconstruct the slug;
- the export manifest still carries the normalized human reason;
- existing artifacts are neither renamed nor migrated, and legacy listing still works;
- the required frontend focused suites and production build pass;
- the required focused browser smoke passes with the evidence listed above.

`CR-004` remains separate and inactive. C1, C2, C3, and C4 remain inactive. Packaging smoke and release smoke remain blocked, and product release readiness is not claimed.

Block B is complete. C1, C2, C3, and C4 remain inactive. Current work is release hardening, not feature expansion. Packaging is blocked and release smoke is blocked.

The gate covers exactly these four node IDs:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues
app/tests/test_purchase_suggestions.py::test_manual_api_smoke
```

## Diagnostic outcome

The complete backend baseline was re-executed from `backend/` with Python `3.12.13` and pytest `8.4.2` (rootdir `backend/`, configfile `pyproject.toml`) and reproduced `496 collected, 492 passed, 4 failed, 0 skipped` with zero drift. Each named node ran twice in isolation and each surrounding test file ran completely. All four failures are deterministic. Full evidence: `docs/backend-baseline-failure-triage.md`.

| Node | Classification | Severity | Setup vs call |
|---|---|---|---|
| backups reason sanitization | `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED` | `NOT DETERMINED FROM CURRENT EVIDENCE` | call — API reached, file created |
| exports reason sanitization | `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED` | `NOT DETERMINED FROM CURRENT EVIDENCE` | call — API reached, file written |
| import draft issue count | `TEST DEFECT` | MEDIUM | call — draft created, assertion stale |
| purchase suggestions manual API smoke | `TEST DEFECT` | MEDIUM | setup/arrange — API never reached |

The backups and exports nodes are `INCONCLUSIVE` because the product documentation does not currently define whether consecutive unsafe characters in a filename reason must collapse to a single underscore. The tests require collapsing; the services substitute one underscore per replaced character. **The production behavior is not stated to be wrong.** Deciding the contract is a product decision, not a further diagnostic, and it is tracked as a `needs product decision` change request. No severity, root cause, or correction surface is asserted for those two nodes.

**This table records the classification at diagnosis time and is preserved as history.** `CR-005` has since been decided, `R2` has merged, and nodes 1 and 2 are reclassified as `PRODUCT DEFECT — CONTRACT MISMATCH` (MEDIUM) — see *Post-decision classification of the two remaining nodes* above and `docs/backend-baseline-failure-triage.md` §14.

No node showed data loss or unsafe mutation. Import integrity and the zero-quantity stock-movement domain rule were verified intact. For the two undecided nodes the following were recorded as observed facts rather than as impact findings: traversal characters are neutralized, existing artifacts are not overwritten, the filename charset is restricted, and the source database is not modified.

## Bounded correction sequence

1. `R3` — **DONE**. Repair purchase-suggestions API smoke seeding (test-only). PR #143 merged 2026-07-27 at merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec` from final reviewed head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`.
2. `R2` — **DONE**. Align the import draft baseline test with the documented date-normalization contract (test-only). PR #144 merged 2026-07-27 at merge commit `8efbdc5c85b5932f4aeef51045542c207cf4635c` from final reviewed head `52e2c64fc601b458cfd60e8b86a778efabd65671`.
3. `R4` — **DONE**. Canonical backup/export filename reason normalization, covering nodes 1 and 2 in one bounded slice. Unblocked by the accepted `CR-005` decision, which merged as PR #145. PR #146 merged 2026-07-27 at merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453` from final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`; accepted merged backend result `562 collected, 562 passed, 0 failed, 0 skipped`; focused exact-head `/backups` and `/exports` browser smoke `PASS` against `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`. Contract and closure above.

The bounded correction sequence is complete and the gate is **DONE**. No successor runtime slice is selected here.

`R3` and `R2` tied on primary priority; `R3` preceded `R2` on greater direct user/data impact because it restored execution of a real no-mutation guarantee that was unverified at the API layer. Both were fully evidenced from repository sources alone and needed no product decision, which is why one could be activated while the filename nodes could not. `R3` and `R2` are both now merged and DONE. Slice contracts live in `state/current-focus.md` and `docs/backend-baseline-failure-triage.md`.

`R3` and `R2` were test-only, so their required smoke was the **backend suite only**. `R4` is different: it changes runtime services, so it additionally requires the focused frontend suites, the frontend production build, and the focused `/backups` and `/exports` browser smoke specified in the `R4` contract above.

## Separate candidate — not activated

**Potential backup consistency finding — not classified or activated.**

The current backup helper copies the SQLite database file through `shutil.copy2`, and the startup before-migration path uses the same helper. This raises a transaction-consistency question when the database may be live or use auxiliary SQLite files. Some existing tests pass ordinary bytes rather than a real SQLite database to the helper, so a future diagnostic must inspect those fixtures.

This task records only the need for a separate evidence-based diagnostic.

Do not classify the behavior as unsafe and do not prescribe a correction design here.

## Remaining release obligations

Clearing these four failures does **not** make the product release-ready. The following stayed outside the backend baseline correction gate and were not activated by it: final macOS `.app`/`.dmg` and user-ready launch; packaged update flow and update smoke; verified user/remote installation process; Restore product decision and implementation; C1 tax setting; C2 cost, tax, and margin completion; C3 user-facing read-only AuditLog workspace; full release-candidate smoke; continued documentation accuracy. See section 7 and sections 11–13.

> **Status update.** The C1 tax setting has since been completed separately: `CR-007` merged as PR #148 and `C1-I` merged as PR #149, so C1 is `DONE`. C2 remains incomplete; its contract is decided as `CR-008` and only `C2-I` is authorized. Every other obligation in the list above is still open, and product release readiness is still not claimed. Current state: § 11.

---

# 11. ROADMAP COMPLETION WINDOW

## C1 — calculation-sensitive Settings

Статус: `DONE — PRODUCT DECISION ACCEPTED AND C1-I MERGED AND EXACT-HEAD VERIFIED`

### C1-I merge closure

`VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE.` None of the runtime results below was executed in the documentation task that recorded this closure.

| Item | Value |
|---|---|
| Decision PR #148 final reviewed head | `577e0fd0b5c3e6fc82e2399fd17f023b6e221b83` |
| Decision PR #148 merge commit | `80b83de3e838cf676669a1b627770300590c99c0` |
| Implementation PR #149 title | `C1-I — Implement backend-owned tax-rate setting` |
| Implementation PR #149 state | `MERGED` |
| Implementation PR #149 final reviewed head | `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9` |
| Implementation PR #149 merge commit | `ff7afe6b0778ab2b348229a4df34acf3e3fc0001` |
| Implementation PR #149 merged at | `2026-07-27T19:44:53Z` |

Accepted evidence:

| Check | Accepted result |
|---|---|
| Backend complete suite | `671 collected / 671 passed / 0 failed / 0 skipped` |
| Original merged baseline node IDs still collected | all `562` |
| Focused tax-setting frontend suite | `52 passed / 0 failed / 0 skipped` |
| All 13 focused frontend suites | `568 passed / 0 failed / 0 skipped` |
| Frontend production build | `PASS` |
| Exact-head `/settings` browser smoke | `PASS — 146 checks / 0 failures` |
| Exact smoke-tested head | `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9` |
| `frontend/src/main.ts` | `6406` → `6399` lines |

`C1-I` added **no migration** and implemented **only** the tax-rate setting, not any C2 calculation. `C1-I` is `DONE — MERGED AND EXACT-HEAD VERIFIED`; it no longer awaits smoke, review, or merge, and it is not reopened. The pre-merge `C1-I` record further down this section is preserved as an explicitly **historical, superseded** account of the slice as it stood before merge.

Минимум:

- backend-owned tax rate;
- Decimal validation;
- Settings UI;
- audit изменений;
- явное решение по effective date/snapshot;
- отсутствие silent recalculation истории.

Без полноценной бухгалтерии, tax filing и invoices.

### CR-007 — accepted product decision

`CR-007 — Decide the C1 workshop tax-rate setting contract` is **accepted** (RECORDED PRODUCT-OWNER DECISION, 2026-07-27). The durable contract lives in `docs/settings.md` § “C1 — налоговая ставка для расчётов”, with the API shape in `docs/api.md`, the snapshot semantics in `docs/domain-model.md` § 6.14, and the report boundary in `docs/reports.md`. Summary:

**One global setting.** `default_tax_rate`, user-facing `Налоговая ставка для расчётов`, an internal planning estimate — not tax filing, not a declaration, not VAT accounting, not legal advice, not automatic regime detection, not an invoicing or accounting subsystem. The setting is never labelled as a specific legal regime; the user chooses the percentage.

**Representation.** A **percentage**, not a coefficient: `6` and `6.00` mean `6%`, and `0.06` means `0.06%`. `Decimal` only, persisted and transmitted as a decimal string, never a binary float, at most two fractional digits on input, range `0.00`–`100.00` inclusive. Excess precision such as `6.005` is **rejected**, never silently rounded — so `quantize_percentage` must not be reused for this validation. `0.00` is a real configured value and is never the same as missing.

**Canonical form is exactly two fractional digits**, both in the persisted `default_tax_rate` value and in the API `tax_rate_percent`: `6` → `6.00`, `6.0` → `6.00`, `6.00` → `6.00`, `0` → `0.00`, `100` → `100.00`. Canonical formatting is applied **after** validation and never absorbs excess precision, so `6.005` is rejected rather than becoming `6.01`. The no-op comparison uses that exact canonical two-decimal string.

**Taxable base.** The order sale price. `tax_amount = ROUND_MONEY(sale_price_snapshot × tax_rate_percent_snapshot ÷ 100)` with money quantum `0.01` and `ROUND_HALF_UP`, rounding only the final amount. Tax is deducted from gross sale revenue for future margin, never added on top of `sale_price`. No expense-based regimes, fixed amounts, brackets, minimum tax, deductions, VAT modes, multiple rates, or per-product/client/order/batch overrides.

**Effective time.** Immediate effectiveness. `effective_at` is the timestamp of the **currently active setting**: backend-generated, never backdated, scheduled, or edited, with no multiple active rate periods and no user-configurable effective date in the MVP. First configuration and a real rate change each produce a new value; a no-op keeps the existing one; an explicit **Clear returns `effective_at: null`**, because there is no active setting left to timestamp — the clear event time is recorded by `AuditLog.created_at`, and the clear audit metadata carries `previous_effective_at` plus `new_effective_at: null`. A new rate applies to later readiness checks and later confirmations, and never modifies completed batches, existing report snapshots, prior audit records, generated documents, or persisted tax/margin values.

**Timestamp storage.** The source is the existing `AppSetting.updated_at` column, which stays persisted in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format. The service normalizes that value and only the API exposes ISO-8601 UTC. The database does **not** store ISO-8601, and `C1-I` changes no column, default, or migration.

**Snapshots.** Future C2 uses immutable `ProductionBatch` snapshots: existing `sale_price` as taxable base, existing `tax` as the rounded amount, plus future nullable `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot`. Nullable for backward compatibility, **never backfilled**, old rows stay unknown, reports read snapshots and never recalculate with the current rate.

**Missing values.** Missing rate is `null`, never `0%`; it produces a non-blocking warning, leaves tax and dependent margin unavailable, and does not block physical production. Missing sale price leaves tax and margin unavailable. Missing total cost still allows tax but not margin. Old batches without snapshots show `Недоступно`. No missing financial value is ever displayed as a fabricated zero.

**Clear is row deletion.** Explicit only, `tax_rate_percent: null`; an empty string is not a backend substitute for `null`; clearing is confirmed, warned about, audited, and never touches historical rows. `C1-I` deletes **only** the `default_tax_rate` `AppSetting` row through a bounded new repository capability equivalent to `delete_setting(key: str, connection=None)`; the delete and the `AuditLog` insert share one transaction, and a failed audit insert rolls the deletion back. After a successful Clear the API returns `is_configured: false`, `tax_rate_percent: null`, `effective_at: null`. Clearing an absent row is a no-op — no delete, no timestamp change, no `AuditLog`, no misleading changed message. The legacy `tax.default_rate` placeholder row is **never** deleted, read, reinterpreted, migrated, or rewritten. **Not authorized:** a nullable-column migration, a sentinel value, empty-string storage, a new settings table, or a parallel settings store — unconfigured is the absence of the row.

**Audit.** Every real mutation — first configuration, change, clear — writes `tax_rate_setting_changed` / `app_setting` / `default_tax_rate` **atomically** with the persistence change, rolling that change back if the audit write fails. This binds both shapes: the configure/change upsert and the Clear row deletion. Reads, opening Settings, validation failures, failed persistence, and no-ops are not audited. Safe metadata only; never the raw payload, full settings JSON, stack traces, unrelated profile fields, or client data.

**No-op.** When the canonical persisted state would not change, return the current representation and write nothing — no setting write, no row deletion, no `effective_at` change, no `AuditLog`, no misleading success message. The comparison uses the exact canonical two-decimal string.

**UI.** Inside `/settings` only, one percentage input with a `%` unit, help text, configured/unconfigured state, human-readable effective timestamp, Save, Cancel, explicit confirmed Clear, structured field error, form-scoped pending state, success only after backend confirmation, distinct mutation and refresh failures, keyboard accessible, no raw JSON, no API terminology, no tax-law or filing promises. The frontend sends a decimal string or `null` and never calculates tax or margin.

### C1/C2 boundary

**C1 owns:** the persisted global tax rate; Decimal validation; the backend-generated effective timestamp; GET and update API; explicit clear; the Settings UI; the atomic `AuditLog`; persistence and reload behavior; no-op behavior; human-readable help and errors.

**C1 does not own:** readiness tax calculation; confirmation tax calculation; `ProductionBatch` snapshot fields; margin and margin-percent calculation; report calculations; historical migration or backfill. Those are C2.

### C1-I — Backend-owned tax-rate setting

Статус: `DONE — MERGED AND EXACT-HEAD VERIFIED` (PR #149, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`)

> **HISTORICAL PRE-MERGE RECORD — SUPERSEDED.** Everything from here to the end of this `C1-I` subsection was written while the slice was still on its PR branch, and its `IMPLEMENTED — EXACT-HEAD /settings SMOKE REQUIRED BEFORE MERGE` framing was true at the time. It is preserved for traceability and is **not** a current-state claim. The current state is the `C1-I merge closure` table at the top of § 11: the smoke passed (`146 checks / 0 failures`), the PR merged, and `C1-I` is `DONE`.

Exactly one bounded follow-up slice, started from merged `origin/main` `80b83de3e838cf676669a1b627770300590c99c0` after the `CR-007` decision PR #148 merged.

#### Delivered

- `backend/app/domain/tax_rate.py` — percentage validation and canonical two-decimal formatting through `parse_decimal` plus an explicit shape and fractional-digit check, never `quantize_percentage`;
- `backend/app/schemas/tax_rate_settings.py` — request/response schemas; the request field is deliberately untyped so wrong payload shapes reach the domain validator and get the project structured Russian error;
- `backend/app/services/tax_rate_settings.py` — the backend-owned service: one transaction per mutation, read-compare-then-write no-op detection, the monotonic effective timestamp, Clear as row deletion of `default_tax_rate` only, and the atomic `AuditLog`;
- `backend/app/api/tax_rate_settings.py` — the dedicated router registered in `backend/app/main.py` under the existing `/api/settings` namespace;
- `backend/app/repositories/settings.py` — bounded extension only: optional `connection` on `get_setting`/`upsert_setting`, an optional caller-owned `updated_at` on `upsert_setting`, and the new `delete_setting(key, connection=None)`. No schema change, no new table, no parallel store;
- `backend/app/services/settings.py` — Decision Matrix and capability wording only: `default_tax_rate` becomes `editable_now` and nothing else does;
- frontend `settings-tax-contract.ts`, `settings-tax-feedback.ts`, `settings-tax-presentation.ts`, `settings-tax-bindings.ts`, `settings-tax-runtime.ts`, plus `settings-profile-presentation.ts` extracted from the Settings route so `frontend/src/main.ts` did not grow — `6406` lines before, `6399` after;
- focused tests: `backend/app/tests/test_tax_rate_settings.py`, `backend/app/tests/test_tax_rate_settings_api.py`, `frontend/test/settings-tax-feedback.test.mjs` with `tsconfig.test.settings-tax-feedback.json` and the `test:settings-tax-feedback` script.

**Not delivered, by design:** every C2 item — readiness tax, confirmation tax, `ProductionBatch` snapshot columns, the snapshot migration, tax amount, margin, margin percent, and report calculation — plus any migration, historical backfill, or recalculation.

*(Historical, superseded:)* `C1-I` is **not `DONE`**: it is implemented on its PR branch and becomes `DONE` only after the exact-head `/settings` smoke passes and the PR is reviewed and merged. C2 remains blocked until then. — **That condition has since been satisfied. See the `C1-I merge closure` table above.**

#### Scope

- a dedicated backend tax-setting service;
- dedicated request/response schemas;
- dedicated Settings API endpoints, preferred `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate`;
- persistence through the existing settings repository / `AppSetting` mechanism under the preferred key `default_tax_rate`;
- transactional `AuditLog`;
- a Settings UI section;
- focused backend tests;
- focused frontend tests;
- an exact-head `/settings` browser smoke;
- minimal directly affected documentation and state updates.

#### Non-goals

No readiness tax calculation; no confirmation tax calculation; no `ProductionBatch` snapshot fields; no margin or margin-percent calculation; no report calculation change; no historical backfill or recalculation; no new settings table; no new settings architecture; no currency, target-margin, unit, stock-threshold, or expiry setting; no onboarding tax step; no accounting, invoicing, VAT, or tax-filing feature; no restore work; no `CR-004` or `CR-006` work; no C2, C3, or C4 work; no packaging or release work.

#### Architecture constraints

Verified read-only against `origin/main` at `09d11fc32db6ae57f99d522c4aa71e223e4e01a5`. Full evidence: `docs/settings.md` § 14.

- **Do not reuse the seeded placeholder.** `backend/app/migrations/versions/0001_infrastructure.py` seeds `app_settings` with `tax.default_rate = "0.06"`, `value_type` `decimal_string`. Under the decided percentage contract `0.06` means `0.06%`. That row is a pre-decision placeholder: use the distinct key `default_tax_rate`, and do not read, reinterpret, migrate, rewrite, or treat `tax.default_rate` as a configured rate. The historical `tax_rate default 0.06` line in `docs/roadmap.md` is likewise superseded and is not a coefficient authorization.
- **Atomicity requires a bounded repository extension.** `AuditLogRepository.create_log` already accepts an optional `connection`, but `SettingsRepository.upsert_setting` opens its own `session(config)` and accepts none, so the setting write and the audit write cannot currently share a transaction. Add an optional `connection` parameter to the existing settings repository methods, matching the pattern the audit repository and the production services already use. **No schema change, no new settings table, no parallel settings store, no second persistence mechanism.** If implementation evidence shows even this bounded extension cannot satisfy atomicity, stop, record the evidence, and update the contract in `docs/settings.md` before writing the slice.
- **Clear needs one bounded new repository method.** `SettingsRepository` currently exposes only `list_settings`, `get_setting`, and `upsert_setting`. Add a capability equivalent to `delete_setting(key: str, connection=None)`, using the same optional-`connection` pattern so the delete and its `AuditLog` insert run in one transaction. It deletes a settings row by key and nothing more; it is not authorization for a schema change, a nullable column, a sentinel value, empty-string storage, a new settings table, or a parallel store. It must never be called with the legacy `tax.default_rate` key.
- **Effective timestamp.** Use the existing `AppSetting.updated_at`. The column defaults to SQLite `CURRENT_TIMESTAMP`, which **persists** `YYYY-MM-DD HH:MM:SS` in UTC without a `T` or offset and stays that way; the service normalizes that stored value and only the API exposes ISO-8601 UTC. Do not claim the database stores ISO-8601, and do not change the column type, its default, or any migration in this slice. Because Clear removes the row, there is no active `updated_at` to read afterwards and the API returns `effective_at: null`.
- **No-op requires read-compare-then-write.** `upsert_setting` refreshes `updated_at` in its `ON CONFLICT DO UPDATE` branch, so an unchanged canonical value must never reach the repository.
- **Validation helper.** Use `parse_decimal` from `backend/app/domain/decimal_utils.py` plus an explicit fractional-digit check. Do not use `quantize_percentage`, which would silently round `6.005` to `6.01`.
- The workshop profile flow is untouched. This slice does not retroactively add audit to `WorkshopProfileSettingsService.update_profile`; that would be a separate slice.

#### Backend requirements

- validate the percentage range, precision, type, and format, rejecting floats, `bool`, `NaN`, `Infinity`, malformed values, and excess precision with structured Russian errors;
- treat `null` as clear and `0.00` as a configured zero, never conflating them;
- persist and return the canonical exactly-two-decimal string, formatting only after validation;
- generate a new `effective_at` on first configuration and on a real rate change; keep the existing one on a no-op; return `effective_at: null` after a Clear;
- implement Clear as deletion of the `default_tax_rate` row only, never touching the legacy `tax.default_rate` key;
- write the persistence change and the `AuditLog` in one transaction — upsert **and** delete alike — rolling the persistence change back if the audit write fails;
- keep `GET` read-only and unaudited;
- persist and return decimal strings;
- change no existing endpoint response shape, and mark `default_tax_rate` as editable in the Settings Decision Matrix only when the endpoint actually exists.

#### Frontend requirements

- one tax-setting section inside `/settings`, following the existing shared feedback and mutation-lifecycle patterns;
- send a decimal string or `null`; never store the authoritative rate, calculate tax or margin, or invent zero;
- re-render from the confirmed backend response; keep mutation failure and refresh failure distinct;
- accept a comma in the input layer and normalize it before sending;
- no raw JSON, no API terminology, no tax-law or filing promises, and no new dependency.

#### Tests

Focused backend coverage must prove at least: percentage-not-coefficient semantics; boundary values `0.00` and `100.00`; rejection of negatives, values above `100`, three-or-more fractional digits, floats, `bool`, `NaN`, `Infinity`, and malformed strings; equivalence of `6`, `6.0`, and `6.00`; comma handling at the boundary the contract assigns it; `null` clear versus configured `0.00`; the no-op contract writing nothing and creating no `AuditLog`; an audited first configuration, change, and clear; persistence and reload; and that no order, production batch, stock movement, report, or historical row changes.

Four requirements are explicit, because they are where the contract is easiest to implement wrongly:

- **Canonical two-decimal form.** Assert the exact persisted and returned strings: `6` → `"6.00"`, `6.0` → `"6.00"`, `6.00` → `"6.00"`, `0` → `"0.00"`, `100` → `"100.00"`. Assert `6.005` is rejected and that **nothing** is persisted for it — never `6.01`. Assert the no-op comparison works on the canonical string, so `PUT "6"` against stored `"6.00"` writes nothing and creates no `AuditLog`.
- **`effective_at` per event.** New on first configuration; new on a real change; unchanged on a no-op; **`null` after Clear**. Assert the clear audit metadata carries `previous_effective_at` equal to the former setting timestamp and `new_effective_at: null`, and that `AuditLog.created_at` is what records the clear time. Assert the API value is ISO-8601 UTC while the stored `app_settings.updated_at` remains SQLite `YYYY-MM-DD HH:MM:SS`.
- **Clear is row deletion, atomically audited.** Assert a successful Clear removes the `default_tax_rate` row and returns `is_configured: false`, `tax_rate_percent: null`, `effective_at: null`. Assert **atomic delete + audit rollback**: with the `AuditLog` insert forced to fail, the `default_tax_rate` row must still exist with its original value and timestamp, and no audit row may be written. Assert clearing an absent row is a no-op — no delete, no timestamp change, no `AuditLog`, no changed message. Assert no nullable column, sentinel value, empty-string row, new table, or parallel store is introduced.
- **Key isolation.** The seeded `tax.default_rate` row must be proven untouched by configure, change, and Clear alike — never read as a configured rate, never deleted, never rewritten — and `default_tax_rate` and `tax.default_rate` must never be conflated.

Focused frontend coverage must prove the configured, unconfigured, pending, success, validation-error, and refresh-failure states, the explicit confirmed Clear, and that the frontend performs no tax or margin arithmetic. The Settings UI currently lives inline in `frontend/src/main.ts` and no Settings test module exists, so this requires extracting a tax-setting feedback/presentation module into the existing `frontend/src/*-feedback.ts` + `frontend/test/*.test.mjs` + `tsconfig.test.*.json` + npm-script pattern, **without adding dependencies**.

Run the complete backend suite from `backend/`; acceptance is `0 failed` and `0 skipped` with the merged baseline `562 collected, 562 passed, 0 failed, 0 skipped` preserved and no existing test deleted, renamed, skipped, `xfail`-ed, or weakened. The frontend production build remains required.

#### Smoke

Focused `/settings` browser smoke against the exact published implementation head, at desktop `1440 × 900`, with an isolated temporary SQLite database, an isolated temporary user-data directory, an isolated browser profile, no real user data, and evidence kept outside Git. Prove: the route loads with the tax section unconfigured; saving `6` persists and displays the canonical `6.00` with a human-readable effective timestamp, and the API returns exactly `"6.00"`; saving `0` displays `0.00` as a configured value rather than an unconfigured one; the value survives an explicit refetch and a full page reload; `6.005` is rejected with a readable Russian field error, nothing is persisted, and the stored value never becomes `6.01`; re-saving `6` against the stored `6.00` reports no misleading change; explicit Clear requires confirmation, returns the section to the unconfigured state, and yields `is_configured: false`, `tax_rate_percent: null`, and `effective_at: null`; an existing production batch still shows its unchanged financial values. Require zero unexpected console errors, zero unexpected console warnings, zero page errors, zero unexpected HTTP or request failures, and no horizontal page overflow. Full release smoke must not be claimed.

#### Acceptance criteria

`C1-I` is complete only when the decided contract is implemented exactly as written, the backend suite is green with no weakened tests, the focused frontend suite and the production build pass, the exact-head `/settings` smoke passes, no historical record is mutated or recalculated, no `ProductionBatch` snapshot field or C2 calculation is introduced, and the directly affected documentation and state files record the delivered behavior.

## C2 — себестоимость, налог и маржа

Статус: `CONTRACT ACCEPTED (CR-008) — DIVIDED INTO C2-I / C2-II / C2-III-A / C2-III-B`

The C1 gate is satisfied: `C1-I` is merged and exact-head verified, so C2 is no longer blocked on C1. The C2 product contract was decided as `CR-008`; the ADR is `docs/decisions/0012-c2-financial-calculation-snapshots.md`. It refines and completes the C2 semantics `CR-007` had partially fixed (readiness semantics, stale-setting conflict, snapshot fields, rounding order) and contradicts none of them.

Baseline requirements, unchanged:

- backend domain services;
- readiness estimates с limitations;
- immutable production snapshots;
- reports используют snapshots;
- старые production records не пересчитываются текущими ценами/настройками;
- missing data остаётся `Недоступно`, без выдуманных значений;
- Decimal, migration и backward-compatibility tests обязательны.

Authorization states:

| Slice | Status |
|---|---|
| `C2-I` — backend financial readiness estimate | `DONE — MERGED AND EXACT-HEAD VERIFIED` — PR #151 |
| `C2-II` — transactional production financial snapshots | `DONE — MERGED AND EXACT-HEAD VERIFIED` — PR #152 |
| `C2-III-A` — Order and `ProductionBatch` financial presentation | `DONE — MERGED AND EXACT-HEAD VERIFIED` — PR #154 |
| `C2-III-B` — snapshot-backed reports and report documents | `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED` |

`C2-I` merged as PR #151: reviewed head `6f72bffc9a0d17839e3a74c69366fe17df8a318b`, merge commit `7b3dde8278f59658bfa3a81c09e643ea10319551`, merged `2026-07-28T04:22:13Z`, exact-head readiness smoke `PASS — 113 checks / 0 failures`.

`C2-II` merged as PR #152: reviewed head `0cdda1b06b9783975f085207527f7d36a2ef7f22`, merge commit `c3a3a7b8db06fe85290216113b784123ed9b6b30`, merged `2026-07-28T09:00:50Z`. Full closure evidence: § *C2-II — merged and exact-head verified* below.

`C2-III-A` merged as PR #154: reviewed head `ef1103811a8f062f9129bfb465a98e0cfa388935`, merge commit `d432fcaee52a16a4f8b609ec160cf3fa2b33d013`, merged `2026-07-28T13:05:34Z`, exact-head API smoke `PASS — 67 checks / 0 failures` and exact-head browser smoke `PASS — 28 checks / 0 failures`. Full closure evidence: `state/current-focus.md` § *C2-III-A — merged and exact-head verified*.

`C2-III` was subdivided into exactly two runtime slices, as required by ADR 0012. `C2-III-B` is now the only remaining C2 runtime slice; no implementation PR number is assigned to it.

```text
C2 is not complete in this documentation PR.
```

C2 becomes complete only after `C2-III-B` is implemented, its focused and complete tests pass, its exact-head API and browser smoke pass, it is reviewed and merged, and the final active C2 documentation and state are closed consistently. Authorizing `C2-III-B` does not make C2 complete. C3 and C4 remain inactive.

### C2 — accepted product contract (`CR-008`)

**Product boundary.** C2 is an internal operational estimate for the workshop. It is **not** tax filing, a tax declaration, VAT accounting, automatic tax-regime selection, УСН / ОСНО / НПД / ПСН / АУСН / ЕСХН calculation, insurance-contribution accounting, minimum-tax calculation, annual or quarterly tax accounting, marketplace tax accounting, invoicing, bookkeeping, or legal or tax advice. The current setting and calculation are **not** renamed to a tax reserve by this decision.

```text
The simplified tax model is accepted for the current MVP and may be replaced by
a separately decided future tax-regime model. Existing historical snapshots
must remain immutable after such a replacement.
```

**Authoritative inputs, all backend-owned:** the authoritative Order sale price; the existing backend readiness cost estimate; the actual authoritative total cost produced by the transactional confirmation flow; the current `default_tax_rate` state from the backend tax-rate service; and the current backend-owned `effective_at`. The legacy `tax.default_rate` key is never read. The frontend supplies no authoritative monetary value and calculates no total cost, tax, margin, or margin percent; its only financial input responsibility is passing back the latest backend-returned tax-rate context unchanged during confirmation.

**Formulas.** `Decimal` only, never binary float at any intermediate step:

```text
tax_amount     = ROUND_MONEY(sale_price × tax_rate_percent / 100)
margin         = ROUND_MONEY(sale_price - total_cost - tax_amount)
margin_percent = ROUND_PERCENT(margin / sale_price × 100)
```

`tax_rate_percent` is a percentage — `6.00` means `6%` — and is always divided by `100`. Money quantum `0.01`, percentage quantum `0.01`, both `ROUND_HALF_UP`, rounding only the final amount of each formula. Tax is deducted from gross revenue, never added on top. A configured `0.00` produces tax `0.00`; a missing rate or a missing sale price produces `null`, never a fabricated zero. Margin may be positive, zero, or negative, and a negative margin — or a negative margin percent — is never clamped. Margin percent is computed only when margin is available and the sale price is greater than zero.

**Availability matrix.**

| Sale price | Total cost | Tax rate | Tax | Margin | Margin % | `financial_estimate_status` |
|---|---|---|---|---|---|---|
| present, `> 0` | present | configured | available | available | available | `available` |
| present, `= 0` | present | configured | `0.00` | available | unavailable | `partial` |
| present | missing | configured | available | unavailable | unavailable | `partial` |
| present | present | missing | unavailable | unavailable | unavailable | `unavailable` |
| missing | any | any | unavailable | unavailable | unavailable | `unavailable` |
| any | any | invalid persisted value | unavailable | unavailable | unavailable | `unavailable` |

Physical production is **never** blocked by any row of this matrix.

**Invalid persisted tax-rate value** is a defensive local-first corruption case, not a normal API flow: do not calculate with it, do not coerce it, do not treat it as zero, do not expose the raw value as an authoritative rate, treat the estimate as unavailable, return the non-blocking `tax_rate_invalid` warning, do not turn the readiness request into an unhandled HTTP `500`, and do not block physical production.

### No valid configured tax-rate context

**`no valid configured tax-rate context`** means either of two backend states:

1. no `default_tax_rate` row exists; or
2. the persisted `default_tax_rate` value exists but is invalid and cannot be safely interpreted as the canonical C1 percentage.

The two states stay **distinguishable through readiness warnings** — `tax_rate_missing` for the absent row, `tax_rate_invalid` for the invalid value — but they produce **the same authoritative financial context**:

```text
tax_rate_percent      = null
tax_rate_effective_at = null
```

| Backend state | Warning | Rate context | Status | Tax / margin / margin % | Physical production |
|---|---|---|---|---|---|
| row absent | `tax_rate_missing` | `null` / `null` | `unavailable` | `null` | not blocked |
| value invalid | `tax_rate_invalid` | `null` / `null` | `unavailable` | `null` | not blocked |

The invalid case must **not** also emit `tax_rate_missing`, and must not produce an unhandled HTTP `500`.

The raw invalid persisted value must never be returned as the authoritative rate, and must never be normalized, coerced, rounded, treated as zero, copied into a readiness DTO, copied into a confirmation request, or copied into a `ProductionBatch` snapshot.

**Physical-production invariant.** An absent or invalid tax-rate setting may make financial values unavailable, but it must not by itself block physical production.

### Exact timestamp contract

| Surface | Format | Rules |
|---|---|---|
| database persistence (`AppSetting.updated_at`, future `tax_rate_effective_at_snapshot`) | `YYYY-MM-DD HH:MM:SS` | UTC, second precision, SQLite text, no `T`, no `Z`, no offset |
| API and confirmation context (`effective_at`, readiness `tax_rate_effective_at`, `expected_tax_rate_effective_at`, exposed snapshot) | `YYYY-MM-DDTHH:MM:SSZ` | UTC, second precision, literal `T`, literal `Z` |

Example: `2026-07-27T19:44:53Z`.

Not accepted and not documented: local-time values, arbitrary offsets such as `+03:00`, fractional seconds, a space instead of `T`, a missing `Z`, or user-generated timestamps. `expected_tax_rate_effective_at` must be either `null` or the **exact** canonical timestamp previously returned by readiness; anything else is HTTP `422` with `invalid_tax_rate_context`. The API must never expose the raw SQLite storage representation — the confirmation and `ProductionBatch` detail responses normalize the stored snapshot to the canonical `Z` form.

### Exact existing readiness API mapping

`C2-I` extends the **existing** `POST /api/orders/{order_id}/check-production-readiness`. No parallel financial-readiness endpoint. No existing field removed or renamed.

Existing and **reused**: `estimated_cost`, `estimated_tax`, `estimated_margin` — the latter two activated, not duplicated.

Additive: `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, `financial_estimate_status`.

```text
sale_price
estimated_cost
tax_rate_percent
tax_rate_effective_at
estimated_tax
estimated_margin
estimated_margin_percent
financial_estimate_status
```

All monetary and percentage values are decimal strings or `null`; `tax_rate_effective_at` is an ISO-8601 UTC string or `null`. **`estimated_total_cost` is not authorized**, and no duplicate alias for any existing field is authorized. The extension must be backward-compatible with the current frontend.

`financial_estimate_status`: `available` (tax, margin, and margin percent all available), `partial` (at least tax or margin available but not the complete set), `unavailable` (tax unavailable and every dependent value therefore unavailable). Configured rate + sale price `> 0` + total cost → `available`; configured rate + sale price `= 0` + total cost → `partial`; configured rate + sale price + missing total cost → `partial`; missing or invalid rate → `unavailable`; missing sale price → `unavailable`.

### Preserved warning-code contract

Financial warnings are **non-blocking**, use the existing readiness warning mechanism, and preserve the exact existing `ProductionReadinessIssue` response structure. No parallel warning system.

| Code | Status | Meaning |
|---|---|---|
| `tax_rate_missing` | existing, preserved | no configured `default_tax_rate` |
| `sale_price_missing` | existing, preserved | the authoritative Order sale price is unavailable |
| `cost_data_missing` | existing, preserved | the readiness cost calculation cannot produce a complete total cost |
| `margin_percent_unavailable_zero_sale_price` | new | tax and margin may be available, but the denominator is zero |
| `tax_rate_invalid` | new | defensive handling of an invalid persisted canonical tax-rate value |

Do not rename existing codes. Do not introduce aliases such as `tax_rate_unconfigured`, `sale_price_unavailable`, or `total_cost_unavailable`. Do not emit two warnings for one semantic condition. Do not convert a financial warning into a physical blocker: `can_produce` stays governed by recipe and formula readiness, stock, lots, packaging, order lifecycle, and the existing physical-production safety rules.

### C2-I — Backend financial readiness estimate

Статус: `DONE — MERGED AND EXACT-HEAD VERIFIED` — PR #151

> **HISTORICAL PRE-MERGE RECORD — SUPERSEDED.** The paragraph immediately below described `C2-I` while it was still on an unmerged PR branch. It is preserved as history. The current status is the one above and in the authorization table in this section.

The only runtime slice authorized by the `CR-008` decision PR (merged as PR #150). It is implemented on branch `codex/c2-i-backend-financial-readiness-estimate`, started from merged `origin/main` `4c03142ef7acdc31fcb15730484e8e52dde95b69`, and is **not merged**. `C2-II` stays blocked until `C2-I` is merged and exact-head verified.

Delivered on that branch: the pure calculation module `backend/app/domain/production_financials.py` (`TaxRateContext`, `ProductionFinancialInputs`, immutable `ProductionFinancialEstimate`, `FinancialEstimateStatus`, `FinancialWarningCode`); its integration through `ProductionReadinessService._estimate_financials` and `_tax_rate_context`, replacing the previous `_estimate_money`; the five additive response fields on `ProductionReadinessResponse`; and the two new non-blocking warning codes. The domain module opens no connection, reads no repository, and imports neither FastAPI nor Pydantic.

**Invalid-rate re-validation.** The C1 Settings repair surface may still return the stored text for an externally corrupted row, so `is_configured` alone is not treated as authoritative. `_tax_rate_context` re-parses the returned percentage through the existing C1 `parse_tax_rate_percent` and converts anything that fails — or any row with no effective timestamp — into the no-valid-rate context with `tax_rate_invalid`. The raw text is never returned, never calculated with, never treated as `0.00`, and never turned into an HTTP `500`. `GET`/`PUT /api/settings/tax-rate` behavior is unchanged.

#### Goal

Activate the accepted backend-owned tax, margin, and margin-percent estimate inside the existing production readiness flow.

#### Scope

`C2-I` may implement only: one focused backend financial calculation domain service; integration with the existing production readiness service; activation of the existing readiness financial fields; the additive readiness response fields; the stable financial warning codes through the existing warning mechanism; focused backend tests; readiness API integration tests; an exact-head readiness API smoke; and minimal directly affected documentation and state updates.

#### Backend requirements

`C2-I` must reuse the C1 tax-rate service and repository boundary; never read `tax.default_rate`; use `default_tax_rate` only; use `Decimal` only; reuse the existing money and percentage quantization rules; keep calculation logic out of API routers and out of the frontend; perform no persistence write; create no `AuditLog`; change no Order, `ProductionBatch`, stock movement, packaging movement, or report; add no migration; preserve all existing readiness blockers and warnings; preserve physical-production eligibility when only financial inputs are unavailable; and handle invalid persisted tax-rate data safely and non-blockingly.

Preferred focused module:

```text
backend/app/domain/production_financials.py
```

A different precise name is allowed only when it better matches established repository naming. Do **not** place the calculation in `backend/app/api/production_readiness.py`, `backend/app/main.py`, a generic `utils.py`, a generic `helpers.py`, or an all-purpose finance manager.

The focused service should accept already-authoritative values and return a typed immutable result equivalent to:

```text
sale_price
total_cost
tax_rate_percent
tax_rate_effective_at
tax_amount
margin
margin_percent
status
warnings
```

It must not read repositories directly unless the current repository pattern requires a narrowly documented adapter.

#### Non-goals

No `ProductionBatch` snapshot columns; no migration; no production-confirmation tax; no production-confirmation margin; no stale tax-setting confirmation rejection; no report calculation change; no report UI; no readiness UI redesign; no frontend financial arithmetic; no Russian tax regimes; no accounting; no historical backfill; no `C2-II`; no `C2-III`; no `C3`; no `C4`; no Restore; no packaging; no release smoke.

#### Frontend boundary

No frontend production change is expected in `C2-I`. The readiness response extension must be backward-compatible with the current frontend.

Do not modify `frontend/src/main.ts`. Required invariant:

```text
frontend/src/main.ts = 6399 lines
```

Focused frontend **test-only** changes are allowed only when needed to prove that the existing DTO guard safely ignores additive fields. Do not display the new financial estimates in the UI in `C2-I`, do not calculate them in the frontend, and do not add temporary hidden UI.

#### Tests

Focused coverage is required for at least:

1. configured `6.00%` rate;
2. configured `0.00%` rate;
3. missing rate;
4. invalid persisted rate;
5. missing sale price;
6. missing total cost;
7. zero sale price;
8. positive margin;
9. zero margin;
10. negative margin;
11. negative margin percent;
12. tax final rounding with `ROUND_HALF_UP`;
13. margin final rounding;
14. margin-percent final rounding;
15. no intermediate binary float use;
16. exact two-decimal strings;
17. financial warnings are non-blocking;
18. physical `can_produce` unchanged by financial absence;
19. existing readiness blocker behavior unchanged;
20. existing warning response structure unchanged;
21. existing warning codes preserved;
22. no persistence write;
23. no `AuditLog`;
24. no `ProductionBatch` change;
25. no Order change;
26. no `StockMovement` change;
27. no packaging movement change;
28. no report change;
29. legacy `tax.default_rate` ignored;
30. canonical `default_tax_rate` used;
31. API response remains backward-compatible;
32. no `estimated_total_cost` duplicate added;
33. existing readiness frontend DTO handling remains safe;
34. the complete backend suite remains green.

No existing test may be deleted, renamed, skipped, `xfail`-ed, or weakened.

#### Smoke

After publication of the future `C2-I` runtime PR, require an exact-head focused **readiness API** smoke using isolated data. Verify through the API: configured `6.00%`; configured `0.00%`; missing rate; invalid persisted rate defensive behavior; missing sale price; missing total cost; negative margin; the zero-price margin-percent-unavailable case; the exact existing warning codes; the exact new warning codes; the exact financial status values; physical readiness unchanged; no database mutation; no audit rows; no production batch; no stock movement; no packaging movement; no report data change.

A passive browser regression may prove that the Order route still loads. `C2-I` must not claim a new financial UI. Full release smoke is not part of `C2-I`.

#### Acceptance criteria

`C2-I` is complete only when the decided formulas, availability matrix, status values, and warning codes are implemented exactly as written; the existing readiness fields are reused and no `estimated_total_cost` or alias is added; the response stays backward-compatible; no persistence, audit, order, batch, movement, report, or migration change occurs; `frontend/src/main.ts` is still `6399` lines; the complete backend suite is green with no weakened test; the exact-head readiness API smoke passes; and the directly affected documentation and state files record the delivered behavior.

### C2-II — Transactional production financial snapshots

Статус: `DONE — MERGED AND EXACT-HEAD VERIFIED`

#### C2-II — merged and exact-head verified

`VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #152 — `C2-II — Persist transactional production financial snapshots` |
| State | `MERGED`, base `main` |
| Final reviewed head | `0cdda1b06b9783975f085207527f7d36a2ef7f22` |
| Merge commit | `c3a3a7b8db06fe85290216113b784123ed9b6b30` |
| Merged at | `2026-07-28T09:00:50Z` |
| Exact smoke-tested head | `0cdda1b06b9783975f085207527f7d36a2ef7f22` |
| Accepted backend result | complete backend suite `883 passed / 0 failed / 0 skipped`; all `737` original merged-baseline node IDs still collected, zero renames |
| Accepted frontend result | all 15 focused frontend suites green, `0 failed` |
| Production build | `npm run build` — `PASS` |
| Exact-head migration smoke | `PASS — 41 checks / 0 failures` |
| Exact-head API smoke | `PASS — 57 checks / 0 failures` |
| Exact-head browser smoke | `PASS — all Orders-route checks / 0 failures` |
| `frontend/src/main.ts` final line count | `6399` |
| Migration `0019` delivered | yes — `0019_production_batch_tax_rate_snapshots` |
| Commit added after the accepted smoke | none — the head was verified unchanged and the tree clean afterwards |

The final merged head carries **zero test renames**: an earlier revision of the PR renamed two tests, both original node IDs were restored before merge, and the accepted result is `737 / 737` backend node IDs collected.

> **HISTORICAL PRE-MERGE RECORD — SUPERSEDED.** The paragraph immediately below described `C2-II` while it was still on an unmerged PR branch. It is preserved as history.

Authorized once `C2-I` merged as PR #151 and its exact head was verified. Implemented on branch `codex/c2-ii-transactional-production-financial-snapshots` from merged `origin/main` `7b3dde8278f59658bfa3a81c09e643ea10319551`. The contract below is the accepted one and was implemented as written; the durable decision stays `docs/decisions/0012-c2-financial-calculation-snapshots.md`.

Implemented shape:

- migration `0019_production_batch_tax_rate_snapshots` adds only the two nullable `TEXT` columns, additively, with no default and no backfill;
- `TaxRateSettingsService.get_tax_rate(connection=None)` is the bounded transaction-aware read; `backend/app/services/tax_rate_context.py` is the one shared reducer used by readiness and confirmation;
- `backend/app/domain/production_tax_context.py` validates the required-but-nullable request context; `backend/app/domain/tax_rate_timestamps.py` is the single storage/API timestamp boundary;
- the stale comparison runs inside the existing `BEGIN IMMEDIATE` transaction, before the first production write, and raises `409 tax_rate_context_stale`;
- the financial values reuse the merged `C2-I` pure domain calculation — no formula is duplicated in the confirmation service;
- the two snapshots are exposed in the confirmation response and `ProductionBatch` detail only; the list response and every report read model are unchanged;
- the frontend carries the readiness pair unchanged through `frontend/src/order-production-context.ts`, adds no financial arithmetic and no financial presentation, and `frontend/src/main.ts` stays at exactly `6399` lines.

#### Goal

Persist immutable financial snapshots during transactional production confirmation.

#### Migration

One nullable migration adding **only** `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` to `ProductionBatch`. Decimal-string persistence consistent with the existing nullable financial fields; timestamp representation consistent with the accepted API and storage boundary; **no backfill**; old rows remain `null`; no separate taxable-amount snapshot, because the existing `ProductionBatch.sale_price` is the taxable-base snapshot. A backup must be created before applying the migration, migration failure must not destroy user data, and rollback and backup behavior must follow the repository migration contract.

#### Existing fields

Reuse the existing `ProductionBatch` fields `sale_price`, `total_cost`, `tax`, `margin`, and `margin_percent`. Do **not** add duplicate fields such as `sale_price_snapshot`, `total_cost_snapshot`, `tax_amount_snapshot`, or `margin_amount_snapshot`.

#### Transaction-aware tax-setting read boundary

`C2-II` must read the current canonical tax setting **inside the same production transaction**. The current no-argument C1 read behavior must remain valid. One bounded read-only extension is authorized, equivalent to:

```python
TaxRateSettingsService.get_tax_rate(
    connection: sqlite3.Connection | None = None,
)
```

When a connection is supplied: read `default_tax_rate` through the existing `SettingsRepository`; use the supplied production-transaction connection; perform no write; create no `AuditLog`; preserve the public behavior of the current no-argument call; preserve the C1 validation and canonicalization boundaries.

Do not read the setting through a second independent connection while the production transaction is active; do not parse raw `AppSetting` values inside the production-confirmation service; do not bypass the C1 service/domain validation; do not create a second tax-setting service; do not introduce a generic transaction service locator. If the repository implementation proves this exact extension unsafe or incompatible, stop and request a contract correction before implementing `C2-II`.

#### Required-but-nullable confirmation context

The future production confirmation request must **always** contain `expected_tax_rate_percent` and `expected_tax_rate_effective_at`. Both keys are **required but nullable**, and the request schema declares them **without default values**.

Allowed value pairs:

1. **valid configured context** — a canonical two-decimal percentage string plus the canonical `YYYY-MM-DDTHH:MM:SSZ` timestamp, for example `"6.00"` and `"2026-07-27T19:44:53Z"`;
2. **no-valid-rate context** — explicit `null` and explicit `null`.

`null/null` means **"the latest readiness result observed no valid configured tax rate"**, which covers **both** a missing setting row **and** an invalid persisted setting. It must not be described as meaning only that the row is absent.

The frontend passes the pair from the latest confirmed readiness response and must not calculate the percentage, normalize it independently, alter it, invent a timestamp, or reuse an older readiness result after it has become stale.

Reject with HTTP `422` **before any production transaction writes**:

| Condition | Stable code |
|---|---|
| either key is omitted | `tax_rate_context_required` |
| exactly one of the two values is `null` | `invalid_tax_rate_context` |
| the percentage is malformed, non-canonical, out of range, or not a string | `invalid_tax_rate_context` |
| the timestamp is malformed or not the canonical `YYYY-MM-DDTHH:MM:SSZ` form | `invalid_tax_rate_context` |

A rejected context produces no `ProductionBatch`, no stock movement, no packaging movement, no Order mutation, no financial snapshot, and no production audit.

**Do not silently treat omitted keys as `null/null`.** The distinction is required: omitted context means an invalid or outdated client contract; explicit `null/null` means readiness observed no valid configured tax rate.

#### Transactional confirmation

Inside the same production transaction:

1. re-read the authoritative Order;
2. re-run the existing physical production readiness checks;
3. read the current canonical tax setting through the transaction-aware C1 service boundary;
4. compare the required expected tax context from the latest readiness response with the current backend-owned tax context;
5. recompute the authoritative sale price from the locked Order;
6. compute the actual production total cost through the existing confirmation flow;
7. calculate tax, margin, and margin percent through the shared backend financial domain service;
8. persist the `ProductionBatch` and all financial snapshots;
9. persist component movements;
10. persist packaging movements;
11. update the Order through the existing confirmation contract;
12. write the existing production audit or event records;
13. commit only when every required write succeeds.

Any failure must roll back the `ProductionBatch` creation, the rate snapshots, tax, margin, margin percent, component movements, packaging movements, the Order mutation, and the related production audit or event writes. A partially confirmed production must never exist.

#### Stale tax context

Inside the transaction, reduce the current backend state to one of exactly two comparable canonical contexts:

- **valid context** — canonical percentage + canonical API timestamp;
- **no-valid-rate context** — `null` + `null`, produced by both a missing row and an invalid persisted value.

Then compare with the expected context:

| Expected context | Current backend context | Result |
|---|---|---|
| same valid pair | same valid pair | continue |
| valid pair | different valid pair | `409 tax_rate_context_stale` |
| valid pair | missing | `409 tax_rate_context_stale` |
| valid pair | invalid | `409 tax_rate_context_stale` |
| `null/null` | valid pair | `409 tax_rate_context_stale` |
| `null/null` | missing | continue |
| `null/null` | invalid | continue |

Transitions: valid → changed valid is a stale conflict; valid → missing is a stale conflict; valid → invalid is a stale conflict; missing → valid is a stale conflict; invalid → valid is a stale conflict; **missing → invalid is not**; **invalid → missing is not**.

Missing and invalid intentionally share one confirmation context, because both produce exactly the same financial result: no rate snapshot, no tax, no margin, no margin percent. Do **not** add a third request field or a generic financial-context token in this decision; a future decision may introduce a richer state token only if product evidence shows it is necessary.

On a stale conflict: return HTTP `409` with the stable code `tax_rate_context_stale` and a safe Russian message equivalent to `Налоговая ставка изменилась. Обновите готовность и подтвердите производство ещё раз.`; create no `ProductionBatch`; write no movements; change no Order; write no financial snapshot; write no production audit; and do not retry automatically.

The stale check protects the **editable tax setting only**. `C2-II` must still recompute the current authoritative sale price, the current authoritative physical readiness, and the actual production cost inside the backend transaction. Do not introduce a generic opaque token, a second global versioning system, or a frontend-generated context hash without a new accepted decision.

#### Missing financial inputs during confirmation

Financial absence does not block physical production.

- **no valid configured tax-rate context** — a missing row **or** an invalid persisted value → `tax_rate_percent_snapshot = null`, `tax_rate_effective_at_snapshot = null`, `tax = null`, `margin = null`, `margin_percent = null`;
- missing sale price → the rate snapshots preserve the actual current rate context; `tax`, `margin`, and `margin_percent` are `null`;
- unavailable total cost → the rate snapshots preserve the actual current context; tax may be persisted when the sale price and a valid rate exist; `margin` and `margin_percent` are `null`;
- configured `0.00` rate → `tax_rate_percent_snapshot = "0.00"`, a non-null effective timestamp, and `tax = "0.00"`;
- an invalid persisted tax rate must not be used to calculate or persist tax or margin, and must not be silently converted to zero.

When the current backend state is missing or invalid and the expected context is `null/null`, physical production continues: the actual authoritative production cost and every other physical production snapshot are written normally, alongside the five `null` financial values above.

An invalid raw setting value stays untouched in `app_settings`. Production confirmation must **not** repair the setting, clear the setting, rewrite the setting, audit a setting mutation, persist the invalid value into `ProductionBatch`, or treat the invalid value as `0.00`. The normal existing production audit still belongs to the transactional production flow.

#### API exposure boundary

`C2-II` must expose `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` in the production confirmation response and the `ProductionBatch` **detail** response, so the persisted snapshot is verifiable immediately in this slice. It must **not** yet add them to the `ProductionBatch` list presentation, report read models, or user-facing report UI — those surfaces remain `C2-III` scope. Do not create duplicate API aliases; use the existing production confirmation and `ProductionBatch` detail contracts.

#### Frontend boundary

`C2-II` may make the minimum frontend change required to retain the latest authoritative readiness tax context, always send both required-but-nullable context keys, present `tax_rate_context_stale`, and require the user to refresh readiness before confirming again.

The frontend must not calculate tax or margin, must reuse the existing order-production lifecycle, must not create a second confirmation lifecycle, must not automatically retry a stale conflict, and must not send context from a stale, superseded, or unrelated Order readiness result.

```text
FINAL_MAIN_TS_LINES <= 6399
```

New logic must be extracted into focused order and production modules. No new production module above 300 lines.

#### Tests

The future `C2-II` slice must cover at least: required configured tax context accepted; omitted percent rejected with `422`; omitted effective timestamp rejected with `422`; a one-null pair rejected with `422`; a malformed percentage rejected; a non-canonical percentage rejected; a malformed timestamp rejected; configured → changed stale conflict; configured → cleared stale conflict; unconfigured → configured stale conflict; unchanged configured context accepted; unchanged no-valid-rate context accepted; stale conflict writes nothing; validation failure writes nothing; the transaction-aware service uses the supplied connection; no second independent setting read connection; the actual locked Order sale price used; the actual confirmation total cost used; configured `0.00` persisted correctly; missing sale price persists null dependent values; missing total cost permits tax but not margin; negative margin persisted unchanged; rollback covers snapshots and every production write; the confirmation response exposes the rate snapshots; `ProductionBatch` detail exposes the rate snapshots; the `ProductionBatch` list is not expanded in `C2-II`; no report change; no historical backfill; and the complete backend and focused frontend suites remain green.

Additionally, the invalid-rate lifecycle and the timestamp contract must be covered by at least these 21 cases:

1. required `null/null` accepted when the setting is **missing**;
2. required `null/null` accepted when the setting is **invalid**;
3. invalid readiness returns `tax_rate_invalid`, a null rate context, unavailable financial values, and **no HTTP 500**;
4. invalid readiness does **not** also emit `tax_rate_missing`;
5. a valid expected context against a current **invalid** state returns `409 tax_rate_context_stale`;
6. `null/null` against a current **valid** state returns `409 tax_rate_context_stale`;
7. missing → invalid does **not** create a stale conflict;
8. invalid → missing does **not** create a stale conflict;
9. invalid → valid **does** create a stale conflict;
10. valid → invalid **does** create a stale conflict;
11. an accepted invalid-state confirmation persists null rate snapshots;
12. an accepted invalid-state confirmation persists null tax, margin, and margin percent;
13. an accepted invalid-state confirmation still completes physical production transactionally;
14. the raw invalid value is **never** copied to `ProductionBatch`;
15. confirmation does **not** repair, clear, rewrite, or audit a setting mutation;
16. a canonical `YYYY-MM-DDTHH:MM:SSZ` request timestamp is accepted;
17. an offset timestamp such as `+03:00` is rejected;
18. a fractional-second timestamp is rejected;
19. a timestamp without `Z` is rejected;
20. the database snapshot timestamp uses SQLite UTC text `YYYY-MM-DD HH:MM:SS`;
21. the confirmation and detail API responses normalize the snapshot timestamp to canonical UTC `Z` format.

These `C2-II` requirements were implemented and executed on the `C2-II` PR branch, which is now merged as PR #152.

### C2-III — subdivided into two runtime slices

Статус: `SUBDIVIDED — C2-III-A DONE AND MERGED, C2-III-B AUTHORIZED AFTER THIS PR MERGES`

The ADR 0012 subdivision rule required `C2-III` to be divided before implementation if it was not one bounded, independently reviewable vertical slice. It is not. `C2-III` is therefore divided into **exactly two** runtime slices — `C2-III-A` and `C2-III-B`, no more and no fewer. No document authorizes all of `C2-III` in one PR. No future implementation PR number is assigned to either slice.

#### Goal

Expose backend-calculated readiness estimates and immutable production snapshots in existing user-facing screens (`C2-III-A`), and then make reports and report documents snapshot-backed (`C2-III-B`).

### C2-III-A — Order and ProductionBatch financial presentation

Статус: `DONE — MERGED AND EXACT-HEAD VERIFIED`

Merged as PR #154 — final reviewed head `ef1103811a8f062f9129bfb465a98e0cfa388935`, merge commit `d432fcaee52a16a4f8b609ec160cf3fa2b33d013`, merged `2026-07-28T13:05:34Z`, smoke-tested at that identical head. The scope below is the accepted implemented contract and is retained for reference; it is not reopened.

Delivered exactly within the scope below: two focused frontend modules (`frontend/src/production-financial-contract.ts` and `frontend/src/production-financial-presentation.ts`); the readiness financial block with the three accepted status labels; one shared `Фактическая экономика партии` block used by both the production-success card and the historical batch detail; a compact five-field list summary with the rate snapshots still detail-only; DTO validation that requires the complete readiness financial contract and both `ProductionBatch` rate-snapshot keys; and `frontend/src/main.ts` reduced from `6399` to `6398` lines. No backend production source, formula, persistence, migration, endpoint, report, or report document changed, and no backend test was modified.

One user workflow:

```text
check Order readiness
→ understand the financial estimate
→ confirm production
→ see the persisted actual financial result
```

#### Scope — Order readiness presentation

Display the backend-returned readiness values: `sale_price`, `estimated_cost`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_tax`, `estimated_margin`, `estimated_margin_percent`, and `financial_estimate_status`.

Human-readable status labels: `available` → `Доступно`; `partial` → `Частично`; `unavailable` → `Недоступно`.

Display the accepted backend financial warnings through the **existing** readiness warning mechanism.

The frontend must not calculate tax, calculate margin, calculate margin percent, reconstruct missing values, reinterpret warning codes, read the current Settings tax rate as a substitute for readiness, or recalculate historical values.

#### Scope — ProductionBatch detail presentation

Display the persisted values from the `ProductionBatch` detail DTO: sale price, total cost, the tax-rate percentage snapshot, the tax-rate effective-timestamp snapshot, tax, margin, and margin percent. These are immutable production snapshots; the frontend renders the DTO and performs no arithmetic.

#### Scope — ProductionBatch list presentation

Add only a compact operational financial summary using the existing batch-list financial fields where available: sale price, total cost, tax, margin, margin percent. Do not add the tax-rate snapshot fields to the list — the rate snapshots remain **detail-only**. Do not create a second financial list endpoint.

#### Presentation semantics

The UI must distinguish a real `"0.00"` from unavailable; a negative margin from a zero margin; a negative margin percent from zero; a missing historical snapshot from a configured zero tax; and `partial` readiness from `unavailable` readiness.

Use normal Russian user-facing text. Do not expose raw JSON, internal DTO terminology, stack traces, database representations, or technical timestamp formats without human-readable presentation.

#### C2-III-A constraints

No report backend change; no report DTO change; no `/reports` UI change; no report-document change; no migration; no financial formula change; no `ProductionBatch` persistence change; no historical backfill; no accounting or tax-regime functionality. The frontend remains display-only. `frontend/src/main.ts` final size must be at most `6399` lines, and `main.ts` must contain no financial arithmetic, no DTO validation, no large HTML template, and no financial lifecycle state machine.

Prefer focused frontend modules — `production-financial-contract.ts`, `production-financial-presentation.ts`, `production-financial-feedback.ts`, `production-financial-runtime.ts`, or the current narrower order and production modules when they are a better home. No catch-all `finance.ts`, `utils.ts`, `helpers.ts`, `manager.ts`, or `common.ts`.

### C2-III-B — Snapshot-backed reports and report documents

Статус: `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED`

`C2-III-A` is merged and exact-head verified, so `C2-III-B` is unblocked and is authorized as the **only** remaining C2 runtime slice. It must not be started from the unmerged documentation branch that authorizes it, and **no PR number is assigned**.

#### Authorized boundary

One bounded backend-plus-frontend report vertical:

```text
persisted ProductionBatch financial snapshots
→ backend report aggregation
→ report DTOs
→ /reports presentation
→ overview report consumers
→ generated «Сводка мастерской»
```

**Backend report ownership.** The affected financial reports must read persisted `ProductionBatch` financial snapshots, and the report layer must not recalculate historical tax or margin using the current tax setting. Report tax comes only from persisted `ProductionBatch.tax`; report margin comes only from persisted `ProductionBatch.margin`; historical rate changes never modify existing report results; the current Settings tax rate is never applied retroactively; report calculations remain backend-owned; report endpoints remain read-only; and report reads create no audit records and no business mutations.

**Missing, zero and negative values.** An explicit stored `"0.00"` stays a real known zero; `null` stays unavailable or incomplete; a negative margin and a negative margin percentage stay valid signed information; and a missing historical snapshot stays different from configured zero tax. A null snapshot must never be included as a fabricated `0`, `0.00`, `0 ₽`, or `0%`. Old batches with incomplete financial snapshots must contribute to explicit incomplete-data counters or warnings rather than silently appearing complete.

**Report DTO and UI boundary.** Synchronized changes are authorized in the affected finance report backend model; the affected overview finance summary; the corresponding API schemas; frontend `/reports`; backend-provided report warnings; and document generation for `Сводка мастерской` where it consumes the affected report DTO. The frontend displays backend report DTOs and backend warnings and must not calculate report tax, report margin, report margin percentage, incomplete-data coverage, or historical financial values.

**Report documents.** `Сводка мастерской` stays synchronized with the report DTO it consumes. Newly generated documents may reflect the snapshot-backed report result; previously generated documents remain immutable and are never rewritten, regenerated, or silently replaced; and document generation remains an explicit user action.

**Explicit exclusions.** `C2-III-B` must not change Orders readiness; Order production confirmation; the Order lifecycle; `ProductionBatch` persistence; `ProductionBatch` list presentation; `ProductionBatch` detail presentation; the `C2-III-A` financial presentation modules; tax-rate Settings behavior; migrations; historical `ProductionBatch` rows; or stock and production transactions.

Reports must never add advanced analytics, a tax declaration, accounting reports, tax-regime reporting, or annual/quarterly filing calculations. Only existing report read models that already contain cost, revenue, tax, margin, or margin percent are updated.

#### No new aggregate margin-percent formula

Do not define a new aggregate margin-percent formula. The only accepted aggregate basis already in this repository is the documented `known_margin_percent` rule in `docs/reports.md`, which uses the same complete paired sale-price/cost basis as `known_margin` rather than the global known-revenue total. That contract is preserved unchanged by this authorization.

The `C2-III-B` implementation task must inspect the current report queries; the paired revenue/cost behavior; the incomplete-data counters and warnings; the finance and overview report schemas; the frontend `/reports`; report-document generation; and the existing tests and smoke boundaries **before** modifying the implementation.

In particular, do not silently choose any of these without a later explicit contract: an arithmetic average of batch percentages; a weighted average of batch percentages; aggregate margin divided by aggregate revenue; or recalculation from current settings. If runtime evidence reveals a contradiction between the documented paired basis and the code required for snapshot-backed aggregation, that implementation task must **stop and report the exact conflict** instead of inventing a formula.

#### Frontend ownership boundary — both slices

Render backend DTO values; render `Недоступно` for null historical values; distinguish a configured zero from a missing value; render a negative margin honestly; render readiness financial warnings; render stale-tax-context recovery guidance. Perform no `Decimal` arithmetic, no tax calculation, no margin calculation, and no historical recalculation.

### God-file limit for every future C2 slice

- `frontend/src/main.ts` baseline: `6399` lines; final: at most `6399` lines;
- no calculation logic in `main.ts`;
- no large financial HTML template in `main.ts`;
- no DTO guards in `main.ts`;
- no lifecycle or stale-context state machine in `main.ts`;
- no minification or artificial line joining;
- each new production module normally at most 300 lines;
- each new function normally at most 60 lines;
- no generic `utils`, `helpers`, `manager`, or `common` dumping ground.

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

## 16. Следующее действие

Slice A1 завершён давно; прежняя инструкция «Первое действие после добавления документа» устарела и удалена.

1. `R3` смержен: PR #143, merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`. Отдельный documentation-only PR для закрытия `R3` не создаётся.
2. Проверить и смержить текущий focused test-only PR `R2 — Align import draft baseline test with date normalization`.
3. После merge `R2` бэкенд-базовая линия остаётся `496 / 494 / 2 / 0`; оставшиеся два падения — только backups и exports.
4. Не начинать исправление имён файлов backup/export: оно заблокировано `CR-005` и не имеет slice. Не начинать его с несмерженной ветки `R2`.
5. Не смешивать `R2` с `CR-004`, C1–C4, restore, packaging или release smoke.
6. Не назначать будущий номер PR заранее.

## 2026-07-18 — A3.6 Client Feedback structured validation

- Baseline: PR #119 / A3.5 merged at `e53e7852c8b384915fb77b59345170c43671151c`.
- Verified runtime head for PR #119: `e19229df1afa74f4470864071e91a0e94a5631cd`; complete external exact-head smoke: PASS.
- A3.5: DONE.
- A3.6 Client Feedback structured validation: DONE in PR #120; published head `e148220ac9ad08a0fd952482a0b293f1f2d22bad`, merge commit `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`, exact-head smoke PASS.
- Scope was Client Feedback create only; no edit/delete, no migration, no Orders or Production changes.


### A3.9 current runtime slice

Base SHA: `c6d87df635a5cf7d063b43ffc16dc02d64e08103`. PR #123 / A3.8 is merged with accepted runtime head `34eeaf11dbe7fbfabb3bd36ad8aa79b9469892f5`; final A3.8 exact-head smoke was `PASS — FULL AUTOMATED SMOKE PASSED` as external local evidence, not GitHub Actions. A3.9 hardens Production Confirmation structured errors, transactional rollback evidence, duplicate/stale/wrong-order frontend ownership, and success-with-refresh-failure handling. A3.9 is not DONE until human review, exact-head production smoke, and merge. A4 remains separate.

## B3.1 — Shared feedback for Dashboard and Onboarding

Status: DONE — runtime head `4eed8c2f64d7524607cf25fc696dd964c25213cc`, merge commit `70bbc783452a373afba76bcd8f6fe94c1e7ac75b`, external exact-head smoke PASS.

Baseline: PR #132 is DONE at merge commit `2ce5a4d7ba099603b733e7f2836f417da0614605`; focused frontend test-compilation hardening is complete.

Scope for this slice is intentionally narrow:

- Dashboard initial load/manual refresh feedback and stale-data preservation.
- Dashboard-rendered onboarding start, complete-step, skip, and reset mutation lifecycle.
- Passive Help Center regression coverage for search, filter, reset, article selection, and related-section navigation.

B1 fixture/backend implementation and B2 backend read-model implementation are not required based on the diagnostic audit. B2 browser presentation evidence is completed only if the B3.1 exact published-head smoke actually passes. B3.2 Alerts and Purchases remains the next route batch.

## B3.3 — Local artifacts and reports shared-feedback lifecycle (DONE)

- B3.1 is DONE: Dashboard, Onboarding, and passive Help shared-feedback lifecycle.
- B3.2a is DONE: Alerts shared-feedback lifecycle.
- B3.2b is DONE: Purchases shared-feedback lifecycle.
- PR #135 is merged at `b11160cc1a06df24fa6666969154c37389e6ab65`.
- PR #136 is merged; B3.3 is complete at merge commit `e7c2d97473070f361052325fd6476208629af1cc`.
- B3.3 scope remains `/backups`, `/exports`, `/report-documents`, and `/reports`.

## B3.4+B3.5 — Core workspace shared-feedback lifecycle (DONE)

- PR #137 is merged at `10e985229e8020fcf98c67427cde889b5cd934f8`.
- Formula/Client Workspace and Inventory/Catalog Workspace shared-feedback lifecycle is complete.

## B3.6 — Order-to-production shared-feedback lifecycle (DONE)

- Starting `main` SHA: `10e985229e8020fcf98c67427cde889b5cd934f8`.
- Bounded scope: `/orders` list, reference and detail reads; create/update; cancel/archive; readiness; Production Confirmation; production request and history handoff; exact original-Order production reconciliation.
- Lifecycle ownership: route generation, exact Order context, request generation, validated DTO boundaries, exactly-once accepted settlement, retained readable snapshots/drafts, request-owned announcements, and route-owned focus.
- Production safety: one POST per accepted confirmation; no automatic production retry; uncertain or untrusted outcomes create an exact original-Order obligation that only a coherent exact Order plus its exact ProductionBatch can clear.
- Backend production semantics, APIs, schema, migrations, and persistence remain unchanged.
- PR #138 accepted runtime head: `a8cf9d3e21aa46af3f9b2837a44b918cad638910`; merge commit: `bac8672ecb04c96e25bf00c50cfba07f79eadb99`.
- PR #139 accepted runtime head: `9ee94810f4dddbc03faf8c7cdbe188faa43a4e72`; merge commit: `c33e7f32decabe74de68051ccdc9e87d75c58cb6`.
- The Backups narrow-width blocker found during the first smoke attempt is closed.
- Final exact-head integration verdict: `PASS — FULL AUTOMATED SMOKE PASSED` on `9ee94810f4dddbc03faf8c7cdbe188faa43a4e72`.
- B3 implementation and its deferred full integration-smoke gate are complete. Block B has since been closed by B4.1 / PR #141; see sections 3 and 10.
