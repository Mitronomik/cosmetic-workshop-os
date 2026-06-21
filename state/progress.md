# Progress

## Current phase
PR1 - App shell implemented

## Done
- Architecture draft
- Final roadmap draft
- Frontend concept draft
- Codex project structure rules
- Codex prompting rules
- PR testing and smoke rules
- Product specification
- Domain model
- Repository starter structure and documentation placement
- Documentation structure review against project contracts
- Nested `AGENTS.md` contracts expanded for backend, frontend, launcher, docs, ADRs, state, help and scripts
- Minimal backend app shell with `/api/health` and `/health`
- Backend health endpoint tests
- Minimal frontend shell with Russian navigation placeholders and dashboard placeholder
- Minimal project commands for PR1 test/build/dev guidance

## In progress
- none

## Blocked
- none

## Next
- Continue with the next roadmap step after PR1 review/merge. Do not add database models or migrations until scoped.

## Important notes
- PR1 intentionally does not add database models, migrations, domain business logic, inventory, recipes, clients, orders, production, imports, exports, backup implementation, cloud, mobile, OCR, auth or roles.
- The frontend uses a dependency-free TypeScript shell in this PR so build checks can run in the current environment where package registry access is blocked; future PRs may switch to the documented React/Vite stack when dependencies are available.
