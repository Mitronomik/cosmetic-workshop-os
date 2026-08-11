# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
PR #186 — MERGED — C4-II-B3 EXACT-HEAD VERIFIED
PR #185 — MERGED — B3 AUTHORIZATION BASELINE
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-C — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #186 reviewed exact head `316358c65a851b46090121c7a6bc877b980176ba` and merged as `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`, closing C4-II-B3 and the complete C4-II-B group.

## Closed Restore authority through B3

C4-I remains the only destructive Restore engine. B1 binds launcher-private retained source proof to C4-I intake. B2 owns the authenticated one-shot `/v1/restore/execute` authority transfer and ordinary-backend restart handoff. B3 owns explicit browser confirmation, exact destructive replay, and pathless `restoring`/final-state presentation.

The browser has no filesystem/source authority. No source path, proof, digest, operation ID, database path, backup path or lock path crosses the browser boundary. No `/v1/restore/confirm` endpoint exists.

## Authorized next work

**C4-II-C — Truthful Restore completion/recovery/restart/support UX** is the only authorized next implementation slice. It is **frontend-only** and must use the already-merged `restore_completed`, `restore_failed`, and `restore_blocked` states without reopening launcher/backend/contract/runtime authority.

Hard constraints: no new launcher state, no new control endpoint, no browser filesystem authority, no destructive retry, no destructive cancel, no durable-phase reconstruction in frontend, and no C4-III implementation.

Restore remains **NOT IMPLEMENTED** as a complete product flow until C4-II-C and later product gates close. Product release readiness remains **NOT CLAIMED**.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine and mandatory `before_restore` recovery point;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-b-implementation-slices.md` — closed B1→B3 implementation contract;
- `docs/restore-interaction-and-validation-session.md` — active browser/control interaction profile.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package, API-first business architecture, safe historical data, recipe versions, first-class client recipes, lot/movement inventory, transactional production, safe import preview/confirmation, backup-before-migration and a human-readable non-technical UI.
