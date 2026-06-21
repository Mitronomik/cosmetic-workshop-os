# Current Focus

Current task: PR8 - First-run onboarding skeleton.

## Allowed scope
Minimal persisted onboarding state, thin onboarding API, warm Russian first-run welcome/checklist UI, small placeholder empty states, onboarding tests, frontend build validation, smoke notes, and state documentation updates.

## Do not touch
Real ingredient UI/forms, ingredient lots, stock movements, packaging inventory, recipes, recipe versions, clients, orders, production, imports, exports, backup UI/restore UI, final packaging, Electron, Docker, cloud/mobile access, OCR, auth, roles, or new business tables.

## Acceptance
Onboarding state is represented cleanly through existing infrastructure, onboarding API can read/start/complete steps/complete/reset, frontend renders a human-friendly local workspace onboarding skeleton and degrades gracefully when backend is unavailable, no forbidden future business tables are added, checks/smoke are reported, and state files are updated.
