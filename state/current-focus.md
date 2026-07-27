# Current focus — Post-R4 pre-release hardening and next-gate selection

Active phase: **Pre-release hardening — backend baseline correction gate CLOSED; next gate not yet selected**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with date normalization`: **DONE**
- `R4 — Canonical backup/export filename reason normalization`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED AND IMPLEMENTED**
- Backend baseline correction gate: **DONE**
- Merged `main` backend baseline: **GREEN**
- **No active runtime implementation slice.**

All four accepted backend baseline gate failures are closed on `main`. **This document does not select the next implementation slice**; the next slice must be separately selected and authorized.

## R4 merge closure

`R4` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE).

- PR #146 `R4 — Canonical backup/export filename reason normalization`, state `MERGED`
- Final reviewed head: `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`
- Merge commit: `127191feb182ccf68a4d7b9f2be28f6aa5b42453`
- Merged at: `2026-07-27T08:51:06Z`
- `origin/main` equals that merge commit; both the final head and the merge commit were verified as ancestors of `origin/main`.

Both original filename nodes are closed on `main`:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

## Accepted merged evidence

All results below are **VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE**. None of them was executed in the documentation task that wrote this section.

| Check | Accepted result |
|---|---|
| Backend complete suite | `562 collected, 562 passed, 0 failed, 0 skipped` |
| Frontend focused suite | `40 passed, 0 failed, 0 skipped` |
| Frontend production build | `PASS` |
| Focused exact-published-head `/backups` and `/exports` browser smoke | `PASS — FULL AUTOMATED SMOKE PASSED` |
| Exact smoke-tested head | `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb` |

The merged slice involved **no frontend production change**, **no database migration**, **no filesystem migration**, and **no existing artifact renamed, rewritten, or deleted**.

## CR-005 status

`CR-005` remains **accepted** and is now **implemented**. The durable contract is unchanged and lives in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`. The canonical filename reason segment is owned by the shared backend helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`; the export JSON manifest continues to carry the normalized human reason.

`R4` is closed and is **not reopened**. `CR-005` is closed and is **not reopened**.

## CR-006 — export create-response fallback — NEEDS EVIDENCE, not active

`CR-006 — Investigate export create-response fallback confirmation semantics` is a new **`needs evidence`** row in `state/change-requests.md`. It is **not an active implementation slice** and is **non-blocking** for `R4` closure.

Exact current behavior in `backend/app/api/exports.py::create_export`:

- after `create_json_export` writes an export, the endpoint attempts to find the exact created file through `list_export_files`;
- when the exact file is found, the API response uses parsed filename metadata and therefore returns the canonical filename-derived reason;
- when the exact file is **not** found, the defensive fallback constructs an `ExportFile` using `ExportResult.reason`;
- `ExportResult.reason` is the normalized **human** reason preserved in the export manifest;
- therefore the fallback may return a human reason where the API contract normally expects the canonical filename-derived slug.

Classification: **NEEDS EVIDENCE.** This is **not** classified as a confirmed product defect. No user-visible failure has been reproduced. No data loss, overwrite, incorrect file content, or unsafe mutation is proven. The normal path is green in the backend suite, in create/list/status integration coverage, and in the exact-head browser smoke. Fallback reachability is not established, **no severity is assigned**, and **no correction design is authorized**.

`CR-006` is not part of `CR-004`, is not a reason to reopen `CR-005`, and is not a reason to reopen `R4`. It is **not** a fifth backend baseline failure. Full evidence: `docs/backend-baseline-failure-triage.md` §17.

## Remaining release obligations

None of these is activated here.

- `CR-004` — SQLite backup transaction-consistency investigation — remains a separate `needs evidence` row and is **not active**.
- Restore product decision and implementation remains **open**.
- Final macOS packaging and user-ready launch remains **open**.
- Installation verification remains **open**.
- Packaged update flow and update smoke remain **open**.
- Full release-candidate smoke remains **open**.
- C1, C2, C3, and C4 remain **inactive** unless separately authorized.
- Continuing documentation accuracy remains an obligation — `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md` still carry a pre-merge `R4` implementation-status line and were outside the scope of the closure slice.

**Product release readiness is not claimed.**
