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

- Read `docs/current-lifecycle.md` before acting on lifecycle or authorization statements in large reference documents.
- Accepted ADRs and `docs/current-lifecycle.md` override dated branch-era status prose in `docs/architecture.md`, `docs/roadmap.md`, and `docs/backup-and-restore.md`.
- A superseded status sentence does not revoke the surrounding product, safety, API, or architecture contract.
- `docs/history/` is searchable evidence and context only. It must never authorize current runtime work or override an accepted decision.
- Before compacting an active document, preserve the complete pre-compaction version under `docs/history/` and update the history index.
- Git history alone is not sufficient project memory for this agent-driven repository.
- When lifecycle changes, update the active lifecycle profile, implementation plan, compact state files, change-request ledger when applicable, and every active status surface or its explicit supersession map in the same PR.
- Run `python3 scripts/check_documentation_lifecycle.py` after lifecycle documentation changes.
