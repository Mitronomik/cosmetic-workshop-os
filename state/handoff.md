# Handoff

## Last completed work
Implemented PR1 app shell and follow-ups: backend health endpoint now uses FastAPI only with no temporary ASGI fallback, health tests target FastAPI TestClient, frontend shell has Russian navigation placeholders, TypeScript dev dependency is declared, dev script builds before serving `dist`, and README/state command notes are updated.

## Current repo state
Minimal runnable foundation exists. Backend exposes stable health payload at `/api/health` and `/health` through FastAPI only. Frontend builds a static local-first shell with placeholders only.

## Important decisions
- Repo: `cosmetic-workshop-os`
- Product: `Мастерская косметолога`
- MVP remains local-first and API-first.
- Health response shape is documented in `README.md`.
- No database models, migrations or business-domain services were added in PR1.
- Temporary dependency-free backend ASGI fallback was removed; backend tests now require FastAPI/httpx dependencies from `backend[test]`.
- Frontend shell is intentionally dependency-free TypeScript for PR1 because package registry access returned 403 during setup checks; `typescript` is declared as a dev dependency for clean-clone reproducibility when `npm install` is possible. This should be revisited when adopting full React/Vite tooling.

## Known issues
- `make setup` or backend dependency installation may fail in this environment while Python/npm registries return 403. Clean clones should install `backend[test]` and `frontend/package.json` dependencies when registry access is available.
- The frontend health indicator expects `/api/health`; when serving the static frontend alone, it shows that the local API is unavailable until backend/proxy wiring is added.

## Next recommended task
Proceed to the next roadmap-scoped foundation task after PR1 review/merge; keep database and business features out unless explicitly scoped.

## Commands run
- `git status --short`
- `git branch --show-current`
- `python3 -m pytest backend/app/tests`
- `cd frontend && npm run build`
- `cd frontend && npm run dev` smoke with HTTP checks for `/` and `/assets/main.js`
- `make test`
- `make build`

## Tests status
After removing the backend fallback, backend tests require FastAPI/httpx dependencies. Frontend build passed. `npm run dev` smoke passed by requesting `/` and `/assets/main.js` from the local dev server. PR1 smoke should verify `/health` and `/api/health` once backend dependencies are installable.
