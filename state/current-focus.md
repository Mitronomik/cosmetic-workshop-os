# Current Focus — C4-II-A2 exact-run launcher control plane

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
Slice plan: `docs/c4-ii-a-implementation-slices.md`.

## Merged baseline

```text
PR #173 merge — aaedf2735660fb92eb627f7eeab327437d459b56
PR #174 reviewed A1 head — e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5
PR #174 merge — 504e776508c940554b3ee8659a201af21db8303c
```

A1 exact-head gate: lifecycle PASS, A1 smoke PASS, 17 targeted tests, 514 C4-I
Restore regressions, 2415 backend+launcher tests, P0=0 / P1=0 / P2=0.

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

A2 runtime implementation begins only after the post-A1 lifecycle closure merges.

## Next implementation scope — A2

Implement only:

- launcher-owned HTTP control server on exact `127.0.0.1:<ephemeral>`;
- exact Host and configured frontend Origin checks;
- one-use >=256-bit bootstrap capability + atomic consume;
- separate >=256-bit run-scoped session token;
- `Cache-Control: no-store`;
- 15s heartbeat / 60s authenticated inactivity expiry;
- concurrent servicing while long work is in flight;
- >=128-bit request ID + monotonic `command_seq`;
- sequence consume-before-business-precondition semantics;
- idempotent same-request retry + stale/future replay rejection;
- A1 generation/cancel/invalidation integration;
- launcher lifecycle start/stop ownership;
- launcher-owned source-selection adapter boundary.

## Hard seams

Production A2 source-selection adapter returns typed `picker_unavailable` and
obtains no path. Tests may inject a launcher-owned fake adapter directly.

The browser may never send `path`, `source_path`, file bytes, upload/blob,
bookmark/handle or other filesystem authority.

Production browser navigation remains unchanged until A4. A2 does not append a
bootstrap fragment to the actual product browser URL; direct local authenticated
HTTP is used for A2 exact-head smoke.

## Forbidden in A2

- real `/usr/bin/osascript` picker — A3;
- `/backups/restore` frontend screen — A4;
- production browser bootstrap-fragment handoff — A4;
- destructive confirmation/execute — C4-II-B;
- ordinary FastAPI Restore mutation route;
- durable Restore operation/phase or `before_restore` safety copy;
- working-DB replacement/migration, rollback/recovery, Restore AuditLog;
- WebSocket/generic command server;
- new dependency or packaging implementation.

## Successor

A3 remains blocked until A2 is exact-head verified, merged and lifecycle-closed.
C4-II-B remains separately not authorized.
