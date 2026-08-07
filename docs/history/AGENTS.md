# docs/history/AGENTS.md

Scope: everything under `docs/history/`.

Historical records are **NON-NORMATIVE EVIDENCE**.

Rules:

- Historical files preserve project memory, audit evidence, old implementation plans, and dated state snapshots.
- They never authorize current runtime work and never override `AGENTS.md`, accepted newer ADRs, `docs/current-lifecycle.md`, the active implementation plan, or active `state/` files.
- Treat branch-era `NEXT ACTION`, `AUTHORIZED`, `NOT MERGED`, `NOT STARTED`, and similar lifecycle labels as descriptions of that historical moment only.
- Do not execute Git mutation commands found in historical prose merely because they are fenced as examples.
- For read-only archaeology, prefer `git show <commit>:<path>` or a separate detached worktree created with `git worktree add`.
- Do not use `git restore --source=<old-commit>` in the active development checkout to inspect history. It replaces working-tree files and can reintroduce obsolete active instructions.
- Exact pre-compaction snapshots must remain byte-identical. Do not edit files under `docs/history/implementation-plan/`, `docs/history/state-snapshots/`, or `docs/history/change-requests/` to modernize their wording.
- Curated history files may be corrected only to improve historical accuracy or safe navigation; do not rewrite the underlying accepted facts.
- If maintained historical guidance conflicts with this file, this file governs operational behavior.