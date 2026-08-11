# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
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
C4-II-B3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #184 reviewed exact head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4` merged as `266c50a77e5f353fa77701cb854629a99460667f`. B2 is closed on accepted exact-head tests, external process smoke, independent `P0=0 / P1=0 / P2=0` audit and final clean-head gate.

## Closed Restore authority through B2

A1 retains launcher-private source path + `SourceIdentity` + SHA-256. B1 binds that proof to the exact `HeldSource` entering C4-I. B2 adds the one-shot authenticated `/v1/restore/execute` coordinator on the launcher main runtime path. C4-I remains the only destructive Restore engine.

The browser remains presentation only. No source path, proof, digest, operation ID, database path, backup path or lock path crosses the control boundary.

## Authorized next slice — C4-II-B3

B3 is frontend-only destructive confirmation/presentation wiring. It may extend the existing browser Restore contract with the B2 states and the `execute` action, but it must preserve launcher-only filesystem authority and exact replay semantics.

An ambiguous execute retry must resend the same `request_id + command_seq + generation`. No `/v1/restore/confirm` endpoint is authorized.

C4-II-C/C4-III remain blocked. Product Restore remains **NOT IMPLEMENTED** until later lifecycle slices close the user-facing result/recovery flow.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine and mandatory `before_restore` recovery point;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-b-implementation-slices.md` — B1→B3 implementation and authorization contract.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package, API-first business architecture, safe historical data, recipe versions, first-class client recipes, lot/movement inventory, transactional production, safe import preview/confirmation, backup-before-migration and a human-readable non-technical UI.

Restore additionally preserves immutable selected source, launcher filesystem/destructive authority, pathless browser presentation, C4-I as the single destructive engine, exact-run authenticated control, one-shot command semantics, and explicit human confirmation before browser destructive execution.
