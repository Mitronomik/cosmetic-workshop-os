# Handoff

Updated: `2026-08-08`

Current lifecycle authority: `docs/current-lifecycle.md`. Accepted CR-011 architecture: ADR 0018. C4-II-A slice plan: `docs/c4-ii-a-implementation-slices.md`.

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

## Last merged lifecycle — PR #179

```text
reviewed head — 72b04510efd6d1f104369a450ed1c4d4dfe063ad
merge commit — 52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf
```

PR #179 closed A3 after its 14 A3 / 28 A2 / 17 A1 / 514 C4-I / 2457 full / native-picker smoke / 0-0-0 gate and authorized only A4.

## Current work — A4 browser Restore session UX

Implemented:

- launcher-owned fragment handoff, no query transport;
- SPA consumes/removes fragment before shell routing;
- one-use bootstrap → exact run-scoped session;
- `sessionStorage` only for `control_origin`, `run_id`, session token;
- non-secret same-tab `history.state` for exact command replay metadata;
- network-uncertain mutation retries the same request ID/sequence;
- missing replay after prior activity fails closed rather than guessing;
- 15s heartbeat and state polling;
- exact response-field allowlists reject unknown/path-bearing fields;
- `/backups/restore` + human-readable entry from `/backups`;
- accepted state remains explicitly non-destructive;
- `frontend/src/main.ts` unchanged;
- targeted tests and cross-layer smoke.

## Not A4

- browser path/source_path/file bytes/upload/bookmark/handle or file input;
- localStorage token persistence;
- ordinary FastAPI Restore mutation;
- WebSocket/generic launcher server;
- destructive confirmation/execute;
- durable Restore phase/safety copy/working-DB mutation/rollback/AuditLog;
- packaging/cloud/OCR/multiuser/advanced analytics.

## Verification required

A4 still requires exact-head diff/lifecycle, frontend build + targeted/relevant regressions, launcher A4/A3/A2/A1/C4-I/full regressions, exact-head browser-session smoke, desktop/narrow/keyboard review, clean status/head and independent P0=0/P1=0/P2=0.

## Successor gate

C4-II-B remains separately not authorized. A4 merge does not authorize destructive Restore; post-merge lifecycle/architecture closure is required first.
