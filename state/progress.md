# Progress

Updated: `2026-08-09`

## Completed / merged baseline

- C1/C2 completed; C3 completed, merged, exact-head verified and hardened.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- A1/A2/A3 — merged and exact-head verified.
- A4 / PR #180 — reviewed `79c698ed76d478d608a25f4b95499ff519794228`, merged as `e61d4e233c98d3c53e7749fe96ed0ee630610372`.
- A4 gate: launcher 15 / A3 14 / A2 29 / A1 17 / C4-I 514 / full backend+launcher 2470 / frontend A4 16 / backup 25 / audit-log 92 / exact-head smoke PASS / manual desktop+narrow+keyboard+native-picker UI PASS / independent 0-0-0.
- C4-II-A is now complete.
- Searchable history and five exact pre-compaction snapshots remain protected.

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

## B1 authorization

B1 is intentionally small: add the launcher-private expected-source proof gate at existing C4-I intake, using the same `HeldSource` descriptor that will be staged. It must compare expected `SourceIdentity`, revalidate identity/path/self-containment, recompute full SHA-256 through the held descriptor, verify byte count, then revalidate again.

A mismatch must stop before `prepared`, safety copy or any working-database mutation. Existing C4-I callers without expected proof remain unchanged.

## Still blocked

```text
C4-II-B2 — not authorized
C4-II-B3 — not authorized
C4-II-C — not authorized
C4-III — not authorized
```

## Open product obligations

- merge/verify the A4 closure + B1 authorization documentation PR;
- implement and exact-head verify B1;
- lifecycle-close B1 before deciding B2 destructive coordinator/control semantics;
- later B3 explicit destructive confirmation;
- later C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
