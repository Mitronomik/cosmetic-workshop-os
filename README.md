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

The active window is **Pre-release hardening — backend baseline correction gate**. The four accepted failures were diagnosed and bounded in `docs/backend-baseline-failure-triage.md`. Two correction slices are now closed. `R3 — Repair purchase-suggestions API smoke seeding` is **merged and DONE**: PR #143 merged on 2026-07-27 at merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec` from final reviewed head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`, taking the complete backend baseline from `496 collected, 492 passed, 4 failed, 0 skipped` to `496 collected, 493 passed, 3 failed, 0 skipped`. `R2 — Align import draft baseline test with date normalization` is also **merged and DONE**: PR #144 merged on 2026-07-27 at merge commit `8efbdc5c85b5932f4aeef51045542c207cf4635c` from final reviewed head `52e2c64fc601b458cfd60e8b86a778efabd65671`, taking the baseline to `496 collected, 494 passed, 2 failed, 0 skipped`. No production code changed in either slice; both were test-only.

The backend baseline now has **exactly two known failures**, both filename-reason nodes — backups and exports. `CR-005` is **decided and accepted**: the canonical filename reason segment collapses runs of non-alphanumeric characters to one underscore, normalizes hyphens to underscores, strips leading and trailing underscores, falls back to `manual`, prefixes a digits-only result with `reason_`, and preserves case and Unicode alphanumerics. The backup/export API and UI reason are that canonical filename-derived segment; the export JSON manifest keeps the normalized human reason. Existing artifacts are never renamed or migrated, and legacy listing stays best-effort. The contract is durable in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`. With the contract decided, both nodes are reclassified from `INCONCLUSIVE` to `PRODUCT DEFECT — CONTRACT MISMATCH`, severity MEDIUM, with no proven data loss.

`R4 — Canonical backup/export filename reason normalization` is the next bounded implementation slice and is **AUTHORIZED BUT NOT IMPLEMENTED**; it may begin only after the `CR-005` decision PR merges, and only from `origin/main`. The two failures are still open. The product is **not** release-ready: packaging, update flow, install verification, Restore, C1–C3, and the full release-candidate smoke all remain open.

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

The current focus is the **`CR-005` backup/export filename reason product decision**, which is documentation-only. `R3` and `R2` are both merged and DONE, and the backend baseline is `496 collected, 494 passed, 2 failed, 0 skipped` with exactly two known filename-reason failures.

`CR-005` is accepted. For newly created backups and exports, the filename reason segment collapses each maximal run of non-alphanumeric separators to one underscore, normalizes literal hyphens to underscores, strips leading and trailing underscores, uses `manual` when empty, prefixes a digits-only result with `reason_`, and preserves letter case and Unicode alphanumerics without lowercasing, transliteration, or new truncation — so `before/update ../unsafe` becomes `before_update_unsafe`, `before-import` becomes `before_import`, `123` becomes `reason_123`, and `перед обновлением` becomes `перед_обновлением`. The create, list, and status `reason` values and the visible UI reason are that canonical filename-derived segment, and the uniqueness suffix is never part of it. The export JSON manifest keeps the normalized human reason. Existing artifacts are not renamed, rewritten, or migrated, and legacy listing stays best-effort.

`R4 — Canonical backup/export filename reason normalization` is authorized as one bounded slice covering both nodes through a single shared backend helper, and it is **not implemented**. It may begin only after the `CR-005` decision PR merges, and only from `origin/main`. `CR-004` remains separate and inactive, C1–C4 remain inactive, and product release readiness is not claimed. Contract: `state/current-focus.md` and `docs/implementation-plan.md`. Evidence: `docs/backend-baseline-failure-triage.md`.
