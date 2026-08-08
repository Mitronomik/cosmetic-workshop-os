# Change Requests

Updated: `2026-08-08`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger is preserved byte-for-byte at
`docs/history/change-requests/2026-08-06-pre-compaction.md`. Historical evidence
does not override current lifecycle or authorization.

## Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
PR #177 — MERGED — A2 CLOSED / A3 AUTHORIZED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
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

## C4-II-A sliced implementation authorization

PR #173 is not a new CR. It fixes the implementation order already selected by
CR-011:

```text
A1 — validation-session core
→ A2 — exact-run launcher control plane
→ A3 — native picker integration
→ A4 — browser Restore screen
```

## A1/A2 closure evidence

A1 remains the single non-destructive candidate-preparation authority.

PR #176 completed A2 at reviewed head
`681cb4050bec082db6b637285590e232880af739`, merged as
`90a14dd9a11b83bc31a40e1d3fb9523f41772b88`, with race 2, A2 28,
A1 17, C4-I 514, full 2443, smoke and audit P0=0/P1=0/P2=0.

PR #177 reviewed head `d767b957cb3debae584709f2bbadafebd8dd6a9e`
merged as `e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263`, closing A2 and
authorizing only A3.

## A3 current implementation

This is not a new change request and does not change ADR 0018.

A3 is **IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED**. The current runtime
changeset is limited to the already-decided launcher-owned native macOS picker:

- exact `/usr/bin/osascript` + fixed Standard Additions `choose file`;
- no user-controlled AppleScript interpolation;
- `shell=False`, no `System Events`;
- error `-128` → typed user cancellation;
- launcher-private absolute POSIX path;
- cancel/expiry owned child terminate/reap + kill fallback;
- existing A2 source-selection seam → merged A1 validation;
- no new dependency.

A3 does not add browser path/file authority, `/backups/restore`, production
bootstrap-fragment handoff or destructive Restore authority. It still requires
exact-head tests/smoke/audit and merge + post-merge lifecycle closure before A4
can open.

## C4-II-B boundary

C4-II-B remains **PLANNED — NOT AUTHORIZED**. No C4-II-A slice may add destructive
execute/confirm authority, safety-copy creation, working-DB replacement/migration,
rollback/recovery mutation or Restore AuditLog.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger
can shorten their row. Preserve historical ledgers under `docs/history/` and keep
the protected pre-compaction snapshot byte-identical.
