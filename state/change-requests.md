# Change Requests

Updated: `2026-08-09`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger remains byte-identical at `docs/history/change-requests/2026-08-06-pre-compaction.md`.

## Current lifecycle

```text
PR #181 — MERGED — B1 AUTHORIZED
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
C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
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

## B1 implementation under accepted decisions

No new CR/ADR was needed. PR #181 authorized B1 under ADR 0016/0018 and merged as `beae1407af270ad1c800c308ea7907750430eb1d`.

B1 implements only the authorized source-proof binding seam. Historical base `RestoreRequest` remains selected-source-only; launcher-private `ProofBoundRestoreRequest(RestoreRequest)` adds only `ExpectedSourceProof(SourceIdentity, SHA-256)`. That proof is checked against the same C4-I `HeldSource` later staged, before `prepared`.

Mismatch maps to fixed `SOURCE_CHANGED` guidance and creates no Restore record, safety copy or working-database mutation. Legacy C4-I callers continue to use the unchanged base request. No additional destructive/application-owned path is caller-supplied.

`launcher/restore/staging.py` remains byte-identical; phase, safety-copy, replacement, rollback/recovery and AuditLog semantics are unchanged.

- B1 — **IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED**;
- B2 — planned, not authorized;
- B3 — planned, not authorized.

B1 is not permission to implement B2/B3. If exact-head tests reveal that this seam cannot preserve current C4-I semantics, stop and open a new change request instead of silently changing architecture.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger can shorten their row. Preserve historical ledgers under `docs/history/` and keep the protected pre-compaction snapshots byte-identical.
