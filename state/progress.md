# Progress

## Current phase
PR1b - App shell branding implemented

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
- PR1 follow-up: frontend `typescript` devDependency declared and `npm run dev` now builds before serving `dist`
- PR1 follow-up: temporary backend ASGI fallback removed; FastAPI is now the only backend runtime path
- PR1b branding pass: compact sidebar brand area, existing monogram/logo usage, warm cream/deep brown/rose-gold styling, favicon wiring, responsive shell refinements

## In progress
- none

## Blocked
- none

## Next
- Continue with the next roadmap step after PR1b review/merge. Do not add database models or migrations until scoped.

## Important notes
- PR1b is UI-only and intentionally does not add database models, migrations, backend behavior, domain business logic, inventory, recipes, clients, orders, production, imports, exports, backup implementation, cloud, mobile, OCR, auth or roles.
- The app shell uses `frontend/public/brand/mch-logo.png` for the sidebar brand mark and favicon. A text fallback (`МК`) remains visible if the image fails to load.
- The frontend uses a dependency-free TypeScript shell so build checks can run in the current environment; `typescript` remains declared in `frontend/package.json` for clean-clone reproducibility.
