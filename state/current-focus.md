# Current Focus — Slice A1b3a Reports copy

Active task: Slice A1b3a — clean up Reports and Report Documents product copy.

## Runtime scope
- `/reports` static product copy.
- `/report-documents` static product copy.
- `dashboardReportsCard()` static product copy.

## Non-goals
- Do not implement A1b3b Help Center or route/navigation readiness metadata work.
- Do not implement A1c final runtime terminology sweep.
- Do not implement Slice A2 structured validation or any later implementation-plan slice.
- Do not change backend files, report calculations, report-document generation, routes, navigation identifiers, CSS, dependencies, lockfiles, or documentation pages.
- Do not change `docs/implementation-plan.md`; Slice A1 remains IN PROGRESS.

## Required source-diff checks
- Review Reports diff for request count, `Promise.all`, state, report DTO, and calculation preservation.
- Review Report Documents diff for `can_create`, disabled rules, `aria-busy`, announcers, success/list-refresh separation, open/download controls, and format values.
- Review navigation diff for unchanged `data-nav-section`, route, pathname, and navigation behavior.
- Run the scoped terminology search and classify remaining matches without broad replacement.

## Validation plan
- Run repository hygiene checks: `git status --short`, `git diff --check`, `git diff --name-only`, and `git diff --stat`.
- Run frontend build: `cd frontend && npm run build`.
- Run backend baseline: `cd backend && python3 -m pytest`; report collected, passed, failed, exact failures, and whether failures match the known baseline.

## Review and publication gate
- Commit changes on the current branch only after checks are complete.
- Create a focused pull request with the requested title and structured body after the commit.
- Publication metadata must be verified by the repository owner if the environment has no GitHub remote.
- Do not assign or predict a future pull request number.

## Browser policy
- Browser smoke is not required as a merge gate when the final runtime diff changes static strings only and does not modify HTML structure, CSS, controls, routes, requests, focus, state transitions, report calculations, or report-document behavior.
