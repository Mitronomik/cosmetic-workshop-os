# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
PR #183 — MERGED — B2 AUTHORIZED
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
C4-II-B2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #183 final reviewed authorization head `fa922f56c19a2dd33b6307ae0a197d476f91489b` merged as `4617b8c436eaa510fd545d863346595e2d808ea7`, authorizing B2 only.

## Closed B1 boundary

B1 preserves historical base `RestoreRequest` as selected-source-only and adds launcher-private `ProofBoundRestoreRequest` carrying `ExpectedSourceProof(SourceIdentity, SHA-256)`. C4-I re-proves that evidence against the exact same held source descriptor that it later stages, before `prepared`, safety copy or working-database mutation.

The B1/C4-I source-proof, staging and destructive engine implementations remain closed and byte-protected in the B2 lifecycle gate.

## B2 implementation changeset

B2 now implements the launcher-only destructive coordination seam authorized by PR #183:

- authenticated `POST /v1/restore/execute` with exact `request_id + command_seq + generation` body;
- one-shot transfer of the current launcher-private A1 retained path/proof into in-memory `RestoreExecutionIntent`;
- immediate invalidation of retained source authority;
- pathless `restoring`, `restore_completed`, `restore_failed` and `restore_blocked` launcher control states;
- no C4-I execution in HTTP/session workers;
- synchronous destructive execution on the main launcher runtime owner loop;
- existing C4-I remains the only component that stops/excludes the backend and performs B1 re-proof, staging, validation, safety copy, durable phases, replacement, verification and rollback;
- ordinary-backend restart handoff uses the existing `BackendProcessOwner` and canonical database path;
- the same control-plane instance/ephemeral port stays alive through the destructive interval;
- session expiry invalidates browser authentication but cannot cancel an accepted destructive Restore.

This changeset adds no browser confirmation or frontend support. B3 remains separately **NOT AUTHORIZED**, so product Restore is still incomplete.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine and mandatory `before_restore` recovery point;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-a-implementation-slices.md` — closed A1→A4 sequence;
- `docs/c4-ii-b-implementation-slices.md` — bounded B1→B3 sequence and B2 implementation contract.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package, API-first business architecture, safe historical data, recipe versions, first-class client recipes, lot/movement inventory, transactional production, safe import preview/confirmation, backup-before-migration and a human-readable non-technical UI.

Restore additionally preserves immutable selected source, launcher filesystem/destructive authority, pathless browser presentation, C4-I as the single destructive engine, exact-run authenticated control, one-shot command semantics, and no browser destructive action before separately authorized B3.
