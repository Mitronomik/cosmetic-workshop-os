# Current focus — R4 Canonical backup/export filename reason normalization

Active phase: **Pre-release hardening — backend baseline correction gate**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with date normalization`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED / DECIDED**, decision PR #145 **MERGED**
- `R4 — Canonical backup/export filename reason normalization`: **ACTIVE**
- `R4` status: **`IMPLEMENTED — EXACT-HEAD SMOKE REQUIRED BEFORE MERGE`**

`R4` is the single active implementation slice. It is **not DONE**: it is not reviewed and not merged.

## CR-005 decision closure

PR #145 `Decide CR-005 backup/export filename reason contract` is merged (VERIFIED FROM REPOSITORY / GITHUB).

- PR #145 state: `MERGED`
- Final reviewed head: `7d68b45bee1f223b67f105c30e3acbb89dc8d41d`
- Merge commit: `bef36822e50c245b72f813dad0afbffc7f772588`
- Merged at: `2026-07-27T05:15:04Z`

`CR-005` remains **accepted**. The durable contract is unchanged and lives in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`.

## R4 base

- Branch: `claude/r4-canonical-artifact-reason-normalization`
- Base `origin/main`: `bef36822e50c245b72f813dad0afbffc7f772588`
- Merge-base with `origin/main`: `bef36822e50c245b72f813dad0afbffc7f772588`
- Created directly from `origin/main`. No rebase, no force-push, no history rewrite.

## R4 scope, as implemented

Backend production:

```text
backend/app/services/local_artifact_filenames.py   (new shared helper)
backend/app/services/backup.py
backend/app/services/export.py
```

Backend tests:

```text
backend/app/tests/test_local_artifact_filenames.py  (new focused helper matrix)
backend/app/tests/test_backups_api.py               (added cases only)
backend/app/tests/test_exports_api.py               (added cases only)
```

Frontend, test-only:

```text
frontend/test/local-artifacts-reports-feedback.test.mjs
```

Documentation and state: `README.md`, `docs/backup-and-restore.md`, `docs/export.md`, `docs/api.md`, `docs/implementation-plan.md`, `docs/backend-baseline-failure-triage.md`, `state/current-focus.md`, `state/progress.md`, `state/handoff.md`.

**No frontend production change.** `frontend/src/` is untouched. **No migration** — no database migration and no filesystem migration. No API or schema file changed; `backend/app/api/` and `backend/app/schemas/` are untouched. No existing backup or export artifact is renamed, rewritten, or deleted.

## Implementation summary

One shared helper, `normalize_artifact_reason_segment(value: str | None) -> str`, owns the canonical filename reason segment for newly generated backups and exports. It preserves Unicode alphanumerics and letter case, treats the underscore and every other non-alphanumeric character as a separator, collapses each maximal separator run to one underscore, strips edge underscores, falls back to `manual`, and prefixes a digits-only result with `reason_`. Separator classification uses `str.isalnum()` character semantics deliberately, because a `\w`-style regular expression would preserve `_` and other Unicode connector characters.

The same module holds `normalize_artifact_reason`, the human reason rule `(reason or "manual").strip() or "manual"`, to which `normalize_backup_reason` and `normalize_export_reason` now delegate. The human reason and the canonical slug stay distinct: the export manifest keeps the human reason.

The existing filename parsers in `backup.py` and `export.py` needed **no** correction. Because a canonical segment never contains a hyphen and is never digits-only, the existing suffix and stem handling already excludes the `-N` uniqueness suffix and already survives a hyphenated source database stem; both properties are now covered by tests.

## Results

Backend, executed from `backend/` with Python `3.12.13` and pytest `8.4.2` in a temporary virtual environment outside the repository:

- pre-change baseline: `496 collected, 494 passed, 2 failed, 0 skipped`, the two failures being exactly the backups and exports filename-reason nodes;
- post-change: `562 collected, 562 passed, 0 failed, 0 skipped`;
- both former baseline nodes pass, each re-run twice in isolation;
- all 496 previously collected node IDs are still collected; no existing test removed, renamed, skipped, `xfail`-ed, or weakened.

Frontend:

- `npm run test:local-artifacts-reports-feedback`: `40 pass, 0 fail, 0 skipped` (34 before the added cases);
- `npm run build`: succeeds.

Frontend evidence is mixed by necessity: the generic presentation layer is imported and invoked directly, proving an unmapped slug renders verbatim; the `backupReasonLabelRaw` / `exportReasonLabelRaw` mappings live in `frontend/src/main.ts` and are not exported, so their coverage is **static source-contract evidence**, not runtime invocation. The runtime proof for both the unmapped slug and the known `before_import` Russian mapping comes from the exact-published-head browser smoke.

## Remaining gate

The focused `/backups` and `/exports` browser smoke against the **exact published pull-request head**, at desktop `1440 × 900`, with an isolated temporary SQLite database, an isolated temporary user-data directory, an isolated browser profile, and no real user data. Evidence stays outside Git. A passing smoke is invalidated by any later commit; a new commit requires the complete smoke to be re-run.

Repository files deliberately do **not** claim a passing browser smoke, because a post-smoke documentation commit would change the head and invalidate the evidence.

## Other work

- `CR-004` — potential SQLite backup transaction consistency — remains a separate `needs evidence` row. It is **not** resolved, activated, or affected by `R4`.
- Restore remains unimplemented.
- C1, C2, C3, and C4 remain **inactive**.
- Packaging and release smoke remain **blocked**.
- **Product release readiness is not claimed.**
