# Change Requests

Updated: `2026-08-08`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger remains byte-identical at `docs/history/change-requests/2026-08-06-pre-compaction.md`.

## Current lifecycle

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
PR #179 — MERGED — A3 CLOSED / A4 AUTHORIZED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B — PLANNED — NOT AUTHORIZED
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

## C4-II-A implementation status

A1/A2/A3 are merged and exact-head verified. PR #179 reviewed head `72b04510efd6d1f104369a450ed1c4d4dfe063ad` merged as `52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf`, closing A3 and authorizing only A4.

A4 is **IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED**. It implements the already-decided browser presentation/session layer: fragment-only bootstrap, immediate fragment removal, sessionStorage descriptor allowlist, same-tab non-secret strict-command replay metadata, heartbeat/reload, `/backups/restore`, select/cancel/reselect and safe browser presentation over the existing A2→A3→A1 chain.

This is not a new CR and does not amend ADR 0018.

## C4-II-B boundary

C4-II-B remains **PLANNED — NOT AUTHORIZED**. Browser session state, history replay metadata, filename and accepted validation are never destructive authority. No C4-II-A slice may add destructive execute/confirm, safety-copy creation, working-DB replacement/migration, rollback/recovery mutation or Restore AuditLog.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger can shorten their row. Preserve historical ledgers under `docs/history/` and keep the protected pre-compaction snapshots byte-identical.
