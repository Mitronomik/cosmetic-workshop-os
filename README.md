# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
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
C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #182 reviewed exact head `27726058af4f373ab65225ecf4d1a945f1c53067` merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`. Its final gate was full backend+launcher `2480/2480`, external exact-head source-substitution smoke PASS, and independent `P0=0 / P1=0 / P2=0`.

## Closed B1 boundary

B1 preserves historical base `RestoreRequest` as selected-source-only and adds launcher-private `ProofBoundRestoreRequest` carrying `ExpectedSourceProof(SourceIdentity, SHA-256)`. C4-I re-proves that evidence against the exact same held source descriptor that it later stages, before `prepared`, safety copy or working-database mutation.

`launcher/restore/staging.py` remains byte-identical to the B1 baseline. No second Restore engine, staging algorithm or browser authority was introduced.

## Authorized next slice — C4-II-B2

B2 is launcher-only destructive coordination. It may add exactly one authenticated control command, `/v1/restore/execute`, and a launcher-private one-shot execution intent consumed by the main launcher runtime loop. The HTTP/session thread must never run C4-I directly.

B2 must consume the current accepted browser generation, transfer the current launcher-private A1 proof into `ProofBoundRestoreRequest`, invalidate that proof before execution, and invoke the existing C4-I `execute_restore(...)` once. The existing control plane remains alive on the same exact-run ephemeral port while the ordinary backend is stopped/restarted.

The launcher main runtime owns backend stop/restart lifecycle. C4-I remains the only component that performs backend exclusion, safety copy, durable phases, replacement, verification and rollback. B2 adds no browser confirmation UI; B3 remains separately **NOT AUTHORIZED**.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine and mandatory `before_restore` recovery point;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-a-implementation-slices.md` — closed A1→A4 sequence;
- `docs/c4-ii-b-implementation-slices.md` — bounded B1→B3 sequence and exact B2 authorization.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package, API-first business architecture, safe historical data, recipe versions, first-class client recipes, lot/movement inventory, transactional production, safe import preview/confirmation, backup-before-migration and a human-readable non-technical UI.

Restore additionally preserves immutable selected source, launcher filesystem/destructive authority, pathless browser presentation, C4-I as the single destructive engine, exact-run authenticated control, one-shot command semantics, and no browser destructive action before separately authorized B3.
