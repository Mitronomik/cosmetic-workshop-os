# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-09`

This is the compact authority for current implementation lifecycle and authorization. ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

## Current lifecycle

```text
PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
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
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## A4 closure evidence

PR #180 final reviewed head:
`79c698ed76d478d608a25f4b95499ff519794228`

Merge/new main:
`e61d4e233c98d3c53e7749fe96ed0ee630610372`

Accepted evidence:

- `git diff --check`: PASS;
- documentation lifecycle checker: PASS;
- A4 launcher targeted: 15 passed;
- A3 regression: 14 passed;
- A2 regression: 29 passed;
- A1 regression: 17 passed;
- C4-I Restore regression: 514 passed;
- full backend + launcher: 2470 passed;
- frontend build: PASS;
- frontend A4: 16 passed, including bootstrap/session race regressions;
- backup frontend regression: 25 passed;
- audit-log frontend regression: 92 passed;
- A4 exact-head cross-layer smoke: PASS;
- `frontend/src/main.ts` remained blob `ea98a76638bddcb5a92b9ba31941508f8a816d42`;
- desktop, narrow-window, keyboard/focus and real macOS picker UI smoke: PASS;
- valid backup acceptance remained explicitly non-destructive and pathless;
- clean exact head before/after;
- independent audit: P0=0 / P1=0 / P2=0.

## Closed C4-II-A boundary

A1 remains non-destructive candidate preparation and retained source proof. A2 remains exact-run loopback authentication/liveness/replay authority. A3 remains the launcher-owned native picker/path/process boundary. A4 remains the browser fragment/session/presentation layer under `/backups/restore`.

A4 browser state is never destructive authority. Filename, session token, `history.state` and accepted presentation cannot authorize database replacement.

## Authorized B1 boundary

Only **C4-II-B1 — retained-source proof binding into C4-I intake** is authorized next.

B1 must reuse the source descriptor opened by existing `open_selected_source(...)`. When an expected A1 proof is supplied, the C4-I intake must compare the held `SourceIdentity`, revalidate path/descriptor identity, re-check sidecars/self-containment and recompute the full SHA-256 through `HeldSource.digest()` before any durable Restore record, safety copy or working-database mutation exists.

The proof check must be against the same `HeldSource` descriptor that C4-I will stage. A separate path re-open followed by a later destructive re-open is not sufficient because it leaves a substitution window.

B1 is an additive safety gate only. Existing C4-I callers without an expected proof retain current behavior. B1 may not add a browser action, a new control endpoint, a new Restore engine, a safety copy, replacement, migration, rollback/recovery mutation or Restore AuditLog.

`docs/c4-ii-b-implementation-slices.md` is the normative implementation slice plan for B1/B2/B3.

## Successor gate

B2 and B3 remain **PLANNED — NOT AUTHORIZED**. B1 must be implemented in one bounded PR, exact-head verified, merged and lifecycle-closed before the exact destructive coordinator/control semantics for B2 may be authorized.

C4-II-C and C4-III remain separately blocked. Product Restore is still **NOT IMPLEMENTED**.
