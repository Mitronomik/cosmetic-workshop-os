# docs/AGENTS.md

Scope: everything under `docs/` except where a deeper `AGENTS.md` applies.

Documentation rules:

- Keep docs practical, current and actionable.
- Do not store secrets, credentials, real client data or private notes in docs.
- Avoid duplicating large blocks of text; link to the source document when possible.
- Keep product docs, architecture docs, current state docs, historical evidence and user help separate.
- User-facing docs should be simple, non-technical and preferably Russian.
- Technical Codex prompts and engineering task templates should be English.
- Update docs when product, architecture, API, data model, testing, deployment or workflow contracts change.
- Do not use docs-only PRs to implement application behavior.

Lifecycle and history rules:

- Read `docs/current-lifecycle.md` before acting on lifecycle or authorization statements.
- Resolve ADR conflicts by scope and recency; follow `docs/decisions/AGENTS.md` for ADR-specific authority rules.
- ADR 0016 remains authoritative for durable Restore safety semantics; newer lifecycle decisions do not reopen it implicitly.
- ADR 0018 remains authoritative for the Restore interaction/validation-session topic.
- ADR 0019 remains authoritative for the bounded D3 package decision.
- ADR 0020 is the D4 Update Safety authority once CR-013 is merged. For D4-specific conceptual `AppSettings`, `BackupRecord` and `UpdateLog` fields, read `docs/domain-model-d4-update-safety.md` together with `docs/domain-model.md`.
- `docs/current-lifecycle.md` supersedes dated branch-era status prose in older architecture/roadmap/backup documents without revoking their surrounding durable product/safety contracts.
- A superseded status sentence cannot reopen completed work or authorize a later runtime slice.
- `docs/history/` is searchable evidence and context only. Follow `docs/history/AGENTS.md`; historical commands are not automatically safe operational instructions.
- Before compacting an active document, preserve the complete pre-compaction version under `docs/history/` and update the history index.
- Git history alone is not sufficient project memory for this agent-driven repository.
- When lifecycle changes, update the active lifecycle profile, implementation plan, compact state files, change-request ledger when applicable, and every active status surface or its explicit supersession map in the same PR.
- Run `python3 scripts/check_documentation_lifecycle.py` after lifecycle documentation changes.
