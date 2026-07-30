# Handoff

## C3-I closure and C3-II-A authorization handoff (2026-07-30)

This is a documentation-only lifecycle handoff. No runtime code, test, schema, migration, dependency, lockfile or generated artifact changes.

### Verified merged closure

```text
C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED
```

- Repository: `Mitronomik/cosmetic-workshop-os`
- PR #159: `MERGED`, base `main`
- Final reviewed and published head: `bf7cde060a43190fdf22c612a16b0c137aa5531b`
- Merge commit: `ba3ca7443e3280bc7f700af11e75dc4fa810665f`
- Merged at: `2026-07-30T03:20:23Z`
- `origin/main` at branch start: exactly `ba3ca7443e3280bc7f700af11e75dc4fa810665f`
- Both commits are ancestors of `origin/main`; tree clean; zero open PRs; no existing exact lifecycle branch.

Exact-final-head evidence: focused AuditLog frontend `92 passed / 0 failed / 0 skipped` in default and `TZ=Europe/Amsterdam`; all frontend `test:*` scripts pass with `0 failed / 0 skipped`; build `PASS`; `frontend/src/main.ts` `6380`; exact-head browser smoke `PASS — EXACT-HEAD BROWSER SMOKE PASSED`, 60 scenarios.

Separately attributed evidence on `2848880f2009158749398aec7d504c0364336ba9`: complete backend `1364 passed / 0 failed`, focused backend `422 passed`, all 942 established node IDs preserved, API smoke `150 checks / 0 failures`. The backend tree is byte-identical at final head `bf7cde060a43190fdf22c612a16b0c137aa5531b`, but backend and API were not re-executed after the final frontend-only correction. Do not claim `PASS — FULL AUTOMATED SMOKE PASSED` for the final head.

### Next authorized slice

```text
C3-II-A — Atomic workshop-profile AuditLog coverage
AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED
```

Only after this documentation PR merges, start a fresh runtime branch from clean `origin/main`. No implementation PR number is assigned. Scope is only `WorkshopProfileSettingsService.update_profile()`:

- canonical validation before writes where possible;
- one caller-owned SQLite transaction and connection;
- read/compare current profile;
- real change upserts `workshop_profile` and inserts exactly one `workshop_profile.updated` / `app_setting` / `workshop_profile` / `user` audit row;
- failure of either write commits neither;
- canonical no-op performs no upsert, preserves `updated_at`, writes no audit and returns an honest Russian no-change message;
- no Clear or profile deletion;
- no profile value, contact data, note, JSON, old value or new value in summary or metadata;
- existing profile endpoints/shape, Settings lifecycle, tax-setting audit, other settings rows and historical report documents stay unchanged;
- C3-I continues to expose only safe backend-owned labels and `display_summary`.

Full requirements, including all 18 backend assertions, frontend suites and isolated exact-head failure-injection smoke: `docs/audit-log.md` § 16 and `docs/implementation-plan.md` § C3.

### Still unresolved

```text
C3-II-B — File-backed artifact AuditLog semantics
NEEDS PRODUCT DECISION — NOT AUTHORIZED
```

This covers only manual backup, JSON export and report-document audit semantics. Do not choose the result of successful artifact creation followed by failed AuditLog persistence implicitly. Success/partial-success feedback, compensation, artifact authority, retry/reconciliation, duplicate protection, startup recovery and exact smoke all require a future product decision. `CR-004` and `CR-006` remain unchanged and separate.

Final lifecycle:

```text
C1 — COMPLETED
C2 — COMPLETED
C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-A — AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED
C3-II-B — NEEDS PRODUCT DECISION — NOT AUTHORIZED
C3 — INCOMPLETE
C4 — INACTIVE — NEEDS PRODUCT DECISION
Product release readiness — NOT CLAIMED
```

Restore, packaging, installation, update and release-candidate smoke remain open and inactive.

## HISTORICAL — SUPERSEDED — C3-I read-only workspace on its pre-merge PR branch

> This section records the true pre-merge state and is preserved for traceability. It is superseded by the 2026-07-30 closure handoff above.

`C3-I — Read-only AuditLog workspace` is **`IMPLEMENTED ON PR BRANCH — NOT MERGED`**.

