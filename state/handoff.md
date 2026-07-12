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
- Completed checks: source searches before/after, `git diff --check`, frontend build, isolated backend/frontend curl smoke. Backend pytest currently reports 5 unrelated backend-area failures. Browser Playwright smoke/screenshots were unavailable because Playwright installation from npm was blocked by 403.
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
- Local Playwright/browser discovery found no installed browser automation path or browser binary, so required browser smoke/screenshots could not run in this environment without installing dependencies.
- Isolated backend/frontend curl startup still passed for `/api/health` and `/settings`.

Next planned system task remains: Scoped busy states for alerts and purchase suggestions.

## PR106 Import Apply correction handoff

Import flow coverage is now explicitly:

- import draft creation;
- import draft cancellation;
- import draft application.

Import Apply mutation and refresh failures are separated. A successful Apply followed by failed list/detail refresh preserves `response.apply_result`, keeps success state, avoids the assertive mutation-failure path, and shows a manual refresh warning. The stale pre-apply selected draft is replaced with the backend apply response before refresh so Apply cannot be triggered again from old readiness state. Structured Apply mutation errors remain preserved for actual mutation failures only.

Local Hermes browser smoke is still pending local verification. No browser, responsive, keyboard, screenshot, or announcement-count claims are made for this correction. Next planned system task remains: Scoped busy states for alerts and purchase suggestions.

## PR106 applied-branch refresh-warning handoff

Import Apply refresh warning now has explicit state (`applyRefreshWarning`) and is visible for an already applied draft. The `status === 'applied'` branch renders the warning with shared warning feedback, then renders the preserved Apply result. Apply success plus refresh failure remains a success state, does not emit an assertive failure, does not show mutation-error/no-partial-change copy, and keeps the authoritative applied draft so Apply cannot be offered again.

Manual recovery remains the existing Import page Refresh action; it rereads the draft list/read model and does not run Apply. Local Hermes browser smoke remains pending local verification. No browser, responsive, keyboard, screenshot, or announcement-count claim is made. Next planned system task remains: Scoped busy states for alerts and purchase suggestions.
