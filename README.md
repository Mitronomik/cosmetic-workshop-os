# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #180 reviewed exact head `79c698ed76d478d608a25f4b95499ff519794228` merged as `e61d4e233c98d3c53e7749fe96ed0ee630610372` after automated exact-head gates, cross-layer smoke, desktop/narrow/keyboard/native-picker UI smoke and independent P0=0 / P1=0 / P2=0 audit.

## Closed C4-II-A browser interaction foundation

```text
A1 launcher non-destructive candidate proof
→ A2 exact-run authenticated loopback control
→ A3 launcher-owned native macOS picker/path
→ A4 fragment bootstrap + /backups/restore browser presentation
```

The browser owns presentation only. Absolute source path and retained proof remain launcher-private. A4 is non-destructive and exposes no final Restore action.

## Authorized next slice — C4-II-B1

B1 is a narrow source-proof binding gate. It may bind the A1 `SourceIdentity` + full SHA-256 expectation to the exact `HeldSource` descriptor opened by existing C4-I intake before any durable Restore state or safety copy exists.

B1 must **not** add browser confirmation, a destructive control command, a second staging/validation engine, safety-copy creation, database replacement/migration, rollback/recovery mutation or Restore AuditLog.

B2 launcher destructive coordination and B3 browser destructive confirmation remain separately **NOT AUTHORIZED**.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine and mandatory `before_restore` recovery point;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-a-implementation-slices.md` — closed A1→A4 sequence;
- `docs/c4-ii-b-implementation-slices.md` — bounded B1→B3 sequence.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package, API-first business architecture, safe historical data, recipe versions, first-class client recipes, lot/movement inventory, transactional production, safe import preview/confirmation, backup-before-migration and a human-readable non-technical UI.

Restore additionally preserves immutable selected source, launcher filesystem/destructive authority, pathless browser presentation, C4-I as the single destructive engine, and no destructive action before the separately authorized B2/B3 gates.
