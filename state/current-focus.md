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