- Branch: `codex/c3-i-read-only-audit-log-workspace`
- Started from clean `origin/main`: `fa433d03acbf68e16b14ba6245885ab9eaf15c35` (PR #158 merge commit; PR #158 final reviewed head `4a37f6700e147fb83b64be29db4793e3579a7eff`)
- Durable contract: `docs/audit-log.md` — authoritative and not reinterpreted

The one implementation-level clarification added is the exact nested `filter_options` DTO (`{"value", "label"}` per option) and the omission of `null` from selectable entity types, recorded in `docs/audit-log.md` § 7.5.1 and `docs/api.md`. No other field, filter, endpoint, write behavior or product capability was added.

### What exists now

Backend: one read-only endpoint `GET /api/audit-logs`; the pure presenter and query validator under `backend/app/domain/`; read methods on the existing `AuditLogRepository`; `backend/app/services/audit_logs.py`; `backend/app/schemas/audit_logs.py`; `backend/app/api/audit_logs.py`. Frontend: `/settings/audit-log` titled `Журнал действий` under `Данные и настройки`, built from `audit-log-contract.ts`, `audit-log-local-time.ts`, `audit-log-presentation.ts`, `audit-log-workspace.ts`, `audit-log-bindings.ts`, `audit-log-dom.ts` and the extracted `app-navigation-routes.ts`.

`AuditLogRepository.create_log` is unchanged (empty diff) and no production write call site was touched. There is **no migration**; the only enum addition is `DomainIssueCode.PAGINATION_OUT_OF_RANGE`.

### Verification

Focused backend `422 passed`; complete backend `1364 passed / 0 failed / 0 skipped`; all `942` merged-baseline node IDs still collected with zero renames. Focused frontend suite `test:audit-log-workspace` `82 passed / 0 failed / 0 skipped` in both the normal and explicit `TZ=Europe/Amsterdam` runs. All `18` frontend `test:*` scripts pass. `npm run build` passes. `git diff --check` clean. `frontend/src/main.ts` `6398` → `6380`. Exact-head API and browser smoke results for the correction commit are recorded in the pull request body. The prior smoke at `749c51992c43af65f8297acb0979aded86fdb607` applies only to that previous head and is superseded for merge-readiness.

Review corrections preserve accepted rows across route re-entry refresh failures,
keep draft and applied filters separate until a successful apply or clear,
preserve keyboard focus through targeted updates and necessary full renders,
reject nonexistent and ambiguous local DST times without issuing a request, and
bound arbitrary-length pagination input before Python integer conversion or
SQLite binding. Rejected reads remain read-only.

### Immediate next step

Review and merge the `C3-I` pull request. Do not merge it from this task, do not enable auto-merge, and do not fold any other slice into it.

After merge, a future product PR may fold the `C3-I` lifecycle closure into its normal state update. Until then the lifecycle stays:

```text
C1 — COMPLETED
C2 — COMPLETED
C3-I — IMPLEMENTED ON PR BRANCH — NOT MERGED
C4 — INACTIVE — NEEDS PRODUCT DECISION
Product release readiness — NOT CLAIMED
```

### Do not do next through this PR

Closing the `docs/audit-log.md` § 11.6 write-coverage gap (backup, export, report-document, workshop-profile auditing); a true process `source` field; a detail endpoint; a metadata or raw-JSON viewer; AuditLog export, search, analytics, retention or compaction; C4; Restore; packaging; the update flow; release-candidate smoke. Each needs its own authorization.

---
## Frontend focused-test infrastructure repair handoff

Slice A5 is DONE. PR #131 merged at `62d372644d00fab38ccb1d652ab44556d8241b6a` (`Merge pull request #131 from Mitronomik/codex/implement-a5-local-artifact-presentation`).

The B1/B2 diagnostic audit found no fixture/backend implementation defect requiring a correction PR: demo-data installation is explicit, duplicate install is safely rejected, alert regeneration and purchase-suggestion regeneration are stable, operational source data is meaningful, and passive database reads do not mutate data. No B1 backend/fixture correction and no B2 backend read-model correction is active. B2 browser presentation was not fully verified by that diagnostic audit.

The current focused task repairs frontend focused-test TypeScript infrastructure only. The four repaired scripts must remain suite-isolated, use repository-local TypeScript project compilation, emit under `frontend/dist-tests/`, remove stale suite output before each run, and execute the existing Node `.mjs` tests. Do not change runtime behavior.

Next runtime slice after this repair: B3.1 — Shared feedback for Dashboard, Onboarding and Help. Do not assign a future PR number before GitHub creates it.

## Repository state

Runtime product implementation is complete through PR98.

PR99-PR101 were documentation and governance changes only:
- PR99 added the project UI/UX contract, project-owned Codex UI skill guidance, and related repository documentation.
- PR100 added the reviewed project-owned Impeccable guidance and provenance record without activating the upstream skill.
- PR101 recorded the Taste Skill review and rejection without installing, vendoring, copying, or activating upstream content.

## Workshop profile behavior

PR98 integrated editable Workshop profile settings with newly generated report documents and cleaned stale Settings copy.

Changed behavior:
- Newly generated Markdown `Сводка мастерской` documents include `Профиль мастерской` near the top when at least one profile field is configured.
- Newly generated PDF overview documents use the same backend-built presentation lines, so configured profile fields are included when local PDF support is available.
- Empty profile fields are omitted; an entirely empty/default profile omits the profile section and document generation still succeeds.
- Profile values are rendered as plain document text and escaped or neutralized for Markdown control characters and HTML-like text.
- Existing generated Markdown/PDF files and metadata sidecars are not mutated.
- `GET /api/settings/status` and `/settings` copy state that the Workshop profile is editable while calculation-sensitive settings remain out of scope.
- `/report-documents` explains that filled Workshop profile fields are added to new Markdown/PDF summaries.

Safety boundaries:
- Profile values are display metadata only and do not affect calculations.
- Report values come from backend `ReportsService`; frontend does not inject profile values into generated documents.
- Document generation remains explicit and backend-owned.
- No recipes, clients, orders, production, stock, costs, taxes, margins, alerts, purchases, imports, exports, backups, demo data, or historical records are changed by this integration.
- No tax/currency/margin/unit settings, stock-threshold settings, expiry settings, template editor, logo upload, DOCX, invoices, labels, certificates, roles/auth, cloud sync, integrations, scheduled jobs, or AI/RAG were added.

## Immediate next step

Manual browser smoke has not yet been recorded as completed.

Run this smoke before starting another implementation slice:
- Save non-empty and empty Workshop profile fields in `/settings`.
- Generate/open new Markdown and PDF summaries from `/report-documents`.
- Confirm only non-empty values appear.
- Clear the profile and generate another document.
- Confirm the profile section is omitted, generation does not crash, and previous files remain unchanged.

After smoke:
- Clean result: prepare Workshop profile display polish / app header integration.
- Failed result: prepare a focused report document integration fix first.

Do not assign a new PR number until the PR is actually created.

## Settings UI repair handoff

Manual browser smoke found a blocking `/settings` UI defect: the Workshop profile form was not laid out as a usable vertical form and the page displayed internal planning material. The current focused repair keeps the existing branch scope narrow: runtime Settings now shows only a compact introduction, Workshop profile editing, and local data/navigation. Technical planning content is removed from the runtime Settings screen, while backend-compatible status fields are unchanged. The Workshop profile renders independently from the general Settings status request.

Next step after merge: rerun isolated browser smoke for `/settings` Workshop profile states and `/report-documents` integration.

## Shared action-state visual contract handoff

Source and runtime audits identified inconsistent shared action visual states. This branch is limited to the shared visual contract for existing primary, secondary, danger, compact, action-link, and sidebar navigation focus states. No application behavior or API behavior changed. Browser smoke remains required across representative routes before merge. The next planned system-level task is shared feedback presentation and semantics.

## PR105 focus contrast follow-up handoff

Shared action focus contrast was fixed by changing the `.primary-action`, `.secondary-action`, and `.danger-action` `:focus-visible` outline from `rgba(211, 154, 122, .75)` to `#9a5f49`; sidebar focus styling was intentionally left unchanged. Browser smoke ran with an isolated temporary SQLite database/user-data directory on `/settings`, `/exports`, `/report-documents`, `/alerts`, `/purchase-suggestions`, `/demo-data`, sidebar keyboard navigation, and 1440×900 plus 390×844 viewports. Passed scenarios included focus visibility, hover/pressed states, disabled settings controls, loading/error presentation, generated document links, demo danger action after isolated demo install, no horizontal overflow, screenshots, and no page errors. Alert row actions, purchase-suggestion row actions, and disabled danger action presentation were unavailable in the isolated data. The only console error was the intentional intercepted `/exports` 503 request-failure smoke. Frontend build passed.

## Shared feedback semantics slice handoff

This branch introduces the initial shared feedback presentation and announcement contract for exactly `/settings`, `/exports`, `/report-documents`, `/imports`, and `/demo-data`.

- Visible feedback uses a shared helper with neutral, success, warning, and error tones.
- Persistent hidden announcers are created outside `#root`: polite action results use `role="status"`; assertive action failures use `role="alert"`.
- Visible feedback elements do not carry live-region semantics, preventing duplicate announcements when `root.innerHTML` re-renders.
- Action handlers clear stale announcer text at the start of a new request and announce only new success/error results.
- Static route-load errors remain visible recovery cards and are not treated as action alerts.
- `aria-busy` is limited to the affected action region: Workshop profile form, export creation form, report document creation form, import upload/apply panels, and demo install/clear confirmation panels.
- Import apply errors remain structured and escaped.
- Completed checks: source searches before/after, `git diff --check`, frontend build, isolated backend/frontend curl smoke. Backend pytest currently reports 5 unrelated backend-area failures. Earlier Codex-local browser Playwright smoke/screenshots were unavailable because Playwright installation from npm was blocked by 403; the completed external Hermes audit is recorded below.
- Legacy feedback outside the five migrated routes remains intentionally for follow-up.

Next planned system task: Scoped busy states for alerts and purchase suggestions.

## PR106 follow-up handoff

The existing shared feedback PR has been updated in place, not replaced.

Fixes completed:

- Workshop profile action-result feedback is now marked with `data-workshop-profile-result` and cleared when editing starts; state `message`/`error` and persistent announcer text are cleared without a keystroke render.
- Initial Workshop profile load no longer displays the backend GET message as a success result.
- Persistent announcers are created at startup via `ensureAnnouncementRegions()` before `render()`.
- Export/report/import/demo flows no longer convert follow-up refresh failures into false mutation failures.
- Import draft cancellation now clears stale announcers, announces cancellation success politely, and cancellation failure assertively.
- Workshop profile cancel now announces the existing cancellation result politely without backend persistence.

Verification notes:

- Backend base/PR comparison is complete: both base `2265802f07b3ee3df7a1c5478bc6ae11fed096b7` and this PR branch report the same 5 failing tests and 463 passing tests for `cd backend && python3 -m pytest`.
- Local Playwright/browser discovery in Codex found no installed browser automation path or browser binary, so Codex itself could not run browser smoke without installing dependencies; the later external Hermes audit completed browser verification and is recorded below.
- Isolated backend/frontend curl startup still passed for `/api/health` and `/settings`.

Next planned runtime task is superseded by the active implementation plan: Slice A1 — User-facing technical copy cleanup.

## PR106 Import Apply correction handoff

Import flow coverage is now explicitly:

- import draft creation;
- import draft cancellation;
- import draft application.

Import Apply mutation and refresh failures are separated. A successful Apply followed by failed list/detail refresh preserves `response.apply_result`, keeps success state, avoids the assertive mutation-failure path, and shows a manual refresh warning. The stale pre-apply selected draft is replaced with the backend apply response before refresh so Apply cannot be triggered again from old readiness state. Structured Apply mutation errors remain preserved for actual mutation failures only.

Local pending-smoke wording for this correction is superseded by the completed external Hermes audit recorded below. Next planned runtime task is superseded by the active implementation plan: Slice A1 — User-facing technical copy cleanup.

## PR106 applied-branch refresh-warning handoff

Import Apply refresh warning now has explicit state (`applyRefreshWarning`) and is visible for an already applied draft. The `status === 'applied'` branch renders the warning with shared warning feedback, then renders the preserved Apply result. Apply success plus refresh failure remains a success state, does not emit an assertive failure, does not show mutation-error/no-partial-change copy, and keeps the authoritative applied draft so Apply cannot be offered again.

Manual recovery remains the existing Import page Refresh action; it rereads the draft list/read model and does not run Apply. The completed external Hermes audit below supersedes earlier pending-smoke wording. Next planned runtime task is superseded by the active implementation plan: Slice A1 — User-facing technical copy cleanup.


## PR106 completed Hermes browser smoke handoff

External GitHub verification confirmed PR #106 was published at canonical runtime head `4a2a88d156d1516568b608b113818dfe77e32210`, which is the exact head tested by Hermes. The local Codex task checkout may have a rewritten local SHA, but no runtime commit was published after the tested head.

Audit environment:
- Isolated temporary repository checkout: `/tmp/cwo-pr106-deterministic-20260713-092916/repository`.
- Isolated SQLite database and isolated user-data directory; no real user data was used.
- Local frontend, backend, and deterministic local fault proxy.
- Headless Chrome with desktop viewport 1440×900 and narrow viewport 390×844.

Verdict: `PR106_DETERMINISTIC_SMOKE_PASS_WITH_NON_BLOCKING_FINDINGS`.

Scenario results:
- Normal Import Apply: draft creation returned 201; Apply returned 200; exactly one Apply POST occurred; exactly one ingredient was created; Apply result remained visible; repeat Apply became unavailable; polite success was observed; no assertive failure occurred; `aria-busy` returned to false.
- Apply success plus refresh failure: Apply mutation returned 200; the proxy intentionally returned 503 for immediate draft detail/list refresh; mutation success and applied result remained visible; the imported ingredient existed exactly once; shared warning feedback instructed the user to press `Обновить`; false mutation-failure text was absent; no assertive Apply failure was emitted; repeat Apply remained unavailable; manual Refresh recovered final state; no second Apply POST or duplicate record occurred.
- Structured mutation conflict: duplicate Apply returned 409; structured row-level details were visible; the persistent assertive `role="alert"` region received the blocking failure; no polite Apply success was emitted; no duplicate ingredient was created; no partial domain write occurred; `applyRefreshWarning` remained empty.
- Settings: normal initial profile load did not appear as action-success feedback; Cancel restored the saved value and produced polite feedback; Save produced polite feedback; editing after Save cleared stale visible success; focus remained in the field; `aria-busy` behaved correctly during Save.
- Responsive and keyboard: no page-level horizontal overflow at 390×844; tested controls remained reachable; persistent announcement regions were outside `#root`; 27 keyboard-reachable elements were observed in logical DOM order. This is DOM/browser smoke evidence, not screen-reader certification or formal WCAG conformance.
- Diagnostics: intentional 503 responses were limited to the refresh-failure scenario; the expected 409 belonged only to the conflict scenario; final record counts were normal import 1, refresh-failure import 1, duplicate created by rejected conflict 0; seven PNG screenshots and seven matching metrics files were verified; repository remained clean after the audit; audit-started ports were released.

Non-blocking observations:
1. MutationObserver errors came from the deterministic audit harness attempting to observe `#root` before the node existed; they were not an application defect.
2. A separate narrow screenshot of the already-failed conflict draft was unavailable after the scenario state transition; required conflict workflow and desktop evidence was present.

All mandatory PR106 browser scenarios passed. No code blocker remains. PR #106 is now merged and verified. Browser smoke does not need to be repeated for this documentation-only plan PR because it changes only documentation/state files.

Next planned runtime task is superseded by the active implementation plan: Slice A1 — User-facing technical copy cleanup.

## MVP product-readiness plan handoff

Current repository state after PR #106:
- PR #106 is merged and verified.
- Runtime product implementation remains the same as the PR #106 verified baseline; this branch is documentation-only.
- The active implementation plan is now `docs/implementation-plan.md`.
- `docs/roadmap.md` remains the strategic product roadmap and scope boundary.
- Future Codex tasks must check both `docs/roadmap.md` and `docs/implementation-plan.md` before choosing scope.

Next action:
- Next active runtime slice: Slice A1 — User-facing technical copy cleanup.
- Slice A1 must be created as a separate focused runtime PR.
- No future PR number has been assigned.
- Do not start validation-error migration, responsive table containment, dashboard work, tax/margin, restore, packaging, update behavior, cloud sync, OCR, AI/RAG, roles, or multi-user behavior as part of this documentation-only plan PR.

## Slice A1a focused technical copy cleanup handoff

This branch implements only A1a: normal healthy operation no longer renders a positive local-service availability badge, the unavailable topbar state uses Russian product recovery language, `/imports` introduction now describes CSV/XLSX draft creation, validation, confirmation, and Apply before records are added, and `/demo-data` count keys are displayed through a centralized Russian label map with «Другие данные» for unknown visible keys.

Files changed are intentionally narrow: `frontend/src/main.ts`, `docs/implementation-plan.md`, `state/current-focus.md`, plus append-only updates to `state/progress.md` and this handoff. No backend, API, schema, migration, CSS, dependency, polling, retry, import Apply behavior, or demo install/clear behavior changes were made.

Verification completed: frontend build passed; backend pytest reported the known 5 unchanged baseline failures and 463 passing tests; Import Apply diff identifiers were reviewed and only existing context matched; focused Playwright smoke used isolated temporary data at 1440×900 and 390×844, with screenshots in `/tmp/cwo-a1a-screens`. Healthy, Import copy, Demo labels, narrow overflow, keyboard focus, and unavailable recovery checks were covered. Offline simulation intentionally aborted API requests, so failed resource console messages are expected for that scenario only.

Next step: repository owner should review the focused PR diff and mergeability. Do not assign any future PR number before GitHub creates it.

## Slice A1b1 handoff — Demo Data and inventory movement copy cleanup

This slice is limited to copy-only cleanup for `/demo-data`, `/ingredient-lots`, and `/stock-movements`. Static runtime wording in those routes now avoids backend/API/internal English terminology and uses Russian product language for Demo Data blocking/clearing boundaries, ingredient-lot load failures, stock-movement loading/fallback states, movement-derived balance display, and outgoing movement safety.

No backend, API, schema, migration, CSS, dependency, lockfile, demo install/clear behavior, stock calculation, validation, request timing, confirmation, disabled-rule, aria-busy, focus, or dynamic-message contract changes are intended. Dynamic backend-provided reasons remain rendered through the existing escaping path. Browser smoke was not run and is not required for this copy-only slice because the final diff changes static text only and does not modify HTML structure, CSS, controls, requests, state transitions, Demo Data behavior, stock behavior, or business logic.

## Slice A1b2 handoff — Backup and Export capability copy
- Published pull request: PR #111.
- Published GitHub branch before the correction: `codex-rzipfx`.
- Published head before the correction: `b6d44e935d5e320d91b955feec97667f03c93b05`.
- Runtime scope is limited to `frontend/src/main.ts` copy in `/backups`, `/exports`, and `dashboardBackupReminder()`; no CSS or backend changes are intended.
- State update scope: `state/current-focus.md` rewritten for A1b2; `state/progress.md` and `state/handoff.md` appended only.
- Verification completed: repository hygiene and focused source-diff checks passed; frontend build passed; backend pytest collected 468 tests with 463 passed and the same 5 known baseline failures; no backend files changed.
- Browser smoke was not run and is not required because the final runtime diff changes static strings only and does not modify HTML structure, CSS, controls, requests, focus, state transitions, Backup behavior, or Export behavior.

## Slice A1b3a handoff — Reports and Report Documents product copy
- Active handoff scope: clean static Russian product copy for `/reports`, `/report-documents`, and `dashboardReportsCard()` only.
- Preserve report requests, report-document requests, `can_create`, disabled rules, `aria-busy`, announcers, success/list-refresh-failure separation, open/download behavior, dynamic filenames, dynamic paths, escaping, routes, and navigation identifiers.
- Do not broaden into Help Center, route readiness metadata, A1c terminology sweep, A2 validation, backend files, CSS, dependencies, docs/implementation-plan.md, docs/reports.md, or docs/report-documents.md.
- Required checks: source-diff reviews for Reports, Report Documents, and navigation; scoped terminology classification; frontend build; backend pytest baseline; repository hygiene checks.
- Browser smoke is not required if the final diff remains static-copy only with no structure or behavior changes.
- Publication metadata must be verified by the repository owner. Do not claim a GitHub PR number or published branch before verification.

## PR #113 correction handoff — A1 closure pending review

- Runtime scope remains the approved A1 closure slice: implemented navigation sections are ready, stale standalone Production Readiness navigation is removed, Help/onboarding copy uses product language, and fallback copy no longer promises already implemented modules later.
- The seven technical contract documents changed by the first PR #113 head were restored to the main baseline and should not appear in the final PR diff.
- Preserved contracts: no backend files, migrations, CSS, dependencies, lockfiles, new routes, request behavior, form behavior, calculations, production readiness/confirmation behavior, import Apply behavior, file open/download behavior, paths, filenames, or escaping are intended to change.
- A1 remains IN PROGRESS; A2 remains blocked. Do not claim A1 completion until the corrected GitHub head is reviewed and focused browser smoke passes.
- Browser smoke remains required before merge for desktop 1440×900 and narrow 390×844 navigation/Help coverage plus previously cleaned A1 routes.

## Slice A1 final handoff — PR #113 verified

- Slice A1 language and navigation cleanup is complete.
- Verified runtime SHA: `040c90fa781edea8484eb84595745c3a3aaf5eaf`.
- Browser smoke result: 53/53 PASS.
- Targeted offline/recovery retest: PASS.
- The backend was genuinely stopped and restarted against the same isolated temporary database.
- The offline UI remained understandable and usable, exposed no raw technical errors, and recovered without a permanent technical-status message.
- No real user data was accessed.
- No backend, CSS, dependency, migration, route, request, form, calculation, production, inventory, import Apply, file-access, or historical-data contract was changed by this final state update.
- Slice A1 is DONE.
- Slice A2 structured form validation is READY and is the next implementation slice.

## Slice A2 handoff — structured form validation foundation

This branch implements PR #114 scope for structured form validation on Clients and Ingredients only. The shared parser lives in `frontend/src/form-validation.ts` and supports existing backend structured error payloads while assigning inline errors only through explicit route-specific allow-lists. `/clients` create/edit maps full_name, phone, email, address, birthday, skin_notes, allergy_notes, preference_notes, contraindication_notes, and notes. `/ingredients` create/edit maps name, category, default_unit, density_g_per_ml, notes, inci_name, supplier_hint, allergen_note, and usage_note.

Validation lifecycle is scoped to the affected form: old validation is cleared before submit, after successful submit, when cancelling/resetting, when switching edited records, and per-field when that field changes. Rejected submits preserve entered form values. Submit buttons remain disabled while their mutation is in flight, and stale responses are ignored with request tokens.

No backend runtime behavior was changed. No migrations, dependencies, lockfiles, navigation routes, recipe/inventory/production/import/backup/export behavior, or broad form migration were added. Slice A3 remains blocked until A2 is reviewed and accepted.

## Slice A2 correction handoff — PR #114

Correction scope stays inside Clients and Ingredients validation. Field-level stale validation is now cleared by updating the affected control/error DOM only; the application is not fully re-rendered on each corrected keystroke. In-flight create/edit contexts are guarded by disabled/guarded cancel and record-switch actions plus request-token checks. Mutation failures still show structured validation, while successful mutations followed by list-refresh failures keep truthful success feedback and show a separate refresh warning that directs the user to reload the list instead of repeating the mutation.

The parser now maps only exact known fields or fields with approved transport prefixes (`body`, `query`, `path`). Nested application paths such as `profile.email` or `metadata.name` remain form-level errors. A2 remains IN PROGRESS — correction under review; A3 remains BLOCKED A2.

## Slice A2 final handoff — PR #114

Slice A2 is complete and verified.

Verified runtime head:

`8eb5d0c2c116c83d4162d10895268375e0bc1e1e`

The reusable structured-validation foundation is implemented for Clients and Ingredients create/edit forms.

Field errors, form summaries and ARIA attributes are updated without replacing the focused input node. Mutation failures remain separate from post-save refresh failures, stale request contexts are guarded, and backend validation remains the source of truth.

The final frontend test setup is dependency-free. The unused `linkedom` dependency was removed. Parser and targeted DOM tests use separate generated directories and pass when executed concurrently.

PR #114 contains no Slice A3 implementation.

Slice A3 is READY and must begin as a new focused task only after PR #114 is merged.

## Slice A3.1 handoff — Ingredient Lots structured validation

Implemented scope is limited to `/ingredient-lots` create/edit validation migration. The form now uses the shared structured validation parser, an explicit Ingredient Lot field allow-list, inline ARIA-connected field errors, form-level summaries for unknown or nested paths, targeted DOM updates, draft preservation, duplicate-submit protection, guarded context switches, stale-response checks, and separate success-versus-refresh-warning feedback.

Preserved contracts: backend validation remains the source of truth; no backend runtime, schema, migration, dependency, inventory calculation, stock movement, route, cloud, import, production, or historical-data behavior is intentionally changed. `/stock-movements` remains pending and unchanged.

Evidence for this correction: frontend parser tests pass (11/11), targeted validation DOM tests pass (6/6), frontend build passes, concurrent frontend validation tests pass, focused Ingredient Lot backend tests pass (15/15), and isolated local API smoke passed on `/tmp/cwo-pr115-smoke.sqlite` with the expected structured `422` plus one successful lot create. Browser smoke is still pending reviewer execution and must not be reported as passed until that evidence exists.

Remaining A3 sub-slices include `/stock-movements` and other critical forms not covered by A3.1. Slice A3.1 remains IN PROGRESS — implementation under review until accepted review and smoke evidence.

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

## Slice A3.3 handoff — Recipe Template and immutable Recipe Version validation
- PR #116 / Slice A3.2 is merged at `79286f076292645b3e83dfedfccb366dee1777f6`; A3.2 is closed and browser-smoke verified.
- Active runtime scope is A3.3 on `/recipes`: Recipe Template creation and immutable Recipe Version creation use the shared structured-validation and mutation lifecycle foundations.
- Recipe Version edit/delete remains prohibited. Existing saved versions and ingredients are not mutated; rejected version creates must write no partial version, ingredients, or audit event.
- Slice A3 remains IN PROGRESS after this PR unless the repository owner explicitly closes all remaining A3 candidates.

- PR #117 correction targets published branch `codex/add-structured-validation-for-recipes`; pre-correction published head was `718d8cafa62dd9bed87f8eab4e1d7896427a9a9d`. Browser smoke remains reviewer-required unless explicitly run against the published correction head.


## Slice A3.4 handoff — Client Recipe structured validation
- Exact scope: `/client-recipes` Client Recipe create and composition update only. Client Wishes, Client Feedback, Orders, Production Readiness, and Production Confirmation were not included.
- Architecture boundaries: backend domain validation remains authoritative; API handlers stay thin; no schema changes, migrations, new tables, cloud dependency, artificial composition refresh, or historical Recipe Version mutation was introduced.
- Indexed validation behavior: visible composition fields use exact approved paths (`ingredients.{index}.ingredient_id`, `position`, `phase`, `amount_value`, `amount_unit`, `personalization_note`, `notes`). `status`, aggregate `ingredients`, generic `id`/`position`, indexed hidden `id`, malformed paths, unknown nested paths, and service-level ownership/conflict messages remain in the form summary.
- Mutation lifecycle behavior: create and composition update use separate locks, direct DOM guards, duplicate-submit prevention, stale-context checks, targeted validation updates, create success/list-refresh warning separation, and authoritative composition `PUT` response application without follow-up refresh.
- Tests executed in this workspace: `npm run test:form-validation` (16/16), `npm run test:targeted-validation-update` (29/29), `npm run build`, and `python3 -m pytest app/tests/test_client_recipes.py` (40/40).
- Browser smoke: NOT RUN. Reason: waiting for review of the exact published GitHub PR head.
- Remaining A3 candidates: Client Wishes, Client Feedback, Orders, Production Readiness/Confirmation, and any other critical forms selected by the roadmap owner.

## Slice A3.5 handoff — Client Wishes structured validation

Scope: existing Client Wish creation inside the client card only (`POST /api/clients/{client_id}/wishes`). Visible migrated fields: `title`, `description`, `category`, `priority`, and `client_recipe_id`.

Validation mapping boundary: exact approved fields and approved transport-prefixed paths such as `body.title` render inline. Hidden/aggregate/conflict paths including `client_id`, `id`, `status`, `is_active`, timestamps, malformed paths, unknown nested paths such as `metadata.title` or `items.0.title`, and non-structured/network failures remain in the Client Wish form summary. Backend messages continue through safe text rendering/escaping.

Mutation lifecycle: Client Wish create uses its own request lifecycle and client-card context token. Duplicate submits while saving are ignored; the form receives scoped `aria-busy`; inputs/textareas become readonly; selects and conflicting client-card controls are disabled narrowly; stale responses from an old client context cannot update a newer card. Rejected creates keep the form open and preserve title, description, category, priority, linked Client Recipe, focused node, caret, and selection.

Success versus refresh failure: the successful create response is treated as authoritative and inserted into local wishes before refresh. The create form resets/closes after success and announces success. If the follow-up wishes refresh fails, the created wish remains visible, no second POST is sent, the form is not reopened, and a separate refresh warning is shown instead of mutation-failure feedback.

Preserved behavior: active/archived filtering, `Показать архивные`, status labels/actions, archive confirmation, linked Client Recipe choices including archived recipes where already loaded, backend ownership validation, audit logging, and Client Wish list rendering semantics are preserved.

Client Feedback exclusion: Client Feedback create payloads, fields, append-only behavior, endpoints, and runtime validation remain unchanged; it is the next separate validation candidate after A3.5.

Commands actually run will be recorded in the PR/final response. Browser smoke remains required externally against the exact published GitHub PR head before merge if no existing Codex browser automation path is available.

A3.5 commands run in Codex:
- `cd frontend && npm run test:form-validation` — passed.
- `cd frontend && npm run test:targeted-validation-update` — passed.
- `cd frontend && npm run build` — passed.
- concurrent frontend validation test command from the PR prompt — passed.
- `cd backend && python3 -m pytest app/tests/test_client_wishes_feedback.py` — passed, 7 tests.
- `git diff --check`, `git status --short`, `git diff --name-only`, `git diff --stat` — run for repository hygiene.
- Client Feedback scope search and stale project-state search — run and reviewed; changed Client Feedback matches are mechanical context/type references and a source guard confirming `submitClientFeedbackForm` is not migrated.

Checks not run: focused browser smoke was NOT RUN in Codex because no existing browser executable or Playwright command was available without installing browser dependencies. External exact-head browser smoke remains required before merge using the checklist in the PR description.

## PR #119 A3.5 correction — Client Wish validation payload unwrapping

Correction scope: Client Wish create mutation failure handling only. The failure path now unwraps `ApiErrorWithDetails.payload` through the existing shared `apiValidationPayload(error)` helper before calling `normalizeBackendValidation`, so backend structured `detail.field` / `detail.message` payloads can reach the approved Client Wish inline field mapping. No backend contract, parser, schema, Client Feedback behavior, status/archive behavior, dependencies, CSS, or unrelated runtime code was changed.

Test-report boundary: frontend validation parser and targeted DOM tests are behavioral unit tests; `main.ts` wiring checks for the Client Wish submit handler and Client Feedback boundary are source guards only. Source guards do not prove browser-level POST counts, focus/caret behavior, refresh-warning rendering, or stale client-card isolation; external exact-head browser smoke for PR #119 remains required before merge.

## 2026-07-18 — A3.6 handoff
- Baseline recorded: PR #119 / A3.5 merged at `e53e7852c8b384915fb77b59345170c43671151c`; verified runtime head `e19229df1afa74f4470864071e91a0e94a5631cd`; complete external exact-head smoke PASS.
- A3.5 is DONE. A3.6 Client Feedback structured validation is DONE in PR #120; published head `e148220ac9ad08a0fd952482a0b293f1f2d22bad`, merge commit `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`, exact-head smoke PASS.
- This slice was limited to Client Feedback creation in the client card; feedback remains append-only.

## 2026-07-18 — Project memory sync after PR #120

Application runtime baseline before this documentation-only synchronization: `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`. PR #120 / `A3.6 — Client Feedback structured validation` is merged at that commit; published head `e148220ac9ad08a0fd952482a0b293f1f2d22bad` passed complete automated exact-head smoke with verdict `PASS — FULL AUTOMATED SMOKE PASSED`.

Automated evidence recorded for PR #120: frontend form-validation `18/18 PASS`, frontend targeted-validation-update `61/61 PASS`, frontend build `PASS`, concurrent frontend validation tests `PASS`, focused backend Client Wishes/Feedback tests `7/7 PASS`, smoke Bash syntax check `PASS`, and browser-runner Node syntax check `PASS`. Browser smoke covered normal Client Feedback creation, structured backend `422`, draft/focus/caret/selection preservation, no write after rejected validation, duplicate-submit protection, successful create plus controlled refresh failure, stale background response protection, append-only boundary, exact request URL/client ID/body/count assertions, and backend state verification. Controlled failures were limited to expected `422` validation and expected `503` post-create refresh failure. Unexpected browser console errors: `0`; unexpected network failures: `0`. Exact-head repository cleanup passed. Git comparison found no file-tree difference between the tested head and merge commit. Smoke artifacts were generated externally and are not committed.

PR #96 / `PR96 — Workshop profile settings foundation` was reviewed as superseded by current main. No unique required behavior is missing: current code already includes backend-owned Workshop Profile persistence, schemas, `GET`/`PUT /api/settings/workshop-profile`, validation, unrelated-setting preservation, approved editable status, Settings UI with Save/Cancel, focused tests, documentation, and Markdown/PDF report-document integration that does not mutate existing generated documents. Actual GitHub state during this handoff: `open`; closure remains pending and is not claimed.

This documentation-only PR scope is limited to `README.md`, `docs/implementation-plan.md`, `state/current-focus.md`, `state/progress.md`, and `state/handoff.md`. It changes no runtime code, backend, frontend, migrations, dependencies, CI, tests, or smoke infrastructure.

Next runtime task: **A3.7 — Orders structured validation**. No future PR number exists yet. A3.7 must not include order schema changes, migrations, status workflow redesign, Production Readiness, Production Confirmation, inventory/production write-offs, cost/tax/margin implementation, responsive-table redesign, dependency or CI changes, or unrelated routes.

## 2026-07-18 — A3.7 Orders structured validation handoff

A3.7 is implemented in the current focused runtime branch for Order create/update only. Backend `OrderDraft.create()` now runs inside the write error boundary, so domain validation returns structured `422` DomainIssue responses while FastAPI/Pydantic `422`, positive-reference `404`, and inactive/lifecycle `409` boundaries remain separate. The Orders form uses shared `FormValidationState`, Russian field labels, explicit `recipe_source → source_type` mapping, targeted validation updates, mutation guards, duplicate-submit protection, authoritative saved Order responses before list refresh, and a separate post-save refresh warning.

PR #120 / A3.6 remains DONE at merge commit `4553536d2300ac93cb780cc07d3fe8a38ec1b5a6`; published runtime head `e148220ac9ad08a0fd952482a0b293f1f2d22bad`; exact-head smoke `PASS — FULL AUTOMATED SMOKE PASSED`. PR #121 synchronized project memory at `5c1edba2ca50b4a503d7dd44df2fdf7fda60aa6c`.

A3.7 was subsequently merged in PR #122 at `8c4a092d055fd221cb18da901cee9e90106b33a4` and is DONE. Production Readiness and Production Confirmation remain separate follow-up slices.

## 2026-07-19 — A3.8 Production Readiness feedback and lifecycle handoff

PR #122 / A3.7 is DONE at merge commit `8c4a092d055fd221cb18da901cee9e90106b33a4`. Its verified runtime head is `b44b80bd875ec184bbccfc376f1562ddf25fbb46`; the user-provided external smoke verdict is `PASS — FULL AUTOMATED SMOKE PASSED`. Treat that verdict as external evidence, not GitHub Actions evidence.

The current scope is A3.8 only. It extends the existing Order request-generation/transient-owner architecture with explicit readiness duplicate suppression and per-order attempt/result freshness. A valid cached result survives safe navigation, while a newer failed attempt, a changed Order, a wrong-order DTO, or a stale generation prevents Production Confirmation. Order-local edit/cancel/archive/reload conflicts are guarded only while the active readiness check owns loading; switching context invalidates and releases that transient presentation.

Readiness results keep backend-owned calculations and now group escaped messages by visible recipe/formula, component, lot, packaging, Order, or general context. Valid blocked results remain result DTOs. `404`, `409`, structured `422`, local connection failures, and unexpected failures use a separate retryable system-error state without raw exception, table, JSON, or internal-ID leakage.

Backend readiness remains read-only. Focused snapshots verify no ProductionBatch row, ProductionBatch ingredient/packaging row, ingredient StockMovement, packaging StockMovement, or Order lifecycle mutation for ready and blocked checks. No `POST /produce`, production confirmation, inventory write-off, reservation, FEFO, cost/tax/margin rule, schema, migration, dependency, CI, responsive table, or unrelated route change is in scope.

Pre-review automated evidence at published head `69da410bccfc7bf9c852ef5a807d039b4fa4a74d`: frontend form-validation `19/19 PASS`; targeted validation `62/62 PASS`; Order lifecycle `18/18 PASS`; build `PASS`; focused readiness/Orders backend `19/19 PASS`. Full backend matched clean base `8c4a092d055fd221cb18da901cee9e90106b33a4` at `480 passed, 5 failed`. That reviewed head also passed exact-head browser smoke as external local evidence, not GitHub Actions evidence.

Draft PR #123 now exists and remains IN REVIEW; A3.8 is not DONE. Human review found that readiness did not exclude already-pending production/cancel/archive writes in the reverse direction, readiness success borrowed `updated_at` at response completion, and readiness presentation lacked committed behavioral DOM/view coverage.

The correction stays on `codex/a3.8-production-readiness-lifecycle`: use explicit same-Order owners for production/cancel/archive, keep stale owner cleanup generation-safe, capture readiness Order revision/operation generation at request start, and test the extracted presentation without a new framework or dependency. A corrected published head must receive a completely new exact-head smoke; the earlier smoke cannot verify the correction. Keep PR #123 Draft. A3.9 Production Confirmation and A4 remain separate.

## 2026-07-19 — PR #123 persistent-write presentation follow-up

Reviewed published head `b6413f9b38710c1d3b8e231a52206d9a9dd7b9be` successfully closed the earlier readiness freshness, reverse same-Order exclusion, presentation test, escaping, and duplicate-request findings. Human review retained PR #123 in Draft because production/cancel/archive ownership was safely global in the start guard but unrelated Order controls still looked enabled, and cancel/archive did not expose honest pending copy or ARIA busy state.

The current correction preserves that global serialization. A single valid-owner helper now drives the persistent write guard, Order row/detail lifecycle rendering, Production Confirmation opening/submission, and explanatory text. A production/cancel/archive owner on Order A disables production/cancel/archive controls for Order B without disabling read-only navigation or safe unrelated readiness. The owning cancel/archive action renders `Отменяем…` / `Архивируем…`, native disabled, `aria-busy="true"`, and the existing danger style. Generation-bound cleanup still prevents stale callbacks from clearing a newer owner.

Keyboard-invoked readiness also keeps focus on a stable readiness-region anchor while the initiating control is disabled and after a system failure. It does not auto-focus the retry button; the next Tab reaches `Повторить проверку` without dropping back to `body`.

The previous exact-head smoke artifacts were not retained, and keyboard traversal was not completed against `b6413f9b38710c1d3b8e231a52206d9a9dd7b9be`; do not reuse or report that evidence as the final correction result. After publishing the new head, run the complete exact-head browser smoke and real Chrome/Chromium keyboard scenario, retain the Markdown/JSON/request/error/log/database/repository-clean bundle in an external archive, and update Draft PR #123 with the exact evidence. Missing retained evidence is `INCONCLUSIVE — RUNNER`; an unavailable browser environment is `INCONCLUSIVE — ENVIRONMENT`.

No backend readiness calculation, FEFO, density conversion, inventory policy, Production Confirmation domain behavior, production transaction, stock movement, Order backend lifecycle rule, schema, migration, dependency, CI, A3.9, or A4 change belongs in this correction.

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

## PR #124 A3.9 corrective handoff

Corrective scope is limited to reviewed Production Confirmation gaps: render failures without readiness, structured error extraction with `next_action`, uncertain-outcome reconciliation, Order A result retention after navigating to Order B, focus anchors, rollback assertions, and transaction lock audit. Do not run final browser smoke until the corrective head has human code review. Keep PR #124 Draft; do not merge or enable auto-merge.

## PR #124 A3.9 second corrective handoff

PR #124 remains the active A3.9 Draft PR on managed branch `codex-l6nqu0`. Previous reviewed published GitHub head `f29d8115586e528afec6d9ee2c5efd1fc4fb0a5d` still required correction. Exact base remains `c6d87df635a5cf7d063b43ffc16dc02d64e08103`. The current correction scopes SQLite `BEGIN IMMEDIATE` to Production Confirmation, adds an Order-bound reconciliation lifecycle with loading/duplicate/stale-response protection, fixes the generic transport-message presentation test, and keeps final exact-head browser smoke pending human code review. A3.9 remains IN PROGRESS; A4 remains separate.

## PR #124 A3.9 final presentation correction

PR #124 remains the active A3.9 Draft PR. Reviewed published GitHub head `f29d8115586e528afec6d9ee2c5efd1fc4fb0a5d` had one remaining presentation mismatch: Production Confirmation reconciliation was guarded in request logic but some controls still looked active. This correction keeps backend and transaction behavior unchanged, treats reconciliation as same-Order transient busy presentation for Production Confirmation and Order detail actions, and keeps final browser smoke pending smoke review. A3.9 remains IN PROGRESS; A4 remains separate.


## 2026-07-19 — A4.1 responsive table containment

Slice A3 is marked complete based on the product owner's confirmed A3.9 Production Confirmation tests and smoke verification. PR #124 is the completed A3.9 implementation baseline; this is external product-owner evidence, not GitHub Actions evidence.

Slice A4 is now active. Current runtime work is A4.1: establish a small shared responsive table containment contract and prove it on `/ingredient-lots`. The scope is frontend layout containment only: shrinkable content/card/table-wrapper ancestors, local table scrolling, row-action reachability, and visible focus outlines. `/orders`, `/clients`, `/inventory`, and `/packaging-items` remain separate A4 follow-ups, with `/inventory` and `/packaging-items` inspected only for obvious passive shared-CSS regressions.

## A4.2 responsive Orders containment handoff

A4.1 is merged and DONE via PR #125 (merge commit `50c44ff0919401d51c165d6ebec1266c688bfb08`, runtime head `effb5ee270c9fbddc777e57c41ad0b53acd77f9d`). The active focused slice is A4.2 for `/orders` responsive containment. This slice must remain presentation-only: no Order lifecycle, readiness, production confirmation, reconciliation, cancellation, archiving, backend, API, schema, migration, stock, FEFO, cost, tax, or margin changes. `/clients`, `/inventory`, and `/packaging-items` remain future A4 follow-ups.

## 2026-07-20 — A4.3 Clients responsive containment handoff

PR #126 / A4.2 is merged and DONE. Merge commit: `4487e4044d89d88538226c5b36543e6009f279f9`; runtime head: `010bd1bf3791dd6a6d754ea2ed0efdcd2ab564d3`. Product-owner manual responsive verification passed at `1440×900`, `1024×768`, `768×900`, and `390×844`.

The active focused slice is A4.3 for `/clients` responsive containment. Keep it presentation-only: no Client API payload changes, backend/domain/schema/migration changes, wish/feedback lifecycle changes, ClientRecipe semantics changes, mutation guard changes, audit behavior changes, or unrelated route implementation changes.

`/inventory` and `/packaging-items` remain future A4 follow-ups. Slice A4 is not complete yet.

## 2026-07-20 — A4.4a Inventory responsive containment started

- PR #127 / A4.3 is merged and DONE. A4.3 runtime head: `1f6930d8f2e3367372a384a51e7d04a3a7c96bee`; merge commit: `255703d26d9e166f00f2c9ba3030cf4bc41fe044`.
- Product-owner manual exact-head smoke for A4.3 passed.
- A4.4a `/inventory` is active and scoped to responsive containment of the read-only Inventory workspace.
- `/packaging-items` remains a separate A4.4b task.
- Slice A4 remains incomplete.

## 2026-07-20 — A4.4b Packaging Items responsive containment handoff

- Exact current base SHA: `bc5082f6b6e1e3796f269ec317fcbb1184ca5c83` (PR #129 merge commit).
- A4.4a accepted `/inventory` runtime head: `4a39c815ac8fdb73bc0c7dd5f88d0779e9eb6dd5`; merge commit: `b89a40f2651f3e2ae7174cfdb7989ddf03a6221e`; exact-head responsive smoke passed.
- PR #129 baseline repair runtime head: `413ae2d5e94f7efc0e7c8c9dc6a86f6aa1a511f6`; merge commit: `bc5082f6b6e1e3796f269ec317fcbb1184ca5c83`.
- A4.4b scope is presentation-only responsive containment for `/packaging-items`: stable route hook, route-scoped CSS containment, safe wrapping for long Packaging catalog content, and preserved local table scrolling/reachability.
- Pending evidence for the A4.4b PR: exact published-head browser smoke against the GitHub PR head with isolated database/profile and passive `/ingredients` regression.
- Next task after A4.4b merge: run the separate final cross-route A4 responsive regression before marking Slice A4 complete.

## 2026-07-21 — B3.1 Dashboard and Onboarding feedback handoff

Current branch implements the first small batch of Slice B3 from baseline `2ce5a4d7ba099603b733e7f2836f417da0614605` (PR #132 merge). Remote fetch was unavailable because no `origin` remote is configured in this runner; the clean local object matched the expected SHA and merge message before work began.

Implemented scope:

- Dashboard initial load and manual refresh now use a small dependency-free lifecycle helper for active request ownership, duplicate refresh rejection, stale response rejection, stale feedback clearing, silent initial success, polite manual-refresh success, assertive load/refresh failure, and refresh-warning separation while preserving previously loaded cards.
- Onboarding start, complete-step, skip, and reset mutations use the same helper boundary for duplicate mutation rejection, busy/disabled controls, authoritative mutation responses, separate mutation error versus refresh warning state, polite success, assertive failure, and controlled focus recovery when the triggering control disappears.
- Help remains passive. The new dependency-free Help regression helper covers search, category filtering, reset, article selection, and related-section navigation as non-mutating/non-feedback-owning behavior.

Verification in this runner:

- Frontend focused suites passed, including the new B3.1 Dashboard/Onboarding and Help suites run independently and twice.
- Frontend production build passed.
- Focused backend read/mutation tests relevant to onboarding, orders, alerts, purchases, production history, and backup status matched the known baseline failures in backup sanitization and manual purchase-suggestion smoke.
- Full backend suite on exact base and final head both collected 496 tests with 492 passed and the same 4 failures: backup reason sanitization, export reason sanitization, import draft error count, and manual purchase suggestion smoke. Branch-only backend failure delta: 0.
- Browser smoke was not completed in this runner because no Chrome/Chromium/Playwright browser executable is available. Do not claim B2 browser presentation complete or B3.1 ready-for-merge until exact published-head browser smoke passes externally.

Next step after this PR: B3.2 — Alerts and Purchases feedback migration. Do not broaden B3.1 into other route groups.

## 2026-07-21 — B3.1 correction pass review gaps

Correction pass for PR #133 keeps B3.1 ACTIVE and not merge-ready until external exact published-head browser smoke passes. It closes review findings around stale onboarding feedback, onboarding GET ownership, stale-readable onboarding state, valid empty Dashboard snapshots, route-owned announcements/focus, real focus-policy tests, real stale Dashboard/onboarding callback tests, and runtime-backed Help helper usage.

Automated evidence in this correction pass: focused frontend suites passed sequentially (`form-validation` 19/19, `targeted-validation-update` 62/62, `order-mutation-lifecycle` 32/32, `order-readiness-presentation` 15/15, `dashboard-onboarding-feedback` 15/15, `help-passive-regression` 3/3), the two new B3.1 suites passed a second time, and `npm --prefix frontend run build` passed. Full backend suite on base `2ce5a4d7ba099603b733e7f2836f417da0614605` and corrected head both collected 496 tests with 492 passed and the same 4 known baseline failures; branch-only backend failure delta is 0.

Browser smoke is intentionally pending for the next separate step after review corrections. B2 browser presentation evidence remains incomplete until that exact published-head smoke passes. B3.2 Alerts and Purchases remains next after B3.1 merge. No future PR number is recorded.

## 2026-07-21 — B3.1 retry-control wiring correction handoff

External exact-head smoke against PR #133 published head `fb7a4e5c2dd4757b61fd4be07c8c49003188b35b` found one product failure: Desktop Dashboard initial-load failure rendered an explicit `Повторить` retry button, but clicking it did not send the expected five Dashboard source GET requests.

The confirmed root cause was narrow event binding in `bindEvents`: multiple controls can render with `data-action="reload-dashboard"` (header refresh plus initial-error retry/stale retry), while a single `querySelector` only attached the handler to the first one. This correction adds a small shared action-control binding helper and uses it for every rendered Dashboard reload/retry control and every rendered onboarding refresh control. The Dashboard and onboarding lifecycle helper remains responsible for duplicate-request rejection, stale ownership, route-owned announcements, and safe stale readable data.

B3.1 remains ACTIVE, not DONE, and not merge-ready. Browser smoke must be rerun externally against the new published PR #133 head after this correction is pushed. B3.2 Alerts and Purchases remains next after B3.1 merge; do not begin it inside B3.1.

## B3.2a Alerts shared feedback lifecycle handoff
- Scope: Alerts-only shared feedback lifecycle for `/alerts`, including list reads, refreshes, filters, regeneration, resolve/dismiss actions, route ownership, visible feedback, announcements, final focus recovery, and all reload-control binding.
- Implementation summary: added a dependency-free Alerts lifecycle module used by runtime and focused tests; kept backend alert generation and mutation rules authoritative; applied resolve/dismiss DTOs locally without an automatic list GET.
- Tests actually run: `npm --prefix frontend run test:alerts-feedback`; `npm --prefix frontend run build`.
- Browser smoke still pending: PENDING — EXTERNAL EXACT-PUBLISHED-HEAD BROWSER SMOKE REQUIRED AFTER PUBLICATION.
- Next separate slice: B3.2b Purchases shared feedback lifecycle.

## B3.2a correction handoff for PR #134
- Scope: corrective update for PR #134 only; Alerts route ownership, final focus recovery, invalid DTO recovery, regeneration refresh-warning announcement, and real focused tests.
- Implementation summary: route ownership is centralized for startup/navigation/popstate; resolve/dismiss focus selection happens after final render; wrong current-owner DTOs clear the lock with refresh-before-retry copy; stale DTOs remain ignored.
- Tests actually run: full required frontend checks, frontend build, base backend suite, corrected-head backend suite, and repository hygiene checks were run locally; branch-only backend failure delta is zero.
- Browser smoke still pending: PENDING — EXTERNAL EXACT-PUBLISHED-HEAD BROWSER SMOKE REQUIRED.
- Next separate slice: B3.2b Purchases shared feedback lifecycle.

## B3.2a second correction handoff for PR #134
- Scope: corrective update for PR #134 only; Alerts leave-and-return active-operation races, regeneration follow-up ownership, and busy reset controls.
- Implementation summary: re-entering Alerts invalidates stale owners and requires current-visit reconciliation; regeneration follow-up presentation is based on the follow-up read result; empty-state reset buttons receive the busy disabled state.
- Tests actually run: full required frontend checks, frontend build, base backend suite, corrected-head backend suite, and repository hygiene checks were run locally; branch-only backend failure delta is zero.
- Browser smoke still pending: PENDING — EXTERNAL EXACT-PUBLISHED-HEAD BROWSER SMOKE REQUIRED.
- Next separate slice: B3.2b Purchases shared feedback lifecycle.

## B3.2a final settlement-order correction handoff for PR #134
- Scope: corrective update for PR #134 only; detached Alerts reads versus detached mutations, settlement-ordered re-entry reconciliation, away-settled operation reconciliation, and busy reset presentation evidence.
- Implementation summary: re-entering Alerts during a detached mutation now waits in a neutral busy state until that mutation settles, then consumes exactly one reconciliation GET for the current visit or the next Alerts entry; detached reads remain safe for immediate fresh GETs.
- Tests actually run: required frontend checks, frontend build, base backend suite, corrected-head backend suite, and repository hygiene checks are recorded in the PR evidence for this correction.
- Browser smoke still pending: PENDING — EXTERNAL EXACT-PUBLISHED-HEAD BROWSER SMOKE REQUIRED.
- Next separate slice: B3.2b Purchases shared feedback lifecycle.

## B3.2a identity-owned detached mutation handoff for PR #134
- Scope: corrective update for PR #134 only; identity-bearing detached Alerts mutation ownership, stale-read isolation, lossless reconciliation, regeneration counter preservation, and double-GET prevention.
- Implementation summary: leaving Alerts moves the exact active mutation owner into detached state; only a matching request ID, kind, and alert ID can settle it; read callbacks cannot settle mutations; reconciliation is consumed only by an accepted current-visit GET.
- Tests actually run: focused Alerts tests include asynchronous callback-routing races with injected GET/POST counters plus the required frontend regression suites, build, backend base/head comparison, and repository hygiene checks.
- Browser smoke still pending: PENDING — EXTERNAL EXACT-PUBLISHED-HEAD BROWSER SMOKE REQUIRED.
- Next separate slice: B3.2b Purchases shared feedback lifecycle.

## B3.2b Purchases shared-feedback lifecycle handoff
B3.2a Alerts is merged into main. Accepted Alerts head: `ac8656c2357b50fa755fef58349501d072e298a7`; merge commit / B3.2b base: `4692bdfa4d5171fb270687cb385a37571a8e9e2d`.

Current B3.2b scope adds a Purchases-only shared-feedback lifecycle module and a small Purchases runtime coordinator. The lifecycle owns read request identity, snapshot server filters, local search, identity-bearing active/detached mutations, authoritative DTO validation, mutation-vs-refresh separation, and durable reconciliation obligations. Marking purchased remains explicit UI feedback only and does not create stock receipt, ingredient lots, packaging movements, or order changes.

Automated evidence collected on this branch:
- `npm --prefix frontend run test:purchase-suggestions-feedback` — run 1: obsolete eight-test suite passed.
- `npm --prefix frontend run test:purchase-suggestions-feedback` — run 2: obsolete eight-test suite passed.
- `npm --prefix frontend run test:alerts-feedback` — 56 passed.
- Related frontend suites run: dashboard/onboarding 17 passed; form-validation 19 passed; targeted-validation-update 62 passed; order-mutation-lifecycle 32 passed; order-readiness-presentation 15 passed; help-passive-regression 3 passed.
- `npm --prefix frontend run build` passed.
- `cd backend && pytest -q app/tests/test_purchase_suggestions.py` matched known baseline failure: 10 passed, 1 failed (`test_manual_api_smoke`).

Browser smoke status: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE. This is not a browser-smoke pass; a full Block B integration browser smoke remains mandatory after all B slices.

Next expected step: human review of this focused B3.2b PR, then continue remaining Block B slices; do not run per-PR external browser smoke for this slice unless the product owner changes the temporary sequencing decision.

## B3.2b PR #135 runtime correction handoff
The first reviewed PR #135 head was blocked because it added Purchases lifecycle modules but did not migrate the real `/purchase-suggestions` runtime. The route still used legacy direct list/mutation Promise chains, coupled list loading to reference data, and allowed reconciliation behavior that could run while the route was away.

Correction work now wires the Purchases runtime coordinator into `frontend/src/main.ts`, routes Purchases list reads and mutations through lifecycle ownership, derives busy state from lifecycle presentation, detaches active mutations on route leave, keeps reconciliation route-owned, and separates manual-form reference loading from list loading. Mark purchased still only closes the recommendation and does not create stock records.

Current automated evidence on the correction head:
- `npm --prefix frontend run test:purchase-suggestions-feedback` run 1: obsolete eight-test suite passed.
- `npm --prefix frontend run test:purchase-suggestions-feedback` run 2: obsolete eight-test suite passed.
- `npm --prefix frontend run build`: passed.

Browser smoke remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE. This is not a browser-smoke pass.

## B3.2b PR #135 route-ownership and test-evidence correction handoff
The reviewed PR #135 head `0cf2992329b5586d898da09c5de4b9fb820da056` had connected the Purchases runtime to primary list and mutation flows, but missed production `leave()` across all navigation paths and retained shared-state announcement reconstruction plus the rejected eight-test omnibus suite.

This correction adds one Purchases route-transition helper used by runtime navigation, browser `popstate`, and initial route ownership. The transition calls Purchases `enter()` only on non-Purchases → Purchases, calls `leave()` only on Purchases → non-Purchases, and preserves same-section/non-Purchases transitions without duplicate route generations. Purchases reference ownership is separated into a production-shared controller with independent ingredient and packaging owners; reference failures preserve the purchase list and manual draft. Purchases control binding is moved behind a production-shared helper that binds every rendered duplicate control while honoring disabled states.

Completion feedback is now result-owned: lifecycle finish results carry the exact message for that completion, and the runtime announces only `result.message` instead of rebuilding announcements from retained visual feedback fields. Detached and stale completions do not announce or focus, and reconciliation remains route-owned.

Automated evidence on the correction head:
- `npm --prefix frontend run test:purchase-suggestions-feedback` run 1: 84 passed, 0 failed, 0 skipped.
- `npm --prefix frontend run test:purchase-suggestions-feedback` run 2: 84 passed, 0 failed, 0 skipped.
- Related frontend regressions passed: Alerts 56, Dashboard/Onboarding 17, form-validation 19, targeted-validation-update 62, order-mutation-lifecycle 32, order-readiness-presentation 15, help-passive-regression 3.
- `npm --prefix frontend run build` passed.
- Focused backend Purchases suite matched known baseline: 10 passed, 1 failed (`app/tests/test_purchase_suggestions.py::test_manual_api_smoke`).
- Complete backend suite matched known baseline: 492 passed, 4 failed, 0 skipped.

Publication note: shell GitHub verification was unavailable because `gh` is not installed and this checkout has no usable GitHub remote. Block B smoke remains deferred: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.


## B3.2b PR #135 neutral-feedback ownership correction handoff
The reviewed published head `5dc1f247f5520737930a31e2dae5b48e1d06d1ed` still allowed the Purchases neutral message `Завершаем предыдущее действие и проверяем список…` to persist after detached settlement or reconciliation terminal states. It also contained focused tests with names that overstated direct production evidence.

This correction clears detached/reconciliation neutral feedback at detached settlement, reconciliation success, and reconciliation failure without clearing retryable reconciliation obligations. The Purchases runtime still announces only result-owned completion messages. Production now uses shared helpers for feedback item presentation and form-state completion/guard behavior, so tests can verify rendered neutral disappearance and complete manual/edit draft preservation without duplicating runtime logic.

Focused Purchases tests were expanded to 108 independently named checks. New coverage includes rendered neutral disappearance, retryable reconciliation failure then success, stale reconciliation protection, source-level navigation wiring evidence, production form-state draft preservation/cleanup, public reference-controller older/newer ownership sequences, and corrected binding rerender behavior. Frontend regression suites and build passed; backend verification matched the accepted baseline with branch-only failure delta 0.

Publication note: this local environment still lacks `gh` and a usable GitHub `origin`, so shell publication could not verify a new published head. Browser smoke remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.


## B3.2b PR #135 composition-evidence correction handoff
The reviewed published head `9a95b310d4e3d414052e2f565eecf1efd938f450` still had several focused tests whose form/reference assertions used disconnected local objects. This correction replaces those cases with a composed Purchases harness that connects `PurchaseSuggestionsFeedbackLifecycle`, `createPurchaseSuggestionsRuntime`, shared manual/edit form state, `completeManualPurchaseDraft`, `completeEditPurchaseDraft`, reference-data ownership, route ownership, deferred requests, and render/announce/focus counters.

Manual and edit failure, invalid DTO, stale newer-draft, detached settlement, and valid success tests now assert the connected production form state that the runtime callbacks can actually mutate. Reference side-effect tests now assert the real lifecycle snapshot, applied filters, local search, mutation owner, reconciliation obligation, and manual draft while ingredient/packaging requests fail or settle. Settings target navigation now has source-contract coverage through `navigateToSection`.

Focused Purchases tests now pass with 116 checks. Browser smoke remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-22 — B3.3 handoff: local artifacts and reports shared-feedback lifecycle

### Route contract matrix

| Route | Initial reads | Refresh reads | Mutations | Follow-up reads | Retained result behavior |
|---|---|---|---|---|---|
| Backups | `GET /api/backups/status` + `GET /api/backups` | same GET pair | `POST /api/backups` | same GET pair after accepted create | previous list/status remain on refresh failure; returned backup remains as last-created |
| Exports | `GET /api/exports/status` + `GET /api/exports` | same GET pair | `POST /api/exports` | same GET pair after accepted create | previous list/status remain on refresh failure; returned export remains as last-created |
| Report Documents | `GET /api/report-documents/status` + `GET /api/report-documents` | same GET pair | `POST /api/report-documents/reports/overview` for Markdown/PDF | same GET pair after accepted generation | previous documents/status remain on refresh failure; returned document remains as last-created |
| Reports | five read-only report GETs: overview, inventory, orders, production, finance | same five GETs | none | none | previous report snapshot remains on refresh failure |

### Implemented ownership model

- `frontend/src/local-artifacts-reports-feedback.ts` owns shared request IDs, route generations, read owners, mutation owners, detached settlement safety, loaded snapshots, retained last-created artifacts, refresh warnings, and result-owned completion messages.
- `frontend/src/main.ts` wires Backups, Exports, Report Documents, and Reports into the shared route-ownership transition used by app navigation, `popstate`, startup/direct route, Help/settings/onboarding related navigation, sidebar, and `data-nav-section` actions.
- Successful mutation followed by failed refresh remains success plus warning; recovery refresh uses GET only and does not repeat POST/generation.
- Detached mutation settlement does not render, announce, or move focus for an absent route.
- Reports remains read-only; route entry and refresh do not regenerate alerts, purchases, documents, backups, or exports.

### Verification notes

- Known backend baseline failures remain: `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`, `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`, `app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`, `app/tests/test_purchase_suggestions.py::test_manual_api_smoke`.
- Local head/published head must be verified after push; this runner had no GitHub remote or `gh`.
- Historical next-slice note superseded by the combined B3.4+B3.5 slice recorded below.
- Block B smoke status: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.3 PR #136 correction handoff

- PR #136 is merged; B3.3 is complete at merge commit `e7c2d97473070f361052325fd6476208629af1cc`.
- Historical correction branch: `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`; its earlier base was `b11160cc1a06df24fa6666969154c37389e6ab65`.
- Runtime correction: detached mutations are irreversible and require read reconciliation; ambiguous outcomes lock create/generate until authoritative GET reconciliation; success, warning, and error remain separate; production focus callbacks are invoked only for accepted current-route completions.
- Test correction: the focused B3.3 suite now uses production runtime and route modules with deferred API dependencies, render/announcement/focus recording, and exact GET/POST call assertions.
- Backend remains unchanged; known baseline failures are unchanged.
- Historical next-slice note superseded by the combined B3.4+B3.5 slice recorded below.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.4+B3.5 implementation handoff

- PR #136 is merged and B3.3 is complete at merge commit `e7c2d97473070f361052325fd6476208629af1cc`.
- The active branch is `codex/b3.4-b3.5-core-workspace-feedback`, based on the same verified `main` SHA.
- Formula/Client coverage includes Recipe Template list/detail/create, rendered recipe category/tag operations, immutable Recipe Version list/detail/create with complete composition, backend calculation GET, Client list/related/create/update/deactivate, ClientRecipe list/detail/create/composition/deactivate/restore, Wish list/create/status/archive, and Feedback list/create.
- Inventory/Catalog coverage includes composed read-only Inventory overview/balances, Ingredient list/create/update/deactivate/category/tag operations, Ingredient Lot list/references/create/update/deactivate, selected-lot StockMovement history/balance plus append-only create, and Packaging list/create/update/deactivate/category/tag operations.
- The two bounded production lifecycle families own route generations, request identity, stale/detached rejection, snapshots, DTO boundaries, reconciliation locks, one-shot GET queues, announcements, focus, binding, and presentation.
- StockMovement creation performs exactly one POST. Ambiguous or invalid results lock repetition; reconciliation uses authoritative movement/balance GETs only, never loops, and remains manually repeatable.
- Accepted mutation success is not downgraded when its follow-up GET fails; definite failures preserve drafts; obsolete same-route reference requests are discarded silently.
- Unsupported paths remain absent: RecipeTemplate update, in-place RecipeVersion editing, persisted RecipeIngredient CRUD, ClientRecipe calculation, Feedback update, Packaging StockMovement, Orders, Production, backend expansion, and migrations.
- External smoke-authoring contract not stored in the repository; not required for this smoke-deferred runtime slice.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
- Next slice: B3.6 — Order-to-production shared-feedback lifecycle.

## 2026-07-23 — B3.3 PR #136 DOM binding and reconciliation correction handoff

- Correction scope remains `/backups`, `/exports`, `/report-documents`, and `/reports` only.
- B3.3 bindings are extracted to a production binding helper used by `main.ts` and focused tests; invalid compound selectors and duplicate focus-key attributes are removed from B3.3 markup.
- Detached mutation reconciliation now distinguishes provisional reads from post-settlement authoritative reads and queues at most one post-settlement reconciliation GET when needed; POST is never retried automatically.
- The production runtime owns lifecycle construction, focus configuration, request-owned announcements, reconciliation locks, and result-owned feedback cleanup.
- Reports remains read-only in production and in the focused harness.
- GitHub PR body was not updated by this correction. Browser smoke remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.3 PR #136 remaining reconciliation/result-boundary correction handoff

- PR: #136; branch `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`; base `main`; base SHA `b11160cc1a06df24fa6666969154c37389e6ab65`; published head before this correction `aae116536c2b68dec0808ccd0cae099f325e09ae`.
- Reconciliation invariant: a detached-mutation obligation may clear only after an accepted reconciliation GET that started after the detached mutation definitely settled. Provisional GET success before settlement keeps the lock; provisional GET failure after settlement starts exactly one queued authoritative GET; failed authoritative GET does not loop and leaves manual retry available.
- Runtime result boundary: Export `entity_counts` and Report Document reason clearing are committed only after validated, owned, current-route mutation success. Invalid, ambiguous, stale, detached, and definite-failure completions do not apply those route-specific side effects.
- Focus contract: create forms for Backups, Exports, and Report Documents are focusable with `tabindex="-1"`; invalid DTO recovery focuses refresh/reconciliation controls instead of disabled create controls.
- Focused B3.3 tests include ordering scenarios, accepted-only route side effects, restored initial/stale/absent-route and same-route transition evidence, binding selector contracts, and read-only Reports coverage.
- GitHub PR body was not updated by this correction. Browser smoke remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.3 PR #136 reconciliation retry ownership correction handoff

- PR: #136; branch `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`; base `main`; base SHA `b11160cc1a06df24fa6666969154c37389e6ab65`; published head before this correction `1e8a9fa8f063346cab5cb28c24c6eacf38e526a1`.
- Corrected invariant: `reconciliationRequired` is the safety lock for create/generate controls; automatic reconciliation GET execution is permitted only when `pendingReconciliationAfterRead` represents one unconsumed post-settlement queue.
- Snapshot-aware ordering tests now create a readable initial snapshot before mutation, then cover provisional failure before settlement, provisional failure after settlement, authoritative failure without loop, authoritative success without extra GET, and POST count staying at one.
- Runtime result boundary now exposes `knownMutationSuccess`; `commitAccepted` and `applyCreated` run only for validated known-success mutation results after route ownership is confirmed.
- GitHub PR body was not updated by this correction. Browser smoke remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — B3.4+B3.5 verification handoff

- Formula/Client focused tests: 34/34 passed twice.
- Inventory/Catalog focused tests: 41/41 passed twice.
- Frontend regressions: 19 form-validation, 62 targeted-validation, 32 order-mutation, 15 order-readiness, 17 Dashboard/Onboarding, 3 Help, 56 Alerts, 116 Purchases, and 32 Local Artifacts/Reports checks passed.
- Frontend build passed.
- Focused backend Formula/Client/Inventory/Catalog suites: 190 passed.
- Complete backend comparison: 496 collected, 492 passed, 4 accepted baseline failures, 0 skipped; branch-only failure delta 0.
- No browser smoke was run or claimed. Status remains: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
- Next slice remains B3.6 — Order-to-production shared-feedback lifecycle.

## 2026-07-23 — PR #137 ownership correction handoff

- PR #137 remains open, non-draft, and under review on `codex/b3.4-b3.5-core-workspace-feedback`; do not create a replacement PR or branch.
- Published head before this correction: `8c58e5e1466f05aa27950e2157f597e3fa4414b3`.
- The correction closes the reviewed same-route context defect by making reads and mutations entity-context-owned in addition to route, operation, generation, and request identity.
- The selected policy is explicit supersession: a read for Context B removes the prior same-operation Context A owner, while a duplicate for the exact same context remains rejected.
- Production runtime callbacks discard obsolete read owners or settle obsolete mutation owners before returning, so a later request for the same operation/context is accepted.
- Reconciliation is a structured domain-mapped obligation. Only the required validated operation and exact context at the obligation epoch, after mutation settlement, can clear it.
- StockMovement create remains exactly one POST. Its obligation records `stock-movement-create`, `lot:<originalLotId>`, and `stock-reconciliation` for the same lot. Only the composed history and balance GET result for that original lot can unlock creation.
- Route re-entry and general StockMovement references do not unlock detached work. One authoritative original-lot GET may run after settlement; failure does not loop, and the recovery control continues to target the original obligated lot.
- No backend production, schema, migration, dependency, lockfile, Orders, Production, unsupported mutation, or smoke-infrastructure change belongs to this correction.
- Final pre-publication verification: Formula/Client 47/47 twice; Inventory/Catalog 51/51 twice; all required frontend regressions and build passed; focused backend domains 186/186; complete backend 496 collected, 492 passed, the same 4 accepted failures, 0 skipped, branch-only delta 0.
- B3.4+B3.5 remains under review; B3.6 remains next.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-23 — PR #137 detached settlement and recipe snapshot correction handoff

- Continue only on PR #137 and `codex/b3.4-b3.5-core-workspace-feedback`; the published head before this correction was `b95b0b293f6f381495fa9e08d36b1ad27a214252`.
- Both bounded production runtimes now expose an exactly-once settlement callback for every accepted mutation request. A rejected start neither issues the request nor invokes settlement.
- Settlement only restores route-local UI availability. DTO application, form/draft reset, selection/list updates, announcements, focus, and reconciliation clearing remain owned by accepted validated lifecycle results.
- Direct RecipeTemplate/RecipeVersion/Client and Ingredient/Ingredient Lot/Packaging handlers use the shared route-local UI finalizer so detached completion cannot strand a route-level saving flag.
- ClientRecipe create/composition/deactivate/restore settlement can resume the existing exact GET-only reconciliation loader after route return; user drafts remain intact unless a current-context validated success explicitly owns their reset.
- RecipeTemplate opening now requests template detail and that template's version list together and commits one coherent snapshot only after both responses validate. Partial failure preserves the prior coherent snapshot.
- The independent RecipeVersion reconciliation path remains `recipe-version-list` with context `template:<id>` and cannot update versions for a different selected template.
- StockMovement safety is unchanged: one POST, original-lot obligation, exact history-plus-balance GET validation, at most one post-settlement automatic attempt, no loop, and manual original-lot retry.
- Final pre-publication verification: Formula/Client 60/60 twice; Inventory/Catalog 62/62 twice; all required frontend regressions and build passed; focused backend domains 186/186; complete backend 496 collected, 492 passed, the same 4 accepted failures, 0 skipped, branch-only delta 0.
- B3.4+B3.5 remains under review; B3.6 remains next. Do not claim browser smoke.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-24 — B3.6 implementation handoff

### Repository state

- PR: #138
- Branch: `codex/b3.6-order-production-feedback`
- Base `main` SHA: `10e985229e8020fcf98c67427cde889b5cd934f8`
- Reviewed runtime head before this documentation commit: `a02d5a89f56421ab55f3d75c2ef4699a6a4946a2`

### Commit history

- `32cec36 Add Order-to-production shared feedback lifecycle`
- `a02d5a8 Prevent cross-order production reconciliation loss`

### Runtime scope

- Order list and refresh.
- Atomic Order reference reads.
- Exact Order detail reads.
- Order create/update.
- Cancel/archive.
- Production readiness.
- Production Confirmation.
- Exactly one production POST per accepted confirmation.
- Production-history handoff.
- Exact original-Order GET-only reconciliation.
- Shared neutral, success, warning, and error feedback.
- Request-owned announcements.
- Route/context-owned focus.
- Exactly-once accepted request settlement.

### Reconciliation safety

- Uncertain or untrusted production outcomes create one exact originating-Order reconciliation obligation.
- Another Order or later production generation cannot replace an existing obligation.
- While any obligation remains unresolved, Production Confirmation and the production POST are globally blocked.
- Unrelated Orders remain readable.
- Unrelated readiness checks may remain available, but they cannot authorize production while the global lock exists.
- Automatic reconciliation is GET-only, runs at most once, and never loops.
- Reconciliation never retries production.
- Manual reconciliation remains available only for the originating Order.
- Only the exact coherent originating Order plus its exact ProductionBatch clears the production lock.
- Exact reconciliation endpoints:
  - `GET /api/orders/{original_order_id}`
  - `GET /api/orders/{original_order_id}/production-batch`

### Feedback and presentation safety

- Neutral, success, warning, and error feedback are mutually controlled.
- Known mutation success remains success when a follow-up refresh fails.
- Passive reads do not announce action success.
- Stale, detached, wrong-context, partial, invalid, or mismatched callbacks cannot present, announce, move focus, or clear reconciliation.
- Backend production semantics remain unchanged.

### Verification evidence

- Order production feedback: 21/21 PASS, repeated twice.
- Order mutation lifecycle: 32/32 PASS, repeated twice.
- Order readiness presentation: 15/15 PASS, repeated twice.
- Form validation: 19/19 PASS.
- Targeted validation: 62/62 PASS.
- Formula/Client Workspace: 60/60 PASS.
- Inventory/Catalog Workspace: 62/62 PASS.
- Core Workspace wrapper: 122/122 PASS.
- Frontend build: PASS.

Previously accepted evidence for unaffected suites was not rerun for the frontend-only correction:

- Dashboard/Onboarding: 17/17 PASS.
- Help passive regression: 3/3 PASS.
- Alerts: 56/56 PASS.
- Purchases: 116/116 PASS.
- Local Artifacts/Reports: 32/32 PASS.

Backend was not rerun for the frontend-only correction.

- Preserved focused backend evidence: 95/95 PASS.
- Preserved complete backend evidence: 496 collected, 492 passed, 4 known baseline failures, 0 skipped.
- Branch-only backend failure delta: 0.

The known baseline failures remain:

- `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
- `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
- `app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`
- `app/tests/test_purchase_suggestions.py::test_manual_api_smoke`

### Current acceptance state

- Runtime exact-head review passed for `a02d5a8`.
- The cross-Order production reconciliation blocker is closed.
- This documentation commit aligns project memory with the published and reviewed runtime state.
- B3.6 remains not DONE.
- PR #138 must not be merged before the full Block B exact-head integration smoke is reviewed.
- Run the smoke once against the final PR head after this documentation commit.
- Smoke status: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## 2026-07-26 — Authoritative B3 closure and B4.1 handoff

### Repository and merge state

- Current `main`: `c33e7f32decabe74de68051ccdc9e87d75c58cb6`.
- PR #138 — `B3.6 — Order-to-production shared-feedback lifecycle`:
  - accepted runtime head: `a8cf9d3e21aa46af3f9b2837a44b918cad638910`;
  - merge commit: `bac8672ecb04c96e25bf00c50cfba07f79eadb99`.
- PR #139 — `Fix Backups page responsive containment`:
  - accepted runtime head: `9ee94810f4dddbc03faf8c7cdbe188faa43a4e72`;
  - merge commit: `c33e7f32decabe74de68051ccdc9e87d75c58cb6`.
- B3 implementation and its deferred full integration-smoke gate are complete. Block B remains active through B4, beginning with B4.1. The earlier pending-smoke wording is superseded by this handoff; accurate historical entries remain unchanged.

### Accepted full integration smoke for the implemented B3 scope

- Exact tested and published head: `9ee94810f4dddbc03faf8c7cdbe188faa43a4e72`.
- Exact checked-out head matched the tested head.
- Verdict: `PASS — FULL AUTOMATED SMOKE PASSED`.
- Runner exit code: `0`.
- Repository clean after smoke: `true`.
- PR head unchanged after smoke: `true`.
- Backend branch-only failure delta: `0`.
- Isolated database migrations passed.
- Frontend production build passed.
- All required focused and regression frontend suites passed.
- Unexpected console errors: `0`.
- Unexpected HTTP failures: `0`.
- Request failures: `0`.

### Scenario summary

- Scenario A: isolated seed and backend cross-module reads passed.
- Scenario B: Dashboard, onboarding, Help Center, and route matrix passed.
- Scenario C: alerts, purchase suggestions, backups, exports, and report documents passed.
- Scenario D: blocked production readiness could not start production.
- Scenario E: normal Order production was exactly once and transactional.
- Scenario F: uncertain production created the global production lock; another Order could not replace the originating obligation; exact coherent reconciliation unlocked production.
- Scenario G: narrow viewport and keyboard focus remained usable, including corrected Backups responsive containment.
- Scenario P1: restart preserved produced Orders, ProductionBatch records, and local artifacts.
- The `502 Bad Gateway` in Scenario F for `drop-production-response` was intentional fault injection, correctly classified as expected, and was not a product failure.

### Known backend baseline failures

These remain unresolved separate findings and are not regressions from PR #138 or PR #139:

1. `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
2. `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
3. `app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`
4. `app/tests/test_purchase_suggestions.py::test_manual_api_smoke`

Do not describe these as fixed and do not correct them inside B4.1.

### Next task boundary

The only active next runtime slice is `B4.1 — Safe GET timeout and recovery foundation`.

- Use the existing Dashboard read lifecycle as the initial pilot.
- Treat all required Dashboard source GET requests as one composed read owner/request generation, and commit a new snapshot only after every required result for that generation validates successfully.
- A required-source timeout or failure must not commit a partial or mixed snapshot. A refresh timeout preserves the previous coherent snapshot where safe; an initial timeout without one presents explicit recoverable failure.
- Manual retry creates a clean new composed generation. Late individual-source callbacks cannot mutate Dashboard state, feedback, announcements, focus, or busy state; duplicate starts remain rejected and busy state settles exactly once.
- Reuse `DashboardOnboardingFeedbackLifecycle` and the current API client boundary; do not create a second lifecycle system or perform a global fetch rewrite.
- The runtime PR must choose, document, and test whether its timeout deadline applies to the whole composed read or to each request without allowing excessive multiplied sequential waits; no duration is selected by this lifecycle closure.
- Do not include onboarding mutations, Alerts/Purchases mutations, production, Import Apply, stock movement creation, backup/export/report generation, hidden polling, cloud/offline sync, framework migration, backend/API/schema/migration changes, or new dependencies.
- No source timeout may authorize an automatic retry. Automatic retry for any mutation is explicitly forbidden, and no mutation path may use the safe-GET timeout primitive.
- Required future evidence: focused timeout/lifecycle tests, existing Dashboard/Onboarding regressions, frontend production build, and exact-head Dashboard browser smoke covering initial timeout, refresh timeout with retained snapshot, explicit recovery, late-result rejection, route ownership, desktop/narrow behavior, keyboard focus, and intentional-fault classification.

This lifecycle closure is documentation-only. It does not implement B4.1 and does not claim browser smoke for the documentation commit.

## 2026-07-26 — B4.1 Dashboard safe GET timeout handoff

### Runtime scope

- Branch: `codex/b4.1-dashboard-safe-get-timeout`.
- Exact starting `origin/main`: `f3fc8d0c8872908801f1b667731c5792c82448ea`, the PR #140 merge.
- The pilot covers only Dashboard initial read and manual refresh.
- `frontend/src/dashboard-read-runtime.ts` owns one five-source generation, the `8_000 ms` whole-operation deadline, one abort controller, deterministic scheduling, validation aggregation, atomic candidate construction, race rejection, and exactly-once cleanup.
- `DashboardOnboardingFeedbackLifecycle` remains the Dashboard state/presentation owner; `main.ts` remains the dependency, route-ownership, rendering, announcement, and control-binding boundary.
- Route leave aborts and settles silently. Timeout, ordinary failure, invalid DTO, abort rejection, late result, duplicate start, and supersession cannot commit partial or mixed state or settle busy ownership twice.
- Initial timeout offers `Повторить` and states that workshop data was not changed. Refresh timeout retains the prior coherent snapshot and warns that it may be stale. Recovery is manual only.

### Transport and startup findings

- Only `getOrders`, `getClients`, `getAlerts`, `getPurchaseSuggestions`, and `getProductionBatches` accept an optional signal. Non-Dashboard callers pass none.
- `apiGet` is structurally GET-only; `apiSend` and mutation functions accept no signal from this boundary. No mutation is retried.
- The launcher completes startup initialization and waits one second for the backend process to remain alive before opening the browser, but does not poll health readiness. The selected eight-second localhost deadline bounds this remaining startup gap and indefinite hangs without adding health polling.

### Verification and acceptance state

- Dashboard/Onboarding focused suite: 33/33 passed twice.
- Direct regressions: Help 3/3; form validation 19/19; targeted validation 62/62; Alerts 56/56; Purchases 116/116; Orders/Production 21/21; Formula/Clients 60/60.
- Frontend production build passed.
- Backend base/head comparison: both runs collected 496, passed 492, failed the same 4 accepted baseline tests, and skipped 0; branch-only failure delta is `0`.
- Publication SHA, PR URL, and browser smoke status are added to the PR/final report after publication.
- Current status: `IMPLEMENTED — EXACT-HEAD BROWSER SMOKE REQUIRED`. Do not mark B4.1, B4, or Block B DONE, and do not activate B4.2.

## 2026-07-26 — Block B closure and backend baseline correction gate handoff

### Verified repository state

- Current `origin/main`: `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` — the PR #141 merge commit. Confirmed to contain the expected merge (VERIFIED FROM REPOSITORY / GITHUB).
- Branch for this documentation task: `claude/close-block-b-authorize-backend-hardening`, created from that exact `origin/main`. Merge-base equals `origin/main`; no divergence.
- PR #141 — `B4.1 — Dashboard safe GET timeout and recovery`: state `MERGED`, merged `2026-07-26T14:58:37Z`, base `main`, head branch `codex/b4.1-dashboard-safe-get-timeout`, final reviewed head `d0cde127355b146f101ddf3769d76d0226c71ec0`, merge commit `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa`. PR #141 and its merged branch were not modified or reused.
- This change is documentation and state only. No backend or frontend production file, no test, no schema, no migration, no dependency, no lockfile, and no pytest configuration was touched.

### Provenance of supplied evidence

- `VERIFIED FROM REPOSITORY / GITHUB` — PR #141 merge state, final reviewed head, merge commit, merge date, and every production/test source relationship quoted in the triage document.
- `EXECUTED IN THIS TASK` — the complete backend baseline, both isolated runs of each named node, all four surrounding test files, the diagnostic environment details, and the temporary-environment cleanup.
- `SUPPLIED TASK BASELINE` — Dashboard/Onboarding `42/42`, frontend production build `PASS`, accepted backend baseline, and PR #141 backend branch-only failure delta `0`.
- `SUPPLIED TASK BASELINE — product-owner-verified exact-head smoke of PR #141 on 2026-07-26; not re-run in this documentation task` — every browser, keyboard, responsive, network, and exact-head smoke result. These are **not** GitHub Actions evidence, **not** checks executed by this PR, and **not** checks executed by Claude Code.

### Superseded wording

- `IMPLEMENTED — EXACT-HEAD BROWSER SMOKE REQUIRED` for B4.1 is superseded: B4.1 is DONE.
- `Block B remains active through B4` and `ACTIVE NEXT IMPLEMENTATION WINDOW` for B4 are superseded: B4 and Block B are DONE.
- The `docs/implementation-plan.md` instruction to start Slice A1 is superseded and removed; Slice A1 completed long ago in PR #113.
- Accurate historical dated entries in `state/progress.md` and `state/handoff.md` remain unedited, including the `33/33` record, which belongs to an earlier recorded branch state.

### B4 limitation

B4 is closed with the Dashboard safe-GET pilot only. Safe GET timeout and recovery coverage for the remaining read routes, including but not limited to Alerts, Purchases, Orders, Reports, Backups, Exports, and Report Documents, was deliberately deferred and was not delivered. Any future expansion requires a separately authorized slice and a change request. Closing B4 does not imply that those routes are protected against an indefinitely hanging local GET.

No approved B4.2 contract exists. No B4.2 section was created and no B4.2 slice is authorized.

### Diagnostic outcome

`PATH A / COMPLETE`. Python `3.12.13` in an external venv outside the repository, pytest `8.4.2`, run from `backend/` with rootdir `backend/` and configfile `pyproject.toml`. The complete baseline reproduced `496 collected, 492 passed, 4 failed, 0 skipped` with zero drift and no additional failures. Every named node ran twice in isolation, every surrounding test file ran completely, and all four failures are deterministic. The temporary environment was removed and verified absent.

- backups reason sanitization — `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED`, call-phase.
- exports reason sanitization — `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED`, call-phase. Structurally duplicated implementation of the same filename contract as the backups node.
- import draft issue count — `TEST DEFECT`, MEDIUM, call-phase. The documented `DD.MM.YYYY` normalization makes the observed `error_count` of `3` correct.
- purchase-suggestions manual API smoke — `TEST DEFECT`, MEDIUM, setup/arrange. The API is never reached; the domain correctly rejects a zero-quantity movement.

The two filename nodes are `INCONCLUSIVE` because no product documentation defines whether consecutive unsafe characters in a filename reason must collapse to a single underscore. The tests require collapsing; `backend/app/services/backup.py:47` and `backend/app/services/export.py:84` map each replaced character to one underscore. **Do not state that the production behavior is wrong.** Severity, root cause, correction surface, schema requirement, grouping, slice, tests, and smoke are all `NOT DETERMINED FROM CURRENT EVIDENCE` for those nodes. The blocker is a product decision, not missing diagnostic evidence — no further test execution would resolve it. It is tracked as `CR-005`, status `needs product decision`, covering collapsing, whether literal hyphens remain allowed, the filename-to-metadata reason round-trip, whether the displayed reason is filename-derived or stored independently, and the required focused smoke after implementation.

No data loss or unsafe mutation was found. Detailed evidence and the mandatory per-node fields live in `docs/backend-baseline-failure-triage.md`; do not duplicate them into `state/`.

### Active slice

Exactly one: `R3 — Repair purchase-suggestions API smoke seeding`, **test-only**. Contract in `state/current-focus.md`.

- Change exactly one value: `lot_qty="0"` → `lot_qty="1"` in the `seed_ready(...)` call at `backend/app/tests/test_purchase_suggestions.py:214`.
- Leave `packaging_qty="2"` on that same line unchanged.
- Leave the existing `minimum_stock='10'` setup at `backend/app/tests/test_purchase_suggestions.py:215-216` unchanged. The existing threshold of `10` is already higher than the new lot quantity of `1`, so the below-minimum condition the test needs remains true without touching the threshold.
- Do not change any other line in the test. The diff is exactly one changed value on one line.
- Preserve and execute all existing API and no-mutation assertions.
- No production-code change. No skip, `xfail`, deletion, rename, or weakened assertion.
- Run the complete backend suite from `backend/`.
- Required smoke is the **backend suite only**. The slice changes no runtime surface, so no browser, visual, or route-rendering check applies, is required, or may be claimed.

`R2` (import draft issue-count contract alignment, test-only) is the next deferred slice. The two filename nodes have **no slice** and must not receive one until `CR-005` is decided. Any focused `/backups` and `/exports` visual check belongs to that product decision and its future implementation slice, not to the active slice. Do not start deferred work, do not combine it with `R3`, and do not assign a future PR number.

Recorded neutrally without diagnosis or activation: a potential SQLite backup transaction-consistency candidate requiring a separate evidence-based diagnostic, tracked as `CR-004` / `needs evidence` in `state/change-requests.md`. It is distinct from the `CR-005` filename-contract decision.

### Remaining release blockers

Clearing the four baseline failures does not make the product release-ready. Still open and not activated here:

1. final macOS `.app`/`.dmg` and user-ready launch;
2. packaged update flow and update smoke;
3. verified user/remote installation process;
4. Restore product decision and implementation;
5. C1 tax setting;
6. C2 cost, tax, and margin completion;
7. C3 user-facing read-only AuditLog workspace;
8. full release-candidate smoke;
9. continued documentation accuracy.

C1, C2, C3, and C4 remain inactive. Packaging is blocked and release smoke is blocked. Product release readiness is not claimed.

## 2026-07-27 — Handoff after R3 implementation

- `R3 — Repair purchase-suggestions API smoke seeding` is **implemented but not DONE**. Status: `IMPLEMENTED — REVIEW AND MERGE REQUIRED`. It is not merged. It stays the active slice until it is reviewed and merged.
- Branch: `claude/r3-repair-purchase-suggestions-api-smoke-seeding`, created from clean `origin/main` `6cb6f446c2a47a5272c51bfb63b3159d23cb5db2`, which contains the final reviewed PR #142 head `64850b3aa508d63ca1f1cefe240b2eaba50d9e72`. No rebase, no force-push, no history rewrite.
- Exact runtime/test diff — one changed value on one line:

```diff
- c = config(tmp_path); _, ingredient, _, _, _ = seed_ready(c, lot_qty="0", packaging_qty="2")
+ c = config(tmp_path); _, ingredient, _, _, _ = seed_ready(c, lot_qty="1", packaging_qty="2")
```

  `packaging_qty="2"` on that same line and the `minimum_stock='10'` setup at `backend/app/tests/test_purchase_suggestions.py:215-216` are unchanged, and no other line of the test changed. No production file changed; the zero-quantity domain rule and `seed_ready(...)` are untouched.
- Exact test evidence (EXECUTED IN THIS TASK, from `backend/`, Python `3.12.13`, pytest `8.4.2`, rootdir `backend/`, configfile `pyproject.toml`, temporary venv outside the repository, removed and verified absent):
  - pre-change complete suite `496 collected, 492 passed, 4 failed, 0 skipped` — the four accepted gate nodes;
  - pre-change isolated target node failed during arrangement inside `seed_ready(...)`, before the API;
  - post-change isolated target node `PASSED` twice;
  - `app/tests/test_purchase_suggestions.py` `11 passed`;
  - post-change complete suite `496 collected, 493 passed, 3 failed, 0 skipped`.
  - The three no-mutation assertions executed and passed; the node now exercises the real `/api/purchase-suggestions` HTTP surface.
- Remaining failures, exactly three:
  - `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`
- `R2 — Import draft issue-count contract alignment` remains deferred and next. **Do not start `R2` from the unmerged `R3` branch.** Start it only from `origin/main` after `R3` is reviewed and merged.
- Nodes 1 and 2 — the backups and exports filename-reason nodes — remain blocked on `CR-005` (`needs product decision`) and still have no slice. `CR-004` remains a separate `needs evidence` row and is not activated.
- Smoke for `R3` was the **backend suite only — PASS**. No browser, visual, keyboard, responsive, packaging, or release smoke was required, executed, or claimed. C1–C4 remain inactive, packaging and release smoke remain blocked, and product release readiness is not claimed.

## 2026-07-27 — Handoff after R3 merge and R2 implementation

- **`R3` — DONE.** PR #143 `R3 — Repair purchase-suggestions API smoke seeding` is merged (VERIFIED FROM REPOSITORY / GITHUB): state `MERGED`, final reviewed head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`, merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`, merged at `2026-07-27T04:01:23Z`, accepted backend result `496 collected, 493 passed, 3 failed, 0 skipped`, no production code changed. The previous dated handoff described the pre-merge `R3` state and is superseded by this entry, not edited.
- **`R2 — Align import draft baseline test with the documented date-normalization contract` is implemented but not DONE.** Status: `IMPLEMENTED — REVIEW AND MERGE REQUIRED`. It is not merged. It is the single current slice and stays active until it is reviewed and merged.
- Branch: `claude/r2-align-import-draft-baseline-test`, created from clean `origin/main` `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`. No rebase, no force-push, no history rewrite.
- Exact test-only diff — the assertion block of `backend/app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`:

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

  The response status assertion, the request payload, the CSV data, the date `05.07.2026`, the target type, and the global `missing_required_column` assertion are unchanged, and no other line of the file changed. No production file changed: `_normalize_date_value`, `_readiness`, `_issue_counts`, required-column handling, `missing_required_value`, and import Apply are untouched, and `docs/import-format.md` was not modified.
- Contract evidence: `05.07.2026` is a deterministic Russian `DD.MM.YYYY` date that `docs/import-format.md` requires to normalize to ISO with a `date_format_normalized` **warning**. `invalid_date` stays reserved for genuinely invalid dates. The corrected assertions are strictly more specific than the ones they replace, and no validation was weakened.
- Exact test evidence (EXECUTED IN THIS TASK, from `backend/`, Python `3.12.13`, pytest `8.4.2`, rootdir `backend/`, configfile `pyproject.toml`, temporary venv outside the repository, removed and verified absent):
  - pre-change complete suite `496 collected, 493 passed, 3 failed, 0 skipped`;
  - pre-change isolated target node returned `201` and failed at `assert 3 >= 4`, with observed `error_count` `3`, `warning_count` `1`, readiness `blocked`, `can_apply` `false`;
  - post-change isolated target node `PASSED` twice;
  - `app/tests/test_imports_api.py` `7 passed`;
  - `app/tests/test_import_parsing.py` `16 passed`, `0 skipped`;
  - post-change complete suite `496 collected, 494 passed, 2 failed, 0 skipped`, with `app/tests/test_purchase_suggestions.py::test_manual_api_smoke` passing.
- Remaining failures, exactly two:
  - `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
  - `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
- Nodes 1 and 2 — the backups and exports filename-reason nodes — remain `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED`, still have no slice, and remain blocked on `CR-005` (`needs product decision`). **Do not begin the filename correction work, and in particular do not begin it from the unmerged `R2` branch.** Start any future filename slice only from `origin/main` after `CR-005` is decided.
- `CR-004` remains a separate `needs evidence` row and is not activated. `state/change-requests.md` was not modified.
- Smoke for `R2` was the **backend suite only — PASS**. No browser, visual, keyboard, responsive, route-rendering, packaging, restore, migration, or release smoke was required, executed, or claimed. C1–C4 remain inactive, packaging and release smoke remain blocked, and **product release readiness is not claimed**.

## 2026-07-27 — Handoff after R2 merge and the CR-005 product decision

- **`R2` — DONE.** PR #144 `R2 — Align import draft baseline test with date normalization` is merged (VERIFIED FROM REPOSITORY / GITHUB): state `MERGED`, final reviewed head `52e2c64fc601b458cfd60e8b86a778efabd65671`, merge commit `8efbdc5c85b5932f4aeef51045542c207cf4635c`, merged at `2026-07-27T04:21:16Z`, accepted backend result `496 collected, 494 passed, 2 failed, 0 skipped`, no production code changed. `R3` remains DONE. The previous dated handoff described the pre-merge `R2` state and is superseded by this entry, not edited.
- This handoff covers a **documentation-only product-decision PR**. Branch `claude/decide-cr-005-artifact-reason-contract`, created from clean `origin/main` `8efbdc5c85b5932f4aeef51045542c207cf4635c`. No rebase, no force-push, no history rewrite, no auto-merge. No backend code, frontend code, or test changed.
- **`CR-005` is accepted.** The exact contract, durable in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`:
  - two distinct representations that must never be conflated — the **human reason** `text = (reason or "manual").strip() or "manual"`, and the **canonical filename reason segment** derived from it;
  - canonical algorithm for newly created backups and exports: preserve Unicode alphanumerics exactly; treat underscore and every non-alphanumeric character as a separator, including whitespace, hyphen, dot, slash, backslash, punctuation, and symbols; collapse each maximal run of separators to one underscore; strip leading and trailing underscores; empty → `manual`; digits-only → prefix `reason_`; preserve letter case; no lowercasing; no transliteration; no new length limit;
  - contract examples: `before/update ../unsafe` → `before_update_unsafe`; `before-import` → `before_import`; `___before---import___` → `before_import`; `перед обновлением` → `перед_обновлением`; `123` → `reason_123`; whitespace-only → `manual`; punctuation-only → `manual`;
  - literal hyphens are not allowed inside a new filename reason segment and normalize to underscore; they stay allowed in the human reason and the export manifest reason;
  - a filename reason segment is never purely numeric, so it cannot collide with the uniqueness suffix `-1`, `-2`, `-3`;
  - the existing filename grammar is preserved — `{timestamp}-{safe_source_stem}-{canonical_reason}[-N].{sqlite_suffix}` and `{timestamp}-cosmetic_workshop-export-{canonical_reason}[-N].json` — with no new version, marker, sidecar format, or migration;
  - for new artifacts the create, list, and status reasons are all the canonical segment, the visible UI reason resolves from that segment, and the uniqueness suffix is never part of the reported reason;
  - the displayed reason is filename-derived from the existing API `reason` field — no metadata table, sidecar file, new API field, frontend-only reconstruction rule, or hidden persistent metadata. Two layers, both binding: the **backend/API `reason` is the canonical slug** and the single source of truth, and the **frontend consumes that slug and must never reconstruct, sanitize, or normalize it**, mapping **known system slugs** to the **existing localized Russian display labels** and rendering **custom or unmapped slugs verbatim**. The visible label is therefore **not always literally the canonical slug** — canonical `before_import` renders as `Перед импортом`, unmapped canonical `before_update_unsafe` renders verbatim. Backup and export mappings are separate and differ (`manual` is `Обычная резервная копия` on `/backups`, `Обычный экспорт` on `/exports`; `support_snapshot` is export-only). Exact tables: `docs/backup-and-restore.md` and `docs/export.md`. No Russian label is added, removed, or reworded;
  - the export JSON manifest keeps the normalized human reason and the export schema version does not change;
  - existing artifacts are never renamed, rewritten, or deleted; no migration; legacy listing stays best-effort and exact recovery is not claimed for ambiguous legacy filenames;
  - one shared helper, recommended `normalize_artifact_reason_segment(value: str | None) -> str` in `backend/app/services/local_artifact_filenames.py`, scoped **only** to backup and export filename reason segments; `backend/app/services/report_documents.py` stays a different contract and out of scope.
- Post-decision classification, recorded without rewriting the diagnosis-time history: Nodes 1 and 2 are both `PRODUCT DEFECT — CONTRACT MISMATCH`, severity `MEDIUM`, no proven data loss, no source database mutation, no overwrite regression.
- **`R4` implementation boundary.** `R4 — Canonical backup/export filename reason normalization` is authorized as exactly one bounded slice covering both nodes, and it is **NOT IMPLEMENTED**. **Do not start `R4` from this unmerged decision branch.** Start it only from `origin/main` after this decision PR is reviewed and merged. Expected production surface is bounded to `backend/app/services/local_artifact_filenames.py`, `backend/app/services/backup.py`, and `backend/app/services/export.py`; a parser change inside those same service modules is allowed only where the new-file round-trip contract requires it, and a filename-format migration must not be authorized merely to simplify parsing. Full Scope, Non-goals, Architecture constraints, Backend requirements, Frontend requirements, Tests, Smoke, and Acceptance criteria: `docs/implementation-plan.md`.
- **Required backend tests for `R4`.** Preserve the two existing failing tests and make them pass without weakening them. Add focused coverage for at least: unsafe run collapse; hyphen normalization; mixed separator collapse; Unicode; numeric-only; empty and unsafe-only fallback; backup create/list/status round-trip; export create/list/status round-trip; duplicate-suffix exclusion from the metadata reason; a backup source stem containing hyphens; the export manifest preserving the normalized human reason; existing-artifact non-overwrite behavior; legacy artifact listing without rename, deletion, or crash; and current default `manual` behavior. Do not delete, rename, skip, `xfail`, or weaken any existing test. Run the complete backend suite from `backend/`; acceptance is `0 failed` and `0 skipped` with both former baseline nodes passing. The `496` collection count is not required to stay exact.
- **Required frontend verification for `R4`.** **No frontend production change is expected**, but focused **frontend test-only** changes are allowed, because no runnable suite currently proves the canonical-reason display contract. Verified repository state: `npm run test:local-artifacts-reports-feedback` is runnable and its tsconfig already compiles `src/local-artifact-presentation.ts`, but it asserts nothing about reason presentation; `frontend/test/local-artifact-presentation.test.mjs` is **not runnable** because no tsconfig emits to `dist-tests/local-artifact-presentation/` and no npm script invokes it; and the mapping functions `backupReasonLabelRaw` / `exportReasonLabelRaw` live in `frontend/src/main.ts`, which no focused test tsconfig includes. `R4` must therefore either **(preferred)** add focused reason-presentation assertions to the runnable `frontend/test/local-artifacts-reports-feedback.test.mjs`, or **(alternative)** make the standalone local-artifact-presentation suite runnable through an exact tsconfig and npm script **without adding dependencies**. Those tests must prove: an unmapped canonical slug such as `before_update_unsafe` renders verbatim; a known canonical system slug uses the existing localized Russian mapping; the frontend does not reconstruct, sanitize, or normalize the slug; and no frontend production behavior changes unless implementation evidence proves it necessary **and the contract is updated first** — reaching the mapping in `main.ts` may require such evidence and is **not** pre-authorized. Existing Russian label text must not be introduced, removed, or reworded. The frontend production build remains required.
- **Required focused browser smoke for `R4`.** Run focused browser smoke against the final published implementation head using an isolated temporary user-data directory, an isolated temporary SQLite database, an isolated browser profile, no real user data, and evidence kept outside Git. Create one backup and one export through the backend/API with a reason such as `before-update ../unsafe`, then verify on `/backups` and `/exports` that the route loads, the artifact appears, the filename contains `before_update_unsafe`, the visible reason label equals exactly `before_update_unsafe` — this slug is deliberately **unmapped**, so it must render verbatim rather than through any Russian label — the value survives route reload or refetch, the uniqueness suffix is not part of the reason, the export manifest still contains the normalized human reason `before-update ../unsafe`, and no unrelated file is overwritten. Evidence requires desktop `1440 × 900`, zero unexpected console errors, zero unexpected console warnings, zero page errors, zero unexpected HTTP failures, zero unexpected request failures, no horizontal page overflow from the rendered filename or reason, and no production data beyond the intended temporary artifacts. Full release smoke must not be claimed.
- **Nothing was executed for this decision PR.** No backend pytest, no frontend tests, no frontend build, no browser smoke, no API smoke, no packaging smoke, and no release smoke were run or claimed. The merged PR #144 backend result is carried only as `VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE`. The two backend failures are still open and no backend `0-failure` state is claimed.
- `CR-004` remains a separate `needs evidence` row and is **not** resolved, activated, or affected by this decision. In `state/change-requests.md` only the `CR-005` row changed, to `accepted`, with Target PR left empty and no future implementation PR number assigned. C1–C4 remain inactive, packaging and release smoke remain blocked, and **the product remains not release-ready**.

## 2026-07-27 — Handoff after the CR-005 merge and the R4 branch implementation

- **`CR-005` decision is closed.** PR #145 is merged (VERIFIED FROM REPOSITORY / GITHUB): final reviewed head `7d68b45bee1f223b67f105c30e3acbb89dc8d41d`, merge commit `bef36822e50c245b72f813dad0afbffc7f772588`, merged `2026-07-27T05:15:04Z`. `CR-005` remains **accepted** and its contract is unchanged. The previous handoff described the pre-merge decision state and is superseded by this entry, not edited.
- **`R4` is IMPLEMENTED but NOT DONE.** Status: `IMPLEMENTED — EXACT-HEAD SMOKE REQUIRED BEFORE MERGE`. Branch `claude/r4-canonical-artifact-reason-normalization`, created directly from clean `origin/main` `bef36822e50c245b72f813dad0afbffc7f772588`. No rebase, no force-push, no history rewrite, no auto-merge. It is not reviewed and not merged, and the backend correction gate stays open until it is.
- **Checks completed before publication:**
  - backend, from `backend/` with Python `3.12.13` and pytest `8.4.2` in a temporary virtual environment outside the repository — pre-change baseline `496 collected, 494 passed, 2 failed, 0 skipped` reproduced exactly with the two expected nodes and no drift, each node re-run twice; post-change complete suite `562 collected, 562 passed, 0 failed, 0 skipped`; both former baseline nodes pass, each re-run twice; all 496 previously collected node IDs still collected; no existing test deleted, renamed, skipped, `xfail`-ed, or weakened;
  - frontend — `npm run test:local-artifacts-reports-feedback` `40 pass, 0 fail, 0 skipped`, re-run after the build with the same result; `npm run build` succeeds; **no frontend production file changed** and no dependency, lockfile, or npm script changed.
- **The exact-published-head browser smoke is the remaining pre-merge gate and runs only after publication.** Focused `/backups` and `/exports` smoke at desktop `1440 × 900`, against the exact published pull-request head, with an isolated temporary SQLite database, an isolated temporary user-data directory, an isolated browser profile, no real user data, and all runner code and evidence kept outside the tested repository. Create one backup and one export through the real backend API with reason `before-update ../unsafe`; require API `reason` `before_update_unsafe` on create, list, and status; require `/backups` and `/exports` to display exactly `before_update_unsafe` — deliberately an **unmapped** slug, so it renders verbatim — and to keep it after an explicit refetch and after a full page reload; require the export manifest to still read `before-update ../unsafe`; require a small secondary check that a `before_import` artifact displays the existing Russian label `Перед импортом`.
- **No commit may be added after a passing smoke.** Any new commit changes the pull-request head, makes the prior smoke stale, and requires the complete exact-head smoke to be re-run against the new head. This is why no repository file claims a passing smoke: a post-smoke documentation commit would invalidate the evidence. Pull-request body edits are safe because they do not change the head.
- **Read before continuing:** `state/current-focus.md` for the `R4` scope as implemented, `docs/backend-baseline-failure-triage.md` §15 for the branch result, and `docs/implementation-plan.md` for the full `R4` contract. The `CR-005` durable contract is in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`; it was not changed by `R4`.
- `state/change-requests.md` was not modified. `CR-004` — potential SQLite backup transaction consistency — remains a separate, unresolved `needs evidence` row and is not activated or affected by `R4`. Restore remains unimplemented.
- C1, C2, C3, and C4 remain inactive. Packaging and release smoke remain blocked. **The product is not release-ready.**

## 2026-07-27 — Handoff after the R4 merge, gate closure, and the CR-006 export fallback evidence request

- **`R4` is closed and DONE.** PR #146 is merged (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE): final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`, merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453`, merged `2026-07-27T08:51:06Z`; `origin/main` equals that merge commit. The previous handoff described the pre-merge `R4` branch state and is superseded by this entry, not edited.
- **The backend baseline correction gate is DONE** and the **merged `main` backend baseline is green**. Accepted merged evidence, none of it executed in the closure task: backend `562 collected, 562 passed, 0 failed, 0 skipped`; frontend focused suite `40 passed, 0 failed, 0 skipped`; frontend production build `PASS`; focused exact-published-head `/backups` and `/exports` browser smoke `PASS — FULL AUTOMATED SMOKE PASSED` against `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`. Both original filename nodes are closed on `main`; all four gate nodes are now closed. `CR-005` remains accepted and is now implemented, and neither `CR-005` nor `R4` is reopened.
- **There is no active implementation slice.** The closure task deliberately selected none and assigned no future PR number. **The next work must be separately selected and authorized** before any runtime change begins.
- **Open evidence question — `CR-006`.** `CR-006 — Investigate export create-response fallback confirmation semantics` is a `needs evidence` row with an **empty Target PR**. In `backend/app/api/exports.py::create_export`, the endpoint looks up the exact created file through `list_export_files`; on a hit it returns the canonical filename-derived reason from parsed filename metadata, and on a miss a defensive fallback builds the response from `ExportResult.reason`, the normalized **human** reason kept in the export manifest — so the fallback may return a human reason where the API contract normally expects the canonical slug. It is **not** a confirmed defect: no user-visible failure reproduced, no data loss or unsafe mutation proven, reachability not established, **no severity assigned**, **no correction authorized**. Answer reachability first — artifact disappearance after write, a filesystem race, a permission or `stat` failure, a list/read failure, or mocked or injected repository/service behavior — and only then the desired contract: canonical reason, explicit failure because the created artifact cannot be confirmed, or another documented outcome. Do not implement a fallback correction, add an API error response, or change `ExportResult`, `list_export_files`, or the API schemas before both questions are answered. Full record: `docs/backend-baseline-failure-triage.md` §17.
- **`CR-004` remains separate.** Potential SQLite backup transaction consistency stays an unresolved `needs evidence` row, is not activated, is not affected by `R4`, and is **not** merged with `CR-006` — the two are independent findings.
- **Remaining release obligations**, none activated: `CR-004`; the Restore product decision and implementation; final macOS packaging and user-ready launch; installation verification; the packaged update flow and update smoke; the full release-candidate smoke; C1, C2, C3, and C4, which remain **inactive** unless separately authorized; and continuing documentation accuracy.
- **Durable `CR-005` documentation is now consistent with merged `main`.** `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md` each had a stale pre-merge `R4` implementation-status paragraph claiming `R4` was unmerged and that `main` still produced the older repeated-underscore output. All three were corrected in this same slice to the accurate merged status — `R4` merged and DONE at head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb` / merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453`, merged `main` implementing the canonical reason contract, `562 / 562 / 0 / 0`, exact-head smoke passed, no response-shape change, no schema change, no migration, existing artifacts untouched, `CR-004` unresolved, Restore unimplemented, release readiness not claimed. The durable normalization algorithm and the UI/API/manifest contract are unchanged. **No documentation-gap slice is outstanding.**
- **Read before continuing:** `state/current-focus.md` for the post-`R4` status and the `CR-006` boundaries, `docs/backend-baseline-failure-triage.md` §16 for the gate closure and §17 for the fallback observation, `docs/implementation-plan.md` section 10a for the closed window, and `state/change-requests.md` for the `CR-006` row. The `CR-005` durable contract is in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`; its normalization, UI, API, and manifest rules are unchanged and only the implementation-status paragraph in each file was updated.
- The closure slice was **documentation-only**: no backend code, no frontend code, and no test changed, and no runtime test or smoke was executed in it. `CR-001` through `CR-004` are unchanged; the `CR-005` row changed only in its lifecycle tail, preserving its ID, date, title, `accepted` status, full contract, boundaries, legacy wording, and empty Target PR. Branch `claude/close-r4-record-export-fallback` was created directly from clean `origin/main` `127191feb182ccf68a4d7b9f2be28f6aa5b42453`; no rebase, no force-push, no history rewrite, no auto-merge.
- **The product is not release-ready.**

## 2026-07-27 — Handoff after the CR-007 C1 tax-setting product decision

- **This handoff covers a documentation-only product-decision PR.** Branch `claude/decide-c1-tax-setting-contract`, created directly from clean `origin/main` `09d11fc32db6ae57f99d522c4aa71e223e4e01a5`. No rebase, no force-push, no history rewrite, no auto-merge. No backend code, frontend code, or test changed, and no runtime test, build, or smoke was executed in it. The previous handoff described the post-`R4` closure state and is superseded by this entry, not edited.
- **`CR-007` is accepted and not implemented.** The durable contract is `docs/settings.md` § “C1 — налоговая ставка для расчётов”:
  - **one global setting** `default_tax_rate`, user-facing `Налоговая ставка для расчётов`, an internal planning estimate — never tax filing, a declaration, VAT accounting, jurisdiction-specific legal advice, automatic regime detection, or an invoicing/accounting subsystem, and never labelled as a specific legal regime; required UI copy `Ставка используется для внутренней оценки налога с цены продажи. Приложение не формирует налоговую отчётность.`;
  - **percentage, not coefficient** — `6` and `6.00` mean `6%`, `0.06` means `0.06%`; `Decimal` only, decimal strings on the wire, never binary float, at most two fractional digits on input, range `0.00`–`100.00` inclusive; `6`, `6.0`, and `6.00` are equivalent, and `6.005` is **rejected, never rounded**;
  - **canonical form is exactly two fractional digits**, both persisted and in the API — `6` → `6.00`, `6.0` → `6.00`, `6.00` → `6.00`, `0` → `0.00`, `100` → `100.00` — applied after validation and never used to absorb excess precision, and the no-op comparison uses that exact canonical string, so `PUT "6"` against stored `"6.00"` writes nothing;
  - **taxable base is the order sale price** — `tax_amount = ROUND_MONEY(sale_price_snapshot × tax_rate_percent_snapshot ÷ 100)`, money quantum `0.01`, `ROUND_HALF_UP`, rounding only the final amount and never intermediate products; tax is deducted from gross revenue and never added on top; no expense-based regimes, fixed amounts, brackets, minimum tax, deductions, VAT modes, multiple rates, or per-product/client/order/batch overrides;
  - required rounding examples: `1000.00 @ 6.00 → 60.00`; `999.99 @ 6.00 → 60.00`; `1.00 @ 0.50 → 0.01`; `1.00 @ 0.00 → 0.00`; missing rate → unavailable; missing sale price → unavailable;
  - **immediate effectiveness** through a backend-generated `effective_at` describing the **currently active setting** — no backdating, no scheduling, no multiple active periods, no user-configurable effective date, no user editing; new on first configuration and on a real rate change, unchanged on a no-op, and **`null` after Clear**, because there is no active setting left to timestamp — the clear time is recorded by `AuditLog.created_at`, and the clear metadata carries `previous_effective_at` plus `new_effective_at: null`;
  - **timestamp storage** — the source is `AppSetting.updated_at`, which stays persisted in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format; the service normalizes it and only the API exposes ISO-8601 UTC. The database does not store ISO-8601, and `C1-I` changes no column, default, or migration;
  - **history is immutable** — a rate change never modifies completed `ProductionBatch` rows, existing report snapshots, prior audit records, generated documents, or persisted tax/margin values; an order created before a change but produced after it uses the rate active at confirmation;
  - **missing is not zero** — `null` gives a non-blocking warning, leaves tax and dependent margin unavailable, does not block physical production, and leaves the resulting batch's tax fields `null` forever; old rows show `Недоступно`; a configured `0.00` is a real value that must not display as unconfigured; no fabricated zero anywhere;
  - **explicit clear is row deletion** — `tax_rate_percent: null`, an empty string is not a backend substitute, confirmed, warned about, audited, never retroactive, and a no-op when already unconfigured. `C1-I` deletes **only** the `default_tax_rate` `AppSetting` row through a bounded new `delete_setting(key, connection=None)` capability, and never deletes, reads, reinterprets, migrates, or rewrites the legacy `tax.default_rate` key. The delete and its `AuditLog` insert share one transaction, and a failed audit insert rolls the deletion back. After a successful Clear the API returns `is_configured: false`, `tax_rate_percent: null`, `effective_at: null`. Clearing an absent row does nothing at all — no delete, no timestamp change, no audit, no changed message. **Not authorized:** a nullable-column migration, sentinel value, empty-string storage, new settings table, or parallel settings store; unconfigured is the absence of the row;
  - **atomic audit** — every real mutation writes `tax_rate_setting_changed` / `app_setting` / `default_tax_rate` in the same transaction as the persistence change, upsert and delete alike, and rolls that change back if the audit write fails; reads, opening Settings, validation failures, failed persistence, and no-ops are not audited; safe metadata only, never the raw payload, full settings JSON, stack traces, unrelated profile fields, or client data;
  - **no-op** returns the current representation and writes nothing — no setting write, no row deletion, no `effective_at` change, no `AuditLog`, no misleading success message;
  - **UI** stays inside `/settings` with one percentage input and `%` unit, help text, configured/unconfigured state, human-readable effective timestamp, Save, Cancel, explicit confirmed Clear, structured field error, form-scoped pending state, success only after backend confirmation, distinct mutation and refresh failures, keyboard accessibility, and no raw JSON, API terminology, or tax-law promises; the frontend sends a decimal string or `null` and never calculates tax or margin.
- **C1/C2 boundary.** C1 owns the persisted rate, validation, the effective timestamp, the GET/update API, explicit clear, the Settings UI, the atomic audit, persistence and reload, and no-op behavior. C2 owns readiness estimates, stale-setting detection, `ProductionBatch` tax snapshots and their nullable migration, tax amount, margin and margin percent, reports from snapshots, old-record unavailable behavior, and backward-compatibility tests. **C2 stays blocked until the C1 implementation is merged and verified** and must not be implemented inside the C1 slice. C2's readiness contract is already binding: readiness uses the currently effective rate and the current order `sale_price`, is recalculated per request, reports the rate used, the effective timestamp, whether the rate is configured, and whether the result is available — and confirmation must re-read the setting, detect a stale effective timestamp, and reject through a structured conflict such as `financial_settings_changed` with no stock movement, batch, order-status change, or partial write.
- **`C1-I — Backend-owned tax-rate setting` is the single authorized follow-up slice, and it is NOT IMPLEMENTED.** Status: `AUTHORIZED AFTER THIS DECISION PR MERGES — NOT IMPLEMENTED`. **Do not start `C1-I` from this unmerged decision branch.** Start it only from `origin/main` after the decision PR is reviewed and merged. No implementation PR number is assigned. Full Scope, Non-goals, Architecture constraints, Backend requirements, Frontend requirements, Tests, Smoke, and Acceptance criteria: `docs/implementation-plan.md` § 11.
- **Read the recorded repository constraints before writing `C1-I`** — full evidence in `docs/settings.md` § 14. The five that will otherwise cause wrong money or a wrong architecture: the seeded `app_settings` row `tax.default_rate = "0.06"` is a **superseded coefficient-shaped placeholder** and must never be read, reinterpreted, migrated, rewritten, deleted, or treated as a configured rate — use the distinct key `default_tax_rate`, and never conflate the two; `SettingsRepository.upsert_setting` accepts no external connection while `AuditLogRepository.create_log` does, so atomicity needs a **bounded optional-`connection` extension** with no schema change and no new settings architecture, and if that proves insufficient the slice must stop, record evidence, and update the contract first; `SettingsRepository` has **no delete capability**, so Clear needs one bounded new `delete_setting(key, connection=None)` method sharing that pattern, and nothing more; `app_settings.updated_at` is SQLite `CURRENT_TIMESTAMP` and **stays stored in that format**, normalized to ISO-8601 UTC only at the service boundary for the API; and `quantize_percentage` must not be reused for validation because it would silently round `6.005` to `6.01`.
- **Expected `C1-I` test and smoke shape.** Focused backend coverage for percentage-not-coefficient semantics, the `0.00`/`100.00` boundaries, rejection of negatives, over-100 values, three-or-more fractional digits, floats, `bool`, `NaN`, `Infinity`, and malformed strings, equivalence of `6`/`6.0`/`6.00`, `null` clear versus configured `0.00`, the no-op contract writing nothing, audited configure/change/clear, persistence and reload, and proof that no order, batch, movement, report, or historical row changes. Four assertions are called out explicitly in `docs/implementation-plan.md` § 11 because they are the easiest to implement wrongly: the **exact canonical two-decimal strings** (`6` → `"6.00"`, `100` → `"100.00"`, `6.005` rejected with nothing persisted and never `6.01`, and the no-op comparison made on that canonical string); **`effective_at` per event**, including `null` after Clear plus clear metadata carrying `previous_effective_at` and `new_effective_at: null` while `AuditLog.created_at` records the clear time, and the API being ISO-8601 while stored `updated_at` stays `YYYY-MM-DD HH:MM:SS`; **atomic delete + audit rollback**, where a forced `AuditLog` insert failure must leave the `default_tax_rate` row intact with its original value and timestamp and write no audit row, plus clearing an absent row doing nothing; and **key isolation**, proving `tax.default_rate` is untouched by configure, change, and Clear alike. Focused frontend coverage requires extracting a tax-setting feedback/presentation module into the existing focused-suite pattern, since the Settings UI is inline in `frontend/src/main.ts` and no Settings test module exists — without adding dependencies. The complete backend suite must stay at `0 failed` / `0 skipped` with the merged `562 / 562 / 0 / 0` baseline preserved and no test weakened, the frontend production build must pass, and an exact-published-head `/settings` browser smoke at desktop `1440 × 900` with isolated temporary database, user-data directory, and browser profile must prove save, redisplay as the canonical `6.00`, a configured `0.00` showing as configured rather than unconfigured, survival across refetch and reload, rejection of `6.005` with nothing persisted, an honest no-op re-save of `6` against stored `6.00`, confirmed Clear yielding `is_configured: false` / `tax_rate_percent: null` / `effective_at: null`, and an unchanged existing production batch.
- **Nothing was executed for this decision PR.** No backend pytest, no frontend tests, no frontend build, no browser smoke, no API smoke, no packaging smoke, and no release smoke were run or claimed. The merged backend baseline `562 collected, 562 passed, 0 failed, 0 skipped` is carried only as `VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE`.
- **Pre-merge correction passes.** A second commit on the same branch resolved four inconsistencies found in review and widened the allowed documentation scope. `AGENTS.md` § 6.6 now reads `tax = sale_price * tax_rate_percent / 100` with the percentage range, `6.00` meaning `6%`, missing-is-unavailable-not-zero, no historical recalculation, snapshot use once C2 lands, and `docs/settings.md` as the durable contract; every unrelated `AGENTS.md` rule is preserved. The active `docs/roadmap.md` `AppSettings MVP fields` entry now reads `default_tax_rate` with no default plus an explicit `CR-007` note superseding `tax_rate default 0.06`, and unrelated roadmap history is untouched. The same coefficient statements inside `docs/domain-model.md` — the `AppSettings` field list, the `tax_rate default is 0.06` rule, and the § 8.4 cost formula — were corrected identically. Clear persistence is now explicitly row deletion; `effective_at` no longer both exists and is `null` after Clear; the storage wording no longer implies the database stores ISO-8601; and the canonical representation is exact rather than "may use two decimals". A third commit closed the last contradiction by correcting `docs/architecture.md` § 8.6 the same way, with directly adjacent rules covering the percentage range, `6.00` meaning `6%`, missing-is-unavailable-not-zero, an explicit `0.00` being real, Decimal-only calculation, rounding only the final amount to `0.01` with `ROUND_HALF_UP`, no recalculation of historical `ProductionBatch` rows, snapshot use once C2 lands, and pointers to `docs/settings.md` and `docs/domain-model.md`; unrelated architecture sections are untouched. **Every active tax formula in the repository documentation now uses `tax_rate_percent / 100`, no coefficient default for this setting remains, and no accepted decision was reversed in any pass.**
- `state/change-requests.md` gained only the new `CR-007` row, which appears once and remains `accepted`; `CR-001` through `CR-006` are unchanged. `CR-004` — SQLite backup transaction consistency — and `CR-006` — export create-response fallback — remain separate, unresolved `needs evidence` rows, are not activated, and are not merged with `CR-007`. No `CLAUDE.md` or `.claude/` file was created or modified.
- **Read before continuing:** `docs/settings.md` for the durable contract and the repository constraints, `docs/implementation-plan.md` § 11 for the `C1-I` slice contract and the C1/C2 boundary, `docs/decisions/0011-tax-rate-setting.md` for the decision rationale and rejected alternatives, `docs/api.md` for the preferred future endpoint shape, `docs/domain-model.md` § 6.14 for the snapshot semantics, `docs/reports.md` for the report boundary, and `state/current-focus.md` for current status.
- Restore remains unimplemented, packaging, installation, update, and full release-candidate smoke remain open, C2, C3, and C4 remain inactive, and **the product is not release-ready.**

## 2026-07-27 — Handoff after the C1-I implementation on its PR branch

`C1-I — Backend-owned tax-rate setting` is **implemented on branch `claude/c1-backend-owned-tax-rate-setting` and not merged**. Status: `IMPLEMENTED — EXACT-HEAD /settings SMOKE REQUIRED BEFORE MERGE`. It is **not `DONE`**, **C2 remains blocked**, and **product release readiness is not claimed**.

The branch was created from clean `origin/main` `80b83de3e838cf676669a1b627770300590c99c0` — the merge commit of the merged `CR-007` decision PR #148, whose final reviewed head was `577e0fd0b5c3e6fc82e2399fd17f023b6e221b83`. No rebase, no force-push, no history rewrite, no auto-merge.

What exists now that did not exist on merged `main`:

- `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate`, backed by `backend/app/domain/tax_rate.py`, `backend/app/schemas/tax_rate_settings.py`, `backend/app/services/tax_rate_settings.py`, and `backend/app/api/tax_rate_settings.py`;
- the `default_tax_rate` key in the existing `app_settings` table, with **no migration and no schema change**;
- a bounded `SettingsRepository` extension: optional `connection`, an optional caller-owned `updated_at`, and `delete_setting(key, connection=None)`;
- the `Налоговая ставка для расчётов` section inside `/settings`, built from five focused frontend modules plus one extracted profile-presentation module, with `frontend/src/main.ts` shrinking from `6406` to `6399` lines;
- focused suites `backend/app/tests/test_tax_rate_settings.py`, `backend/app/tests/test_tax_rate_settings_api.py`, and `frontend/test/settings-tax-feedback.test.mjs`.

Executed evidence on that branch: backend `671 collected, 671 passed, 0 failed, 0 skipped` with all 562 original node IDs still collected; targeted settings/tax suites `123 passed`; `npm run test:settings-tax-feedback` `34 pass, 0 fail, 0 skipped`; all 13 focused frontend suites green; `npm run build` `PASS`.

Outstanding before this slice can be called `DONE`:

1. the focused exact-published-head `/settings` browser smoke at `1440 × 900`, from an external runner under a temporary root outside the repository, with an isolated database, user-data directory, `HOME`, browser profile, and runner-owned ports, and evidence kept outside Git;
2. review and merge of the open PR.

Do **not** start C2 before that. Readiness tax estimates, production tax snapshots, the nullable snapshot migration, tax amount, margin, margin percent, and report calculations from snapshots all remain C2 and are unimplemented; production readiness still returns `estimated_tax = null`, and `ProductionBatch` still has no tax snapshot columns.

Other obligations are unchanged: `CR-004` remains `needs evidence` and inactive, `CR-006` remains `needs evidence` and non-blocking, and the Restore decision, macOS packaging, installation verification, the packaged update flow, and the full release-candidate smoke all remain open.

## 2026-07-27 — Handoff after closing C1-I and deciding the bounded C2 financial contract

`C1-I — Implement backend-owned tax-rate setting` is **merged and `DONE — MERGED AND EXACT-HEAD VERIFIED`**. `CR-008` is **accepted** and records the C2 financial calculation and immutable-snapshot contract. **No C2 runtime implementation exists.** **Product release readiness is not claimed.**

This was a **documentation-only** task. No backend code, frontend code, test, schema, migration, dependency, or lockfile changed, and **no runtime tests, build, browser smoke, API smoke, migration smoke, packaging smoke, or release smoke were executed**. Every runtime result below is merged PR evidence.

Branch `claude/close-c1-decide-c2-financial-contract`, created from clean `origin/main` `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`; HEAD, `origin/main`, and the merge-base all equalled that commit before any edit. No rebase, no force-push, no history rewrite, no auto-merge.

### C1-I closure (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE)

- PR #149 `C1-I — Implement backend-owned tax-rate setting`, state `MERGED`, base `main`;
- final reviewed head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`, merged `2026-07-27T19:44:53Z`; both verified as ancestors of `origin/main`;
- decision PR #148 final reviewed head `577e0fd0b5c3e6fc82e2399fd17f023b6e221b83`, merge commit `80b83de3e838cf676669a1b627770300590c99c0`;
- backend complete suite `671 collected / 671 passed / 0 failed / 0 skipped`, all 562 original merged baseline node IDs still collected;
- focused tax-setting frontend suite `52 passed / 0 failed / 0 skipped`; all 13 focused frontend suites `568 passed / 0 failed / 0 skipped`; frontend production build `PASS`;
- exact-head `/settings` browser smoke `PASS — 146 checks / 0 failures` at head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`;
- `frontend/src/main.ts` `6406` → `6399`; **no migration added**; only the tax-rate setting was implemented, no C2 calculation.

Nothing in `C1-I` still awaits smoke, review, or merge. `CR-007` remains accepted and is now recorded implemented. Neither is reopened.

### What CR-008 decided

Formulas, `Decimal` only: `tax_amount = ROUND_MONEY(sale_price × tax_rate_percent / 100)`; `margin = ROUND_MONEY(sale_price − total_cost − tax_amount)`; `margin_percent = ROUND_PERCENT(margin / sale_price × 100)`. Percentage always divided by `100`, money and percentage quanta `0.01` with `ROUND_HALF_UP`, only the final amount rounded, tax deducted from gross revenue.

Configured `0.00` yields tax `0.00`; a missing rate or sale price yields `null` and never a fabricated zero; margin needs sale price, total cost, and tax; margin percent needs an available margin **and** a sale price greater than zero, so a zero sale price is `partial` with margin percent `null`; negative margin and margin percent are never clamped; an invalid persisted rate is handled defensively without coercion, without a fabricated zero, and without an unhandled HTTP 500.

Financial warnings are non-blocking and reuse the existing `ProductionReadinessIssue` structure. `tax_rate_missing`, `sale_price_missing`, and `cost_data_missing` are preserved; only `margin_percent_unavailable_zero_sale_price` and `tax_rate_invalid` are added; no aliases; `can_produce` is never affected by a financial gap.

Readiness reuses `estimated_cost`, `estimated_tax`, and `estimated_margin` and adds only `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, and `financial_estimate_status`. `estimated_total_cost` is not authorized.

`C2-II` will add exactly two nullable `ProductionBatch` columns, never backfilled, read the setting inside the production transaction through a bounded `connection`-aware extension of the C1 service, require both nullable confirmation-context keys (omission is **not** `null/null`), and return `409 tax_rate_context_stale` that writes nothing. Reports read snapshots only. `frontend/src/main.ts` stays at most `6399` lines throughout C2.

Durable contract: `docs/decisions/0012-c2-financial-calculation-snapshots.md`. Slice contracts: `docs/implementation-plan.md` § 11.

### Second commit — `Resolve C2 documentation contradictions`

The first commit established the C2 contract. Review found five remaining active contradictions and one incomplete lifecycle, closed by a second commit on the same branch — no amend, no rebase, no force-push, no new PR.

1. **ADR 0011 corrected directly.** `docs/decisions/0011-tax-rate-setting.md` joined the allowlist as the fifteenth file and now records `C1-I` as `DONE — MERGED AND EXACT-HEAD VERIFIED` with PR #149's head, merge commit, merge time, and smoke result. The accepted `CR-007` product meaning is unchanged and not reopened. ADR 0012's superseding note became a short lifecycle relationship note.
2. **API Settings status** now says the Workshop profile **and** `default_tax_rate` are editable, that `default_tax_rate` is the only editable calculation-sensitive setting, and that the rest stay closed. The PR96 wording survives only as an explicit historical note.
3. **API readiness limitation** no longer claims the explicit tax setting is absent; the setting exists and readiness simply does not read it yet.
4. **Implementation-plan current baseline** is now `ff7afe6b0778ab2b348229a4df34acf3e3fc0001` (PR #149 merge commit). The PR #141 baseline `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` survives only under an explicit `HISTORICAL RECORD` heading.
5. **Implementation-plan active state and MVP obligations** now say `C2-I` becomes the only authorized runtime slice after PR #150 merges, and split the old ambiguous tax row into a **closed** tax-rate-setting obligation and an **open** cost/tax/margin C2 obligation.

### Invalid persisted tax-rate lifecycle — completed contract

The gap the first commit left: readiness treated an invalid persisted rate as unavailable and non-blocking, but confirmation allowed `null/null` only for a genuinely missing setting — so an invalid rate would have made the confirmation context impossible to build and would have indirectly blocked physical production.

**`no valid configured tax-rate context`** now means either a missing `default_tax_rate` row or a persisted value that is invalid under the C1 rules.

- The two states stay distinguishable by warning: `tax_rate_missing` versus `tax_rate_invalid`, and the invalid case never also emits `tax_rate_missing`.
- Both return `tax_rate_percent = null` and `tax_rate_effective_at = null`, both give `financial_estimate_status = unavailable` with null tax, margin, and margin percent, both avoid an unhandled HTTP 500, and **neither blocks physical production**.
- Both map to the single `null/null` confirmation context. Omitting a key is still `422 tax_rate_context_required`; a partial-null, malformed, non-canonical, or out-of-range context is still `422 invalid_tax_rate_context`.
- Stale matrix: valid → changed valid, valid → missing, valid → invalid, missing → valid, and invalid → valid are all `409 tax_rate_context_stale`. **Missing ↔ invalid is not**, because both produce the same financial result.
- An accepted no-valid-rate confirmation persists null rate snapshots and null tax, margin, and margin percent while completing physical production transactionally. It never repairs, clears, rewrites, or audits the invalid setting, and never persists the raw invalid value.
- Invariant, now stated in ADR 0012, the API, the domain model, the implementation plan, the architecture, and `AGENTS.md`: an absent or invalid tax-rate setting may make financial values unavailable, but it must not by itself block physical production.

### Exact timestamp contract

| Surface | Format |
|---|---|
| database persistence (`AppSetting.updated_at`, future `tax_rate_effective_at_snapshot`) | `YYYY-MM-DD HH:MM:SS` — UTC, second precision, SQLite text, no `T`, no `Z`, no offset |
| API and confirmation context | `YYYY-MM-DDTHH:MM:SSZ` — UTC, second precision, literal `T` and `Z` |

Local time, arbitrary offsets, fractional seconds, a space instead of `T`, and a missing `Z` are rejected with `422 invalid_tax_rate_context`. `expected_tax_rate_effective_at` must be `null` or the exact canonical timestamp readiness returned. The API normalizes the stored snapshot and never exposes the raw SQLite form. No backfill.

21 additional future `C2-II` test requirements covering this lifecycle and these formats are recorded in `docs/implementation-plan.md` § 11. They are `NOT IMPLEMENTED` and were `NOT EXECUTED` here.

### Next operator instructions

1. Review and merge this documentation PR. Do **not** merge it automatically and do not enable auto-merge.
2. **Only after it merges**, start `C2-I — Backend financial readiness estimate` from the new `origin/main`. Do **not** start it from this unmerged documentation branch, and do not assign it a PR number in advance.
3. Keep `C2-I` inside its bounds: one focused backend financial domain service (preferred `backend/app/domain/production_financials.py`), the existing readiness endpoint extended additively, the five stable warning codes, focused backend tests plus readiness API integration tests, and an exact-head readiness API smoke. No migration, no persistence write, no `AuditLog`, no Order / `ProductionBatch` / movement / report change, and no frontend production change — `frontend/src/main.ts` must remain exactly `6399` lines.
4. Do **not** start `C2-II` or `C2-III`. They are `PLANNED — BLOCKED`, and `C2-III` must be subdivided before implementation if it is not one bounded vertical slice.
5. Leave `CR-004` and `CR-006` inactive, and leave C3 and C4 inactive.

Other obligations are unchanged: the Restore decision, macOS packaging, installation verification, the packaged update flow, and the full release-candidate smoke all remain open.

## C2-I handoff — implemented on an unmerged PR branch (2026-07-28)

`C2-I — Backend financial readiness estimate` is **`IMPLEMENTED ON PR BRANCH — NOT MERGED`** on branch `codex/c2-i-backend-financial-readiness-estimate`, started from merged `origin/main` `4c03142ef7acdc31fcb15730484e8e52dde95b69`. It is **not** `DONE` and must not be recorded as `DONE` until it is merged and exact-head verified.

### What exists now

- `backend/app/domain/production_financials.py` — the pure calculation. Inputs are backend-owned `sale_price`, `total_cost`, and a `TaxRateContext`; outputs are canonical two-decimal strings or `null`, the bounded `FinancialEstimateStatus`, and the ordered `warning_codes`. No connection, no repository, no FastAPI, no Pydantic, no `ProductionReadinessIssue`, no write.
- `ProductionReadinessService._estimate_financials` / `_tax_rate_context` — the only integration points. The former `_estimate_money` is gone; its behavior is preserved and extended.
- `ProductionReadinessResponse` — reuses `estimated_cost`, `estimated_tax`, `estimated_margin` and adds exactly `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, `financial_estimate_status`. `estimated_total_cost` does not exist.
- Tests: `backend/app/tests/test_production_financials.py` (new, pure domain) and extended `backend/app/tests/test_production_readiness.py`. One frontend test-only addition proves the existing readiness DTO guard tolerates the additive fields.

### Boundaries a follow-up must not cross by accident

- The rate is read through the **no-argument** `TaxRateSettingsService.get_tax_rate()`. Adding `connection=` is `C2-II` work and was deliberately left out.
- Readiness re-validates the returned percentage through the C1 domain parser because the Settings repair surface may still return raw stored text for an externally corrupted row. Do not "simplify" this into trusting `is_configured`, and do not turn the correction into a Settings refactor.
- Only `default_tax_rate` is read. The legacy `tax.default_rate` placeholder is never read or interpreted.
- Every financial warning is non-blocking. Do not let any financial condition reach `can_produce`, the blocking issues, or the physical readiness status.
- `frontend/src/main.ts` must stay at exactly `6399` lines. `C2-I` adds no financial UI and no frontend arithmetic; presentation is `C2-III`.

### Next steps

1. Review and merge the `C2-I` PR. Do **not** merge it automatically and do not enable auto-merge.
2. **Only after it merges and is exact-head verified**, `C2-II — Transactional production financial snapshots` becomes startable from the new `origin/main`. Do not start it from this unmerged branch, and do not assign it a PR number in advance.
3. `C2-II` scope stays as decided: one nullable migration adding only `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot`, the transaction-aware tax-setting read, the required-but-nullable confirmation context, the `409 tax_rate_context_stale` conflict, snapshot persistence inside the existing production transaction, and exposure in the confirmation and `ProductionBatch` detail responses only.
4. `C2-III` remains `PLANNED — BLOCKED` and must be subdivided before implementation if it is not one bounded vertical slice.
5. Leave `CR-004` and `CR-006` inactive, and leave C3 and C4 inactive.

Other obligations are unchanged: the Restore decision, macOS packaging, installation verification, the packaged update flow, and the full release-candidate smoke all remain open. Product release readiness is not claimed.

## C2-II handoff — implemented on an unmerged PR branch (2026-07-28)

> **HISTORICAL PRE-MERGE RECORD — SUPERSEDED.** This section described `C2-II` while it was still on an unmerged PR branch. `C2-II` merged as PR #152 and is now `DONE — MERGED AND EXACT-HEAD VERIFIED`; see § *C2-II closure and C2-III subdivision handoff (2026-07-28)* at the end of this file. Its final sentence about two intentionally renamed tests describes an earlier revision of the branch: both original node IDs were restored before merge, and the accepted merged result is `737 / 737` backend node IDs collected with zero renames.

`C2-I` is now **merged and exact-head verified** (PR #151, reviewed head `6f72bffc9a0d17839e3a74c69366fe17df8a318b`, merge commit `7b3dde8278f59658bfa3a81c09e643ea10319551`, exact-head readiness smoke `PASS — 113 checks / 0 failures`). The earlier `C2-I` handoff section above is preserved as history.

`C2-II — Transactional production financial snapshots` is **`IMPLEMENTED ON PR BRANCH — NOT MERGED`** on branch `codex/c2-ii-transactional-production-financial-snapshots`, started from merged `origin/main` `7b3dde8278f59658bfa3a81c09e643ea10319551`. It is **not** `DONE` and must not be recorded as `DONE` until it is merged and exact-head verified.

### What a reviewer should know

- The durable contract is unchanged: `docs/decisions/0012-c2-financial-calculation-snapshots.md`. ADR 0012 was not rewritten, reinterpreted, or expanded, and no conflict with the merged implementation was found.
- The setting is read inside the production transaction through `TaxRateSettingsService.get_tax_rate(connection=...)`. The no-argument call is unchanged. There is no second tax-setting service, no direct raw `app_settings` read in `ProductionConfirmationService`, and no generic transaction abstraction.
- Missing and invalid tax-rate states reduce to the same comparable `null/null` context in `backend/app/services/tax_rate_context.py`, which readiness and confirmation share. The missing-versus-invalid distinction survives only for readiness warning generation.
- The stale check runs before the first production write and protects the editable tax context only. The existing locked-order snapshot check, physical readiness re-check, duplicate-batch check, and `transaction(..., immediate=True)` behavior are all unchanged.
- The financial arithmetic is the merged `C2-I` domain calculation, called once. `ProductionConfirmationService` contains no formula.
- Migration `0019_production_batch_tax_rate_snapshots` is additive and idempotent. Because Python's `sqlite3` runs DDL outside the implicit transaction, a mid-migration failure can leave the added column while the `schema_migrations` insert rolls back; idempotency is what makes the retry safe, and a test proves the data and the backup both survive.
- `frontend/src/main.ts` is `6399` lines before and after. The only changes to it are two identifiers added to an existing import list and one call-site argument; all context ownership, validation, and stale handling live in `frontend/src/order-production-context.ts`.
- Two superseded tests were intentionally renamed and strengthened; both renames are justified in the PR body. Every other previously collected node ID is still collected.

### Next steps

1. Review and merge the `C2-II` PR. Do **not** merge it automatically and do not enable auto-merge.
2. **Only after it merges and is exact-head verified**, `C2-III — Financial presentation and snapshot-backed reports` becomes startable from the new `origin/main`. Do not start it from this unmerged branch, and do not assign it a PR number in advance.
3. `C2-III` remains a **planning umbrella**. Before it is authorized, repository evidence must determine whether it is one bounded, independently reviewable vertical slice; if it is not, subdivide it — for example readiness and `ProductionBatch` financial presentation, and separately snapshot-backed reports. Do not merge readiness UI, batch UI, and report backend plus frontend into one catch-all PR.
4. Reports still read no snapshots. Making them do so is `C2-III` work and must keep the snapshot-only rule: never recalculate history with the current rate, and show old rows as unavailable rather than `0.00`.
5. Leave `CR-004` and `CR-006` inactive, and leave C3 and C4 inactive.

Other obligations are unchanged: the Restore decision, macOS packaging, installation verification, the packaged update flow, and the full release-candidate smoke all remain open. Product release readiness is not claimed.

## C2-II closure and C2-III subdivision handoff (2026-07-28)

> **PARTIALLY SUPERSEDED — HISTORICAL FOR THE `C2-III` LIFECYCLE.** The `C2-II` closure evidence below stands. Its § *Next steps*, and its statement that there is no financial presentation in the UI, were true when written, before PR #154 merged. `C2-III-A` merged as PR #154 and `C2-III-B` merged as PR #157; both are `DONE — MERGED AND EXACT-HEAD VERIFIED`, **C2 is `COMPLETED`**, and its statement that reports read no snapshots no longer describes merged `main`. See § *C2 closure and C3-I AuditLog authorization handoff (2026-07-29)* at the end of this file for the current state.

`C2-II — Persist transactional production financial snapshots` is **`DONE — MERGED AND EXACT-HEAD VERIFIED`**. The `C2-II` handoff section above is preserved as history.

### Verified merged evidence

`VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #152 — `C2-II — Persist transactional production financial snapshots` |
| State | `MERGED`, base `main` |
| Final reviewed head | `0cdda1b06b9783975f085207527f7d36a2ef7f22` |
| Merge commit | `c3a3a7b8db06fe85290216113b784123ed9b6b30` |
| Merged at | `2026-07-28T09:00:50Z` |
| Exact smoke-tested head | `0cdda1b06b9783975f085207527f7d36a2ef7f22` |
| Accepted backend result | `883 passed / 0 failed / 0 skipped`; all `737` original merged-baseline node IDs still collected, zero renames |
| Accepted frontend result | all 15 focused frontend suites green, `0 failed` |
| Production build | `npm run build` — `PASS` |
| Exact-head migration smoke | `PASS — 41 checks / 0 failures` |
| Exact-head API smoke | `PASS — 57 checks / 0 failures` |
| Exact-head browser smoke | `PASS — all Orders-route checks / 0 failures` |
| `frontend/src/main.ts` final line count | `6399` |
| Migration `0019` delivered | yes — `0019_production_batch_tax_rate_snapshots` |
| Commit added after the accepted smoke | none |

`origin/main` equals the PR #152 merge commit.

### What a reviewer should know about the current state

- Merged `main` carries the `C2-I` readiness estimate **and** the `C2-II` transactional snapshots, including migration `0019`, the required-but-nullable confirmation context, and `409 tax_rate_context_stale`.
- There is still **no financial presentation in the UI** and **no report change**. Reports read no snapshots.
- The durable contract remains `docs/decisions/0012-c2-financial-calculation-snapshots.md`. It was not rewritten or reinterpreted; only the slice lifecycle statuses and the executed `C2-III` subdivision were recorded.

### C2-III is subdivided into exactly two runtime slices

ADR 0012 already required subdivision if `C2-III` was not one bounded, independently reviewable vertical slice. It is not, so the umbrella is replaced by `C2-III-A` and `C2-III-B` — no more and no fewer.

### Next steps

1. Review and merge the `C2-II` closure and `C2-III` subdivision documentation PR. Do **not** merge it automatically and do not enable auto-merge.
2. **Only after it merges**, `C2-III-A — Order and ProductionBatch financial presentation` becomes startable from the new `origin/main`. Do not start it from the unmerged documentation branch, and do not assign it a PR number in advance. It is the **only** authorized slice.
3. `C2-III-A` covers Orders readiness presentation, `ProductionBatch` detail presentation, and a compact `ProductionBatch` list financial summary — one user workflow: check Order readiness → understand the financial estimate → confirm production → see the persisted actual financial result. The rate snapshots stay detail-only and are not added to the list, and no second financial list endpoint is created. It excludes reports, report DTOs, `/reports` UI, and report documents. The frontend stays display-only, performs no arithmetic, does not reinterpret warning codes, and never substitutes the current Settings tax rate for readiness. `frontend/src/main.ts` must stay at most `6399` lines, with no financial arithmetic, DTO validation, large HTML template, or financial lifecycle state machine inside it. Full scope: `docs/implementation-plan.md` § 11.
4. `C2-III-B — Snapshot-backed reports and report documents` remains `PLANNED — BLOCKED` until `C2-III-A` is implemented, reviewed, exact-head smoke verified, and merged. Do not authorize or start it now, and do not assign it a PR number. When it is authorized, reports must read persisted snapshots only, never recalculate history with the current rate, keep old rows unavailable rather than `"0.00"`, keep configured zero tax a real value, and update the `/reports` DTO and frontend together with the `Сводка мастерской` document it feeds. It must not change Orders readiness or `ProductionBatch` UI.
5. **Do not invent an aggregate report percentage formula.** The only accepted aggregate basis is the existing documented `known_margin_percent` paired basis in `docs/reports.md`. An arithmetic average of batch percentages, a weighted average of batch percentages, aggregate margin divided by aggregate revenue, and recalculation from current settings must not be chosen silently without an explicit later contract. Before authorizing `C2-III-B`, inspect the current report queries, paired revenue/cost behavior, incomplete-data counters and warnings, the finance and overview report schemas, the frontend `/reports`, report-document generation, and the existing tests and smoke boundaries.
6. `C2 is not complete after C2-III-A.` Leave `CR-004` and `CR-006` inactive, do not reopen ADR 0011, `CR-007`, or `CR-008`, and leave C3 and C4 inactive.

Other obligations are unchanged: the Restore decision, macOS packaging, installation verification, the packaged update flow, and the full release-candidate smoke all remain open. Product release readiness is not claimed.

## C2-III-A handoff — implemented on an unmerged PR branch (2026-07-28)

> **HISTORICAL PRE-MERGE RECORD — SUPERSEDED.** This section described `C2-III-A` while it was still on an unmerged PR branch and was true when written. `C2-III-A` merged as PR #154 and is now `DONE — MERGED AND EXACT-HEAD VERIFIED`; see § *C2-III-A closure and C2-III-B authorization handoff (2026-07-28)* at the end of this file.

`C2-III-A — Order and ProductionBatch financial presentation` was **`IMPLEMENTED ON PR BRANCH — NOT MERGED`** on branch `codex/c2-iii-a-production-financial-presentation`, started from merged `origin/main` `1eb0d5420eaabbd8f61a66dba523f058a38826a6` — the PR #153 merge commit. It was **not** `DONE` at that point and was not to be recorded as `DONE` until merged and exact-head verified — which has since happened.

### What is on the branch

- Two focused frontend modules — `frontend/src/production-financial-contract.ts` (financial DTO types, the `available` / `partial` / `unavailable` status enum, readiness financial validation) and `frontend/src/production-financial-presentation.ts` (every financial render function, plus the two per-line batch cost-snapshot tables moved out of `frontend/src/main.ts`). The canonical tax-rate pair checks stay in the existing `frontend/src/order-production-context.ts`.
- The readiness financial block inside the existing result card, with the three accepted Russian status labels, the human-readable `Ставка действует с:` line when a rate is configured, and no warning of its own — backend financial warnings are still shown once through the existing readiness warning section.
- One shared `Фактическая экономика партии` block used by both the production-success card and the historical `ProductionBatch` detail.
- A compact five-field financial summary in the `/production` history list, with the rate snapshots still detail-only.
- Tightened DTO validation: the complete readiness financial contract, and both `ProductionBatch` rate-snapshot keys required present, with explicit `null/null` still valid.
- `frontend/src/main.ts` `6399` → `6398` lines; no backend production source changed and no backend test changed.

### What the next task had to do

1. Review and merge the `C2-III-A` PR. Do **not** merge it automatically and do not enable auto-merge. — **done: PR #154 merged.**
2. **Only after it merges and is exact-head verified**, record `C2-III-A` as `DONE — MERGED AND EXACT-HEAD VERIFIED` and close the active documentation and state consistently. — **done in the closure section below.**
3. `C2-III-B — Snapshot-backed reports and report documents` remains `PLANNED — BLOCKED` until `C2-III-A` is merged and exact-head verified. — **superseded: that gate is now satisfied and `C2-III-B` is authorized below.** Its boundary and the ban on silently inventing an aggregate margin-percent formula are unchanged.
4. Do not extend `C2-III-A` into reports, report DTOs, `/reports` UI, report documents, the overview finance summary, or dashboard financial cards — none of those changed in it.
5. `C2 is not complete after C2-III-A.` Leave `CR-004` and `CR-006` inactive, do not reopen ADR 0011, `CR-007`, or `CR-008`, and leave C3 and C4 inactive.

Other obligations are unchanged: the Restore decision, macOS packaging, installation verification, the packaged update flow, and the full release-candidate smoke all remain open. Product release readiness is not claimed.

## C2-III-A closure and C2-III-B authorization handoff (2026-07-28)

> **PARTIALLY SUPERSEDED — HISTORICAL FOR THE `C2-III-B` LIFECYCLE.** The `C2-III-A` closure evidence below stands and is not reopened. Its § *What a reviewer should know about the current state* and § *What the next task must do* describe `C2-III-B` as unstarted, unassigned and startable only from a future `main`; that was true when written and is now **superseded**. `C2-III-B` merged as PR #157 and is `DONE — MERGED AND EXACT-HEAD VERIFIED`, so **C2 is `COMPLETED`** and its statement that reports are not snapshot-backed no longer describes merged `main`. See § *C2 closure and C3-I AuditLog authorization handoff (2026-07-29)* at the end of this file.

`C2-III-A — Order and ProductionBatch financial presentation` is:

```text
C2-III-A — Order and ProductionBatch financial presentation:
DONE — MERGED AND EXACT-HEAD VERIFIED
```

### Verified merged evidence

`VERIFIED FROM MERGED PR #154 EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #154 — `C2-III-A — Present Order and ProductionBatch financials` |
| State | `MERGED`, base `main` |
| Final reviewed head | `ef1103811a8f062f9129bfb465a98e0cfa388935` |
| Merge commit | `d432fcaee52a16a4f8b609ec160cf3fa2b33d013` |
| Merged at | `2026-07-28T13:05:34Z` |
| Exact smoke-tested head | `ef1103811a8f062f9129bfb465a98e0cfa388935` — identical to the final reviewed head |
| Focused frontend suites | `order-readiness-presentation` `19 pass`; `order-mutation-lifecycle` `33 pass`; `order-production-context` `25 pass`; `order-production-feedback` `21 pass`; new `production-financial-presentation` `22 pass` — all `0 fail / 0 skipped` |
| Complete frontend test-script result | all 16 `test:*` scripts pass, `0 failed`, `0 skipped` |
| Frontend production build | `npm run build` — `PASS` |
| Focused backend result | `160 passed / 0 failed / 0 skipped` across the four production suites |
| Complete backend result | `883 passed / 0 failed / 0 skipped`, byte-identical to the pre-change baseline, all `883` node IDs still collected |
| Exact-head API smoke | `PASS — 67 checks / 0 failures` |
| Exact-head browser smoke | `PASS — 28 checks / 0 failures` |
| `frontend/src/main.ts` | `6399` before → `6398` after |
| Commit added after the accepted smoke | none — the head was verified unchanged and the tree clean afterwards |
| Backend formulas, persistence, migrations and reports | unchanged in `C2-III-A` |

`origin/main` at the start of this documentation branch is `d432fcaee52a16a4f8b609ec160cf3fa2b33d013`, equal to the PR #154 merge commit.

### What a reviewer should know about the current state

- Merged `main` carries the `C2-I` readiness estimate, the `C2-II` transactional snapshots and migration `0019`, and the `C2-III-A` financial presentation in the Orders and `ProductionBatch` UI.
- **Reports are still not snapshot-backed on merged `main`.** There, `/reports`, the report DTOs, the overview finance summary and `Сводка мастерской` read no `ProductionBatch` financial snapshots. *(Superseded: PR #157 merged, so reports on `main` now read the persisted snapshots.)*
- The durable contracts remain `docs/decisions/0012-c2-financial-calculation-snapshots.md` and `docs/reports.md`. Neither was rewritten or reinterpreted; only the slice lifecycle and the `C2-III-B` authorization were recorded.

### What the next task must do

1. Review and merge this documentation PR. Do **not** merge it automatically and do not enable auto-merge.
2. **Only after it merges**, `C2-III-B — Snapshot-backed reports and report documents` becomes startable from the new `origin/main`. Do not start it from this unmerged documentation branch, and do not assign it a PR number in advance. It is the **only** remaining authorized C2 runtime slice.
3. `C2-III-B` covers one bounded backend-plus-frontend report vertical: persisted `ProductionBatch` financial snapshots → backend report aggregation → report DTOs → `/reports` presentation → overview report consumers → generated `Сводка мастерской`. Report tax comes only from persisted `ProductionBatch.tax` and report margin only from persisted `ProductionBatch.margin`; historical tax and margin are never recalculated from the current Settings rate; report calculations stay backend-owned; report endpoints stay read-only and create no audit records or business mutations; and the frontend stays display-only and calculates no report tax, margin, margin percentage, incomplete-data coverage, or historical value. Full scope: `docs/implementation-plan.md` § 11 and `docs/reports.md`.
4. Keep `null`, zero and negative distinct: explicit stored `"0.00"` is a real known zero, `null` is unavailable or incomplete, negative margin and negative margin percentage are valid signed information, and a missing historical snapshot is different from configured zero tax. A null snapshot is never rendered or aggregated as a fabricated `0`, `0.00`, `0 ₽`, or `0%`, and batches with incomplete snapshots must feed explicit incomplete-data counters or warnings rather than silently appearing complete.
5. **Do not invent an aggregate report percentage formula.** *(SUPERSEDED — the conflict this anticipated was found and resolved; see § C2-III-B report aggregation contract clarification handoff (2026-07-28) at the end of this file.)* The only accepted aggregate basis is the existing documented `known_margin_percent` paired basis in `docs/reports.md` — the same complete paired sale-price/cost basis as `known_margin`, not the global known-revenue total. An arithmetic average of row percentages, a weighted average of row percentages, aggregate margin divided by all known revenue, and recalculation using the current tax setting must not be chosen silently. Inspect the current report queries, schemas and tests first, and if the documented paired basis contradicts the code required for snapshot-backed aggregation, **stop and report the exact conflict** instead of inventing a formula.
6. `Сводка мастерской` is in scope only as a consumer of the affected report DTO. Newly generated documents may reflect the snapshot-backed result; previously generated documents remain immutable and are never rewritten, regenerated, or silently replaced; document generation remains an explicit user action.
7. Do not change Orders readiness, Order production confirmation, the Order lifecycle, `ProductionBatch` persistence, `ProductionBatch` list or detail presentation, the `C2-III-A` presentation modules, tax-rate Settings behavior, migrations, historical `ProductionBatch` rows, or stock and production transactions.
8. `C2 is not complete in this documentation PR.` C2 becomes complete only after `C2-III-B` is implemented, its focused and complete tests pass, its exact-head API and browser smoke pass, it is reviewed and merged, and the final active C2 documentation and state are closed consistently. Leave `CR-004` and `CR-006` inactive, do not reopen ADR 0011, `CR-007`, or `CR-008`, and leave C3 and C4 inactive.

Other obligations are unchanged: the Restore decision, macOS packaging, installation verification, the packaged update flow, and the full release-candidate smoke all remain open. Product release readiness is not claimed.

## C2-III-B report aggregation contract clarification handoff (2026-07-28)

> **PARTIALLY SUPERSEDED — HISTORICAL FOR THE `C2-III-B` LIFECYCLE.** The accepted aggregation contract recorded below stands and is unchanged. Its § *Next steps*, and every statement that `C2-III-B` is unimplemented, unmerged or has no PR number, were true when written and are **superseded**: `C2-III-B` merged as PR #157 (merge commit `87410910aad472343c057f0bcbfcc3797f8b8e09`, merged `2026-07-28T22:21:18Z`), and **C2 is `COMPLETED`**. See § *C2 closure and C3-I AuditLog authorization handoff (2026-07-29)* at the end of this file.

This is a **documentation-only** handoff. No backend or frontend production code, test, schema, migration, dependency, lockfile, package script, smoke runner or generated report document was changed.

### Why this PR exists

The `C2-III-B` runtime implementation was attempted. Its mandatory read-only Phase 0 contract audit returned `STOPPED — CONTRACT CONFLICT` and recorded:

```text
C2-III-B — BLOCKED BY REPORT AGGREGATION CONTRACT CONFLICT
```

That attempt was a **read-only diagnostic, not an implementation PR**. It created **no branch, no edit, no commit and no pull request** — precisely the behaviour every active document required. This PR resolves the blocker so the runtime slice can proceed.

The conflict: the merged implementation derives `known_margin` from paired `sale_price` and `total_cost`, while the authorized contract requires reports to read persisted `ProductionBatch.tax` and `ProductionBatch.margin` only. The paired row set `P` and the persisted-margin row set `M` coincide only while margin is derived. Under snapshot-backed aggregation they diverge, because a row can carry a known sale price and a known total cost with `tax` and `margin` both `null` — the ADR 0012 matrix row *present / present / missing*, and every pre-`C2-II` row, since there is no backfill. "The same basis as `known_margin`" therefore named two different denominators, and the legacy counters could not stay truthful without being silently repurposed.

### Accepted contract

```text
R = all ProductionBatch rows
P = rows where both sale_price and total_cost are non-null
T = rows where persisted tax is non-null
M = rows where persisted margin is non-null
```

- `known_tax` = Σ non-null persisted `ProductionBatch.tax`; `null` when no tax snapshot exists; `"0.00"` when snapshots exist and sum to zero. Null never contributes zero.
- `known_margin` = Σ persisted `ProductionBatch.margin` over exactly `M`. Signs preserved; `"0.00"` is a real zero; nothing is derived, repaired or backfilled.
- `known_margin_percent` = `ROUND_PERCENT(Σ margin over M ÷ Σ sale_price over M × 100)`, `null` when `M` is empty or that denominator is zero.

The denominator uses sale prices from exactly the rows contributing to the numerator. The global `known_revenue` is never the denominator, and persisted row `margin_percent` is never summed or averaged. `P` and `M` are never treated as the same set.

A zero-sale row with non-null margin is in `M`: it contributes its margin, contributes zero to the denominator, and does not by itself make the percentage available.

`complete_finance_record_count` and `incomplete_margin_count` keep their existing paired sale-price/cost meanings for backward compatibility, are documented as legacy paired-input coverage, and are **not** snapshot-coverage counters. Additive DTO fields: `known_tax`, `tax_snapshot_record_count`, `missing_tax_snapshot_count`, `margin_snapshot_record_count`, `missing_margin_snapshot_count`, with each counter pair summing to `produced_order_count`. Additive warnings: `tax_unavailable`, `partial_tax_basis`, `margin_percent_unavailable_zero_basis`. `margin_unavailable` and `partial_margin_basis` are preserved but restated against margin snapshots.

Full contract: `docs/reports.md` § *Accepted `C2-III-B` snapshot aggregation contract*; ADR 0012 § *Accepted clarification — snapshot report aggregation contract*.

### What the next task must do

1. Review and merge this documentation PR. Do **not** merge it automatically and do not enable auto-merge.
2. **Only after it merges**, start `C2-III-B — Snapshot-backed reports and report documents` from the new `origin/main`. Do not start it from this unmerged documentation branch, and do not assign it a PR number in advance. It remains the **only** remaining authorized C2 runtime slice.
3. Implement against the accepted contract above. The formula, the denominator basis, the zero-sale rule, the counter identities, the exact additive field names and the warning conditions are all settled — they must be implemented as written, not re-derived.
4. Reports read persisted snapshots only. Never read the current Settings tax rate, never recalculate a historical row, never convert `null` to zero, keep configured zero distinct from missing, and keep negative values signed.
5. The frontend stays display-only and calculates no report tax, margin, margin percentage, snapshot coverage, counter or historical value.
6. `Сводка мастерской` is in scope only as a consumer of the affected report DTO. Previously generated documents remain immutable; document generation remains explicit.
7. Do not change Orders readiness, Order production confirmation, the Order lifecycle, `ProductionBatch` persistence, `ProductionBatch` list or detail presentation, the `C2-III-A` presentation modules, tax-rate Settings behavior, migrations, historical `ProductionBatch` rows, or stock and production transactions.
8. `C2 is not complete.` It becomes complete only after `C2-III-B` is implemented, its focused and complete tests pass, its exact-head API and browser smoke pass, it is reviewed and merged, and the final active C2 documentation and state are closed consistently. Leave `CR-004` and `CR-006` inactive, do not reopen ADR 0011, `CR-007` or `CR-008`, and leave C3 and C4 inactive.

### What a reviewer should know

- `origin/main` at this branch's start was `8eed36c1f749628865d743ff88eace3ffa2c56a5`, the verified PR #155 merge commit; it had not advanced.
- Reports are still **not** snapshot-backed. `/reports`, the report DTOs, the overview finance summary and `Сводка мастерской` are unchanged in this PR and still read no `ProductionBatch` financial snapshots.
- ADR 0012 was amended only as an explicit accepted clarification appended to its existing `C2-III-B` section. Its accepted product decision is unchanged. No new ADR and no new Change Request was created.
- Superseded paragraphs are labelled `HISTORICAL — RESOLVED` rather than deleted; dated records that were true when written are preserved.
- **Not executed, because this PR is documentation-only:** backend tests, frontend tests, `npm run build`, API smoke, browser smoke, migration smoke, packaging smoke and release smoke.

Other obligations are unchanged: the Restore decision, macOS packaging, installation verification, the packaged update flow, and the full release-candidate smoke all remain open. Product release readiness is not claimed.

---

## C2-III-B snapshot-backed reports implementation handoff (2026-07-28)

> **SUPERSEDED — the slice is now merged.** What was built, and the review corrections, stand. Its status line `IMPLEMENTED ON PR BRANCH — NOT MERGED`, its § *Next steps* asking for review and merge, and its statement that C2 is not complete were true when written and are superseded: PR #157 merged at `87410910aad472343c057f0bcbfcc3797f8b8e09` on `2026-07-28T22:21:18Z`, and **C2 is `COMPLETED`**. See § *C2 closure and C3-I AuditLog authorization handoff (2026-07-29)* at the end of this file.

`C2-III-B — Snapshot-backed reports and report documents` is:

```text
C2-III-B — IMPLEMENTED ON PR BRANCH — NOT MERGED
```

| Item | Value |
|---|---|
| Branch | `codex/c2-iii-b-snapshot-backed-reports` |
| Started from | clean `origin/main` `7369e7f133f0ce02aea5f2021cbb0e14104b7b34` (PR #156 merge commit) |
| PR #156 verification | `MERGED`, head `75ae6d22dbe6ee556c6571596a1b7dd5fe8b517d`, merged `2026-07-28T16:56:28Z` — every expected value matched |
| Backend aggregation | `backend/app/domain/report_financials.py` (pure; no connection, no FastAPI, no Pydantic, no Settings read) |
| Frontend modules | `frontend/src/report-financial-contract.ts`, `frontend/src/report-financial-presentation.ts` |
| `frontend/src/main.ts` | `6398` before → `6398` after |
| Backend suite | `942 passed / 0 failed / 0 skipped` (baseline `883`, all `883` baseline node IDs still collected) |
| Frontend suites | all 17 `test:*` scripts pass, `0 failed`, including the new `test:report-financial-presentation` (`54 pass`; the earlier `40 pass` in this row was stale when written and is superseded) |
| Build | `npm run build` `PASS` |
| Exact-head smoke | API and browser smoke are recorded in the PR body as this PR's evidence |

### What changed

- The contract conflict recorded by the Phase 0 audit is **resolved in runtime**. Reports read the persisted `ProductionBatch` snapshots only: `known_tax` is the sum of non-null persisted `tax`, `known_margin` is the sum of persisted `margin` over `M`, and `known_margin_percent` divides that margin total by the sale prices of exactly the rows in `M`.
- The exact authorized additive DTO fields are implemented: `known_tax`, `tax_snapshot_record_count`, `missing_tax_snapshot_count`, `margin_snapshot_record_count`, `missing_margin_snapshot_count`. Each counter pair sums to `produced_order_count`.
- `complete_finance_record_count` and `incomplete_margin_count` keep their legacy paired sale-price/cost meanings and are presented under `Полнота исходных данных` with truthful labels — never as snapshot coverage.
- The three additive warnings `tax_unavailable`, `partial_tax_basis` and `margin_percent_unavailable_zero_basis` are implemented; `margin_unavailable` and `partial_margin_basis` are restated against persisted margin snapshots without being renamed.
- `OverviewReportResponse.finance_summary` is the same `FinanceReportResponse`, and `/reports` renders both tabs through one presentation module. The frontend performs no financial arithmetic and validates the finance DTO strictly, failing the read into the existing retained-snapshot path rather than rendering a malformed response.
- The Reports warning panel no longer prints raw DTO field names. It shows `Показатель: <человекочитаемое название>` via a label map owned by the report presentation module, and shows nothing for an unrecognized field.
- A newly generated `Сводка мастерской` shows the persisted tax and margin, both coverage counts, and wording that says the values were saved at production time and are not recalculated from the current rate. The old `Налог не рассчитывается в этом документе` line was false once tax is shown and is replaced. Previously generated documents and sidecars remain byte-identical.

### Review corrections (PR #157, after head `8f50e741469b7f5097c1c38dfcdfa52287d9d3d1`)

- **Monetary DTO validation is now canonical.** Every finance monetary and percentage field accepts only an explicit `null` or a canonical signed two-decimal string (`^-?(?:0|[1-9]\d*)\.\d{2}$`), checked by character shape with no numeric conversion and no trimming, padding, rounding or repair. A malformed decimal fails the finance read into the existing retained-snapshot path.
- **Tax and margin coverage are explained separately.** The single note that claimed the affected batches were absent from both totals — and called them old — is replaced by one backend-warning-driven statement per total, each appearing at most once, neither mentioning the other total. Overview and Finance share the helper, so both surfaces state it identically. `Сводка мастерской` was reviewed and left unchanged: its wording is already qualified and prints each coverage count separately, so it never carried the coupling.
- **No backend formula, row set, DTO field name or warning condition changed**, and `frontend/src/main.ts` stays at `6398` lines with no validation or coverage copy added to it.

### Next steps

1. Review and merge this runtime PR. Do not merge it here and do not enable auto-merge.
2. **Only after it merges**, close the `C2-III-B` lifecycle in the active documentation and state, and only then may C2 be assessed as complete.
3. `C2 is not complete.` C2 remains incomplete until `C2-III-B` is reviewed, exact-head verified and merged, and its active lifecycle is closed.
4. Leave `CR-004` and `CR-006` inactive, do not reopen ADR 0011, `CR-007`, `CR-008` or the accepted report contract, and leave C3 and C4 inactive.
5. Product release readiness is not claimed.

### Boundaries honoured

- No migration, no historical backfill, no report persistence table, no new endpoint.
- No change to Orders readiness, production confirmation, `ProductionBatch` persistence, `ProductionBatch` list or detail UI, the `C2-III-A` presentation modules, tax-rate Settings behaviour, or stock and production transactions.
- Report reads remain read-only: no audit record, no file, no business mutation.
- No accounting, tax filing, VAT, tax regimes, date filters, charts, forecasting, analytics, tax-rate averages, DOCX, automatic document regeneration, `C3`, `C4`, Restore, packaging or release work. No dependency and no lockfile changed.

## HISTORICAL — SUPERSEDED — C2 closure and C3-I authorization handoff (2026-07-29)

> This handoff was true before C3-I implementation and PR #159 merge. Its next-step instructions are superseded by the 2026-07-30 handoff at the top of this file.

### Verified lifecycle

```text
C1 — COMPLETED
C2 — COMPLETED
C2-III-B — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-I — AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED
C4 — INACTIVE — NEEDS PRODUCT DECISION
Product release readiness — NOT CLAIMED
```

`VERIFIED FROM MERGED PR #157 EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #157 — `C2-III-B — Implement snapshot-backed reports and report documents` |
| State | `MERGED`, base `main`, not a draft |
| Head branch | `codex/c2-iii-b-snapshot-backed-reports` |
| Final reviewed head | `305d5421e79b8cb833df9588e705e9418781e021` |
| Merge commit | `87410910aad472343c057f0bcbfcc3797f8b8e09` |
| Merged at | `2026-07-28T22:21:18Z` |
| `origin/main` at branch start | `87410910aad472343c057f0bcbfcc3797f8b8e09` — equal to the merge commit, with no commit after it |
| Open pull requests at branch start | none |
| Exact-head API smoke | `PASS — 53 checks / 0 failures` |
| Exact-head browser smoke | `PASS — FULL AUTOMATED SMOKE PASSED` |
| Complete backend suite | `942 passed / 0 failed / 0 skipped` |
| Focused report frontend suite | `54 pass / 0 fail` |
| All 17 frontend test scripts | `PASS` |
| Production build | `PASS` |
| `frontend/src/main.ts` | `6398` lines |

### What this pull request did

Exactly two things: it closed the merged C2 lifecycle, and it defined and authorized one bounded C3 runtime slice. It is documentation-only — every changed file ends in `.md`, and no runtime code, test, schema, migration, dependency, lockfile, package script, generated artifact, smoke runner or user data changed.

Merged `main` reports now read persisted `ProductionBatch` financial snapshots. The former paired sale-price/cost margin derivation is gone from `main`, and every active document that still claimed otherwise was corrected.

### The accepted `C3-I` contract

Durable contract: **`docs/audit-log.md`**. It is authoritative; `docs/api.md`, `docs/domain-model.md`, `docs/roadmap.md` § PR27 and `docs/implementation-plan.md` § C3 defer to it.

- **Purpose.** `Журнал действий` — a plain-language history of important workshop actions, so the user can understand what happened without opening SQLite, JSON, logs, GitHub or a terminal. Not a technical admin console, database browser, SIEM, analytics, rollback, event editor or debugging console.
- **Actor field — `actor_type`, not `source`.** The API keeps the persisted column name and exposes `actor_type` / `actor_label`. **No `source` field is exposed or authorized.** `system` and `user` are **actor identities, not process origins**, so mapping them onto `source` would silently change the field's meaning. Labels: `system → Система`, `user → Пользователь`, anything else → `Другой инициатор`. The historical process vocabulary (`manual`, `import`, `production`, `migration`, `backup`, `onboarding`, `restore`) is aspirational — no call site persists that dimension — so a true `source` is **deferred** to a separately authorized decision and write-side slice. No column rename, no migration, no backfill, no write-call-site change.
- **API.** Exactly one new endpoint, `GET /api/audit-logs`. `GET /api/audit-logs/{id}` is **explicitly superseded for the MVP**. No create, update, delete, rollback or export endpoint.
- **Safe read model.** `items`, `total`, `limit`, `offset`, `filter_options`; item fields exactly `id`, `created_at`, `action`, `action_label`, `entity_type`, `entity_label`, `display_summary`, `actor_type`, `actor_label`. The raw persisted summary, raw `metadata_json`, `entity_id`, table names, stack traces, SQL, paths, payloads and secrets are never returned, and sensitive client text is never reconstructed. Unknown codes fall back to `Другое действие`, `Другая сущность`, `Другой инициатор`.
- **`display_summary`.** The raw `audit_logs.summary` is **never returned verbatim and is never an unrestricted fallback**. A focused backend presenter (`AuditLogDisplayPresenter` or equivalent) resolves a safe Russian value from the known `action` — no internal IDs, no metadata, no business-table join, no historical rewrite, no sensitive text. A suffix may contribute only through the seven-condition rule and the exact 21-row allowlist of `docs/audit-log.md` § 6.4; unknown actions and unrecognized summary shapes fall back to `action_label`.
- **Ordering and pagination.** `created_at DESC, id DESC`; `limit` default `50`, accepted integer `1..200`; `offset` default `0`, accepted integer `>= 0`. Ordered precedence — missing → default; wrong type/fractional/boolean/malformed → `non_integer_quantity`; negative → `negative_quantity`; non-negative `limit` of `0` or `> 200` → `pagination_out_of_range` — so every invalid input has exactly one code. Invalid values are **rejected, never silently clamped**. No unbounded history.
- **Filters.** `created_from` inclusive, `created_before` exclusive, plus `action`, `entity_type`, `actor_type`, `limit`, `offset` — **no `source` filter** — combined with AND, ISO-8601 UTC, structured `422` with the existing `invalid_date` code for malformed input, options derived from values that actually exist as rows in `audit_logs`, no writes.
- **Validation wire shape.** `HTTPException(status_code=422, detail=issue.__dict__)` means the `DomainIssue` is the **value of `detail`**: the body is `{"detail": {"code", "message", "field", "value", "next_action"}}`. Codes are `invalid_date`, `non_integer_quantity`, `negative_quantity`, plus the one new authorized enum member `PAGINATION_OUT_OF_RANGE = "pagination_out_of_range"`. The date-range conflict returns `field: created_before`.
- **Read-only.** No audit record, no business mutation, no file, no setting change, no regeneration, no normalization of historical rows. Append-only preserved — the presenter changes only what is shown.
- **Frontend.** `/settings/audit-log`, title `Журнал действий`, full state set including filtered-empty and refresh-failure-retaining-previous-list, keyboard accessible, narrow viewport safe. Filters are date, action, entity and actor. No raw codes, no raw persisted summary, no JSON, `metadata_json`, table names, internal IDs, stack traces, SQL, developer paths or GitHub/PR terminology. Focused modules only; `frontend/src/main.ts` must not grow net from its current `6398` lines.

### Findings the implementer must not rediscover

- **Current write vocabulary.** 50 `action` codes, 19 `entity_type` values, and two `actor_type` values — `system` (default) and `user` (only `tax_rate_setting_changed`). These were read from merged-`main` production call sites, **not** by querying a database containing a row for every code, so a real database may hold fewer of them and an older one may hold values no current call site produces. `filter_options` is therefore derived from rows that actually exist, and the unknown-code fallbacks are mandatory. Required Russian labels are tabulated in `docs/audit-log.md` § 11.
- **`ImportDraft` is PascalCase** while every other `entity_type` is snake_case. Match it as persisted; do not normalize, alias or rewrite it.
- **Most persisted summaries are English** (`Client created: …`, `Order #4 produced as batch #7`); only the `onboarding.*`, `demo_data.*` and `tax_rate_setting_changed` summaries are Russian, and several embed internal record IDs. That is why the raw summary is never returned and `display_summary` is resolved from `action` instead. Rewriting history is forbidden; changing what future writes put in a summary is a separate slice.
- **`client_wish.*` summaries embed the user-authored wish title**, so those actions are excluded from the name-retention allowlist and always render generically as `Пожелание клиента добавлено` and the analogous forms. `client_recipe.*` is excluded on the same reasoning, because an individual-formula title can describe a client's personal condition.
- **Coverage gap:** backups, exports, report-document generation and workshop-profile updates write **no** audit record on merged `main`. `Журнал действий` will not show them. Do not add those write call sites in `C3-I`.
- **Route architecture:** every existing frontend route is a single path segment resolved through a flat exact-match table in `frontend/src/main.ts`. `/settings/audit-log` is the first nested route, so route resolution, the navigation entry under `Данные и настройки`, and the nested-path static fallback all need handling.

### Next steps

1. Merge this documentation pull request. Do not merge it here and do not enable auto-merge.
2. **Only after it merges**, implement `C3-I` as one bounded backend-plus-frontend read-only slice on a new branch from clean `origin/main`. Do not start it from this unmerged branch and do not assign a PR number before GitHub creates it.
3. Keep `C3-I` inside `docs/audit-log.md`. No second C3 slice is authorized.
4. Leave `CR-004` and `CR-006` inactive; do not reopen ADR 0011, ADR 0012, `CR-007`, `CR-008` or the accepted report contract.
5. **C4, Restore, packaging, the update flow and release-candidate work remain inactive.** Product release readiness is not claimed.

### Verification performed here

Level 0 documentation checks only: `git status --short --untracked-files=all`, `git diff --check`, `git diff --stat`, `git diff --name-only`, and the three-dot `origin/main...HEAD` variants, plus the semantic consistency audit across active documentation and state. Every changed file ends in `.md`. **Backend tests, frontend tests, the build, API smoke, browser smoke, migration smoke, packaging smoke and release smoke were not run.** No runtime command is claimed as executed.

## C3-I contract correction handoff (2026-07-29, PR #158)

Review of PR #158 at head `25d48f3848b9277ab31f768fcbbbf35505342a1e` accepted the **C2 lifecycle closure** and the **bounded C3 direction**, and rejected the C3 contract for two semantic contradictions and one API ambiguity. All three are corrected in the same PR; no new branch and no new PR were created. `C2 — COMPLETED` and `C2-III-B — DONE — MERGED AND EXACT-HEAD VERIFIED` are untouched.

### What changed in the contract

| Before | After |
|---|---|
| `source`, `source_label`, `source` filter | `actor_type`, `actor_label`, `actor_type` filter |
| unknown source → `Другой источник` | unknown actor → `Другой инициатор` |
| `actor_type → source` described as a harmless read-time rename | rename rejected; `system` / `user` are **actors, not process origins**; a true `source` is **deferred** until write call sites persist that dimension |
| item field `summary`, returned verbatim from `audit_logs.summary` | item field `display_summary`, produced by a backend presenter; the raw persisted summary is **never returned** |
| "the existing structured Russian validation response" | the exact body `{"detail": {"code", "message", "field", "value", "next_action"}}` |
| pagination bounds stated without rejection semantics | explicit reject-not-clamp rules and error codes |
| "actual persisted values" | "current write vocabulary — values producible by merged-`main` production call sites" |

### Corrected item shape

```text
id
created_at
action
action_label
entity_type
entity_label
display_summary
actor_type
actor_label
```

### Corrected filters

```text
created_from
created_before
action
entity_type
actor_type
limit
offset
```

There is no `source` filter.

### Actor labels

```text
system → Система
user   → Пользователь
other  → Другой инициатор
```

### `display_summary` rules the implementer must follow

Resolved from the known `action`; Russian and user-readable; the raw persisted summary is never an API or frontend fallback; no internal IDs; no raw metadata; no business-table join; no historical row rewritten; no wish text, client notes, allergies, addresses or feedback bodies; a known safe business name only through the explicit action-specific allowlist in `docs/audit-log.md` § 6.4, which **excludes `client_wish.*` and `client_recipe.*`**; unknown actions and unrecognized summary shapes fall back to the resolved `action_label`.

```text
Ingredient lot created for ingredient #12  →  Создана партия компонента
Order #4 produced as batch #7              →  Производство заказа подтверждено
Client wish created: Убрать компонент X    →  Пожелание клиента добавлено
```

### Validation

```json
{
  "detail": {
    "code": "invalid_date",
    "message": "Russian user-readable message",
    "field": "created_from",
    "value": "the rejected value",
    "next_action": "Russian user-readable next action"
  }
}
```

Codes: `invalid_date` for malformed dates and for `created_before <= created_from`, never a silent empty result; `non_integer_quantity` for non-integer, fractional, boolean or malformed `limit`/`offset`; `negative_quantity` for negative values; `pagination_out_of_range` for a **non-negative** `limit` outside `1..200`. The last is the **one** new `DomainIssueCode` member authorized by `C3-I` — an enum addition, not a schema change or migration.

Pagination: omitted `limit` → `50`, accepted integer `1..200`; omitted `offset` → `0`, accepted integer `>= 0`. An explicitly supplied invalid value is **rejected, never silently clamped, coerced, rounded or ignored**.

> **Refined by the second review — see § *C3-I contract ambiguity resolution handoff (2026-07-29, PR #158, second review)* at the end of this file.** The codes above are now governed by an ordered precedence in which the first match wins, so `limit=-1` is only `negative_quantity` and `limit=0` is only `pagination_out_of_range`. The date-range conflict returns `field: created_before`, never a synthetic `date_range`.

### Still true from the previous handoff

The lifecycle table, the PR #157 evidence, the current write vocabulary (50 actions, 19 entity types, two actor types), the `ImportDraft` PascalCase note, the audit coverage gap for backups/exports/report documents/workshop profile, and the nested-route note for `/settings/audit-log` all stand unchanged.

### Verification

Level 0 documentation checks only, plus the semantic consistency audit. **Backend tests, frontend tests, the build and every smoke were not run** for this correction. No runtime code, test, schema, migration, dependency, lockfile, package script, generated file or user data changed. PR #158 stays open and unmerged with auto-merge disabled.

## C3-I contract ambiguity resolution handoff (2026-07-29, PR #158, second review)

The second review at head `773af68ab6bc2c27a767872d98744d128b608261` accepted `actor_type` / `actor_label`, the absent process-source field and filter, the backend-owned `display_summary`, the exclusion of raw metadata and internal IDs, the `{"detail": DomainIssue}` envelope, the `pagination_out_of_range` enum member, the C2 closure, the C3-I authorization and C4 staying inactive. **None of those is reopened.** Two ambiguities are fixed here.

### Corrected raw-summary rule

```text
The raw persisted summary is never returned verbatim and is never used
as an unrestricted API or frontend fallback.

A suffix extracted from the persisted summary may contribute to
display_summary only when all of the following are true:

1. the action is explicitly allowlisted;
2. the persisted summary starts with the exact prefix assigned to that action;
3. the remaining suffix is non-empty;
4. the action is authorized to retain that category of business name;
5. the suffix is rendered only as plain text;
6. the suffix contains no internal identifier supplied by the presenter;
7. no database lookup or metadata lookup is performed.

Otherwise display_summary falls back to the generic action-specific phrase.
```

Still prohibited: the complete persisted summary; its English technical prefix; unrestricted fallback use; summaries containing internal IDs; wish text; individual-recipe titles; metadata; business-table joins; rewriting historical rows.

### The exact allowlist — 21 actions, verified from production call sites

| `action` | Exact prefix | Suffix | Fallback | Template |
|---|---|---|---|---|
| `client.created` | `Client created: ` | client full name | `Клиент создан` | `Клиент создан: <имя>` |
| `client.updated` | `Client updated: ` | client full name | `Клиент изменён` | `Клиент изменён: <имя>` |
| `client.deactivated` | `Client deactivated: ` | client full name | `Клиент архивирован` | `Клиент архивирован: <имя>` |
| `ingredient.created` | `Ingredient created: ` | ingredient name | `Компонент создан` | `Компонент создан: <название>` |
| `ingredient.updated` | `Ingredient updated: ` | ingredient name | `Компонент изменён` | `Компонент изменён: <название>` |
| `ingredient.deactivated` | `Ingredient deactivated: ` | ingredient name | `Компонент архивирован` | `Компонент архивирован: <название>` |
| `packaging_item.created` | `Packaging item created: ` | packaging name | `Тара создана` | `Тара создана: <название>` |
| `packaging_item.updated` | `Packaging item updated: ` | packaging name | `Тара изменена` | `Тара изменена: <название>` |
| `packaging_item.deactivated` | `Packaging item deactivated: ` | packaging name | `Тара архивирована` | `Тара архивирована: <название>` |
| `recipe_template.created` | `Recipe template created: ` | recipe name | `Рецепт создан` | `Рецепт создан: <название>` |
| `recipe_template.deactivated` | `Recipe template deactivated: ` | recipe name | `Рецепт архивирован` | `Рецепт архивирован: <название>` |
| `order.created` | `Order created: ` | order product name | `Заказ создан` | `Заказ создан: <продукт>` |
| `order.updated` | `Order updated: ` | order product name | `Заказ изменён` | `Заказ изменён: <продукт>` |
| `order.cancelled` | `Order cancelled: ` | order product name | `Заказ отменён` | `Заказ отменён: <продукт>` |
| `order.archived` | `Order archived: ` | order product name | `Заказ архивирован` | `Заказ архивирован: <продукт>` |
| `catalog_category.created` | `Catalog category created: ` | reference name | `Категория справочника создана` | `… создана: <название>` |
| `catalog_category.updated` | `Catalog category updated: ` | reference name | `Категория справочника изменена` | `… изменена: <название>` |
| `catalog_category.archived` | `Catalog category archived: ` | reference name | `Категория справочника архивирована` | `… архивирована: <название>` |
| `catalog_tag.created` | `Catalog tag created: ` | reference name | `Тег справочника создан` | `… создан: <название>` |
| `catalog_tag.updated` | `Catalog tag updated: ` | reference name | `Тег справочника изменён` | `… изменён: <название>` |
| `catalog_tag.archived` | `Catalog tag archived: ` | reference name | `Тег справочника архивирован` | `… архивирован: <название>` |

Full table with write-call-site locations: `docs/audit-log.md` § 6.4.3.

**Excluded and never eligible:** `client_wish.*` (user-authored wish title); `client_recipe.*` (individual-formula title); every ID-bearing action — `ingredient_lot.*`, `stock_movement.created`, `packaging_stock_movement.created`, `production_confirmed`, `recipe_version.created`; and every catalog-assignment action, whose summary is the fixed string `Catalog category assigned` or `Catalog tags updated`. **The allowlist is the exact 21-row table, not a prefix glob** — `ingredient.catalog_tags.updated` matches `ingredient.*` but is not allowlisted.

**Fallback behaviour:** prefix mismatch, empty suffix, non-allowlisted action, unknown action, or any of the seven conditions failing → the generic action-specific phrase from `docs/audit-log.md` § 6.6, which for an unknown action is the resolved `action_label`.

### Pagination validation order

```text
1. Missing value        limit → default 50; offset → default 0
2. Wrong type or representation
   non-integer, fractional, boolean, malformed string  → non_integer_quantity
3. Negative integer     limit < 0, offset < 0          → negative_quantity
4. Non-negative limit outside accepted range
   limit == 0, limit > 200                             → pagination_out_of_range
5. Accepted             limit: integer 1..200; offset: integer >= 0
```

First match wins, so `limit=-1` is only `negative_quantity` and `limit=0` is only `pagination_out_of_range`.

```text
limit=true  → non_integer_quantity
limit=1.5   → non_integer_quantity
limit=abc   → non_integer_quantity
limit=-1    → negative_quantity
offset=-1   → negative_quantity
limit=0     → pagination_out_of_range
limit=201   → pagination_out_of_range
limit=200   → accepted
offset=0    → accepted
```

Nothing is silently clamped, coerced, rounded or ignored.

### Date-range conflict

```text
HTTP status: 422
code: invalid_date
field: created_before
value: the supplied created_before value
```

Russian `message`: the end of the period must be later than its beginning. Russian `next_action`: select an end date later than the start date. No synthetic `date_range` field.

### Enum decision preserved

`PAGINATION_OUT_OF_RANGE = "pagination_out_of_range"` stays the single new `DomainIssueCode` authorized by `C3-I`. It must not be replaced by `percentage_out_of_range`, `invalid_category`, `invalid_decimal` or `zero_quantity`. Bounded enum addition, not a schema migration.

### Verification

Level 0 documentation checks only, plus the semantic consistency audit. **Backend tests, frontend tests, the build and every smoke were not run.** No runtime code, test, schema, migration, dependency, lockfile, package script, generated file or user data changed. PR #158 stays open and unmerged with auto-merge disabled.
