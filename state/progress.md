# Progress

Updated: `2026-08-07`

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
- PR #173 / C4-II-A sliced authorization:
  - reviewed head `9f5722c5dec695588596d45daa5588092ce7f080`;
  - merge `aaedf2735660fb92eb627f7eeab327437d459b56`;
  - documentation gate PASS;
  - authorization audit P0=0 / P1=0 / P2=0.
- Searchable history and five exact pre-compaction snapshots remain protected.

## Current lifecycle

```text
PR #173 — MERGED — C4-II-A SLICED AUTHORIZATION
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## A1 implemented in current changeset

Runtime:

- `launcher/restore/validation_scratch.py` — private system-temp validation
  namespace and owned-only cleanup;
- `launcher/restore/validation_session.py` — non-destructive candidate preparation,
  generation/cancel/reselection, typed results and retained launcher-private proof;
- `launcher/restore/__init__.py` — exposes the A1 typed internal service surface.

Verification assets:

- `launcher/tests/test_restore_validation_session.py` — current/older/newer,
  invalid source classes, immutability, no durable Restore/safety-copy/AuditLog/DB
  mutation, stale/cancel/reselection, cleanup and safe failure coverage;
- `scripts/smoke_restore_validation_session.py` — exact-head real-service smoke on
  temporary SQLite sources.

A1 reuses existing C4-I `open_selected_source(...)`, held-descriptor identity and
digest, `stage_source(...)` two-pass staging and `validate_staged_candidate(...)`.
No duplicate staging algorithm was introduced.

## Not implemented / still blocked

A1 contains no HTTP control plane, `command_seq`, browser bootstrap/session,
`/usr/bin/osascript`, frontend Restore UI or destructive action.

```text
A2 — blocked
A3 — blocked
A4 — blocked
C4-II-B — not authorized
```

## Verification status

Implementation exists, but exact-head verification is still pending. Do not mark
A1 `DONE` until these are actually run on the published head:

- `git diff --check`;
- documentation lifecycle checker;
- targeted A1 tests;
- C4-I Restore regression tests;
- full backend + launcher tests;
- exact-head A1 smoke;
- independent exact-head code/architecture audit;
- P0=0 / P1=0 / P2=0.

## Open product obligations

- close A1 exact-head gate and merge;
- post-merge A1 lifecycle closure;
- then A2, A3 and A4 sequentially;
- separately authorize C4-II-B;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
