# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
PR #181 — MERGED — B1 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #181 reviewed exact head `d2549cd9be2b60c5aee2479050e05a6ad8530c6c` merged as `beae1407af270ad1c800c308ea7907750430eb1d`, closing C4-II-A and authorizing only B1.

## Current B1 implementation boundary

B1 is a launcher-private additive source-proof gate. The historical base `RestoreRequest` remains selected-source-only. A future trusted launcher coordinator that owns current A1 evidence uses `ProofBoundRestoreRequest(RestoreRequest)` with one additional non-path `ExpectedSourceProof` containing the A1 `SourceIdentity` + full SHA-256 expectation.

C4-I opens the source once through the existing `open_selected_source(...)`, then `bind_expected_source_proof(...)` proves identity, path/descriptor stability, self-containment, full held-descriptor SHA-256 and byte count before `prepared` exists. The exact same `HeldSource` object then continues into the unchanged `stage_source(...)` implementation.

A mismatch returns the fixed non-technical `SOURCE_CHANGED` result before any durable Restore record, safety copy or working-database mutation. Legacy C4-I callers continue to construct base `RestoreRequest` and retain existing behavior.

`launcher/restore/staging.py` remains byte-identical to the PR #181 baseline; B1 does not create a second staging or validation algorithm. The proof subtype adds no database, backup-directory, Restore-directory or lock path.

B1 adds no browser action, control-plane command or destructive coordinator. B2 launcher destructive coordination and B3 browser destructive confirmation remain separately **NOT AUTHORIZED**.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine and mandatory `before_restore` recovery point;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-a-implementation-slices.md` — closed A1→A4 sequence;
- `docs/c4-ii-b-implementation-slices.md` — bounded B1→B3 sequence.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package, API-first business architecture, safe historical data, recipe versions, first-class client recipes, lot/movement inventory, transactional production, safe import preview/confirmation, backup-before-migration and a human-readable non-technical UI.

Restore additionally preserves immutable selected source, launcher filesystem/destructive authority, pathless browser presentation, C4-I as the single destructive engine, and no destructive action before the separately authorized B2/B3 gates.
