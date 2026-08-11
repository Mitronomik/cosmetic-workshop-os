# Change Requests

Updated: `2026-08-09`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger remains byte-identical at `docs/history/change-requests/2026-08-06-pre-compaction.md`.

## Current lifecycle

```text
PR #183 — MERGED — B2 AUTHORIZED
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
C4-II-B2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
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
| CR-011 | 2026-08-06 | Launcher Restore interaction and non-destructive validation-session boundary | **accepted — ADR 0018 normative on main** | launcher loopback control, native picker, exact-run browser session, non-destructive validation. |

## B1 closure / B2 implementation under accepted decisions

No new CR/ADR is required. B1 and B2 remain inside ADR 0016 destructive authority and ADR 0018 exact-run launcher control architecture.

PR #182 implemented and closed B1 on exact head `27726058af4f373ab65225ecf4d1a945f1c53067`, then merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`.

PR #183 reviewed B2 authorization at `fa922f56c19a2dd33b6307ae0a197d476f91489b` and merged as `4617b8c436eaa510fd545d863346595e2d808ea7`.

The current B2 changeset implements only that accepted coordinator contract:

- one authenticated `/v1/restore/execute` command;
- exact `request_id + command_seq + generation` body;
- browser generation used only as accepted-control stale-view guard;
- current A1 path/proof transferred once into launcher-private memory and invalidated immediately;
- no path/proof/digest from browser;
- HTTP/session worker queues only and never runs C4-I;
- main launcher runtime synchronously invokes existing C4-I exactly once;
- same control plane stays alive across ordinary backend stop/restart;
- browser/session expiry cannot cancel already accepted destructive execution;
- restart/result handoff uses canonical `BackendProcessOwner` without reinterpreting C4-I truth;
- B1/C4-I, A1/A3/A4 and frontend closed boundaries stay protected.

- B1 — **DONE — MERGED AND EXACT-HEAD VERIFIED**;
- B2 — **IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED**;
- B3 — planned, not authorized.

B2 still requires exact-head focused/regression tests, external isolated process smoke and independent audit before merge. Its merge will not authorize B3; a separate lifecycle closure is required.

If verification reveals that B2 cannot preserve main-runtime ownership, exact-run control or the existing C4-I boundary, stop and open a new change request instead of silently changing architecture.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger can shorten their row. Preserve historical ledgers under `docs/history/` and keep the protected pre-compaction snapshots byte-identical.
