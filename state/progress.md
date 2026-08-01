# Progress

## Current phase

`C1 — COMPLETED`. `C2 — COMPLETED`. `C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED`. `C3-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED`. `CR-009 — ACCEPTED`. `C3-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED`. The broader C3 obligation is incomplete.

## Current next step

- Run the `CR-006` evidence-only diagnostic: establish whether the JSON export create-response fallback is reachable, then define the required contract. Diagnostic only — no export AuditLog implementation, no C3-II-B2 authorization, no migration, no production change.
- Keep C3-II-B2 blocked by CR-006 and C3-II-B3 blocked by CR-004; both change requests stay `needs evidence`.
- Keep C4, Restore, packaging, installation, update and release-candidate work inactive.

## 2026-08-01 — C3-II-B1 merged and closed

- **Milestone:** `C3-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED`.
- **Merged facts:** PR #163, base `main`, state `MERGED` at `2026-08-01T05:30:38Z`; head branch `claude/c3-ii-b1-report-document-audit`; final reviewed head `afd65fd2878fa02a0d4dc4963812c80644a4e787`; merge commit `ef0297e41a731f082a2a21a46b361aa9aac36cfa`. The final reviewed head is an ancestor of the merge commit, and the merge commit is an ancestor of `origin/main`.
- **Accepted merged PR #163 evidence — not re-executed in the closure documentation PR:** complete backend + launcher suite `1550 passed / 0 failed`; backend collection `1533`; all `1376` original backend baseline node IDs preserved with `0` missing and `157` added; complete launcher suite `17 passed / 0 failed`; all `19` frontend `test:*` scripts passed; frontend build `PASS`; final exact-head launcher smoke `PASS` on `afd65fd`; final audit with no unresolved P0 or P1 findings (`P0 — none`, `P1 — none remaining`, `P2 — documented and non-blocking`). The focused exact-head launcher smoke is not release smoke.
- **Delivered on merged `main`:** the `0020_artifact_audit_operations` ledger, the idempotent write-serialized finalizer, startup and pre-create reconciliation, `report_document.created`, additive `audit_status` / `audit_message` / `pending_audit_count`, and the frontend success-plus-separate-warning presentation.
- **Next authorized work:** the `CR-006` evidence-only diagnostic of JSON export create-response fallback reachability and the required product contract. C3-II-B2 implementation is **not** authorized.
- **Lifecycle unchanged:** `C3-II-B2` blocked by CR-006, `C3-II-B3` blocked by CR-004, `CR-006` and `CR-004` both `needs evidence`, C3 incomplete, C4 inactive, product release readiness not claimed.
- **Documentation-only scope of the closure PR:** no production, migration, dependency, lockfile or test-code change; no product suite re-executed.

## HISTORICAL SNAPSHOT — SUPERSEDED — 2026-07-31 — C3-II-B1 implemented on a PR branch (not merged)

> True while PR #163 was open and unmerged. The implementation record below stands; its lifecycle statement and its per-head evidence counts are superseded by the `2026-08-01` closure entry above, which records the merged final head `afd65fd` and its `1550 passed / 0 failed` result.

