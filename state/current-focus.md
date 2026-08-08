# Current Focus — C4-II-A3 native macOS picker

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
Slice plan: `docs/c4-ii-a-implementation-slices.md`.

## Merged baseline

```text
PR #176 reviewed A2 head — 681cb4050bec082db6b637285590e232880af739
PR #176 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
PR #177 reviewed closure head — d767b957cb3debae584709f2bbadafebd8dd6a9e
PR #177 merge — e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263
```

A2 final gate: race 2, A2 28, A1 17, C4-I 514, full 2443, smoke PASS,
audit P0=0 / P1=0 / P2=0. PR #177 lifecycle gate/audit also passed 0/0/0.

## Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
PR #177 — MERGED — A2 CLOSED / A3 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Current implementation — A3

Implemented only:

- `launcher/restore/macos_picker.py` native adapter;
- exact `/usr/bin/osascript` + fixed Standard Additions `choose file` script;
- `shell=False`, no `System Events`, no user-controlled interpolation;
- typed GUI Cancel using AppleScript error `-128` sentinel;
- launcher-private absolute POSIX result only;
- cancel-event polling and owned terminate/reap + kill fallback;
- production-only injection from `runtime.start_restore_control_plane()`;
- existing closed A2 unavailable default retained for direct/test construction;
- path passed only into merged A1 candidate preparation;
- no dependency.

Verification assets:

- `launcher/tests/test_restore_native_picker.py`;
- `launcher/tests/test_restore_native_picker_session.py`;
- `launcher/tests/test_restore_native_picker_runtime.py`;
- `scripts/smoke_restore_native_picker.py`.

## Hard seams

Browser/control requests remain pathless. Production browser navigation remains
unchanged: no `#cw-control`, control port, bootstrap capability or session token.
A4 owns the first browser handoff and `/backups/restore`.

A3 is non-destructive. C4-II-B remains separately not authorized.

## Forbidden in A3

- frontend Restore screen or browser path fallback;
- production browser bootstrap-fragment handoff;
- destructive confirmation/execute or `execute_restore(...)`;
- durable Restore state, `before_restore` safety copy, DB replacement/migration,
  rollback/recovery mutation or Restore AuditLog;
- ordinary FastAPI Restore mutation route;
- WebSocket/generic launcher command server;
- dependency/packaging work.

## Verification still required

No PASS is claimed until the final exact A3 head passes lifecycle/diff checks,
targeted A3 tests, closed A2/A1/C4-I regressions, full backend+launcher suite,
exact-head native-picker smoke, clean status/head and independent audit at
P0=0 / P1=0 / P2=0.
