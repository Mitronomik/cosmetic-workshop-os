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
- Local Hermes browser smoke remains pending local verification; no browser, responsive, keyboard, screenshot, or announcement-count claims are made here.

## PR106 Import Apply applied-branch warning correction

Focused correction for the already-applied Import Apply branch:

- Added explicit `applyRefreshWarning` UI state instead of overloading `applyMessage` for refresh warnings.
- The warning is cleared on Apply reset/open/start/failure/successful refresh paths so it cannot leak to another draft.
- Apply success plus read-model refresh failure remains a success state and keeps the authoritative applied draft from the mutation response.
- The `status === 'applied'` branch now renders the refresh warning with shared warning feedback, while keeping Apply unavailable.
- No assertive failure is emitted for read-model refresh failure.
- Local Hermes browser smoke remains pending; no browser, responsive, keyboard, screenshot, or announcement-count claim is made.
