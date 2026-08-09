# Current Focus — C4-II-A4 browser Restore session UX

Updated: `2026-08-08`

## Merged baseline

```text
PR #178 reviewed A3 head — b0de148032d9b3d2f9912298897f8649c9b1692b
PR #178 merge — 9d95b0c39c4abd05d5a574c6cd8574b8e457f36b
PR #179 reviewed closure head — 72b04510efd6d1f104369a450ed1c4d4dfe063ad
PR #179 merge — 52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf
```

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

## Current A4 implementation

- fragment-only launcher handoff through `launcher/restore/browser_handoff.py`;
- `/backups/restore` exact nested route and secondary entry from `/backups`;
- `restore-control-entry.ts` loaded before `main.js`;
- synchronous fragment removal before shell routing;
- one-use bootstrap exchange;
- only `control_origin`, `run_id`, session token in `sessionStorage`;
- same-tab non-secret `history.state` replay metadata for exact A2 retry/sequence safety;
- fail-closed reload if prior command history cannot be proved;
- 15s heartbeat + active-state polling;
- strict DTO allowlists and no browser path/file authority;
- safe Russian states and no destructive action;
- `frontend/src/main.ts` stays byte-identical;
- cross-layer browser-session smoke added.

## Hard seams

No `localStorage` token, query token, browser file input/upload/path, FastAPI Restore mutation, WebSocket/generic launcher command surface, `execute_restore`, safety copy, DB replacement/migration, rollback/recovery mutation or Restore AuditLog.

C4-II-B remains separately not authorized.

## Verification still required

No PASS is claimed until the final exact A4 head passes lifecycle/diff, frontend build + targeted tests, launcher A4/A3/A2/A1/C4-I regressions, full backend+launcher regression, relevant frontend regression, exact-head A4 browser-session smoke, desktop/narrow/keyboard review, clean status/head and independent P0=0/P1=0/P2=0 audit.
