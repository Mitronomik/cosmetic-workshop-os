# Handoff

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted CR-011 architecture: ADR 0018.

## Current lifecycle

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Last merged implementation — PR #178 / A3

```text
reviewed head — b0de148032d9b3d2f9912298897f8649c9b1692b
merge commit — 9d95b0c39c4abd05d5a574c6cd8574b8e457f36b
```

Final accepted A3 evidence: A3 14, A2 28, A1 17, C4-I 514, full 2457, native-picker smoke PASS, lifecycle PASS, clean exact head and P0=0 / P1=0 / P2=0.

## Closed A3 contract

- `MacOSNativeSourceSelectionAdapter`;
- exact `/usr/bin/osascript`;
- fixed Standard Additions `choose file`;
- `shell=False`, no `System Events`, no user script interpolation;
- typed ordinary Cancel;
- absolute selected path only inside launcher;
- cancel/expiry/close terminate and reap owned picker child;
- A2 source selection → A1/C4-I validation only.

## Current work — A4 browser presentation/session

Implement only:

- `/backups/restore` route and human-readable entry from `/backups`;
- one-use launcher bootstrap transported only in URL fragment;
- SPA bootstrap consumption during ordinary startup, then immediate fragment removal;
- run-scoped descriptors in `sessionStorage` only;
- authenticated exact-origin control client;
- reload via `GET /v1/state`;
- stale descriptor cleanup on invalid token/run mismatch;
- 15s heartbeat lifecycle;
- select/cancel/reselect with secure request IDs and monotonic `command_seq`;
- typed nontechnical states and missing-session open/restart guidance;
- exact-head non-destructive E2E browser/macOS smoke.

## Not A4

- browser path/file/upload/bookmark authority or file-input fallback;
- query-token transport or `localStorage` token;
- ordinary FastAPI Restore mutation route;
- destructive confirmation/execute;
- durable Restore state, `before_restore` safety copy, DB replacement/migration, rollback/recovery mutation or Restore AuditLog;
- C4-II-B.

## Verification required

A4 requires targeted frontend/bootstrap/session/route tests, relevant launcher regressions, A3/A2/A1/C4-I preservation, exact-head real non-destructive browser smoke, clean status/head and independent P0=0 / P1=0 / P2=0 audit before merge.