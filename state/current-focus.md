# Current focus — CR-005 Backup/export filename reason product decision

Active phase: **Pre-release hardening — backend baseline correction gate**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with date normalization`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED / DECIDED**
- Next implementation slice: `R4 — Canonical backup/export filename reason normalization`
- `R4` status: `AUTHORIZED AFTER THIS DECISION PR MERGES — NOT IMPLEMENTED`

This focus covers a **documentation-only product decision**. No runtime correction is implemented here.

## R3 lifecycle closure

`R3` is **DONE**. PR #143 `R3 — Repair purchase-suggestions API smoke seeding` is merged (VERIFIED FROM REPOSITORY / GITHUB).

- PR #143 state: `MERGED`
- Final reviewed head: `c5fc27059a7aea0435c84535d2d15e6a0fc58428`
- Merge commit: `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`
- Merged at: `2026-07-27T04:01:23Z`
- Accepted `R3` backend result: `496 collected, 493 passed, 3 failed, 0 skipped`
- No production code changed in `R3`; it was test-only.

## R2 lifecycle closure

`R2` is **DONE**. PR #144 `R2 — Align import draft baseline test with date normalization` is merged (VERIFIED FROM REPOSITORY / GITHUB).

- PR #144 state: `MERGED`
- Final reviewed head: `52e2c64fc601b458cfd60e8b86a778efabd65671`
- Merge commit: `8efbdc5c85b5932f4aeef51045542c207cf4635c`
- Merged at: `2026-07-27T04:21:16Z`
- `origin/main` at the time of this decision: `8efbdc5c85b5932f4aeef51045542c207cf4635c`
- No production code changed in `R2`; it was test-only.

`R2` is no longer active. Nodes 3 and 4 of the gate are closed.

## Current backend baseline

Accepted result after `R2` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — **not** re-executed for this decision):

```text
496 collected
494 passed
2 failed
0 skipped
```

The two remaining failing nodes are exactly:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

Both still fail. This decision does not fix them and does not claim a `0-failure` backend state.

## CR-005 decision

`CR-005` is **accepted** (RECORDED PRODUCT-OWNER DECISION). The durable contract lives in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`; the plan record is in `docs/implementation-plan.md`.

**Two representations, never conflated.** The *human reason* is `text = (reason or "manual").strip() or "manual"`. The *filename reason segment* is a canonical, path-safe, unambiguous slug derived from it.

**Canonical algorithm** for newly created backups and exports:

1. preserve Unicode alphanumerics exactly;
2. treat underscore as a separator;
3. treat every non-alphanumeric character as a separator — whitespace, hyphen, dot, slash, backslash, punctuation, symbols;
4. collapse each maximal run of separators to one underscore;
5. strip leading and trailing underscores;
6. empty result → `manual`;
7. digits-only result → prefix `reason_`;
8. preserve letter case;
9. preserve Unicode alphanumerics — no lowercasing, no transliteration;
10. no new length limit; the existing 80-character request limit is unchanged.

| Input | Canonical segment |
|---|---|
| `before/update ../unsafe` | `before_update_unsafe` |
| `before-import` | `before_import` |
| `___before---import___` | `before_import` |
| `перед обновлением` | `перед_обновлением` |
| `123` | `reason_123` |
| whitespace only | `manual` |
| punctuation only | `manual` |

**Hyphen** — not allowed inside a newly generated filename reason segment; normalizes to underscore. The hyphen is already a structural filename separator, backup metadata parsing splits on it, allowing it makes the round trip ambiguous, and the uniqueness suffix is a hyphen plus a number. Hyphens stay allowed in the human reason and the export manifest reason.

**Numeric-only** — a filename reason segment is never purely numeric; a numeric-only human reason gets the `reason_` prefix so it cannot be confused with the uniqueness suffix `-1`, `-2`, `-3`.

**Grammar preserved** — no new filename version, marker, sidecar format, or migration. New names remain conceptually `{timestamp}-{safe_source_stem}-{canonical_reason}[-N].{sqlite_suffix}` and `{timestamp}-cosmetic_workshop-export-{canonical_reason}[-N].json`, with `-N` reserved solely for uniqueness and non-overwrite behavior unchanged.

**Round trip** — for newly generated artifacts the create, list, and status reasons are all the same canonical segment and the visible UI reason resolves from it; the uniqueness suffix is never part of the reported reason. The source database stem keeps separate sanitization and may contain hyphens; the implementation must prove a hyphenated stem does not break canonical reason parsing.

**Displayed reason** — filename-derived, from the existing API `reason` field. No metadata table, sidecar file, new API field, frontend-only reconstruction rule, or hidden persistent metadata. Two layers, both preserved:

- the **backend/API `reason` is the canonical slug** and the single source of truth;
- the **frontend consumes that slug and must never reconstruct, sanitize, or normalize it** — it maps **known system slugs** to the **existing localized Russian display labels** and renders **custom or unmapped slugs verbatim**.

