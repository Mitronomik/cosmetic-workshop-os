# Handoff

Updated: `2026-08-09`

Current lifecycle authority: `docs/current-lifecycle.md`. Accepted Restore decisions: ADR 0016 and ADR 0018. Closed A plan: `docs/c4-ii-a-implementation-slices.md`. Current B plan: `docs/c4-ii-b-implementation-slices.md`.

## Current lifecycle

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

## Last merged implementation — PR #180

```text
reviewed head — 79c698ed76d478d608a25f4b95499ff519794228
merge/new main — e61d4e233c98d3c53e7749fe96ed0ee630610372
```

A4 closed after automated exact-head gates, cross-layer non-destructive smoke, desktop/narrow/keyboard/native-picker UI smoke and independent P0=0/P1=0/P2=0.

## Current work — B1 retained source-proof binding

Implement one internal safety seam only:

```text
A1 retained SourceIdentity + SHA-256
→ future trusted expectation
→ C4-I open_selected_source(...)
→ exact same HeldSource descriptor
→ identity + revalidate + self-containment
→ held digest + exact byte count
→ revalidate + self-containment again
→ existing C4-I staging/validation may continue
```

The mismatch path must stop before durable `prepared`, safety copy or working-database mutation.

## Not B1

- browser confirmation or button;
- new control HTTP command;
- user-facing `execute_restore` coordinator;
- duplicate staging/validation engine;
- durable phase vocabulary changes;
- safety-copy/replacement/recovery redesign;
- Restore AuditLog changes;
- packaging/cloud/OCR/multiuser/advanced analytics.

## Successor gate

B2/B3 are not authorized. After B1 is implemented, exact-head verified and merged, create a separate closure/authorization PR before defining the destructive coordinator/control command.
