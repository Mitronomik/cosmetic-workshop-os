# Current focus — R3 Repair purchase-suggestions API smoke seeding

Active phase: **Pre-release hardening — backend baseline correction gate**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- Active correction slice: `R3 — Repair purchase-suggestions API smoke seeding`
- Starting `origin/main`: `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa`

Block B is complete. C1, C2, C3, and C4 remain inactive. Current work is release hardening, not feature expansion. Packaging is blocked and release smoke is blocked.

The gate covers exactly these four node IDs:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues
app/tests/test_purchase_suggestions.py::test_manual_api_smoke
```

Gate status by node:

- backups and exports filename nodes — `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED`. No slice. Blocked on the `needs product decision` change request in `state/change-requests.md`.
- import draft node — `TEST DEFECT`. Slice `R2`, deferred, next after `R3`.
- purchase-suggestions node — `TEST DEFECT`. Slice `R3`, **active**.

Full diagnostic evidence and the mandatory per-node fields live in `docs/backend-baseline-failure-triage.md`.

## Goal

Make the purchase-suggestions API smoke test reach and exercise the `/api/purchase-suggestions` HTTP surface by repairing only its invalid seed, so that its existing assertions — including the three no-mutation assertions — actually execute.

## Allowed scope

Change exactly one value, and nothing else:

- In the `seed_ready(...)` call at `backend/app/tests/test_purchase_suggestions.py:214`, change `lot_qty="0"` to `lot_qty="1"`.
- Leave `packaging_qty="2"` on that same line unchanged.
- Leave the existing `minimum_stock='10'` setup at `backend/app/tests/test_purchase_suggestions.py:215-216` unchanged.
- The existing threshold of `10` is already higher than the new lot quantity of `1`, so the below-minimum condition the test needs remains true without touching the threshold.
- No other line in the test may change.

## Expected affected area

- `backend/app/tests/test_purchase_suggestions.py`;
- minimal state/documentation updates.

The runtime task must inspect the final baseline before naming its exact changed-file list.

## Non-goals

- Any production-code change. This slice is **test-only**.
- Any change to `seed_ready`'s signature or body in `backend/app/tests/test_production_confirmation.py`, or to any other of its 45 call sites.
- Any change to the zero-quantity domain rule at `backend/app/domain/stock_movements.py:84-93`.
- Any change to the existing `minimum_stock='10'` setup, or to any line of the test other than the `lot_qty` value on line 214.
- The backups and exports filename nodes, which have no slice and are blocked on a product decision.
- The import draft node (deferred slice `R2`).
- The separate SQLite backup transaction-consistency candidate.
- Any API, schema, migration, dependency, lockfile, or pytest-configuration change.
- Any frontend change.
- Restore, packaging, release smoke, C1, C2, C3, or C4 work.

## Architecture constraints

- The zero-quantity rejection rule stays intact and unmodified; it is correct behavior and is not the subject of this slice.
- Stock changes stay routed through `StockMovement`.
- The test's three no-mutation assertions stay intact and must execute.
- The existing `minimum_stock='10'` threshold stays unchanged; the below-minimum condition is preserved by the threshold already exceeding the new lot quantity of `1`, not by editing the threshold.
- The diff for this slice is exactly one changed value on one line.
- No production file is modified.

## Required tests

- The node reaches the API and exercises: regenerate creates at least one suggestion; list returns it; mark-purchased returns `purchased`; the suggestion leaves the open list; it remains visible under `status=all`.
- The three no-mutation assertions execute and pass: stock-movement count, packaging-stock-movement count, and ingredient-lot count are all unchanged.
- Every existing assertion is preserved.
- No skip, `xfail`, deletion, rename, or weakened assertion.
- The complete backend suite is run from `backend/`.

## Smoke

**Backend suite only.** This slice changes no runtime surface, so no browser, visual, or route-rendering check applies, is required, or may be claimed.

Any focused visual check for `/backups` and `/exports` belongs to the unresolved backup/export filename product decision and its future implementation slice, not to this slice.

## Acceptance criteria

- The backend baseline improves from `4 failed` to `3 failed` with no new failure.
- The three remaining failures are exactly the two undecided filename nodes and the deferred `R2` node.
- The three no-mutation assertions execute and pass.
- No production file is modified.
- No skip, `xfail`, deletion, rename, or weakened assertion is introduced.
