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
