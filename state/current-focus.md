# Current Focus — C4-II-A4 browser Restore session UX

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted architecture: ADR 0018.

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

## A3 closure evidence

Reviewed head `b0de148032d9b3d2f9912298897f8649c9b1692b` merged as `9d95b0c39c4abd05d5a574c6cd8574b8e457f36b`.

Accepted gate: A3 14, A2 28, A1 17, C4-I 514, full 2457, native-picker smoke PASS, lifecycle PASS, clean exact heads, audit P0=0 / P1=0 / P2=0.

## Current implementation window — A4

Implement only the browser presentation/session slice:

- nested route `/backups/restore` and entry from `/backups`;
- launcher handoff through the URL fragment defined by ADR 0018;
- SPA consumes the one-use bootstrap capability during ordinary startup and removes the fragment immediately;
- only run-scoped control descriptors are retained in `sessionStorage`, never `localStorage`;
- reload uses `GET /v1/state`;
- invalid launcher session clears stale descriptors;
- 15-second heartbeat lifecycle;
- select/cancel/reselect use existing A2 commands with random request IDs and monotonic `command_seq`;
- typed safe UX backed by A2/A3/A1;
- exact-head non-destructive browser/macOS smoke.

## Hard seams

Browser never owns filesystem path/file authority and has no file-input fallback.

Bootstrap/session capability never enters query parameters, backend business API, logs or persistent storage.

A4 remains non-destructive: no execute/confirm, no durable Restore phase, no `before_restore`, no DB replacement/migration, no rollback/recovery mutation and no Restore AuditLog.

C4-II-B remains separately not authorized.