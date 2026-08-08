# Progress

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.

## Completed / merged baseline

- C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED.
- C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED.
- C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED.
- PR #177 closed A2 and authorized A3.
- PR #178 completed A3 at reviewed head `b0de148032d9b3d2f9912298897f8649c9b1692b`, merged as `9d95b0c39c4abd05d5a574c6cd8574b8e457f36b`.
- A3 accepted evidence: 14 A3, 28 A2, 17 A1, 514 C4-I, 2457 full backend+launcher, native-picker smoke PASS, lifecycle PASS and independent audit P0=0 / P1=0 / P2=0.
- Searchable history and five exact pre-compaction snapshots remain protected.

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

## Closed A1/A2/A3 boundaries

A1 remains candidate-preparation authority. A2 remains exact-run loopback/session authority. A3 remains exact `/usr/bin/osascript` launcher-owned picker with fixed `choose file`, typed cancel, launcher-private POSIX path and owned child quiescence.

## Authorized next — A4

A4 may implement only `/backups/restore`, entry from `/backups`, URL-fragment bootstrap handoff/consumption/removal, run-scoped `sessionStorage`, reload/state, heartbeat, select/cancel/reselect and safe non-destructive browser UX over the existing A2/A3/A1 chain.

## Still blocked

```text
C4-II-B — not authorized
```

No browser filesystem authority, destructive execute, safety copy, DB replacement/migration, rollback/recovery mutation or Restore AuditLog is authorized in A4.

## Open product obligations

- merge A3 closure / A4 authorization;
- implement/review/exact-head verify/merge A4;
- lifecycle-close A4;
- separately authorize C4-II-B;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.