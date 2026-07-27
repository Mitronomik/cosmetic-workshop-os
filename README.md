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

The **backend baseline correction gate is DONE**. The four accepted failures were diagnosed and bounded in `docs/backend-baseline-failure-triage.md`, and all three correction slices — `R3`, `R2`, and `R4` — are now merged and closed. `R3 — Repair purchase-suggestions API smoke seeding` is **merged and DONE**: PR #143 merged on 2026-07-27 at merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec` from final reviewed head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`, taking the complete backend baseline from `496 collected, 492 passed, 4 failed, 0 skipped` to `496 collected, 493 passed, 3 failed, 0 skipped`. `R2 — Align import draft baseline test with date normalization` is also **merged and DONE**: PR #144 merged on 2026-07-27 at merge commit `8efbdc5c85b5932f4aeef51045542c207cf4635c` from final reviewed head `52e2c64fc601b458cfd60e8b86a778efabd65671`, taking the baseline to `496 collected, 494 passed, 2 failed, 0 skipped`. No production code changed in either slice; both were test-only.

The two filename-reason nodes — backups and exports — were the last open gate nodes and are now **closed on `main`** by the merged `R4`. `CR-005` is **decided, accepted, and implemented**: the canonical filename reason segment collapses runs of non-alphanumeric characters to one underscore, normalizes hyphens to underscores, strips leading and trailing underscores, falls back to `manual`, prefixes a digits-only result with `reason_`, and preserves case and Unicode alphanumerics. The backup/export API `reason` is that canonical filename-derived segment and is the single source of truth; the frontend consumes it without reconstructing, sanitizing, or normalizing it, mapping known system slugs to the existing localized Russian display labels and rendering custom or unmapped slugs verbatim — so the visible label is not always literally the slug. The export JSON manifest keeps the normalized human reason. Existing artifacts are never renamed or migrated, and legacy listing stays best-effort. The contract is durable in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`. With the contract decided, both nodes are reclassified from `INCONCLUSIVE` to `PRODUCT DEFECT — CONTRACT MISMATCH`, severity MEDIUM, with no proven data loss.

The `CR-005` decision PR #145 is **merged** — merged on 2026-07-27 at merge commit `bef36822e50c245b72f813dad0afbffc7f772588` from final reviewed head `7d68b45bee1f223b67f105c30e3acbb89dc8d41d`. `CR-005` remains **accepted and implemented**.

`R4 — Canonical backup/export filename reason normalization` is **merged and DONE**. PR #146 merged on 2026-07-27 at merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453` from final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). With `R4` merged, the **backend baseline correction gate is DONE**: all four accepted gate failures are closed, and the two remaining filename-reason nodes — backups and exports — are closed on `main`.

