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
- `docs/audit-log.md` - durable AuditLog workspace product, API, privacy and presentation contract (C3)
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

*Accepted `R4` merged evidence (PR #146) — historical, not the current baseline:* the complete backend suite run from `backend/` gave `562 collected, 562 passed, 0 failed, 0 skipped`, up from the pre-change baseline `496 collected, 494 passed, 2 failed, 0 skipped`; the 66-test difference is added regression coverage and every previously collected node ID is still collected. The focused frontend suite `npm run test:local-artifacts-reports-feedback` gives `40 pass, 0 fail, 0 skipped` and `npm run build` is `PASS`. The focused exact-published-head `/backups` and `/exports` browser smoke **passed** against the exact smoke-tested head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`. No frontend production file changed, no database or filesystem migration was involved, and no existing artifact was renamed, rewritten, or deleted.

**Current merged baseline.** `origin/main` is `ba3ca7443e3280bc7f700af11e75dc4fa810665f` (the PR #159 merge commit). `C3-I — Read-only AuditLog workspace` is on merged `main`; its final reviewed and published head is `bf7cde060a43190fdf22c612a16b0c137aa5531b`, and PR #159 merged at `2026-07-30T03:20:23Z`. The earlier value `87410910aad472343c057f0bcbfcc3797f8b8e09` (PR #157) and every earlier baseline below it are **historical**.

**`C1-I — Implement backend-owned tax-rate setting` is merged and `DONE`.** PR #149 merged on 2026-07-27 at `2026-07-27T19:44:53Z`, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`, from final reviewed head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). That merge commit was `main` at the time; `main` has since advanced to `d432fcaee52a16a4f8b609ec160cf3fa2b33d013` through PR #151, PR #152, PR #153, and PR #154. Accepted `C1-I` evidence, historical to that slice: backend `671 collected, 671 passed, 0 failed, 0 skipped` with all 562 original merged baseline node IDs still collected; the focused tax-setting frontend suite `52 passed, 0 failed, 0 skipped`; all 13 focused frontend suites `568 passed, 0 failed, 0 skipped`; frontend production build `PASS`; the exact-head `/settings` browser smoke `PASS — 146 checks / 0 failures` against head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`; `frontend/src/main.ts` `6406 → 6399` lines. The slice adds `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate`, persistence of the `default_tax_rate` key through the existing `app_settings` table, atomic `tax_rate_setting_changed` audit, and a `Налоговая ставка для расчётов` section inside `/settings`. It added **no migration**, calculates **no tax and no margin**, and mutates **no historical record**. Nothing in `C1-I` still awaits smoke or merge.

**The C2 financial contract is accepted and fully implemented. `C2 — COMPLETED`.** `CR-008 — Decide C2 financial estimates and immutable production snapshots` records the accepted calculation and immutable-snapshot contract. All four slices are **merged and `DONE — MERGED AND EXACT-HEAD VERIFIED`**: `C2-I` — the backend financial readiness estimate (PR #151); `C2-II` — the transactional production financial snapshots, including migration `0019` (PR #152, merge commit `c3a3a7b8db06fe85290216113b784123ed9b6b30`, merged `2026-07-28T09:00:50Z`); `C2-III-A` — Order and `ProductionBatch` financial presentation (PR #154, final reviewed head `ef1103811a8f062f9129bfb465a98e0cfa388935`, merge commit `d432fcaee52a16a4f8b609ec160cf3fa2b33d013`, merged `2026-07-28T13:05:34Z`); and `C2-III-B` — snapshot-backed reports and report documents (PR #157, final reviewed head `305d5421e79b8cb833df9588e705e9418781e021`, merge commit `87410910aad472343c057f0bcbfcc3797f8b8e09`, merged `2026-07-28T22:21:18Z`). **Reports on merged `main` are snapshot-backed**: report tax and margin come only from persisted `ProductionBatch` snapshots, and the former paired sale-price/cost margin derivation is gone. Accepted PR #157 evidence — not re-executed here: exact-head API smoke `PASS — 53 checks / 0 failures`; exact-head browser smoke `PASS — FULL AUTOMATED SMOKE PASSED`; complete backend suite `942 passed / 0 failed / 0 skipped`; focused report frontend suite `54 pass / 0 fail`; all 17 frontend test scripts `PASS`; production build `PASS`; `frontend/src/main.ts` `6398` lines. Contract: `docs/decisions/0012-c2-financial-calculation-snapshots.md`. **The product is still not release-ready.**

**`C3-I — Read-only AuditLog workspace` is `DONE — MERGED AND EXACT-HEAD VERIFIED`.** PR #159 merged into `main` from final reviewed and published head `bf7cde060a43190fdf22c612a16b0c137aa5531b` at merge commit `ba3ca7443e3280bc7f700af11e75dc4fa810665f` on `2026-07-30T03:20:23Z`. Merged `main` now contains `GET /api/audit-logs` and `/settings/audit-log` (`Журнал действий`) with the accepted read-only, backend-owned privacy contract. At the merged PR #160 baseline, Workshop-profile changes, manual backup creation, JSON export creation and report-document generation had no AuditLog write call sites. On the current PR #161 branch, Workshop-profile AuditLog coverage is **implemented on the PR branch and not merged**; the remaining write-coverage gap is only manual backup creation, JSON export creation and report-document generation. That remaining `C3-II-B` work is **`NEEDS PRODUCT DECISION — NOT AUTHORIZED`**. Therefore `C3 — INCOMPLETE`, and product release readiness is not claimed.

Remaining C3 work is bounded deliberately. `C3-II-A — Atomic workshop-profile AuditLog coverage` is **implemented on its PR branch and not merged**. `C3-II-B — File-backed artifact AuditLog semantics` covers only manual backup creation, JSON export creation and report-document generation; it remains **`NEEDS PRODUCT DECISION — NOT AUTHORIZED`** because filesystem artifact creation cannot be claimed atomic with a later SQLite AuditLog insert without an explicit success, compensation, retry and recovery contract. Therefore `C3 — INCOMPLETE`.

The API field is **`actor_type` / `actor_label`**, not `source`. The values that exist — `system` and `user` — describe the **actor that initiated the action**, not a process origin, so presenting them as a source would silently change the field's meaning. The historical process vocabulary (`manual`, `import`, `production`, `migration`, `backup`, `onboarding`, `restore`) is aspirational: no write call site persists that dimension, so a true `source` field is **deferred** to a separately authorized decision and write-side slice. The column is not renamed, and there is no migration and no backfill.

The API returns **`display_summary`**, a backend-owned safe Russian value resolved from the known `action` by a focused presenter. The **raw persisted summary is never returned verbatim and is never used as an unrestricted fallback** — it is write-time technical text, mostly English, sometimes carrying internal record IDs, and `client_wish.*` values carry user-authored wish text. A safe business name may contribute only through a bounded seven-condition rule and an exact 21-action allowlist that excludes `client_wish.*`, `client_recipe.*` and every ID-bearing action. Raw `metadata_json`, table names, internal entity IDs, stack traces, SQL and developer paths are never returned or displayed either, and no historical row is ever rewritten. Invalid pagination is rejected with a structured `422` under a fixed precedence — `limit=-1` is `negative_quantity`, `limit=0` is `pagination_out_of_range` — never silently clamped. The old roadmap proposal `GET /api/audit-logs/{id}` is **explicitly superseded for the MVP**. No AuditLog edit, delete, rollback, export, analytics or search over sensitive text is authorized. Durable contract: `docs/audit-log.md`. C4 remains **inactive** and still needs a product decision.

`CR-007 — Decide the C1 workshop tax-rate setting contract` is **accepted**, and its authorized slice `C1-I` is **implemented and merged**. One global setting `default_tax_rate`, user-facing `Налоговая ставка для расчётов`, is an internal planning estimate and never tax filing, a declaration, VAT accounting, legal advice, regime detection, or an accounting subsystem. It is a **percentage, not a coefficient** — `6` and `6.00` mean `6%`, `0.06` means `0.06%` — held as `Decimal` decimal strings in the range `0.00`–`100.00`, where excess precision such as `6.005` is rejected rather than rounded. The canonical persisted and API form is **exactly two fractional digits**, so `6` becomes `6.00` and `100` becomes `100.00`, applied after validation and never used to absorb precision. The taxable base is the order sale price, `tax_amount = ROUND_MONEY(sale_price × tax_rate_percent ÷ 100)` with money quantum `0.01` and `ROUND_HALF_UP`, and tax is deducted from gross revenue rather than added on top. A change takes effect immediately through a backend-generated `effective_at` — exposed as ISO-8601 UTC by the API while the underlying `app_settings.updated_at` column stays in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format — and never modifies completed production batches, report snapshots, prior audit records, or generated documents. A missing rate is `null` and never `0%`, leaving tax and dependent margin unavailable without blocking physical production, while a configured `0.00` is a real value; no missing financial value is ever displayed as a fabricated zero. Explicit Clear is **row deletion** of the `default_tax_rate` setting — never of the legacy `tax.default_rate` placeholder — after which `effective_at` is `null` and the clear time lives in the audit record. Every real mutation, upsert or delete, is audited atomically with the persistence change, and a no-op writes nothing. The durable contract is `docs/settings.md`, with the API shape in `docs/api.md`, snapshot semantics in `docs/domain-model.md`, the report boundary in `docs/reports.md`, and the rationale in `docs/decisions/0011-tax-rate-setting.md`. `AGENTS.md` § 6.6 and the `docs/roadmap.md` settings placeholder were aligned with the decision.

`C1-I` was the single authorized follow-up slice and it is **merged**, started from merged `origin/main` `80b83de3e838cf676669a1b627770300590c99c0`. Delivered: the two endpoints, Decimal-string validation with structured Russian errors, the canonical exactly-two-decimal representation, backend-generated monotonic `effective_at`, explicit confirmed Clear as row deletion, one atomic `AuditLog` per real mutation, a no-op contract that writes nothing, the `/settings` UI section, focused backend and frontend tests, and the Settings Decision Matrix update that makes `default_tax_rate` — and only `default_tax_rate` — newly editable. The exact-head `/settings` browser smoke passed before merge. Readiness tax estimates, production tax snapshots, and margin were left to **C2**, and every C2 slice has since merged: on current merged `main` production readiness returns `estimated_tax`, `estimated_margin`, and `estimated_margin_percent` (`C2-I`, PR #151); `ProductionBatch` carries the `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` columns added by migration `0019` together with persisted `tax`, `margin`, and `margin_percent` (`C2-II`, PR #152); Orders and `ProductionBatch` present those financials (`C2-III-A`, PR #154); and reports read the persisted snapshots (`C2-III-B`, PR #157). C2 is **complete**. `C3-I` has since merged as PR #159; after this documentation PR merges, the only authorized runtime slice is `C3-II-A`, and no future implementation PR number is assigned.

`CR-006 — Investigate export create-response fallback confirmation semantics` is a new **`needs evidence`** row and is **non-blocking**. In `backend/app/api/exports.py::create_export`, when the exact created export file is found through `list_export_files` the response uses parsed filename metadata and returns the canonical filename-derived reason; when it is not found, a defensive fallback builds the response from `ExportResult.reason`, which is the normalized human reason, so the fallback may return a human reason where the API contract normally expects the canonical slug. The normal path is green in backend tests, create/list/status integration coverage, and the exact-head smoke. Fallback reachability is **not established**, **no product defect is confirmed**, **no data loss is proven**, no severity is assigned, and no correction is authorized. See `state/change-requests.md` and `docs/backend-baseline-failure-triage.md` §17.

The product is **not** release-ready. The remaining release obligations include: the `CR-004` SQLite backup transaction-consistency investigation; the Restore product decision and implementation; final macOS packaging and user-ready launch; installation verification; the packaged update flow and update smoke; the full release-candidate smoke; the incomplete C3 write-side AuditLog coverage described above; C4, which remains **inactive** and still needs a product decision; and continuing documentation accuracy. `C3-I` itself is closed, but neither its merge nor this documentation work completes C3 or claims release readiness. C1 and C2 are merged and **COMPLETED**.

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

The current focus is C3-II-A review. C1 and C2 are **COMPLETED**. `C3-I — Read-only AuditLog workspace` is **DONE — MERGED AND EXACT-HEAD VERIFIED** as PR #159, and the C3-II-A baseline is merged `main` `4ef02b8478c3eba06883f5b71290f91edb42a871`. C3 remains **INCOMPLETE**. `C3-II-A — Atomic workshop-profile AuditLog coverage` is implemented on its PR branch and not merged. `C3-II-B — File-backed artifact AuditLog semantics` remains `NEEDS PRODUCT DECISION — NOT AUTHORIZED`. Durable contract: `docs/audit-log.md`.

`CR-005` is accepted and implemented. For newly created backups and exports, the filename reason segment collapses each maximal run of non-alphanumeric separators to one underscore, normalizes literal hyphens to underscores, strips leading and trailing underscores, uses `manual` when empty, prefixes a digits-only result with `reason_`, and preserves letter case and Unicode alphanumerics without lowercasing, transliteration, or new truncation — so `before/update ../unsafe` becomes `before_update_unsafe`, `before-import` becomes `before_import`, `123` becomes `reason_123`, and `перед обновлением` becomes `перед_обновлением`. The create, list, and status `reason` values are that canonical filename-derived segment, and the uniqueness suffix is never part of it.

The visible UI label resolves from the same canonical slug but is not always literally equal to it: the frontend receives the slug from the API and must never reconstruct, sanitize, or normalize it, mapping **known system slugs** to the **existing localized Russian display labels** — canonical `before_import` renders as `Перед импортом` — and rendering **custom or unmapped slugs verbatim**, so canonical `before_update_unsafe` renders as `before_update_unsafe`. The export JSON manifest keeps the normalized human reason. Existing artifacts are not renamed, rewritten, or migrated, and legacy listing stays best-effort.

`R4 — Canonical backup/export filename reason normalization` delivered that contract as one bounded slice covering both nodes through a single shared backend helper, and it is **merged and DONE** as PR #146. `CR-006` is a `needs evidence` row and is **not active**. `CR-004` remains separate and inactive. C1 and C2 are **COMPLETED**. C3-I is merged and closed, but C3 is incomplete under the bounded split above. C4 remains inactive. Restore, packaging/install/update work and full release-candidate smoke remain open, and **product release readiness is not claimed**. Contract: `state/current-focus.md` and `docs/implementation-plan.md`. Evidence: `docs/backend-baseline-failure-triage.md`.

The durable `CR-005` contract documents `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md` record the merged `R4` implementation status, so they agree with the merged `main` behavior.
