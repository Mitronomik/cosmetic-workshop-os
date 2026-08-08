# Handoff

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted CR-011 architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
C4-II-A slice plan: `docs/c4-ii-a-implementation-slices.md`.

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

## Last merged lifecycle — PR #177

```text
reviewed head — d767b957cb3debae584709f2bbadafebd8dd6a9e
merge commit — e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263
```

PR #177 closed A2 after its 2 race / 28 A2 / 17 A1 / 514 C4-I / 2443
full / smoke / 0-0-0 gate and authorized only A3.

## Closed A2 contract

A2 remains unchanged except for production source-selection injection: exact
loopback/Host/Origin, atomic bootstrap, run token, no-store/narrow CORS,
15s/60s liveness, strict `command_seq`, one worker, responsive
heartbeat/state/cancel and stale A2→A1 proof-race hardening.

## Current work — A3 native picker

Implemented:

- `launcher/restore/macos_picker.py`;
- exact `/usr/bin/osascript` owned child;
- fixed Standard Additions `choose file` AppleScript;
- no shell/System Events/user interpolation;
- typed user cancellation through error `-128` sentinel;
- absolute POSIX result only in launcher memory;
- cancel-event polling, terminate/reap, kill fallback;
- non-macOS/missing helper → unavailable;
- production-only injection in `runtime.start_restore_control_plane()`;
- selected path only to merged A1;
- targeted A3 tests + exact-head smoke.

The default A2 `UnavailableSourceSelectionAdapter` remains for direct/test
construction, preserving the closed A2 test seam.

## Not A3

- browser `path`, `source_path`, file bytes, upload/blob, bookmark/handle;
- `/backups/restore` frontend screen;
- production `#cw-control` handoff;
- destructive confirmation/execute;
- ordinary FastAPI Restore mutation route;
- durable Restore state/safety copy/working-DB mutation/rollback/AuditLog;
- WebSocket/generic launcher command surface;
- new dependency/packaging work.

## Verification required

A3 still requires exact-head diff/lifecycle, targeted native-picker tests, closed
A2/A1/C4-I regressions, full backend+launcher suite, exact-head A3 smoke, clean
status/head and independent audit at P0=0 / P1=0 / P2=0.

## Successor gates

A4 cannot start until A3 is independently exact-head verified, merged and
lifecycle-closed. C4-II-B remains separately not authorized.
