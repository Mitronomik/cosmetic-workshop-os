# Progress

Updated: `2026-08-11`

## Completed / merged baseline

- C1/C2 completed; C3 completed, merged, exact-head verified and hardened.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- A1/A2/A3/A4 — merged and exact-head verified.
- B1 — merged and exact-head verified on PR #182.
- B2 — reviewed head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4`, merged as `266c50a77e5f353fa77701cb854629a99460667f`, exact-head verified and closed.
- B2 accepted evidence: focused 37 PASS; launcher 636; backend 1867; total 2503/2503; frontend Restore 16/16; anti-hang PASS; corrected external process smoke PASS; independent `P0=0/P1=0/P2=0`; final clean-head PASS.
- PR #185 reviewed B3 authorization head `f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c`, merged as `f6589bdd7c403b6d400e3f5b7a0daea75b14632a`.

## Current lifecycle

```text
PR #185 — MERGED — B3 AUTHORIZED
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## B3 implementation changeset

Implemented:

- frontend parses `restoring`, `restore_completed`, `restore_failed`, `restore_blocked` and still rejects unknown states;
- current accepted candidate exposes explicit destructive confirmation rather than auto-executing;
- confirmation dismiss/Escape stays local and sends no cancel command;
- execute body is exactly `request_id + command_seq + generation`;
- runtime derives generation only from current accepted snapshot;
- execute pending replay stores that generation while select/cancel historical replay shape remains unchanged;
- ambiguous execute retry preserves the **same request ID, command sequence and generation**;
- reload can resume exact pending execute;
- duplicate execute race is guarded before HTTP by the persisted pending command;
- restoring state continues launcher-control polling and removes select/cancel/reconfirm/fake-progress affordances;
- final B2 states minimally show safe launcher messages;
- `main.ts` remains unchanged;
- no launcher/backend/migration/dependency/package-resource implementation change.

Actual build/test/smoke PASS is not claimed until exact-head verification runs on the published B3 PR head.

## Still blocked

```text
C4-II-C — not authorized
C4-III — not authorized
```

## Open B3 gates

- lifecycle checker + `git diff --check`;
- frontend build/type-check;
- focused Restore control tests including exact replay and duplicate-submit race;
- desktop and narrow-screen Restore route smoke;
- keyboard/focus/Escape confirmation smoke;
- loading/network/restoring/final/disabled-state review;
- clean exact head/worktree;
- independent `P0=0/P1=0/P2=0` audit;
- merge only after all exact-head evidence is green;
- separate B3 lifecycle closure before any C4-II-C authorization.