The visible label is therefore **not always literally the canonical slug**: canonical `before_import` renders as `Перед импортом`, while canonical `before_update_unsafe` is unmapped and renders verbatim. Exact per-screen mappings are recorded in `docs/backup-and-restore.md` and `docs/export.md`; the backup and export mappings differ (`manual` is `Обычная резервная копия` on `/backups` and `Обычный экспорт` on `/exports`). No Russian label is added, removed, or reworded by this decision.

**Export manifest** — keeps the normalized human reason, not the slug. Export schema version unchanged.

**Legacy compatibility** — existing artifacts are never renamed, rewritten, or deleted; no migration. Legacy listing stays best-effort and preserves filename, path, created-timestamp fallback, size, and list availability. Exact round-trip recovery is not claimed for legacy ambiguous filenames.

**Shared helper boundary** — one narrowly scoped helper, recommended `normalize_artifact_reason_segment(value: str | None) -> str` in `backend/app/services/local_artifact_filenames.py`. It applies only to backup and export filename reason segments — never to backup source stems, report-document reasons or filenames, uploaded filenames, recipe names, client names, or any unrelated domain value. `backend/app/services/report_documents.py` keeps its deliberately different contract and is not unified into it.

## Post-decision classification

The original diagnostic evidence and its classification at diagnosis time are preserved in `docs/backend-baseline-failure-triage.md` §5, §6, and §9.

| Node | Post-decision classification | Severity |
|---|---|---|
| Node 1 — backups filename reason | `PRODUCT DEFECT — CONTRACT MISMATCH` | MEDIUM |
| Node 2 — exports filename reason | `PRODUCT DEFECT — CONTRACT MISMATCH` | MEDIUM |

No proven data loss, no source database mutation, and no overwrite regression for either node. Shared root cause: duplicated one-character-at-a-time sanitizers that both preserve the hyphen and both lack the decided run-collapse and numeric-disambiguation rules. One bounded slice corrects both.

## Next slice — R4

`R4 — Canonical backup/export filename reason normalization`

Status: **`AUTHORIZED AFTER THIS DECISION PR MERGES — NOT IMPLEMENTED`**

- **No runtime implementation may begin from this unmerged decision branch.** Start `R4` only from `origin/main` after this decision PR is merged.
- Scope, Non-goals, Architecture constraints, Backend requirements, Frontend requirements, Tests, Smoke, and Acceptance criteria are recorded in `docs/implementation-plan.md` and summarized in `docs/backend-baseline-failure-triage.md` §14.6.
- Expected production surface: `backend/app/services/local_artifact_filenames.py`, `backend/app/services/backup.py`, `backend/app/services/export.py`. A parser change inside those same modules is allowed only where the new-file round-trip contract requires it.
- Acceptance requires the complete backend suite from `backend/` with **`0 failed` and `0 skipped`**, both former baseline nodes passing, and no existing test deleted, renamed, skipped, `xfail`-ed, or weakened. The `496` collection count is not required to stay exact, because `R4` adds tests.
- `R4` additionally requires the focused frontend local-artifact suites, the frontend production build, and the focused `/backups` and `/exports` browser smoke at desktop `1440 × 900` with isolated temporary data. The smoke reason `before_update_unsafe` is deliberately an **unmapped** slug, so its visible label must be exactly `before_update_unsafe`.
- **No frontend production change is expected**, but `R4` is allowed **focused frontend test-only** changes, because no runnable suite currently proves the canonical-reason display contract. Preferred: add reason-presentation assertions to the runnable `frontend/test/local-artifacts-reports-feedback.test.mjs`. Alternative: make the standalone local-artifact-presentation suite runnable via an exact tsconfig and npm script **without adding dependencies**. Those tests must prove verbatim rendering of an unmapped slug, the existing Russian mapping for a known system slug, and that the frontend does not reconstruct, sanitize, or normalize the slug. Any production change needed to reach the mapping is **not** pre-authorized — record the evidence and update the contract first.

## Scope of this decision task

Allowed: `README.md`, `docs/backup-and-restore.md`, `docs/export.md`, `docs/api.md`, `docs/implementation-plan.md`, `docs/backend-baseline-failure-triage.md`, `state/current-focus.md`, `state/progress.md`, `state/handoff.md`, `state/change-requests.md`.

Not allowed here: any backend or frontend production change; any test change; creating the shared helper; changing filename generation, metadata parsing, or API responses; making either failing test pass; running backend, frontend, API, packaging, or browser smoke; claiming a backend `0-failure` state; implementing `R4`.

## Other work

- `CR-004` — potential SQLite backup transaction consistency — remains a separate `needs evidence` row. It is **not** resolved, activated, or affected by this decision.
- C1, C2, C3, and C4 remain **inactive**.
- Packaging and release smoke remain **blocked**.
- **Product release readiness is not claimed.**
