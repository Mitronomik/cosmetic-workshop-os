# C4-II-B implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-09`

This document slices `C4-II-B — destructive Restore confirmation and execution` without changing ADR 0016 or ADR 0018. Destructive Restore enters only through small independently reviewed PRs.

## Merged baseline

```text
PR #180 reviewed A4 head — 79c698ed76d478d608a25f4b95499ff519794228
PR #180 / A4 merge — e61d4e233c98d3c53e7749fe96ed0ee630610372
PR #181 reviewed B1-authorization head — d2549cd9be2b60c5aee2479050e05a6ad8530c6c
PR #181 / B1-authorization merge — beae1407af270ad1c800c308ea7907750430eb1d
```

## Current slice status

```text
PR #181 — MERGED — B1 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

B2/B3 remain blocked until B1 is exact-head verified, merged, lifecycle-closed and separately followed by a B2 authorization decision.

## Why B1 exists

A1 retains launcher-private source path, `SourceIdentity`, full SHA-256, selection generation and compatibility. C4-I already owns source intake, held-descriptor staging, validation, `before_restore`, durable phases, replacement, verification and rollback. B1 therefore adds only the missing safety seam: bind the accepted A1 proof to the exact held source C4-I would later stage.

## B1 — Bind retained source proof into C4-I intake — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED

### Implementation

B1 adds:

- `ExpectedSourceProof` with only `SourceIdentity` + SHA-256 evidence;
- dedicated launcher-private `ProofBoundRestoreRequest(RestoreRequest)` carrying that non-path evidence;
- unchanged base `RestoreRequest` with exactly one caller-supplied field, `selected_source: Path`;
- `launcher/restore/source_proof.py` with `bind_expected_source_proof(...)`;
- fixed `RestoreFailure.SOURCE_CHANGED` user-safe guidance;
- focused isolated tests in `launcher/tests/test_restore_source_proof_binding.py`.

The engine sequence is:

```text
legacy RestoreRequest(selected_source=Path)
or
ProofBoundRestoreRequest(selected_source=Path, expected_source_proof=ExpectedSourceProof(...))
→ existing open_selected_source(selected_source, database_path)
→ HeldSource H
→ if expected proof exists:
     H.identity == expected identity
     → H.revalidate()
     → H.assert_still_self_contained()
     → H.digest()
     → exact byte-count + SHA-256 equality
     → H.revalidate()
     → H.assert_still_self_contained()
→ same HeldSource H
→ existing _execute_with_source(...)
→ existing stage_source(..., H)
```

The gate is before `_execute_with_source(...)`, so mismatch occurs before operation-directory creation, before `prepared`, before `before_restore`, and before any working-database mutation. If the source cannot even be reopened after an A1 expectation exists, that refusal also maps to `SOURCE_CHANGED` rather than leaking a technical/path-specific reason.

`launcher/restore/staging.py` is intentionally unchanged and remains baseline blob `3126d5b1e68e764c135739fad71915912481c493`. B1 does not create a second intake, staging or validation algorithm.

### Compatibility requirement

The historical C4-I base request invariant remains true: `RestoreRequest.__dataclass_fields__` contains only `selected_source`. Existing C4-I callers continue to construct that type and retain current behavior. Only the future trusted launcher coordinator that owns current retained A1 evidence may construct `ProofBoundRestoreRequest`; the extra proof contains no filesystem path and grants no authority by itself.

B1 is therefore an additive safety gate without widening the base C4-I caller-supplied path surface.

### B1 hard prohibitions

B1 does not:

- add/change browser routes, buttons, confirmation or frontend modules;
- add a control-plane HTTP command or broaden A2 vocabulary;
- introduce a user-facing call to `execute_restore(...)`;
- create a second Restore engine, staging algorithm or validation algorithm;
- create a durable Restore record/phase merely to compare proof;
- create a safety copy merely to compare proof;
- change replacement, migration, rollback/recovery or Restore AuditLog semantics;
- persist the A1 absolute path/proof/token;
- weaken source immutability, sidecar checks or held-descriptor staging;
- add any caller-supplied database, backup, Restore-directory or lock path.

### B1 exact-head tests required before closure

- exact A1 identity + digest match allows existing C4-I flow;
- proof binder and `stage_source` receive the same `HeldSource` object and fd;
- same path / different inode is refused before `prepared`;
- same inode/size with changed bytes is refused by full digest proof;
- late sidecar and symlink substitution are refused;
- digest byte-count mismatch is refused;
- mismatch creates no operation record, safety copy or working-DB mutation;
- selected source remains unchanged;
- `SOURCE_CHANGED` result contains no path/SQL/internal detail;
- base `RestoreRequest` remains selected-source-only;
- legacy C4-I behavior remains green;
- closed A1/A2/A3/A4 and C4-I regressions remain green;
- an **external**, exact-head, isolated smoke runner demonstrates that a changed source cannot cross B1. PR-specific smoke code must not be committed into this functional PR.

## B2 — Launcher destructive coordinator/control command — PLANNED — NOT AUTHORIZED

Future B2 will decide the exact launcher/session command that consumes the current accepted generation, constructs `ExpectedSourceProof` from the current A1 retained proof, constructs `ProofBoundRestoreRequest`, transitions from ordinary-running backend into existing C4-I `execute_restore(...)`, and invalidates stale browser/session authority around that transition.

B2 must reuse C4-I. It may not duplicate safety-copy, replacement, phase, verification or rollback logic. Exact command replay, one-shot confirmation semantics, control-plane lifetime while backend is stopped/restarted and result handoff must be specified in the B1 closure PR before B2 is authorized.

## B3 — Browser explicit destructive confirmation — PLANNED — NOT AUTHORIZED

B3 remains blocked until B2 is merged and exact-head verified. Browser state, filename, token possession and prior A4 acceptance are never destructive authority.

## Successor discipline

Each B slice is a separate PR with exact changed-path review, tests, smoke and independent P0/P1/P2 audit. B1 merge does not authorize B2. B2 merge does not authorize B3. C4-II-C and C4-III remain separately blocked.
