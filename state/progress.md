# Progress

Updated: `2026-08-08`

## Completed / merged baseline

- C1/C2 completed; C3 completed, merged, exact-head verified and hardened.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- A1 — merged/exact-head verified.
- A2 — merged/exact-head verified with 2 stale-authority race tests, 28 A2, 17 A1, 514 C4-I, 2443 full and smoke PASS.
- A3 / PR #178 — reviewed `b0de148032d9b3d2f9912298897f8649c9b1692b`, merge `9d95b0c39c4abd05d5a574c6cd8574b8e457f36b`, 14 A3 / 28 A2 / 17 A1 / 514 C4-I / 2457 full / smoke / audit 0/0/0.
- PR #179 A3 closure / A4 authorization — reviewed `72b04510efd6d1f104369a450ed1c4d4dfe063ad`, merge `52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf`, lifecycle PASS, 12 docs/state/checker paths, audit 0/0/0.
- Searchable history and five exact pre-compaction snapshots remain protected.

## Current lifecycle

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
PR #179 — MERGED — A3 CLOSED / A4 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## A4 implemented in current changeset

Runtime/frontend:

- launcher browser fragment handoff and fail-closed ordinary-product fallback;
- exact nested `/backups/restore` route;
- pre-shell fragment capture/removal;
- one-use bootstrap and sessionStorage descriptor allowlist;
- same-tab `history.state` command replay metadata;
- strict A2 sequence/idempotent retry behavior across network uncertainty/reload;
- heartbeat/state polling;
- exact DTO shape allowlists;
- pathless Russian Restore presentation;
- `frontend/src/main.ts` unchanged.

Verification assets:

- launcher handoff/runtime tests;
- targeted frontend Restore control tests;
- TypeScript build coverage;
- live A4→A2→A3→A1/C4-I non-destructive smoke.

## Verification status

Implementation exists, but exact-head verification is pending. Do not mark A4 `DONE` until lifecycle/diff, frontend build/targeted/relevant regressions, launcher A4/A3/A2/A1/C4-I/full regressions, browser-session smoke, desktop/narrow/keyboard review and independent audit pass on the final published head.

## Still blocked

```text
C4-II-B — not authorized
C4-II-C — not authorized
C4-III — not authorized
```

## Open product obligations

- exact-head verify/review/merge A4;
- post-merge lifecycle/authorization decision before C4-II-B;
- later C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
