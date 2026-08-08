# Handoff

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted CR-011 architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
C4-II-A slice plan: `docs/c4-ii-a-implementation-slices.md`.

## Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Last merged implementation — PR #176 / A2

```text
reviewed head — 681cb4050bec082db6b637285590e232880af739
merge commit — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
```

Final A2 gate: lifecycle PASS, stale-A1-authority race 2/2, A2 targeted 28/28,
A1 17/17, C4-I Restore 514/514, full backend+launcher 2443/2443, exact-head
control-plane smoke PASS, P0=0 / P1=0 / P2=0.

## Closed A2 contract

A2 owns the exact-run launcher control/session layer and remains unchanged through
A3 except for its production source-selection adapter seam:

- exact loopback ephemeral HTTP;
- exact Host/configured Origin;
- atomic one-use bootstrap + run-scoped token;
- no-store/narrow CORS/no cookie authority;
- 15s heartbeat / 60s inactivity expiry;
- strict monotonic `command_seq` + idempotent same-request retry;
- one long-work owner with responsive heartbeat/state/cancel;
- A1 proof invalidation and stale A2→A1 begin-race hardening;
- backend→control→ordinary-browser and control→backend lifecycle ordering.

## Current work — A3 native picker

Implement only the ADR 0018 native source-selection adapter:

- owned short-lived `/usr/bin/osascript` child;
- Standard Additions `choose file`;
- fixed AppleScript, no user-controlled interpolation;
- no `shell=True`, no `System Events`;
- typed ordinary user cancellation;
- selected absolute POSIX path only in launcher memory;
- cancel/expiry owns child termination and quiescence;
- integrate only through existing A2 `SourceSelectionAdapter` into merged A1;
- no new dependency.

## Not A3

- browser `path`, `source_path`, upload/blob/file bytes, bookmark/handle;
- `/backups/restore` frontend screen;
- production `#cw-control` bootstrap-fragment handoff;
- destructive confirmation/execute;
- ordinary FastAPI Restore mutation route;
- durable Restore state/safety copy/working-DB mutation/rollback/AuditLog;
- WebSocket/generic localhost command surface;
- packaging/cloud sync/OCR/multiuser/advanced analytics.

## Verification required

A3 must pass targeted native-picker/process/cancel tests, A2/A1/C4-I
regressions, full backend+launcher suite, exact-head A3 integration smoke, clean
status/head and independent exact-head audit at P0=0 / P1=0 / P2=0.

## Successor gates

A4 cannot start until A3 is independently exact-head verified, merged and
lifecycle-closed. C4-II-B remains separately not authorized.
