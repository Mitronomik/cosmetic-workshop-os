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
  - A1 17 passed; C4-I 514 passed; full 2415 passed;
  - audit P0=0 / P1=0 / P2=0.
- PR #175 A1 closure / A2 authorization:
  - reviewed head `b1a48d8f668fa984e3032f85c226f77e30d92e4e`;
  - merge `636645ece744752f6a753ae5a25a05297fd34e10`;
  - docs lifecycle gate PASS; audit P0=0 / P1=0 / P2=0.
- PR #176 / C4-II-A2:
  - reviewed head `681cb4050bec082db6b637285590e232880af739`;
  - merge `90a14dd9a11b83bc31a40e1d3fb9523f41772b88`;
  - lifecycle PASS;
  - stale-A1-authority race 2 passed;
  - all A2 targeted 28 passed;
  - A1 17 passed;
  - C4-I Restore 514 passed, 62 deselected;
  - full backend + launcher 2443 passed;
  - exact-head A2 smoke PASS;
  - audit P0=0 / P1=0 / P2=0.
- Searchable history and five exact pre-compaction snapshots remain protected.

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

## Closed A1/A2 boundaries

A1 remains the only candidate-preparation authority. A2 remains the exact-run
loopback control/session authority with exact Host/configured Origin, atomic
bootstrap, run token, no-store/narrow CORS, 15s/60s liveness, strict
`command_seq`, concurrent heartbeat/state/cancel and stale A2→A1 proof-race
hardening.

Production source selection is still `picker_unavailable`; browser/control
requests carry no filesystem path/file authority and product browser navigation
carries no control bootstrap/session material.

## Authorized next — A3

A3 may implement only the launcher-owned native macOS picker:

- `/usr/bin/osascript`;
- Standard Additions `choose file`;
- fixed non-user-interpolated script;
- no `shell=True`, no `System Events`;
- typed cancel;
- launcher-private absolute POSIX path;
- owned child terminate/wait on cancel/expiry;
- existing A2 adapter → merged A1 validation;
- no new dependency.

## Still blocked

```text
A4 — blocked by A3 merge + exact-head gate + lifecycle update
C4-II-B — not authorized
```

## Open product obligations

- implement/review/exact-head verify/merge A3;
- post-merge A3 lifecycle closure;
- then A4 + real non-destructive browser E2E flow;
- separately authorize C4-II-B;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