- **Baseline:** branched from verified `origin/main` = `385873fa9f393f9dc4dcac14e7bc79e0da12c5d1` (PR #162 merge commit) with a clean worktree. Branch `claude/c3-ii-b1-report-document-audit`.
- **Migration:** `0020_artifact_audit_operations`, registered exactly once after `0019`. One table plus a partial unique index on the active `(artifact_kind, primary_filename)` identity and a kind/status lookup index. `CHECK` constraints pin the status, artifact-kind and audit-action vocabularies, require an `audited` row to carry its `audit_logs.id` and a non-`audited` row to carry none, and require a `report_document` row to record its companion sidecar. No legacy backfill, no artifact touched, no AuditLog row created by the migration.
- **Reservation:** report-document creation validates the request, runs one bounded pre-create reconciliation pass, advances the existing deterministic numeric-suffix identity search — now also treating an active ledger identity (primary *or* companion name) as a collision — commits one `prepared` row, and only then writes either file.
- **Preparation failure:** exact HTTP `500` `artifact_audit_tracking_unavailable` with the accepted Russian message and next action. No document, sidecar, AuditLog row or committed ledger row; no raw SQLite text, SQL or stack trace. Existing `422` format validation still takes precedence.
- **Compensation:** an incomplete pair keeps its existing Russian error and file cleanup, and the operation is marked `abandoned` best-effort; a failure to transition preserves the original error and leaves the operation for reconciliation.
- **Verification:** one shared verifier for immediate finalization, startup reconciliation and pre-create reconciliation. It classifies a pair as `valid`, `definitely_absent` or `ambiguous`, never rerenders, never compares against current report data, and never rewrites a document or sidecar. Ambiguous pairs stay unresolved, counted and warned about rather than guessed at.
- **Exactly-once finalization:** verification happens outside the write transaction; the transaction uses one caller-owned connection with `BEGIN IMMEDIATE`, re-reads the operation, returns an existing `audit_log_id` without inserting when already `audited`, and commits the AuditLog insert together with the `audited` transition or neither. A ledger-update miss rolls the insert back. Proven for sequential repeats, startup-then-pre-create, and two concurrent finalizers.
- **API:** additive `audit_status` (`recorded` | `pending`) and `audit_message` on create, bound by a model validator so an inconsistent pair cannot be returned; additive `pending_audit_count` on status. Every existing field and the exact `Документ отчета создан.` message are preserved. A verified pair with a failed Journal write returns `201` + `pending`, never `409` or `500`.
- **Read-only endpoints:** status, list, download and `GET /api/audit-logs` reconcile nothing, write nothing and change no artifact bytes.
- **Startup:** bounded reconciliation runs strictly after successful initialization and migrations and before the API is served. It never raises, so one pending event cannot make the app unusable — but migration and database-initialization failures still propagate untouched. The `before_migration` backup still runs before migrations, is not audited and creates no ledger row.
- **Privacy:** the event is `report_document.created` / `report_document` / `operation_id` / `user` / `Report document created`, with metadata of exactly `operation_id`, `document_type`, `format`, `reconciled_after_failure`. No filename, path, request reason, Workshop profile, report content or count is persisted; the action is not added to the suffix allowlist; no Journal details route was added.
- **Frontend:** a focused `report-document-audit-contract` module classifies the response; `main.ts` gained only wiring and shrank from `6399` to `6393` lines. Recorded success renders as before; pending renders success plus a separate warning region; an invalid audit contract routes into the existing reconciliation path and never re-POSTs; the standing pending-count warning clears only on a later status read of zero.
- **Review corrections (second PR head):** `run_local_runtime` now passes the startup-selected database path to the uvicorn child via `COSMETIC_WORKSHOP_DB_PATH`, overriding any inherited value, so startup backup, migration `0020`, reconciliation and the served API all use one database in both user and development mode. `pending_count()` no longer fabricates `0` on a ledger read failure; it surfaces through the existing service/API boundary as fixed Russian text with no SQLite detail, and status stays read-only. The frontend now requires an explicit `audit_message: null` for `recorded`, and parses `pending_audit_count` as `number | null` so a missing or malformed value cannot clear a real warning. The stale launcher `ALLOWED_TABLES` copy was replaced with the shared `app.tests.table_guards`.
- **Evidence:** complete suite `1539 passed / 0 failed` (backend and launcher), with all `1376` baseline node IDs preserved and `149` added; focused backend report-document suites `142 passed`; complete launcher `14 passed / 0 failed`; all `19` frontend `test:*` scripts `945 passed / 0 failed`; frontend build `PASS`.
- **Lifecycle unchanged:** `C3-II-B2` blocked by CR-006, `C3-II-B3` blocked by CR-004, C3 incomplete, C4 inactive, product release readiness not claimed.

## 2026-07-30 — C3-II-A closed; CR-009 accepted; C3-II-B subdivided

- **Verified merged closure:** PR #161 `C3-II-A — Implement atomic workshop-profile AuditLog coverage`, state `MERGED`, base `main`, final reviewed and smoke-tested head `6c327630d0e4cca3c566253bf9f8224aaaa33172`, merge commit `3fec160f08aa7e775aa3e7ea650e570bf48955ad`, merged `2026-07-30T08:11:41Z`. Both commits are ancestors of `origin/main`, which was exactly the merge commit with no later commits at branch start.
- **Honest evidence attribution:** exact-final-head `6c327630d0e4cca3c566253bf9f8224aaaa33172` has `PASS — EXACT-HEAD C3-II-A FOCUSED SMOKE PASSED`. Focused backend `591 passed / 0 failed / 0 skipped`, complete backend `1376 collected / 1376 passed / 0 failed / 0 skipped`, all `1364` baseline node IDs preserved with `12` added, all `18` frontend `test:*` scripts, focused AuditLog frontend `92 passed`, `TZ=Europe/Amsterdam` focused AuditLog frontend `92 passed`, and frontend build `PASS` were executed on `354104cc326f1e1374324ef9128e5ef771a4a063`. The final documentation-only head was production/test byte-identical, but those suites were not rerun there and are not relabelled as exact-final-head runs. The exact-head focused smoke is not release smoke.
- **CR-009 accepted:** one new accepted change-request row, no Target PR, with the durable decision in `docs/decisions/0013-file-backed-artifact-audit-semantics.md`. A verified artifact is authoritative; audit-finalization failure preserves it and returns HTTP `201` with `audit_status: pending` plus a separate Russian warning.
- **Bounded ledger:** backend-generated canonical lowercase UUID `operation_id`; exact typed fields and status `CHECK`; statuses `prepared`, `pending_audit`, `audited`, `abandoned`; commit `prepared` before file creation; one active operation per artifact identity; insert exactly one AuditLog row and mark `audited` in one caller-owned write-serialized SQLite transaction; no generic outbox/event bus/job queue.
- **Filename privacy correction:** internal safe relative filename fields are required for deterministic reconciliation. Report-document filenames contain no request reason; future B2/B3 primary filenames may contain the canonical filename-derived reason segment accepted by CR-005. There is no separate reason column or separately stored raw human/request/export-manifest reason. Filenames, paths and reasons remain strictly prohibited from AuditLog and `GET /api/audit-logs`; CR-005 is not reopened and existing artifacts are not renamed or rewritten.
- **B1 result/status contract:** preparation failure is exact HTTP `500` `artifact_audit_tracking_unavailable` and creates no file, metadata, audit or prepared row. Pending HTTP `201` names only next startup and next document creation as retry triggers. `pending_audit_count` counts `report_document` operations in `prepared`/`pending_audit`, excludes `audited`/`abandoned`, and is read without reconciliation or false failure presentation.
- **Finalizer and verification:** B1 compatibly returns `cursor.lastrowid` from `AuditLogRepository.create_log(...)`; finalization serializes writers, returns an existing audited ID, inserts only from unresolved states and commits audit plus ledger together or neither. The document pair must pass the exact twelve-point safe filename/path/file/metadata identity and size contract; malformed, unsafe or ambiguous pairs remain unresolved and are never audited, deleted or rewritten.
- **Reconciliation:** run only after successful initialization and migrations before the ordinary UI, and once before the next report-document create; inspect only recorded safe filenames under the expected directory; no GET/list/status mutation, background thread, unbounded retry, directory scan or legacy backfill. One pending-event failure does not make startup or the older artifact fail and does not hide independent initialization/migration failure. `before_migration` startup backups remain outside CR-009 and before migrations.
- **Subdivision:** C3-II-B1 alone is `AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED`; C3-II-B2 is `BLOCKED BY CR-006 — NOT AUTHORIZED`; C3-II-B3 is `BLOCKED BY CR-004 — NOT AUTHORIZED`. C3 remains incomplete; C4 remains inactive; product release readiness is not claimed.
- **Documentation-only scope:** no runtime, test, migration, schema, dependency, lockfile, generated-file or local-artifact change. Runtime tests, builds, API/browser smoke and migration execution were not run because this is a Level 0 documentation-only PR.

## HISTORICAL — SUPERSEDED — 2026-07-30 C3-II-A implemented on PR branch

> This section was true before PR #161 merged and CR-009 was accepted. It is
> preserved as the implementation-branch record.

- **Baseline:** branch `codex/c3-ii-a-atomic-workshop-profile-audit` from exact `origin/main` `4ef02b8478c3eba06883f5b71290f91edb42a871` (PR #160 merge commit); clean start; baseline backend collection `1364`.
- **Runtime:** canonical Workshop-profile mutations now read, compare, upsert and append exactly one `workshop_profile.updated` row on one caller-owned SQLite connection and transaction. Failure of either persistence step rolls the whole mutation back.
- **No-op and empty behavior:** canonical identical saves perform no upsert or audit and preserve `updated_at`; missing-row + empty is a no-op; existing-empty + empty is a no-op; configured-to-empty persists canonical empty JSON without deleting the row and audits once.
- **Privacy:** persisted summary is exactly `Workshop profile updated`; metadata is limited to `setting_key`, sorted `changed_fields`, `changed_field_count`, `previous_configured`, and `new_configured`; no profile values, raw payloads, timestamps or `source`.
- **Presentation:** action vocabulary is 51; entity vocabulary remains 19; suffix allowlist remains 21. `workshop_profile.updated` presents as `Профиль мастерской изменён` / `Настройка приложения` / `Профиль мастерской обновлён`.
- **Compatibility:** existing profile endpoints and response shape remain unchanged; no frontend production file, migration, schema, repository, backup, export or report-document production service changed.
- **Lifecycle:** `C3-II-A — IMPLEMENTED ON PR BRANCH — NOT MERGED`; `C3-II-B — NEEDS PRODUCT DECISION — NOT AUTHORIZED`; `C3 — INCOMPLETE`; `C4 — INACTIVE — NEEDS PRODUCT DECISION`; product release readiness is not claimed.
- **Verification before publication:** focused backend `591 passed`; complete backend `1376 collected / 1376 passed / 0 failed / 0 skipped`; every `1364` baseline node ID remains collected and `12` new nodes were added. All `18` frontend `test:*` scripts passed, including `test:settings-tax-feedback` (`52 passed`) and `test:audit-log-workspace` (`92 passed`) in both default time zone and `TZ=Europe/Amsterdam`; production build passed. Exact published-head smoke evidence belongs to the PR and the external `/tmp` smoke report; this committed lifecycle record does not claim that publication-only check.

## HISTORICAL — SUPERSEDED — 2026-07-30 C3-I closed; atomic workshop-profile audit slice authorized

> This documentation-only state was true before C3-II-A implementation began. It is superseded by the implementation entry above.

- **Verified start gate.** Repository `Mitronomik/cosmetic-workshop-os`; PR #159 `MERGED`, base `main`, final reviewed and published head `bf7cde060a43190fdf22c612a16b0c137aa5531b`, merge commit `ba3ca7443e3280bc7f700af11e75dc4fa810665f`, merged `2026-07-30T03:20:23Z`; both commits ancestors of `origin/main`; `origin/main` exactly the merge commit; clean tree including untracked files; zero open PRs; no existing exact documentation-task branch.
- **`C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED`.** `GET /api/audit-logs` and `/settings/audit-log` are on merged `main`.
- **Honest evidence attribution.** Exact-final-head `bf7cde060a43190fdf22c612a16b0c137aa5531b`: focused frontend `92 passed / 0 failed / 0 skipped` in default and `TZ=Europe/Amsterdam`; all frontend `test:*` scripts pass with `0 failed / 0 skipped`; build `PASS`; `frontend/src/main.ts` `6380`; browser smoke `PASS — EXACT-HEAD BROWSER SMOKE PASSED`, 60 scenarios. Backend `1364 passed / 0 failed`, focused backend `422 passed`, 942 preserved node IDs and API smoke `150 checks / 0 failures` ran on `2848880f2009158749398aec7d504c0364336ba9`; the backend tree is byte-identical at `bf7cde060a43190fdf22c612a16b0c137aa5531b`, but those results were not re-executed or relabelled as exact-final-head results.
- **`C3-II-A — AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED`.** One real canonical workshop-profile update and exactly one safe `workshop_profile.updated` row must share one caller-owned SQLite transaction. Failure of either write commits neither; canonical no-op preserves `updated_at` and writes neither. No profile value may enter audit summary or metadata. Existing API/UI and historical documents remain compatible.
- **`C3-II-B — NEEDS PRODUCT DECISION — NOT AUTHORIZED`.** Manual backup, JSON export and report-document generation are file-backed. Artifact-success/audit-failure semantics, feedback, compensation, authority, retry/reconciliation, duplicates, startup recovery and smoke remain undecided.
- **Lifecycle:** `C3 — INCOMPLETE`; `C4 — INACTIVE — NEEDS PRODUCT DECISION`; product release readiness not claimed. Restore, packaging, installation, update and release-candidate smoke remain open. `CR-004` and `CR-006` are unchanged.
- **Scope:** Markdown only. No production code, tests, configuration, schema, migration, dependency, lockfile, generated artifact or user data change. No future implementation PR number assigned.
- **Verification:** Level 0 documentation checks passed. `git status --short --untracked-files=all` was clean after commit; `git diff origin/main...HEAD --check` passed; `git diff origin/main...HEAD --stat` completed; and `git diff origin/main...HEAD --name-only` confirmed that every changed path is Markdown. The semantic stale-claim audit passed. No runtime tests, builds or runtime smoke were executed because this is a documentation-only PR.

## HISTORICAL — SUPERSEDED — C3-I implemented on its PR branch, not merged (2026-07-29)

> This dated section was true before PR #159 merged. It is preserved for traceability and superseded by the 2026-07-30 closure entry above.

Branch `codex/c3-i-read-only-audit-log-workspace`, from clean `origin/main` `fa433d03acbf68e16b14ba6245885ab9eaf15c35`. Durable contract: `docs/audit-log.md`. **Not merged, not `DONE`, not release-ready.**

- Backend read path: `GET /api/audit-logs` only, through `backend/app/api/audit_logs.py`, `backend/app/services/audit_logs.py`, read methods on `backend/app/repositories/audit.py`, the pure `backend/app/domain/audit_log_presentation.py` and `backend/app/domain/audit_log_query.py`, and `backend/app/schemas/audit_logs.py`.
- Backend-owned safe labels and `display_summary`: 50 action labels, 19 entity labels, 2 actor labels, three unknown-code fallbacks, and the exact 21-action suffix allowlist with its exact persisted prefixes.
- `DomainIssueCode.PAGINATION_OUT_OF_RANGE` added — the only new enum member and the only schema-adjacent change. **No migration.**
- Frontend `/settings/audit-log` («Журнал действий») under `Данные и настройки`, with automatic re-entry refresh, separate draft/applied filters, a pending-filter hint, disabled load-more while filters are dirty, focus-preserving targeted updates and renders, deterministic local-time/DST rejection, and every required loading, empty, filtered-empty, failure, stale-response, duplicate-request, narrow-layout and accessibility state.
- Focused frontend modules `audit-log-contract.ts`, `audit-log-local-time.ts`, `audit-log-presentation.ts`, `audit-log-workspace.ts`, `audit-log-bindings.ts`, `audit-log-dom.ts`, plus the extracted route table `app-navigation-routes.ts`; `frontend/src/main.ts` went `6398` → `6380`.
- New focused frontend script `test:audit-log-workspace` with its own TypeScript project, bringing the `test:*` script count from `17` to `18`.
- Review-correction results: focused backend `422 passed`; complete backend `1364 passed / 0 failed / 0 skipped`; all `942` merged-baseline node IDs still collected with zero renames; focused frontend `82 passed / 0 failed / 0 skipped` in both the normal and `TZ=Europe/Amsterdam` runs; all `18` frontend test scripts pass; production build `PASS`; `git diff --check` clean.
- Extreme pagination is bounded at `offset=9223372036854775807`; arbitrary 5000-digit positive and negative values receive their structured `422` classifications without reaching unsafe integer conversion or SQLite, and rejected reads remain read-only.
- Exact-head API and browser smoke for the correction commit is recorded in PR #159. The smoke at `749c51992c43af65f8297acb0979aded86fdb607` applies only to the previous head and is superseded for merge-readiness.
- Read-only throughout: no AuditLog write-call-site change, no business mutation, no file creation, no setting change, and historical rows byte-identical before and after reads.
- Known gap retained, not closed: backup, export, report-document and workshop-profile actions are still unaudited (`docs/audit-log.md` § 11.6). A true process `source` stays deferred.

## Done
- Architecture draft
- Final roadmap draft
- Frontend concept draft
- Codex project structure rules
- Codex prompting rules
- PR testing and smoke rules
- Product specification
- Domain model
- Repository starter structure and documentation placement
- Documentation structure review against project contracts
- Nested `AGENTS.md` contracts expanded for backend, frontend, launcher, docs, ADRs, state, help and scripts
- Minimal backend app shell with `/api/health` and `/health`
- Backend health endpoint tests
- Minimal frontend shell with Russian navigation placeholders and dashboard placeholder
- Minimal project commands for PR1 test/build/dev guidance
- PR1 follow-up: frontend `typescript` devDependency declared and `npm run dev` now builds before serving `dist`
- PR1 follow-up: temporary backend ASGI fallback removed; FastAPI is now the only backend runtime path
- PR1b branding pass: compact sidebar brand area, existing monogram/logo usage, warm cream/deep brown/rose-gold styling, favicon wiring, responsive shell refinements
- PR2 SQLite persistence foundation with test-friendly database configuration
- PR2 stable repository-root default development database path with `COSMETIC_WORKSHOP_DB_PATH` override
- PR2 migration helper and initial infrastructure migration for `app_settings` and `audit_logs` only
- PR2 technical API endpoints for database status and app settings with no hidden migration side effects
- PR2 tests for temporary database initialization, idempotent migrations, stable path behavior, explicit initialization, infrastructure table presence, endpoint behavior, and no business table creation
- PR3 user data directory resolver for `~/Documents/Мастерская косметолога/` with `data`, `backups`, `exports`, `attachments`, and `logs` paths
- PR3 optional `COSMETIC_WORKSHOP_USER_DATA_DIR` override for user-mode data directory resolution
- PR3 explicit startup initialization service that creates user data directories and applies migrations only when called
- PR4 backend backup service for copying existing SQLite databases into user-data `backups/` without modifying or overwriting the source
- PR4 user-mode startup backup-before-migration guard for existing databases with pending migrations
- PR73 manual backup API foundation with `GET /api/backups/status`, `GET /api/backups`, and `POST /api/backups`; status/list are read-only, create copies only the configured SQLite database, no restore/UI/migrations/business mutations were added.
- PR5 backend-only Decimal parsing and quantization helpers for grams, milliliters, percentages, money, counts, and density
- PR5 MVP unit primitives for grams, milliliters, percent, and pieces with canonical codes and Russian labels
- PR5 lightweight measurement value objects for weight, volume, percentage, money, quantity/count, and density
- PR5 density conversion foundation that converts ml to grams only with an explicit density and returns a missing-density warning otherwise
- PR6 `ingredients` migration with no stock, lot, recipe, client, order, production, import, packaging, or purchase tables
- PR6 backend ingredient domain category/unit/name/density validation using existing Decimal/Density primitives with missing density allowed
- PR6 repository/service/API foundation for create, read, list active, full PUT update, and deactivate ingredients, plus minimal ingredient audit events
- PR7 local runtime launcher MVP with localhost-only config, explicit user-mode startup initialization, backend process launch helper, optional browser opening, launcher tests, and docs
- PR8 backend onboarding state stored as typed JSON in `app_settings` without adding a new table
- PR8 thin onboarding API for read/start/complete-step/complete/skip/reset with minimal audit events for started, step completed, and completed
- PR8 frontend first-run welcome/checklist skeleton in Russian with graceful backend-unavailable fallback and small empty-state text for Recipes, Clients, and Stock
- PR8 follow-up separates true completion from skip/close behavior so skipped onboarding does not falsely mark all checklist steps complete
- PR9 `ingredient_lots` migration with ingredient relationship, cost/shelf-life/supplier/density metadata, and no stock movement or remaining balance fields
- PR9 backend ingredient lot domain validation using existing UnitCode, Decimal money quantization, and Density primitives with missing density/costs allowed
- PR9 repository/service/API foundation for create, read, list active, list by ingredient, full PUT update, and deactivate ingredient lots, plus minimal lot audit events
- PR10 `stock_movements` migration for immutable ingredient-lot movements with no stored lot balance or `remaining_quantity` columns
- PR10 backend stock movement domain validation for Decimal quantities, allowed stock units, direction/type consistency, no floats, no percent units, and whole-number pieces
- PR10 repository/service/API foundation for create, read, list, list by lot, derived lot balance, negative-balance prevention, and minimal `stock_movement.created` audit events
- PR10 hotfix: test-only allowed/forbidden table guards now treat `stock_movements` as current and keep future business tables forbidden

- PR11 `packaging_items` migration for cosmetic workshop packaging/tare definitions with no packaging stock movements, packaging balances, lots, or stored quantity columns
- PR11 backend packaging item domain validation for stable MVP kind codes, pieces-only unit, optional positive Decimal capacity in ml/g, optional non-negative Decimal unit cost, no floats, and normalized names/text fields
- PR11 repository/service/API foundation for create, read, list active, full PUT update, and deactivate packaging items, plus minimal packaging audit events
- PR11 table guard update treats `packaging_items` as current while recipe/client/order/production/import/backup future tables remain forbidden
- PR11 hotfix: `test_stock_movements.py` now uses the centralized test-only table guard helpers instead of stale local allowed/forbidden table sets.

- PR12 transactional write service foundation adds a small SQLite transaction helper and moves ingredient, ingredient lot, stock movement, packaging item, and audited onboarding state writes into service-level transactions so business writes and audit logs commit or roll back together.
- PR12 repository write methods can accept a shared SQLite connection while preserving standalone repository behavior for callers that do not pass one.
- PR12 rollback tests cover audit failure for ingredient, ingredient lot, stock movement, packaging item, and onboarding writes; stock movement rollback leaves derived lot balance unchanged.

- PR13 `packaging_stock_movements` migration for immutable packaging/tare stock movements with no stored packaging balance, no `current_quantity`/`remaining_quantity`, and no packaging lots.
- PR13 backend packaging stock movement domain validation for positive integer pieces only, stable MVP movement types, no floats, no fractional pieces, no percent/ml/g/arbitrary movement units, and active packaging item requirements.
- PR13 repository/service/API foundation for create, read, list, list-by-packaging-item, and movement-derived packaging item balance, plus negative-balance prevention.
- PR13 transactional `packaging_stock_movement.created` audit event so audit failure rolls back movement creation and leaves derived balance unchanged.
- PR13 follow-up replaced the packaging stock movement `packaging_item_id` validator with packaging-specific validation messages so invalid tare selection no longer references ingredients/components.
- PR58 client wishes and feedback UI plus follow-up fixes preserving client-card drafts are complete.


- PR99 documentation/governance: project UI/UX contract, project-owned Codex UI guidance, repository UI boundaries, and canonical `Склад` navigation wording.
- PR100 documentation/governance: reviewed Impeccable provenance plus safe project-owned non-executable UI guidance; upstream skill not activated.
- PR101 documentation/governance: Taste Skill review recorded as not approved; no upstream content, scripts, dependencies, hooks, or active skill installed.

## In progress

- Slice A3 remains IN PROGRESS after A3.6 because Orders, Production Readiness, and Production Confirmation remain separate future slices.
- PR #96 is reviewed as superseded by current main; actual GitHub state is open, so closure remains pending and is not claimed here.

## Next

- Prepare A3.7 Orders structured validation as a separate focused runtime PR with no future PR number assigned yet.
- Keep Production Readiness, Production Confirmation, schema/migration/dependency/CSS changes, browser dependency installation, CI, responsive-table containment, and unrelated runtime behavior out of A3.7.

## Important notes
- PR13 intentionally does not add packaging lots, purchase suggestions, production, recipes, clients, orders, import/export, frontend UI, launcher changes, or cloud/mobile/auth behavior.
- PR12 intentionally does not add migrations, tables, API routes, frontend changes, packaging stock movements, recipes, clients, orders, production, import/export, or cloud/mobile/auth behavior.
- PR11 intentionally does not add packaging stock movements, packaging lots, packaging balances, `remaining_quantity`, `current_quantity`, purchase suggestions, production consumption, or frontend packaging UI.
- PR10 intentionally does not add `remaining_quantity`, materialized balance tables, production write-off logic, FEFO allocation, packaging movements, or frontend inventory UI.
- Stock movement balances are derived by summing immutable movement rows for a lot; corrections should be represented by new movements rather than editing/deleting existing rows.
- PR9 intentionally does not add `remaining_quantity`, stock movement tables, production write-off logic, FEFO allocation, or frontend inventory UI.
- Ingredient lot `unit` is restricted to grams, milliliters, or pieces; percent is rejected as a lot stock unit.
- Lot creation/update rejects missing and inactive ingredients; inactive lots are hidden from active list endpoints.
- Missing lot density is accepted and no density fallback is assumed.
- Costs and density are Decimal-backed and stored as strings in SQLite.
- Tests and smoke use temporary directories/databases and should not write real user data.

- PR14 backend inventory read models: added read-only ingredient lot balance, packaging balance, and inventory overview DTO/service/repository/API layers. Balances are derived from immutable stock movement history; no stored balance fields, migrations, tables, frontend UI, alerts, purchase list, production, recipes, clients, or orders were added.
- PR15 inventory overview UI foundation: added a read-only `/inventory`/`Склад` frontend screen that consumes existing PR14 inventory read endpoints for overview cards, ingredient lot balances, and packaging balances. It includes loading, empty, and error states and intentionally adds no write forms, backend migrations, alerts, purchase list, production, recipes, clients, or orders.

- PR16 ingredient/component directory UI foundation: added a `/ingredients`/`Компоненты` frontend screen that consumes existing ingredient endpoints for active-list, create, full update, and soft deactivation. It includes loading, empty, and error states and intentionally adds no lots, stock movements, packaging write flows, recipes, clients, orders, production, purchase list, alerts, migrations, or new tables.

- PR16 follow-up aligned frontend ingredient category options with backend IngredientCategory codes and labels, and clears stale ingredient form errors after successful saves/deactivation.

- PR16 follow-up aligned frontend ingredient unit options with backend UnitCode values, including percent (`%`).


- PR17 backend recipe model foundation: added `RecipeTemplate -> RecipeVersion -> RecipeIngredient` tables, domain validation, service/repository/API endpoints, and transactional audit events for create/deactivate operations. No calculation service, percent-sum validation, recipe UI, clients, orders, or production were added.

- PR18 backend recipe version calculation service: added a read-only calculation service and API endpoint for recipe versions. Fixed `g`/`ml`/`pcs` recipe lines are returned unchanged, percent lines calculate from an explicit or stored `g`/`ml` target batch size, percent totals are reported with warning/error issues, and calculation reads do not create audit logs or mutate recipe rows. No migrations, new tables, cost calculation, stock readiness, production, client recipes, orders, import/export, or frontend UI were added.

## PR19 — Recipe UI foundation
- Added `Рецепты` navigation and `/recipes` route in the branded frontend shell.
- Added frontend recipe API usage for listing/creating recipe templates, opening templates, listing/creating versions, opening version details, and requesting backend calculation results.
- Added recipe workspace UI with empty/loading/error states, template creation, version creation with ingredient lines populated from active ingredients, version detail, and Russian calculation panels for backend lines/issues/totals.
- Preserved historical-version safety: existing recipe versions are not edited, deleted, or mutated from the UI.
- No backend migrations, tables, client recipes, orders, production, cost calculation, stock readiness, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR20 — Ingredient lots UI foundation
- Added `Партии` navigation and `/ingredient-lots` route in the frontend shell.
- Added frontend API usage for `GET/POST/PUT /api/ingredient-lots` and `POST /api/ingredient-lots/{lot_id}/deactivate`, plus existing `GET /api/ingredients` for active component selection.
- Added ingredient lot loading, empty, error, create, edit, and soft-deactivate UI states with Russian user-facing labels and expiration status labels.
- Preserved stock boundary: no quantity/current balance input, no stock movement form, no frontend balance calculation, no migrations, and no backend changes.

## PR21 — Ingredient stock movement UI foundation
- Added `Движения склада` navigation and `/stock-movements` route in the frontend shell.
- Added frontend API usage for existing ingredient stock movement endpoints: `POST /api/stock-movements`, `GET /api/ingredient-lots/{lot_id}/movements`, and `GET /api/ingredient-lots/{lot_id}/balance`, plus existing ingredient/lot lists for human-readable lot selection.
- Added lot selection, backend-derived read-only current balance, create movement form, movement history table, and loading/empty/error states.
- Preserved append-only stock accounting: no edit/delete movement UI, no manual current balance field, no frontend balance derivation, no backend changes, no migrations, and no new tables.
- PR21 intentionally excludes packaging stock movement UI, production, purchase list, alerts, recipe/client/order changes, import/export, cloud, mobile, OCR, auth, and roles.

## PR22 — Clients backend foundation
- Added `clients` migration with contact, address, birthday, note, active-status, and timestamp fields.
- Added client validation for required normalized full name, normalized optional strings, email shape, optional non-future birthday, and soft deactivation.
- Added backend client create/read/list/full-update/deactivate service and `/api/clients` endpoints with transactional `client.created`, `client.updated`, and `client.deactivated` audit logging.
- Updated test-only table guards so `clients` is current while future client recipe, wishes/feedback, order, production, import, and backup tables remain forbidden.
- Added backend tests for table scope, client behavior, validation, transactional rollback on audit failure, and API endpoint coverage when the local TestClient dependency set is available.
- No frontend application code or client UI was added.

## PR23 — Client recipes backend foundation
- Added `client_recipes` and `client_recipe_ingredients` as backend persistence for first-class individual client formulas.
- Client recipes link to an active client and an existing source recipe version; source recipe ingredient lines are snapshotted into independent client recipe ingredient rows at creation time.
- Client recipe details read snapshot rows from `client_recipe_ingredients`, not live source `recipe_ingredients`, preserving historical individual formulas when base recipes change later.
- Added backend create/read/list/list-by-client/deactivate behavior with transactional `client_recipe.created` and `client_recipe.deactivated` audit events.
- No client recipe UI, orders, production, stock reservation/write-off, imports/exports, cloud, mobile, OCR, auth, or roles were added.

## PR24 — Catalog categories and tags backend foundation
- Added backend-only user-managed catalog categories and tags scoped to ingredients/components, packaging/tare, and recipe templates.
- Existing system classifications remain intact: `IngredientCategory`, `PackagingKind`, and `recipe_templates.product_type` are not removed, replaced, or reinterpreted.
- Catalog categories/tags are additional organization metadata with nullable category assignment and separate scoped tag bindings.
- Writes are service-layer transactional with audit actions for create/update/archive and assignment updates.
- Full frontend catalog UI remains a follow-up; no technical admin panel was added.
- No production, orders, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR24 follow-up — Catalog scope immutability and controlled errors
- Catalog category and tag scopes are now immutable after creation; updates may change names/slugs/sort/color/parent metadata only within the original scope.
- Catalog assignment routes now convert missing catalog records and missing assignment targets into controlled HTTP 404 responses instead of uncaught errors.
- Added regression tests for immutable scopes, assigned record scope-change prevention, and controlled missing-record assignment errors.

## PR25 — Ingredient catalog category selector and tag chips UI
- Added UI support on «Компоненты» for loading ingredient-scoped catalog categories and tags, showing «Системный тип», «Моя группа», and «Метки» in the component list, and assigning a selected component's category/tags through the existing ingredient assignment endpoints.
- Added minimal ingredient response enrichment for `catalog_category_id` and ingredient tag ids so the frontend can show current assignment state without adding migrations or new tables.
- Catalog categories/tags remain user organization metadata; `IngredientCategory` remains the system classification. Packaging/recipe catalog UI, catalog admin screens, deletion, migrations, production, orders, import/export, cloud, mobile, OCR, auth, and roles were not added.

## PR26 — Ingredient catalog inline create UI
- Added simple Russian inline controls on the `Компоненты` screen to create ingredient catalog groups and tags via the existing PR24 catalog endpoints.
- New categories/tags are created automatically as ingredient-scoped organization metadata and reload into the UI after creation.
- The system `IngredientCategory` semantics remain intact; grouping metadata is not used as business logic for stock, recipes, or production.
- Packaging and recipe catalog UI remain follow-ups.
- No migrations, new tables, production, orders, import/export, cloud, mobile, OCR, auth, or roles were added.

## 2026-06-23 — PR1 UX stabilization: recipe builder ingredient selection
- Fixed stale active component options in the recipe version constructor: active components created in «Компоненты» are refreshed for recipe lines without restarting the app.
- The recipe constructor now explains the empty active-component state and offers an explicit component-list refresh; unsaved version form input is preserved while component options refresh.
- Builder-first recipe creation remains a later UX stabilization PR. Catalog/menu/groups/tags redesign remains out of scope.

## 2026-06-23 — PR2 UX stabilization: grouped sidebar navigation
- Regrouped the left sidebar into user-facing sections: «Главная», «Создание», «Склад», «Производство», «Данные», and «Настройки и помощь».
- Existing implemented routes and screens remain intact, including `/inventory`, `/ingredients`, `/ingredient-lots`, `/stock-movements`, `/recipes`, `/clients`, `/client-recipes`, and `/packaging-items`.
- No backend, domain logic, API, migration, or data model changes were made.
- Recipe catalog, groups/tags UX, builder-first recipe creation, and inventory flow cleanup remain later UX stabilization PRs.

## 2026-06-23 — PR2 update: honest navigation status UX
- Refined PR2 sidebar groups to «Главная», «Рецепты», «Клиенты», «Склад», «Производство», and «Данные и настройки»; removed broad «Создание» grouping.
- Added frontend-only collapsible navigation groups; the active group stays expanded so the current screen remains visible during route and Back/Forward navigation.
- Added explicit module statuses in navigation: ready/empty/planned, with planned modules marked by a visible «скоро» badge and distinct planned-module placeholder pages.
- Added a compact home-page readiness note listing what works now and what is coming soon.
- No backend, domain logic, API, migration, or data model changes were made.

## 2026-06-24 — Frontend stabilization PR3 / GitHub PR #46: shared searchable catalog controls
- Introduced shared frontend helpers for searchable catalog group and tag controls with inline creation support, selected-tag chips, and limited default tag lists to avoid an unlimited chip wall.
- First applied scope: «Компоненты» catalog assignment; the same shared pattern was also safely applied to «Тара» because existing packaging catalog endpoints and UI were already present.
- No backend, domain model, API contract, migration, recipe catalog redesign, or builder-first recipe creation changes were made.
- PR #46 fix before merge: tag assignment now derives the payload from the item's current assigned tag ids plus the explicit toggled tag, so selected tags hidden by search are preserved; catalog search re-renders restore focus/caret for ingredient and packaging controls.

## Frontend stabilization PR4 / GitHub PR #47: component catalog browser and filters
- Components page now has browse-first catalog-level search and filters near the top of `/ingredients`.
- Filtering works over the loaded local frontend state for the local-first MVP; no backend search, pagination, domain, or migration changes were introduced.
- Lightweight generic catalog filter helpers were introduced for future reuse by Packaging, Recipes, Clients, and Client Recipes.
- Group/tag assignment from PR46 remains unchanged and still appears when editing a selected component.
- Packaging, recipes, clients, and client recipes catalog/list UX remain later PRs.
- PR #47 pre-merge fix: `/ingredients` now renders filters first, then the create/edit form and PR46 group/tag assignment area, then compact filtered results so create/edit actions appear near the top even with large catalogs.
- PR #47 final cleanup: default browse mode now renders filters directly followed by compact results, create/edit appears near the top only when active, cancel edit returns to browse mode without opening a blank create form, and search/group/system/status filters have individual clear actions; no backend/domain/API/migration changes.
- PR #47 manual-smoke fix: all `Создать компонент` buttons now use the same create action, opening the form scrolls/focuses the name field, create mode has a separate `Вернуться к каталогу` collapse action, and component results are labeled as `Найденные компоненты`; no backend/domain/API/migration changes.
- PR #47 assignment-picker fix: the shared group assignment picker now uses one searchable list of clickable options with highlighted current selection and `Без группы`; the fake search-plus-select pattern was removed for Ingredients and Packaging assignment panels without backend/domain/API/migration changes.

## PR48 — Staged catalog assignment apply
- Frontend stabilization PR5 / GitHub PR #48: staged apply for catalog assignment.
- Components and Packaging group/tag assignment now uses an explicit local draft and `Применить изменения`; accidental group clicks or tag toggles no longer save immediately.
- Hidden selected tags remain preserved because tag changes update the full draft tag id set, not the visible checkbox DOM.
- Applied only to frontend Components and Packaging assignment UX; no backend/domain/API/migration changes.

## Frontend stabilization PR6 / GitHub PR #49: packaging catalog browser and filters
- Packaging page now has catalog-level search and filters for group, tags, packaging type, and status.
- Packaging filtering works over the loaded local frontend state for the MVP; no backend search, pagination, API, domain, or migration changes were added.
- PR48 staged assignment remains unchanged: group/tag edits stay as a draft until `Применить изменения`, with reset/discard behavior preserved.
- Recipes, clients, and client recipes catalog/list UX remain later PRs.

## Frontend stabilization PR7 / PR50 replacement: recipes browse-first workspace
- Recipes now follow the browse-first workspace pattern used by Components and Packaging: the catalog search/filter area and compact list appear before create/edit/detail workspaces.
- Search/filtering works over loaded frontend recipe state for MVP: name, product type, description, notes, catalog group/tag text, and truthful active/inactive status already returned by the API.
- Create/edit/detail workspaces no longer dominate the first screen; create and opened recipe detail are explicit modes with clear return/close actions.
- No backend/API/domain/migration changes were made.
- Clients and Client Recipes remain separate later PRs.

## Frontend stabilization PR8: clients browse-first workspace

- Clients now follow the browse-first workspace pattern: intro, messages, search/status toolbar, optional create/edit workspace, compact list, and a collapsed create helper.
- Client search/filtering works over the loaded frontend client state and keeps the list visible instead of showing a long always-open form first.
- Status filtering uses the existing `includeInactive` API behavior: `Архив` and `Все` switch to inactive-inclusive loading before local filtering.
- Create/edit workspaces are explicit and closable; edit highlights the active row with the existing selected-row style.
- No backend/API/domain/migration changes were made. Client Recipes remain a separate later PR.

## Frontend stabilization PR9: client recipes browse-first workspace

- Client Recipes now follow the browse-first workspace pattern: intro, messages, search/filter toolbar, optional create/detail workspace, compact list, and collapsed create helper.
- Search and filtering work over loaded frontend client recipe state, including title, status, client name, personalization, allergy, preference, contraindication, and note text.
- Status filtering correctly loads inactive client recipes when `Архив` or `Все` is selected through existing `includeInactive` behavior, then filters locally over the loaded set.
- Base recipe/template filtering was intentionally not added because complete source recipe/template data is not loaded for every client recipe in this workspace.
- Create/detail workspaces no longer dominate the first screen; both are explicitly opened and closable without resetting filters.
- No backend/API/domain/migration changes.

## Frontend stabilization PR53 follow-up: client recipe create UX clarity

- Client Recipe create UX was clarified with non-technical Russian copy for client-specific formulas and saved composition versions.
- Create dependencies now refresh automatically through existing frontend API calls when opening the create form from browse/detail mode, without resetting filters or reloading the client recipe list.
- User-facing Client Recipe copy no longer exposes frontend/backend terminology.
- Version selection now explains that a saved recipe version with composition is required before an individual recipe can be created.
- A full editable ClientRecipe composition builder remains a later PR if backend support is not present.

## PR54: ClientRecipe composition update API

- ClientRecipe already created an independent copied composition from saved RecipeVersion lines.
- Added backend/API support to replace the copied ClientRecipe composition through `PUT /api/client-recipes/{client_recipe_id}/ingredients`.
- Composition updates affect only `client_recipe_ingredients` for the target ClientRecipe; source RecipeVersion / RecipeVersionIngredient rows are not mutated.
- Other ClientRecipes copied from the same source version are not mutated.
- Update validation covers line ids, positive ingredient ids, unique positions, positive precise amounts, allowed units, inactive ingredient replacement, and archived ClientRecipe edits.
- The replace operation is transactional and audited with `client_recipe.composition_updated`.
- No frontend composition editor was implemented; that remains a later PR.

## PR54 follow-up: inactive ClientRecipe line safety

- Tightened ClientRecipe composition updates so inactive existing ingredient lines may only remain if their copied line data is unchanged.
- Inactive existing lines may still be omitted from a full-replace payload to remove them.
- Added duplicate existing line id validation for composition update payloads.
- Source RecipeVersion rows, other ClientRecipes, and frontend UI remain unchanged.

## PR55: ClientRecipe composition editor

- Frontend detail card now has an editor for copied ClientRecipe composition.
- Saving uses the PR54 backend API: `PUT /api/client-recipes/{client_recipe_id}/ingredients`.
- The base recipe and saved RecipeVersion are not changed by composition edits.
- Archived/inactive ClientRecipes remain read-only.
- Inactive/unavailable ingredient lines are protected in the editor: leave unchanged or remove.
- This PR does not add production, stock deduction, cost calculation, or backend changes.

## PR56: Restore archived ClientRecipe
- Archived ClientRecipes can now be restored to the active working list through a backend-controlled restore workflow.
- Restore sets the ClientRecipe back to `draft` with `is_active = true` and keeps copied composition rows unchanged.
- Restore is rejected when the linked client is archived/inactive; source RecipeVersion rows and other ClientRecipes are not mutated.
- Restore writes a transactional `client_recipe.restored` audit event and rolls back if audit logging fails.
- This PR does not add global restore behavior for other entities.

## PR57: Client wishes and feedback backend
- Added backend foundations for client wishes and client feedback.
- Wishes can be created, listed, retrieved, status-updated, resolved, and archived.
- Feedback is append-only in this PR: create/list/get only, with no update or delete endpoint.
- Both wishes and feedback can optionally link to a ClientRecipe belonging to the same client, including archived ClientRecipes for historical context.
- Creating wishes or feedback for inactive clients is rejected.
- Source RecipeVersion, ClientRecipe composition, stock, production, and orders are not mutated.
- Frontend UI will be added in a later PR.

## PR57 follow-up: ClientWish status lifecycle
- Fixed ClientWish status transitions so moving from `resolved` back to `open` or `planned` clears `resolved_at`.
- Generic status updates no longer archive wishes or restore archived wishes; archive remains explicit through `POST /client-wishes/{wish_id}/archive`.
- Feedback remains append-only and no ClientRecipe, RecipeVersion, inventory, production, or frontend behavior was changed.

## PR58: Client wishes and feedback UI
- Added frontend-only client-card sections for `Пожелания клиента` and `Обратная связь` using the existing PR57 backend endpoints.
- Wishes can be created, moved only between `open`, `planned`, and `resolved`, and archived through the explicit archive endpoint; archived wishes are hidden by default, visible through `Показать архивные`, read-only, and not restorable in this PR.
- Feedback can be created and viewed as append-only history; no edit/delete UI was added.
- ClientRecipe linking is implemented in both create forms by loading existing client recipes, including archived recipes when available, and sending only the selected `client_recipe_id` without mutating ClientRecipe composition.
- Backend/domain/migrations were not changed. Orders, production, stock, import/export, backup/restore, cloud, auth, and AI recommendations were not added.

## PR58 follow-up: Preserve client card drafts
- Open ClientWish and ClientFeedback form drafts are now synced from the DOM before background client-card refresh renders, preserving typed text, ClientRecipe selector values, dates, ratings, and follow-up checkbox state.
- Wish title frontend maxlength is aligned with backend validation at 180 characters.
- Backend/domain/migrations were not changed. Feedback edit/delete and wish restore were not added.

## PR58 follow-up: Preserve drafts on client card save
- Client card save now syncs open ClientWish/ClientFeedback drafts before edit-card render paths, so saving the main client details does not lose unsaved wish or feedback form input.
- Backend/domain/migrations were not changed. Feedback edit/delete and wish restore were not added.

## PR60 — Orders backend foundation
- Added the backend Orders foundation: SQLite `orders` table, domain validation, typed repository/model, transactional audited service, schemas, and `/api/orders` routes.
- Orders now connect an active client to exactly one recipe source: either a `RecipeVersion` or a same-client active `ClientRecipe`; optional packaging is validated for active state on new writes.
- Order create/update/cancel/archive writes are audited with rollback on audit failure and do not mutate recipes, client recipes, stock movements, packaging movements, or production data.
- No frontend UI, production readiness, production confirmation, automatic stock write-off, alerts, purchase suggestions, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR61 — Orders UI foundation
- Added `Заказы` navigation and `/orders` route in the frontend shell.
- Added a human-friendly Orders workspace with list, search/status filters, empty/loading/error states, create order form, detail view, safe edit flow, cancel action, and archive action.
- Integrated with existing PR60 Orders endpoints: `POST /api/orders`, `GET /api/orders`, `PUT /api/orders/{order_id}`, `POST /api/orders/{order_id}/cancel`, and `POST /api/orders/{order_id}/archive`.
- Create/update payloads are built from safe order fields only and do not send `status`, `produced_at`, or `delivered_at`.
- The UI displays future production statuses read-only but intentionally adds no production readiness, production confirmation, stock write-off, production batches, cost/tax/margin calculation, alerts, purchase suggestions, import/export, cloud, mobile, OCR, auth, or roles.

## PR62 — Production readiness backend foundation
- Added backend-only Production Readiness foundation for orders.
- Added `POST /api/orders/{order_id}/check-production-readiness` returning structured readiness results with blocking issues, warnings, ingredient requirements, FEFO lot selections, packaging availability, and optional cost/tax/margin estimates.
- Readiness checks current ingredient lot and packaging balances through existing inventory read logic and preserves the production boundary: no stock write-off, no packaging write-off, no production batches, and no order lifecycle mutation.
- Added targeted backend tests for enough stock, missing/insufficient ingredients, FEFO selection, expired/soon-expiring lots, missing density, missing packaging, cancelled/archived rejection, API behavior, and read-only guarantees.
- No frontend UI, production confirmation, alerts, purchase suggestions, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR63 — Production readiness UI
- Added read-only Production Readiness UI inside the Orders workspace.
- Added active-order `Проверить изготовление` action that calls existing `POST /api/orders/{order_id}/check-production-readiness` endpoint.
- Displayed readiness summary, blocking issues, warnings, ingredient requirements, backend-selected FEFO lots, packaging availability, and optional estimates.
- Null tax/margin/cost values are shown as `Не рассчитано`; the frontend does not invent tax settings or calculate margin itself.
- Preserved production boundary: no production confirmation, no stock write-off, no packaging write-off, no lot reservation, no production batches, and no order lifecycle mutation.

## PR64 — Production confirmation backend foundation
- Added transactional backend production confirmation through `POST /api/orders/{order_id}/produce`.
- Added `production_batches`, `production_batch_ingredients`, and `production_batch_packaging` tables for historical production snapshots.
- Production confirmation now requires `confirm=true`, reuses backend Production Readiness, rejects lifecycle/readiness conflicts, writes off ingredient lots and packaging through movement records, marks the order `produced`, sets `produced_at`, and writes a safe audit log in the same transaction.
- Tax, margin, and margin percent remain null; no hidden tax rate or frontend production UI was added.

## PR65 — Production confirmation UI
- Added frontend Production Confirmation UI inside the Orders workspace, using the existing backend readiness result as the gate before showing `Изготовить`.
- Added frontend production batch response types and a `produceOrder` helper that only sends `confirm=true` to `POST /api/orders/{order_id}/produce`.
- Added an inline second-confirmation panel with optional notes before any production request is sent.
- Successful production now displays a human-readable production result panel with batch id, produced date, costs when present, tax/margin as `Не рассчитано`, write-off row counts, and the stock movement safety note.
- After successful production, the frontend refreshes order data from the backend and no longer exposes production actions for produced/cancelled/archived/inactive/delivered orders.
- No frontend readiness, stock write-off, lot selection, production batch, tax, or margin calculations were added; no backend logic or migrations were changed.

## PR66 — Production history read UI and production batch detail page
- Added read-only production batch API endpoints for listing batches, opening one batch detail, and finding a batch by order.
- Production batch repository now supports read-only list/detail access with order, product, and client display context without duplicating production confirmation write logic.
- Added backend tests covering list sorting, detail snapshots, by-order lookup, not-found behavior, and read-only guarantees.
- Added a real frontend `Производство` page with production history search, batch list, and read-only detail panel for cost, ingredient lot, and packaging snapshots.
- Produced/delivered orders can open their production batch without showing production confirmation actions again.
- No migrations, production write actions, reversal/edit/delete flows, frontend stock/cost/tax calculations, alerts, purchases, import/export, cloud, OCR, auth, or analytics were added.

## PR67 — Alert engine backend foundation
- Added the backend `alerts` table with `alert_key` deduplication, alert status/severity/type fields, and safe status timestamps.
- Added backend alert generation for low ingredient stock, low packaging stock, expiring/expired ingredient lots, and order-level ingredient/packaging production readiness blockers.
- Added read-only/list, explicit regenerate, resolve, and dismiss Alert API endpoints.
- Added backend tests for idempotency, deduplication, status transitions, MVP alert types, and read-only guarantees.
- No frontend UI, purchase suggestions, notifications, scheduler, or automatic stock/order/production changes were added.

## PR68 — Alerts UI
- Added a frontend `Алерты` workspace at `/alerts` that consumes the PR67 backend alert endpoints.
- Added status/type/search filters, explicit regeneration, resolve, and dismiss actions with Russian human-readable cards and empty/error states.
- Updated dashboard copy to list Alerts as available.
- No backend behavior, migrations, alert rules, purchase suggestions, notifications, scheduler, polling, or dashboard analytics were added.
- Next recommended PR: purchase suggestions backend foundation.

## PR69 — Purchase suggestions backend foundation
- Added `purchase_suggestions` persistence with generated-key uniqueness and table guard coverage.
- Added backend domain/model/schema/repository/service/API layers for purchase suggestions.
- Added deterministic explicit generation for low ingredient stock, low packaging stock, insufficient order ingredients, and insufficient order packaging.
- Added manual suggestion creation, limited open-suggestion updates, mark purchased, and dismiss endpoints.
- Preserved read-only safety: generation and mark-purchased do not mutate stock movements, packaging movements, ingredient lots, orders, production batches, alerts, clients, recipes, ingredients, or packaging items.
- Updated `docs/api.md`, `state/current-focus.md`, and `state/handoff.md` for PR69.

## PR70 — Purchase Suggestions UI
- Added a frontend `/purchase-suggestions` workspace for purchase suggestions that consumes the PR69 backend endpoints.
- The «Закупки» navigation item now opens the real workspace instead of the old `/#purchases` placeholder.
- Added Russian, card-based purchase suggestion UI with status/reason/item-type/search filters, explicit regeneration, generation summary, manual suggestion creation, safe edit of quantity/unit/notes, mark purchased, and dismiss actions.
- Added visible safety copy that «Куплено» closes the recommendation but does not create IngredientLot records, packaging inbound movements, stock movements, order changes, or production changes.
- Updated dashboard copy to list «Закупки» as working now; no dashboard widgets were added.
- No backend behavior, migrations, supplier integration, online ordering, real procurement, stock mutation, order mutation, production mutation, scheduler, polling, notifications, import/export, or backup UI were added.

## PR71 — Dashboard operational overview frontend
- Replaced the dashboard placeholder with a frontend operational overview on `/`.
- Dashboard uses existing APIs and frontend aggregation for orders, clients, open alerts, open purchase suggestions, and recent production batches.
- Added onboarding, priority cards, “Что сделать сегодня” guidance, active orders, alerts, purchase suggestions, recent production, quick actions, and backup reminder blocks.
- Dashboard reload only repeats existing GET data; it does not regenerate alerts or purchase suggestions and does not run production readiness checks.
- Follow-up hardened dashboard loading so initial load does not show fake empty metrics, manual reload keeps stale data visible, and failed refresh shows a soft stale-data message.
- No backend endpoint, migration, analytics, scheduler, polling, notifications, backup/export, import/export, stock/order/production mutations, or procurement automation were added.
- Next recommended PR: Backup/export UI foundation or Backup/export backend/frontend foundation depending on existing backup/export state.

## PR72 — Orders reference refresh and localized quantity display hotfix
- Added frontend-only Orders reference refresh for create/edit forms so clients, recipe templates, recipe versions, client recipes, and packaging are reloaded before the form shows usable selectors.
- Added explicit Orders form reference loading, retryable error, and post-load empty-state behavior to avoid disabled empty dropdowns caused by stale cached `ordersState` data.
- Added Russian-friendly display formatting for user-facing quantities in Orders, production readiness, production snapshots/history, purchase snippets, and dashboard snippets so raw backend decimals like `100.000 г` render as `100 г`.
- Kept backend Decimal/API payload contracts unchanged by continuing to submit dot-normalized decimal strings and adding no backend endpoints, migrations, or business-logic changes.
- No stock/order/production side effects were added beyond existing explicit order create/edit/cancel/archive actions.

## PR74 Backup UI
- Added a frontend `Резервные копии` workspace at `/backups` that consumes PR73 backup status/list/manual-create endpoints only.
- Added navigation and dashboard reminder link to the backup workspace.
- Added status cards for database path/existence/size, backup directory path/existence, backup count, and latest backup.
- Added explicit manual backup creation with reason presets/custom reason and a refreshed backup history list after success.
- Missing backup directory is shown as a normal empty/local-first state; missing database disables backup creation with a clear next step.
- Restore, download, delete, scheduled backups, cloud backup, export, import, arbitrary paths, polling, notifications, backend changes, migrations, and business mutations were not added.

## PR75 — Export API foundation

- Added backend Export API foundation for explicit local JSON snapshots: `GET /api/exports/status`, `GET /api/exports`, and `POST /api/exports`.
- Added safe export path resolution mirroring backup behavior: user-mode exports use the resolved user `exports/` directory; development/test exports stay next to the configured database.
- Added JSON export creation with `manifest`, whitelisted domain `data`, entity counts, preserved IDs/relationships, catalog/user-organization tables, non-overwriting filenames, and reason normalization/safe filename sanitization.
- Follow-up removed absolute local `database_path` from exported JSON manifests; exports now store `database_filename` and `database_location_kind` while API responses may still show local paths for the local UI.
- Added export listing/status response schemas and tests for read-only GET behavior, missing directories, JSON creation, uniqueness, missing/invalid database handling, reason validation, and malformed filenames.
- Updated API/export documentation.

## PR76 — Export UI
- Added frontend `/exports` workspace and “Экспорт” navigation under “Данные и настройки”.
- Export UI consumes only PR75 endpoints: `GET /api/exports/status`, `GET /api/exports`, and explicit-click `POST /api/exports`.
- Added status cards for database/export directory, manual JSON export creation with reason presets/custom reason, export history list, and entity-count summary from backend response.
- UI explicitly states that import, restore, download/delete, CSV/XLSX, PDF/report, scheduled export, cloud export, and automation are not implemented.
- No backend behavior, migrations, business mutations, dashboard analytics, import/restore/download/delete flows, or arbitrary path inputs were added.

## Next recommended PR

Import CSV/XLSX draft backend foundation.

## PR77 — Import CSV/XLSX draft backend foundation

- Added import source/draft/draft-row persistence for the safe draft-only import flow.
- Added backend parsing and validation for CSV/XLSX import drafts with raw and normalized row storage.
- Added import API endpoints for supported targets, draft creation, draft listing, draft detail, and cancellation.
- Added parser/API tests covering supported formats, validation issues, persistence, cancellation, and safety boundaries.
- Updated API/import docs and state handoff.
- No import apply/confirmation, frontend UI, OCR/PDF/image import, automatic backup/export, or domain-table mutations were added.

### PR77 follow-up fixes

- Fixed CSV/XLSX draft row numbering so preview rows and row-level validation issues keep real source row numbers.
- Fixed XLSX parsing to use cell references and preserve blank/missing cell positions.
- Removed `content_hash` from user-facing import source API responses while keeping it stored internally.
- Documented import columns as user-facing aliases that future confirmation/apply must explicitly map to domain fields.

## PR78 — Import draft UI / preview UI
- Added frontend Import workspace at `/imports` with “Импорт” navigation in “Данные и настройки”.
- The UI consumes only PR77 import draft endpoints: targets, create draft, list drafts, draft detail, and cancel draft.
- The workspace supports CSV/XLSX target selection, explicit multipart draft upload, draft list, detail preview, validation issue display, preview rows, and cancellation.
- The screen repeatedly explains that rows are only draft/preview data and are not applied to real workshop records.
- Import apply/confirmation, column mapping, OCR, PDF/image import, automatic backup/export, polling, and business-domain mutations remain out of scope.
- Next recommended PR: import validation refinement or import apply design/backend, depending on browser smoke feedback.

## PR79 — Import validation refinement and apply readiness contract
- Added explicit import draft apply readiness contract for create/list/detail/cancel responses without adding apply or confirmation.
- Refined import validation with visible header aliases, decimal comma normalization, unit/date normalization, email/ID checks, and target-specific numeric rules.
- Updated Import UI to show readiness while keeping the flow draft-only.
- Updated API/import/state docs for PR79.

## PR80 — Import apply backend foundation
- Added backend-only `POST /api/imports/drafts/{draft_id}/apply` for explicit import application.
- Apply requires confirmation and backup acknowledgement, blocks cancelled/failed/already-applied/blocked drafts, and requires `allow_warnings=true` for ready-with-warnings drafts.
- Implemented transactional all-or-nothing creation for `ingredients`, `clients`, `recipe_templates`, and catalog-only `packaging_items`.
- Kept `ingredient_lots` and `orders` unsupported for apply in PR80.
- Added duplicate/existing-record conflict checks and packaging `stock` apply blocking.
- Successful apply updates draft/source to `applied`, stores `apply_result` in `summary_json`, and writes an audit log entry.
- Added migration support for the new `applied` import status and backend apply tests.
- Next recommended PR: PR81 — Import confirmation/apply UI.

## PR80 follow-up — Applied import cancellation safety
- Blocked cancelling already-applied import drafts; cancel now returns a structured conflict and leaves draft/source status as `applied`.
- Added regression tests for applied-cancel blocking and migration 0017 data preservation/applied status acceptance.
- Updated Import UI defensive labels/readiness pills for `applied` and hides cancel actions unless status is `draft`.
- Updated API/import docs to include `applied` readiness and the no-cancel safety rule for applied drafts.

## PR81 — Import confirmation/apply UI
- Added frontend confirmation/apply UI in the import draft detail panel for PR80-supported targets: ingredients, clients, recipe templates, and packaging items.
- The UI consumes `POST /api/imports/drafts/{draft_id}/apply` only after explicit apply confirmation, backup acknowledgement, and warning acknowledgement for `ready_with_warnings` drafts.
- Blocked, cancelled, failed, already-applied, and unsupported drafts (including ingredient lots and orders) cannot be applied from the UI.
- Successful apply refreshes the draft list/detail and displays created records; backup/export buttons only navigate and do not create files.
- No backend targets, mappings, cell editing, partial import, OCR/PDF/image import, stock/order/lot/production import, automatic backup/export, migrations, or domain direct frontend mutations were added.

## PR81 follow-up — Import apply stale-state and structured errors
- Reset import apply state before upload and after new draft creation so stale success/errors/results from a previous draft cannot appear on the newly selected draft.
- Preserved structured backend `detail.issues` on frontend API errors and surfaced issue messages in import apply conflict/error copy.
- Improved import draft cancel rejection copy to show backend-provided messages while keeping apply gating and supported targets unchanged.

## PR82 — Import apply hardening / smoke fixes
- Hardened import apply after PR80/PR81 without expanding supported targets: `ingredients`, `clients`, `recipe_templates`, and `packaging_items` remain the only apply-supported targets.
- Improved frontend apply failure display so structured backend conflict issues show row, field, code, and user-readable message, plus reassurance that working data was not partially changed.
- Added a double-submit guard while apply is in progress and preserved applied-draft result display after refresh through stored `summary.apply_result`.
- Expanded backend regression coverage for already-applied draft rejection, unsupported orders/lots, duplicate conflicts, warning acknowledgement, unapplied draft/source after failure, no side-effect backup/export/alert/purchase records, and applied detail/list readiness.
- Updated import API/format docs and state handoff. No migrations, new apply targets, automatic backup/export, stock movements, lots, orders, production records, alerts, or purchase suggestions were added.

## PR83 — Refresh existing onboarding checklist after import/apply
- Refreshed the existing single onboarding/checklist flow to match the current MVP workflow after import/apply.
- Added current onboarding steps for component lots, packaging, individual recipes, production readiness/confirmation, alerts/purchases, backup/export, and import drafts.
- Preserved the existing `/api/onboarding` API and `app_settings` state store; no second checklist, table, or API was added.
- Added compatibility handling for old onboarding state, including mapping `first_backup` to `backup_and_export`, ignoring unknown completed steps, and falling back unknown current steps to the first incomplete refreshed step.
- Updated frontend Russian onboarding copy, progress count, safety copy, and navigation hints/buttons.
- Fixed stale import readiness copy that said apply would be added in a separate future PR.
- Import apply targets were not expanded; ingredient lots and orders remain unsupported.

## PR84 — Demo data mode backend foundation
- Added backend-only demo data tracking migration with `demo_data_sessions` and `demo_data_records`.
- Added explicit demo status/install/clear API under `/api/demo-data`.
- Demo install is transactional and blocked for workspaces with non-demo business data.
- Demo clear deletes only tracked rows and blocks when real records reference demo records.
- Demo records are labeled with `Демо ·` and tracked by table name plus record id.
- No frontend UI, startup seeding, migration seeding, backup/export automation, production batches, or import apply target expansion were added.
- Next recommended PR: PR85 — Demo data mode UI.


## PR84 follow-up — Demo data clear safety hardening
- Expanded demo-data clear guards for client wishes, feedback, production batches, production batch rows, alerts, and purchase suggestions.
- Demo status now reports `can_clear=false` with a blocking reason when untracked working records reference tracked demo rows.
- Added regression tests for unsafe alert, purchase suggestion, client wish/feedback, production batch dependencies, and unsafe status behavior.
- No frontend UI, migrations, automatic install/clear, backup/export creation, production confirmation, import target expansion, or user-data deletion behavior was added.


## PR85 — Demo data mode UI
- Added `/demo-data` frontend route and “Демо-данные” navigation item under “Данные и настройки”.
- Added frontend API helpers for PR84 demo-data status/install/clear endpoints.
- Added human-readable demo status cards, backend blocking reason display, demo dataset explanation, explicit install confirmation with two checkboxes, explicit clear confirmation with one checkbox, created/deleted counts, safety boundaries, and post-install navigation links.
- Added compact dashboard card linking to demo data mode; dashboard does not duplicate the full demo UI.
- Demo data is not installed or cleared on page load; frontend does not create/delete business records directly and does not create backup/export automatically.
- No backend demo dataset changes, migrations, import apply target expansion, help center, reports, cloud, OCR/PDF/image behavior, or packaging work was added.

## PR85 follow-up — Demo data UI polish
- Clarified `docs/demo-data.md` so PR84 is described as the backend/API foundation and PR85 as the frontend UI route.
- Failed demo install/clear attempts now refresh demo-data status afterward, preserving the action error while replacing stale `can_install`, `can_clear`, and `blocking_reasons` with backend truth when available.
- No backend endpoints, migrations, demo dataset changes, automatic install/clear, backup/export creation, production behavior, import behavior, or direct frontend business-data mutation were added.

## PR86 — In-app help center foundation
- Added a static frontend Help Center at `/help` and marked “Помощь” ready in the “Данные и настройки” navigation group.
- Help content is bundled in `frontend/src/main.ts`, works offline, and does not call backend APIs or mutate business data.
- Added Russian user-facing articles for first steps, inventory/components/lots/movements/packaging, recipes/client recipes, clients, orders/readiness/production, alerts/purchases, backup/export, import, and demo data.
- Added frontend-only search, category filter, selected article detail view, and related-section navigation buttons that only navigate.
- Added a compact dashboard card linking to Help; no backup/export/import/demo actions are triggered from Help.
- No backend help API, database tables, migrations, CMS, AI/RAG, external docs, reports/settings/audit/package work, or import apply target changes were added.


## PR87 — Reports backend foundation
- Added read-only backend reports service, schemas, and `/api/reports` endpoints for overview, inventory, orders, production, and finance.
- Reports aggregate existing SQLite data only and do not create audit logs, backups, exports, alerts, purchase suggestions, or report tables.
- Finance values use Decimal-backed string totals and do not invent tax. Missing sale price/cost and mixed production units are surfaced as warnings.
- Added backend report service/API tests and docs.
- Next recommended PR: PR88 — Reports UI foundation, unless report API smoke finds backend follow-up fixes.


## PR87 follow-up — finance margin basis safety
- Fixed finance report margin basis: `known_margin` and `known_margin_percent` now use only production batches where both `sale_price` and `total_cost` are known on the same row.
- `known_revenue` and `known_production_cost` remain independent known totals, but reports no longer combine revenue from one incomplete batch with cost from another unrelated incomplete batch to produce margin.
- Added `complete_finance_record_count`, `incomplete_margin_count`, `margin_unavailable`, and `partial_margin_basis` coverage/docs.
- Manual long-running API smoke was not run in this non-interactive session; automated service/API tests cover the finance mismatch regression and read-only endpoints.

## PR88 — Reports UI foundation
- Added `/reports` frontend route and marked “Отчеты” ready in “Данные и настройки”.
- Added typed frontend report DTOs and API helpers for PR87 read-only endpoints: overview, inventory, orders, production, and finance.
- Added Reports page hero, reload button, tabs, metric cards, backend warning panels, friendly empty state, related navigation buttons, and finance safety copy.
- Added compact dashboard card linking to Reports.
- Reports UI displays backend-provided values only and does not calculate core report values, mutate business data, create backup/export files, regenerate alerts/purchase suggestions, or add PDF/export/charts/accounting.


## PR88 follow-up — Reports dashboard card wiring
- Wired the compact Reports dashboard card into the dashboard between demo data and help so users can open `/reports` from the main screen.
- Updated the defensive planned-section fallback for “Отчеты” so it no longer says reports are a future module.
- Reports remain read-only and backend-owned; no mutations, backup/export creation, alert/purchase regeneration, production actions, import apply actions, or frontend finance recalculation were added.

## PR89 — Report document export foundation
- Added backend report document schemas, service, and `/api/report-documents` endpoints for status, metadata listing, and explicit overview document creation.
- Added Markdown “Сводка мастерской” generation from backend `ReportsService.get_overview()` data with required Russian sections, warnings, finance limitation copy, and explicit non-accounting/non-tax notes.
- Generated files are stored under the safe report-documents directory with non-overwriting timestamped filenames and JSON metadata sidecars.
- PDF and DOCX are rejected with a clear Russian unsupported-format message; Markdown is the only PR89 format.
- Document generation writes only the Markdown document and metadata sidecar, does not mutate business data, does not create backup/export snapshots, and does not regenerate alerts or purchase suggestions.
- Added `docs/report-documents.md`, API docs, Reports docs cross-reference, state updates, and backend service/API tests.
- Next recommended PR: PR90 — Report document export UI, unless backend smoke finds follow-up fixes.

## PR89 follow-up — Report document pair-safety and docs polish
- Made report document file creation pair-safe: the service now chooses a unique `.md + .json` pair where both paths are free before writing.
- Added rollback behavior so metadata sidecar write failure best-effort removes the newly created Markdown file and does not leave orphan Markdown.
- Added service regression tests for stale metadata sidecars and metadata-write failure rollback.
- Corrected report document filename examples and documented numeric suffix behavior.
- Updated Reports docs so they no longer describe the `/reports` frontend UI as future-only.
- Manual long-running API smoke was not run in this non-interactive session; automated tests cover the follow-up safety scenarios.

## PR90 — Report document export UI + sidecar cleanup hardening
- Added a focused `/report-documents` frontend route labeled «Документы отчетов» under «Данные и настройки».
- The UI loads PR89 report document status/list endpoints and creates only explicit Markdown «Сводка мастерской» documents via `POST /api/report-documents/reports/overview`.
- Page load and list refresh remain read-only; PDF/DOCX are documented in the UI as future work and no unsupported format actions are shown.
- Added a Reports page contextual navigation link to the document export UI; it does not create documents from `/reports`.
- Hardened `ReportDocumentService` cleanup so the metadata sidecar is unlinked only if this operation actually created it, while preserving original safe errors.

## PR92 — Report PDF generation foundation
- Added explicit PDF generation for workshop overview report documents through the existing `/api/report-documents/reports/overview` pipeline.
- Markdown remains supported; DOCX remains unsupported with a clear Russian error.
- PDF generation uses backend `ReportsService` overview data and the same report document sections as Markdown, without frontend recalculation, tax invention, business-data mutation, backup/export/import/demo creation, or alert/purchase regeneration.
- Generated PDF files and metadata sidecars are stored only in the safe `exports/report-documents` area with non-overwriting filenames and cleanup on current-operation failures.
- Status reports `pdf` only when a local Cyrillic-capable font is available for readable Russian text.
- `/report-documents` can explicitly create Markdown or PDF when available, and `/reports` navigation copy was clarified to «Открыть документы отчетов».
- Next recommended PR: PR93 — Report PDF UI polish / download-open workflow, unless smoke finds follow-up fixes.

## PR92 follow-up — deterministic PDF availability
- Made PDF availability deterministic and independent of host test environment fonts.
- Updated PDF happy-path service/API tests to monkeypatch PDF availability and fake PDF output instead of relying on installed DejaVu, Liberation, or Noto fonts.
- PDF is advertised only when the backend finds a parseable local `.ttf` font with Cyrillic glyphs that the current renderer can use.
- TTC font collections are not supported in PR92.
- Markdown remains always available, and unavailable PDF creation is rejected with a safe Russian message.
- Corrected report-document docs so they no longer describe PDF as future-only after PR92 and use document-file + metadata-sidecar wording.

## PR93 — Report PDF UI polish / download-open workflow
- Added a read-only `/api/report-documents/{document_id}/download` endpoint for known generated Markdown/PDF report documents.
- The endpoint validates metadata, format/filename consistency, safe directory containment, file existence, and disposition before serving files.
- `/report-documents` now shows `Открыть PDF`, `Скачать PDF`, and `Скачать Markdown` actions through the backend endpoint.
- Document creation remains explicit; `/reports` remains navigation-only and DOCX remains unsupported.

## PR93 docs follow-up — frontend concept wording
- Removed stale `docs/frontend-concept.md` wording that described report document export as Markdown-only or PDF future-only.
- Documented the current PR92/PR93 workflow: Markdown always available, PDF shown only when backend support is advertised, DOCX unsupported, and generated files accessed only through the safe backend download endpoint.
- Reconfirmed that `/reports` only navigates to `/report-documents` and does not create files.

## PR94 — Settings UI foundation
- Added a ready `/settings` route and «Настройки» navigation item.
- Added a user-facing, read-only Settings foundation page for local data, backups, import/export, report documents, demo data, Help Center, About app, and future settings boundaries.
- Settings actions only navigate to existing safe workflows and do not run backup/export/import/demo/report document creation actions.
- No backend settings API, persistence, migrations, file creation, or business-data mutations were added.

## PR95 — Settings data/status foundation
- Added read-only `GET /api/settings/status` backend endpoint.
- Added Settings status DTOs/service with local-first app status, user-data separation status, safe workflow capabilities, and Settings Decision Matrix.
- Updated `/settings` to load backend status, render local data status, capability cards, future settings groups, app info, and MVP boundaries.
- Settings actions remain navigation-only; no editable controls, persistence, migrations, file creation, or business-data mutations were added.
- Added `docs/settings.md` and updated API/frontend docs.

## PR95 type-safety polish
- Replaced the raw `str` status parameter in `SettingsService._definition()` with the shared Settings definition status Literal type.
- Removed the `# type: ignore[arg-type]` from settings status construction.
- No runtime Settings behavior, response shape, persistence, migrations, or editability changed.

- PR96 added the first safe editable Settings area: backend-owned workshop profile fields for workshop name, master name, contact text, and note.
- Added `GET /api/settings/workshop-profile` and `PUT /api/settings/workshop-profile`, using the existing `app_settings` storage with grouped JSON key `workshop_profile` and no migration.
- Updated `/settings` with an explicit «Профиль мастерской» form, save/cancel states, validation display, and safety copy.
- Updated Settings status so only workshop profile fields are `editable_now`; calculation-sensitive settings remain non-editable.

## PR98 — Workshop profile integration with report documents
- Report document generation now reads the saved Workshop profile and includes configured fields in new Markdown/PDF workshop overview documents.
- Profile rendering is backend-owned, plain-text/Markdown-safe, and shared by Markdown/PDF content lines.
- Empty/default profiles continue to generate documents without an empty profile section.
- Existing generated documents and metadata are not rewritten.
- Settings and report-document UI copy now reflects that Workshop profile is editable and added to new summaries.
- Docs/state were cleaned up from stale PR94/PR95/PR96/PR97 wording.
- No report calculations, business records, tax/currency/margin/unit/stock-threshold/expiry settings, document templates, logo upload, DOCX, invoices, labels, or certificates were added.

## Settings UI repair

- Manual browser smoke found a blocking Settings UI defect: profile fields flowed horizontally and the page exposed technical planning content.
- The focused Settings repair removes future settings matrices, readiness classifications, repository metadata, and MVP-boundary planning copy from the runtime `/settings` screen.
- The Workshop profile section now renders from its own API state instead of being hidden by the general Settings status request.
- Next step after merge: rerun isolated browser smoke for Workshop profile saving/clearing and report-document generation integration.

## Shared action-state visual contract

- Source and runtime audits identified inconsistent shared action visual states across routes.
- Current branch contains only the shared visual action-state contract in the frontend styles and minimal state notes.
- No application behavior, API behavior, route logic, loading logic, or data behavior changed.
- Browser smoke remains required across representative routes before merge.
- Next planned system-level task: shared feedback presentation and semantics.

## PR105 focus contrast follow-up

- Changed shared action `:focus-visible` outline color from `rgba(211, 154, 122, .75)` to `#9a5f49`; sidebar focus styling remains unchanged.
- Browser smoke used an isolated temporary SQLite database and temporary user-data directory.
- Tested `/settings`, `/exports`, `/report-documents`, `/alerts`, `/purchase-suggestions`, `/demo-data`, sidebar keyboard navigation, and 1440×900 plus 390×844 viewports.
- Passed: shared action keyboard focus, hover/pressed states, disabled settings controls, `/exports` intercepted request-failure presentation, document action links, demo danger action after isolated demo install, no horizontal overflow, screenshots, and no page errors.
- Unavailable in isolated data: alert resolve/dismiss row actions, purchase-suggestion row actions, and a disabled danger action after the safe demo install state.
- Browser console finding: one expected 503 resource error from the intentional `/exports` request-failure interception; no unexpected console errors.
- Frontend build passed.

## Initial shared feedback presentation and semantics slice

- Added one shared frontend feedback helper for neutral/success/warning/error presentation.
- Added shared CSS for readable, non-color-only feedback blocks with structured detail support and narrow-screen wrapping.
- Added persistent hidden announcement regions outside the re-rendered app root: polite `role="status"` and assertive `role="alert"`.
- Migrated feedback and one-time announcement behavior for `/settings`, `/exports`, `/report-documents`, `/imports`, and `/demo-data` only.
- Preserved structured import apply errors with row number, field name where available, safe user-facing message, issue list, and no-partial-change statement.
- Added `aria-busy` coverage for the scoped forms/panels only.
- Source inventory found remaining legacy `.page-message`, `.error-message`, and `.inline-message` uses across dashboard, alerts, purchase suggestions, backup, reports, recipes, clients, production history, stock/catalog, onboarding, and help; these remain outside this migration slice.
- Checks: `git diff --check` passed; `cd frontend && npm run build` passed; `cd backend && python3 -m pytest` ran 468 tests with 463 passed and 5 existing backend-area failures unrelated to this frontend/state-only branch; isolated backend/frontend startup curl passed for `/api/health` and `/settings`.
- Earlier Codex-local Playwright smoke and screenshots were unavailable in that environment because Playwright was not installed and npm registry access failed; this limitation was later superseded by the completed external Hermes audit recorded below.

## PR106 follow-up — feedback semantics fixes

- Fixed Workshop profile stale result feedback after editing begins: state `message`/`error`, visible result markup, and persistent announcers are cleared while the dirty notice remains controlled without full render.
- Changed normal Workshop profile initial load to keep the action-result message empty; save/cancel remain user-action results.
- Pre-created persistent polite/assertive announcers during startup before the first action can update text.
- Split mutation success/failure from follow-up refresh failure for export creation, report document creation, import draft creation, demo-data install, and demo-data clear. A successful mutation with failed refresh now preserves the success result and asks the user to refresh instead of announcing a false action failure.
- Added import draft cancellation success/failure announcements to the scoped action-result contract.
- Backend baseline verification: base commit `2265802f07b3ee3df7a1c5478bc6ae11fed096b7` and PR branch both ran `cd backend && python3 -m pytest` with the identical 5 failing tests and 463 passing tests; no backend test failure exists only on this PR branch.
- Playwright/local browser discovery in Codex found no local browser automation tool, so Codex itself did not run browser smoke at that time; the later external Hermes audit completed the required browser verification recorded below.

## PR106 correction — Import Apply mutation vs refresh

- Corrected the earlier broad Import-flow statement: import draft creation, import draft cancellation, and import draft application are all covered, and Apply now has its own mutation-vs-refresh separation.
- Import Apply mutation failure remains the only path that sets `applyStatus = 'error'`, fills `applyError` / `applyErrorIssues`, announces assertively, and shows the no-partial-change statement.
- Import Apply mutation success now immediately preserves `response.apply_result`, sets success, closes confirmation, resets Apply checkboxes, announces politely once, and replaces the stale selected draft with the backend apply response before refreshing.
- Apply success plus failed list/detail refresh now preserves the successful mutation result and shows a refresh warning instead of `Не удалось применить черновик`.
- Stale pre-apply detail cannot offer Apply again after successful mutation because selected draft state is replaced with the apply response before refresh.
- Structured mutation errors still preserve row, field, code, and message details for actual Apply failures.
- Local pending-smoke wording is superseded by the completed external Hermes audit recorded below.

## PR106 correction — render already-applied refresh warning

- Added explicit `applyRefreshWarning` state for Import Apply read-model refresh failures.
- The previously hidden Apply refresh warning is now rendered in the `status === 'applied'` branch using `feedbackMessage('warning', importUiState.applyRefreshWarning)`.
- Apply success plus refresh failure remains `applyStatus = 'success'`, preserves `response.apply_result`, preserves the authoritative applied draft, and tells the user to press Refresh to reread the draft list/preview.
- Read-model refresh failure does not set `applyError`, does not populate structured mutation issues, does not show the no-partial-change statement, and does not call `announceAssertive()`.
- Stale applied state cannot offer Apply again because selected draft is already replaced with the mutation response before refresh.
- Warning state is cleared on Apply reset, opening another draft, starting Apply, actual Apply mutation failure, and successful post-Apply refresh.
- Local pending-smoke wording is superseded by the completed external Hermes audit recorded below.


## PR106 Hermes browser smoke completed

- Canonical tested GitHub runtime head: `4a2a88d156d1516568b608b113818dfe77e32210`. External GitHub verification confirmed this was the published PR #106 head; the local Codex task checkout may use rewritten SHAs.
- Environment: isolated temporary repository checkout at `/tmp/cwo-pr106-deterministic-20260713-092916/repository`, isolated SQLite database, isolated user-data directory, local frontend/backend plus deterministic local fault proxy, Headless Chrome, 1440×900 desktop viewport, 390×844 narrow viewport, no real user data.
- Verdict: `PR106_DETERMINISTIC_SMOKE_PASS_WITH_NON_BLOCKING_FINDINGS`.
- Normal Import Apply passed: draft creation returned 201, Apply returned 200, exactly one Apply POST occurred, exactly one ingredient was created, Apply result remained visible, repeat Apply became unavailable, polite success was observed, no assertive failure occurred, and `aria-busy` returned to false.
- Apply success plus refresh failure passed: Apply mutation returned 200, the proxy intentionally returned 503 for the immediate draft detail/list refresh requests, mutation success and the applied result were preserved, the imported ingredient existed exactly once, shared warning feedback told the user to press `Обновить`, false mutation-failure text was absent, no assertive Apply failure was emitted, repeat Apply stayed unavailable, manual Refresh recovered the final state, and no second Apply POST or duplicate record occurred.
- Structured mutation conflict passed: duplicate Apply returned 409, structured row-level details were visible, the persistent assertive `role="alert"` region received the blocking failure, no polite Apply success was emitted, no duplicate ingredient was created, no partial domain write occurred, and `applyRefreshWarning` remained empty.
- Settings passed: initial profile load did not show action-success feedback, Cancel restored the saved value and produced polite feedback, Save produced polite feedback, editing after Save cleared stale visible success, focus remained in the field, and `aria-busy` behaved correctly during Save.
- Responsive/keyboard smoke passed: no page-level horizontal overflow at 390×844, tested controls remained reachable, persistent announcement regions were outside `#root`, and 27 keyboard-reachable elements were observed in logical DOM order. No screen-reader certification or formal WCAG conformance claim is made.
- Diagnostics: intentional 503 responses belonged only to the refresh-failure scenario; the expected 409 belonged only to the conflict scenario; final record counts were normal import 1, refresh-failure import 1, duplicate created by rejected conflict 0; seven PNG screenshots and seven matching metrics files were verified; repository remained clean after the audit; audit-started ports were released.
- Non-blocking observations: MutationObserver errors came from the deterministic audit harness observing `#root` before it existed and were not an application defect; a separate narrow screenshot of the conflict draft was unavailable after scenario state transition, while required conflict workflow evidence was present.
- All mandatory PR106 browser scenarios passed, no code blocker remains, and PR #106 is now merged and verified. Browser smoke does not need to be repeated for this documentation-only plan PR because it changes only documentation/state files.

## MVP product-readiness implementation plan

- Added the approved active implementation plan at `docs/implementation-plan.md`.
- The plan is derived from the current strategic roadmap, actual implementation status, and the evidence-based Hermes project audit.
- `docs/roadmap.md` remains authoritative for product scope and strategic sequencing.
- `docs/implementation-plan.md` now controls the current short-horizon sequence, product-readiness slices, unfinished MVP obligations, and MVP release gates.
- PR #106 is merged and verified; its completed Hermes browser smoke remains the latest runtime verification baseline.
- Next active runtime focus is Slice A1 — User-facing technical copy cleanup, which must be implemented in a separate focused PR with no future PR number assigned yet.
- This documentation-only PR changed no runtime behavior, APIs, schemas, migrations, dependencies, lockfiles, CSS, frontend runtime code, or backend runtime code.

## Slice A1a — focused technical copy cleanup

- Implementation summary: removed the normal healthy local-service badge, kept a Russian unavailable recovery message, corrected the `/imports` introduction to match the existing draft/preview/confirm/Apply workflow, and centralized `/demo-data` visible count labels with «Другие данные» fallback for unknown keys.
- Actual changed files: `frontend/src/main.ts`, `docs/implementation-plan.md`, `state/current-focus.md`, `state/progress.md`, and `state/handoff.md`.
- Actual checks: `git diff --check` passed; `git diff --name-only`, `git diff --stat`, and `git status --short` were reviewed; `cd frontend && npm run build` passed; `cd backend && python3 -m pytest` reported the known unchanged 5 backend failures and 463 passing tests.
- Actual browser evidence: Playwright smoke used an isolated temporary SQLite database and user-data directory, local backend on `127.0.0.1:8010`, frontend on `127.0.0.1:5173`, and 1440×900 plus 390×844 viewports. Healthy state loaded without the positive API/backend badge or page-level overflow; `/imports` showed the corrected workflow copy; `/demo-data` showed Russian labels after demo install with no raw snake_case count keys; narrow view had no page-level overflow and keyboard focus remained visible; unavailable-state recovery text appeared with the existing repeat action and no observed polling loop. Screenshots were saved under `/tmp/cwo-a1a-screens`.
- Limitations: backend pytest failures are unchanged baseline failures outside this frontend-copy slice; offline smoke intentionally produced failed network-resource console messages while API requests were aborted to simulate unavailable local service.
- Merge status: branch is ready for focused review after commit/PR creation; no future PR number is assigned here.

## Slice A1b1 — Demo Data and inventory movement copy cleanup

- Scope: static user-facing copy only in `/demo-data`, `/ingredient-lots`, and `/stock-movements`.
- Updated Demo Data blocking, installation, clearing, and boundary wording to avoid backend/internal terminology while keeping dynamic blocking reasons visible and escaped.
- Updated ingredient-lot and stock-movement loading/fallback wording to describe user-visible failures without API terminology.
- Updated stock-movement balance and safety explanations to describe movement-derived balances and outgoing movement limits in product language.
- Preserved demo install/clear behavior, confirmation rules, disabled rules, stock calculations, backend-owned validation, request flow, CSS, dependencies, migrations, and `docs/implementation-plan.md`.

## Slice A1b2 — Backup and Export capability copy
- Scope: static user-facing copy only for `/backups`, `/exports`, and `dashboardBackupReminder()`.
- Updated wording to distinguish резервная копия from export, explain local file storage, and state that restore/import-back-from-export are not performed on these screens.
- Preserved dynamic filenames, raw path values, request flow, disabled states, announcements, escaping, and backend-owned status/count data.
- Deferred Reports, Help Center, route readiness metadata, path presentation redesign, and remaining A1 closure work to later focused slices.
- Verification: repository hygiene and focused source-diff review passed; frontend build passed.
- Backend baseline: 468 collected, 463 passed, and the same 5 known baseline failures; no backend files changed.
- Publication: PR #111 was published from GitHub branch `codex-rzipfx`; the pre-correction head was `b6d44e935d5e320d91b955feec97667f03c93b05`.
- Review status: runtime diff is static-copy only and approved for merge after this metadata correction and final GitHub mergeability check.

## Slice A1b3a — Reports and Report Documents product copy
- Started focused A1b3a runtime-copy cleanup from the local baseline that includes merge commit `06ade9372ff060a7c3ec33aaa01e50e32c5aceee` for PR #111.
- Scope is limited to `/reports`, `/report-documents`, and `dashboardReportsCard()` static user-facing copy, plus this state update.
- Slice A1 remains IN PROGRESS; A1b3b, A1c, A2, backend behavior, CSS, documentation rewrites, report calculations, and report-document generation remain out of scope.
- Publication metadata must be verified by the repository owner; no future PR number is assigned here.

## Slice A1 closure correction — PR #113 pending review

- Navigation readiness and Help Center cleanup are implemented in runtime: implemented modules stay marked ready, the standalone readiness placeholder stays removed, Help uses Russian product language, and onboarding terminology is cleaned.
- Technical contract rewrites from the first PR #113 head were rejected and restored to the main baseline; the runtime Help Center remains the user-facing help surface for this PR.
- Runtime source review is pending final confirmation on the corrected diff.
- Required browser smoke is pending for navigation, Help, and previously cleaned A1 routes.
- A1 is not yet closed; it remains IN PROGRESS until corrected-head review and required smoke pass.
- A2 is not yet ready and remains blocked by A1.

## Slice A1 closure verified — PR #113

- Slice A1 runtime implementation was reviewed on published SHA `040c90fa781edea8484eb84595745c3a3aaf5eaf`.
- Deterministic browser smoke completed with 53 of 53 checks passing.
- Desktop and narrow navigation, Help Center, Orders readiness workflow, cleaned A1 routes, back/forward navigation, and sidebar behavior passed.
- The original offline/recovery test infrastructure gap was not accepted as evidence; R1-R5 were replaced by a targeted retest with genuine backend termination and restart.
- The targeted retest confirmed PID termination, an empty listening port, connection-refused health state, friendly offline UI, restart against the same temporary database, and complete browser recovery.
- JavaScript console errors: 0.
- Real user data and production data were not used.
- Repository integrity and temporary-data isolation passed.
- Slice A1 is DONE.
- Slice A2 is READY and is the next allowed implementation slice.

## Slice A2 structured form validation — PR #114 implementation under review

- Implemented a shared frontend validation parser/normalizer for backend `detail`, `issues`, `field`, `loc`, `message`, `msg`, `code`, and `type` shapes.
- Applied the validation state to `/clients` create/edit and `/ingredients` create/edit only, with explicit allow-listed Russian field labels and inline field errors.
- Added minimal accessible feedback markup/styles: form-level summaries for unassigned errors, `aria-invalid`, `aria-describedby`, and stable error IDs.
- Preserved draft values on rejected submits, cleared validation on retry/success/cancel/record switch/field edits, and kept duplicate-submit protection without retry logic.
- Added dependency-free parser tests through `cd frontend && npm run test:form-validation`.
- Backend code, schemas, migrations, domain rules, recipe calculations, inventory write-offs, production readiness/confirmation, Import Apply, backup/export behavior, navigation routes, dependencies, and lockfiles were not intentionally changed.
- Slice A2 status remains IN PROGRESS — implementation PR under review. Slice A3 remains BLOCKED A2.

## Slice A2 PR #114 correction under review

- Repaired field-error clearing so typing in a corrected Clients or Ingredients field updates only that field's validation DOM and preserves focus/caret instead of re-rendering the app.
- Guarded create/edit close and record-switch actions while the corresponding Clients or Ingredients mutation is in flight, with request tokens invalidated on safe context changes.
- Split mutation validation failures from post-save list-refresh failures so saved records show success and a separate refresh warning instead of save-validation errors.
- Tightened parser field-path mapping: exact known fields and approved `body`/`query`/`path` transport prefixes map inline; unknown nested paths stay in the form summary.
- Slice A2 remains IN PROGRESS — correction under review. Slice A3 remains BLOCKED A2.

## Slice A2 verified closure — PR #114

- Final verified runtime head: `8eb5d0c2c116c83d4162d10895268375e0bc1e1e`.
- Structured validation foundation is complete for Clients create/edit and Ingredients create/edit.
- Final correction preserves the original focused input DOM node, caret and selection without a global render or programmatic refocus.
- Parser tests passed: 11/11.
- Targeted validation DOM tests passed: 4/4.
- Both frontend test scripts passed when executed concurrently.
- Frontend build passed.
- Targeted Clients and Ingredients backend tests passed: 29/29.
- Real Firefox focus-preservation smoke passed for Clients and Ingredients.
- Expected HTTP 422 validation responses were separated from unexpected request failures.
- JavaScript exceptions: 0.
- Console errors: 0.
- Unused `linkedom` and its transitive lockfile entries were removed.
- No backend runtime, schema, migration, domain, inventory, production, import, backup, export or navigation behavior changed.
- Slice A2 is DONE and awaiting PR #114 merge.
- Slice A3 is READY for a separate focused sub-slice after PR #114 is merged.

## Slice A3.1 Ingredient Lots structured validation — implementation under review

- Began the first Slice A3 sub-slice after PR #114 merged.
- Scope is limited to `/ingredient-lots` create/edit structured validation.
- `/stock-movements` and all other A3 candidate forms remain pending.
- Backend runtime behavior, schemas, migrations, dependencies, inventory calculations, and stock movement behavior are not intentionally changed.
- Slice A3.1 remains IN PROGRESS — implementation under review until PR review and accepted smoke evidence.

## Slice A3.1 correction — validation lifecycle under review

- Corrected Ingredient Lot submit start so empty validation is applied through the targeted updater before the request, clearing stale summary, inline errors, and validation-owned ARIA without a global render.
- Completed in-flight action guards for submit, cancel/clear, row edit, and row deactivate actions; deactivation now also has a handler-level guard during create/update.
- Verification: frontend parser tests, targeted validation DOM tests, frontend build, concurrent frontend tests, focused Ingredient Lot backend tests, and isolated local API smoke passed.
- Browser smoke remains pending reviewer execution. Slice A3.1 remains IN PROGRESS — correction under review.

## Slice A3.2 Inventory structured validation closure — PR116 implementation

- Baseline includes merged PR #115 / A3.1 at merge commit `8b3ea5f7ab2b880d901250d111f6f5dca369c4b4`.
- Migrated existing frontend inventory forms only: `/stock-movements` manual ingredient-lot movement create, `/packaging-items` Packaging Item create, and `/packaging-items` Packaging Item edit.
- Reused the shared structured validation parser and targeted validation DOM updater; added Stock Movement and Packaging Item wrappers, explicit field-label allow-lists, inline errors, form summaries, ARIA attributes, draft preservation, duplicate-submit guards, stale-response tokens, and success-versus-refresh-warning separation.
- The initial PR116 implementation was frontend-only. The correction added focused backend domain validation for the documented manual-adjustment reason invariant, without schema, migration, persistent model, direct packaging stock edit, historical Stock Movement edit/delete action, or new inventory architecture changes.
- Current frontend `/stock-movements` supports ingredient-lot movements only. Backend packaging movement APIs exist, but a packaging movement UI is not implemented in PR116 and remains follow-up work.
- Initial verification was superseded by later PR116 correction checks; see the correction entries below for final counts.
- Browser/UI smoke was not run in this environment; reviewer smoke remains required before merge.
- Slice A3 remains IN PROGRESS after A3.2; recipe and recipe-version validation remain a later separate slice.
- A3.2 implementation complete in PR116; merge pending.

## Slice A3.2 PR116 correction — validation lifecycle and manual-adjustment invariant

- Corrected Stock Movement and Packaging Item submit-start lifecycle so stale validation is cleared through the targeted updater and current DOM controls/actions are guarded directly, without calling the global renderer before the mutation request.
- Stock Movement lot selector is disabled during an active movement mutation and re-enabled after recoverable failure.
- Packaging create/edit/cancel context switches now clear validation, refresh warnings, and stale-response tokens only after discard confirmation succeeds; cancelled confirmations preserve the current validation state.
- Backend domain drafts now enforce the existing manual-adjustment invariant for ingredient-lot and packaging movements: `manual_adjustment_in` and `manual_adjustment_out` require non-empty `reason` and return structured `422` with `field = "reason"` through existing APIs.
- Verification after correction: frontend form-validation tests (11/11), targeted validation/update lifecycle tests (superseded; final 15/15 below), frontend build, focused backend inventory tests (82/82), and isolated API smoke with manual-adjustment-without-reason rejection all passed.
- Browser smoke remains pending reviewer execution in an environment with browser tooling.
- A3.2 implementation corrected in PR116; merge pending. A3 remains IN PROGRESS.

## Slice A3.2 PR116 correction — remaining mutation lifecycle races
- Packaging Item mutation now guards adjacent packaging filters, catalog creation, assignment, tag/category search, reload, create/edit/cancel/archive controls at both rendered/direct-DOM and handler levels so they cannot rerender over the active form during submit.
- Stock Movement selected-lot detail loading now uses a detail request token and selected-lot check, and stale detail responses do not render while a Stock Movement mutation is active.
- Control restoration uses mutation markers so pre-existing disabled/readonly states remain intact after recoverable `422` responses.
- A3.2 implementation corrected in PR116; merge pending. A3 remains IN PROGRESS. Browser smoke has not been run in Codex unless a later entry records it.

## Slice A3.2 PR116 final async lifecycle correction
- Stock Movement selected-lot balance/history reads now use a shared request-generation helper: mutation start invalidates old detail requests, post-save refresh is token-aware, and state is written only after selected-lot and submit-token freshness checks pass.
- Packaging page writes are mutually exclusive across item save, item deactivation, catalog category/tag creation, and category/tag assignment save; context changes, filters, catalog searches, reload, and row actions are blocked while any Packaging write is active.
- Mutation marker helpers moved into a focused frontend lifecycle helper module so tests execute the production helper rather than copying it.
- Final verification in Codex: frontend form-validation tests 11/11, targeted validation/update lifecycle tests 20/20, concurrent frontend validation tests 11/11 and 20/20, frontend build passed, focused backend inventory tests 82/82, and isolated temporary-SQLite API smoke passed.
- Browser smoke remains pending reviewer execution. A3.2 implementation corrected in PR116; merge pending. A3 remains IN PROGRESS.

## Slice A3.2 PR116 final correction — post-save refresh lifecycle gaps
- Packaging Item save now keeps the Packaging page mutation lock active until post-save list refresh succeeds or fails; no intermediate unlocked render is emitted before refresh completion.
- Stock Movement post-save detail refresh failure now terminates the detail status with `error` while preserving the movement success message and separate refresh warning.
- Added deferred Promise regression tests for Packaging lock-through-refresh, Packaging refresh failure, stale Packaging refresh, Stock refresh failure terminal state, and stale Stock refresh failure.
- Final verification in Codex: frontend form-validation tests 11/11, targeted validation/update lifecycle tests 20/20, concurrent frontend validation tests 11/11 and 20/20, frontend build passed, focused backend inventory tests 82/82, and isolated temporary-SQLite API smoke passed.
- Browser smoke remains pending reviewer execution. A3.2 implementation corrected in PR116; merge pending. A3 remains IN PROGRESS.

## Slice A3.3 Recipe structured validation — implementation
- PR #116 / Slice A3.2 is merged at `79286f076292645b3e83dfedfccb366dee1777f6`; A3.2 is closed and browser-smoke verified.
- Current focused slice is A3.3: structured validation for Recipe Template creation and immutable Recipe Version creation on `/recipes`.
- Recipe Version edit/delete remains prohibited; existing versions remain immutable and new formulas are created only as new versions.
- Slice A3 remains IN PROGRESS after this PR unless all remaining A3 candidates are explicitly completed.

- PR #117 correction targets published branch `codex/add-structured-validation-for-recipes`; pre-correction published head was `718d8cafa62dd9bed87f8eab4e1d7896427a9a9d`. Browser smoke remains reviewer-required unless explicitly run against the published correction head.


## Slice A3.4 Client Recipe structured validation — implementation
- Verified closure of A3.3: PR #117 is merged at `cce60e73670171717d9bfd619cd79e1c0b960fe9` and browser-smoke verified.
- Implemented A3.4 scope for Client Recipe create and composition update: shared structured backend validation, exact indexed composition paths, targeted DOM updates, structural row-error invalidation, duplicate-submit guards, create success versus list-refresh warning separation, and authoritative composition `PUT` response handling.
- Backend added an API adapter that safely prefixes individual composition-line `DomainValidationError` fields with `ingredients.{index}.` only for approved line fields; aggregate composition errors remain non-indexed.
- Automated verification in this workspace: frontend form-validation tests 16/16 passed; targeted validation/update lifecycle tests 29/29 passed; frontend build passed; focused backend Client Recipe tests 40/40 passed.
- Browser smoke: NOT RUN.
- Reason: waiting for review of the exact published GitHub PR head.
- Slice A3 remains IN PROGRESS; Client Wishes, Client Feedback, Orders, and Production Confirmation remain separate future candidates.

## 2026-07-17 — A3.5 Client Wishes structured validation branch

Historical A3.5 branch baseline at the time: Slice A3 was still open after PR #118 / A3.4 merged at `1489b0f99602ef08fc1a11ab67549a954f80335d`; exact published head `1a5dcce9a919e2ad2fb803dacdc1608b7ff24a25` passed local exact-head full automated smoke. A3.5 Client Wishes structured validation was the active branch. Later entries supersede this historical status.

Work completed in this branch:
- Migrated the existing Client Wish create form to shared structured backend validation with approved inline fields only.
- Added targeted Client Wish DOM validation updates and ARIA-connected field errors.
- Added a narrow Client Wish create mutation lifecycle with duplicate-submit prevention, context/stale-response guards, scoped busy/read-only/disabled controls, draft/focus preservation on rejected creates, and separate success-vs-refresh-warning handling.
- Preserved Client Wish status/archive behavior and left Client Feedback behavior unchanged.
- Updated README, implementation plan, current focus, progress, and handoff memory for A3.4 closure and A3.5 active scope.

Verification reported for this branch must list only commands actually run. Browser smoke is still pending for the exact published GitHub PR head; Codex has not claimed A3.5 merge or exact-head verification.

A3.5 verification run in this branch:
- `cd frontend && npm run test:form-validation` — passed.
- `cd frontend && npm run test:targeted-validation-update` — passed.
- `cd frontend && npm run build` — passed.
- Concurrent frontend form-validation and targeted-validation test execution — passed.
- `cd backend && python3 -m pytest app/tests/test_client_wishes_feedback.py` — passed, 7 tests.
- Browser smoke: NOT RUN in Codex because no existing browser executable or Playwright command was available (`command -v google-chrome`, `chromium`, `chromium-browser`, and `playwright` returned no path). External exact-head browser smoke remains required before merge.

## 2026-07-18 — A3.6 Client Feedback structured validation
- PR #119 / A3.5 merged at `e53e7852c8b384915fb77b59345170c43671151c`.
- Verified PR #119 runtime head `e19229df1afa74f4470864071e91a0e94a5631cd`; complete external exact-head smoke: PASS.
- A3.5: DONE.
- A3.6 Client Feedback structured validation: DONE in PR #120; published head `e148220ac9ad08a0fd952482a0b293f1f2d22bad`, merge commit `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`, exact-head smoke PASS.

## 2026-07-18 — PR #120 A3.6 Client Feedback exact-head verification and memory sync

- PR #120 title: `A3.6 — Client Feedback structured validation`.
- Published head: `e148220ac9ad08a0fd952482a0b293f1f2d22bad`.
- PR #120 merge commit and application runtime baseline: `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`.
- Exact-head smoke verdict: `PASS — FULL AUTOMATED SMOKE PASSED`. Smoke evidence was generated externally and is not committed to the repository.
- Automated checks recorded for the exact-head smoke: frontend form-validation tests `18/18 PASS`; frontend targeted-validation-update tests `61/61 PASS`; frontend build `PASS`; concurrent frontend validation tests `PASS`; focused backend Client Wishes/Feedback tests `7/7 PASS`; smoke Bash syntax check `PASS`; browser-runner Node syntax check `PASS`.
- Browser scenarios covered: normal Client Feedback creation; backend-authoritative structured `422` validation; draft/focus/caret/selection preservation; no write after rejected validation; duplicate-submit protection; successful create followed by controlled refresh failure; stale background response protection; Client Feedback append-only boundary; exact request URL/client ID/body/count assertions; backend state verification.
- Controlled failures were limited to the expected `422` validation response and expected `503` post-create refresh failure. Unexpected console errors: `0`. Unexpected network failures: `0`.
- Exact-head worktree was clean after smoke, and final HEAD remained `e148220ac9ad08a0fd952482a0b293f1f2d22bad`.
- Git comparison confirmed `e148220ac9ad08a0fd952482a0b293f1f2d22bad` is an ancestor of `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6` with no file-tree differences between the tested head and the merge commit.
- Known limitation: the detailed smoke artifacts are external evidence and are not stored in the repository; this documentation entry records the durable summary only.
- PR #96 / `PR96 — Workshop profile settings foundation` was reviewed as superseded by the current Workshop Profile implementation. Current main already includes backend-owned persistence, schemas, `GET`/`PUT /api/settings/workshop-profile`, length/control-character validation, unrelated-setting preservation, approved `editable_now` status, Settings UI, explicit Save/Cancel behavior, focused backend tests, current documentation, and later Markdown/PDF report-document integration that preserves existing documents. No unique required PR #96 behavior was found missing.
- Actual GitHub state for PR #96 during this sync: `open`; closure is still pending and is not claimed here.
- Next runtime slice: A3.7 Orders structured validation, with no future PR number assigned.

## 2026-07-18 — A3.7 Orders structured validation implementation

- Implemented Order create/update structured backend validation for `/api/orders` POST and `/api/orders/{order_id}` PUT.
- Preserved PR #120 / A3.6 as DONE: merge commit `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`, verified runtime head `e148220ac9ad08a0fd952482a0b293f1f2d22bad`, exact-head smoke `PASS — FULL AUTOMATED SMOKE PASSED`.
- PR #121 synchronized project memory at `5c1edba2ca50b4a503d7dd44df2fdf7fda60aa6c`.
- A3.7 was later merged in PR #122 at `8c4a092d055fd221cb18da901cee9e90106b33a4` and is DONE; its external exact-head evidence is recorded in the A3.8 entry below.
- Production Readiness and Production Confirmation remained separate follow-up slices after A3.7.

## 2026-07-19 — A3.8 Production Readiness feedback and lifecycle

- Base is PR #122 merge commit `8c4a092d055fd221cb18da901cee9e90106b33a4`. PR #122 verified runtime head `b44b80bd875ec184bbccfc376f1562ddf25fbb46` has user-provided external smoke verdict `PASS — FULL AUTOMATED SMOKE PASSED`; this is not claimed as GitHub Actions evidence.
- Audit preserved the existing Order request generations, context invalidation, order-bound transient ownership, stale callback guards, order-scoped errors, cached results, backend readiness service, response DTO, and Production Confirmation boundary.
- A3.8 adds explicit duplicate readiness suppression, order-local conflicting-action guards, accessible `Проверяем…` busy semantics, safe status-specific request failure copy, contextual issue grouping without raw IDs, and per-order attempt/result freshness metadata so a failed, older, edited-order, or wrong-order result cannot authorize Production Confirmation.
- Cached results remain stored across safe order navigation. A cached result that no longer matches the latest attempt or Order `updated_at` is visibly marked as previous/stale and cannot enable production.
- Backend no-write snapshots now cover ProductionBatch tables, ingredient movements, packaging movements, and Order lifecycle fields for valid ready and valid blocked checks. The readiness service still performs no write or reservation.
- Commands already run in the implementation worktree: frontend form-validation `19/19 PASS`; targeted-validation-update `62/62 PASS`; Order mutation lifecycle `18/18 PASS`; frontend build `PASS`; focused backend readiness/Orders `19/19 PASS`.
- Full backend branch run: `480 passed, 5 failed`; clean detached base run at `8c4a092d055fd221cb18da901cee9e90106b33a4`: the same `480 passed, 5 failed` with the same backup filename, export filename, import issue-count, inventory fixture, and purchase-suggestion fixture failures. Branch-only full-suite failure delta: zero.
- Exact published-head browser smoke is not yet claimed in this repository state entry. It remains mandatory before the Draft PR can be reported ready for human review.

## 2026-07-19 — Draft PR #123 human-review correction

- Draft PR #123 exists on `codex/a3.8-production-readiness-lifecycle` and remains IN REVIEW; A3.8 is not DONE.
- The reviewed published head was `69da410bccfc7bf9c852ef5a807d039b4fa4a74d`. Its exact-head browser smoke passed as external local evidence, not GitHub Actions evidence.
- Human review accepted the read-only backend direction but found incomplete reverse mutual exclusion, response-time borrowing of a potentially newer Order `updated_at`, and missing committed behavioral readiness-presentation tests.
- The correction keeps the existing Order controller and adds narrow same-Order write ownership for production/cancel/archive, duplicate lifecycle-action suppression, generation-safe stale callback cleanup, and readiness freshness captured at request start.
- Readiness presentation is extracted into a small dependency-free module so ready, warning, blocked, stale, loading, system-error/retry, escaping, and Production Confirmation eligibility are inspected through a behavioral DOM/view harness rather than source-string guards.
- `docs/api.md` now reflects that an Orders frontend exists while retaining the no-confirmation, no-reservation, no-write, no-batch, and no-lifecycle-mutation API boundary.
- A new corrective published head requires a complete new exact-head browser smoke. The reviewed-head smoke is historical evidence only. A3.9 and A4 remain separate.

## 2026-07-19 — Draft PR #123 persistent-write presentation correction

- Reviewed published head `b6413f9b38710c1d3b8e231a52206d9a9dd7b9be` closed the readiness freshness, same-Order reverse mutual-exclusion, behavioral presentation-test, escaping, and duplicate-request findings. PR #123 remains Draft/IN REVIEW; A3.8 is not DONE.
- Human review found a presentation mismatch: the existing start guard intentionally serialized production/cancel/archive ownership globally, while unrelated Order controls still looked enabled and could silently no-op. Cancel/archive also lacked honest visible pending labels and busy semantics.
- The correction preserves global serialization and adds one explicit valid-owner helper shared by write guards, lifecycle buttons, Production Confirmation open/submit guards, explanatory copy, and tests. It does not introduce a generic request manager or concurrent writes.
- Pending cancel/archive actions now render `Отменяем…` / `Архивируем…` with native disabled, `aria-busy="true"`, and existing danger styling on every rendered instance for the owning Order. Other Orders expose disabled production/cancel/archive controls and visible copy while navigation and safe unrelated readiness remain available.
- Keyboard-invoked readiness now preserves focus on a stable readiness-region anchor through loading and system failure; the retry action is not auto-focused, so the next Tab reaches it without an unexpected fallback to `body`.
- Deterministic lifecycle and presentation coverage now includes global owner validation, no owner overwrite, unrelated readiness/navigation, production/cancel/archive cross-Order disabled states, pending copy/ARIA, one cancel/archive request, recovery, and stale-owner cleanup.
- The prior reviewed-head exact-smoke evidence archive is unavailable and its keyboard traversal was incomplete. A new published correction head therefore requires a full exact-head smoke plus real Chrome/Chromium keyboard traversal and a retained external evidence archive before a PASS may be reported.
- Backend readiness rules, Production Confirmation domain behavior, stock movements, Order lifecycle backend rules, schemas, migrations, dependencies, CI, A3.9, and A4 remain unchanged and separate.

## A3.9 — Production Confirmation structured errors and mutation safety

- A3.9 base SHA (managed checkout `work`): `c6d87df635a5cf7d063b43ffc16dc02d64e08103`.
- PR #123 / A3.8 is merged in local history. Accepted and exact-head-smoked runtime head: `34eeaf11dbe7fbfabb3bd36ad8aa79b9469892f5`.
- PR #123 merge commit resolved locally: `c6d87df635a5cf7d063b43ffc16dc02d64e08103`.
- `gh` is unavailable in this managed environment, so PR #123 was verified by local merge history and ancestry.
- Final A3.8 exact-head smoke: `PASS — FULL AUTOMATED SMOKE PASSED`; this was external local evidence, not GitHub Actions.
- A3.8 is DONE.
- A3.9 is the current focused runtime slice. It hardens existing Production Confirmation structured errors, duplicate/stale/wrong-order ownership, authoritative success after refresh failure, and rollback tests.
- A3.9 is not DONE until review, exact-head production smoke, and merge.
- A4 responsive table containment remains separate.

## PR #124 A3.9 corrective pass

- PR #124 remains the active A3.9 Draft PR on managed branch `codex-l6nqu0`.
- Reviewed published head `f29d8115586e528afec6d9ee2c5efd1fc4fb0a5d` still required correction.
- Exact base remains `c6d87df635a5cf7d063b43ffc16dc02d64e08103`.
- Final exact-head production browser smoke has not been run in this corrective pass and remains pending human code review.
- A3.9 remains IN PROGRESS; A4 remains separate.


## 2026-07-19 — A4.1 responsive table containment

Slice A3 is marked complete based on the product owner's confirmed A3.9 Production Confirmation tests and smoke verification. PR #124 is the completed A3.9 implementation baseline; this is external product-owner evidence, not GitHub Actions evidence.

Slice A4 is now active. Current runtime work is A4.1: establish a small shared responsive table containment contract and prove it on `/ingredient-lots`. The scope is frontend layout containment only: shrinkable content/card/table-wrapper ancestors, local table scrolling, row-action reachability, and visible focus outlines. `/orders`, `/clients`, `/inventory`, and `/packaging-items` remain separate A4 follow-ups, with `/inventory` and `/packaging-items` inspected only for obvious passive shared-CSS regressions.

## A4.2 responsive Orders containment in progress

- PR #125 / A4.1 is merged and DONE.
- A4.1 merge commit: `50c44ff0919401d51c165d6ebec1266c688bfb08`.
- A4.1 runtime head: `effb5ee270c9fbddc777e57c41ad0b53acd77f9d`.
- A4.2 `/orders` is the active focused slice.
- `/clients`, `/inventory`, and `/packaging-items` remain future A4 follow-ups; do not mark all of A4 complete.

## 2026-07-20 — A4.3 Clients responsive containment started

- PR #126 / A4.2 — Contain responsive Orders tables is merged at `4487e4044d89d88538226c5b36543e6009f279f9`; runtime head `010bd1bf3791dd6a6d754ea2ed0efdcd2ab564d3`.
- A4.2 is DONE with product-owner manual responsive verification passed at `1440×900`, `1024×768`, `768×900`, and `390×844`.
- A4.3 `/clients` is now the active focused runtime slice.
- `/inventory` and `/packaging-items` remain future A4 follow-ups; Slice A4 is not complete yet.

## 2026-07-20 — A4.4a Inventory responsive containment started

- PR #127 / A4.3 is merged and DONE. A4.3 runtime head: `1f6930d8f2e3367372a384a51e7d04a3a7c96bee`; merge commit: `255703d26d9e166f00f2c9ba3030cf4bc41fe044`.
- Product-owner manual exact-head smoke for A4.3 passed.
- A4.4a `/inventory` is active and scoped to responsive containment of the read-only Inventory workspace.
- `/packaging-items` remains a separate A4.4b task.
- Slice A4 remains incomplete.

## 2026-07-20 — A4.4b Packaging Items responsive containment started

- PR #128 / A4.4a `/inventory` is merged and exact-head-smoked with `PASS — FULL AUTOMATED EXACT-HEAD SMOKE PASSED` (merge commit `b89a40f2651f3e2ae7174cfdb7989ddf03a6221e`; runtime head `4a39c815ac8fdb73bc0c7dd5f88d0779e9eb6dd5`).
- PR #129 is merged as a test-only Inventory read-model baseline repair (merge commit `bc5082f6b6e1e3796f269ec317fcbb1184ca5c83`; runtime head `413ae2d5e94f7efc0e7c8c9dc6a86f6aa1a511f6`).
- A4.4b `/packaging-items` is now the active focused runtime containment slice.
- Full backend baseline is known to have four unrelated failures in backups, exports, imports, and manual purchase suggestions tests.
- Slice A4 remains incomplete; the final cross-route responsive regression remains after A4.4b.

## 2026-07-21 — B3.1 Dashboard and Onboarding feedback branch

PR #132 is DONE at merge commit `2ce5a4d7ba099603b733e7f2836f417da0614605`; focused frontend test-compilation hardening is complete. The B1/B2 diagnostic audit still requires no fixture/backend implementation and no Dashboard backend read-model implementation. B3.1 is active in this branch and is scoped to Dashboard refresh feedback, Dashboard-rendered onboarding mutations, and passive Help regression coverage.

This branch adds a small dependency-free Dashboard/Onboarding feedback lifecycle helper plus focused tests. Dashboard manual refresh preserves previously loaded operational cards on refresh failure and reports a warning instead of a false empty state. Onboarding start, complete-step, skip, and reset share duplicate-request, stale-response, busy, announcement, and focus-recovery behavior while keeping backend responses authoritative. Help remains static/passive and does not own Dashboard or onboarding feedback.

B3.1 is not DONE until merge and required exact published-head verification. B3.2 Alerts and Purchases feedback migration remains next. No future PR number is recorded here.

## 2026-07-21 — B3.1 correction pass

PR #133 correction pass addressed Dashboard/onboarding feedback lifecycle review gaps without backend, schema, migration, dependency, CSS, or unrelated route changes. Dashboard now tracks a loaded snapshot independently from record counts, so valid empty data remains readable after refresh failure. Onboarding load now distinguishes initial load from manual refresh, blocks conflicting refresh/mutation work, clears stale feedback on explicit refresh, preserves prior state on refresh failure, and avoids unsupported post-mutation follow-up refresh behavior. Route ownership suppresses Dashboard/onboarding transient feedback, announcements, and focus after navigation, while authoritative data may still update silently.

Focused B3.1 tests now cover valid empty Dashboard snapshots, stale Dashboard callbacks, onboarding stale feedback clearing, stale-state refresh failure, refresh/mutation conflicts, stale mutation callbacks, route ownership, real focus policy, and Help helper logic used by runtime. Browser smoke remains pending and PR #133 is not merge-ready until external exact published-head smoke passes. B3.2 remains next after B3.1 merge.

## 2026-07-21 — B3.1 retry-control wiring correction

Exact-head browser smoke on published PR #133 head `fb7a4e5c2dd4757b61fd4be07c8c49003188b35b` found a product failure in the Desktop Dashboard initial-load retry scenario: the explicit `Повторить` button inside the initial-load error card was rendered but did not start the Dashboard retry request sequence.

Root cause: Dashboard rendered multiple `data-action="reload-dashboard"` controls, but runtime event binding used a single `querySelector`, wiring only the first matching control. The correction binds every rendered Dashboard reload/retry control and every rendered onboarding refresh control while preserving the existing B3.1 lifecycle helper ownership and duplicate-request protection.

B3.1 remains ACTIVE and is not DONE. PR #133 is not merge-ready until browser smoke is rerun against the new published head and passes. B3.2 Alerts and Purchases remains next after B3.1 merge.

## B3.1 shared feedback completion evidence
- B3.1 Dashboard and Onboarding shared feedback lifecycle is DONE at runtime head `4eed8c2f64d7524607cf25fc696dd964c25213cc` and merge commit `70bbc783452a373afba76bcd8f6fe94c1e7ac75b`.
- External exact-head browser smoke for B3.1 passed: PASS — FULL AUTOMATED SMOKE PASSED.

## B3.2a Alerts shared feedback lifecycle local implementation evidence
- Started from clean local exact base `70bbc783452a373afba76bcd8f6fe94c1e7ac75b` after product-owner GitHub baseline verification.
- Implemented Alerts-only lifecycle module and focused test wiring locally for human diff review.
- B3.2b Purchases remains the next separate slice.

## B3.2a correction for PR #134
- PR #134 correction targets existing branch `codex/implement-alerts-feedback-lifecycle` from base `70bbc783452a373afba76bcd8f6fe94c1e7ac75b` and previous published head `931d15c573cb821459fc4ef426cca88632c23f59`.
- Correction scope: wire Alerts route ownership to startup/navigation/popstate, run focus recovery after final resolve/dismiss render, release current mutation owners on invalid authoritative DTOs, preserve regeneration success plus refresh-warning announcement, and replace placeholder Alerts tests with real behavioral coverage.
- Browser smoke remains pending after publication; B3.2b Purchases remains a separate next slice.

## B3.2a second correction for PR #134
- PR #134 remains active on `codex/implement-alerts-feedback-lifecycle`; base is `70bbc783452a373afba76bcd8f6fe94c1e7ac75b`, first implementation head was `931d15c573cb821459fc4ef426cca88632c23f59`, and first correction head was `461c0d2a3b9e736a568b482af2e61883b694f855`.
- Correction scope: Alerts route re-entry during active operations, regeneration follow-up ownership after route loss, and disabled reset controls in empty-state rendering.
- Browser smoke remains pending; B3.2b Purchases remains separate.

## B3.2a final settlement-order correction for PR #134
- PR #134 remains active on `codex/implement-alerts-feedback-lifecycle`; base is `70bbc783452a373afba76bcd8f6fe94c1e7ac75b`.
- Published history before this correction: first implementation head `931d15c573cb821459fc4ef426cca88632c23f59`, first correction head `461c0d2a3b9e736a568b482af2e61883b694f855`, and second correction head `4b94a236037c458907b20fb425fea76e94114492`.
- Correction scope: settlement-ordered reconciliation for detached Alerts mutations, durable next-entry reconciliation for away-settled operations, and executable race-order coverage while preserving Alerts-only scope.
- Browser smoke remains pending; B3.2b Purchases remains a separate next slice.

## B3.2a identity-owned detached mutation correction for PR #134
- PR #134 remains active on `codex/implement-alerts-feedback-lifecycle`; authoritative external current head before this correction is `871b6666dc854ccc3cfd0072dc85dc2ce8e7d589`.
- Completed local Alerts-only correction replaces boolean detached mutation state with identity-bearing ownership, exact detached settlement checks, read/mutation completion separation, and lossless accepted-read reconciliation consumption.
- Focused Alerts tests include asynchronous race coverage for stale reads plus detached resolve/dismiss/regeneration, regeneration route orders, duplicate callbacks, wrong identity, invalid DTOs, and preservation of detached regeneration counters.
- Browser smoke remains pending; B3.2b Purchases remains separate and blocked until B3.2a acceptance.

## B3.2b Purchases shared-feedback lifecycle — implementation progress
- Started from logical main baseline `4692bdfa4d5171fb270687cb385a37571a8e9e2d` containing merged B3.2a Alerts lifecycle.
- Added focused Purchases feedback lifecycle and Purchases runtime coordinator modules with request-owned reads, identity-bearing mutations, detached settlement, authoritative DTO validation, snapshot/filter truth, local search, and reconciliation tests.
- Added deterministic focused frontend suite `test:purchase-suggestions-feedback` and ran it twice successfully: obsolete eight-test suite passed on each run.
- Kept backend production files unchanged. Focused backend purchase suite was run and matched the known baseline failure `app/tests/test_purchase_suggestions.py::test_manual_api_smoke` with 10 passed / 1 failed.
- Product-owner browser-smoke status for this B slice: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## B3.2b PR #135 correction progress
- Corrected the initial PR #135 defect where the Purchases lifecycle existed but the production route still used the old direct request chains.
- Wired `createPurchaseSuggestionsRuntime` into `frontend/src/main.ts`, routed Purchases list reads and mutations through lifecycle ownership, removed the old chained refresh helper, separated list reads from reference loading, and made route leave detach active mutations.
- Ran `npm --prefix frontend run test:purchase-suggestions-feedback` twice successfully after correction: obsolete eight-test suite passed on each run.
- Ran `npm --prefix frontend run build` successfully after correction.

## B3.2b PR #135 route ownership, result-owned feedback, and real focused tests
- Corrected the reviewed PR #135 head `0cf2992329b5586d898da09c5de4b9fb820da056` by adding a production-shared Purchases route transition, removing duplicate Purchases entry from `loadSectionData`, wiring normal navigation, browser `popstate`, and initial boot through that route transition, and keeping Purchases reference ownership invalidated on route leave.
- Replaced shared-state announcement reconstruction with result-owned lifecycle messages; the runtime now announces only the exact message returned by the accepted completion result.
- Extracted Purchases reference-data ownership and Purchases control binding into production-shared modules imported by runtime code and focused tests.
- Replaced the rejected eight-test focused suite with 84 independently named route/runtime/message/reference/binding tests using deferred injected requests and production-shared helpers.
- Verification completed: focused Purchases suite passed twice (84/84 both runs); related frontend suites passed (Alerts 56/56, Dashboard/Onboarding 17/17, form-validation 19/19, targeted-validation-update 62/62, order-mutation-lifecycle 32/32, order-readiness-presentation 15/15, Help 3/3); frontend build passed.
- Backend verification matched the accepted baseline: focused Purchases suite 10 passed / 1 known failed (`test_manual_api_smoke`), complete backend suite 492 passed / 4 known failed, branch-only backend failure delta 0.
- Browser smoke status remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.


## B3.2b PR #135 neutral feedback and evidence correction
- Corrected stale Purchases neutral feedback by clearing detached/reconciliation progress copy at terminal detached settlement and reconciliation success/failure while preserving retryable reconciliation obligations.
- Added production-shared Purchases feedback presentation and form-state helpers used by `main.ts` and focused tests.
- Replaced/renamed misleading focused tests and expanded the suite to 108 checks covering rendered neutral disappearance, route wiring evidence, complete manual/edit draft state, public reference ownership sequences, and binding rerender ownership.
- Verification completed: focused Purchases suite passed twice (108/108 both runs); related frontend suites passed (Alerts 56/56, Dashboard/Onboarding 17/17, form-validation 19/19, targeted-validation-update 62/62, order-mutation-lifecycle 32/32, order-readiness-presentation 15/15, Help 3/3); frontend build passed.
- Backend verification matched the accepted baseline: focused Purchases suite 10 passed / 1 known failed (`test_manual_api_smoke`), complete backend suite 492 passed / 4 known failed, branch-only backend failure delta 0.
- Browser smoke status remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.


## B3.2b PR #135 production-composition test evidence
- Replaced remaining disconnected Purchases form/reference tests with a composed harness that wires runtime callbacks to real shared form state and reference requests to the real lifecycle/form state under test.
- Added Settings target navigation source-contract coverage for `[data-action="navigate-settings-target"]` through `navigateToSection`.
- Verification completed: focused Purchases suite passed twice with 116/116 checks; related frontend suites and build passed; backend verification matched the accepted baseline with branch-only failure delta 0.
- Browser smoke status remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-22 — B3.3 local artifacts and reports feedback lifecycle implementation

- PR #135 is merged at `b11160cc1a06df24fa6666969154c37389e6ab65`; B3.2a Alerts and B3.2b Purchases are complete.
- Implemented a shared local-artifacts/reports frontend lifecycle for Backups, Exports, Report Documents, and Reports with route generation, read ownership, mutation ownership where applicable, stale callback rejection, duplicate protection, retained readable snapshots, retained last-created artifacts, refresh warnings, and result-owned announcements.
- Route contract matrix: Backups reads status + list and creates backups with a follow-up status/list GET; Exports reads status + list and creates exports with a follow-up status/list GET; Report Documents reads status + list and creates Markdown/PDF overview documents with a follow-up status/list GET; Reports reads five report endpoints and remains read-only.
- Focused frontend suite: run 1 collected 14 / passed 14 / failed 0 / skipped 0; run 2 collected 14 / passed 14 / failed 0 / skipped 0.
- Frontend regressions passed: dashboard/onboarding 17, help 3, alerts 56, purchases 116, form-validation 19, targeted-validation 62, order-mutation 32, order-readiness 15; frontend build passed.
- Backend focused artifact/report command `pytest -q app/tests/test_backups_api.py app/tests/test_exports_api.py app/tests/test_reports_api.py app/tests/test_report_documents_api.py` collected 25 / passed 23 / failed 2 (known backup/export reason sanitization baseline); `pytest -q app/tests/test_reports.py app/tests/test_report_documents.py` collected 34 / passed 34.
- Complete backend suite collected 496 / passed 492 / failed 4 / skipped 0 with known failing node IDs only; branch-only backend failure delta: 0.
- Publication metadata is inconclusive in this runner: no GitHub remote is configured and `gh` is unavailable, so a GitHub-assigned PR number and published head could not be verified here.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.4+B3.5 core workspace shared-feedback lifecycle

- PR #136 is merged; B3.3 is complete at merge commit `e7c2d97473070f361052325fd6476208629af1cc`.
- Active combined slice: B3.4+B3.5 on `codex/b3.4-b3.5-core-workspace-feedback`, starting from the same `main` SHA.
- Backend production change count remains zero; no schema, migration, dependency, lockfile, Orders, or Production expansion is included.

### Supported Formula/Client operation matrix

| Area | Supported reads | Supported mutations | Lifecycle boundary |
|---|---|---|---|
| Recipe Templates | `GET /api/recipe-templates`, `GET /api/recipe-templates/{id}` | `POST /api/recipe-templates`; rendered recipe category/tag create and assignment | list/detail/reference owners; authoritative entity DTO before clear/select; mutation-follow-up GET |
| Recipe Versions | `GET /api/recipe-templates/{id}/versions`, `GET /api/recipe-versions/{id}` | `POST /api/recipe-templates/{id}/versions` with complete ingredient composition | immutable version-create owner; version list/detail owners; prior snapshots are never mutated |
| Recipe Calculation | `GET /api/recipe-versions/{id}/calculation` | none | independent calculation owner keyed by version and requested target |
| Clients | `GET /api/clients`; selected-client related reads | `POST /api/clients`, `PUT /api/clients/{id}`, `POST /api/clients/{id}/deactivate` | list/related owners; client-context mutation owners; structured validation preserves drafts |
| Client Recipes | list/detail GETs and client-owned list reads | create, full composition replacement, deactivate, restore through existing endpoints | list/detail/reference owners and selected-ClientRecipe mutation context; source RecipeVersion remains unchanged |
| Wishes | client wish list GET | create, status PUT, archive POST | client-context related-read and mutation owners; submitted sensitive text is excluded from technical feedback |
| Feedback | client feedback list GET | create only | client-context related-read and create owner; no update/archive/delete path |

Explicitly unsupported: RecipeTemplate update, in-place RecipeVersion update/delete/archive, persisted RecipeIngredient row CRUD, ClientRecipe calculation, and Client Feedback update/archive/delete.

### Supported Inventory/Catalog operation matrix

| Area | Supported reads | Supported mutations | Lifecycle boundary |
|---|---|---|---|
| Inventory | overview, ingredient-lot balances, packaging balances | none | one composed read-only snapshot with retained data after refresh failure |
| Ingredients | ingredient list plus category/tag reference GETs | create, update, deactivate, category/tag create and assignment | list/reference owners and entity/catalog mutation owners; filters and drafts remain local |
| Ingredient Lots | lot list and ingredient references | create, update, deactivate | list/reference owners and lot-context mutation owners; backend remains authoritative for identity, units, costs, and balance |
| Stock Movements | selected-lot movement list and balance GETs | one append-only create POST | exactly one POST; validated response; ambiguous lock; GET-only one-shot/manual reconciliation; no loop |
| Packaging | packaging list plus category/tag reference GETs | create, update, deactivate, category/tag create and assignment | list/reference owners and item/catalog mutation owners; no stock-movement behavior |

Explicitly unsupported: ingredient/lot balance overwrite, StockMovement update/delete, Packaging StockMovement/write-off, Orders, and Production.

### Implementation decisions

- Production modules provide bounded lifecycle, runtime, route ownership, binding, and presentation adapters for each family; `main.ts` composes those same modules.
- Reads distinguish initial, manual refresh, detail, related, reference, calculation, mutation-follow-up, and reconciliation work.
- Route leave rejects stale presentation and detaches mutations; obsolete same-route references are discarded silently through their current context predicate.
- Mutation completion must match the current owner, active route/context, and authoritative DTO before any form reset or selected-entity/list side effect.
- Definite backend failures preserve drafts. Ambiguous transport outcomes lock repeat mutation until authoritative GET reconciliation.
- Accepted success remains visible when a follow-up read fails; refresh failure is a warning over the retained readable snapshot.
- Focus targets resolve to actual controls/forms/workspaces, and announcements are owned by the accepted request result.
- External smoke-authoring contract not stored in the repository; not required for this smoke-deferred runtime slice.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
- Next slice: B3.6 — Order-to-production shared-feedback lifecycle.

## 2026-07-23 — B3.3 PR #136 correction

- Earlier local runner notes could not verify publication, but GitHub publication was subsequently verified by the product owner.
- Authoritative PR: #136 — B3.3 — Local artifacts and reports shared-feedback lifecycle.
- Authoritative branch: `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`.
- Historical correction base was `b11160cc1a06df24fa6666969154c37389e6ab65`; PR #136 is now merged and B3.3 is complete at `e7c2d97473070f361052325fd6476208629af1cc`.
- Correction addresses five review gaps: irreversible detached mutation ownership, production-composed runtime tests, real production focus recovery, separate warning/error presentation, and reconciliation lock after ambiguous outcomes.
- Focused and regression test counts are recorded in the PR body and final correction response after execution.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.3 PR #136 DOM binding and reconciliation correction

- Added a focused correction for PR #136 on `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle` to address DOM binding validity, duplicate focus attributes, detached reconciliation sequencing, request-owned announcements, focus target consistency, feedback cleanup, reconciliation-disabled controls, Dashboard navigation cleanup, and the Reports read-only test harness.
- Focused test counts and regression/backend verification are recorded in the final correction response after execution.
- GitHub PR body is intentionally not updated by this correction; the product owner will update it manually.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.3 PR #136 remaining reconciliation/result-boundary correction

- Historical correction entry for PR #136; the PR is now merged and B3.3 is complete at `e7c2d97473070f361052325fd6476208629af1cc`.
- Branch: `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`; base `main`; base SHA `b11160cc1a06df24fa6666969154c37389e6ab65`.
- Published head before this correction: `aae116536c2b68dec0808ccd0cae099f325e09ae`.
- Correction scope closes remaining B3.3 gaps for detached-mutation reconciliation ordering, failed provisional reconciliation GET queueing, focusable create targets, accepted-only Export entity counts, accepted-only Report Document reason clearing, restored stale/absent and same-route tests, and dead helper cleanup.
- GitHub PR body is intentionally not updated by this correction; the product owner will update it manually.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.3 PR #136 reconciliation retry ownership correction

- Historical correction entry for PR #136; the PR is now merged and B3.3 is complete at `e7c2d97473070f361052325fd6476208629af1cc`.
- Published head before this correction: `1e8a9fa8f063346cab5cb28c24c6eacf38e526a1`.
- Corrected retry ownership so `reconciliationRequired` controls the mutation lock, while automatic GET execution is allowed only by one unconsumed post-settlement queue represented by `pendingReconciliationAfterRead`.
- Added snapshot-aware focused tests proving provisional failure before settlement does not auto-retry, detached settlement later starts exactly one authoritative GET, authoritative failure does not loop, authoritative success does not add extra GETs, and validated known success is the only path to `commitAccepted`/`applyCreated`.
- GitHub PR body remains product-owner-owned and was not updated by this correction.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.4+B3.5 verification evidence

- New Formula/Client suite passed twice: 34 collected, 34 passed, 0 failed, 0 skipped on each run.
- New Inventory/Catalog suite passed twice: 41 collected, 41 passed, 0 failed, 0 skipped on each run.
- Existing frontend regressions passed: form validation 19/19; targeted validation 62/62; order mutation lifecycle 32/32; order readiness presentation 15/15; Dashboard/Onboarding 17/17; Help 3/3; Alerts 56/56; Purchases 116/116; Local Artifacts/Reports 32/32.
- Frontend build passed after the final lifecycle and regression-test alignment.
- Focused backend domain suites discovered from the repository collected 190 and passed 190 with 0 failures/skips.
- Complete backend suite matched the accepted baseline exactly: 496 collected, 492 passed, 4 failed, 0 skipped. The four failing node IDs are the accepted backup reason, export reason, import issue-count, and purchase manual-smoke baseline failures; branch-only failure delta is 0.
- Browser smoke was not run or claimed: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
- Publication and exact final-head evidence are recorded after commits, push, and PR creation.

## 2026-07-23 — PR #137 context and reconciliation ownership correction

- PR #137 remains open and under review; B3.4+B3.5 is not marked DONE.
- Corrected same-route entity ownership so read identity includes route, operation, context key, route generation, and request identity. A different context explicitly supersedes the previous same-operation owner; obsolete callbacks settle without presentation effects or owner leaks.
- Corrected mutation ownership so exact entity context participates in completion matching and rejected/obsolete callbacks cannot reset or apply a different context.
- Replaced route-level boolean-only reconciliation with a structured, epoch-owned obligation mapped by the Formula/Client and Inventory/Catalog domain adapters.
- Exact authoritative operation and context are now required to clear a lock; unrelated, wrong-context, invalid, stale, detached, and provisional reads preserve it.
- StockMovement reconciliation is attached to the original lot and requires validated movement-history plus lot-balance GETs for that lot. Reference loading, lot lists, overview reads, and another lot cannot clear it.
- StockMovement remains one POST per user action. The post-settlement automatic GET queue is consumed at most once, failure does not loop, and manual original-lot retry remains available.
- Final correction verification before publication: Formula/Client 47/47 twice; Inventory/Catalog 51/51 twice; form validation 19/19; targeted validation 62/62; Order mutation 32/32; Order readiness 15/15; Dashboard/Onboarding 17/17; Help 3/3; Alerts 56/56; Purchases 116/116; Local Artifacts/Reports 32/32; frontend build passed.
- Focused backend domain verification passed 186/186. Complete backend comparison collected 496: 492 passed, the same 4 accepted failures, 0 skipped; branch-only failure delta 0.
- Publication SHA is recorded after the correction commit and push.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — PR #137 detached settlement and recipe snapshot correction

- PR #137 remains open and under review; B3.4+B3.5 is not marked DONE. Published head before this correction: `b95b0b293f6f381495fa9e08d36b1ad27a214252`.
- Added an exactly-once mutation settlement callback to both B3.4+B3.5 production runtimes. It runs only after an accepted mutation start and covers success, definite/ambiguous failure, invalid DTO, detached completion, obsolete context, and stale ownership.
- Route-local finalizers clear busy/saving/deactivating state and restore controls without applying DTOs, clearing drafts, announcing, focusing, clearing reconciliation, or repeating the write.
- Direct RecipeTemplate, RecipeVersion, Client, Ingredient, Ingredient Lot, and Packaging handlers use the shared route-local finalization primitive and resume GET-only reconciliation when the user has returned to the route.
- ClientRecipe create, composition, deactivate, and restore now recover from detached settlement without leaving the route permanently blocked.
- RecipeTemplate opening is one context-owned atomic detail-plus-version snapshot. Partial failure commits neither half, and a late Template A snapshot cannot overwrite Template B.
- Exact RecipeVersion reconciliation remains independent and can clear only the matching `recipe-version-list` / `template:<id>` obligation; it does not overwrite another selected template.
- Focused production-aware coverage includes every mutation settlement path, rejected-start exclusion, direct and runtime route-return recovery, retained drafts, atomic snapshot delay/failure/context-switch cases, and the existing exact StockMovement contract.
- Final verification before publication: Formula/Client 60/60 passed twice; Inventory/Catalog 62/62 passed twice; form validation 19/19; targeted validation 62/62; Order mutation 32/32; Order readiness 15/15; Dashboard/Onboarding 17/17; Help 3/3; Alerts 56/56; Purchases 116/116; Local Artifacts/Reports 32/32; frontend build passed.
- Focused backend domain verification passed 186/186. Complete backend comparison collected 496: 492 passed, the same 4 accepted failures, 0 skipped; branch-only failure delta 0.
- Publication SHA is recorded after the correction commit and push.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-24 — B3.6 Order-to-production shared-feedback lifecycle

- B3.4+B3.5 is DONE: PR #137 merged at `10e985229e8020fcf98c67427cde889b5cd934f8`. B3.6 started from that exact `main` SHA on `codex/b3.6-order-production-feedback`.
- Extended the existing `OrderMutationController` with `/orders` route ownership, exact request settlement, one-result feedback channels, request-owned announcements, full Order/readiness/ProductionBatch DTO boundaries, and a structured exact original-Order production reconciliation obligation.
- Order list, reference and detail reads now reject stale/wrong-context responses, retain readable data on refresh failure, and apply the multi-source reference snapshot atomically.
- Create/update, cancel/archive, readiness and production use exact owners and exactly-once local finalizers. Drafts survive deterministic or ambiguous failures; known mutation success remains success when a later GET fails.
- Production sends one POST per accepted confirmation and never retries it automatically. Network-uncertain or invalid outcomes block unsafe actions; at most one automatic exact reconciliation attempt is consumed, failures do not loop, and manual recovery remains available.
- Only `GET /api/orders/{original_id}` plus `GET /api/orders/{original_id}/production-batch`, both fully validated and coherent, can clear production uncertainty. Lists, partial reads, wrong Order, wrong batch, stale or detached reads cannot unlock it.
- PR #138 exact-head correction preserves the first unresolved production reconciliation obligation and globally blocks new Production Confirmation/POST work for every Order until the original exact Order and exact ProductionBatch reconcile coherently. Unrelated Orders remain readable and may still run readiness checks.
- Correction verification: Order production feedback 21/21 twice; Order mutation lifecycle 32/32 twice; readiness presentation 15/15 twice; form validation 19/19; targeted validation 62/62; Formula/Client 60/60; Inventory/Catalog 62/62; core wrapper 122/122; production build passed.
- Previously accepted frontend evidence remains unchanged for Dashboard/Onboarding 17/17, Help 3/3, Alerts 56/56, Purchases 116/116, and Local Artifacts/Reports 32/32; those unaffected suites were not rerun for this correction.
- Backend was not rerun because the correction changes no backend file. Preserved evidence: focused Orders/Production/Stock suites 95/95; complete suite collected 496, passed 492, failed the same 4 accepted baseline tests, skipped 0; branch-only backend failure delta 0.
- No backend production, migration, dependency, lockfile, database, smoke runner, screenshot, or browser artifact belongs to this slice.
- Smoke status: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-26 — B3 implementation window closed; B4.1 activated

- PR #138 is merged: accepted runtime head `a8cf9d3e21aa46af3f9b2837a44b918cad638910`; merge commit `bac8672ecb04c96e25bf00c50cfba07f79eadb99`.
- PR #139 is merged: accepted runtime head `9ee94810f4dddbc03faf8c7cdbe188faa43a4e72`; merge commit `c33e7f32decabe74de68051ccdc9e87d75c58cb6`.
- B3.1–B3.6 are complete.
- The Backups narrow-width blocker found during the first full-smoke attempt was closed by PR #139.
- Final exact-head smoke on `9ee94810f4dddbc03faf8c7cdbe188faa43a4e72`: `PASS — FULL AUTOMATED SMOKE PASSED`.
- Backend branch-only failure delta: `0`.
- The four known backend baseline failures remain unresolved:
  - `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`
  - `app/tests/test_purchase_suggestions.py::test_manual_api_smoke`
- B3 implementation and its deferred full integration-smoke gate are complete. Block B remains active through B4.
- Next focused runtime slice: `B4.1 — Safe GET timeout and recovery foundation`.

## 2026-07-26 — B4.1 Dashboard safe GET timeout implementation

- Started from clean `origin/main` `f3fc8d0c8872908801f1b667731c5792c82448ea` on `codex/b4.1-dashboard-safe-get-timeout`; PR #138, PR #139, and PR #140 remain merged and untouched.
- Added one production-used Dashboard read coordinator with a single `8_000 ms` whole-operation deadline, one `AbortController`, five concurrent source GETs, per-source validation, atomic candidate construction, and exactly-once terminal cleanup.
- Extended the existing Dashboard lifecycle for timeout and silent cancellation presentation. Initial timeout shows explicit Russian recovery copy; refresh timeout preserves the prior coherent snapshot, including a valid empty snapshot.
- Abort support is opt-in through the five shared Dashboard GET functions. Existing non-Dashboard callers omit the signal, mutations cannot pass through the GET-only helper, and no automatic retry, polling, backend change, API change, schema change, migration, dependency, lockfile, or CSS change was added.
- Launcher inspection found that database initialization completes before backend process start, followed by a one-second process-alive check before the browser opens; there is no health-readiness poll. The eight-second localhost deadline safely bounds the remaining startup gap and indefinite read hangs without adding polling.
- Frontend verification: Dashboard/Onboarding 33/33 passed twice; Help 3/3; form validation 19/19; targeted validation 62/62; Alerts 56/56; Purchases 116/116; Orders/Production 21/21; Formula/Clients 60/60; production build passed.
- Backend base/head comparison: both runs collected 496, passed 492, failed the same 4 accepted baseline tests, and skipped 0; branch-only failure delta is `0`. Exact-head browser smoke is recorded after final implementation publication.
- Status: `IMPLEMENTED — EXACT-HEAD BROWSER SMOKE REQUIRED`. B4.1, B4, and Block B are not marked DONE.

## 2026-07-26 — Block B closed; backend baseline correction gate opened

- Branch: `claude/close-block-b-authorize-backend-hardening`. Starting `origin/main`: `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa`. Documentation and state only; no production or test file changed.
- **B4.1 — DONE.** PR #141 `B4.1 — Dashboard safe GET timeout and recovery` merged 2026-07-26; final reviewed head `d0cde127355b146f101ddf3769d76d0226c71ec0`; merge commit `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` (VERIFIED FROM REPOSITORY / GITHUB).
- Accepted PR #141 evidence, all SUPPLIED TASK BASELINE and not re-run here: Dashboard/Onboarding focused suite `42/42`; frontend production build `PASS`; backend branch-only failure delta `0`; product-owner-verified exact-head browser smoke `PASS` on 2026-07-26.
- The earlier dated record reports `33/33` for an intermediate branch state. The accepted PR #141 record reports `42/42` for the final reviewed head. Neither result was re-run in this documentation task, and no cause for the difference is claimed.
- Accepted PR #141 smoke coverage, all SUPPLIED TASK BASELINE — product-owner-verified exact-head smoke of PR #141 on 2026-07-26; not re-run in this documentation task: normal Dashboard initial load; initial timeout; manual recovery; refresh timeout retaining the coherent snapshot; expired-generation rejection; route-detached rejection; duplicate-start protection; desktop `1440 × 900`; narrow `390 × 844`; visible and unclipped keyboard focus; initial retry with Enter; initial retry with Space; refresh retry with Enter; refresh retry with Space; exactly five GET requests per accepted generation; zero mutations; zero unexpected console errors; zero unexpected console warnings; zero page errors; zero HTTP failures; zero unexpected request failures.
- **B4 — DONE.** B4 is closed with the Dashboard safe-GET pilot only. Safe GET timeout and recovery coverage for the remaining read routes, including but not limited to Alerts, Purchases, Orders, Reports, Backups, Exports, and Report Documents, was deliberately deferred and was not delivered. Any future expansion requires a separately authorized slice and a change request. Closing B4 does not imply that those routes are protected against an indefinitely hanging local GET.
- **Block B — DONE.** B4.1 was the only approved B4 runtime slice. No approved B4.2 contract exists and no B4.2 slice was created or activated.
- **Diagnostic outcome: PATH A / COMPLETE** (EXECUTED IN THIS TASK). Python `3.12.13` in an external venv outside the repository; pytest `8.4.2`; run from `backend/` with rootdir `backend/` and configfile `pyproject.toml`. Complete baseline reproduced `496 collected, 492 passed, 4 failed, 0 skipped` with zero drift and no additional failures. Each named node ran twice in isolation; each surrounding test file ran completely. All four failures are deterministic. The temporary environment was removed and verified absent.
- Findings: backups and exports reason sanitization are `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED`. Both failed at the assertion after the API was reached and the artifact was written. `backend/app/services/backup.py:47` and `backend/app/services/export.py:84` are structurally duplicated implementations that map each replaced character to one underscore, while both tests require a run of replaced characters to collapse to a single underscore. No product documentation defines which behavior is required: `docs/backup-and-restore.md:24` and `docs/export.md` describe the filename parts and the manifest reason but state no normalization rule. **The production behavior is not stated to be wrong.** Severity, root cause, correction surface, schema requirement, grouping, slice, tests, and smoke are all recorded as `NOT DETERMINED FROM CURRENT EVIDENCE`. Resolving this needs a product decision, not more diagnostics; it is tracked as `CR-005`, status `needs product decision`.
- Recorded as observed facts for those two nodes, independent of the undecided contract: traversal characters are neutralized, existing artifacts are not overwritten, the filename charset is restricted to alphanumerics plus `-` and `_`, generation is backend-owned, artifacts are human-readable, and the source database is not modified. A related undecided point is that the backup metadata reason is recovered by splitting the filename stem on `-` while `-` is itself permitted inside the sanitized reason.
- The import draft node is a `TEST DEFECT`, severity MEDIUM: `05.07.2026` is a deterministic Russian `DD.MM.YYYY` date that `docs/import-format.md:152` requires to be a `date_format_normalized` warning, so the actual `error_count` of `3` is correct and the test's `>= 4` and `invalid_date` assertions encode a superseded contract. The draft was created, blocked, and never applied.
- The purchase-suggestions node is a `TEST DEFECT`, severity MEDIUM: it fails in seeding before the API is reached because `seed_ready(c, lot_qty="0")` asks for a zero-quantity stock movement that the domain correctly rejects. It is the only one of 45 `seed_ready` call sites passing `"0"`; every other low-stock scenario seeds a positive quantity. This node already sets its own threshold separately at `:215-216` (`minimum_stock='10'`), so unlike the `:79` sibling it needs no threshold change — only the lot quantity is invalid.
- No data loss or unsafe mutation was found in any node. Full per-node evidence: `docs/backend-baseline-failure-triage.md` (created by this task, then fully replaced in place after review of the same active gate).
- **Next slice — exactly one active:** `R3 — Repair purchase-suggestions API smoke seeding`, test-only. It changes exactly one value: `lot_qty="0"` → `lot_qty="1"` in the `seed_ready(...)` call at `backend/app/tests/test_purchase_suggestions.py:214`. `packaging_qty="2"` on that same line and the existing `minimum_stock='10'` setup at `:215-216` stay unchanged, because the existing threshold of `10` is already higher than the new lot quantity of `1` and the below-minimum condition therefore remains true without touching the threshold. No other line in the test may change. Every existing API and no-mutation assertion is preserved and must execute. No production-code change, no skip, xfail, deletion, rename, or weakened assertion. Required smoke is the **backend suite only**; the slice changes no runtime surface, so no browser, visual, or route-rendering check applies.
- `R2` (import draft issue-count contract alignment, test-only) is the next deferred slice. The two filename nodes have **no slice** and are blocked on `CR-005`. Any focused `/backups` and `/exports` visual check belongs to that product decision and its future implementation slice, not to the active slice.
- `R3` and `R2` tie on primary priority 5; `R3` was selected on the tie-breaker criterion of greater direct user/data impact, because it restores execution of the guarantee that mark-purchased creates no stock movements, no packaging movements, and no lots. Both are fully evidenced from repository sources alone and need no product decision, which is why one could be activated while the filename nodes could not.
- Recorded neutrally without diagnosis or activation: a potential SQLite backup transaction-consistency candidate needing a separate evidence-based diagnostic (`CR-004`), distinct from the `CR-005` filename-contract decision.
- Product release readiness is not claimed. Packaging and release smoke remain blocked; C1–C4 remain inactive.
- No browser, keyboard, responsive, packaging, or release smoke was executed or claimed for this documentation commit.

## 2026-07-27 — R3 purchase-suggestions API smoke seeding repaired

- Branch: `claude/r3-repair-purchase-suggestions-api-smoke-seeding`. Starting `origin/main`: `6cb6f446c2a47a5272c51bfb63b3159d23cb5db2` (PR #142 merge commit, which contains the final reviewed PR #142 head `64850b3aa508d63ca1f1cefe240b2eaba50d9e72`).
- Exact changed value: `lot_qty="0"` → `lot_qty="1"` in the `seed_ready(...)` call at `backend/app/tests/test_purchase_suggestions.py:214`. `packaging_qty="2"` on that same line and the `minimum_stock='10'` setup at `:215-216` are unchanged, and no other line of the test changed. The runtime/test diff is exactly one changed value on one line.
- No production change of any kind. The zero-quantity domain rule, `seed_ready(...)`, and every other `seed_ready(...)` call site are untouched. This slice is test-only.
- Diagnostic environment (EXECUTED IN THIS TASK): Python `3.12.13` in a temporary venv outside the repository, pytest `8.4.2`, run from `backend/` with rootdir `backend/` and configfile `pyproject.toml`. The environment was removed and verified absent afterwards.
- Pre-change complete backend suite reproduced the accepted baseline exactly: `496 collected, 492 passed, 4 failed, 0 skipped`, failing exactly the four accepted gate nodes. The isolated target node failed during arrangement inside `seed_ready(...)` with `DomainValidationError: Количество движения должно быть больше нуля.`, before the API surface was reached.
- Post-change target-node results: `app/tests/test_purchase_suggestions.py::test_manual_api_smoke` `PASSED` on both isolated runs. It now reaches `POST /api/purchase-suggestions/regenerate`, `GET /api/purchase-suggestions`, `POST /api/purchase-suggestions/{id}/mark-purchased`, the default open-list filter, and `status=all`, and its three no-mutation assertions — stock movements, packaging stock movements, and ingredient lots unchanged — execute and pass.
- Surrounding file result: `app/tests/test_purchase_suggestions.py` `11 passed`.
- Complete backend result after the change: `496 collected, 493 passed, 3 failed, 0 skipped`.
- Remaining three failing node IDs, exactly and with no new failure:
  - `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`
- Smoke: backend suite only — `PASS`. No browser, visual, keyboard, responsive, packaging, or release smoke was required, executed, or claimed.
- `R2` remains deferred and was not implemented. The two filename nodes remain blocked on `CR-005`. `CR-004` remains separate and unactivated. C1–C4 remain inactive and product release readiness is not claimed.
- PR publication state: the branch is pushed and a Ready-for-review pull request targeting `main` is opened immediately after this commit; GitHub assigns the number at creation time. `R3` is `IMPLEMENTED — REVIEW AND MERGE REQUIRED` and is not DONE until reviewed and merged.

## 2026-07-27 — PR #143 merged (R3 DONE); R2 import draft baseline test contract aligned

- **`R3` — DONE.** PR #143 `R3 — Repair purchase-suggestions API smoke seeding` is merged (VERIFIED FROM REPOSITORY / GITHUB): state `MERGED`, final reviewed head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`, merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`, merged at `2026-07-27T04:01:23Z`. Accepted `R3` backend result: `496 collected, 493 passed, 3 failed, 0 skipped`. No production code changed in `R3`. The prior dated `R3` entry above described the pre-merge state and is superseded by this line, not edited.
- Branch: `claude/r2-align-import-draft-baseline-test`. Starting `origin/main`: `f6468fae04f9dc7ae03a491560a32fac94f3a1ec` (the PR #143 merge commit, which contains the final reviewed PR #143 head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`). No rebase, no force-push, no history rewrite.
- Exact test assertion changes, confined to the assertion block of `backend/app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`:

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

- The response status assertion, the request payload, the CSV data, the date `05.07.2026`, the target type, and the global `missing_required_column` assertion are unchanged. The corrected assertions are strictly more specific than the ones they replace: exact counts, an explicit blocked-apply assertion, and an exact row-code set instead of a subset.
- No production change of any kind. `_normalize_date_value`, `_readiness`, `_issue_counts`, required-column handling, `missing_required_value`, import Apply, and the import preview/confirmation flow are untouched, and `docs/import-format.md` was not modified. This slice is test-only.
- Test environment (EXECUTED IN THIS TASK): Python `3.12.13` in a temporary venv outside the repository, pytest `8.4.2`, run from `backend/` with rootdir `backend/` and configfile `pyproject.toml`. The environment was removed and verified absent afterwards.
- Pre-change complete backend suite reproduced the accepted post-`R3` baseline exactly: `496 collected, 493 passed, 3 failed, 0 skipped`, failing exactly the two filename nodes and the import node.
- Pre-change isolated target node: the endpoint returned `201` and the test failed at `assert 3 >= 4` at `backend/app/tests/test_imports_api.py:107`. Observed values were `error_count` `3`, `warning_count` `1`, readiness `blocked`, `apply_readiness.can_apply` `false`, global codes `{missing_required_column}`, and row-0 codes `{invalid_decimal, invalid_unit, date_format_normalized}` — the date issue carrying severity `warning` with the message "В строке 2 дата «05.07.2026» будет прочитана как 2026-07-05". No import Apply occurred and no production data was written.
- Post-change target-node results: `app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues` `PASSED` on both isolated runs.
- Surrounding file result: `app/tests/test_imports_api.py` `7 passed`.
- Import parsing sibling result: `app/tests/test_import_parsing.py` `16 passed`, `0 skipped` — proving that deterministic `DD.MM.YYYY` normalization still emits `date_format_normalized` and that genuinely invalid dates still emit `invalid_date`.
- Complete backend result after the change: `496 collected, 494 passed, 2 failed, 0 skipped`. `app/tests/test_purchase_suggestions.py::test_manual_api_smoke` passes.
- Remaining two failing node IDs, exactly and with no new failure and no skip:
  - `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
- Smoke: backend suite only — `PASS`. No browser, visual, keyboard, responsive, route-rendering, packaging, restore, migration, or release smoke was required, executed, or claimed.
- The two filename nodes keep their `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED` classification, have no slice, and remain blocked on `CR-005`. They must not be started from the unmerged `R2` branch. `CR-004` remains separate and unactivated. `state/change-requests.md` was not modified. C1–C4 remain inactive and product release readiness is not claimed.
- PR publication state: the branch is pushed and a Ready-for-review pull request targeting `main` is opened immediately after this commit; GitHub assigns the number at creation time. `R2` is `IMPLEMENTED — REVIEW AND MERGE REQUIRED` and is not DONE until reviewed and merged.

## 2026-07-27 — PR #144 merged (R2 DONE); CR-005 backup/export filename reason contract decided

- **`R2` — DONE.** PR #144 `R2 — Align import draft baseline test with date normalization` is merged (VERIFIED FROM REPOSITORY / GITHUB): state `MERGED`, final reviewed head `52e2c64fc601b458cfd60e8b86a778efabd65671`, merge commit `8efbdc5c85b5932f4aeef51045542c207cf4635c`, merged at `2026-07-27T04:21:16Z`. No production code changed in `R2`; it was test-only. The prior dated `R2` entry above described the pre-merge state and is superseded by this line, not edited.
- Starting `origin/main` for this documentation commit: `8efbdc5c85b5932f4aeef51045542c207cf4635c` — exactly the PR #144 merge commit, which contains the final reviewed PR #144 head. Both commits were verified as ancestors of `origin/main`. Branch: `claude/decide-cr-005-artifact-reason-contract`, created from that clean `origin/main`. No rebase, no force-push, no history rewrite, no auto-merge.
- Accepted backend baseline after `R2`, carried forward as **VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE** and **not** re-executed in this task: `496 collected, 494 passed, 2 failed, 0 skipped`. The two remaining failing nodes are exactly:
  - `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
- **Product-owner decision recorded: `CR-005` is accepted.** Two distinct representations are separated permanently. The *human reason* stays `text = (reason or "manual").strip() or "manual"`. The *filename reason segment* is a canonical, path-safe slug derived from it: preserve Unicode alphanumerics exactly; treat underscore and every non-alphanumeric character as a separator, including whitespace, hyphen, dot, slash, backslash, punctuation, and symbols; collapse each maximal run of separators to one underscore; strip leading and trailing underscores; use `manual` when empty; prefix a digits-only result with `reason_`; preserve letter case; no lowercasing, no transliteration, and no new length limit. Worked contract examples: `before/update ../unsafe` → `before_update_unsafe`; `before-import` → `before_import`; `___before---import___` → `before_import`; `перед обновлением` → `перед_обновлением`; `123` → `reason_123`; whitespace-only → `manual`; punctuation-only → `manual`.
- Hyphen decision: literal hyphens are not allowed inside a newly generated filename reason segment and normalize to underscore, because the hyphen is already a structural filename separator, backup metadata parsing splits the stem on it, allowing it makes the round trip ambiguous, and the uniqueness suffix is itself a hyphen plus a number. Hyphens remain allowed in the human reason and in the export manifest reason.
- Numeric-only decision: a filename reason segment is never purely numeric; a numeric-only human reason receives the `reason_` prefix so it cannot be confused with the numeric uniqueness suffix `-1`, `-2`, `-3`.
- Filename grammar is preserved. No new filename version, marker, sidecar format, or migration is authorized. Round trip: for newly generated artifacts the create, list, and status reasons are all the same canonical segment, the visible UI reason resolves from that segment, and the uniqueness suffix is never part of the reported reason. The export JSON manifest keeps the normalized human reason and the export schema version does not change. Existing artifacts are never renamed, rewritten, or deleted, no migration is required, and legacy listing stays best-effort without claiming exact recovery for ambiguous legacy filenames.
- Displayed reason is filename-derived from the existing API `reason` field — no metadata table, sidecar file, new API field, frontend-only reconstruction rule, or hidden persistent metadata. The contract has two layers: the **backend/API `reason` is the canonical slug** and the single source of truth, and the **frontend consumes that slug and must never reconstruct, sanitize, or normalize it**, mapping **known system slugs** to the **existing localized Russian display labels** and rendering **custom or unmapped slugs verbatim**. The visible label is therefore **not always literally the canonical slug**: canonical `before_import` renders as `Перед импортом`, while the unmapped canonical `before_update_unsafe` renders verbatim. The backup and export mappings are separate and differ — `manual` is `Обычная резервная копия` on `/backups` and `Обычный экспорт` on `/exports`, and `support_snapshot` exists only in the export mapping. These tables record existing `frontend/src/main.ts` behavior; no Russian label is added, removed, or reworded by this decision.
- Documentation was also corrected for stale implementation status: the manual backup UI and local JSON exports with their `/exports` workspace **are implemented**, while Restore, scheduled backups, CSV/XLSX export, and cloud backup are **not**. `CR-004` and Restore remain unresolved and are not claimed as resolved.
- Shared helper boundary: one narrowly scoped backend helper, recommended `normalize_artifact_reason_segment(value: str | None) -> str` in `backend/app/services/local_artifact_filenames.py`, applying **only** to backup and export filename reason segments — never to backup source database stems, report-document reasons or filenames, arbitrary uploaded filenames, recipe names, client names, or any unrelated domain value. `backend/app/services/report_documents.py` keeps its deliberately different contract and is not unified into it.
- Post-decision classification, added without rewriting the original diagnostic history in `docs/backend-baseline-failure-triage.md` §5, §6, and §9: Node 1 (backups filename reason) and Node 2 (exports filename reason) are both `PRODUCT DEFECT — CONTRACT MISMATCH`, severity `MEDIUM`, with a user-visible filename/reason-label mismatch, an ambiguous round trip for hyphenated reasons, a backend baseline failure, **no proven data loss**, no source database mutation, and no overwrite regression. Shared root cause: duplicated one-character-at-a-time sanitizers that both preserve the hyphen and both lack the decided run-collapse and numeric-disambiguation rules. The two nodes now share one decided contract and may be corrected in one bounded slice.
- `R4 — Canonical backup/export filename reason normalization` is authorized as that single bounded slice and is **NOT IMPLEMENTED**. It may begin only after this decision PR merges, and only from `origin/main`. Its exact Scope, Non-goals, Architecture constraints, Backend requirements, Frontend requirements, Tests, Smoke, and Acceptance criteria are recorded in `docs/implementation-plan.md`. Acceptance requires the complete backend suite from `backend/` with `0 failed` and `0 skipped`, both former baseline nodes passing, and no existing test deleted, renamed, skipped, `xfail`-ed, or weakened; the `496` collection count is deliberately not required to stay exact because `R4` adds tests.
- The `R4` frontend contract was strengthened. **No frontend production change is expected**, but focused **frontend test-only** changes are now allowed, because no runnable suite currently proves the canonical-reason display contract: `npm run test:local-artifacts-reports-feedback` runs and already compiles `src/local-artifact-presentation.ts` but asserts nothing about reason presentation, `frontend/test/local-artifact-presentation.test.mjs` is not runnable because no tsconfig emits to `dist-tests/local-artifact-presentation/` and no npm script invokes it, and the mapping functions themselves live in `frontend/src/main.ts`, which no focused test tsconfig includes. `R4` must either add reason-presentation assertions to the existing runnable feedback suite (preferred) or make the standalone suite runnable through an exact tsconfig and npm script without adding dependencies, and must prove verbatim rendering of an unmapped slug, the existing Russian mapping for a known system slug, that the frontend does not reconstruct/sanitize/normalize the slug, and that no frontend production behavior changes unless implementation evidence proves it necessary and the contract is updated first. The frontend production build and the final published-head browser smoke both remain required, and the smoke value `before_update_unsafe` must still display exactly as `before_update_unsafe`.
- **Documentation-only scope.** Exactly ten files changed: `README.md`, `docs/backup-and-restore.md`, `docs/export.md`, `docs/api.md`, `docs/implementation-plan.md`, `docs/backend-baseline-failure-triage.md`, `state/current-focus.md`, `state/progress.md`, `state/handoff.md`, `state/change-requests.md`. No backend code, frontend code, test, schema, migration, dependency, or lockfile changed. No shared helper was created, no filename generation or metadata parsing changed, and neither failing test was made to pass.
- **No tests and no smoke were executed for this decision PR.** No backend pytest, no frontend tests, no frontend build, no browser smoke, no API smoke, no packaging smoke, and no release smoke were run or claimed. The merged PR #144 backend result is carried strictly as `VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE` and is not relabelled as executed here. Applicable smoke level is Level 0 — docs smoke.
- The two backend failures remain open and no backend `0-failure` state is claimed. `CR-004` remains a separate `needs evidence` row and is not resolved, activated, or affected. In `state/change-requests.md` only the `CR-005` row changed, from `needs product decision` to `accepted`, with Target PR left empty and no future implementation PR number assigned; `CR-001` through `CR-004` are unchanged.
- C1, C2, C3, and C4 remain inactive. Packaging and release smoke remain blocked. **Product release readiness is not claimed.**
- PR publication state: the branch is pushed and a Ready-for-review pull request targeting `main` is opened immediately after this commit; GitHub assigns the number at creation time. The decision becomes durable implementation authority only after that PR is reviewed and merged.

## 2026-07-27 — PR #145 merged (CR-005 accepted); R4 canonical backup/export filename reason normalization implemented on branch

- **`CR-005` decision closed.** PR #145 `Decide CR-005 backup/export filename reason contract` is merged (VERIFIED FROM REPOSITORY / GITHUB): state `MERGED`, final reviewed head `7d68b45bee1f223b67f105c30e3acbb89dc8d41d`, merge commit `bef36822e50c245b72f813dad0afbffc7f772588`, merged at `2026-07-27T05:15:04Z`. Both the head and the merge commit were verified as ancestors of `origin/main`. `CR-005` remains **accepted** and its durable contract is unchanged.
- Branch: `claude/r4-canonical-artifact-reason-normalization`, created directly from clean `origin/main` `bef36822e50c245b72f813dad0afbffc7f772588`; merge-base with `origin/main` is the same commit. No rebase, no force-push, no history rewrite, no auto-merge. `state/change-requests.md` was not modified; `CR-001` through `CR-005` are unchanged.
- **Implementation summary.** One narrowly scoped shared helper, `normalize_artifact_reason_segment(value: str | None) -> str`, was added in `backend/app/services/local_artifact_filenames.py` and is now the single owner of the canonical filename reason segment for newly generated backups and exports. It preserves Unicode alphanumerics and letter case, treats the underscore and every other non-alphanumeric character as a separator, collapses each maximal separator run to one underscore, strips leading and trailing underscores, falls back to `manual`, and prefixes a digits-only result with `reason_`. Separator classification uses `str.isalnum()` character semantics deliberately, because a `\w`-style regular expression would preserve `_` and other Unicode connector characters. The same module holds `normalize_artifact_reason`, the human reason rule `(reason or "manual").strip() or "manual"`, to which `normalize_backup_reason` and `normalize_export_reason` now delegate, removing the duplicated sanitizers that were the shared root cause.
- Human reason and canonical slug stay distinct. The export JSON manifest continues to carry the normalized **human** reason and the export schema version is unchanged. The backup source database stem keeps its own separate sanitization and may still contain hyphens; that sanitizer was renamed to `_safe_source_stem_part` so it cannot be mistaken for the reason helper. `backend/app/services/report_documents.py` was not imported, reused, or changed.
- **No parser correction was required.** Because a canonical segment never contains a hyphen and is never digits-only, the existing `_parse_backup_reason` and `_parse_export_reason` already exclude the `-N` uniqueness suffix and already survive a hyphenated backup source stem. Both properties are now covered by tests rather than assumed.
- **No API or schema change.** `backend/app/api/` and `backend/app/schemas/` are untouched; no response shape changed and no field was added. **No migration** — no database migration and no filesystem migration. **No existing artifact was renamed, rewritten, or deleted.** Legacy listing stays best-effort and is covered by tests asserting that legacy files are listed with unchanged bytes.
- **Backend tests.** Executed from `backend/` with Python `3.12.13` and pytest `8.4.2` (rootdir `backend/`, configfile `pyproject.toml`) in a temporary virtual environment created outside the repository. Pre-change baseline reproduced exactly: `496 collected, 494 passed, 2 failed, 0 skipped`, the two failures being exactly the backups and exports filename-reason nodes; each node was re-run twice in isolation with identical deterministic output and no drift. Post-change complete suite: `562 collected, 562 passed, 0 failed, 0 skipped`.
- The two former baseline nodes now pass, each re-run twice in isolation:
  - `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters` — **PASSED**
  - `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters` — **PASSED**
- All 496 previously collected node IDs are still collected; the 66-test difference is added regression coverage only. No existing test was deleted, renamed, skipped, `xfail`-ed, or weakened. New coverage includes a table-driven helper matrix in `backend/app/tests/test_local_artifact_filenames.py` plus focused integration cases for backup and export create/list/status round-trip, uniqueness-suffix exclusion, a hyphenated backup source stem, export manifest human-reason preservation, non-overwrite behavior, source-database immutability, and legacy listing without rename, deletion, rewrite, or crash.
- **Frontend.** `cd frontend && npm run test:local-artifacts-reports-feedback` — `40 pass, 0 fail, 0 skipped` (`34` before the added cases; the pre-change run also passed). `cd frontend && npm run build` — succeeds. The focused suite was re-run after the build with the same result. **No frontend production file changed**; `frontend/src/` is untouched and no dependency, lockfile, or npm script changed. The frontend evidence is mixed by necessity and is labelled as such in the test file: the generic presentation layer is imported and invoked directly, proving an unmapped slug renders verbatim, while `backupReasonLabelRaw` / `exportReasonLabelRaw` live unexported in `frontend/src/main.ts` and are covered by **static source-contract assertions**, not runtime invocation.
- **Browser smoke was still pending at commit time.** The focused exact-published-head `/backups` and `/exports` smoke runs only after publication; a post-smoke commit would change the head and invalidate the evidence, so no repository file claims a passing smoke. Repository status is recorded as `IMPLEMENTED — EXACT-HEAD SMOKE REQUIRED BEFORE MERGE`.
- Changed files: `backend/app/services/local_artifact_filenames.py` (new), `backend/app/services/backup.py`, `backend/app/services/export.py`, `backend/app/tests/test_local_artifact_filenames.py` (new), `backend/app/tests/test_backups_api.py`, `backend/app/tests/test_exports_api.py`, `frontend/test/local-artifacts-reports-feedback.test.mjs`, `README.md`, `docs/backup-and-restore.md`, `docs/export.md`, `docs/api.md`, `docs/implementation-plan.md`, `docs/backend-baseline-failure-triage.md`, `state/current-focus.md`, `state/progress.md`, `state/handoff.md`.
- `CR-004` remains a separate `needs evidence` row and is not resolved, activated, or affected. Restore remains unimplemented. C1, C2, C3, and C4 remain inactive. Packaging and release smoke remain blocked. **Product release readiness is not claimed.**
- PR publication state: the branch is pushed and a **Draft** pull request targeting `main` is opened immediately after this commit; GitHub assigns the number at creation time. The PR stays Draft until the exact-published-head browser smoke passes, and it is not merged and has no auto-merge. `R4` is `IMPLEMENTED — EXACT-HEAD SMOKE REQUIRED BEFORE MERGE` and is **not DONE** until reviewed and merged.

## 2026-07-27 — PR #146 merged (R4 DONE); backend baseline correction gate closed; CR-006 export fallback recorded as needs evidence

- **`R4` closed.** PR #146 `R4 — Canonical backup/export filename reason normalization` is merged (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE): state `MERGED`, final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`, merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453`, merged at `2026-07-27T08:51:06Z`. `origin/main` equals that merge commit, and both the final head and the merge commit were verified as ancestors of `origin/main`. `R4` is **DONE**.
- **Backend baseline correction gate is DONE.** Both original filename nodes — `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters` and `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters` — are closed on `main`. With node 3 closed by `R2` and node 4 closed by `R3`, all four accepted gate failures are now closed. The merged `main` backend baseline is **green**.
- **Accepted merged evidence** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — **not** executed in this documentation task): backend complete suite `562 collected, 562 passed, 0 failed, 0 skipped`; frontend focused suite `40 passed, 0 failed, 0 skipped`; frontend production build `PASS`; focused exact-published-head `/backups` and `/exports` browser smoke `PASS — FULL AUTOMATED SMOKE PASSED`. Smoke provenance: the smoke ran against the exact published pull-request head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`, which is PR #146's final reviewed head, with no commit added afterwards; it used an isolated temporary SQLite database, an isolated temporary user-data directory, an isolated browser profile, no real user data, and all runner code and evidence kept outside the tested repository.
- The merged slice involved **no frontend production change**, **no database migration**, **no filesystem migration**, and **no existing artifact renamed, rewritten, or deleted**. `CR-005` remains **accepted** and is now **implemented**; its durable contract in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md` is unchanged. Neither `CR-005` nor `R4` is reopened.
- **No active runtime implementation slice.** This documentation task deliberately selects no successor slice and assigns no future PR number. The next gate must be separately selected and authorized.
- **`CR-006` added as `needs evidence`.** New row in `state/change-requests.md`: `CR-006 — Investigate export create-response fallback confirmation semantics`, status `needs evidence`, **Target PR empty**. Exact finding, from read-only inspection of `backend/app/api/exports.py::create_export` on `origin/main` at `127191feb182ccf68a4d7b9f2be28f6aa5b42453`: after `create_json_export` writes an export, the endpoint attempts to find the exact created file through `list_export_files`; when the exact file is found the response uses parsed filename metadata and returns the canonical filename-derived reason; when the exact file is **not** found, the defensive fallback constructs an `ExportFile` using `ExportResult.reason`, which is the normalized **human** reason preserved in the export manifest — so the fallback may return a human reason where the API contract normally expects the canonical filename-derived slug.
- `CR-006` is classified **`NEEDS EVIDENCE`** and explicitly **not** a confirmed product defect. No user-visible failure has been reproduced. No data loss, overwrite, incorrect file content, or unsafe mutation is proven. Fallback reachability is not established, **no severity is assigned**, and **no correction design is authorized**. The normal path is green in the merged backend suite, in create/list/status integration coverage, and in the exact-head browser smoke. `CR-006` is non-blocking for `R4` closure, is not an active implementation slice, is not part of `CR-004`, is not a reason to reopen `CR-005` or `R4`, and is **not** recorded as a fifth backend baseline failure. A future diagnostic must first establish reachability — artifact disappearance after write, a filesystem race, a permission or `stat` failure, a list/read failure, or mocked or injected repository/service behavior — and only then the desired contract: return a canonical reason, fail explicitly because the created artifact cannot be confirmed, or another documented outcome. Full record: `docs/backend-baseline-failure-triage.md` §17.
- **No runtime change in this PR.** This slice is documentation-only. `backend/app/api/exports.py`, `ExportResult`, `list_export_files`, the API schemas, and every other backend and frontend production file are unchanged; no test changed; no schema, migration, dependency, or lockfile changed. Changed files, exactly ten: `README.md`, `docs/api.md`, `docs/backend-baseline-failure-triage.md`, `docs/backup-and-restore.md`, `docs/export.md`, `docs/implementation-plan.md`, `state/change-requests.md`, `state/current-focus.md`, `state/handoff.md`, `state/progress.md`. `CR-001` through `CR-004` are unchanged; the `CR-005` row changed only in its lifecycle tail — ID, date, title, `accepted` status, the complete accepted normalization contract, all architectural boundaries, all legacy compatibility wording, and its empty Target PR are preserved, and the stale "`R4` may begin only after this decision PR merges / is not implemented yet / implementation PR number is not assigned" tail was replaced with the merged PR #146 lifecycle evidence. No `CLAUDE.md` or `.claude/` file was created or modified.
- **No runtime tests and no smoke were executed in this task**: no backend pytest, no frontend tests, no frontend build, no browser smoke, no API smoke, no packaging smoke, and no release smoke. Only documentation and repository-integrity checks were run. Every runtime result recorded here is merged PR #146 evidence.
- Branch: `claude/close-r4-record-export-fallback`, created directly from clean `origin/main` `127191feb182ccf68a4d7b9f2be28f6aa5b42453`; HEAD, `origin/main`, and the merge-base all equal that commit. No rebase, no force-push, no history rewrite, no auto-merge. Work was not done on `main` and not continued on the merged `R4` branch.
- **Durable `CR-005` contract documents corrected in this same slice.** `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md` had each carried a stale pre-merge `R4` implementation-status paragraph claiming `R4` was unmerged and that `main` still produced the older repeated-underscore output. Each of those three paragraphs was replaced with the accurate merged status: `CR-005` remains accepted, `R4` is merged and DONE at final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb` and merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453`, merged `main` now implements the canonical reason contract, accepted backend result `562 / 562 / 0 / 0`, exact-head `/backups` and `/exports` smoke passed, no response-shape change, no schema change, no database or filesystem migration, existing artifacts untouched, `CR-004` unresolved, Restore unimplemented, and product release readiness not claimed. The durable normalization algorithm and the UI/API/manifest contract in those three files are unchanged. No separate documentation slice is outstanding for them.
- `CR-004` remains a separate, unresolved `needs evidence` row and is not activated or affected. Restore remains unimplemented. Final macOS packaging and user-ready launch, installation verification, the packaged update flow and update smoke, and the full release-candidate smoke all remain open. C1, C2, C3, and C4 remain **inactive** unless separately authorized. **Product release readiness is not claimed.**
- PR publication state: the branch is pushed and one **Ready-for-review** pull request targeting `main` is opened after this commit. It is **not merged** and has **no auto-merge**.

## 2026-07-27 — CR-007 accepted: C1 workshop tax-rate setting contract decided; C1-I authorized after merge

- **Documentation-only product-decision slice.** No backend code, no frontend code, no test, no schema, no migration, no dependency, and no lockfile changed. No runtime tests, no frontend build, and no browser, API, packaging, or release smoke were executed or claimed in this task. Every runtime result referenced here is merged PR evidence.
- Branch: `claude/decide-c1-tax-setting-contract`, created directly from clean `origin/main` `09d11fc32db6ae57f99d522c4aa71e223e4e01a5`; HEAD, `origin/main`, and the merge-base all equal that commit. No rebase, no force-push, no history rewrite, no auto-merge. Work was not done on `main` and not continued on the merged `claude/close-r4-record-export-fallback` branch.
- Verified merged state before editing (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE): PR #147 `Close R4 lifecycle and record export fallback evidence request` is `MERGED`, final reviewed head `82cc4063c877c5a7060f2cd5f58f6f37386004f6`, merge commit `09d11fc32db6ae57f99d522c4aa71e223e4e01a5`, merged `2026-07-27T10:28:54Z`; both the head and the merge commit were verified as ancestors of `origin/main`. R3, R2, R4, and the backend baseline correction gate remain `DONE`; the merged backend baseline stays `562 collected / 562 passed / 0 failed / 0 skipped`; `CR-004` and `CR-006` remain inactive `needs evidence` rows.
- **`CR-007` is accepted.** New row in `state/change-requests.md`, status `accepted`, **Target PR empty**. The durable contract lives in `docs/settings.md` § “C1 — налоговая ставка для расчётов”, the API shape in `docs/api.md`, the snapshot semantics in `docs/domain-model.md` § 6.14, the report boundary in `docs/reports.md`, the ADR in `docs/decisions/0011-tax-rate-setting.md`, and the slice contract in `docs/implementation-plan.md` § 11.
- **Decision summary.** One global setting `default_tax_rate`, user-facing `Налоговая ставка для расчётов`, an internal planning estimate and never tax filing, a declaration, VAT accounting, legal advice, regime detection, or an accounting subsystem. Representation is a **percentage, not a coefficient** — `6` and `6.00` mean `6%`, `0.06` means `0.06%` — as `Decimal` decimal strings, never binary float, at most two fractional digits on input, range `0.00`–`100.00` inclusive, with excess precision such as `6.005` **rejected rather than rounded**. The **canonical persisted and API form is exactly two fractional digits** — `6` → `6.00`, `6.0` → `6.00`, `6.00` → `6.00`, `0` → `0.00`, `100` → `100.00` — applied after validation, never used to absorb precision, and the no-op comparison uses that exact canonical string. The taxable base is the order sale price: `tax_amount = ROUND_MONEY(sale_price_snapshot × tax_rate_percent_snapshot ÷ 100)` with money quantum `0.01` and `ROUND_HALF_UP`, rounding only the final amount; tax is deducted from gross revenue and never added on top of `sale_price`. Effectiveness is immediate through a backend-generated `effective_at` that describes the **currently active setting**, with no backdating, scheduling, multiple active periods, or user-configurable effective date: new on first configuration and on a real change, unchanged on a no-op, and **`null` after Clear**, with the clear time recorded by `AuditLog.created_at` and the clear metadata carrying `previous_effective_at` plus `new_effective_at: null`. The stored source `AppSetting.updated_at` stays persisted in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format; the service normalizes it and only the API exposes ISO-8601 UTC. A rate change never modifies completed `ProductionBatch` rows, report snapshots, prior audit records, generated documents, or persisted tax/margin values. Missing is `null` and never `0%` — non-blocking warning, tax and dependent margin unavailable, physical production not blocked, old rows shown as `Недоступно`, no fabricated zero — while a configured `0.00` is a real value. Explicit clear is `tax_rate_percent: null`, confirmed, warned about, audited, never retroactive, and implemented as **row deletion** of only the `default_tax_rate` row through a bounded new `delete_setting(key, connection=None)` capability, never touching the legacy `tax.default_rate` key; after a successful Clear the API returns `is_configured: false`, `tax_rate_percent: null`, `effective_at: null`, clearing an absent row is a no-op, and no nullable-column migration, sentinel value, empty-string storage, new settings table, or parallel store is authorized. Every real mutation writes `tax_rate_setting_changed` / `app_setting` / `default_tax_rate` **atomically** with the persistence change — upsert and delete alike — and rolls that change back if the audit write fails; reads, validation failures, failed persistence, and no-ops are not audited. The UI stays inside `/settings`.
- **C1/C2 boundary decided.** C1 owns the persisted rate, Decimal validation, the backend-generated effective timestamp, the GET/update API, explicit clear, the Settings UI, the atomic `AuditLog`, persistence and reload, no-op behavior, and human-readable help and errors. C2 owns readiness tax estimates, stale-setting detection between readiness and confirmation, `ProductionBatch` tax snapshots and their nullable migration, the tax amount, margin and margin percent, reports reading snapshots, old-record unavailable behavior, and backward-compatibility tests. C2 stays blocked until the C1 implementation is merged and verified, and must not be implemented inside the C1 slice.
- **`C1-I — Backend-owned tax-rate setting` is authorized but NOT implemented.** Status `AUTHORIZED AFTER THIS DECISION PR MERGES — NOT IMPLEMENTED`. It must not be started from this unmerged decision branch, and no implementation PR number is assigned. Full Scope, Non-goals, Architecture constraints, Backend requirements, Frontend requirements, Tests, Smoke, and Acceptance criteria: `docs/implementation-plan.md` § 11.
- **Recorded repository facts that materially shape `C1-I`**, all verified read-only against `origin/main` at `09d11fc32db6ae57f99d522c4aa71e223e4e01a5` and recorded in `docs/settings.md` § 14:
  - `backend/app/migrations/versions/0001_infrastructure.py` already seeds `app_settings` with `tax.default_rate = "0.06"`, `value_type` `decimal_string`, description `Default tax rate placeholder.`. Under the decided percentage contract `0.06` would mean `0.06%`. It is a **superseded pre-decision placeholder**: `C1-I` uses the distinct key `default_tax_rate` and must never read, reinterpret, migrate, rewrite, delete, or treat that row as a configured rate, and the two keys are never conflated. The `tax_rate default 0.06` line in the `AppSettings MVP fields` block of `docs/roadmap.md` and the coefficient formulas in `AGENTS.md` § 6.6, `docs/domain-model.md`, and `docs/architecture.md` § 8.6 were all **corrected in this same slice**, so no active coefficient formula or coefficient default for this setting remains anywhere in the repository documentation.
  - Atomic setting + audit is **not currently possible** through the existing repository API: `AuditLogRepository.create_log` accepts an optional `connection`, but `SettingsRepository.upsert_setting` opens its own `session(config)` and accepts none. The decided resolution is a **bounded optional-`connection` extension** of the existing settings repository methods, with **no schema change and no new settings architecture**; a new settings table, a parallel store, or a second persistence mechanism is not authorized, and if even the bounded extension proves insufficient the slice must stop, record evidence, and update the contract first.
  - `SettingsRepository` exposes only `list_settings`, `get_setting`, and `upsert_setting`, so the decided Clear-by-row-deletion contract needs one bounded new method equivalent to `delete_setting(key: str, connection=None)`, sharing the optional-`connection` pattern so the delete and its `AuditLog` insert run in one transaction. It is scoped to deleting a settings row by key and is not authorization for a schema change, a nullable column, a sentinel value, empty-string storage, a new table, or a parallel store.
  - `app_settings.updated_at` defaults to SQLite `CURRENT_TIMESTAMP` and **stays persisted** as `YYYY-MM-DD HH:MM:SS` in UTC without a `T` or offset; the service normalizes that stored value and only the API exposes ISO-8601 UTC `effective_at`. The database does not store ISO-8601, and the column, its default, and migrations are unchanged.
  - `upsert_setting` refreshes `updated_at` in its `ON CONFLICT DO UPDATE` branch, so the no-op contract requires a read-compare-then-write in the service.
  - `quantize_percentage` in `backend/app/domain/decimal_utils.py` quantizes with `ROUND_HALF_UP` and would silently turn `6.005` into `6.01`, so it must not be reused for tax-rate validation; use `parse_decimal` plus an explicit fractional-digit check.
  - No settings mutation is audited today — `WorkshopProfileSettingsService.update_profile` writes no `AuditLog` — so the tax setting will be the first audited settings mutation. This decision does **not** authorize retroactively adding audit to the workshop profile.
  - Readiness and confirmation already behave as the contract requires: `production_readiness._estimate_money` returns `estimated_tax = None` / `estimated_margin = None` with the `tax_rate_missing` warning, and `production_confirmation` creates batches with `sale_price` snapshotted and `tax`, `margin`, `margin_percent` set to `None`. C1 does not change either; C2 will.
  - `production_batches.sale_price`, `tax`, `margin`, and `margin_percent` are nullable `TEXT` in `0013_production_batches.py`, so the future C2 snapshot columns can follow the same nullable decimal-string pattern.
  - The Settings UI is inline in `frontend/src/main.ts` and no Settings frontend test module exists, so a focused `C1-I` frontend test requires extracting a tax-setting feedback/presentation module into the existing `*-feedback.ts` + `test/*.test.mjs` + `tsconfig.test.*.json` + npm-script pattern without adding dependencies.
- **Correction passes before merge.** A second commit on the same branch resolved four contract inconsistencies found in review and expanded the allowed documentation scope by two files. (1) `AGENTS.md` § 6.6 no longer carries the ambiguous coefficient rule `tax = sale_price * tax_rate`; it reads `tax = sale_price * tax_rate_percent / 100` and records the percentage range, `6.00` meaning `6%`, missing-is-unavailable-not-zero, no historical recalculation, snapshot use once C2 lands, and `docs/settings.md` as the durable contract. All unrelated `AGENTS.md` rules are preserved. (2) The active `docs/roadmap.md` `AppSettings MVP fields` entry now reads `default_tax_rate` with no default and an explicit `CR-007` note that the former `tax_rate default 0.06` line is superseded, is a percentage, and is `null` when unconfigured, with `C1-I` not implemented; unrelated roadmap history is untouched. The same coefficient statements inside the allowed `docs/domain-model.md` — the `AppSettings` field list, the `tax_rate default is 0.06` rule, and the § 8.4 cost formula — were corrected the same way. (3) Clear persistence is now explicitly **row deletion**. (4) `effective_at` no longer both exists and is `null` after Clear, and the storage wording no longer implies the database stores ISO-8601. (5) The canonical representation is now exact rather than "may use two decimals". A third commit closed the last documentation contradiction: `docs/architecture.md` § 8.6 now reads `tax = sale_price * tax_rate_percent / 100` with directly adjacent rules for the percentage range, `6.00` meaning `6%`, missing-is-unavailable-not-zero, an explicit `0.00` being a real value, Decimal-only calculation, rounding only the final amount to `0.01` with `ROUND_HALF_UP`, no recalculation of historical `ProductionBatch` rows, snapshot use once C2 lands, and pointers to `docs/settings.md` and `docs/domain-model.md`; unrelated architecture sections are untouched. **Every active tax formula in the repository documentation now uses `tax_rate_percent / 100`, and no coefficient default for this setting remains.** No accepted decision from the first commit was reversed in any pass.
- Changed files, exactly fourteen: `AGENTS.md`, `README.md`, `docs/api.md`, `docs/architecture.md`, `docs/decisions/0011-tax-rate-setting.md` (new), `docs/domain-model.md`, `docs/implementation-plan.md`, `docs/reports.md`, `docs/roadmap.md`, `docs/settings.md`, `state/change-requests.md`, `state/current-focus.md`, `state/handoff.md`, `state/progress.md`. `CR-001` through `CR-006` are unchanged; only the new `CR-007` row was added, and it appears once. No `CLAUDE.md` and no `.claude/` file was created or modified. No backend, frontend, test, schema, migration, dependency, or lockfile change in any commit.
- `CR-004` and `CR-006` remain separate, unresolved `needs evidence` rows and are not activated or affected. Restore remains unimplemented. Final macOS packaging and user-ready launch, installation verification, the packaged update flow and update smoke, and the full release-candidate smoke all remain open. C2, C3, and C4 remain **inactive**. **Product release readiness is not claimed.**
- PR publication state: the branch is pushed and one **Ready-for-review** pull request targeting `main` is opened after this commit. It is **not merged** and has **no auto-merge**.

## 2026-07-27 — C1-I implemented on branch: backend-owned tax-rate setting; exact-head /settings smoke required before merge

- **`C1-I — Backend-owned tax-rate setting` is IMPLEMENTED on its PR branch and NOT MERGED.** Status: `IMPLEMENTED — EXACT-HEAD /settings SMOKE REQUIRED BEFORE MERGE`. It is **not `DONE`**; it becomes `DONE` only after the smoke passes and the PR is reviewed and merged. **C2 remains blocked.** **Product release readiness is not claimed.**
- Branch `claude/c1-backend-owned-tax-rate-setting`, created from clean `origin/main` `80b83de3e838cf676669a1b627770300590c99c0`; HEAD, `origin/main`, and the merge-base all equalled that commit before any edit. No rebase, no amend of merged commits, no force-push, no history rewrite, no auto-merge. Work was not done on `main` and not continued on the merged decision branch.
- Verified before editing (VERIFIED FROM GITHUB): PR #148 `Decide the C1 workshop tax-rate setting contract` is `MERGED`, final reviewed head `577e0fd0b5c3e6fc82e2399fd17f023b6e221b83`, merge commit `80b83de3e838cf676669a1b627770300590c99c0`, merged at `2026-07-27T12:35:01Z`; both commits verified as ancestors of `origin/main`.
- **Baseline recorded before editing (EXECUTED):** backend `562 collected, 562 passed, 0 failed, 0 skipped`; `app/tests/test_settings.py` `10 passed`; frontend `npm run build` `PASS`. One documented deviation from the task specification: `git show origin/main:frontend/src/main.ts | wc -l` returns **`6406`**, not the specified `6407`, while `origin/main` is exactly the expected merge commit and both ancestry checks pass. The baseline is therefore not obsolete and the specification's number is off by one; the stricter verified ceiling `6406` was enforced.
- **Backend delivered.** `backend/app/domain/tax_rate.py` (percentage validation and canonical two-decimal formatting via `parse_decimal` plus an explicit shape and fractional-digit check — never `quantize_percentage`), `backend/app/schemas/tax_rate_settings.py`, `backend/app/services/tax_rate_settings.py`, `backend/app/api/tax_rate_settings.py`, and router registration in `backend/app/main.py`. `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate` live under the existing `/api/settings` namespace and persist the key `default_tax_rate` through the existing `app_settings` table.
- **Repository extension was bounded.** `backend/app/repositories/settings.py` gained an optional `connection` on `get_setting`/`upsert_setting`, an optional caller-owned `updated_at` on `upsert_setting`, and the new `delete_setting(key, connection=None)`. No schema change, no migration, no new table, no nullable column, no sentinel, no empty-string storage, no parallel settings store, and no generic SQL execution capability.
- **Contract behavior proven by tests.** Canonical two-decimal persistence and response (`6`/`6.0`/`6.00` → `6.00`, `0` → `0.00`, `100` → `100.00`); rejection of negatives, values above `100`, three or more fractional digits, scientific notation, empty strings, commas at the API boundary, malformed strings, JSON numbers, JSON integers, `bool`, `NaN`, and `Infinity`; `6.005` rejected and never persisted as `6.01`; a configured `0.00` treated as a real value and never as missing; the no-op contract writing nothing, preserving `effective_at`, and creating no `AuditLog`; exactly one atomic `tax_rate_setting_changed` / `app_setting` / `default_tax_rate` audit per real mutation; forced audit failure rolling back the first configuration, a change, and Clear alike, preserving the previous value, timestamp, and row presence with no partial audit row; Clear deleting only the `default_tax_rate` row and returning null fields; no-op Clear performing no delete and no audit; strictly increasing effective timestamps for rapid successive changes **without any `sleep()`**, through an injected clock; stored `updated_at` staying SQLite `YYYY-MM-DD HH:MM:SS` UTC text while the API exposes ISO-8601 UTC.
- **Legacy key isolation proven.** The seeded `tax.default_rate = "0.06"` placeholder is byte-for-byte unchanged after configure, change, and Clear, is never read as a configured rate, and is never passed to `delete_setting`.
- **Historical safety proven.** With one real production batch seeded through the supported API flow, a full configure → change → invalid → Clear sequence left every non-settings table count, every `ProductionBatch` row and financial field, every Order row, every stock movement, every packaging movement, and all five report payloads unchanged; the batch keeps `tax`, `margin`, and `margin_percent` as `NULL`, and readiness still returns `estimated_tax = null`.
- **Frontend delivered without growing the entry file.** New focused modules `settings-tax-contract.ts` (68), `settings-tax-feedback.ts` (212), `settings-tax-presentation.ts` (140), `settings-tax-bindings.ts` (33), `settings-tax-runtime.ts` (120), plus `settings-profile-presentation.ts` (42) extracted from the Settings route. **`frontend/src/main.ts`: 6406 before → 6399 after.** No tax-specific validation, normalization, response guard, mutation lifecycle, request ownership, stale-callback handling, state machine, presentation mapping, HTML template, field-error mapping, Clear-confirmation state, audit interpretation, or API error classification was added to `main.ts`; it received only imports, a route-composition call, small adapter callbacks over the existing generic `apiGet`/`apiSend`, and one runtime registration. No new production module exceeds 300 lines.
- **Settings Decision Matrix updated accurately.** `default_tax_rate` moved from `requires_backend_rules` to `editable_now`, keeping `affects_calculations: true`, `affects_historical_data: true`, `requires_backend_service: true`, and a safety note stating history is not recalculated. No other setting became editable. The Settings capability and status wording now say the workshop profile **and** the tax-rate setting are editable while the remaining calculation-sensitive settings stay closed.
- **Test evidence (EXECUTED IN THIS TASK):** backend complete suite `671 collected, 671 passed, 0 failed, 0 skipped`, with all **562** original merged node IDs still collected and none deleted, renamed, skipped, `xfail`-ed, or weakened; targeted `test_settings.py`, `test_settings_api.py`, `test_tax_rate_settings.py`, `test_tax_rate_settings_api.py` `123 passed`; frontend `npm run test:settings-tax-feedback` `34 pass, 0 fail, 0 skipped`; all 13 focused frontend suites `0 fail, 0 skipped`; `npm run build` `PASS`.
- Four existing Settings assertions were updated — not weakened — to the newly accurate editable set and capability wording: `test_settings_status_response_builds_local_first_status`, `test_settings_status_capabilities_are_navigation_only`, `test_settings_status_marks_only_workshop_profile_editable`, and `test_workshop_profile_api_get_put_and_status`. Their node IDs and exactness are preserved, and the last of them now asserts that `default_tax_rate` is the **only** newly editable calculation-sensitive setting.
- **Not implemented, by design:** readiness tax calculation, production-confirmation tax calculation, `ProductionBatch` tax snapshot columns, any migration, tax amount, margin, margin percent, report calculation changes, historical backfill or recalculation, tax-regime selection, УСН, ОСНО, НДС, insurance contributions, annual tax periods, minimum tax, deductions, marketplace tax accounting, accounting reports, invoices, tax filing, per-order/product/client overrides, multiple active rates, user-configurable effective dates, scheduled rates, C2, C3, C4, `CR-004`, `CR-006`, Restore, packaging, the update flow, and release smoke. No dependency was added and no lockfile changed.

## 2026-07-27 — C1-I closed as merged and verified; CR-008 accepted: C2 financial contract decided and divided into bounded slices

- **Documentation-only product-decision slice.** No backend code, no frontend code, no test, no schema, no migration, no dependency, and no lockfile changed. **No runtime tests, no frontend build, and no browser, API, migration, packaging, or release smoke were executed or claimed in this task.** Every runtime result referenced here is merged PR evidence, recorded as `VERIFIED FROM MERGED PR EVIDENCE` and never as executed here.
- Branch: `claude/close-c1-decide-c2-financial-contract`, created directly from clean `origin/main` `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`; HEAD, `origin/main`, and the merge-base all equalled that commit before any edit. No rebase, no amend of merged commits, no force-push, no history rewrite, no merge of another branch, no auto-merge. Work was not done on `main` and was not continued on the merged `claude/c1-backend-owned-tax-rate-setting` branch.
- **C1-I closure verified before editing (VERIFIED FROM REPOSITORY / GITHUB).** PR #149 `C1-I — Implement backend-owned tax-rate setting` is `MERGED`, final reviewed head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`, merged `2026-07-27T19:44:53Z`, base `main`, not a draft; both the head and the merge commit were verified as ancestors of `origin/main`. The decision PR #148 final reviewed head was `577e0fd0b5c3e6fc82e2399fd17f023b6e221b83` and its merge commit `80b83de3e838cf676669a1b627770300590c99c0`.
- **`C1-I` is `DONE — MERGED AND EXACT-HEAD VERIFIED`.** Accepted merged evidence: backend complete suite `671 collected / 671 passed / 0 failed / 0 skipped`, with all 562 original merged baseline node IDs still collected; focused tax-setting frontend suite `52 passed / 0 failed / 0 skipped`; all 13 focused frontend suites `568 passed / 0 failed / 0 skipped`; frontend production build `PASS`; exact-head `/settings` browser smoke `PASS — 146 checks / 0 failures` against the exact smoke-tested head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`; `frontend/src/main.ts` `6406` before → `6399` after; **no migration was added**; `C1-I` implemented only the tax-rate setting and no C2 calculation.
- **Stale pre-merge current-state claims removed.** Every active statement that `C1-I` was unmerged, still required the exact-head `/settings` smoke, was not `DONE`, or that C2 was blocked because C1-I was unmerged, was corrected in `README.md`, `docs/api.md`, `docs/settings.md`, `docs/roadmap.md`, `docs/implementation-plan.md`, `docs/decisions/0011-tax-rate-setting.md`, and `state/current-focus.md`. Explicitly historical pre-merge records were **preserved as historical**: the pre-merge `C1-I` subsection in `docs/implementation-plan.md` § 11 is now introduced by a `HISTORICAL PRE-MERGE RECORD — SUPERSEDED` note pointing at the new closure table, the Block B closure baseline in § 3 is preserved under an explicit `HISTORICAL RECORD` heading, and every earlier dated `state/progress.md` and `state/handoff.md` entry is unchanged byte-for-byte.
- **Second commit — `Resolve C2 documentation contradictions`.** The first commit established the C2 contract; review found five remaining active contradictions plus one incomplete lifecycle, and the second commit closed all of them on the same branch without amending, rebasing, or force-pushing.
  1. **ADR 0011 corrected directly.** `docs/decisions/0011-tax-rate-setting.md` joined the allowlist as the fifteenth file. Its status section now reads `Accepted — 2026-07-27. Recorded as CR-007. Implemented by C1-I and merged as PR #149.` with `C1-I` status `DONE — MERGED AND EXACT-HEAD VERIFIED` and a table carrying final reviewed head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`, merged `2026-07-27T19:44:53Z`, and exact-head `/settings` smoke `PASS — 146 checks / 0 failures`. The accepted `CR-007` product meaning — percentage representation, validation, canonical two-decimal storage, effective-time meaning, Clear semantics, atomic audit, missing-versus-zero, and the C1/C2 ownership boundary — is unchanged and not reopened; only the satisfied C2 gating condition is annotated. ADR 0012's superseding note was replaced with a short lifecycle relationship note, because there is no longer a stale ADR 0011 status to supersede.
  2. **API Settings status corrected.** `docs/api.md` no longer says `PR96 marks only workshop profile fields as editable_now; calculation-sensitive settings remain closed`. It now records that the Workshop profile fields **and** `default_tax_rate` are `editable_now`, that `default_tax_rate` is the only currently editable calculation-sensitive setting, and that every other calculation-sensitive setting stays `requires_backend_rules`. The PR96 wording is retained only as an explicitly labelled historical note.
  3. **API readiness limitation corrected.** `docs/api.md` no longer says `estimated_tax` and `estimated_margin` stay null "until explicit tax settings exist". The explicit setting already exists; readiness simply does not read it yet. A three-row table now separates the implemented C1 setting, the authorized-but-unimplemented `C2-I` calculations, and the planned-and-blocked `C2-II` snapshots. The confirmation-endpoint note was corrected the same way.
  4. **Implementation-plan current baseline corrected.** § 3 no longer presents the PR #141 merge commit `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` as the current baseline. The current baseline is now recorded as `ff7afe6b0778ab2b348229a4df34acf3e3fc0001` — the PR #149 merge commit, the `C1-I` merged baseline, and the verified current `origin/main` at the start of PR #150 — with the merged backend baseline `671 / 671 / 0 / 0`. The PR #141 values are preserved beneath an explicit `HISTORICAL RECORD — Block B closure baseline` heading.
  5. **Implementation-plan active state and obligations corrected.** § 3 now states that no runtime implementation is active in this documentation PR, that `C2-I` becomes the only authorized runtime slice after PR #150 merges, that `C2-II` and `C2-III` remain blocked, and that `C2-I` must not start from the unmerged PR #150 branch — replacing the claim that no slice had been selected. In § 7 the single ambiguous `Налоговая настройка | Calculation-sensitive Settings пока закрыты` row was split in meaning: the tax-rate setting row is **closed** (implemented and editable, C1 complete, the only editable calculation-sensitive setting, others still closed), and the cost/tax/margin row remains **open** as C2 work that the C1 setting does not close.
- **Invalid persisted tax-rate lifecycle completed (DECIDED IN THIS TASK).** The first commit left a gap: readiness treated an invalid persisted rate as financially unavailable and non-blocking, but confirmation allowed `null/null` only for a genuinely missing setting, so an invalid rate would have made the confirmation context impossible to construct and would have indirectly blocked physical production. The completed contract defines **`no valid configured tax-rate context`** as either a missing `default_tax_rate` row or a persisted value that is invalid under the C1 rules. The two states stay distinguishable through readiness warnings — `tax_rate_missing` and `tax_rate_invalid`, and the invalid case must **not** also emit `tax_rate_missing` — but both return `tax_rate_percent = null` and `tax_rate_effective_at = null`, both give `financial_estimate_status = unavailable` with null tax, margin, and margin percent, both avoid an unhandled HTTP 500, and **neither blocks physical production**. Both map to the single `null/null` confirmation context. The stale matrix is: valid → changed valid, valid → missing, valid → invalid, missing → valid, and invalid → valid are `409 tax_rate_context_stale`; **missing ↔ invalid is not**, because both produce the same financial result. An accepted no-valid-rate confirmation persists `tax_rate_percent_snapshot = null`, `tax_rate_effective_at_snapshot = null`, `tax = null`, `margin = null`, `margin_percent = null` while every physical production snapshot is written normally, and confirmation never repairs, clears, rewrites, or audits the invalid setting and never persists the raw invalid value. No third request field and no generic financial-context token was introduced. The invariant `An absent or invalid tax-rate setting may make financial values unavailable, but it must not by itself block physical production` is now stated in ADR 0012, `docs/api.md`, `docs/domain-model.md`, `docs/implementation-plan.md`, `docs/architecture.md`, and `AGENTS.md`.
- **Exact timestamp contract decided (DECIDED IN THIS TASK).** Database persistence — `AppSetting.updated_at` and the future `tax_rate_effective_at_snapshot` — is exactly `YYYY-MM-DD HH:MM:SS`: UTC, second precision, SQLite text, no `T`, no `Z`, no offset. The API and confirmation-context representation is exactly `YYYY-MM-DDTHH:MM:SSZ`: UTC, second precision, literal `T`, literal `Z`. Local-time values, arbitrary offsets such as `+03:00`, fractional seconds, a space instead of `T`, a missing `Z`, and user-generated timestamps are not accepted; `expected_tax_rate_effective_at` must be `null` or the exact canonical timestamp previously returned by readiness, and anything else is `422 invalid_tax_rate_context`. The confirmation and `ProductionBatch` detail responses normalize the stored snapshot and never expose the raw SQLite form. No backfill is authorized.
- **21 additional future `C2-II` test requirements recorded** in `docs/implementation-plan.md` § 11 for the invalid-rate lifecycle and the timestamp contract, covering `null/null` acceptance for both missing and invalid states, the distinct `tax_rate_invalid` warning without a duplicate `tax_rate_missing`, every stale and non-stale transition, null snapshot persistence with completed physical production, the raw invalid value never reaching `ProductionBatch`, no setting repair or audit, and canonical / offset / fractional-second / missing-`Z` timestamp handling in both storage and API form. They are `NOT IMPLEMENTED` and `NOT EXECUTED` in PR #150.
- **Repository evidence verified read-only before writing the decision**, all against merged `main` `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`, and all thirteen expected facts matched: `C1-I` exists on merged `main`; `default_tax_rate` is the authoritative key (`backend/app/services/tax_rate_settings.py::DEFAULT_TAX_RATE_KEY`); `tax.default_rate = "0.06"` remains a superseded legacy placeholder seeded by `0001_infrastructure.py`; `ProductionBatch` already has nullable `sale_price`, `total_cost`, `tax`, `margin`, `margin_percent`; it has **no** `tax_rate_percent_snapshot` and **no** `tax_rate_effective_at_snapshot`; production confirmation creates the batch with the authoritative locked-order sale price, real component/packaging/other/total cost, and explicit `tax=None, margin=None, margin_percent=None`; readiness already exposes `estimated_cost`, `estimated_tax`, `estimated_margin`; `_estimate_money` computes cost when inputs allow, leaves tax and margin unavailable, computes no margin percent, and exposes no tax-rate context; the warning codes `cost_data_missing`, `sale_price_missing`, and `tax_rate_missing` exist; `ProductionConfirmRequest` contains exactly `confirm` and `notes`; reports use no snapshots; no migration implements C2; and `frontend/src/main.ts` is exactly `6399` lines. The repository-path correction was confirmed: there is **no** `backend/app/schemas/production_confirmation.py`, and the confirmation request and batch response schemas live in `backend/app/schemas/production_batches.py`. Also confirmed for the `C2-II` contract: `TaxRateSettingsService.get_tax_rate()` currently takes no connection argument, while `SettingsRepository.get_setting(key, connection=None)` already accepts one.
- **`CR-008` is accepted.** One new row in `state/change-requests.md`, status `accepted`, **`Target PR` empty**, appearing exactly once. `CR-001` through `CR-006` are byte-identical; `CR-007` keeps its accepted product contract untouched and only its lifecycle tail was updated to record `C1-I` implemented, PR #149 merged, and `C1-I` `DONE`. `CR-004` and `CR-006` were not reactivated or modified.
- **Accepted C2 product meaning.** C2 is an internal operational estimate for the workshop and is never tax filing, a declaration, VAT accounting, automatic regime selection, УСН/ОСНО/НПД/ПСН/АУСН/ЕСХН calculation, insurance contributions, minimum tax, annual or quarterly tax accounting, marketplace tax accounting, invoicing, bookkeeping, or legal or tax advice; nothing is renamed to a tax reserve. The simplified percentage-of-sale model remains the accepted MVP model and may be replaced only by a separately decided future tax-regime model, after which existing historical snapshots must remain immutable. All authoritative inputs are backend-owned — the authoritative Order sale price, the existing readiness cost estimate, the actual confirmation total cost, the current `default_tax_rate` state, and the current backend `effective_at` — and the frontend calculates no total cost, tax, margin, or margin percent, passing back only the latest backend-returned tax-rate context unchanged.
- **Formulas, `Decimal` only and never binary float:** `tax_amount = ROUND_MONEY(sale_price × tax_rate_percent / 100)`; `margin = ROUND_MONEY(sale_price − total_cost − tax_amount)`; `margin_percent = ROUND_PERCENT(margin / sale_price × 100)`. The percentage is always divided by `100` (`6.00` means `6%`), money and percentage quanta are both `0.01` with `ROUND_HALF_UP`, only the final amount of each formula is rounded, and tax is deducted from gross revenue rather than added on top.
- **Missing, zero, and negative behavior.** Configured `0.00` produces tax `0.00` and is never shown as unconfigured; a missing rate or missing sale price produces `null` and never a fabricated zero; margin is `null` when sale price, total cost, or tax is unavailable; margin percent requires an available margin **and** a sale price greater than zero, so a zero sale price gives `partial` with margin percent `null`; negative margin and negative margin percent are valid and are **never clamped**; an invalid persisted rate is handled defensively — no calculation, no coercion, not treated as zero, raw value never exposed, estimate unavailable, non-blocking warning, no unhandled HTTP 500, and physical production not blocked.
- **Warning semantics.** Financial warnings are **non-blocking** and reuse the existing readiness mechanism and the exact existing `ProductionReadinessIssue` structure. `tax_rate_missing`, `sale_price_missing`, and `cost_data_missing` are preserved and never renamed; only `margin_percent_unavailable_zero_sale_price` and `tax_rate_invalid` are added; aliases such as `tax_rate_unconfigured`, `sale_price_unavailable`, and `total_cost_unavailable` are not introduced; and no two warnings are emitted for one semantic condition. `can_produce` stays governed only by recipe and formula readiness, stock, lots, packaging, order lifecycle, and existing physical-production safety rules.
- **Readiness API mapping.** The existing `POST /api/orders/{order_id}/check-production-readiness` is extended additively, with no parallel financial-readiness endpoint and no field removed or renamed. `estimated_cost`, `estimated_tax`, and `estimated_margin` are **reused** — the latter two activated, not duplicated. Only `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, and `financial_estimate_status` (`available` / `partial` / `unavailable`) are added. **`estimated_total_cost` is not authorized** and no duplicate alias is authorized.
- **`C2-I — Backend financial readiness estimate` is AUTHORIZED AFTER THIS PR MERGES and is NOT IMPLEMENTED.** It is the only runtime slice this decision authorizes. It must not be started from this unmerged documentation branch, and no implementation PR number is assigned. It has no migration, no persistence write, no `AuditLog`, no Order / `ProductionBatch` / movement / report change, and **no frontend production change**: `frontend/src/main.ts` must stay at exactly `6399` lines, with focused frontend test-only changes allowed only to prove the existing DTO guard safely ignores additive fields. Preferred module `backend/app/domain/production_financials.py`, never inside the API router, `main.py`, a generic `utils.py`/`helpers.py`, or an all-purpose finance manager. 34 required test cases and an exact-head readiness API smoke are specified in `docs/implementation-plan.md` § 11.
- **`C2-II — Transactional production financial snapshots` is PLANNED — BLOCKED** on merged and verified `C2-I`. Its recorded contract: one nullable migration adding only `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot`, with no backfill and a backup before applying; reuse of the existing `sale_price`, `total_cost`, `tax`, `margin`, `margin_percent` fields with no duplicate monetary snapshot fields; a bounded read-only `connection`-aware extension of `TaxRateSettingsService.get_tax_rate` so the setting is read inside the production transaction, never through a second independent connection and never by parsing raw `AppSetting` values in the confirmation service; **required-but-nullable** `expected_tax_rate_percent` and `expected_tax_rate_effective_at` declared without defaults, where **omission is not equivalent to explicit `null/null`** — omitted keys are HTTP 422 `tax_rate_context_required`, while a partial-null, malformed, non-canonical, out-of-range, or bad-timestamp context is HTTP 422 `invalid_tax_rate_context`; a changed, cleared, or newly configured rate is HTTP 409 `tax_rate_context_stale` with a safe Russian message and **no write at all**; a thirteen-step transactional confirmation whose failure rolls back every snapshot and production write; honest persistence of missing inputs; and exposure of the two rate snapshots **only** in the confirmation response and `ProductionBatch` detail, not in the batch list or reports.
- **`C2-III — Financial presentation and snapshot-backed reports` is PLANNED — BLOCKED** on merged and verified `C2-II`, and is explicitly a **planning umbrella, not authorization for one large implementation PR**. Before it is authorized, repository evidence must determine whether it can remain one bounded vertical slice; if it contains more than one independently reviewable user-facing vertical slice it must be subdivided — for example readiness and `ProductionBatch` financial presentation, and separately snapshot-backed reports. Reports read persisted snapshots only, never recalculate history with the current rate, and show old rows as unavailable rather than `0.00`.
- **God-file ceiling for all of C2:** `frontend/src/main.ts` baseline `6399` and final at most `6399` lines, no calculation logic, financial HTML template, DTO guard, or lifecycle/stale-context state machine in `main.ts`, no minification or artificial line joining, each new production module normally at most 300 lines and each new function normally at most 60 lines, and no generic `utils`/`helpers`/`manager`/`common` dumping ground.
- **New ADR.** `docs/decisions/0012-c2-financial-calculation-snapshots.md`, Status `Accepted`, Date `2026-07-27`, covering context, decision, product boundary, formula contract, missing-value matrix, rounding rules, existing readiness API mapping, preserved warning-code semantics, readiness financial status semantics, the physical-production non-blocking rule, the C2-I/C2-II/C2-III split, the C2-III umbrella and subdivision rule, the required-but-nullable confirmation context, confirmation validation rules, the transaction-aware tax-setting read boundary, the stale tax-context rule, the snapshot and migration rule, the C2-II API exposure boundary, historical immutability, the report snapshot-only rule, the frontend ownership boundary, god-file constraints, consequences, non-goals, and the explicit statement that the simplified tax model may be replaced later while existing snapshots stay immutable. It also records that the stable stale-conflict code is `tax_rate_context_stale`, superseding the illustrative `financial_settings_changed` name used while `CR-007` was being decided, and — after the second commit — the `no valid configured tax-rate context` definition, the full stale matrix including the non-conflicting missing ↔ invalid transitions, and the exact storage and API timestamp formats.
- Changed files, exactly fifteen: `AGENTS.md`, `README.md`, `docs/api.md`, `docs/architecture.md`, `docs/decisions/0011-tax-rate-setting.md`, `docs/decisions/0012-c2-financial-calculation-snapshots.md` (new), `docs/domain-model.md`, `docs/implementation-plan.md`, `docs/reports.md`, `docs/roadmap.md`, `docs/settings.md`, `state/change-requests.md`, `state/current-focus.md`, `state/handoff.md`, `state/progress.md`. `docs/decisions/0011-tax-rate-setting.md` was added to the allowlist by the second commit so its stale status could be corrected directly instead of being labelled historical. No `CLAUDE.md` and no `.claude/` file was created or modified. No backend, frontend, test, schema, migration, runtime schema, dependency, lockfile, package-script, launcher, generated-artifact, or smoke-runner change in either commit.
- Checks executed: `Level 0 — documentation smoke` only — `git status --short --untracked-files=all`, `git diff --check`, `git diff --stat`, `git diff --name-only`, `git diff origin/main...HEAD --check`, `git diff origin/main...HEAD --stat`, `git diff origin/main...HEAD --name-only`, `git diff --cached --check`, `git diff --cached --name-only`, changed-file allowlist verification, documentation existence and reference checks, active stale-status searches, invalid-rate consistency searches, timestamp-format consistency searches, contradiction greps, and a documentation-appropriate secret scan. **Not executed:** `pytest`, backend targeted tests, frontend focused tests, `npm run build`, browser smoke, API smoke, migration smoke, packaging smoke, and release smoke.
- `CR-004` and `CR-006` remain separate, unresolved `needs evidence` rows and are not activated or affected. Restore remains unimplemented. Final macOS packaging and user-ready launch, installation verification, the packaged update flow and update smoke, and the full release-candidate smoke all remain open. C3 and C4 remain **inactive**. **Product release readiness is not claimed.**
- PR publication state: PR #150 is open on branch `claude/close-c1-decide-c2-financial-contract`, **Ready for review**, targeting `main`, with two commits — `9b12a3dc8e432e5c6b9063e00e6533645fac4737` `Close C1-I and decide C2 financial contract` and the correction commit `Resolve C2 documentation contradictions`. It is **not merged** and has **no auto-merge**. No second pull request and no replacement branch was created, no commit was amended, no rebase or force-push happened, and no second correction-only entry was appended to this file.

## 2026-07-28 — C2-I implemented on an unmerged PR branch

> **HISTORICAL PRE-MERGE RECORD — SUPERSEDED.** `C2-I` merged as PR #151 and is `DONE — MERGED AND EXACT-HEAD VERIFIED`. **C2 is `COMPLETED`.**

- **Status: `IMPLEMENTED ON PR BRANCH — NOT MERGED`.** Not `DONE`. Branch `codex/c2-i-backend-financial-readiness-estimate`, started from merged `origin/main` `4c03142ef7acdc31fcb15730484e8e52dde95b69` (the PR #150 merge commit, final reviewed head `b2857b114542688b6a52c7fb1208d8db6b4ed2ae`) with a clean working tree. No open PR already implemented `C2-I`. No history was reset, rewritten, amended, rebased, or force-pushed.
- **One pure domain module.** `backend/app/domain/production_financials.py` owns the whole calculation: `TaxRateContext` (valid / missing / invalid, never carrying raw text), `ProductionFinancialInputs`, the frozen `ProductionFinancialEstimate`, the bounded `FinancialEstimateStatus`, and `FinancialWarningCode`. It opens no database connection, reads no repository, imports neither FastAPI nor Pydantic, constructs no `ProductionReadinessIssue`, and writes nothing. No generic finance service, calculator manager, or helper dump was created.
- **Formulas exactly as decided.** `Decimal` only, no binary float at any step, reusing the existing `quantize_money` and `quantize_percentage` (`0.01`, `ROUND_HALF_UP`) rather than creating a second rounding policy. Only the final result of each formula is rounded; tax uses the gross sale price as the taxable base and is deducted from revenue; configured `0.00` yields tax `0.00`; negative margin and negative margin percent are returned unclamped; no missing value becomes a fabricated zero.
- **Service integration.** `ProductionReadinessService._estimate_money` was replaced by `_estimate_financials` plus `_tax_rate_context`, so calculation semantics were extracted rather than grown into a larger conditional block. `ProductionReadinessService` gained no other responsibility.
- **Tax-rate read boundary.** The rate is read only through the existing no-argument C1 `TaxRateSettingsService.get_tax_rate()`. The transaction-aware `connection=` extension was **not** added — that stays `C2-II`. `app_settings` is never read directly from the readiness service, and the legacy `tax.default_rate` row is never read or interpreted; only `default_tax_rate` is used.
- **Invalid persisted value.** The C1 Settings repair surface may still return the stored text for an externally corrupted row, so `is_configured` alone is not treated as financially authoritative. The returned percentage is re-validated through the existing C1 `parse_tax_rate_percent`; anything that fails to re-parse — and any row with no effective timestamp — becomes the C2 no-valid-rate context: `tax_rate_percent = null`, `tax_rate_effective_at = null`, warning `tax_rate_invalid`, status `unavailable`. The raw text is never returned through readiness, never calculated with, never treated as `0.00`, and never turned into an unhandled HTTP `500`. `GET`/`PUT /api/settings/tax-rate` behavior is unchanged.
- **Response contract.** The existing `estimated_cost`, `estimated_tax`, and `estimated_margin` are reused, with the latter two activated. Exactly five fields were added: `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, `financial_estimate_status`. `estimated_total_cost` is absent, no field was renamed, removed, or duplicated, and the extension is backward-compatible.
- **Warnings.** `tax_rate_missing`, `sale_price_missing`, and `cost_data_missing` are preserved unchanged in name and meaning; only `margin_percent_unavailable_zero_sale_price` and `tax_rate_invalid` were added; no alias such as `tax_rate_unconfigured`, `sale_price_unavailable`, or `total_cost_unavailable` exists. Each semantic warning is emitted at most once, an invalid rate emits `tax_rate_invalid` and never also `tax_rate_missing`, different missing inputs warn together, and every financial warning is non-blocking. `can_produce` still depends only on recipe/formula readiness, lots and stock, packaging, order lifecycle, and the existing physical safety rules.
- **Read-only.** No migration, no schema or table change, no snapshot column, no backfill, no persistence write, no `AuditLog`, no automatic production confirmation, and no stock or packaging reservation. Read-only safety was proved for representative ready, blocked, and warning results, including repeated calls and an invalid persisted rate that readiness deliberately does not repair.
- **Frontend.** No production behavior, no readiness financial card, no frontend arithmetic, and no hidden or temporary UI. `frontend/src/main.ts` is unchanged at exactly `6399` lines and no frontend production source file was touched. The single frontend change is test-only: one added case proving the existing `productionReadinessDtoIsValid` guard tolerates the five additive fields while still rejecting malformed existing fields — no existing guard was weakened.
- **Tests.** Focused pure-domain suite `backend/app/tests/test_production_financials.py` (35 tests) plus extended integration coverage in `backend/app/tests/test_production_readiness.py`. Backend baseline on `origin/main` verified as `671 collected / 671 passed / 0 failed / 0 skipped`; after this slice `737 passed / 0 failed / 0 skipped`. All `671` baseline node IDs remain collected. No test was deleted, skipped, or `xfail`-ed.
- **One existing test's assertions were necessarily updated.** `test_readiness_tax_estimate_remains_c2_work` asserted that readiness returns `estimated_tax = null` with a configured rate — that is precisely the pre-`C2-I` state this authorized slice removes. Its node ID and name are unchanged, and its body now asserts the delivered `C2-I` behavior **and** the still-unimplemented `C2-II` half (production batches keep null `tax`, `margin`, and `margin_percent`), so the test is strengthened rather than weakened.
- **Frontend checks.** `test:order-mutation-lifecycle` `33 passed`, `test:order-readiness-presentation` `15 passed`, `test:order-production-feedback` `21 passed`, `test:settings-tax-feedback` `52 passed`, and `npm run build` `PASS`.
- **Non-goals honored.** No `C2-II`, no confirmation tax context, no `tax_rate_context_stale`, no transaction-aware `get_tax_rate(connection=...)`, no `ProductionBatch` snapshot columns, no migration or backup-before-migration flow, no production-confirmation tax or margin, no report calculation or report UI, no `ProductionBatch` list/detail change, no Russian tax regimes, no VAT, no accounting, no tax filing, no historical recalculation, no per-order or per-product overrides, no multiple rates, no `C3`, no `C4`, no Restore, no packaging work, and no release-candidate smoke. No dependency and no lockfile changed.
- `C2-II` and `C2-III` remain `PLANNED — BLOCKED`, and no implementation PR number is assigned to either. `CR-004` and `CR-006` are untouched, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## 2026-07-28 — C2-I merged; C2-II implemented on an unmerged PR branch

> **HISTORICAL PRE-MERGE RECORD — SUPERSEDED.** `C2-II` merged as PR #152 and is `DONE — MERGED AND EXACT-HEAD VERIFIED`. **C2 is `COMPLETED`.**

- **`C2-I` is `DONE — MERGED AND EXACT-HEAD VERIFIED`.** PR #151, final reviewed head `6f72bffc9a0d17839e3a74c69366fe17df8a318b`, merge commit `7b3dde8278f59658bfa3a81c09e643ea10319551`, merged `2026-07-28T04:22:13Z`, exact-head readiness API smoke `PASS — 113 checks / 0 failures`. Both the head and the merge commit are ancestors of `origin/main`. The earlier dated entry recording it as unmerged is preserved above as history.
- **`C2-II` status: `IMPLEMENTED ON PR BRANCH — NOT MERGED`.** Not `DONE`. Branch `codex/c2-ii-transactional-production-financial-snapshots`, started from clean merged `origin/main` `7b3dde8278f59658bfa3a81c09e643ea10319551` with a clean working tree. No open PR already implemented `C2-II`. No history was reset, rewritten, amended, rebased, or force-pushed.
- **Migration.** `0019_production_batch_tax_rate_snapshots` adds only the two nullable `TEXT` columns `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` to `production_batches`, additively via `ALTER TABLE ... ADD COLUMN`, with no default, no backfill, no table rebuild, and no new table. It is idempotent, and it is registered last in the existing `MIGRATION_MODULES` ordering.
- **Backup before migration.** The existing user-mode startup flow is preserved and proven: a database at the `0018` level reports exactly one pending migration, user-mode startup writes a `before_migration` backup first, the backup holds the pre-migration schema and data, and the live database then receives the two columns with every existing value intact. A fresh database creates no pointless backup, and a fully migrated one creates none on the next start.
- **Migration-failure evidence, recorded honestly.** Python's `sqlite3` runs DDL outside the implicit transaction, so an `ALTER TABLE ADD COLUMN` that already executed survives a mid-migration failure while the `schema_migrations` insert rolls back. That is why `0019` is idempotent: a failed run loses no user value, leaves the backup in place, and the next startup completes the migration exactly once.
- **Transaction-aware read.** `TaxRateSettingsService.get_tax_rate(connection=None)` — the no-argument behavior is unchanged, and a supplied connection reads `default_tax_rate` through the existing `SettingsRepository` on that exact connection, performing no write and creating no `AuditLog`. No second tax-setting service, no raw `AppSetting` parsing in the confirmation service, and no generic transaction service locator.
- **One shared reducer.** `backend/app/services/tax_rate_context.py` is used by both readiness and confirmation, so the missing/invalid parsing exists once. `TaxRateContext` gained `__post_init__` guards rejecting impossible state combinations, plus `comparable_pair` for the stale check.
- **One timestamp boundary.** `backend/app/domain/tax_rate_timestamps.py` owns every conversion between the `YYYY-MM-DD HH:MM:SS` storage form and the `YYYY-MM-DDTHH:MM:SSZ` API form; `tax_rate_settings.py` now delegates to it rather than keeping private copies.
- **Request contract.** `expected_tax_rate_percent` and `expected_tax_rate_effective_at` are required and declared without defaults. Omission returns `422 tax_rate_context_required` through a narrowly scoped `RequestValidationError` handler that leaves every other endpoint's validation response byte-identical; a partial-null, non-string, malformed, non-canonical, or out-of-range value returns `422 invalid_tax_rate_context` from `backend/app/domain/production_tax_context.py`. Validation runs before the service is called, so a rejected request writes nothing.
- **Stale matrix.** Implemented exactly as accepted, inside the existing `BEGIN IMMEDIATE` transaction and before the first production write, returning `409 tax_rate_context_stale` with the safe Russian guidance. Missing → invalid and invalid → missing are deliberately not conflicts. A conflict writes nothing and never repairs, clears, rewrites, or audits the invalid setting.
- **Snapshots.** The arithmetic reuses the merged `C2-I` pure domain calculation; no formula is duplicated in `ProductionConfirmationService`. Inputs are the locked authoritative Order sale price and the actual transactional production cost. Configured `0.00` persists as a real snapshot; a missing or invalid rate persists five nulls without blocking physical production; a missing sale price keeps the rate snapshots; a missing total cost still persists tax; zero sale price persists `0.00` tax with an honest negative margin; negative margin and negative margin percent are never clamped.
- **API exposure.** The two snapshots appear in the confirmation response and `ProductionBatch` detail only. The batch list response, all five report read models, the report API responses, the report UI, and generated documents are unchanged.
- **Frontend.** `frontend/src/order-production-context.ts` owns the readiness context and request construction. The readiness DTO guard now requires the context pair and never fabricates `null/null`; a stale `409` is a known no-write conflict that invalidates the cached readiness, closes the confirmation, and demands a fresh readiness check with no automatic retry and no uncertain-outcome reconciliation. No financial arithmetic and no financial presentation were added.
- **Tests.** Backend baseline on `origin/main` verified as `737 passed / 0 failed / 0 skipped`; after this slice `841 passed / 0 failed / 0 skipped`. New focused suites: `backend/app/tests/test_production_tax_snapshots.py` (93) and `backend/app/tests/test_production_batch_tax_snapshot_migration.py` (11). All `737` baseline node IDs remain collected except one intentional rename, below. No test was deleted, skipped, or `xfail`-ed.
- **Two superseded tests were intentionally updated.** `test_production_batches_table_has_no_tax_snapshot_columns_yet` was renamed to `test_production_batches_table_has_exactly_the_two_tax_snapshot_columns` — it asserted the absence of exactly the columns this authorized slice adds, so the guard flips to "both exist, nullable, and nothing else was added". The frontend test proving the readiness DTO guard tolerated additive `C2-I` fields was renamed to state that `C2-II` now requires them, because a DTO without the context is no longer a valid no-rate result. Both are strengthened, not weakened.
- **Frontend checks.** `test:order-mutation-lifecycle` `33 passed`, `test:order-readiness-presentation` `15 passed`, `test:order-production-feedback` `21 passed`, `test:settings-tax-feedback` `52 passed`, the new `test:order-production-context` `20 passed`, all 15 suites green, and `npm run build` `PASS`. `frontend/src/main.ts` is `6399` before and `6399` after.
- **Non-goals honored.** No `C2-III`, no readiness or `ProductionBatch` financial presentation, no batch-list expansion, no report recalculation or report snapshot reads, no report UI, no historical backfill or recalculation, no tax-rate history, no multiple or scheduled rates, no per-order/product/client overrides, no accounting, no tax filing, no VAT, no Russian tax regimes, no `C3`, no `C4`, no Restore, no packaging/release work, no `CR-004`, no `CR-006`, and no release-candidate smoke. No dependency and no lockfile changed.
- `C2-III` remains `PLANNED — BLOCKED` and no implementation PR number is assigned to it. `CR-004` and `CR-006` are untouched, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## 2026-07-28 — C2-II merged and closed; C2-III subdivided into C2-III-A and C2-III-B

> **PARTIALLY SUPERSEDED — HISTORICAL FOR THE `C2-III` SLICE LIFECYCLE.** The `C2-II` closure evidence and the subdivision decision below stand. The slice statuses recorded below were true when written and are **superseded**: `C2-III-A` merged as PR #154 and is `DONE — MERGED AND EXACT-HEAD VERIFIED`, and `C2-III-B` is no longer `PLANNED — BLOCKED` with no PR number — it merged as PR #157 and is `DONE — MERGED AND EXACT-HEAD VERIFIED`, so **C2 is `COMPLETED`**. See the `2026-07-29` entry at the end of this file.

- **Documentation-only lifecycle and planning entry.** No runtime code, test, migration, schema, dependency, lockfile, or generated artifact changed. No new ADR, Change Request, implementation task file, smoke rules file, architecture document, or report contract was created, and no future implementation PR number was assigned.
- **`C2-II` closure verified before editing (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR).** PR #152 `C2-II — Persist transactional production financial snapshots` is `MERGED`, base `main`, final reviewed head `0cdda1b06b9783975f085207527f7d36a2ef7f22`, merge commit `c3a3a7b8db06fe85290216113b784123ed9b6b30`, merged `2026-07-28T09:00:50Z`. Current `origin/main` equals that merge commit; both the head and the merge commit are ancestors of `origin/main`. The working tree was clean, no open PR already closed `C2-II` or authorized `C2-III`, and no runtime implementation of `C2-III` was open.
- **`C2-II` is `DONE — MERGED AND EXACT-HEAD VERIFIED`.** Accepted merged evidence, attributed and not re-executed here: exact smoke-tested head `0cdda1b06b9783975f085207527f7d36a2ef7f22`; complete backend suite `883 passed / 0 failed / 0 skipped` with all `737` original merged-baseline node IDs still collected and **zero renames**; all 15 focused frontend suites green with `0 failed`; frontend production build `PASS`; exact-head migration smoke `PASS — 41 checks / 0 failures`; exact-head API smoke `PASS — 57 checks / 0 failures`; exact-head browser smoke `PASS — all Orders-route checks / 0 failures`; `frontend/src/main.ts` final line count `6399`; migration `0019_production_batch_tax_rate_snapshots` delivered; and no commit added after the accepted smoke — the head was verified unchanged and the tree clean afterwards.
- **Correction to an earlier dated record.** The 2026-07-28 entry above states that two tests were intentionally renamed. That was true of an earlier revision of the PR branch. Both original node IDs were restored before merge, so the accepted final merged result is `737 / 737` backend node IDs collected with zero renames. The earlier dated entry is preserved unchanged as history.
- **Stale pre-merge `C2-II` claims removed or marked historical.** Active statements that `C2-II` was `IMPLEMENTED ON PR BRANCH — NOT MERGED`, that merged `main` contained only the `C2-I` readiness estimate, that no `ProductionBatch` rate snapshot column existed on `main`, or that `C2-III` was blocked on an unmerged `C2-II` were corrected in `docs/decisions/0012-c2-financial-calculation-snapshots.md`, `docs/implementation-plan.md`, `docs/roadmap.md`, `docs/api.md`, `docs/domain-model.md`, `docs/settings.md`, `docs/reports.md`, `docs/architecture.md`, `README.md`, `state/current-focus.md`, and `state/handoff.md`. Dated historical records that were true when written are preserved and, where they sit next to an active status, are explicitly introduced as `HISTORICAL PRE-MERGE RECORD — SUPERSEDED`.
- **`C2-III` subdivided into exactly two runtime slices.** ADR 0012 already required subdivision if `C2-III` was not one bounded, independently reviewable vertical slice. It is not, so the umbrella is replaced by `C2-III-A` and `C2-III-B` — no more and no fewer. No new financial formula, product capability, Change Request, or architecture was introduced.
- **`C2-III-A — Order and ProductionBatch financial presentation` is `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED`.** It is the only slice this documentation change authorizes and must not be started from the unmerged documentation branch. One user workflow: check Order readiness → understand the financial estimate → confirm production → see the persisted actual financial result. Scope: Order readiness presentation of `sale_price`, `estimated_cost`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_tax`, `estimated_margin`, `estimated_margin_percent`, and `financial_estimate_status`, with the labels `available` → `Доступно`, `partial` → `Частично`, `unavailable` → `Недоступно` and the accepted backend financial warnings shown through the existing readiness warning mechanism; `ProductionBatch` detail presentation of the persisted sale price, total cost, rate-percentage snapshot, rate-effective-timestamp snapshot, tax, margin, and margin percent; and a compact `ProductionBatch` list financial summary using only the existing batch-list fields, with the rate snapshots staying detail-only and no second financial list endpoint. The frontend must not calculate tax, margin, or margin percent, reconstruct missing values, reinterpret warning codes, read the current Settings tax rate as a substitute for readiness, or recalculate history. The UI must keep real `"0.00"` distinct from unavailable, negative margin distinct from zero, negative margin percent distinct from zero, missing historical snapshots distinct from configured zero tax, and `partial` distinct from `unavailable`. Constraints: no report backend, report DTO, `/reports` UI, or report-document change; no migration; no financial formula change; no `ProductionBatch` persistence change; no historical backfill; no accounting or tax-regime functionality; display-only frontend; `frontend/src/main.ts` at most `6399` lines with no financial arithmetic, DTO validation, large HTML template, or financial lifecycle state machine in it; focused modules only, with no catch-all `finance.ts`, `utils.ts`, `helpers.ts`, `manager.ts`, or `common.ts`.
- **`C2-III-B — Snapshot-backed reports and report documents` is `PLANNED — BLOCKED`** until `C2-III-A` is implemented, reviewed, exact-head smoke verified, and merged. It is **not authorized here** and has no PR number. Planned boundary: the finance report reads persisted `ProductionBatch` snapshots; report tax comes only from persisted `ProductionBatch.tax` and report margin only from persisted `ProductionBatch.margin`; history is never recalculated with the current tax setting; old batches with null snapshots stay incomplete or unavailable; null is never fabricated as `"0.00"`; configured zero tax stays a real known value; the `/reports` backend DTO and frontend presentation are updated together; the overview finance summary becomes snapshot-backed where directly affected; the document `Сводка мастерской` stays synchronized with the report DTO it consumes; and Orders readiness and `ProductionBatch` UI are not changed in that slice.
- **No aggregate report percentage formula was invented.** The only accepted aggregate basis remains the existing documented `known_margin_percent` rule in `docs/reports.md`, which uses the same complete paired sale-price/cost basis as `known_margin`. An arithmetic average of batch percentages, a weighted average of batch percentages, aggregate margin divided by aggregate revenue, and recalculation from current settings are all explicitly recorded as choices that may not be made silently before an explicit later contract. Before `C2-III-B` is authorized, the implementation-planning task must inspect the current report queries, the paired revenue/cost behavior, the incomplete-data counters and warnings, the finance and overview report schemas, the frontend `/reports`, report-document generation, and the existing tests and smoke boundaries.
- **C2 completion rule recorded.** `C2 is not complete after C2-III-A.` C2 becomes complete only after `C2-III-A` is merged and exact-head verified, `C2-III-B` is separately authorized, `C2-III-B` is merged and exact-head verified, and the active documentation and state are closed consistently.
- **Verification performed.** Level 0 documentation checks only — `git status --short --untracked-files=all`, `git diff --check`, `git diff --stat`, `git diff --name-only`, and the same `--check` / `--stat` / `--name-only` against `origin/main...HEAD`. **Not executed, because this is documentation-only:** `pytest`, frontend tests, `npm run build`, API smoke, browser smoke, migration smoke, packaging smoke, and release smoke.
- ADR 0011, `CR-007`, and `CR-008` are not reopened. `CR-004` and `CR-006` are untouched, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## 2026-07-28 — C2-III-A implemented on an unmerged PR branch

> **HISTORICAL PRE-MERGE RECORD — SUPERSEDED.** This entry described `C2-III-A` while it was still on an unmerged PR branch, and its slice statuses were true when written. `C2-III-A` merged as PR #154 and `C2-III-B` merged as PR #157; both are `DONE — MERGED AND EXACT-HEAD VERIFIED`, and **C2 is `COMPLETED`**.

- **`C2-III-A` status: `IMPLEMENTED ON PR BRANCH — NOT MERGED`.** Not `DONE`. Branch `codex/c2-iii-a-production-financial-presentation`, started from clean merged `origin/main` `1eb0d5420eaabbd8f61a66dba523f058a38826a6` with a clean working tree. PR #153 `Close C2-II and authorize two bounded C2-III slices` was verified `MERGED` first — final reviewed head `2ff16f7a0097364e79f2890ab7b7165e439299a3`, merge commit `1eb0d5420eaabbd8f61a66dba523f058a38826a6`, merged `2026-07-28T11:32:24Z` — and no open PR already implemented `C2-III-A`. No history was reset, rewritten, amended, rebased, or force-pushed.
- **Two focused frontend modules, no catch-all.** `frontend/src/production-financial-contract.ts` owns the financial DTO types, the `available` / `partial` / `unavailable` status enum, and readiness financial validation. `frontend/src/production-financial-presentation.ts` owns every financial render function plus the two per-line batch cost-snapshot tables moved out of the shell. The canonical tax-rate pair checks stay in the existing `frontend/src/order-production-context.ts`; no `finance.ts`, `utils.ts`, `helpers.ts`, `manager.ts`, or `common.ts` was created.
- **Order readiness financial presentation.** One block inside the existing readiness result card renders `Цена продажи`, `Ориентировочная себестоимость`, `Ставка налога`, `Налог`, `Маржа`, and `Маржа, %`, plus `Ставка действует с: <formatted timestamp>` through the existing application date/time formatter when a rate is configured. `financial_estimate_status` is rendered directly from the backend as `Доступно` / `Частично` / `Недоступно` on an existing pill, with the label always beside the colour, and is never inferred from which fields are null.
- **Immutable actual result, one template.** `Фактическая экономика партии` renders the persisted `ProductionBatch` sale price, total cost, rate-percentage snapshot, rate-effective-timestamp snapshot, tax, margin, and margin percent. The same renderer serves the production-success card and the historical batch detail, so the two cannot drift apart. No estimate-versus-actual variance exists and the current Settings rate is never compared with a historical snapshot.
- **Production history list.** A compact operational summary from only the five existing list fields. The rate snapshots stay detail-only, and no aggregate, total, sort, filter, report table, or second list endpoint was added. Existing search, selection, loading, retained-snapshot and error behavior is unchanged.
- **DTO validation tightened, never loosened.** A trusted readiness result now requires every additive financial key, an exact `available` / `partial` / `unavailable` status, and a rate context that is either canonical or explicit `null/null`. `ProductionBatch` detail now requires **both** rate-snapshot keys present — a missing key is an outdated response, not an implicit null — while explicit `null/null` stays valid, so old rows remain compatible because the backend always returns both keys. Malformed or partial context uses the existing untrusted-response path; nothing is normalized or repaired. The batch list contract is unchanged and still carries no rate snapshots.
- **Value semantics.** Backend `"0.00"` renders as a real zero; `null` renders as `Недоступно` and never as `0`, `0.00`, `0 ₽`, or `0%`; negative margin and negative margin percent keep their sign and are marked negative. No money, percentage, or rate is converted to a JavaScript number, and no tax, margin, percentage, status, or variance is derived in the frontend.
- **One superseded test was intentionally inverted.** `a pre-C2-II batch DTO without the snapshot keys is still accepted` asserted exactly the behavior this authorized slice removes, so it became `a batch DTO missing a snapshot key is untrusted, while explicit null/null is accepted`. It is strengthened, not weakened, and no test was deleted, skipped, renamed away, or `xfail`ed to make the PR pass.
- **Verification.** Complete backend suite `883 passed / 0 failed / 0 skipped`, unchanged from the pre-change baseline, with all `883` baseline node IDs still collected and zero renames; focused backend suites `160 passed`; all 16 focused frontend suites green with `0 failed`, including the new `test:production-financial-presentation` (`22 passed`); `npm run build` `PASS`; `frontend/src/main.ts` `6399` before → `6398` after.
- **Non-goals honored.** No `C2-III-B`, no report backend, report DTO, `/reports` UI, report-document, overview finance-summary, dashboard financial-card, or `Сводка мастерской` change; no aggregation, no aggregate margin-percent decision, no formula change, no historical recalculation or backfill, no current-rate lookup for historical batches, no migration, no new endpoint, no accounting, tax filing, VAT, Russian tax regimes, multiple or scheduled rates, or per-client/product/order rates; no `C3`, `C4`, Restore, packaging, or release-candidate smoke. No dependency and no lockfile changed.
- `C2-III-B` remains `PLANNED — BLOCKED` with no PR number assigned. `C2 is not complete after C2-III-A.` `CR-004` and `CR-006` are untouched, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## 2026-07-28 — C2-III-A merged and closed; C2-III-B authorized as the last C2 runtime slice

> **PARTIALLY SUPERSEDED — HISTORICAL FOR THE `C2-III-B` REPORT CONTRACT.** Every statement below was true when written. Two of its bullets have since been superseded: the `C2-III-B` status is now `DONE — MERGED AND EXACT-HEAD VERIFIED` (PR #157), so its statements that the slice is unimplemented and has no PR number no longer describe the current state; and the bullet recording that no aggregate report percentage formula was invented has been resolved — the stop-and-report instruction it carried was followed, the conflict was found, and the accepted formula is recorded in the later entry § *2026-07-28 — C2-III-B report aggregation contract conflict found by Phase 0 and clarified (documentation-only)*. The current implementation state is in § *2026-07-28 — C2-III-B snapshot-backed reports and report documents implemented on its PR branch* at the end of this file.

- **Documentation-only lifecycle entry.** No runtime code, test, test configuration, package script, schema, migration, dependency, lockfile, or generated artifact changed. No new ADR, Change Request, implementation task file, smoke rules file, or report contract was created, and no future implementation PR number was assigned.
- **`C2-III-A` closure verified before editing (VERIFIED FROM MERGED PR #154 EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR).** PR #154 `C2-III-A — Present Order and ProductionBatch financials` is `MERGED`, base `main`, final reviewed head `ef1103811a8f062f9129bfb465a98e0cfa388935`, merge commit `d432fcaee52a16a4f8b609ec160cf3fa2b33d013`, merged `2026-07-28T13:05:34Z`. Every expected value matched the verified GitHub value exactly. `origin/main` at this branch's start equals that merge commit and has not advanced beyond it; both the head and the merge commit are ancestors of `origin/main`. The working tree was clean, and the repository had zero open PRs — none closing `C2-III-A` and none implementing `C2-III-B`.
- **`C2-III-A` is `DONE — MERGED AND EXACT-HEAD VERIFIED`.** Accepted merged evidence, attributed and not re-executed here: exact smoke-tested head `ef1103811a8f062f9129bfb465a98e0cfa388935`, identical to the final reviewed head; focused frontend suites `order-readiness-presentation` `19 pass`, `order-mutation-lifecycle` `33 pass`, `order-production-context` `25 pass`, `order-production-feedback` `21 pass`, and the new `production-financial-presentation` `22 pass`, all `0 fail / 0 skipped`; all 16 frontend `test:*` scripts pass with `0 failed` and `0 skipped`; frontend production build `npm run build` `PASS`; focused backend suites `160 passed / 0 failed / 0 skipped`; complete backend suite `883 passed / 0 failed / 0 skipped`, byte-identical to the pre-change baseline with all `883` baseline node IDs still collected; exact-head API smoke `PASS — 67 checks / 0 failures`; exact-head browser smoke `PASS — 28 checks / 0 failures`; `frontend/src/main.ts` `6399` before → `6398` after; no commit added after the accepted smoke, with the head verified unchanged and the tree clean afterwards; and backend formulas, persistence, migrations and reports unchanged in the slice.
- **Stale pre-merge `C2-III-A` claims removed or marked historical.** Active statements that `C2-III-A` was `IMPLEMENTED ON PR BRANCH — NOT MERGED`, that it was authorized and not implemented, that `C2-III-B` was `PLANNED — BLOCKED`, that no financial presentation existed in the UI, and that `origin/main` was `c3a3a7b8db06fe85290216113b784123ed9b6b30` were corrected in `README.md`, `docs/decisions/0012-c2-financial-calculation-snapshots.md`, `docs/implementation-plan.md`, `docs/reports.md`, `docs/roadmap.md`, `docs/api.md`, `docs/architecture.md`, `docs/domain-model.md`, `docs/settings.md`, `state/current-focus.md`, and `state/handoff.md`. Dated historical records that were true when written are preserved, and where they sit next to an active status they are explicitly introduced as `HISTORICAL PRE-MERGE RECORD — SUPERSEDED` or `PARTIALLY SUPERSEDED`.
- **`C2-III-B — Snapshot-backed reports and report documents` is `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED`.** It is the only newly authorized runtime slice and the only remaining C2 runtime slice, it must not be started from this unmerged documentation branch, and no PR number is assigned to it. Authorized vertical: persisted `ProductionBatch` financial snapshots → backend report aggregation → report DTOs → `/reports` presentation → overview report consumers → generated `Сводка мастерской`.
- **Backend report ownership recorded.** The affected financial reports must read persisted `ProductionBatch` financial snapshots, and the report layer must not recalculate historical tax or margin using the current tax setting. Report tax comes only from persisted `ProductionBatch.tax`; report margin comes only from persisted `ProductionBatch.margin`; historical rate changes never modify existing report results; the current Settings tax rate is never applied retroactively; report calculations remain backend-owned; report endpoints remain read-only; and report reads create no audit records and no business mutations.
- **Missing, zero and negative values stay distinct.** Explicit stored `"0.00"` is a real known zero; `null` is unavailable or incomplete; negative margin and negative margin percentage are valid signed information; and a missing historical snapshot is different from configured zero tax. A null snapshot must never be included as a fabricated `0`, `0.00`, `0 ₽`, or `0%`, and old batches with incomplete financial snapshots must contribute to explicit incomplete-data counters or warnings rather than silently appearing complete.
- **No aggregate report percentage formula was invented.** The existing accepted `known_margin_percent` contract in `docs/reports.md` is preserved unchanged: it uses the same complete paired basis as `known_margin` and does not use the global known-revenue total. An arithmetic average of row percentages, a weighted average of row percentages, aggregate margin divided by all known revenue, and recalculation using the current tax setting are explicitly recorded as choices that may not be selected silently. The `C2-III-B` implementation task must inspect the current report queries, schemas and tests before modifying the implementation, and if runtime evidence reveals a contradiction between the documented paired basis and the code required for snapshot-backed aggregation it must stop and report the exact conflict instead of inventing a formula.
- **Report DTO, UI and document boundary recorded.** Synchronized changes are authorized in the affected finance report backend model, the affected overview finance summary, the corresponding API schemas, frontend `/reports`, backend-provided report warnings, and document generation for `Сводка мастерской` where it consumes the affected report DTO. The frontend displays backend report DTOs and warnings and calculates no report tax, margin, margin percentage, incomplete-data coverage, or historical value. Newly generated documents may reflect the snapshot-backed result; previously generated documents remain immutable and are never rewritten, regenerated, or silently replaced; and document generation remains an explicit user action.
- **Explicit `C2-III-B` exclusions recorded.** Orders readiness, Order production confirmation, the Order lifecycle, `ProductionBatch` persistence, `ProductionBatch` list presentation, `ProductionBatch` detail presentation, the `C2-III-A` financial presentation modules, tax-rate Settings behavior, migrations, historical `ProductionBatch` rows, and stock or production transactions must not change.
- **C2 completion boundary recorded.** `C2 is not complete in this documentation PR.` C2 becomes complete only after `C2-III-B` is implemented, its focused and complete tests pass, its exact-head API and browser smoke pass, it is reviewed and merged, and the final active C2 documentation and state are closed consistently. C2 is not marked complete merely because `C2-III-B` became authorized.
- **Verification performed.** Level 0 documentation checks only — `git status --short --untracked-files=all`, `git diff --check`, `git diff --stat`, `git diff --name-only`, and the same `--check` / `--stat` / `--name-only` against `origin/main...HEAD`. Every changed file is Markdown. **Not executed, because this PR is documentation-only:** backend tests, frontend tests, `npm run build`, API smoke, browser smoke, migration smoke, packaging smoke, and release smoke.
- ADR 0011, ADR 0012, `CR-007`, and `CR-008` are not reopened. `CR-004` and `CR-006` are untouched, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## 2026-07-28 — C2-III-B report aggregation contract conflict found by Phase 0 and clarified (documentation-only)

> **PARTIALLY SUPERSEDED — HISTORICAL FOR THE `C2-III-B` LIFECYCLE.** The accepted contract recorded below stands and is unchanged. Its lifecycle bullet stating that `C2-III-B` remains unimplemented with no PR number assigned was true when written and is **superseded**: `C2-III-B` merged as PR #157 and is `DONE — MERGED AND EXACT-HEAD VERIFIED`. See the `2026-07-29` entry at the end of this file.

- **Documentation-only PR.** No backend or frontend production code, no test, no schema, no migration, no dependency or lockfile, no package script, no smoke runner and no generated report document was changed. Every changed file is Markdown.
- **`C2-III-B` runtime implementation was attempted and correctly stopped.** The mandatory read-only Phase 0 contract audit returned `STOPPED — CONTRACT CONFLICT` and recorded `C2-III-B — BLOCKED BY REPORT AGGREGATION CONTRACT CONFLICT`. That attempt was a **read-only diagnostic, not an implementation PR**: it created **no branch, no edit, no commit and no pull request**. This is exactly the behaviour that `docs/reports.md`, `docs/implementation-plan.md`, ADR 0012, `state/handoff.md` and `state/current-focus.md` all required.
- **PR #155 merge evidence verified before editing (VERIFIED FROM MERGED PR #155 EVIDENCE — NOT RE-EXECUTED AS RUNTIME WORK).** PR #155 `Close C2-III-A and authorize C2-III-B` is `MERGED`, base `main`, final reviewed head `83565786b13a5d25dc724ae5d3566bc30a55cfa3`, merge commit `8eed36c1f749628865d743ff88eace3ffa2c56a5`, merged `2026-07-28T13:26:52Z`. Every expected value matched exactly. `origin/main` at this branch's start equals that merge commit and has not advanced beyond it. The working tree was clean, the repository had zero open PRs, and no `codex/c2-iii-b-*` implementation branch existed.
- **The conflict.** The merged implementation derives `known_margin` as paired revenue minus paired cost, while the authorized `C2-III-B` contract requires reports to read persisted `ProductionBatch.tax` and `ProductionBatch.margin` **only**. The paired sale-price/cost row set `P` and the persisted-margin row set `M` are identical only while margin is derived. Under snapshot-backed aggregation they diverge: a row can hold a known `sale_price` and a known `total_cost` while `tax` and `margin` are both `null` — the ADR 0012 missing-value matrix row *present / present / missing*, and every pre-`C2-II` row, because there is no backfill. "The same basis as `known_margin`" therefore pointed at two different denominators, and `complete_finance_record_count` / `incomplete_margin_count` could not stay truthful under either reading without being silently repurposed.
- **Accepted row sets recorded.** `R` = all rows; `P` = rows where `sale_price` and `total_cost` are both non-null; `T` = rows where persisted `tax` is non-null; `M` = rows where persisted `margin` is non-null. `P` and `M` are never treated as the same set, and membership in `T` and `M` is read from persisted snapshots, never reconstructed by calculating tax or margin.
- **Accepted `known_tax` rule.** The sum of every non-null persisted `ProductionBatch.tax`. A null tax never contributes zero; `known_tax` is `null` when no row has a tax snapshot and `"0.00"` when at least one snapshot exists and the sum is zero. Tax may be aggregated for a row whose margin is unavailable because its total cost is missing. Reports never calculate row tax and never read the current Settings tax rate.
- **Accepted `known_margin` rule.** The sum of persisted `ProductionBatch.margin` over exactly the rows in `M`. A `null` margin never contributes, a negative margin keeps its sign, persisted `"0.00"` is a real zero, and reports never compute `sale_price - total_cost` or `sale_price - total_cost - tax`, never repair or backfill old rows, and never apply the current tax setting to a historical row. An old row with known sale price and cost but null `tax` and `margin` stays in `P`, is not in `T` or `M`, contributes to known revenue and known production cost, and contributes to neither known tax, known margin, nor the margin-percent numerator.
- **Accepted `known_margin_percent` formula.** `margin_basis_revenue = Σ ProductionBatch.sale_price over exactly the rows in M`, and `known_margin_percent = ROUND_PERCENT(Σ ProductionBatch.margin over M ÷ margin_basis_revenue × 100)`, returning `null` when `M` is empty or `margin_basis_revenue` is zero. This is the accepted meaning of "the same basis as `known_margin`" — the denominator uses sale prices from exactly the rows whose persisted margin is in the numerator. The existing prohibition on *aggregate margin divided by aggregate revenue* is scoped to mean: do not divide snapshot-backed `known_margin` by the global `known_revenue` total when that total contains rows outside `M`. Arithmetic and weighted averages of row percentages, sums or averages of persisted `margin_percent`, the global `known_revenue` denominator, current Settings and reconstructed row margin all remain prohibited.
- **Zero-sale behaviour recorded.** A row with `sale_price == "0.00"` and a non-null margin belongs to `M`, contributes its persisted margin to `known_margin`, contributes zero to `margin_basis_revenue`, increments the margin snapshot record count, and does not on its own make the aggregate percentage available. When every row in `M` has a zero sale price, `known_margin` stays available, `known_margin_percent` is `null`, and `margin_percent_unavailable_zero_basis` is emitted.
- **Existing counters preserved, not repurposed.** `complete_finance_record_count` stays the count of rows in `P` and `incomplete_margin_count` stays the count of rows outside `P` excluded because sale price or total cost is missing. Both remain for backward API compatibility, are documented as **legacy paired sale-price/cost input coverage**, are explicitly **not** the authoritative snapshot-margin coverage counters, and are neither removed nor renamed in `C2-III-B`. The future frontend must use truthful labels such as `Партий с ценой и себестоимостью` and `Партий с неполной парой цены и себестоимости`.
- **Additive DTO fields authorized with exact names.** `known_tax: str | null`, `tax_snapshot_record_count: int`, `missing_tax_snapshot_count: int`, `margin_snapshot_record_count: int`, `missing_margin_snapshot_count: int`. Each counter pair must sum to `produced_order_count`. No tax-rate averages, margin-percent averages, taxable-base snapshots, duplicate known-margin fields, generic coverage objects, report status enums or accounting fields. `OverviewReportResponse.finance_summary` uses this exact same `FinanceReportResponse`, with no overview-only finance field and no overview-only finance calculation.
- **Warning contract recorded.** `missing_sale_price`, `missing_production_cost`, `margin_unavailable` and `partial_margin_basis` are preserved and restated: `margin_unavailable` when production rows exist but `margin_snapshot_record_count == 0`, and `partial_margin_basis` when `margin_snapshot_record_count > 0` and `missing_margin_snapshot_count > 0`. Additive codes `tax_unavailable` (rows exist but `tax_snapshot_record_count == 0`), `partial_tax_basis` (both known and missing tax snapshots exist) and `margin_percent_unavailable_zero_basis` (known margin available but the same-basis denominator is zero) are authorized. Warnings stay Russian and user-readable, reference the affected DTO field, are never duplicated, never warn a configured zero as missing, never claim reports calculated historical tax or margin, and never expose database-column language.
- **Report-document implications recorded.** A newly generated `Сводка мастерской` may display `known_revenue`, `known_production_cost`, `known_tax`, `known_margin`, `known_margin_percent`, the additive snapshot counters and the backend warnings. It only displays backend DTO values and performs no financial calculation. Previously generated documents remain immutable and are never rewritten, regenerated or replaced; changing or clearing the current tax setting changes no historical `ProductionBatch` value, no existing document, no existing sidecar and no report value sourced from persisted snapshots; and document creation remains an explicit user action with no automatic regeneration.
- **Historical entries preserved.** The `known_margin`/`known_margin_percent` paired-basis records that were true when written are kept, and the superseded "no new aggregate margin-percent formula is defined" paragraphs in `docs/reports.md`, `docs/implementation-plan.md`, ADR 0012 and `state/current-focus.md` are explicitly introduced as `HISTORICAL — RESOLVED` rather than deleted. ADR 0012 was amended only as an explicit accepted clarification appended to its existing `C2-III-B` section; its accepted product decision, per-row formulas, missing-value matrix, snapshot and migration rule and historical immutability rule are unchanged. **No new ADR and no new Change Request was created.**
- **`C2-III-B` remains unimplemented.** Its status is now `AUTHORIZED AFTER THIS PR MERGES — CONTRACT CLARIFIED — NOT IMPLEMENTED`, it must not be started from this unmerged documentation branch, and **no implementation PR number is assigned**.
- **C2 completion boundary unchanged.** `C2 is not complete in this documentation PR.` C2 becomes complete only after `C2-III-B` runtime implementation passes its focused and complete tests, its exact-head API and browser smoke pass, its runtime PR is reviewed and merged, and the final active C2 documentation and state are closed consistently.
- **Verification performed.** Level 0 documentation checks only — `git status --short --untracked-files=all`, `git diff --check`, `git diff --stat`, `git diff --name-only`, and the same `--check` / `--stat` / `--name-only` against `origin/main...HEAD` — plus the semantic contradiction search over active documentation and state. **Not executed, because this PR is documentation-only:** backend tests, frontend tests, `npm run build`, API smoke, browser smoke, migration smoke, packaging smoke, and release smoke.
- ADR 0011, `CR-007` and `CR-008` are not reopened. `CR-004` and `CR-006` are untouched, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## 2026-07-28 — C2-III-B snapshot-backed reports and report documents implemented on its PR branch

> **SUPERSEDED — the slice is now merged.** The implementation detail below stands as the record of what was built. Its lifecycle statements — `IMPLEMENTED ON PR BRANCH — NOT MERGED`, `C2-III-B` is not `DONE`, C2 remains incomplete — were true when written and are superseded: PR #157 merged at `87410910aad472343c057f0bcbfcc3797f8b8e09` on `2026-07-28T22:21:18Z`, and **C2 is `COMPLETED`**. See the `2026-07-29` entry at the end of this file.

- **`C2-III-B — IMPLEMENTED ON PR BRANCH — NOT MERGED`.** One focused backend-plus-frontend runtime slice on branch `codex/c2-iii-b-snapshot-backed-reports`, started from clean `origin/main` `7369e7f133f0ce02aea5f2021cbb0e14104b7b34`. PR #156 `Clarify C2-III-B snapshot report aggregation contract` was verified `MERGED` first — head `75ae6d22dbe6ee556c6571596a1b7dd5fe8b517d`, merge commit `7369e7f133f0ce02aea5f2021cbb0e14104b7b34`, merged `2026-07-28T16:56:28Z` — with every expected value matching, `origin/main` equal to that merge commit and not advanced beyond it, a clean tree, zero open PRs, and no existing `c2-iii-b` implementation branch.
- **The contract conflict is resolved in runtime.** Reports no longer derive margin from paired sale price and cost. `ReportsService.get_finance_report()` selects `sale_price, total_cost, tax, margin` and hands the persisted values to a new pure domain module `backend/app/domain/report_financials.py`, which opens no connection, imports neither FastAPI nor Pydantic, reads no setting, writes nothing, uses `Decimal` only, and rounds each total exactly once.
- **Accepted row sets implemented.** `known_revenue` and `known_production_cost` remain independent totals over every non-null persisted value. `known_tax` is the sum of every non-null persisted `ProductionBatch.tax`. `known_margin` is the sum of persisted `ProductionBatch.margin` over exactly `M`. `known_margin_percent` is `ROUND_PERCENT(Σ margin over M ÷ Σ sale_price over M × 100)`, `null` when `M` is empty or that denominator is zero. The global `known_revenue` is never the denominator, persisted row `margin_percent` is never selected or aggregated, and `sale_price - total_cost` and `sale_price - total_cost - tax` appear nowhere in the report code.
- **Null, zero and negative stay distinct.** No tax snapshot → `known_tax is None`; one or more summing to zero → `"0.00"`; the same for margin. A negative persisted margin keeps its sign. A zero-sale row in `M` contributes its margin to the numerator, contributes zero to the basis, and increments the margin snapshot counter; when every `M` row sells for zero the margin stays available, the percentage is `null`, and `margin_percent_unavailable_zero_basis` is emitted.
- **Counters.** `complete_finance_record_count` and `incomplete_margin_count` keep their exact legacy paired sale-price/cost meanings and are neither removed nor renamed. The four additive snapshot counters `tax_snapshot_record_count`, `missing_tax_snapshot_count`, `margin_snapshot_record_count`, `missing_margin_snapshot_count` are implemented with the accepted definitions, and every response satisfies both `pair == produced_order_count` identities.
- **Warnings.** `missing_sale_price`, `missing_production_cost`, `margin_unavailable` and `partial_margin_basis` are preserved by code and restated against persisted snapshots; `tax_unavailable`, `partial_tax_basis` and `margin_percent_unavailable_zero_basis` are added. Each code appears at most once, uses Russian user-readable text, references the affected DTO field, never warns a configured zero as missing, never claims reports calculated history, and never exposes column names.
- **DTO and Overview.** `FinanceReportResponse` grew additively only; no field was removed or renamed. `OverviewReportResponse.finance_summary` is the exact same `FinanceReportResponse` — no overview-only field and no overview-only calculation.
- **Frontend is display-only.** The finance contract and presentation were extracted into `frontend/src/report-financial-contract.ts` and `frontend/src/report-financial-presentation.ts`. Both tabs render through one presentation module, so Overview and Finance cannot drift. The modules contain no `parseFloat`, `parseInt`, `Number(`, `Math.` or `toFixed`, no arithmetic on a DTO financial value, and no `/ 100` or `* 100`. Warning states come from backend warning codes, never from a `null` field. Strict DTO validation rejects a missing additive key, a non-string monetary value, a malformed, negative or fractional counter, an inconsistent counter pair, a malformed or duplicated warning, and a malformed nested overview summary; a rejected response takes the existing Reports read-failure path and the previously accepted snapshot is retained.
- **No raw DTO field name reaches the page.** The Reports warning panel previously printed `Поле: known_revenue`; the additive warnings would have exposed `known_tax` and `known_margin` the same way. It now shows `Показатель: <человекочитаемое название>` through a label owned by the report presentation module, and shows nothing at all for an unrecognized field rather than leaking a raw name.
- **User-facing presentation.** `Известная выручка`, `Известная себестоимость`, `Зафиксированный налог`, `Зафиксированная маржа`, and `Маржа по партиям с зафиксированными финансовыми данными` — not a bare `Маржа, %`. Coverage reads `Налог зафиксирован: X из Y партий` and `Маржа зафиксирована: X из Y партий` from backend counters. Incomplete coverage is explained in plain language only when a backend warning says so. The legacy paired counters sit in a secondary `Полнота исходных данных` section labelled `Партий с ценой и себестоимостью` and `Партий с неполной парой цены и себестоимости`, and are never presented as snapshot coverage.
- **Report documents.** A newly generated `Сводка мастерской` displays the same `OverviewReportResponse.finance_summary` values, both coverage counts and the backend warnings, and explains that tax and margin were saved at production time, are not recalculated from the current rate, are not applied retroactively, may be unavailable for old incomplete batches, and may cover different subsets. The line `Налог не рассчитывается в этом документе` became false and was replaced. Previously generated documents and sidecars remain byte-identical, generation stays explicit, filenames stay unique, and Markdown, PDF availability, Cyrillic font detection, profile rendering, safe paths and metadata behaviour are unchanged.
- **Verification.** Complete backend suite `942 passed / 0 failed / 0 skipped`, up from the recorded baseline of `883 passed / 0 failed / 0 skipped`, with all `883` baseline node IDs still collected and zero renames, deletions, skips or `xfail`s. Focused backend suites: `test_report_financials.py` `38 passed`, `test_reports.py` `19 passed`, `test_reports_api.py` `4 passed`, `test_report_documents.py` `32 passed`, `test_report_documents_api.py` `5 passed`. All 17 frontend `test:*` scripts pass with `0 failed`, including the new `test:report-financial-presentation` (`54 pass` after the review corrections below; the `40 pass` first recorded here was stale on the day it was written — the suite already stood at `43 pass`). `npm run build` `PASS`. `frontend/src/main.ts` `6398` before → `6398` after. Exact-head API and browser smoke results are recorded in the PR body as this PR's evidence.
- **Three directly affected tests were updated, none weakened.** `test_finance_report_sums_decimal_values_and_warns_for_missing_data` and two report-document tests asserted the derived-margin behaviour this slice removes; their assertions now pin the snapshot-backed result and the corrected document wording. No test was deleted, renamed, skipped or `xfail`ed to make the PR pass.
- **Non-goals honoured.** No migration, no historical backfill, no report persistence table, no new endpoint, no `ProductionBatch` persistence change, and no change to Orders readiness, production confirmation, `ProductionBatch` list or detail UI, the `C2-III-A` presentation modules, Settings, or stock and production transactions. No accounting, tax filing, VAT, tax regimes, date filters, annual or quarterly reports, charts, forecasting, analytics, product or client profitability, tax-rate averages or history, DOCX, automatic document regeneration, `C3`, `C4`, Restore, packaging or release-candidate work. No dependency and no lockfile changed.
- **`C2 remains incomplete until C2-III-B is reviewed, exact-head verified and merged, and its active lifecycle is closed.`** `C2-III-B` is **not** `DONE`. ADR 0011, ADR 0012, `CR-007` and `CR-008` are not reopened and the accepted formula and counter contract are unchanged. `CR-004` and `CR-006` are untouched, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## 2026-07-28 — C2-III-B review corrections on the PR branch (PR #157)

> **SUPERSEDED — the slice is now merged.** The corrections below stand. The lifecycle statements — PR #157 open and unmerged, `C2-III-B` not `DONE`, C2 not complete — were true when written and are superseded. See the `2026-07-29` entry at the end of this file.

- **`C2-III-B — IMPLEMENTED ON PR BRANCH — NOT MERGED`** is unchanged. Review of PR #157 at head `8f50e741469b7f5097c1c38dfcdfa52287d9d3d1` accepted the implementation direction and raised two frontend findings plus one stale-evidence correction. All three are fixed on the same branch; no new branch and no new PR were created.
- **Finding 1 — canonical decimal-string validation.** `monetaryValueIsValid()` in `frontend/src/report-financial-contract.ts` accepted any JavaScript string, which is not strict decimal validation. Every finance monetary and percentage field — `known_revenue`, `known_production_cost`, `known_tax`, `known_margin`, `known_margin_percent` — now accepts only an explicit `null` or a canonical signed two-decimal string matching the anchored shape `^-?(?:0|[1-9]\d*)\.\d{2}$`. The check reads characters only: no `parseFloat`, `parseInt`, `Number(`, `Math.` or `toFixed`, and no trimming, padding, rounding or repair. `""`, `" "`, `"abc"`, `"NaN"`, `"Infinity"`, `"+1.00"`, `"01.00"`, `"1"`, `"1.0"`, `"1.000"`, `"1e3"`, `"6,00"`, `"--1.00"` and `"<script>"` are rejected; `null`, `"0.00"`, `"-0.01"`, `"1.00"`, `"1000000.00"` and `"-72.00"` remain accepted. A malformed decimal fails the whole finance read into the existing Reports read-failure path, so the previously accepted snapshot is retained rather than replaced.
- **Finding 2 — tax and margin coverage explained separately.** The superseded `incompleteCoverageNote()` mapped any one of `tax_unavailable`, `partial_tax_basis`, `margin_unavailable` or `partial_margin_basis` to the single statement `Часть старых партий не содержит финансовых снимков. Они не включены в налог и маржу.` That claimed one set of batches was missing from both totals, which the backend never states, and called every affected batch old, which the backend never states either. `frontend/src/report-financial-presentation.ts` now emits one backend-warning-driven statement per total: incomplete tax coverage alone gives `Часть партий не содержит сохранённых данных о налоге. Они не включены в сумму налога.`; incomplete margin coverage alone gives `Часть партий не содержит сохранённых данных о марже. Они не включены в сумму маржи и расчёт её процента.`; both incomplete gives both statements, one per total. Each statement appears at most once however many coverage codes the backend sent about that total, neither statement mentions the other total, the word `старых` is gone, and state is still read from backend warning codes only — never inferred from a `null` value. The Overview and Finance surfaces share the same helper, so the rule applies identically to both. This supersedes the wording recorded in the entry above.
- **`Сводка мастерской` was reviewed and left unchanged.** Its existing wording is qualified (`налог и маржа могут быть недоступны`) and it already states that the totals may cover different sets of batches, with each coverage count printed separately, so it does not carry the tax-and-margin coupling that was corrected in the frontend. No report-document code changed.
- **Finding 3 — stale verification evidence corrected.** The `test:report-financial-presentation` count recorded in the implementation entry above and in `state/handoff.md` was `40 pass`; the suite already stood at `43 pass` when that was written. Both locations now record the actual post-correction count `54 pass`, and the superseded figures are marked as such rather than deleted.
- **Verification after the corrections.** `test:report-financial-presentation` `54 passed / 0 failed / 0 skipped`. All 17 frontend `test:*` scripts pass with `0 failed`. `npm run build` `PASS`. Complete backend suite `942 passed / 0 failed / 0 skipped` with `942 collected`, unchanged — no backend file was touched by these corrections, so every baseline node ID remains collected. `git diff --check` clean. `frontend/src/main.ts` `6398` before → `6398` after; no validation or coverage-copy logic was added to it.
- **Scope held.** No backend report formula, row set `R`/`P`/`T`/`M`, DTO field name or warning condition changed. No report-document persistence, `ProductionBatch` persistence, Orders, production-confirmation, Settings, migration, dependency or lockfile change. Because a commit was added after the previously accepted smoke, both the exact-head API smoke and the exact-head browser smoke were re-run against the new published head, and no commit was added afterwards.
- **`C2 remains incomplete until C2-III-B is reviewed, exact-head verified and merged, and its active lifecycle is closed.`** PR #157 stays open and unmerged with auto-merge disabled, `C2-III-B` is not `DONE`, C2 is not marked complete, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## 2026-07-28 — C2-III-B lifecycle documentation contradiction corrected (documentation-only)

> **SUPERSEDED — the slice is now merged.** The documentation corrections below stand as the record of that pass. Every statement it makes about PR #157 being open and unmerged, and about merged `main` keeping the pre-`C2-III-B` Reports runtime, was true when written and is superseded. See the `2026-07-29` entry at the end of this file.

- **Documentation-only correction on the PR #157 branch.** Review of `ac68204ee70978749c423dfa69944689ff56a09b` accepted the runtime corrections — canonical finance decimal-string validation, separated tax and margin coverage explanations, expanded focused frontend tests, no backend formula change required — but found that active lifecycle documentation still stated `C2-III-B` was *not implemented*, *not startable*, and had *no PR number assigned*, while other active sections in the same files stated it was implemented on a PR branch. No active document may say both. Every changed file in this commit is Markdown.
- **`docs/reports.md`.** The heading `Tax snapshots — decided, not implemented` became `Tax snapshots — implemented on PR branch, not merged`. The sentence claiming `C2-III-B` is not implemented with no PR number assigned now records `IMPLEMENTED ON PR BRANCH — NOT MERGED`, PR #157, branch `codex/c2-iii-b-snapshot-backed-reports`, and states that merged `main` keeps the pre-`C2-III-B` Reports runtime until that PR merges. The Phase 0 conflict record is retained under an explicit `HISTORICAL` marker and its present-tense claim about "the current implementation" is now scoped to the pre-`C2-III-B` implementation. The accepted aggregation formula, row sets `R`/`P`/`T`/`M`, DTO fields, counters and warning contract are **unchanged**.
- **`state/current-focus.md`.** The stale § *What is authorized next* — which said both that the slice is implemented on a PR branch and that it is not implemented, not startable and unassigned — is replaced by § *What is in progress now*, recording one consistent state: `C2-III-B — IMPLEMENTED ON PR BRANCH — NOT MERGED`, PR #157, branch `codex/c2-iii-b-snapshot-backed-reports`, reviewed head. It states separately that merged `main` still contains the pre-`C2-III-B` Reports runtime and that snapshot-backed Reports exist on the PR branch only.
- **`docs/roadmap.md`.** The C1–C4 completion-window block records `C2-III-B` as implemented on the PR #157 branch, not merged and not `DONE`, with snapshot-backed Reports on the branch and the old behaviour on merged `main`. The active statement that no future implementation PR number is assigned to any remaining C2 slice is removed and replaced with the actual number, #157. C3 and C4 stay inactive and release readiness is not claimed.
- **`README.md`.** The current merged baseline is corrected to `7369e7f133f0ce02aea5f2021cbb0e14104b7b34` (the PR #156 merge commit); the accepted merged backend baseline remains `883 passed / 0 failed / 0 skipped` because PR #155 and PR #156 were documentation-only, and the PR #154 and PR #152 merge commits are marked historical. `C2-III-B` is recorded as `IMPLEMENTED ON PR #157 BRANCH — NOT MERGED`, and the claims that it is not implemented, that reports have no implementation branch, and that no PR number is assigned are removed. Merged `main` not receiving the runtime until PR #157 merges is stated explicitly.
- **Semantic contradiction search performed** over `README.md`, `docs/roadmap.md`, `docs/reports.md`, `docs/api.md`, `docs/report-documents.md`, `docs/implementation-plan.md`, ADR 0012, `state/current-focus.md`, `state/progress.md` and `state/handoff.md`. Two further active contradictions were corrected: `docs/api.md` said `C2-III-B` was `AUTHORIZED AFTER THE CLOSURE DOCUMENTATION PR MERGES — NOT IMPLEMENTED`, and ADR 0012 § `C2-III-B` said the same with no PR number assigned. Every surviving historical statement now sits under an explicit `HISTORICAL` / `SUPERSEDED` / `PARTIALLY SUPERSEDED` marker: new markers were added to the `C2-II`-closure, `C2-III-A`-branch and Phase 0 entries in `state/progress.md` and to the `C2-III-A` closure handoff in `state/handoff.md`, and two existing markers that themselves quoted the stale status were updated. `state/handoff.md`'s "Reports are still not snapshot-backed" is now scoped to merged `main`. `docs/implementation-plan.md` and `docs/report-documents.md` were already consistent; the plan gained the PR number.
- **No runtime change.** No backend or frontend production code, no test, no test configuration, no package script, no schema, no migration, no dependency, no lockfile, no report formula, no DTO field, no warning condition and no report-document behaviour changed. **Tests and the build were not re-executed**, because the runtime tree is byte-identical to `ac68204`: the preserved evidence from that head is backend `942 passed / 0 failed / 0 skipped` with all `883` baseline node IDs collected, `test:report-financial-presentation` `54 pass`, all 17 frontend `test:*` scripts passing, `npm run build` `PASS`, and `frontend/src/main.ts` at `6398` lines.
- **Smoke re-run.** Because this commit follows the previously accepted smoke, the exact-head API smoke and the exact-head browser smoke were re-run against the new published head under the same isolation requirements, and no commit was added afterwards.
- **`C2 remains incomplete until C2-III-B is reviewed, exact-head verified and merged, and its active lifecycle is closed.`** `C2-III-B` is not `DONE`, C2 is not marked complete, PR #157 stays open and unmerged with auto-merge disabled, C3 and C4 remain inactive, and **product release readiness is not claimed.**

## HISTORICAL — SUPERSEDED — 2026-07-29 C2 closure and C3-I authorization

> This entry records the true state before C3-I implementation and PR #159 merge. Its C3-I authorization status is superseded by the 2026-07-30 closure entry at the top of this file.

- **Documentation-only pull request.** Every changed file ends in `.md`. No backend or frontend production code, no test, no test configuration, no package script, no schema, no migration, no dependency, no lockfile, no generated artifact, no smoke runner and no user data changed.
- **PR #157 merge evidence independently verified before editing.** `gh pr view 157` returned state `MERGED`, base `main`, head branch `codex/c2-iii-b-snapshot-backed-reports`, head `305d5421e79b8cb833df9588e705e9418781e021`, merge commit `87410910aad472343c057f0bcbfcc3797f8b8e09`, merged at `2026-07-28T22:21:18Z` — every expected value matched. `origin/main` equalled that merge commit, no commit existed on `main` after it, the working tree was clean, and there were zero open pull requests, so no open PR closed C2 or implemented or authorized C3.
- **`C2-III-B — DONE — MERGED AND EXACT-HEAD VERIFIED`.** Accepted merged PR #157 evidence, attributed to that PR and **not re-executed here**: exact-head API smoke `PASS — 53 checks / 0 failures`; exact-head browser smoke `PASS — FULL AUTOMATED SMOKE PASSED`; complete backend suite `942 passed / 0 failed / 0 skipped`; focused report frontend suite `54 pass / 0 fail`; all 17 frontend test scripts `PASS`; production build `PASS`; `frontend/src/main.ts` `6398` lines.
- **`C2 — COMPLETED`.** All four slices are merged and exact-head verified: `C2-I` (PR #151), `C2-II` (PR #152), `C2-III-A` (PR #154), `C2-III-B` (PR #157). Reports on merged `main` are snapshot-backed; the paired sale-price/cost margin derivation is gone from `main`. C2 is not reopened.
- **Stale active claims removed.** No active document now says PR #157 is open, that `C2-III-B` is unmerged or implemented only on a branch, that reports on merged `main` still use the old paired-input calculation, that C2 is incomplete, or that C3 is blocked by C2. Surviving historical text sits under explicit `HISTORICAL`, `SUPERSEDED` or `PARTIALLY SUPERSEDED` markers in `state/current-focus.md`, `docs/reports.md`, `docs/decisions/0012-c2-financial-calculation-snapshots.md` and `docs/roadmap.md` § PR27.
- **New durable contract `docs/audit-log.md`.** It records the accepted `C3-I` product, API, privacy and presentation contract: the `Журнал действий` purpose and its explicit non-purposes; the `actor_type` / `actor_label` field decision and the deferral of a true process `source`; exactly one endpoint `GET /api/audit-logs`; the explicit MVP supersession of `GET /api/audit-logs/{id}`; the safe list response (`items`, `total`, `limit`, `offset`, `filter_options`) and the nine-field item; the backend-owned `display_summary` presenter; the exclusion of the raw persisted summary, raw `metadata_json`, `entity_id`, table names, stack traces, SQL, paths and payloads; the unknown-code fallbacks `Другое действие` / `Другая сущность` / `Другой инициатор`; ordering `created_at DESC, id DESC`; pagination defaults and the explicit reject-not-clamp rule; the seven filters with inclusive `created_from` and exclusive `created_before`; the exact `{"detail": {...}}` validation envelope; append-only read-only behavior; the `/settings/audit-log` route and its full state set; and the complete non-goal list.
- **`C3-I — AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED`**, and it is the only authorized C3 runtime slice. No branch, no PR number, no runtime code.
- **`actor_type`, not `source`.** The API exposes `actor_type` / `actor_label`. `system` and `user` describe the **actor that initiated the action**, not a process origin, so renaming the field to `source` would have silently changed its meaning. The historical process vocabulary — `manual`, `import`, `production`, `migration`, `backup`, `onboarding`, `restore` — is **aspirational**: no write call site persists that dimension, so a true `source` field cannot be implemented truthfully and is **deferred** to a separately authorized product decision and write-side slice. No column rename, no migration, no backfill, no write-call-site change. Unknown actors resolve to `Другой инициатор`.
- **The raw persisted summary is never returned.** It is write-time technical text — mostly English, several values embedding internal record IDs (`Ingredient lot created for ingredient #12`, `Order #4 produced as batch #7`), and `client_wish.*` values embedding user-authored wish text — so returning it verbatim would have contradicted the same contract's ban on internal IDs, technical detail and sensitive text. The API returns `display_summary` instead: a backend-owned safe Russian value resolved from the known `action` by a focused presenter (`AuditLogDisplayPresenter` or equivalent), with no internal IDs, no metadata, no business-table join, no historical rewrite and no sensitive text. A safe business name is retained only under an explicit action-specific allowlist that excludes `client_wish.*` and `client_recipe.*`; unknown actions and unrecognized summary shapes fall back to `action_label`. Historical rows are untouched — only what is shown changes.
- **Exact validation contract recorded.** The routers raise `HTTPException(status_code=422, detail=issue.__dict__)`, so the `DomainIssue` is the **value of `detail`**, and the documented wire body is `{"detail": {"code", "message", "field", "value", "next_action"}}` rather than a bare `DomainIssue`. Dates and range conflicts use the existing `invalid_date`; pagination uses `non_integer_quantity` and `negative_quantity`, plus `pagination_out_of_range` — the one new `DomainIssueCode` member authorized by `C3-I`, because no existing member carries out-of-range pagination semantics. Explicitly supplied invalid pagination is **rejected, never silently clamped**.
- **Inventory taken from the code — current write vocabulary, not verified database rows.** 50 `action` codes, 19 `entity_type` values and two `actor_type` values are producible by merged-`main` production call sites. They were read from the call sites, **not** by querying a database containing a row for every code; a real database may hold fewer, and an older one may hold values no current call site produces. `filter_options` is therefore derived from values that actually exist as rows in `audit_logs`, and the unknown-code fallbacks are mandatory. `entity_type` `ImportDraft` is PascalCase while every other value is snake_case, and is matched as-is rather than normalized. No call site was edited.
- **Metadata findings.** No stored metadata contains client notes, allergies, addresses, phones, emails or feedback bodies — it is internal foreign-key IDs, enum codes and counters, which is why `metadata_json` is excluded in full rather than field-by-field. The `source` key inside `tax_rate_setting_changed` metadata is an unrelated internal write-time marker with the constant value `settings`; it is never returned and is not an audit source dimension.
- **Coverage gap recorded.** Backups, exports, report-document generation and workshop-profile updates are **not** audited on merged `main`, despite `AGENTS.md` § 3.5 and `docs/domain-model.md` § 3.8. `C3-I` must not add those write call sites; closing the gap needs a separately authorized write slice.
- **Level 0 documentation smoke only.** `git status --short --untracked-files=all`, `git diff --check`, `git diff --stat`, `git diff --name-only` and the three-dot `origin/main...HEAD` variants were run, and every changed file ends in `.md`. **Backend tests, frontend tests, the build, API smoke, browser smoke, migration smoke, packaging smoke and release smoke were not run**, and no runtime command is claimed as executed.
- **C4 remains `INACTIVE — NEEDS PRODUCT DECISION`.** Restore, packaging, installation verification, the update flow and the full release-candidate smoke all remain open, and **product release readiness is not claimed.**

## 2026-07-29 — C3-I contract corrections after PR #158 review (documentation-only)

Review of PR #158 at head `25d48f3848b9277ab31f768fcbbbf35505342a1e` **accepted the C2 lifecycle closure and the bounded C3 direction**, and raised two semantic contradictions plus one API ambiguity in the C3 contract. All three are corrected in the same PR. C2 closure is unchanged and is not reopened. Every changed file ends in `.md`.

- **Finding 1 — `actor_type` is not `source`.** The first draft mapped persisted `actor_type` to an API field named `source` and called it a harmless read-time rename. It is not. The values current call sites produce, `system` and `user`, describe the **actor or initiator**, while the historically documented vocabulary `manual` / `import` / `production` / `migration` / `backup` / `onboarding` / `restore` describes a **process origin**. Mapping one onto the other would have changed the meaning of the field. Corrected: the API now uses `actor_type` and `actor_label`; the authorized filter is `actor_type`; `source`, `source_label` and the source filter are removed from the C3-I response, filters and non-goals; unknown actors resolve to `Другой инициатор`; and a true process source is recorded as **not implementable until write call sites persist a separate source/process dimension through a separately authorized decision**. No column rename, no migration, no write-call-site change.
- **Finding 2 — raw persisted summaries violated the contract.** The first draft returned the persisted `summary` verbatim while the same document forbade internal entity IDs, technical detail, English technical text, sensitive user-authored wish text and technical-admin presentation. The inventory itself proved the contradiction: `Ingredient lot created for ingredient #12`, `Order #4 produced as batch #7`, and `client_wish.*` summaries embedding wish titles. Corrected: the raw `audit_logs.summary` is **never returned by the C3-I API**, and the item field `summary` is replaced by **`display_summary`** — a backend-owned safe Russian value produced by a focused `AuditLogDisplayPresenter` (or equivalently focused module). Presentation is resolved from the known `action`; the raw summary is never an API or frontend fallback; internal IDs, raw metadata, business-table joins and sensitive text are excluded; no historical row is rewritten; a known safe business name is retained only through an explicit action-specific allowlist that excludes `client_wish.*` and `client_recipe.*`; and unknown actions or unrecognized summary shapes fall back to the resolved `action_label`. Contract examples: `Ingredient lot created for ingredient #12 → Создана партия компонента`; `Order #4 produced as batch #7 → Производство заказа подтверждено`; `Client wish created: Убрать компонент X → Пожелание клиента добавлено`.
- **Finding 3 — exact validation wire response.** The first draft described the bare `DomainIssue` shape as the response. Because the routers raise `HTTPException(status_code=422, detail=issue.__dict__)`, the `DomainIssue` is the **value of `detail`**. The documented body is now exactly `{"detail": {"code", "message", "field", "value", "next_action"}}`. Dates and `created_before <= created_from` use the existing `invalid_date` code, and a range conflict identifies the date range rather than silently returning an empty result. Pagination validation is now explicit: omitted `limit` → `50`, valid integer `1..200`; omitted `offset` → `0`, valid integer `>= 0`; below-range, above-range, negative, non-integer, boolean or malformed values return a structured `422` and are **never silently clamped**. Codes reuse `non_integer_quantity` and `negative_quantity`, plus `pagination_out_of_range` — the one new `DomainIssueCode` member authorized by `C3-I`, since no existing member carries out-of-range pagination semantics. It is an enum addition, not a schema change or migration.
- **Inventory wording corrected.** The 50 action codes, 19 entity types and two actor types are now described as the **current write vocabulary — values producible by merged-`main` production call sites**, read from the code rather than by querying a database containing a row for every code. Historical databases may contain unknown values, so the safe fallback contract is mandatory, and `filter_options` is derived from values that actually exist as rows in `audit_logs`.
- **Corrected item shape:** `id`, `created_at`, `action`, `action_label`, `entity_type`, `entity_label`, `display_summary`, `actor_type`, `actor_label`. **Corrected filters:** `created_from`, `created_before`, `action`, `entity_type`, `actor_type`, `limit`, `offset`.
- **Files corrected:** `docs/audit-log.md`, `docs/api.md`, `docs/architecture.md`, `docs/domain-model.md`, `docs/implementation-plan.md`, `docs/roadmap.md`, `README.md`, `state/current-focus.md`, `state/handoff.md`, `state/progress.md`, and the PR #158 body.
- **Preserved unchanged:** `C2 — COMPLETED`; `C2-III-B — DONE — MERGED AND EXACT-HEAD VERIFIED`; one endpoint only; no detail endpoint; no write endpoint; no migration; no backfill; append-only history; ordering `created_at DESC, id DESC`; bounded pagination; date/action/entity/actor filters; backend-owned privacy; no raw metadata; no business-table joins; no edit/delete/rollback/export/analytics; `/settings/audit-log`; focused frontend modules; `frontend/src/main.ts` must not grow net; C4 inactive; product release readiness not claimed.
- **Verification.** Level 0 documentation checks only, plus the semantic consistency audit. **Backend tests, frontend tests, the build and every smoke were not run** for this correction, and no runtime code, test, schema, migration, dependency, lockfile, package script, generated file or user data changed.

## 2026-07-29 — C3-I contract ambiguities resolved after the second PR #158 review (documentation-only)

The second review of PR #158, at head `773af68ab6bc2c27a767872d98744d128b608261`, **accepted** the `actor_type` / `actor_label` decision, the absence of a process-source field and filter, the backend-owned `display_summary`, the exclusion of raw metadata and internal IDs, the exact `{"detail": DomainIssue}` envelope, the new `pagination_out_of_range` enum member, the C2 closure, the C3-I lifecycle authorization and C4 remaining inactive. None of those is reopened. Two contract ambiguities remained and are corrected here. Every changed file ends in `.md`.

- **Finding 1 — the raw-summary prohibition contradicted the name allowlist.** § 5.3 said the persisted summary is never returned "in any form, whole or partial", while § 6.4 authorized extracting a business name from that same summary after an exact English prefix. Both could not be true. Corrected: the absolute prohibition is replaced by a precise rule — the raw persisted summary is never returned **verbatim** and is never used as an **unrestricted** API or frontend fallback, and a suffix may contribute to `display_summary` only when **all seven** conditions hold (allowlisted action; exact assigned prefix matched; non-empty remaining suffix; action authorized to retain that category of business name; suffix rendered only as plain text; no presenter-supplied internal identifier in the suffix; no database or metadata lookup). Otherwise the generic action-specific phrase applies. Still prohibited: returning the complete persisted summary, returning its English technical prefix, using it as an unrestricted fallback, returning summaries containing internal IDs, returning wish text, returning individual-recipe titles, returning metadata, joining business tables and rewriting historical rows.
- **The exact prefix table is now authoritative and enumerated.** Inventoried from merged-`main` production write call sites rather than guessed, `docs/audit-log.md` § 6.4.3 lists all **21** allowlisted actions with `action`, exact persisted prefix, retained suffix category, generic fallback, `display_summary` template and the write call site: `client.created` / `.updated` / `.deactivated`; `ingredient.created` / `.updated` / `.deactivated`; `packaging_item.created` / `.updated` / `.deactivated`; `recipe_template.created` / `.deactivated`; `order.created` / `.updated` / `.cancelled` / `.archived`; `catalog_category.created` / `.updated` / `.archived`; `catalog_tag.created` / `.updated` / `.archived`. Verified example: `client.created`, prefix `Client created: `, template `Клиент создан: <имя>`, fallback `Клиент создан`.
- **The allowlist is an exact list, not a prefix glob.** `client_recipe.*` and `client_wish.*` are excluded; every action whose summary embeds an internal ID is excluded (`ingredient_lot.*`, `stock_movement.created`, `packaging_stock_movement.created`, `production_confirmed`, `recipe_version.created`); and every catalog-assignment action is excluded because its persisted summary is the fixed string `Catalog category assigned` or `Catalog tags updated` with no name to retain — even though those actions share a dotted namespace with allowlisted groups.
- **Finding 2 — pagination validation codes overlapped.** A negative `limit` matched both the `negative_quantity` rule and the "outside `1..200`" rule. Corrected with an explicit ordered precedence where the first match decides: missing → default (`limit` `50`, `offset` `0`); wrong type or representation, including non-integer, fractional, boolean and malformed strings → `non_integer_quantity`; negative integer → `negative_quantity`; non-negative `limit` outside its range, that is `0` or `> 200` → `pagination_out_of_range`; otherwise accepted (`limit` integer `1..200`, `offset` integer `>= 0`). Binding examples: `limit=true`, `limit=1.5` and `limit=abc` → `non_integer_quantity`; `limit=-1` and `offset=-1` → `negative_quantity`; `limit=0` and `limit=201` → `pagination_out_of_range`; `limit=200` and `offset=0` accepted. Nothing is silently clamped, coerced, rounded or ignored.
- **Date-range conflict field defined.** `created_before <= created_from` returns HTTP `422`, `code: invalid_date`, **`field: created_before`**, `value` the supplied `created_before` value, a Russian `message` explaining that the end of the period must be later than its beginning, and a Russian `next_action` telling the user to select an end date later than the start date. The undefined synthetic field `date_range` is explicitly rejected.
- **Enum decision preserved.** `PAGINATION_OUT_OF_RANGE = "pagination_out_of_range"` remains the single new `DomainIssueCode` authorized by `C3-I`, and must not be replaced by `percentage_out_of_range`, `invalid_category`, `invalid_decimal` or `zero_quantity`. It is a bounded enum addition, not a schema migration.
- **Files corrected:** `docs/audit-log.md`, `docs/api.md`, `docs/implementation-plan.md`, `README.md`, `state/current-focus.md`, `state/handoff.md`, `state/progress.md`, and the PR #158 body.
- **Verification.** Level 0 documentation checks only, plus the semantic consistency audit. **Backend tests, frontend tests, the build and every smoke were not run** for this correction, and no runtime code, test, schema, migration, dependency, lockfile, package script, generated file or user data changed.
