# Change Requests

Updated: `2026-08-09`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger remains byte-identical at `docs/history/change-requests/2026-08-06-pre-compaction.md`.

## Current lifecycle

```text
PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Ledger

| ID | Date | Request | Current status | Durable record / outcome |
|---|---|---|---|---|
| CR-001 | 2026-06-21 | Add Codex project-memory structure | accepted and in use | `docs/codex-project-structure.md`. |
| CR-002 | 2026-07-26 | Dashboard safe-GET pilot only | accepted and implemented | broader expansion deferred. |
| CR-003 | 2026-07-26 | Backend baseline correction gate | accepted and completed | deterministic failures closed. |
| CR-004 | 2026-07-26 | SQLite backup transaction consistency | accepted and implemented | SQLite Online Backup API; ADR 0015. |
| CR-005 | 2026-07-27 | Backup/export filename reason contract | accepted and implemented | canonical grammar. |
| CR-006 | 2026-07-29 | JSON export confirmation semantics | accepted and implemented | ADR 0014. |
| CR-007 | 2026-07-27 | Workshop tax-rate setting | accepted and implemented | backend-owned setting. |
| CR-008 | 2026-07-27 | Financial estimates/snapshots | accepted and implemented | ADR 0012. |
| CR-009 | 2026-07-30 | File-backed artifact AuditLog semantics | accepted and implemented | ADR 0013. |
| CR-010 | 2026-08-02 | Launcher-assisted Restore semantics | accepted; C4-I implemented; product Restore incomplete | ADR 0016. |
| CR-011 | 2026-08-06 | Launcher Restore interaction and non-destructive validation-session boundary | **accepted — ADR 0018 normative on main** | launcher loopback control, `/usr/bin/osascript` picker, exact-run browser session, non-destructive validation. |

## A4 closure

PR #180 reviewed exact head `79c698ed76d478d608a25f4b95499ff519794228` merged as `e61d4e233c98d3c53e7749fe96ed0ee630610372`. A4 passed automated gates, cross-layer smoke, manual desktop/narrow/keyboard/native-picker UI smoke and independent P0=0/P1=0/P2=0. C4-II-A is complete.

## B slicing decision

No new CR or ADR is required for B1. ADR 0016 already requires immutable source, full revalidation before destructive work, mandatory safety copy and C4-I launcher ownership. ADR 0018 already requires a later B to reopen/re-prove the launcher-private source before destructive execution.

`docs/c4-ii-b-implementation-slices.md` translates those accepted decisions into small PR boundaries:

- B1 — source-proof binding at C4-I held-descriptor intake — **AUTHORIZED NEXT**;
- B2 — launcher destructive coordinator/control command — planned, not authorized;
- B3 — browser explicit destructive confirmation — planned, not authorized.

B1 is not permission to implement B2/B3. If B1 cannot preserve current C4-I phase/safety/recovery semantics without a new architectural decision, stop and open a new change request instead of silently changing the contract.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger can shorten their row. Preserve historical ledgers under `docs/history/` and keep the protected pre-compaction snapshots byte-identical.
