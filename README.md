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

The active window is **Pre-release hardening — backend baseline correction gate**. The four accepted failures were diagnosed and bounded in `docs/backend-baseline-failure-triage.md`, and exactly one correction slice is active. `R3 — Repair purchase-suggestions API smoke seeding` is **merged and DONE**: PR #143 merged on 2026-07-27 at merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec` from final reviewed head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`, taking the complete backend baseline from `496 collected, 492 passed, 4 failed, 0 skipped` to `496 collected, 493 passed, 3 failed, 0 skipped`. `R2 — Align import draft baseline test with the documented date-normalization contract` is now the single current slice and is **implemented on the current PR branch and awaiting review and merge**; it is not merged and not DONE. With `R2` applied, the backend baseline improves from three failures to two: `496 collected, 494 passed, 2 failed, 0 skipped`. No production code changed in either slice. The two remaining failures are the filename-reason nodes — backups and exports — which stay blocked on `CR-005` and are `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED`: the product documentation does not currently define whether consecutive unsafe characters in a filename reason must collapse to a single underscore, so the production behavior is not stated to be wrong and no slice is opened for them pending a product decision. The product is **not** release-ready: packaging, update flow, install verification, Restore, C1–C3, and the full release-candidate smoke all remain open.

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

`R2 — Align import draft baseline test with the documented date-normalization contract` is the only active slice, it is **test-only**, and it is `IMPLEMENTED — REVIEW AND MERGE REQUIRED`. It changed exactly one assertion block, in `backend/app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`: `error_count >= 4` became `error_count == 3`, `warning_count == 1` and `apply_readiness.can_apply is False` were added, and the row-code subset assertion became the exact set `{invalid_decimal, invalid_unit, date_format_normalized}`. The CSV input, the date `05.07.2026`, the target type, the response status assertion, and the global `missing_required_column` assertion are unchanged, and the corrected assertions are strictly more specific than the ones they replace. The deterministic Russian `DD.MM.YYYY` date normalizes to ISO and emits the documented `date_format_normalized` **warning**, exactly as `docs/import-format.md` requires; `invalid_date` stays reserved for genuinely invalid dates and stays covered by `backend/app/tests/test_import_parsing.py`. Apply remains blocked and no production import data is written. No production code changed, and its required smoke is the backend suite only. `R3` is merged and DONE. The backups and exports filename nodes remain blocked on `CR-005` and have no slice; do not begin that work from the unmerged `R2` branch. Contract: `state/current-focus.md`. Evidence: `docs/backend-baseline-failure-triage.md`.
