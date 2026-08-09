# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-09`

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

## Merged baseline

```text
PR #180 reviewed A4 head — 79c698ed76d478d608a25f4b95499ff519794228
PR #180 merge/new main — e61d4e233c98d3c53e7749fe96ed0ee630610372
```

A4 final proof: launcher 15, A3 14, A2 29, A1 17, C4-I 514, full backend+launcher 2470, frontend A4 16, backup regression 25, audit-log regression 92, exact-head cross-layer smoke PASS, manual desktop/narrow/keyboard/native-picker smoke PASS, lifecycle PASS, independent P0=0/P1=0/P2=0.

## Current implementation window — C4-II-B1

Implement only the launcher-private expected-source proof binding described in `docs/c4-ii-b-implementation-slices.md`.

B1 must add a narrow reusable gate at existing C4-I source intake. When a future trusted caller supplies the A1 expected source proof, C4-I must compare it against the exact `HeldSource` descriptor it has opened before any durable Restore operation exists.

Required proof:

```text
expected A1 SourceIdentity + SHA-256
→ open_selected_source(...)
→ same held descriptor
→ identity equality
→ revalidate()
→ assert_still_self_contained()
→ HeldSource.digest()
→ exact byte count + SHA-256 equality
→ revalidate + self-containment again
→ only then existing C4-I staging/validation may continue
```

A mismatch must stop before `prepared`, before `before_restore`, and before any working-database mutation.

## Mandatory B1 seams

### Single-engine seam

C4-I remains the only staging/validation/destructive Restore engine. B1 must not copy C4-I logic into a new coordinator or create a second staging algorithm.

### Held-descriptor seam

The expectation must be checked against the descriptor C4-I actually stages. A pre-check that reopens the path and then lets C4-I reopen it later is insufficient because the path could be substituted between checks.

### Compatibility seam

Existing C4-I calls without an expected proof keep current behavior. B1 is additive safety hardening for the future C4-II-B trusted path, not a rewrite of historical internal C4-I callers.

### Presentation seam

B1 adds no browser route, control endpoint or destructive button. Any mismatch maps to a fixed safe source-changed category/message; raw paths, SQL, migration IDs, stack traces and database contents remain private.

## Required B1 proof

At minimum prove:

1. matching identity+digest can continue into unchanged C4-I behavior;
2. same path/new inode is rejected before `prepared`;
3. same inode/size but different bytes is rejected by held-descriptor digest;
4. a newly appeared WAL/SHM/journal sidecar is rejected;
5. symlink/path substitution remains rejected;
6. digest byte-count mismatch is rejected;
7. mismatch creates no durable operation record, safety copy or working-DB change;
8. selected source remains byte-identical;
9. legacy C4-I calls without expectation retain behavior;
10. closed A1/A2/A3/A4 regressions remain green;
11. exact-head smoke proves changed-source refusal before any destructive boundary;
12. independent P0=0/P1=0/P2=0 audit.

## Forbidden scope

No B2/B3 runtime wiring, browser destructive confirmation, new control command, FastAPI Restore mutation, second Restore engine, phase/recovery redesign, packaging redesign, cloud sync, OCR, roles/multiuser or advanced analytics.

## Next action

Merge and independently verify this A4-closure/B1-authorization docs PR → implement B1 as one bounded PR → exact-head tests/smoke/audit → lifecycle-close B1 before deciding B2 command/coordinator semantics.
