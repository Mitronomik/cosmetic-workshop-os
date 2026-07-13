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

## Slice A1 closure handoff — Help, navigation readiness, terminology, and docs sync

- Changed runtime copy only in `frontend/src/main.ts`: implemented sidebar sections are marked ready, visible labels use «Отчёты» / «Документы отчётов», the stale standalone «Готовность» navigation item and `#production-readiness` placeholder mapping were removed, Help Center copy was converted to product language, and onboarding hints now use Russian product terminology.
- Preserved contracts: no backend files, migrations, CSS, dependencies, lockfiles, routes, API requests, request order, form payloads, form validation, disabled rules, aria-busy semantics, announcers, focus handling, Help search/category/article IDs/related-section behavior, sidebar collapse behavior, pushState/popstate routing, calculations, production readiness behavior, production confirmation, import Apply behavior, open/download behavior, paths, filenames, or escaping were intentionally changed.
- Documentation/state updates are limited to A1 closure: `docs/implementation-plan.md` marks A1 done and A2 ready; directly affected user/help docs were synchronized; `state/progress.md` and this handoff were append-only.
- Smoke requirement: focused browser smoke is required before merge because navigation readiness changed and the stale standalone Production Readiness item was removed.
- Next slice: Slice A2 structured validation foundation is ready next, but no A2 implementation is included in this PR.
