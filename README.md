# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

Local-first web app for a cosmetic workshop: recipes, recipe versions, individual client formulas, clients, wishes and feedback, ingredients, lots, packaging, orders, production, stock movements, alerts, purchase suggestions, imports, exports, backups and onboarding.

## Documentation map

- `AGENTS.md` - main Codex contract
- `docs/product-spec.md` - product specification
- `docs/architecture.md` - architecture contract
- `docs/roadmap.md` - PR-based roadmap
- `docs/implementation-plan.md` - current implementation sequence, product-readiness slices, and MVP release gates
- `docs/domain-model.md` - domain model
- `docs/ui-ux-contract.md` - human-friendly UI rules
- `docs/ui-skill-policy.md` - UI skill priority and third-party skill boundaries
- `docs/third-party-skills.md` - registry template for future third-party Codex skills
- `docs/codex-project-structure.md` - repository memory structure
- `docs/codex-prompting-rules.md` - Codex Web prompt rules
- `docs/pr-testing-and-smoke-rules.md` - testing and smoke rules
- `docs/import-format.md` - CSV/XLSX import format contract
- `state/current-focus.md` - current task
- `state/progress.md` - current progress
- `state/handoff.md` - cross-session handoff

## Status

Slice A5 is DONE. PR #131 merged at `62d372644d00fab38ccb1d652ab44556d8241b6a` (`Merge pull request #131 from Mitronomik/codex/implement-a5-local-artifact-presentation`).

The B1/B2 diagnostic audit found no demo-fixture or backend Dashboard read-model implementation defect requiring a correction PR: demo-data installation is explicit, duplicate install is safely rejected, alert and purchase-suggestion regeneration is stable, operational source data is meaningful, and passive reads do not mutate the database. B2 browser presentation was not fully verified by that diagnostic audit. The current focused task is frontend focused-test infrastructure repair; B3.1 remains the next runtime slice after this repair. No B1 or B2 implementation PR is active, and no future PR number is assigned.

Runtime product implementation includes the local-first backend/API and SQLite safety foundations, onboarding, recipes and immutable recipe versions, individual client formulas, clients, wishes and append-only feedback, ingredient and packaging stock movements, orders, production readiness and confirmation, production history, alerts, purchase suggestions, reports, manual backups, local exports, safe CSV/XLSX imports, demo data, Help Center, editable Workshop profile settings, and explicit Markdown/PDF `Сводка мастерской` document generation.

Newly generated workshop summary documents include configured Workshop profile fields. Empty fields are omitted, an empty profile omits the whole section, and existing generated documents are not mutated.

Keep DOCX, arbitrary file browsing, unrelated file access, automatic report generation, scheduled jobs, polling, cloud sync, AI/RAG, template editing, logo upload, document preview, calculation-sensitive settings, roles/auth, and unrelated business mutations out of scope unless explicitly approved.

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

Frontend local API proxy for development/smoke only:

```bash
# Terminal 1
export COSMETIC_WORKSHOP_DB_PATH="/path/to/.local/smoke.sqlite"
python3 - <<'PY'
from app.services.startup import initialize_startup
result = initialize_startup("development")
print("DB:", result.database_path)
print("Applied migrations:", result.applied_migrations)
PY
cd backend
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010

# Terminal 2
cd frontend
COSMETIC_WORKSHOP_API_PROXY_TARGET=http://127.0.0.1:8010 npm run dev
```

Then open `http://127.0.0.1:5173/packaging-items`. During `npm run dev`, frontend requests whose path starts with `/api/` are proxied to `COSMETIC_WORKSHOP_API_PROXY_TARGET`; if the variable is not set, the dev server uses `http://127.0.0.1:8000`. This proxy is only for developer smoke testing and does not change the client runtime/deployment contract.



Backend database foundation notes:

- Local development uses SQLite. If `COSMETIC_WORKSHOP_DB_PATH` is unset, the backend uses repository-root `.local/cosmetic_workshop.sqlite`, which is gitignored and intended only for local development.
- Tests should set `COSMETIC_WORKSHOP_DB_PATH` or pass a temporary database path through backend helpers.
- Technical endpoints added in PR2: `GET /api/database/status` and `GET /api/settings`. They do not run migrations implicitly; initialize the database explicitly before reading settings.
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

## Current implementation focus

PR #132 is recorded as DONE at merge commit `2ce5a4d7ba099603b733e7f2836f417da0614605`; the focused frontend TypeScript test-compilation hardening is complete. The active runtime slice is B3.1: shared feedback lifecycle for Dashboard refresh and Dashboard-rendered onboarding mutations, with passive Help Center regression coverage. B3.2 Alerts and Purchases remains the next route batch.
