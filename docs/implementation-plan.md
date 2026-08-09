# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-09`

## Current lifecycle

```text
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Merged baseline

```text
PR #182 reviewed B1 head — 27726058af4f373ab65225ecf4d1a945f1c53067
PR #182 merge/new main — 5e13b50f1918dacbf8d54066c9156942a9adb895
```

B1 closure evidence: full backend+launcher `2480/2480`, external exact-head substitution smoke PASS, independent `P0=0/P1=0/P2=0`.

## Current implementation window — C4-II-B2

Implement only the launcher destructive coordinator/control command defined in `docs/c4-ii-b-implementation-slices.md`.

Required flow:

```text
POST /v1/restore/execute
  exact body: request_id + command_seq + generation
→ authenticated/session/replay checks
→ consume exactly-next sequence before business preconditions
→ require current accepted generation + current retained A1 proof
→ atomically invalidate retained source authority
→ queue exactly one launcher-private RestoreExecutionIntent
→ return safe `restoring` reply; HTTP thread performs no C4-I work
→ launcher main runtime consumes intent
→ ProofBoundRestoreRequest(retained source path, ExpectedSourceProof)
→ existing execute_restore(..., LauncherLifecycleContext)
→ existing C4-I owns backend stop/exclusion + all destructive semantics
→ main runtime performs ordinary-backend restart handoff when safe
→ publish one safe final control state
```

## Mandatory B2 seams

- `/v1/restore/execute` is the only new destructive control command.
- Browser body carries no path, proof, digest, operation ID or target path.
- `generation` is a stale-view guard only; source authority remains launcher-private retained proof.
- Command sequence/retry rules remain ADR 0018 exact-next and idempotent.
- The accepted source authority is one-shot and invalidated before destructive execution begins.
- HTTP/session workers never call `execute_restore(...)`.
- C4-I remains the only destructive Restore engine.
- The same control plane stays alive while ordinary backend is intentionally stopped/restarted.
- Heartbeat/state remain responsive during `restoring`.
- Cancel/session expiry cannot cancel destructive C4-I after intent acceptance.
- Launcher main runtime, not one stale initial `process.wait()`, owns backend lifetime across the stop/restart transition.
- Backend restart uses the canonical `context.database_path` and `BackendProcessOwner`; no process discovery by port/name/PID pattern.
- If C4-I does not permit normal startup, no ordinary backend starts.
- Backend restart failure does not rewrite or roll back the C4-I result.
- B2 may add safe control states `restoring`, `restore_completed`, `restore_failed`, `restore_blocked`; frontend remains unchanged until B3/C.
- B3 remains not authorized.

## Protected implementation boundaries

B2 should not modify these merged B1/C4-I files:

```text
launcher/restore/contracts.py
launcher/restore/engine.py
launcher/restore/source_proof.py
launcher/restore/staging.py
launcher/restore/validation_session.py
frontend/**
backend/**
migrations/**
```

A new focused launcher execution-coordinator module is allowed. A tiny observation accessor on `BackendProcessOwner` is allowed only if needed for the main runtime loop; ownership/stopping semantics are not.

## Required B2 proof before merge

1. exact endpoint schema and Host/Origin/auth/replay tests;
2. one-shot accepted-generation/proof transfer tests;
3. duplicate/retry executes at most once;
4. stale generation/missing proof/in-progress commands queue nothing;
5. HTTP worker never calls C4-I;
6. main runtime invokes existing C4-I exactly once with `ProofBoundRestoreRequest` built only from retained launcher proof;
7. control plane remains responsive on the same port while backend is stopped;
8. session expiry/cancel does not cancel destructive execution;
9. completed/failed/blocked result mapping is safe and pathless;
10. ordinary backend restart uses exact owner/lock handshake and canonical database;
11. restart failure leaves C4-I truth unchanged and maintenance exclusion safe;
12. intentional Restore stop does not terminate launcher runtime or kill a restarted backend;
13. existing A1/A2/A3/A4/B1/C4-I regressions remain green;
14. frontend remains byte-identical;
15. full backend+launcher regression green;
16. external exact-head isolated process smoke proves command → stop → B1 re-proof → C4-I → restart/result handoff;
17. clean exact head/worktree;
18. independent `P0=0/P1=0/P2=0` audit.

## Forbidden scope

No B3 browser confirmation/UI, no `/v1/restore/confirm`, no ordinary FastAPI Restore mutation, no second Restore engine, no phase/recovery redesign, no Restore AuditLog change, no new dependency, no packaging redesign, no cloud sync/OCR/roles/multiuser/advanced analytics.

## Next action

Merge this B1-closure/B2-authorization docs PR after exact-head lifecycle review → implement B2 as one bounded Draft PR → exact-head tests + external smoke + independent audit → merge only when green → separate lifecycle closure before any B3 authorization.
