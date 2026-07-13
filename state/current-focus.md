# Current focus

Runtime product implementation is complete through PR98 — Workshop profile integration with report documents.

PR99-PR101 were documentation and governance changes only. They added the project UI/UX contract and Codex UI guidance, recorded the reviewed Impeccable adaptation, and recorded the rejection of Taste Skill. They did not add runtime product behavior.

Current task: run the manual browser smoke for Workshop profile and report document integration.

Required smoke path:
- Open `/settings` and save several Workshop profile fields while leaving at least one field empty.
- Open `/report-documents`.
- Generate and open/download a new Markdown `Сводка мастерской`.
- Confirm only non-empty profile fields appear near the top.
- Generate and open a new PDF when local PDF support is available.
- Confirm the same profile values appear and render as plain document text.
- Clear the Workshop profile.
- Generate another document and confirm the profile section is omitted without a crash.
- Confirm previously generated documents remain unchanged.

Decision after smoke:
- If smoke is clean, prepare a focused Workshop profile display polish / app header integration PR.
- If smoke reveals an integration issue, prepare a narrowly scoped report document integration fix first.

Do not assign or reuse a historical PR number before the new PR is actually created.

Do not jump to tax, currency, margin, unit, stock-threshold, expiry, role/auth, cloud, integrations, templates, labels, certificates, accounting, scheduled jobs, AI/RAG, or motion work next.

## Current repair focus

Manual browser smoke found a blocking `/settings` UI defect: the Workshop profile form was visually broken and the runtime screen exposed internal planning/status material. The active implementation branch contains a focused Settings page repair only: compact introduction, independently rendered Workshop profile, and a concise local data section. After merge, rerun isolated browser smoke for `/settings` Workshop profile behavior and `/report-documents` integration.

## Shared action-state visual contract

Source and runtime audits identified system-wide inconsistency in shared action states. This branch contains only the shared visual contract for existing primary, secondary, danger, compact, action-link, and sidebar navigation focus states. No application behavior or API behavior changed. Browser smoke remains required across representative routes before merge. The next planned system-level task is shared feedback presentation and semantics.

## PR105 focus contrast follow-up

Shared action focus outline was corrected from `rgba(211, 154, 122, .75)` to `#9a5f49` for `.primary-action`, `.secondary-action`, and `.danger-action`; the sidebar focus rule was left unchanged. Browser smoke ran against an isolated temporary SQLite database on `/settings`, `/exports`, `/report-documents`, `/alerts`, `/purchase-suggestions`, `/demo-data`, sidebar keyboard navigation, and 1440×900 plus 390×844 viewports. Passed checks covered action focus visibility, hover/pressed states, disabled styling where available, loading/error presentations, action wrapping, no horizontal overflow, screenshots, and no page errors. Row actions were unavailable for alerts and purchase suggestions in the isolated database, and disabled danger action styling was unavailable after the safe demo install state; these were not invented with unsupported data. The only console error observed was the intentionally intercepted `/exports` 503 request-failure smoke. Frontend build passed.

## Initial shared feedback migration slice

Current branch scope: shared feedback presentation and semantics for exactly `/settings`, `/exports`, `/report-documents`, `/imports`, and `/demo-data`.

- Added shared visible feedback tones: neutral, success, warning, error.
- Added persistent hidden polite/assertive announcers outside the `#root` render cycle.
- Success action results announce politely once; action failures announce assertively once.
- Static load-error cards remain visible retry sections, not live alerts.
- Added `aria-busy` to scoped action regions only: Workshop profile form, export create form, report document create form, import upload/apply panels, and demo install/clear confirmations.
- Legacy feedback outside the five migrated routes remains intentionally for follow-up.

## PR106 follow-up fixes

Follow-up scope on the existing shared feedback PR:

- Workshop profile initial load no longer renders backend GET copy as a success action result.
- Workshop profile editing clears stale visible save/cancel/error feedback and clears persistent announcer text without re-rendering on each keystroke.
- Persistent announcement regions are created at application startup before first action results.
- Export, report document, import draft, and demo-data actions now distinguish mutation failure from follow-up refresh failure.
- Import draft cancellation now follows the same action-result announcement contract.

## PR106 Import Apply refresh semantics correction

Focused correction for the existing PR:

