# ADR - JSON export create-response confirmation semantics

## Status

`ACCEPTED`

Date: `2026-08-01`

Change request: `CR-006 — Investigate export create-response fallback confirmation semantics`.

Resulting change-request status: **`accepted — product defect confirmed and contract decided`**.

Surrounding lifecycle:

```text
C1 — COMPLETED
C2 — COMPLETED
C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-009 — ACCEPTED
C3-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-006 — ACCEPTED — PRODUCT DEFECT CONFIRMED AND CONTRACT DECIDED
C3-II-B2 — AUTHORIZED AFTER THIS DECISION PR MERGES — NOT IMPLEMENTED
C3-II-B3 — BLOCKED BY CR-004 — NOT AUTHORIZED
C3 — INCOMPLETE
C4 — INACTIVE — NEEDS PRODUCT DECISION
Product release readiness — NOT CLAIMED
```

This ADR changes **no production code**, adds **no migration**, changes **no
dependency**, and does **not** implement `C3-II-B2`. It records a product
decision and the diagnostic evidence behind it.

> **Current lifecycle pointer — not part of the accepted decision.** The block
> above records the slice authorization as it stood when this ADR was accepted on
> 2026-08-01, and the accepted decision below is unchanged and is not reopened.
> Since then `C3-II-B2` has been implemented on branch
> `claude/c3-ii-b2-json-export-audit` and is
> `IMPLEMENTED ON PR BRANCH — NOT MERGED`; that branch carries the
> create-response correction decided here, so `POST /api/exports` no longer
> re-scans the export directory and its `reason` is parsed from the exact final
> filename. Because the branch is unmerged, merged `main` still exhibits the
> behavior this ADR classifies as the defect. `CR-004` remains `needs evidence`,
> `C3-II-B3` stays blocked, C3 is still incomplete, C4 is still inactive, and
> product release readiness is still not claimed. Current authority:
> `state/current-focus.md`.

---

## Context

`CR-006` was opened as a `needs evidence` row after `R4` merged. It recorded a
read-only observation about `backend/app/api/exports.py::create_export`: after
`create_json_export(...)` has written an export, the endpoint re-scans the whole
export directory through `list_export_files(...)` and looks for the exact
created file; when that exact-path lookup fails, a defensive fallback builds the
response from `ExportResult` instead — and `ExportResult.reason` is the
normalized **human** manifest reason, not the canonical filename-derived slug
that `CR-005` makes the API contract.

`CR-006` deliberately asserted nothing further. Fallback reachability was not
established, no severity was assigned, and no correction design was authorized.
This ADR closes that gate with executed evidence.

The diagnostic question, answered here exactly as posed:

```text
Can the defensive fallback in the JSON export create-response path occur in
real production-equivalent behavior, and what must POST /api/exports return
after create_json_export has already successfully written and stat-ed the exact
final file?
```

---

## Code evidence

