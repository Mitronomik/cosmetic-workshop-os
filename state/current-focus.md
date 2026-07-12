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
