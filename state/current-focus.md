# Current focus — Slice A1b1

Slice A1b1 is limited to static user-facing copy cleanup in exactly three runtime routes:

- `/demo-data`
- `/ingredient-lots`
- `/stock-movements`

Non-goals:

- Do not implement A1b2 or A1b3.
- Do not change Settings, Reports, Backups, Exports, Import, Dashboard, Recipes, Clients, Orders, Production, Packaging, navigation metadata, route readiness statuses, or onboarding copy.
- Do not change backend files, API contracts, schemas, migrations, dependencies, lockfiles, CSS, request timing, confirmation controls, disabled rules, aria-busy, focus behavior, or stock/demo behavior.
- Do not rewrite dynamic backend-provided messages; keep them safely escaped where currently rendered.
- Do not assign or predict a future pull request number.

Required checks before merge:

- `git diff --check`
- `git diff --name-only`
- `git diff --stat`
- source-diff safety review for demo install/clear and stock movement identifiers
- scoped terminology search in `frontend/src/main.ts`
- `cd frontend && npm run build`
- `cd backend && python3 -m pytest`
- focused browser smoke when browser tooling is available; otherwise mark manual focused smoke required before merge

Merge gate:

- Only `frontend/src/main.ts`, `state/current-focus.md`, `state/progress.md`, and `state/handoff.md` should change unless a reviewed conflict proves otherwise.
- No backend, CSS, dependency, lockfile, or `docs/implementation-plan.md` changes.
- The branch must remain a focused A1b1 copy-only PR based on the latest available main baseline.
