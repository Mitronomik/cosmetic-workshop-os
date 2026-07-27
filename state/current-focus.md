# Current focus — R2 Import draft baseline test contract alignment

Active phase: **Pre-release hardening — backend baseline correction gate**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- Active correction slice: `R2 — Align import draft baseline test with the documented date-normalization contract`
- Slice status: `IMPLEMENTED — REVIEW AND MERGE REQUIRED`
- Starting `origin/main` for the `R2` implementation: `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`

## R3 lifecycle closure

`R3` is **DONE**. PR #143 `R3 — Repair purchase-suggestions API smoke seeding` is merged (VERIFIED FROM REPOSITORY / GITHUB).

- PR #143 state: `MERGED`
- Final reviewed head: `c5fc27059a7aea0435c84535d2d15e6a0fc58428`
- Merge commit: `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`
- Merged at: `2026-07-27T04:01:23Z`
- Accepted `R3` backend result: `496 collected, 493 passed, 3 failed, 0 skipped`
- No production code changed in `R3`; it was test-only.

`R3` is no longer active. Exactly one slice is active and it is `R2`.

## Implementation status

`R2` is implemented on branch `claude/r2-align-import-draft-baseline-test` and is **not merged and not DONE**. It stays the current active slice until it is reviewed and merged.

- Exact test change: the assertion block of `backend/app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues` only. `error_count >= 4` became `error_count == 3`; `warning_count == 1` and `apply_readiness.can_apply is False` were added; the row-code subset assertion `{"invalid_decimal", "invalid_unit", "invalid_date"} <= row_codes` became the exact-set assertion `row_codes == {"invalid_decimal", "invalid_unit", "date_format_normalized"}`. The global `missing_required_column` assertion, the response status assertion, the request payload, the CSV data, and the target type are unchanged. The corrected assertions are strictly more specific than the ones they replace.
- No production change. Test-only.
- Executed backend results, from `backend/` with Python `3.12.13` and pytest `8.4.2` (rootdir `backend/`, configfile `pyproject.toml`): pre-change complete suite `496 / 493 / 3 / 0`; pre-change isolated target failed at `assert 3 >= 4` at `backend/app/tests/test_imports_api.py:107` after a `201` response; post-change target node `PASSED` twice; `app/tests/test_imports_api.py` `7 passed`; `app/tests/test_import_parsing.py` `16 passed`; post-change complete suite `496 collected, 494 passed, 2 failed, 0 skipped`.
- Remaining failures are exactly the two undecided filename nodes.
- Smoke: **backend suite only — PASS**. No browser, visual, keyboard, responsive, packaging, restore, migration, or release smoke was required, executed, or claimed.

Block B is complete. C1, C2, C3, and C4 remain inactive. Current work is release hardening, not feature expansion. Packaging is blocked and release smoke is blocked.

The gate covers exactly these four node IDs:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues
app/tests/test_purchase_suggestions.py::test_manual_api_smoke
```

Gate status by node:

- backups and exports filename nodes — `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED`. No slice. Blocked on `CR-005` in `state/change-requests.md`. **Do not begin the filename correction from the unmerged `R2` branch**, and do not begin it at all before `CR-005` is decided.
- import draft node — `TEST DEFECT`. Slice `R2`, **active**, implemented, pending review and merge.
- purchase-suggestions node — `TEST DEFECT`. Slice `R3`, **DONE** (PR #143 merged).

Full diagnostic evidence and the mandatory per-node fields live in `docs/backend-baseline-failure-triage.md`.

## Goal

Make the import draft baseline test assert the documented import validation contract exactly, so the deterministic Russian `DD.MM.YYYY` date `05.07.2026` is expected to produce the documented `date_format_normalized` **warning** rather than an `invalid_date` error.

## Allowed scope

Only the assertion block inside `test_missing_required_columns_and_row_errors_create_draft_with_issues` in `backend/app/tests/test_imports_api.py`:

```python
assert body["draft"]["error_count"] == 3
assert body["draft"]["warning_count"] == 1
assert body["draft"]["apply_readiness"]["can_apply"] is False
assert {issue["code"] for issue in body["issues"]} >= {"missing_required_column"}
row_codes = {issue["code"] for issue in body["preview_rows"][0]["issues"]}
assert row_codes == {
    "invalid_decimal",
    "invalid_unit",
    "date_format_normalized",
}
```

Plus minimal documentation and state reconciliation.

## Non-goals

- Any production-code change. This slice is **test-only**.
- Any change to `_normalize_date_value`, readiness calculation, issue counting, required-column behavior, `missing_required_value`, import Apply, or the import preview/confirmation flow.
- Any change to `docs/import-format.md` to fit the old test.
- Changing the test date `05.07.2026`, replacing it with an invalid date, removing the warning assertion, or using subset assertions for the row codes after correction.
- Skipping, `xfail`-ing, renaming, deleting, or weakening the test.
- The backups and exports filename nodes, which have no slice and are blocked on `CR-005`.
- Deciding `CR-005`, changing backup filename parsing, or creating a shared sanitizer.
- Investigating or implementing `CR-004`.
- Any API, schema, migration, dependency, lockfile, or pytest-configuration change.
- Any frontend change.
- Restore, packaging, release smoke, C1, C2, C3, or C4 work.

## Architecture constraints

- The import flow stays `draft → preview → validation → confirmation → apply`.
- Deterministic `DD.MM.YYYY` normalization remains supported and `date_format_normalized` remains a **warning**.
- `invalid_date` remains reserved for genuinely invalid dates, and that behavior stays covered by `backend/app/tests/test_import_parsing.py`.
- Missing required columns continue to block Apply; blocked drafts cannot be applied.
- Warnings and errors remain visible and are not silently discarded; no validation is weakened.
- No production data is mutated by this test.
- No production file is modified.

## Required tests

- The target node passes twice in isolation.
- `app/tests/test_imports_api.py` passes `7/7`.
- `app/tests/test_import_parsing.py` passes completely with zero skips, proving that `date_format_normalized` still works and that genuinely invalid dates still emit `invalid_date`.
- The complete backend suite is run from `backend/` and reports `496 collected, 494 passed, 2 failed, 0 skipped`.
- No skip, `xfail`, deletion, rename, or weakened assertion.

## Smoke

**Backend suite only.** This slice changes no runtime surface, so no browser, visual, keyboard, responsive, route-rendering, packaging, restore, migration, or release check applies, is required, or may be claimed.

Any focused visual check for `/backups` and `/exports` belongs to the unresolved backup/export filename product decision and its future implementation slice, not to this slice.

## Acceptance criteria

- The backend baseline improves from `3 failed` to `2 failed` with no new failure and no skip.
- The two remaining failures are exactly the two undecided filename nodes.
- The purchase-suggestions node remains passing.
- No production file is modified.
- The corrected assertions are strictly more specific than the ones they replace.
- `R2` is not DONE until it is reviewed and merged.