Traced from source at `origin/main` = `1d4e90ccffb6f154882e685b09803f67f2f75ceb`
(the merge commit of lifecycle-closure PR #164). All line references are that
tree.

### The create path

`backend/app/api/exports.py:58-88`:

1. `resolve_export_paths()` — pure path computation, creates nothing;
2. `normalize_export_reason(...)` — the **human** reason
   (`normalize_artifact_reason`, `backend/app/services/local_artifact_filenames.py:14`);
3. `create_json_export(...)` inside a `try` that maps only
   `ExportSourceMissingError` → `404` and `ExportError` → `409`;
4. `next((export for export in list_export_files(paths.export_dir) if export.path == result.export_path), ExportFile(... reason=result.reason ...))`
   — a **directory-wide re-scan** used as the response metadata source, with an
   eagerly constructed fallback default;
5. `ExportCreateResponse` built from whichever `ExportFile` won.

### What the creator guarantees before it returns

`backend/app/services/export.py:222-268`. `create_json_export` returns an
`ExportResult` only after, in order:

- the source database path exists and is a regular file (`:232-235`);
- the whitelisted tables are read from the source database opened read-only
  (`:238`, `:203-219`);
- the manifest and payload are serialized (`:239-250`);
- the export directory is created if needed (`:252`);
- the **exact final unique path** is selected by `_unique_export_path` (`:253`,
  `:119-128`);
- `export_path.write_text(...)` completes; an `OSError` here is converted to
  `ExportError` and no result is returned (`:254-260`);
- `export_path.stat().st_size` is read from that same exact final path
  (`:266`).

Therefore `ExportResult` carries the exact final path, the creator's own
`created_at`, the human reason, the size measured on the finished file, and the
entity counts. It cannot be produced before the write completed.

### Why the exact-path lookup can fail while the file exists

`list_export_files` (`backend/app/services/export.py:167-184`) is a best-effort
listing, not a confirmation primitive:

- `candidate.is_file()` (`:174`) is evaluated **outside** the `try`. `pathlib`
  swallows only ignorable errnos (`ENOENT`, `ENOTDIR`, `EBADF`, `ELOOP`) and
  **re-raises everything else**, so a non-ignorable `stat` failure on one entry
  escapes the whole listing;
- `_export_file_metadata` (`:151-164`) calls `path.stat().st_size` (`:163`);
  an `OSError` there is caught at `:178-179` and the entry is **silently
  skipped**;
- `resolved_export_dir.iterdir()` (`:173`) is not guarded at all.

So the exact created file can be absent from the returned list for reasons that
have nothing to do with whether creation succeeded, and the whole listing can
raise for reasons that have nothing to do with the created file.

### The two reason representations

- `ExportResult.reason` — `normalize_artifact_reason(...)` — the human reason,
  the value the manifest preserves;
- `ExportFile.reason` from the listing — `_parse_export_reason(path)`
  (`:139-148`) — the canonical filename segment, uniqueness suffix stripped.

`CR-005` makes the second one the API contract for create, list and status.
The fallback uses the first one.

---

## Diagnostic matrix

Executed `2026-08-01` against repository SHA
`1d4e90ccffb6f154882e685b09803f67f2f75ceb`, Python `3.12.10`, FastAPI
`0.115.12`, through the real FastAPI route with `TestClient`, the real
`create_json_export`, an isolated migrated SQLite database and an isolated
export directory per scenario. No production file was modified; faults were
injected only at named OS boundaries (`pathlib.Path.stat`,
`pathlib.Path.iterdir`) or at a named module seam
(`app.api.exports.list_export_files`, `app.api.exports.create_json_export`).
The harness lived outside the repository and is not committed.

Reason under test throughout, chosen so the two representations differ:

```text
human / manifest reason:  before-update ../unsafe
canonical filename reason: before_update_unsafe
```

| # | Scenario | Injected boundary | Classification | HTTP | Artifact result | Response `reason` | Manifest `reason` | Canonical | Conclusion |
|---|---|---|---|---|---|---|---|---|---|
| 8.1 | Normal creation | none | `NORMAL` | `201` | created, `3414` bytes, path exists | `before_update_unsafe` | `before-update ../unsafe` | `before_update_unsafe` | create, list and status agree on the canonical slug; response `size_bytes` equals the on-disk size; manifest keeps the human reason |
| 8.2 | Numeric uniqueness suffix | frozen clock in `app.services.export.datetime` | `NORMAL` | `201`, `201` | `…-before_update_unsafe.json` and `…-before_update_unsafe-1.json` | `before_update_unsafe` for both | `before-update ../unsafe` for both | `before_update_unsafe` | the `-1` suffix never enters any reported reason; create/list/status agree |
| 8.3 | Synthetic empty-list control | `app.api.exports.list_export_files` → `[]` for the create call only | `CONTROL-ONLY` | `201` | created, path exists | **`before-update ../unsafe`** | `before-update ../unsafe` | `before_update_unsafe` | the fallback **is executable** and returns the human reason — a `CR-005` violation. A later ordinary list/status returns the canonical slug, so the two disagree for the same file |
| 8.4a | Re-list `stat` → `ENOENT` on the exact file | `pathlib.Path.stat` during the endpoint's secondary `list_export_files` only | `PRODUCTION-EQUIVALENT` | `201` | **created and still present** | **`before-update ../unsafe`** | `before-update ../unsafe` | `before_update_unsafe` | `is_file()` treats `ENOENT` as ignorable → entry skipped → fallback runs. This is exactly a directory-entry race between `iterdir()` and the per-file `stat` |
| 8.4b | Re-list `stat` → `EACCES` on the first `stat` | same boundary | `PRODUCTION-EQUIVALENT` | **`500`** | **created and still present** | none — generic error body | `before-update ../unsafe` | `before_update_unsafe` | `is_file()` re-raises a non-ignorable `OSError`; nothing catches it. A fully successful creation is reported as a **total failure** |
| 8.4c | Re-list `stat` → `EIO` after `is_file()` succeeded | same boundary | `PRODUCTION-EQUIVALENT` | `201` | **created and still present** | **`before-update ../unsafe`** | `before-update ../unsafe` | `before_update_unsafe` | the principal fallback path: `_export_file_metadata`'s `stat().st_size` fails, `list_export_files` skips the entry, the fallback returns the human reason. A later ordinary list/status returns `before_update_unsafe` for the same file |
| 8.4d | Re-list `stat` → `EACCES` after `is_file()` succeeded | same boundary | `PRODUCTION-EQUIVALENT` | `201` | **created and still present** | **`before-update ../unsafe`** | `before-update ../unsafe` | `before_update_unsafe` | identical outcome to 8.4c; the errno does not matter once `is_file()` has passed |
| 8.5 | Artifact removed after the creator returned | wrapper deletes the exact path after the real creator returned | `EXTERNAL-RACE` | `201` | created by the application, then **removed by the injected external actor** | **`before-update ../unsafe`** | `before-update ../unsafe` (read before deletion) | `before_update_unsafe` | fallback runs; `201` points at a now-missing path with the creator's `size_bytes` `3414`; later list and status correctly omit it. The application completed creation; an external actor removed it afterwards |
| 8.6 | Directory iteration failure | `pathlib.Path.iterdir` → `OSError(EACCES)` for the export dir | `ADJACENT — CR-006 BOUNDARY` | **`500`** | **created and still present** | none — generic error body | `before-update ../unsafe` | `before_update_unsafe` | the fallback is **bypassed**: the exception escapes `list_export_files` before any candidate is considered. Same false-total-failure outcome as 8.4b, same cause — the redundant secondary scan |
| 8.7a | Exact path replaced by a **directory** | replacement after the creator returned | `EXTERNAL-RACE` | `201` | a directory now occupies the path | **`before-update ../unsafe`** | unreadable (`IsADirectoryError`) | `before_update_unsafe` | `is_file()` is false → skipped → fallback; response reports the creator's `3414` bytes |
| 8.7b | Exact path replaced by a **symlink** to an outside file | replacement after the creator returned | `EXTERNAL-RACE` | `201` | symlink to foreign content | `before_update_unsafe` | foreign content, no manifest | `before_update_unsafe` | the re-list **matches the foreign object** and reports **its** size, `18` bytes, instead of the created `3414`. The directory scan actively describes something the application did not create |
| 8.7c | Exact path replaced by **another regular file** | replacement after the creator returned | `EXTERNAL-RACE` | `201` | foreign regular file | `before_update_unsafe` | foreign content, no manifest | `before_update_unsafe` | same as 8.7b with `19` bytes |
| 8.8 | Creator's own final `stat` fails | `pathlib.Path.stat` → `OSError(EIO)` at `export_path.stat().st_size`, after `write_text()` succeeded | `ADJACENT-NON-CR006` | **`500`** | **the export file remains on disk** and lists normally afterwards | none — generic error body | `before-update ../unsafe` | `before_update_unsafe` | `create_json_export` never returns; the raw `OSError` is neither `ExportSourceMissingError` nor `ExportError`, so the endpoint's handlers do not apply. **The fallback is unreachable on this path.** A complete export exists that the caller was told nothing about |
| 8.9 | Ordinary `GET` list and status under the same read failures | `Path.stat` on one file; `Path.iterdir` on the directory | `ADJACENT-NON-CR006` | list `200` with the export **silently omitted**; status `200` with `export_count: 0`, `latest_export: null`; under `iterdir` failure **both** `500` | file present throughout | n/a | n/a | n/a | the GET endpoints inherit the same best-effort listing. Their behavior is recorded, and this decision deliberately does **not** change their contract |

No scenario was `INCONCLUSIVE`.

---

## Reachability conclusion

Answering the sub-questions in order:

1. **Is the fallback executable?** Yes — proven directly by control 8.3.
2. **Is it reachable only through mocks?** **No.** 8.4a, 8.4c and 8.4d reach it
   through realistic filesystem behavior injected at the OS `stat` boundary,
   with the created file present the whole time. 8.4a is precisely a
   directory-entry race between `iterdir()` and the per-file `stat`; 8.4c/8.4d
   are ordinary per-file metadata read failures. 8.7a reaches it through an
   external replacement.
3. **Does a successful `ExportResult` already prove completion?** Yes. The
   creator returns only after the exact final path was written and stat-ed
   (`export.py:254-268`), and 8.1/8.2 confirm the returned path, size and
   timestamp match the finished file exactly.
4. **Is the follow-up directory-wide list an authoritative confirmation step?**
   **No.** It is a secondary metadata lookup. 8.4 shows it can fail to find a
   file that exists; 8.6 shows it can fail entirely for an unrelated reason;
   8.7b/8.7c show it can describe a **foreign** object as if it were the created
   artifact. It provides no information the exact `ExportResult` does not
   already carry, and it can provide **wrong** information the result cannot.
5. **Can the fallback return an API reason that violates `CR-005`?** Yes —
   8.3, 8.4a, 8.4c, 8.4d, 8.5 and 8.7a all return the human manifest reason
   `before-update ../unsafe` where the contract requires `before_update_unsafe`.
6. **Can the fallback return `201` with a path to a file removed after the
   creator returned?** Yes — 8.5.
7. **Can a directory-list failure bypass the fallback and produce another
   result?** Yes — 8.6 and 8.4b both produce a generic `500` while the export
   sits complete on disk.
8. **Does any adjacent post-write failure occur before `create_json_export()`
   returns?** Yes — 8.8. It is a different path and is classified separately.
9. **Which findings belong to `CR-006`?** The create-response contract mismatch
   (8.3, 8.4a, 8.4c, 8.4d, 8.5, 8.7a) and the false total failure produced by
   the same redundant secondary scan (8.4b, 8.6). Both are consequences of one
   design choice: treating a directory-wide re-scan as the confirmation of an
   operation that already returned an exact result.
10. **Which findings are separate?** The creator's own post-write `stat`
    failure (8.8) and the `GET` list/status behavior under read failures (8.9).
    They are recorded below and are **not** resolved by this decision.

**Conclusion: the fallback is reachable in production-equivalent behavior, and
when it runs it returns an API reason that violates the accepted `CR-005`
contract.**

---

## Product classification

```text
PRODUCT DEFECT — CREATE-RESPONSE CONTRACT MISMATCH
Severity: MEDIUM
```

Severity is assigned **after** the evidence, not before it.

Confirmed impact:

- **inaccurate create-response metadata** — yes;
- **human/canonical reason mismatch** — yes, and user-visible: the frontend
  renders the API `reason` through `exportReasonLabelRaw`
  (`frontend/src/main.ts:1540`), which maps known slugs and otherwise renders
  the value **verbatim**, so `before-update ../unsafe` would appear in the
  «Причина» field of `/exports`;
- **false total failure** — yes (8.4b, 8.6): a complete export reported as a
  generic `500`;
- **duplicate-create risk** — yes, indirectly and only via the false total
  failure: a user told the operation failed will reasonably create a second
  export.

Explicitly **not** found:

- **data loss** — no application-caused loss. 8.5 deletes the file with an
  injected external actor after the application finished; that is not the
  application losing data;
- **overwrite** — no. `_unique_export_path` still never overwrites;
- **incorrect file bytes** — no. Every created export's bytes and manifest were
  correct in every scenario;
- **source database mutation** — no. 8.1 confirms the database is untouched;
- **privacy exposure** — no. The leaked value is the requester's own reason text
  returned to the requester in the same response; nothing crosses a boundary;
- **false durable-existence implication** — not as a defect. See *External
  disappearance* below; the decision defines what `201` claims.

---

## Decision

### Authoritative create result

```text
A successfully returned ExportResult is the authoritative result of the
create operation.
```

`POST /api/exports` must **not** re-scan the whole export directory to decide
whether the operation it just performed succeeded. A later directory-wide
listing cannot retroactively redefine whether creation happened, and the
evidence shows it can be wrong in both directions.

### Create-response metadata

The create response must be built **only** from the creator's exact result:

| Response field | Source |
|---|---|
| `filename` | `result.export_path.name` |
| `path` | `result.export_path` |
| `created_at` | `result.created_at` |
| `size_bytes` | `result.size_bytes` |
| `reason` | the **canonical reason parsed from the exact final filename**, through the same filename parsing contract used by list and status |
| `entity_counts` | `result.entity_counts` |

`ExportResult.reason` **must never** be used as the API `reason`. It is the
human manifest reason.

The canonical reason must come from the exact final filename through the same
parsing contract list and status use (`_parse_export_reason`), so that the
create response and every later read of the same file are derived identically.
This is safe: 8.2 confirms the numeric uniqueness suffix is stripped, and
`normalize_artifact_reason_segment` guarantees a canonical segment is never
digits-only, so a `reason_`-prefixed segment can never be mistaken for a
suffix.

### Human and canonical reasons

`CR-005` is **not reopened** and is preserved exactly:

- the export JSON manifest keeps the **normalized human reason**;
- the create, list and status API `reason` is the **canonical
  filename-derived segment**;
- the uniqueness suffix is never part of any reported reason;
- the export schema version is **unchanged**;
- no second persisted reason field, sidecar, metadata table or new API field is
  introduced;
- no existing export is renamed or rewritten.

### External disappearance

A file removed or replaced after the creator successfully returned does **not**
retroactively make the create operation false.

```text
201 Created means: the application completed creation at the operation boundary.
```

It does **not** guarantee that an external process can never remove or replace
the file afterwards. `GET /api/exports` and `GET /api/exports/status` remain the
truthful current-state surface, and 8.5 confirms they correctly stop listing a
removed export. Externally substituted content (8.7b, 8.7c) is **not**
equivalent to the application-created artifact, and the create response must not
describe it — another reason the response must come from the creator's result
rather than from a directory scan.

### Creator failure boundary

If `create_json_export` does not return a successful `ExportResult`, the
endpoint must **not** synthesize success from incomplete information. Post-write
failures that occur before a successful return — such as 8.8 — remain governed
by the operation's own explicit error contract and by the future `C3-II-B2`
verification and reconciliation contract. This decision does not change them.

### List and status boundary

`list_export_files` remains authoritative for the independent
`GET /api/exports` and `GET /api/exports/status` reads. It is **not** the
confirmation mechanism for a `POST` that has already returned an exact creation
result. The `GET` contract is **unchanged by this decision**; the behavior
recorded in 8.9 is noted as an adjacent finding, not decided here.

### `CR-009` compatibility

This decision is compatible with ADR 0013 and needs nothing beyond it:

- artifact-primary semantics — this decision is the same principle applied one
  layer earlier: the artifact, not a secondary read, is the result;
- the bounded ledger, exact final safe filename, pre-write preparation, direct
  artifact verification, exactly-once finalization, pending-audit warning, the
  AuditLog exclusion of filenames and reasons, no backfill, no migration beyond
  `0020`, and startup plus same-kind pre-create reconciliation are all
  unaffected;
- the additive `audit_status` / `audit_message` create fields and the additive
  `pending_audit_count` status field already authorized by `CR-009` remain the
  only response-shape additions, and they belong to `C3-II-B2`, not to this
  decision.

No new migration is required. No export response schema change beyond what
`CR-009` already authorizes is required.

---

## Rejected alternatives

1. **Continue scanning the whole directory after creation.** Rejected. The scan
   is redundant, can fail to find a file that exists (8.4), can fail entirely
   for an unrelated reason (8.6), and can describe a foreign object as the
   created artifact (8.7b, 8.7c). It makes a completed operation depend on an
   unrelated secondary read.
2. **Return the human manifest reason from the fallback.** Rejected. It violates
   the accepted `CR-005` API contract, and the same file then reports two
   different reasons through create and through list/status (8.3, 8.4).
3. **Fail the whole operation after a successful creator return.** Rejected. It
   contradicts ADR 0013's artifact-primary rule and is exactly the
   false-total-failure outcome the evidence identifies as a defect (8.4b, 8.6).
4. **Delete the export because response metadata lookup failed.** Rejected.
   Destroying a correct artifact because a secondary read failed is
   compensation the user never asked for, and ADR 0013 forbids it.
5. **Introduce a sidecar or metadata table for export reasons.** Rejected. The
   exact final filename already carries the canonical reason deterministically;
   `CR-005` explicitly refuses a sidecar or metadata table.
6. **Expose both the human and the canonical reason in new API fields.**
   Rejected. It reopens `CR-005`, doubles the contract surface, and puts a
   decision on the client that the backend already owns.
7. **Change the export manifest.** Rejected. The manifest's human reason is a
   settled `CR-005` contract and is not the problem.
8. **Change the export schema version.** Rejected. Nothing in the exported file
   changes, and bumping it would invalidate readers for no reason.
9. **Silently claim permanent file retention.** Rejected. The API cannot promise
   that an external process never touches the file. `201` describes the
   operation boundary, and the `GET` endpoints describe current state.
10. **Implement `C3-II-B2` in this decision PR.** Rejected. This is a
    product-decision and diagnostic PR with no production change; `C3-II-B2` is
    authorized only after it merges.

---

## Consequences

- `CR-006` moves from `needs evidence` to **`accepted`**, with a confirmed
  `MEDIUM` product defect and a decided contract.
- The correction is small and belongs to the endpoint: build the create response
  from the creator's exact result and derive the canonical reason from the exact
  final filename. It is **not implemented here**.
- The redundant directory re-scan disappears from the create path, which also
  removes the false-total-failure outcome in 8.4b and 8.6 for `POST`.
- `C3-II-B2 — JSON export AuditLog coverage` becomes authorized after this
  decision PR merges, and it carries the correction as part of its bounded
  create-path work, so the export create path is touched exactly once.
- `CR-005`, `R4`, `CR-009` and `C3-II-B1` are **not reopened**.
- `CR-004` remains `needs evidence`, so `C3-II-B3` stays blocked.
- C3 remains incomplete, C4 remains inactive, and **product release readiness is
  not claimed**.

---

## Adjacent findings — recorded, not decided here

These are **outside** `CR-006` and must not be used to broaden it.

1. **Creator's own post-write `stat` failure (8.8).** `export_path.stat()` at
   `backend/app/services/export.py:266` is outside the `try` that maps `OSError`
   to `ExportError`, so a failure there escapes as a raw `OSError`, the endpoint
   returns a generic `500`, and a complete export is left on disk that the
   caller was never told about. The fallback is unreachable on this path.
   `C3-II-B2` **must** carry a verification test for this path, because it is
   exactly the case its reconciliation contract exists for. Whether the
   endpoint's error mapping itself should change is **not decided here**.
2. **`GET` list and status under read failures (8.9).** A per-file `stat`
   failure silently omits a real export from `GET /api/exports` and makes
   `GET /api/exports/status` report `export_count: 0` with
   `latest_export: null`; a directory `iterdir` failure makes both endpoints
   return `500`. This is the same best-effort listing behavior `CR-005`
   accepted for legacy artifacts. **Their contract is unchanged by this
   decision** and any change needs its own evidence and decision.

---

## Non-goals

This decision does not:

- change any production code, migration, dependency or lockfile;
- implement `C3-II-B2`;
- reopen `CR-005`, `R4`, `CR-009` or `C3-II-B1`;
- resolve, reactivate or affect `CR-004`;
- change the export JSON manifest, its `reason`, or the export schema version;
- add a persisted reason column, sidecar or metadata table;
- add, rename or remove an export API field beyond what `CR-009` already
  authorizes for `C3-II-B2`;
- change `GET /api/exports` or `GET /api/exports/status` behavior;
- rename, rewrite, backfill, delete or audit any existing export;
- add an export download or delete endpoint;
- implement Restore, activate C4, or claim release readiness.