- Import draft creation, cancellation, and application are now explicitly tracked as separate mutation-vs-refresh flows.
- Import Apply now treats `applyImportDraft()` success as the completed working-data mutation before refreshing draft list/detail.
- If Apply succeeds but list/detail refresh fails, the UI preserves the successful apply result, does not enter the mutation-error path, and the stale pre-apply detail is replaced with the backend apply response so Apply cannot be offered again.
- Structured Apply mutation errors remain preserved only for actual `applyImportDraft()` failures.
- Local Hermes browser smoke was later completed against the canonical GitHub runtime head listed below; earlier local pending status is superseded by the completed audit record.

## PR106 Import Apply applied-branch warning correction

Focused correction for the already-applied Import Apply branch:

- Added explicit `applyRefreshWarning` UI state instead of overloading `applyMessage` for refresh warnings.
- The warning is cleared on Apply reset/open/start/failure/successful refresh paths so it cannot leak to another draft.
- Apply success plus read-model refresh failure remains a success state and keeps the authoritative applied draft from the mutation response.
- The `status === 'applied'` branch now renders the refresh warning with shared warning feedback, while keeping Apply unavailable.
- No assertive failure is emitted for read-model refresh failure.
- Local Hermes browser smoke was later completed against the canonical GitHub runtime head listed below; earlier local pending status is superseded by the completed audit record.


## PR106 completed Hermes browser smoke

External GitHub verification confirmed PR #106 was published at canonical runtime head `4a2a88d156d1516568b608b113818dfe77e32210`, which may differ from rewritten local Codex task SHAs. The completed Hermes audit tested that exact runtime head in an isolated temporary repository checkout (`/tmp/cwo-pr106-deterministic-20260713-092916/repository`) with an isolated SQLite database, isolated user-data directory, local frontend/backend, deterministic local fault proxy, Headless Chrome, 1440×900 desktop viewport, and 390×844 narrow viewport. No real user data was used.

Verdict: `PR106_DETERMINISTIC_SMOKE_PASS_WITH_NON_BLOCKING_FINDINGS`.

Recorded scenario results:
- Normal Import Apply: draft creation returned 201, Apply returned 200, exactly one Apply POST occurred, exactly one ingredient was created, the Apply result stayed visible, repeat Apply became unavailable, polite success was observed, no assertive failure occurred, and `aria-busy` returned to false.
- Apply success plus refresh failure: Apply returned 200, the proxy intentionally returned 503 for the immediate draft detail/list refresh requests, mutation success and the applied result stayed visible, the imported ingredient existed exactly once, shared warning feedback instructed the user to press `Обновить`, false mutation-failure text was absent, no assertive Apply failure was emitted, repeat Apply remained unavailable, manual Refresh recovered final state, and no second Apply POST or duplicate record occurred.
- Structured Apply conflict: duplicate Apply returned 409, structured row-level details were visible, the persistent assertive `role="alert"` region received the blocking failure, no polite Apply success was emitted, no duplicate ingredient or partial domain write occurred, and `applyRefreshWarning` remained empty.
- Settings: initial profile load did not show action-success feedback, Cancel restored the saved value and produced polite feedback, Save produced polite feedback, editing after Save cleared stale visible success while focus remained in the field, and `aria-busy` behaved correctly during Save.
- Responsive/keyboard: the 390×844 viewport had no page-level horizontal overflow, tested controls remained reachable, persistent announcement regions were outside `#root`, and 27 keyboard-reachable elements were observed in logical DOM order. This is DOM/browser smoke evidence, not screen-reader certification or formal WCAG certification.
- Diagnostics: intentional 503 responses were limited to the refresh-failure scenario; the expected 409 belonged to the conflict scenario; final record counts were normal import 1, refresh-failure import 1, and duplicate created by rejected conflict 0; seven PNG screenshots and seven matching metrics files were verified; the audited repository remained clean; audit-started ports were released.

Non-blocking observations: MutationObserver console errors came from the deterministic audit harness attempting to observe `#root` before it existed and were not an application defect. A separate narrow screenshot of the already-failed conflict draft was unavailable after the scenario state transition, while required conflict workflow and desktop evidence was present.

All mandatory PR106 browser scenarios passed. No code blocker remains. PR106 is ready for merge after this documentation-only commit is verified. Browser smoke does not need to be repeated for this commit because it changes only state documentation.
