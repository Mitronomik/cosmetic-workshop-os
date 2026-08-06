# Current focus — CR-011 decision gate

Updated: `2026-08-06`

This file is the compact current short-horizon source of truth.

Detailed C4-I implementation and audit history:
[`docs/history/c4-i-implementation-and-audit-history.md`](../docs/history/c4-i-implementation-and-audit-history.md).

Current decision:
[`docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`](../docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md).

## Current lifecycle

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED

C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
— PR #170
— final reviewed head ac95e2990efa979b3ded6cb48f91ddd0750aa7c8
— merge commit e6997281d2e0268ce54184d988c114bac71c35e2

CR-011 — Launcher Restore interaction and validation-session boundary
— AUTHORIZED — DECISION ONLY — NOT DECIDED

C4-II-A — Launcher Restore source selection and validation presentation
— PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED

C4-II-B — Explicit confirmation and Restore execution
— PLANNED — NOT AUTHORIZED

C4-II-C — Completion, rollback and support-assisted outcome UX
— PLANNED — NOT AUTHORIZED

C4-III — Restore end-to-end verification and lifecycle closure
— PLANNED — NOT AUTHORIZED

C4 — ACTIVE
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## Only authorized next task

```text
CR-011 — Decide the launcher Restore interaction and validation-session boundary.
Decision-only. No runtime implementation is authorized.
```

CR-011 must choose one concrete architecture for:

- the location and owning process of the user-facing Restore screen;
- the process that opens the native macOS file picker;
- the exact command path between any browser action and the launcher;
- local-run authentication, origin, token, replay, stale-session, and duplicate
  action protection;
- path privacy and whether an absolute source path ever leaves the launcher;
- backend lifecycle during selection and validation;
- allowed dependencies and packaging implications;
- launcher-owned cancellation, reselection, cleanup, and interrupted-session
  recovery;
- exact-head smoke for the chosen architecture.

The decision must also preserve one non-destructive launcher-owned candidate
preparation boundary. Conceptually:

```text
prepare_restore_candidate(...)
```

It must not call `execute_restore(...)`, create a durable Restore operation
record, enter a Restore phase, create a `before_restore` safety copy, mutate the
working database, migrate the working database, perform rollback, or write a
Restore AuditLog event.

## Blocked until CR-011 is accepted

No agent may implement:

- a native picker;
- launcher IPC or WebSocket communication;
- a loopback control endpoint;
- a FastAPI Restore endpoint;
- SPA-owned filesystem access;
- browser upload as the authoritative Restore source;
- frontend Restore controls;
- a validation-session Python service;
- packaging changes for Restore;
- C4-II-A, C4-II-B, C4-II-C, or C4-III runtime work.

The ordinary browser UI currently has no accepted launcher command channel.
Implementation by assumption is prohibited.

## Preserved Restore invariants

- exactly twelve durable phases;
- `phase` is the sole authoritative lifecycle field;
- accepted transition graph and recovery matrix unchanged;
- immutable selected source;
- verified `before_restore` safety copy before future replacement;
- launcher ownership of destructive Restore;
- no ordinary backend or SPA Restore mutation;
- no Restore AuditLog event;
- browser opens into the ordinary workspace only after durable `completed`;
- user-facing Restore remains `NOT IMPLEMENTED`.