# Current Focus — C4-II-B1 retained source-proof binding

Updated: `2026-08-09`

## Merged baseline

```text
PR #180 reviewed A4 head — 79c698ed76d478d608a25f4b95499ff519794228
PR #180 merge/new main — e61d4e233c98d3c53e7749fe96ed0ee630610372
```

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

## A4 closure evidence

- lifecycle/diff PASS;
- A4 launcher 15;
- A3 14;
- A2 29;
- A1 17;
- C4-I 514;
- full backend+launcher 2470;
- frontend A4 16;
- backup regression 25;
- audit-log regression 92;
- exact-head cross-layer smoke PASS;
- desktop/narrow/keyboard/native-picker UI smoke PASS;
- independent P0=0/P1=0/P2=0.

## Current work — B1 only

B1 will bind A1 launcher-private `SourceIdentity` + SHA-256 to the exact held descriptor opened by existing C4-I intake. The comparison must use `HeldSource.revalidate()`, self-containment checks and `HeldSource.digest()` before any durable Restore state or safety copy exists.

The objective is to guarantee that the backup eventually offered to destructive C4-I is the same backup the user previously validated, even if the path was replaced or the bytes changed after A4 acceptance.

## Hard seams

No browser change, no new control endpoint, no destructive confirmation, no new Restore engine, no duplicate staging/validation, no safety-copy/replacement/recovery redesign, no Restore AuditLog change, no packaging/cloud/OCR/multiuser/advanced analytics.

B2/B3 remain separately not authorized.
