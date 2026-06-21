# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

Local-first web app for a cosmetic workshop: recipes, recipe versions, individual client formulas, clients, wishes and feedback, ingredients, lots, packaging, orders, production, stock movements, alerts, purchase suggestions, imports, exports, backups and onboarding.

## Documentation map

- `AGENTS.md` - main Codex contract
- `docs/product-spec.md` - product specification
- `docs/architecture.md` - architecture contract
- `docs/roadmap.md` - PR-based roadmap
- `docs/domain-model.md` - domain model
- `docs/ui-ux-contract.md` - human-friendly UI rules
- `docs/codex-project-structure.md` - repository memory structure
- `docs/codex-prompting-rules.md` - Codex Web prompt rules
- `docs/pr-testing-and-smoke-rules.md` - testing and smoke rules
- `docs/import-format.md` - CSV/XLSX import format contract
- `state/current-focus.md` - current task
- `state/progress.md` - current progress
- `state/handoff.md` - cross-session handoff

## Status

PR2 database foundation is implemented: backend health endpoints remain stable, SQLite infrastructure tables and migration helpers exist, and the frontend shell remains unchanged.

## Developer commands

```bash
make setup          # install backend/frontend development dependencies when registries are available
make dev            # print backend/frontend development startup commands
make test           # run backend tests
make build          # build the frontend shell
make smoke          # print the current smoke checklist
```

Direct commands:

```bash
cd backend && python3 -m pytest
cd frontend && npm run build
cd frontend && npm run dev    # builds the shell, then serves dist on http://127.0.0.1:5173
```

Frontend dependency note: `frontend/package.json` declares `typescript` as a dev dependency because the build script runs `tsc`; run `cd frontend && npm install` when registry access is available.


Backend database foundation notes:

- Local development uses SQLite. If `COSMETIC_WORKSHOP_DB_PATH` is unset, the backend uses `.local/cosmetic_workshop.sqlite`, which is gitignored and intended only for local development.
- Tests should set `COSMETIC_WORKSHOP_DB_PATH` or pass a temporary database path through backend helpers.
- Technical endpoints added in PR2: `GET /api/database/status` and `GET /api/settings`.
- Only infrastructure tables are created in PR2: `app_settings`, `audit_logs`, and migration metadata. Business tables remain future roadmap scope.

Backend dependency note: the PR1 backend runtime is FastAPI only; install backend dependencies with `python3 -m pip install -e "backend[test]"` before running backend tests or local API startup.

Backend health endpoint shape:

```json
{
  "status": "ok",
  "app": "cosmetic-workshop-os",
  "product_name": "Мастерская косметолога",
  "mode": "local-first",
  "version": "0.1.0"
}
```
