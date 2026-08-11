# Change Requests

Updated: `2026-08-11`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger remains byte-identical at `docs/history/change-requests/2026-08-06-pre-compaction.md`.

## Current lifecycle

```text
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
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
| CR-010 | 2026-08-02 | Launcher-assisted Restore semantics | accepted; C4-I/B1/B2 implemented and closed; product Restore incomplete | ADR 0016. |
| CR-011 | 2026-08-06 | Launcher Restore interaction and non-destructive validation-session boundary | **accepted — ADR 0018 normative on main** | launcher loopback control, picker, browser session and bounded B2 coordinator. |

## B2 closure / B3 authorization under accepted decisions

No new CR/ADR is required. PR #184 closes B2 inside ADR 0016/0018 authority.

PR #184 reviewed head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4` merged as `266c50a77e5f353fa77701cb854629a99460667f`.

B3 is now authorized as frontend-only explicit destructive confirmation. It may extend browser parsing/replay/presentation for the already-merged B2 endpoint but may not change launcher/backend destructive semantics.

Load-bearing B3 replay: pending execute preserves the **same request ID, command sequence and accepted generation** on ambiguous retry. Browser never persists source path/proof/digest.

C4-II-C/C4-III remain not authorized. If B3 implementation requires launcher/backend changes, stop and open a new lifecycle/architecture question rather than silently widening scope.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger can shorten their row. Preserve historical ledgers under `docs/history/` and keep protected snapshots byte-identical.
