# Current Focus — C4-II-A2 exact-run launcher control plane

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
Slice plan: `docs/c4-ii-a-implementation-slices.md`.

## Merged baseline

```text
PR #174 reviewed A1 head — e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5
PR #174 merge — 504e776508c940554b3ee8659a201af21db8303c
PR #175 reviewed closure head — b1a48d8f668fa984e3032f85c226f77e30d92e4e
PR #175 merge — 636645ece744752f6a753ae5a25a05297fd34e10
```

A1 exact-head gate: lifecycle PASS, A1 smoke PASS, 17 targeted tests, 514 C4-I
Restore regressions, 2415 backend+launcher tests, P0=0 / P1=0 / P2=0.

## Current lifecycle

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
PR #175 — MERGED — A1 CLOSED / A2 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Current implementation — A2

Implemented only:

- `control_protocol.py` typed state and source-selection seam;
- `control_session.py` bootstrap/session/liveness/replay/generation coordinator;
- `control_plane.py` exact loopback stdlib HTTP boundary;
- exact `127.0.0.1:<ephemeral>`, Host and configured Origin;
- one-use bootstrap + separate run session token;
- no wildcard CORS/cookie authority and no-store state;
- 15s heartbeat / 60s authenticated inactivity expiry;
- concurrent HTTP while one launcher-owned worker owns long work;
- >=128-bit request-ID namespace + monotonic `command_seq`;
- expected-next sequence consumed before business preconditions;
- idempotent retry and conflict/stale/future rejection;
- A1 proof/generation invalidation on reselect/cancel/expiry/close;
- runtime order backend proof → control start → ordinary browser and
  control close → backend stop;
- direct-local-HTTP exact-head smoke harness.

## Hard seams

Production A2 uses `UnavailableSourceSelectionAdapter`, returns typed
`picker_unavailable` and obtains no path. Tests/smoke may inject a launcher-owned
fake adapter directly.

Browser/control requests cannot send `path`, `source_path`, file bytes,
upload/blob, bookmark/handle or other filesystem authority.

Production browser navigation remains unchanged: no `#cw-control`, control port,
bootstrap capability or session token is appended. A4 owns first browser handoff.

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

## Verification still required

No PASS is claimed until the exact published A2 head passes:

```text
git diff --check
python3 scripts/check_documentation_lifecycle.py
targeted A2 tests
A1 validation-session tests
existing C4-I Restore regressions
python3 -m pytest backend/app/tests launcher/tests
python3 scripts/smoke_restore_control_plane.py --expected-head <HEAD>
independent exact-head audit
```

Gate: P0=0 / P1=0 / P2=0.

## Successor

A3 remains blocked until A2 is exact-head verified, merged and lifecycle-closed.
C4-II-B remains separately not authorized.
