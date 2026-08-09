# C4-II-B implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-09`

This document slices `C4-II-B — destructive Restore confirmation and execution` without changing ADR 0016 or ADR 0018. It exists because A4 is now merged and exact-head verified, but destructive Restore must still enter through small independently reviewed PRs.

## Merged baseline

```text
PR #179 / A4 authorization merge — 52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf
PR #180 reviewed A4 head — 79c698ed76d478d608a25f4b95499ff519794228
PR #180 / A4 merge — e61d4e233c98d3c53e7749fe96ed0ee630610372
```

PR #180 final evidence: lifecycle PASS; A4 launcher 15/15; A3 14/14; A2 29/29; A1 17/17; C4-I 514/514; full backend+launcher 2470/2470; frontend A4 16/16; backup regression 25/25; audit-log regression 92/92; A4 cross-layer smoke PASS; manual desktop/narrow/keyboard/native-picker UI smoke PASS; independent P0=0 / P1=0 / P2=0.

## Current slice status

```text
PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

Only **B1** is authorized by the A4-closure changeset. B2/B3 remain blocked until B1 is merged, exact-head verified, lifecycle-closed and separately authorized.

## Why B1 exists

A1 retains launcher-private proof of the backup the user actually validated:

```text
absolute source path
+ SourceIdentity
+ full SHA-256
+ selection generation
+ compatibility
```

C4-I `execute_restore(...)` already reopens the source, holds the descriptor, stages again, validates again, creates the mandatory `before_restore` safety copy, enters the durable phase machine, replaces the working database, verifies startup and rolls back when required.

Therefore C4-II-B must **not** build a second staging/validation/restore engine. The missing safety seam is binding the previously accepted A1 proof to the exact held source C4-I opens for destructive execution. Without that binding, a path could point at a different but otherwise valid backup between A4 validation/confirmation and C4-I intake.

## B1 — Bind retained source proof into C4-I intake — AUTHORIZED NEXT

### Goal

Add a reusable launcher-private expected-source proof gate at the C4-I intake boundary so the exact file accepted by A1 can later be required by destructive execution without trusting a path, filename, browser token or presentation state.

### Required behavior

B1 may add a focused internal expectation type/helper and an optional expected-source proof parameter at the existing C4-I engine intake seam. When an expectation is supplied, the engine must prove it against the **same `HeldSource` descriptor** opened by `open_selected_source(...)` before any Restore operation directory/record, safety copy or working-database mutation is created.

The gate must prove all of the following:

1. the held `SourceIdentity` equals the expected A1 identity;
2. `HeldSource.revalidate()` still succeeds;
3. `HeldSource.assert_still_self_contained()` still succeeds;
4. full SHA-256 is recomputed with `HeldSource.digest()` from the held descriptor, never by reopening the path;
5. the digest byte count equals the held identity size;
6. the digest equals the expected A1 SHA-256;
7. identity/self-containment are re-proved after the digest read before intake may continue.

A mismatch must fail closed **before `prepared` exists** with a fixed non-technical source-changed category/message. No filesystem path, SQL, migration ID, stack trace or database content may enter the user-safe result.

### Compatibility requirement

Existing C4-I internal callers/tests that do not supply an expected proof must remain behaviorally unchanged. B1 is an additive safety gate, not a rewrite of C4-I.

### B1 hard prohibitions

B1 must not:

- add or change any browser route, button, confirmation screen or frontend module;
- add a control-plane HTTP command or broaden A2 vocabulary;
- call `execute_restore(...)` from a new user-facing coordinator;
- create a new Restore engine, staging algorithm or validation algorithm;
- create a durable Restore record/phase merely to compare the proof;
- create a `before_restore` safety copy merely to compare the proof;
- replace/migrate the working database;
- add rollback/recovery behavior;
- write Restore AuditLog;
- persist the A1 absolute path/proof/token;
- weaken source immutability, sidecar checks or held-descriptor semantics.

B1 may modify the existing C4-I internal contracts/intake and focused tests only as required for the expectation gate. Any change to durable phase semantics, replacement semantics, safety-copy semantics or recovery matrix is out of scope and requires a new architecture decision.

### B1 required tests

At minimum prove:

- exact identity + digest match allows existing C4-I flow to continue unchanged;
- same path replaced with a different inode is refused before `prepared`;
- same inode/size but changed bytes is refused by digest proof;
- sidecar appearing after A1 validation is refused;
- symlink/path substitution is refused by existing intake/revalidation;
- expected digest length/count mismatch is refused;
- mismatch creates no operation record, no safety copy and no working-DB mutation;
- selected source remains byte-identical on success and refusal;
- legacy C4-I calls without an expectation retain current behavior;
- C4-I 514-test regression remains green or an intentional count increase is fully explained;
- A1/A2/A3/A4 closed-boundary regressions remain green;
- exact-head smoke demonstrates a changed source cannot cross the B1 gate.

## B2 — Launcher destructive coordinator/control command — PLANNED — NOT AUTHORIZED

Future B2 will decide and implement the exact launcher/session command that consumes the current accepted generation, requires B1 expected-source proof, transitions from ordinary-running backend to C4-I destructive execution, and invalidates stale browser/session authority around that transition.

B2 must reuse C4-I `execute_restore(...)`; it may not duplicate safety-copy, replacement, phase, verification or rollback logic. Exact command replay, one-shot confirmation semantics, control-plane lifetime while the backend is stopped/restarted, and failure/result handoff must be specified in the B1 closure PR before B2 is authorized.

## B3 — Browser explicit destructive confirmation — PLANNED — NOT AUTHORIZED

Future B3 may add the product confirmation UX required by ADR 0016 only after B2 is merged and exact-head verified. The confirmation must identify the already validated copy using safe presentation data, warn that current workshop data will be replaced, state that a safety copy is created first, state that the selected backup remains unchanged, state that the application will restart, and require an explicit destructive action.

Browser state, filename, token possession and prior A4 acceptance are never destructive authority. The launcher remains the sole authority for the current proof and for C4-I execution.

## Successor discipline

Each B slice is a separate PR with exact changed-path review, tests, smoke and independent P0/P1/P2 audit. B1 merge does not authorize B2. B2 merge does not authorize B3. C4-II-C and C4-III remain separately blocked.
