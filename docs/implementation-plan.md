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

**Block B is complete.** B4.1 was the last runtime slice of Block B and is merged.

- Current baseline `origin/main`: `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` — the PR #141 merge commit, merged `2026-07-26` (VERIFIED FROM REPOSITORY / GITHUB).
- PR #141 — `B4.1 — Dashboard safe GET timeout and recovery`: final reviewed head `d0cde127355b146f101ddf3769d76d0226c71ec0`; merge commit `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` (VERIFIED FROM REPOSITORY / GITHUB).
- Accepted Dashboard/Onboarding focused suite for the final reviewed head: `42/42` (SUPPLIED TASK BASELINE).
- Accepted frontend production build: `PASS` (SUPPLIED TASK BASELINE).
- Accepted PR #141 backend branch-only failure delta: `0` (SUPPLIED TASK BASELINE).
- Accepted browser, keyboard, responsive, network, and exact-head smoke: `PASS` — SUPPLIED TASK BASELINE — product-owner-verified exact-head smoke of PR #141 on 2026-07-26; not re-run in this documentation task.
- Complete backend baseline: `496 collected, 492 passed, 4 failed, 0 skipped` — re-executed from `backend/` in the Block B closure task with zero drift (EXECUTED IN THIS TASK).

The four backend baseline failures are not regressions from PR #141 and are now handled by an explicit gate rather than being carried as loose findings.

The active next implementation window is **Pre-release hardening — backend baseline correction gate** (section 10). No runtime feature slice is active. No future PR number is assigned.

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

# 10a. ACTIVE WINDOW — Pre-release hardening: backend baseline correction gate

Статус: `IN PROGRESS`

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with the documented date-normalization contract`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED / DECIDED**
- Next correction slice: `R4 — Canonical backup/export filename reason normalization`
- `R4` status: `AUTHORIZED AFTER THE CR-005 DECISION PR MERGES — NOT IMPLEMENTED`

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

Статус: `AUTHORIZED AFTER THE CR-005 DECISION PR MERGES — NOT IMPLEMENTED`

**`R4` IS NOT IMPLEMENTED.** It may begin only after the `CR-005` decision pull request is merged, and only from `origin/main`. It must not be started from the unmerged decision branch.

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
3. `R4` — **AUTHORIZED, NOT IMPLEMENTED**. Canonical backup/export filename reason normalization, covering nodes 1 and 2 in one bounded slice. Unblocked by the accepted `CR-005` decision; may begin only after the decision PR merges. Contract above.

`R3` and `R2` tied on primary priority; `R3` preceded `R2` on greater direct user/data impact because it restored execution of a real no-mutation guarantee that was unverified at the API layer. Both were fully evidenced from repository sources alone and needed no product decision, which is why one could be activated while the filename nodes could not. `R3` and `R2` are both now merged and DONE. Slice contracts live in `state/current-focus.md` and `docs/backend-baseline-failure-triage.md`.

`R3` and `R2` were test-only, so their required smoke was the **backend suite only**. `R4` is different: it changes runtime services, so it additionally requires the focused frontend suites, the frontend production build, and the focused `/backups` and `/exports` browser smoke specified in the `R4` contract above.

## Separate candidate — not activated

**Potential backup consistency finding — not classified or activated.**

The current backup helper copies the SQLite database file through `shutil.copy2`, and the startup before-migration path uses the same helper. This raises a transaction-consistency question when the database may be live or use auxiliary SQLite files. Some existing tests pass ordinary bytes rather than a real SQLite database to the helper, so a future diagnostic must inspect those fixtures.

This task records only the need for a separate evidence-based diagnostic.

Do not classify the behavior as unsafe and do not prescribe a correction design here.

## Remaining release obligations

Clearing these four failures does **not** make the product release-ready. The following stay outside the active slice and are not activated here: final macOS `.app`/`.dmg` and user-ready launch; packaged update flow and update smoke; verified user/remote installation process; Restore product decision and implementation; C1 tax setting; C2 cost, tax, and margin completion; C3 user-facing read-only AuditLog workspace; full release-candidate smoke; continued documentation accuracy. See section 7 and sections 11–13.

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
