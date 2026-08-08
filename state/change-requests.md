# Change Requests

Updated: `2026-08-08`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger remains protected under `docs/history/`.

## Current lifecycle

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
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
C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Ledger

| ID | Date | Request | Current status | Durable outcome |
|---|---|---|---|---|
| CR-001 | 2026-06-21 | Codex project-memory structure | accepted and in use | bounded project-memory workflow |
| CR-002 | 2026-07-26 | Dashboard safe-GET pilot | accepted and implemented | broader expansion deferred |
| CR-003 | 2026-07-26 | Backend baseline correction | completed | deterministic baseline fixed |
| CR-004 | 2026-07-26 | SQLite backup consistency | implemented | Online Backup API; ADR 0015 |
| CR-005 | 2026-07-27 | Artifact filename reason contract | implemented | canonical grammar |
| CR-006 | 2026-07-29 | JSON export confirmation semantics | implemented | ADR 0014 |
| CR-007 | 2026-07-27 | Workshop tax-rate setting | implemented | backend-owned setting |
| CR-008 | 2026-07-27 | Financial estimates/snapshots | implemented | ADR 0012 |
| CR-009 | 2026-07-30 | File-backed AuditLog semantics | implemented | ADR 0013 |
| CR-010 | 2026-08-02 | Launcher-assisted Restore semantics | accepted; product Restore incomplete | ADR 0016 |
| CR-011 | 2026-08-06 | Launcher Restore interaction and validation-session boundary | **accepted — ADR 0018 normative on main** | loopback control + native picker + browser session + non-destructive validation |

## C4-II-A sliced authorization

PR #173 fixed the implementation order already selected by CR-011:

```text
A1 validation session
→ A2 exact-run control plane
→ A3 native picker
→ A4 browser Restore presentation/session
```

## A3 closure evidence

PR #178 completed A3 at reviewed head `b0de148032d9b3d2f9912298897f8649c9b1692b`, merged as `9d95b0c39c4abd05d5a574c6cd8574b8e457f36b`.

Accepted evidence: A3 14, A2 28, A1 17, C4-I 514, full 2457, exact-head native-picker smoke PASS, lifecycle PASS and independent audit P0=0 / P1=0 / P2=0.

A3 is **DONE — MERGED AND EXACT-HEAD VERIFIED**.

## A4 lifecycle authorization

This closure is not a new CR and does not change ADR 0018.

A4 is **AUTHORIZED NEXT — NOT IMPLEMENTED**. It may implement only the browser route/bootstrap/session/heartbeat/select-cancel presentation seam already decided in ADR 0018. It may not add browser filesystem authority or destructive Restore authority.

## C4-II-B boundary

C4-II-B remains **PLANNED — NOT AUTHORIZED**. No A4 code may add destructive execute/confirm authority, safety-copy creation, working-DB replacement/migration, rollback/recovery mutation or Restore AuditLog.

## History policy

Historical ledgers and five protected pre-compaction snapshots remain byte-identical.