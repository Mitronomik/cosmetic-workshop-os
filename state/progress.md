# Progress

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`.

## Completed / merged baseline

- C1/C2 completed; C3 completed, merged, exact-head verified and hardened.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- PR #174 / A1: reviewed `e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`, merge `504e776508c940554b3ee8659a201af21db8303c`, 17 A1 / 514 C4-I / 2415 full / smoke / audit 0/0/0.
- PR #176 / A2: reviewed `681cb4050bec082db6b637285590e232880af739`, merge `90a14dd9a11b83bc31a40e1d3fb9523f41772b88`, race 2 / A2 28 / A1 17 / C4-I 514 / full 2443 / smoke / audit 0/0/0.
- PR #177 A2 closure / A3 authorization: reviewed `d767b957cb3debae584709f2bbadafebd8dd6a9e`, merge `e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263`, docs lifecycle gate PASS, 12 changed docs/state/checker paths, audit 0/0/0.
- Searchable history and five exact pre-compaction snapshots remain protected.

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

## Closed A1/A2 boundaries

A1 remains the only candidate-preparation authority. A2 remains the exact-run
loopback control/session authority with exact Host/Origin, bootstrap/session,
15s/60s liveness, strict command ordering, one worker and stale-proof hardening.

## A3 implemented in current changeset

Runtime:

- `launcher/restore/macos_picker.py` — native picker adapter;
- `launcher/runtime.py` — narrow production injection only;
- `launcher/restore/control_protocol.py` + `launcher/restore/__init__.py` — seam/docs/export alignment.

Contract:

- exact `/usr/bin/osascript`;
- fixed `use scripting additions` / `choose file` script;
- `shell=False`, no `System Events`, no user text interpolation;
- error `-128` → typed user cancellation;
- selected absolute POSIX path launcher-private;
- cancel/expiry child terminate/reap with kill fallback;
- non-macOS/missing helper → unavailable;
- technical picker failures remain safe through A2;
- real A2 worker → A3 adapter → real A1 validation;
- no new dependency.

Verification assets:

- native-picker unit/process tests;
- cancel/expiry session integration tests;
- production runtime injection test;
- exact-head native-picker smoke.

## Verification status

Implementation exists, but exact-head verification is pending. Do not mark A3
`DONE` until lifecycle/diff, A3 tests, closed A2/A1/C4-I regressions, full suite,
exact-head smoke and independent audit pass on the final published head.

## Still blocked

```text
A4 — blocked by A3 merge + exact-head gate + lifecycle update
C4-II-B — not authorized
```

## Open product obligations

- exact-head verify/review/merge A3;
- post-merge A3 lifecycle closure;
- then A4 + real non-destructive browser E2E flow;
- separately authorize C4-II-B;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
