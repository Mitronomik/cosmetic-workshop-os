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

**Block B is complete.** B4.1, B4, and Block B are DONE. PR #141 — `B4.1 — Dashboard safe GET timeout and recovery` — merged on 2026-07-26 at merge commit `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa` from final reviewed head `d0cde127355b146f101ddf3769d76d0226c71ec0`. The Dashboard pilot uses one 8-second deadline for five concurrent, opt-in safe GET requests, commits only a fully validated coherent snapshot, preserves the previous snapshot after refresh timeout, and recovers only through an explicit user action.

B4 is closed with the Dashboard safe-GET pilot only. Safe GET timeout and recovery coverage for the remaining read routes — including but not limited to Alerts, Purchases, Orders, Reports, Backups, Exports, and Report Documents — was deliberately deferred and was not delivered. Any future expansion requires a separately authorized slice and a change request. Closing B4 does not imply that those routes are protected against an indefinitely hanging local GET. No B4.2 slice exists or is authorized.

The active window is **Pre-release hardening — backend baseline correction gate**. The complete backend baseline reproduces `496 collected, 492 passed, 4 failed, 0 skipped`; the four failures were diagnosed and bounded in `docs/backend-baseline-failure-triage.md`, and exactly one correction slice is active. Two of the four — the backups and exports filename-reason nodes — are `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED`: the product documentation does not currently define whether consecutive unsafe characters in a filename reason must collapse to a single underscore, so the production behavior is not stated to be wrong and no slice is opened for them pending a product decision. The product is **not** release-ready: packaging, update flow, install verification, Restore, C1–C3, and the full release-candidate smoke all remain open.

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

`R3 — Repair purchase-suggestions API smoke seeding` is the only active slice, and it is **test-only**. It replaces the single invalid `lot_qty="0"` seed in `backend/app/tests/test_purchase_suggestions.py` with a positive lot quantity and a higher minimum-stock threshold, so the test reaches the `/api/purchase-suggestions` HTTP surface and its existing assertions — including the three no-mutation assertions — actually execute. No production code changes, and its required smoke is the backend suite only. `R2 — Import draft issue-count contract alignment` is the next deferred slice. Contract: `state/current-focus.md`. Evidence: `docs/backend-baseline-failure-triage.md`.
