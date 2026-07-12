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