The merged `main` backend baseline is **green**: the complete backend suite run from `backend/` gives `562 collected, 562 passed, 0 failed, 0 skipped`, up from the pre-change baseline `496 collected, 494 passed, 2 failed, 0 skipped`; the 66-test difference is added regression coverage and every previously collected node ID is still collected. The focused frontend suite `npm run test:local-artifacts-reports-feedback` gives `40 pass, 0 fail, 0 skipped` and `npm run build` is `PASS`. The focused exact-published-head `/backups` and `/exports` browser smoke **passed** against the exact smoke-tested head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`. No frontend production file changed, no database or filesystem migration was involved, and no existing artifact was renamed, rewritten, or deleted.

**The active runtime implementation slice is `C1-I — Backend-owned tax-rate setting`**, implemented on its PR branch and **not merged**. Status: `IMPLEMENTED — EXACT-HEAD /settings SMOKE REQUIRED BEFORE MERGE`. It adds `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate`, persistence of the `default_tax_rate` key through the existing `app_settings` table, atomic `tax_rate_setting_changed` audit, and a `Налоговая ставка для расчётов` section inside `/settings`. It adds **no migration**, calculates **no tax and no margin**, and mutates **no historical record**. `C1-I` is not `DONE` until it is reviewed and merged, and C2 stays blocked.

`CR-007 — Decide the C1 workshop tax-rate setting contract` is **accepted**, and its authorized slice `C1-I` is **implemented on the PR branch, not merged**. One global setting `default_tax_rate`, user-facing `Налоговая ставка для расчётов`, is an internal planning estimate and never tax filing, a declaration, VAT accounting, legal advice, regime detection, or an accounting subsystem. It is a **percentage, not a coefficient** — `6` and `6.00` mean `6%`, `0.06` means `0.06%` — held as `Decimal` decimal strings in the range `0.00`–`100.00`, where excess precision such as `6.005` is rejected rather than rounded. The canonical persisted and API form is **exactly two fractional digits**, so `6` becomes `6.00` and `100` becomes `100.00`, applied after validation and never used to absorb precision. The taxable base is the order sale price, `tax_amount = ROUND_MONEY(sale_price × tax_rate_percent ÷ 100)` with money quantum `0.01` and `ROUND_HALF_UP`, and tax is deducted from gross revenue rather than added on top. A change takes effect immediately through a backend-generated `effective_at` — exposed as ISO-8601 UTC by the API while the underlying `app_settings.updated_at` column stays in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format — and never modifies completed production batches, report snapshots, prior audit records, or generated documents. A missing rate is `null` and never `0%`, leaving tax and dependent margin unavailable without blocking physical production, while a configured `0.00` is a real value; no missing financial value is ever displayed as a fabricated zero. Explicit Clear is **row deletion** of the `default_tax_rate` setting — never of the legacy `tax.default_rate` placeholder — after which `effective_at` is `null` and the clear time lives in the audit record. Every real mutation, upsert or delete, is audited atomically with the persistence change, and a no-op writes nothing. The durable contract is `docs/settings.md`, with the API shape in `docs/api.md`, snapshot semantics in `docs/domain-model.md`, the report boundary in `docs/reports.md`, and the rationale in `docs/decisions/0011-tax-rate-setting.md`. `AGENTS.md` § 6.6 and the `docs/roadmap.md` settings placeholder were aligned with the decision.

`C1-I — Backend-owned tax-rate setting` is the single authorized follow-up slice. It is **implemented on its PR branch and not merged**, started from merged `origin/main` `80b83de3e838cf676669a1b627770300590c99c0`. Delivered: the two endpoints, Decimal-string validation with structured Russian errors, the canonical exactly-two-decimal representation, backend-generated monotonic `effective_at`, explicit confirmed Clear as row deletion, one atomic `AuditLog` per real mutation, a no-op contract that writes nothing, the `/settings` UI section, focused backend and frontend tests, and the Settings Decision Matrix update that makes `default_tax_rate` — and only `default_tax_rate` — newly editable. The exact-head `/settings` browser smoke is still required before merge. Readiness tax estimates, production tax snapshots, and margin remain **C2**, which stays blocked until the C1 implementation is merged and verified. Any other next slice must be separately selected and authorized.

`CR-006 — Investigate export create-response fallback confirmation semantics` is a new **`needs evidence`** row and is **non-blocking**. In `backend/app/api/exports.py::create_export`, when the exact created export file is found through `list_export_files` the response uses parsed filename metadata and returns the canonical filename-derived reason; when it is not found, a defensive fallback builds the response from `ExportResult.reason`, which is the normalized human reason, so the fallback may return a human reason where the API contract normally expects the canonical slug. The normal path is green in backend tests, create/list/status integration coverage, and the exact-head smoke. Fallback reachability is **not established**, **no product defect is confirmed**, **no data loss is proven**, no severity is assigned, and no correction is authorized. See `state/change-requests.md` and `docs/backend-baseline-failure-triage.md` §17.

The product is **not** release-ready. The remaining release obligations are: the `CR-004` SQLite backup transaction-consistency investigation; the Restore product decision and implementation; final macOS packaging and user-ready launch; installation verification; the packaged update flow and update smoke; the full release-candidate smoke; merging and verifying the C1 tax-setting implementation, which is **implemented on its PR branch and not merged**; C2, C3, and C4, which remain **inactive** unless separately authorized; and continuing documentation accuracy.

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

The current focus is the **C1 tax-setting product decision**. `R3`, `R2`, and `R4` are all merged and DONE, the backend baseline correction gate is **DONE**, and the merged `main` backend baseline is green at `562 collected, 562 passed, 0 failed, 0 skipped`. **No runtime implementation slice is active.** `CR-007` records the accepted C1 tax-rate contract and authorizes exactly one bounded follow-up slice, `C1-I`, which starts only after the decision PR merges.

`CR-005` is accepted and implemented. For newly created backups and exports, the filename reason segment collapses each maximal run of non-alphanumeric separators to one underscore, normalizes literal hyphens to underscores, strips leading and trailing underscores, uses `manual` when empty, prefixes a digits-only result with `reason_`, and preserves letter case and Unicode alphanumerics without lowercasing, transliteration, or new truncation — so `before/update ../unsafe` becomes `before_update_unsafe`, `before-import` becomes `before_import`, `123` becomes `reason_123`, and `перед обновлением` becomes `перед_обновлением`. The create, list, and status `reason` values are that canonical filename-derived segment, and the uniqueness suffix is never part of it.

The visible UI label resolves from the same canonical slug but is not always literally equal to it: the frontend receives the slug from the API and must never reconstruct, sanitize, or normalize it, mapping **known system slugs** to the **existing localized Russian display labels** — canonical `before_import` renders as `Перед импортом` — and rendering **custom or unmapped slugs verbatim**, so canonical `before_update_unsafe` renders as `before_update_unsafe`. The export JSON manifest keeps the normalized human reason. Existing artifacts are not renamed, rewritten, or migrated, and legacy listing stays best-effort.

`R4 — Canonical backup/export filename reason normalization` delivered that contract as one bounded slice covering both nodes through a single shared backend helper, and it is **merged and DONE** as PR #146. `CR-006` is a `needs evidence` row and is **not active**. `CR-004` remains separate and inactive. C1 now has an accepted product contract (`CR-007`) and no implementation; C2, C3, and C4 remain inactive, and C2 stays blocked until the C1 implementation is merged and verified. Restore remains open, packaging/install/update work and the full release-candidate smoke remain open, and **product release readiness is not claimed**. Contract: `state/current-focus.md` and `docs/implementation-plan.md`. Evidence: `docs/backend-baseline-failure-triage.md`.

The durable `CR-005` contract documents `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md` record the merged `R4` implementation status, so they agree with the merged `main` behavior.
