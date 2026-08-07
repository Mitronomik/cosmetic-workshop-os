# Handoff

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted CR-011 architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
C4-II-A slice plan: `docs/c4-ii-a-implementation-slices.md`.

## Current lifecycle

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Last merged implementation — PR #174 / A1

```text
reviewed head — e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5
merge commit — 504e776508c940554b3ee8659a201af21db8303c
```

Exact-head gate:

- lifecycle checker PASS;
- A1 real-service smoke PASS;
- 17 targeted A1 tests passed;
- 514 existing C4-I Restore tests passed;
- 2415 backend+launcher tests passed;
- P0=0 / P1=0 / P2=0.

A1 is closed. It remains the only non-destructive candidate-preparation authority
and future A2 must integrate with it rather than reimplement staging/validation.

## Next runtime slice — A2

A2 may start only from updated `main` after this post-A1 closure merges.

Implement only:

- launcher-owned exact `127.0.0.1:<ephemeral>` control server;
- exact Host / configured Origin validation;
- one-use >=256-bit bootstrap + atomic consume;
- separate >=256-bit run-scoped session token;
- no-store control responses;
- 15s heartbeat / 60s authenticated inactivity expiry;
- concurrent servicing while long work runs elsewhere;
- >=128-bit request ID + monotonic `command_seq`;
- consume expected-next sequence before business preconditions;
- idempotent retry + stale/future replay rejection;
- A1 generation/cancel/invalidation integration;
- launcher lifecycle start/stop ownership;
- source-selection adapter boundary.

## Mandatory A2 seams

Production A2 adapter returns typed `picker_unavailable` and obtains no path.
Tests may inject a launcher-owned fake adapter directly.

Browser/request payload may not contain source path, file bytes, upload/blob,
handle/bookmark or equivalent filesystem authority.

Production browser launch URL remains unchanged. Do not append bootstrap fragment
until A4 provides the actual consumer/removal logic.

## Not A2

- real `/usr/bin/osascript` picker — A3;
- `/backups/restore` browser UI — A4;
- production browser bootstrap handoff — A4;
- destructive confirmation/execute — C4-II-B;
- ordinary FastAPI Restore mutation route;
- durable Restore state/safety copy/working-DB mutation/rollback/AuditLog;
- WebSocket/generic localhost command surface;
- new dependency/packaging work.

## Successor gates

A3 cannot start until A2 is independently exact-head verified, merged and
lifecycle-closed. A4 remains blocked by A3. C4-II-B remains separately not
authorized.
