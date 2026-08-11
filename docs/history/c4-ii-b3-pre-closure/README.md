# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

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

PR #184 reviewed exact head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4` merged as `266c50a77e5f353fa77701cb854629a99460667f`, closing B2.

PR #185 reviewed B2-closure/B3-authorization head `f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c` merged as `f6589bdd7c403b6d400e3f5b7a0daea75b14632a`, authorizing B3 only.

## Closed Restore authority through B2

A1 retains launcher-private source path + `SourceIdentity` + SHA-256. B1 binds that proof to the exact `HeldSource` entering C4-I. B2 adds the one-shot authenticated `/v1/restore/execute` coordinator on the launcher main runtime path. C4-I remains the only destructive Restore engine.

The browser remains presentation only. No source path, proof, digest, operation ID, database path, backup path or lock path crosses the control boundary.

## B3 implementation changeset

B3 now implements the authorized frontend-only confirmation/replay seam without changing launcher/backend authority:

- current `accepted` candidate exposes an explicit destructive confirmation dialog;
- dismiss/Escape are local UI actions and send neither execute nor `/v1/restore/cancel`;
- destructive confirmation calls only `/v1/restore/execute` with exact `request_id + command_seq + generation`;
- generation comes only from the current parsed accepted snapshot;
- ambiguous execute retry preserves the exact same request ID, command sequence and generation;
- select/cancel replay keeps its historical shape;
- browser parsing accepts the merged B2 states `restoring`, `restore_completed`, `restore_failed`, `restore_blocked` and still fails closed on unknown states;
- `restoring` offers no destructive cancel, no duplicate confirmation and no fake progress;
- final B2 states minimally present only the safe launcher-provided message;
- `frontend/src/main.ts` remains unchanged.

No `/v1/restore/confirm` endpoint is introduced. C4-II-C/C4-III remain blocked. Product Restore remains **NOT IMPLEMENTED** until later lifecycle slices close richer result/recovery UX and the end-to-end product gate.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine and mandatory `before_restore` recovery point;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-b-implementation-slices.md` — B1→B3 implementation and authorization contract.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package, API-first business architecture, safe historical data, recipe versions, first-class client recipes, lot/movement inventory, transactional production, safe import preview/confirmation, backup-before-migration and a human-readable non-technical UI.

Restore additionally preserves immutable selected source, launcher filesystem/destructive authority, pathless browser presentation, C4-I as the single destructive engine, exact-run authenticated control, one-shot command semantics, and explicit human confirmation before browser destructive execution.