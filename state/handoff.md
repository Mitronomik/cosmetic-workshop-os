# Handoff

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted CR-011 architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
C4-II-A slice plan: `docs/c4-ii-a-implementation-slices.md`.

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

## Last merged implementation — PR #174 / A1

```text
reviewed head — e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5
merge commit — 504e776508c940554b3ee8659a201af21db8303c
```

A1 exact-head gate: lifecycle/smoke PASS, 17 targeted tests, 514 C4-I Restore
tests, 2415 backend+launcher tests, P0=0 / P1=0 / P2=0.

PR #175 then closed A1 lifecycle and authorized only A2:

```text
reviewed head — b1a48d8f668fa984e3032f85c226f77e30d92e4e
merge commit — 636645ece744752f6a753ae5a25a05297fd34e10
```

## Current work — A2 exact-run control plane

Implemented:

- exact `127.0.0.1:<ephemeral>` stdlib concurrent control server;
- exact Host and configured frontend Origin enforcement;
- one-use bootstrap capability, atomic consume and separate run-scoped session token;
- no wildcard CORS/cookie authority, no-store responses;
- 15s heartbeat / 60s authenticated inactivity expiry;
- one launcher-owned worker for long selection/validation;
- responsive heartbeat/state/cancel while worker runs;
- request ID + monotonic `command_seq` replay discipline;
- expected-next sequence consumed before business preconditions;
- A1 generation/proof invalidation and stale-worker publication guard;
- launcher runtime order: proved backend → control → ordinary browser;
- shutdown order: control/A1 quiescence → backend stop;
- direct-local-HTTP exact-head smoke harness.

The merged A1 service remains the only candidate-preparation authority; A2 calls
it after launcher-owned source selection and does not duplicate staging/validation.

## Mandatory A2 seams

Production source selection uses `UnavailableSourceSelectionAdapter`, returns
typed `picker_unavailable` and obtains no path. Tests/smoke may inject a
launcher-owned fake adapter directly.

Browser/request payload cannot contain `path`, `source_path`, file bytes,
upload/blob, bookmark/handle or equivalent filesystem authority.

Production browser URL remains unchanged: no `#cw-control`, control port,
bootstrap capability or session token until A4.

## Not A2

- real `/usr/bin/osascript` picker — A3;
- `/backups/restore` browser UI — A4;
- production browser bootstrap handoff — A4;
- destructive confirmation/execute — C4-II-B;
- ordinary FastAPI Restore mutation route;
- durable Restore state/safety copy/working-DB mutation/rollback/AuditLog;
- WebSocket/generic localhost command surface;
- new dependency/packaging work.

## Exact-head verification required

Still pending on the final published A2 head:

```text
git diff --check
python3 scripts/check_documentation_lifecycle.py
targeted A2 tests
A1 validation-session tests
existing C4-I Restore tests
python3 -m pytest backend/app/tests launcher/tests
python3 scripts/smoke_restore_control_plane.py --expected-head <HEAD>
clean status/head re-check
independent exact-head audit
```

Do not claim PASS or A2 `DONE` before the exact-head gate closes at
P0=0 / P1=0 / P2=0.

## Successor gates

A3 cannot start until A2 is independently exact-head verified, merged and
lifecycle-closed. A4 remains blocked by A3. C4-II-B remains separately not
authorized.
