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
- PR #173 / C4-II-A sliced authorization merge:
  `aaedf2735660fb92eb627f7eeab327437d459b56`.
- PR #174 / C4-II-A1:
  - reviewed head `e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`;
  - merge `504e776508c940554b3ee8659a201af21db8303c`;
  - `git diff --check` PASS;
  - lifecycle checker PASS;
  - exact-head real-service smoke PASS;
  - targeted A1 tests 17 passed;
  - existing C4-I Restore regression 514 passed, 34 deselected;
  - full backend + launcher regression 2415 passed;
  - exact-head audit P0=0 / P1=0 / P2=0.
- Searchable history and five exact pre-compaction snapshots remain protected.

## Current lifecycle

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## A1 closed

Merged A1 runtime remains intentionally non-destructive:

- private system-temp validation scratch;
- A1 candidate-preparation service;
- direct C4-I intake/staging/validation reuse;
- retained launcher-private path + `SourceIdentity` + SHA-256 proof;
- generation/cancel/reselection invalidation;
- no durable Restore operation/safety copy/AuditLog/working-DB mutation.

## A2 authorized next

After this lifecycle closure merges, A2 may implement only the exact-run
launcher-owned loopback control/session layer. Production A2 still uses typed
`picker_unavailable`; no real picker and no production browser fragment handoff.

A2 must preserve:

- exact loopback-only ephemeral bind;
- exact Host/Origin;
- one-use bootstrap/session security;
- no-store responses;
- 15s heartbeat / 60s inactivity expiry;
- concurrent serviceability;
- request-ID/`command_seq` replay discipline;
- A1 generation/cancel integration;
- no browser path/file authority.

## Still blocked

```text
A3 — blocked by A2 merge + exact-head gate
A4 — blocked by A3 merge + exact-head gate
C4-II-B — not authorized
```

## Open product obligations

- merge post-A1 lifecycle closure;
- implement/review/exact-head verify/merge A2;
- then A3;
- then A4 + non-destructive browser E2E smoke;
- separately authorize C4-II-B;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
