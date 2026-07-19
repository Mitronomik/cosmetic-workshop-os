# Handoff

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
