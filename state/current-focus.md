# Current focus — R1 Shared safe filename part for backup and export reasons

Active phase: **Pre-release hardening — backend baseline correction gate**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- Active correction slice: `R1 — Shared safe filename part for backup and export reasons`
- Starting `origin/main`: `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa`

Block B is complete. C1, C2, C3, and C4 remain inactive. Current work is release hardening, not feature expansion. Packaging is blocked and release smoke is blocked.

The gate covers exactly these four node IDs:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues
app/tests/test_purchase_suggestions.py::test_manual_api_smoke
```

Full diagnostic evidence, per-node classification, and the two deferred slices live in `docs/backend-baseline-failure-triage.md`.

## Goal

Remove the duplicated filename-part sanitizer shared by the backups and exports services and make the generated reason segment read the way the contract intends, without changing any other backup or export behavior.

## Allowed scope

- Extract one shared safe-filename-part helper used by `backend/app/services/backup.py` and `backend/app/services/export.py`.
- Collapse consecutive replaced characters into a single underscore.
- Preserve each caller's existing empty-result fallback default (`backup` for backups, `manual` for exports) through a parameter.
- Update the two directly affected backend test files only where the new coverage in `Required tests` demands it.

## Expected affected area

- `backend/app/services/backup.py`;
- `backend/app/services/export.py`;
- one shared backend helper module chosen to match existing layering in `backend/app/AGENTS.md`;
- `backend/app/tests/test_backups_api.py` and `backend/app/tests/test_exports_api.py` for added cases only;
- minimal state/documentation updates.

The runtime task must inspect the final baseline before naming its exact changed-file list.

## Non-goals

- `backend/app/services/report_documents.py::sanitize_reason`, which implements a different contract and must not be unified into the shared helper;
- timestamp format, directory resolution, uniqueness/suffix logic, manifest content, export payload schema, or the backup copy mechanism;
- the import draft node (deferred slice `R2`) and the purchase-suggestions node (deferred slice `R3`);
- the separate SQLite backup transaction-consistency candidate;
- any API, schema, migration, dependency, lockfile, or pytest-configuration change;
- any frontend change;
- restore, packaging, release smoke, C1, C2, C3, or C4 work.

## Architecture constraints

- User data stays outside code and package.
- Filenames stay restricted to alphanumerics, `-`, and `_`.
- Path traversal stays impossible.
- Existing backups and exports are never overwritten and never rewritten.
- Artifact generation stays backend-owned.
- Artifacts stay human-readable.
- The backup filename→metadata round trip at `backend/app/services/backup.py:144-149` must not regress. `-` is currently a permitted character in the reason part while the parser splits on `-`; the slice must confirm the parser still resolves the reason correctly for every reason the new helper can produce.
- The source database is never modified by a backup.

## Required tests

- Both baseline nodes pass without weakening or removing any existing assertion.
- A reason consisting entirely of unsafe characters.
- A reason that sanitizes to empty, proving each caller's distinct fallback default.
- A reason containing a literal `-`.
- A backup filename→metadata round trip that recovers the intended reason.
- The complete backend suite from `backend/`.

## Smoke

- Backend suite only.
- Visual check that `/backups` and `/exports` render the reason label correctly at desktop width.

No browser, keyboard, responsive, packaging, or release smoke is required or claimed for this slice.

## Acceptance criteria

- The backend baseline improves from `4 failed` to `2 failed` with no new failure.
- The two remaining failures are exactly the deferred `R2` and `R3` nodes.
- One shared helper replaces both private `_safe_filename_part` definitions, and no third implementation is created.
- No production behavior other than the reason segment of generated filenames changes.
- Every architecture constraint above is verified and reported.
- No skip, `xfail`, deletion, rename, or weakened assertion is introduced.
