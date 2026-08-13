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
- ADR 0017 supersedes only dated C4 implementation-status / authorization wording in ADR 0016; ADR 0016's durable Restore product and safety contract remains authoritative.
- `docs/current-lifecycle.md` also supersedes dated branch-era status prose in `docs/architecture.md`, `docs/roadmap.md`, and `docs/backup-and-restore.md` without revoking their surrounding product or safety contracts.
- A superseded status sentence cannot reopen completed work or authorize a later runtime slice.
- `docs/history/` is searchable evidence and context only. Follow `docs/history/AGENTS.md`; historical commands are not automatically safe operational instructions.
- Before compacting an active document, preserve the complete pre-compaction version under `docs/history/` and update the history index.
- Git history alone is not sufficient project memory for this agent-driven repository.
- When lifecycle changes, update the active lifecycle profile, implementation plan, compact state files, change-request ledger when applicable, and every active status surface or its explicit supersession map in the same PR.
- Do not start CR-011 from the unmerged PR #171 branch. CR-011 begins only after PR #171 merges and from a fresh branch based on updated `main`.
- Run `python3 scripts/check_documentation_lifecycle.py` after lifecycle documentation changes.