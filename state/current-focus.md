# Current Focus — C4-II-A3 native macOS picker

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
PR #176 reviewed A2 head — 681cb4050bec082db6b637285590e232880af739
PR #176 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
```

A2 final gate: lifecycle PASS, stale-A1-authority race 2/2, all A2 28/28,
A1 17/17, C4-I Restore 514/514, full backend+launcher 2443/2443, exact-head
control-plane smoke PASS, audit P0=0 / P1=0 / P2=0.

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

## Current implementation window — A3

Implement only the launcher-owned native macOS picker behind the existing A2
`SourceSelectionAdapter` seam:

- exact `/usr/bin/osascript` owned child;
- Standard Additions `choose file`;
- fixed script; no user-controlled AppleScript interpolation;
- no `shell=True` and no `System Events`;
- typed picker cancellation;
- selected absolute POSIX path only in launcher memory;
- cancel/expiry owns child termination and quiescence;
- path flows only to merged A1 candidate preparation;
- no new dependency.

## Hard seams

Browser/control requests remain pathless: no `path`, `source_path`, file bytes,
upload/blob, bookmark/handle or equivalent filesystem authority.

Production browser navigation remains unchanged: no `#cw-control`, control port,
bootstrap capability or session token. A4 owns the first browser handoff and
`/backups/restore`.

A3 is non-destructive. C4-II-B remains separately not authorized.

## Forbidden in A3

- frontend Restore screen or browser path fallback;
- production browser bootstrap-fragment handoff;
- destructive confirmation/execute or `execute_restore(...)`;
- durable Restore state, `before_restore` safety copy, DB replacement/migration,
  rollback/recovery mutation or Restore AuditLog;
- ordinary FastAPI Restore mutation route;
- WebSocket/generic localhost command server;
- new dependency/packaging work;
- cloud sync/OCR/multiuser/advanced analytics.

## Verification required

A3 must pass targeted picker/process/cancel tests, A2/A1/C4-I regressions, full
backend+launcher suite, exact-head A3 integration smoke, clean status/head and
independent audit at P0=0 / P1=0 / P2=0 before merge.
