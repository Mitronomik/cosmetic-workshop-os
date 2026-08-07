# Progress

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.

## Completed / merged baseline

- C1 — completed.
- C2 — completed.
- C3 — completed, merged, exact-head verified and hardened.
- CR-010 — accepted.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- PR #170 merge: `e6997281d2e0268ce54184d988c114bac71c35e2`.
- PR #171 merge: `76ab59216047222714a32f2793a789b3dc8df19a`.
- PR #172 / CR-011 merge: `998596560db6780a677bdec363d1fd19db30c1b6`.
- PR #173 sliced authorization merge: `aaedf2735660fb92eb627f7eeab327437d459b56`.
- PR #174 / C4-II-A1:
  - reviewed head `e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`;
  - merge `504e776508c940554b3ee8659a201af21db8303c`;
  - lifecycle + A1 smoke PASS;
  - targeted A1 17 passed;
  - C4-I Restore 514 passed, 34 deselected;
  - full backend + launcher 2415 passed;
  - audit P0=0 / P1=0 / P2=0.
- PR #175 A1 closure / A2 authorization:
  - reviewed head `b1a48d8f668fa984e3032f85c226f77e30d92e4e`;
  - merge `636645ece744752f6a753ae5a25a05297fd34e10`;
  - docs lifecycle gate PASS;
  - audit P0=0 / P1=0 / P2=0.
- Searchable history and five exact pre-compaction snapshots remain protected.

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

## A1 closed

Merged A1 remains non-destructive and the only candidate-preparation authority:
private validation scratch, C4-I intake/staging/validation reuse, retained
launcher-private `SourceIdentity` + SHA-256 proof, generation invalidation, no
durable Restore/safety-copy/AuditLog/working-DB mutation.

## A2 implemented in current changeset

Runtime:

- `launcher/restore/control_protocol.py` — safe DTOs + source-selection seam;
- `launcher/restore/control_session.py` — bootstrap/session/expiry/replay/worker coordinator;
- `launcher/restore/control_plane.py` — exact loopback concurrent HTTP boundary;
- `launcher/runtime.py` — control start after proved backend and close before backend stop;
- `launcher/restore/__init__.py` — A2 launcher-internal exports.

Verification assets:

- `launcher/tests/test_restore_control_session.py`;
- `launcher/tests/test_restore_control_plane.py`;
- `launcher/tests/test_restore_control_bootstrap_concurrency.py`;
- `launcher/tests/test_restore_control_rejection_order.py`;
- `launcher/tests/test_restore_control_runtime.py`;
- `scripts/smoke_restore_control_plane.py`.

Implemented contract includes exact loopback Host/Origin, atomic one-use bootstrap,
run-scoped bearer token, no-store/narrow CORS, 15s/60s liveness, concurrent
heartbeat/state/cancel, strict `command_seq`, A1 proof invalidation and generation-
gated worker publication.

Production A2 uses `picker_unavailable` and obtains no path. Production browser
navigation remains unchanged and carries no bootstrap/session material.

## Verification status

Implementation exists, but exact-head verification is pending. Do not mark A2
`DONE` until these actually pass on the published head:

- `git diff --check`;
- lifecycle checker;
- targeted A2 tests;
- A1 validation-session tests;
- C4-I Restore regression;
- full backend + launcher regression;
- exact-head direct-local-HTTP A2 smoke;
- independent audit P0=0 / P1=0 / P2=0.

## Still blocked

```text
A3 — blocked by A2 merge + exact-head gate + lifecycle update
A4 — blocked by A3 merge + exact-head gate
C4-II-B — not authorized
```

## Open product obligations

- finish/review/exact-head verify/merge A2;
- post-merge A2 lifecycle closure;
- then A3;
- then A4 + non-destructive browser E2E smoke;
- separately authorize C4-II-B;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
