# Change Requests

Updated: `2026-08-08`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger is preserved byte-for-byte at
`docs/history/change-requests/2026-08-06-pre-compaction.md`. Historical evidence
does not override current lifecycle or authorization.

## Current lifecycle

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
PR #175 — MERGED — A1 CLOSED / A2 AUTHORIZED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Ledger

| ID | Date | Request | Current status | Durable record / outcome |
|---|---|---|---|---|
| CR-001 | 2026-06-21 | Add Codex project-memory structure | accepted and in use | `docs/codex-project-structure.md`; bounded PR/project-memory workflow. |
| CR-002 | 2026-07-26 | Close B4 with Dashboard safe-GET pilot only | accepted and implemented | Dashboard safe-GET pilot delivered; broader expansion deferred. |
| CR-003 | 2026-07-26 | Open backend baseline correction gate | accepted and completed | Deterministic baseline failures classified and closed. |
| CR-004 | 2026-07-26 | Investigate SQLite backup transaction consistency | accepted and implemented | Raw live-file copy replaced by SQLite Online Backup API. ADR 0015. |
| CR-005 | 2026-07-27 | Decide backup/export filename reason contract | accepted and implemented | Canonical filename-derived reason grammar implemented. |
| CR-006 | 2026-07-29 | Decide JSON export confirmation semantics | accepted and implemented | JSON-export AuditLog coverage corrected. ADR 0014. |
| CR-007 | 2026-07-27 | Decide workshop tax-rate setting | accepted and implemented | Backend-owned `default_tax_rate`; immutable historical meaning. |
| CR-008 | 2026-07-27 | Decide financial estimates/snapshots | accepted and implemented | C2 financial snapshot work completed. ADR 0012. |
| CR-009 | 2026-07-30 | Decide file-backed artifact AuditLog semantics | accepted and implemented | Shared durable artifact-audit semantics. ADR 0013. |
| CR-010 | 2026-08-02 | Decide launcher-assisted Restore semantics | accepted; C4-I implemented; product Restore incomplete | ADR 0016; C4-I safety engine merged in PR #170. |
| CR-011 | 2026-08-06 | Decide launcher Restore interaction and non-destructive validation-session boundary | **accepted — ADR 0018 normative on main** | PR #172 selected launcher-owned authenticated loopback control plane, `/usr/bin/osascript` picker, exact-run browser session and non-destructive validation service. |

## C4-II-A sliced implementation authorization

PR #173 is **not** a new architecture/change request. It is the lifecycle
authorization required by CR-011 and fixes the implementation order:

```text
A1 — validation-session core
→ A2 — exact-run launcher control plane
→ A3 — native picker integration
→ A4 — browser Restore screen
```

## A1 closure evidence

PR #174 completed A1:

```text
reviewed head — e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5
merge commit — 504e776508c940554b3ee8659a201af21db8303c
```

Accepted exact-head evidence: lifecycle checker PASS, A1 smoke PASS, 17 targeted
A1 tests, 514 C4-I Restore tests, 2415 backend+launcher tests and independent
audit P0=0 / P1=0 / P2=0.

A1 is **DONE — MERGED AND EXACT-HEAD VERIFIED** and remains the single
non-destructive candidate-preparation authority.

## A2 lifecycle authorization and current implementation

This post-A1 closure is not a new CR and does not change ADR 0018.

PR #175:

```text
reviewed head — b1a48d8f668fa984e3032f85c226f77e30d92e4e
merge commit — 636645ece744752f6a753ae5a25a05297fd34e10
```

A2 is now **IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED**. The current
runtime changeset is limited to the already-decided exact-run launcher
control/session protocol: loopback bind, Host/Origin, one-use bootstrap, run token,
no-store/CORS boundary, 15s/60s liveness, `command_seq`, concurrent worker
coordination, A1 invalidation and launcher lifetime wiring.

Production A2 uses typed `picker_unavailable` and obtains no filesystem path.
Browser/control request schema carries no path/file authority. Production browser
navigation remains unchanged and receives no bootstrap/session material before A4.

A2 still requires exact-head tests/smoke/audit and merge + post-merge lifecycle
closure before A3 can open.

## C4-II-B boundary

C4-II-B remains **PLANNED — NOT AUTHORIZED**. No C4-II-A slice may add
destructive execute/confirm authority, safety-copy creation, working-DB
replacement/migration, rollback/recovery mutation or Restore AuditLog.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger
can shorten their row. Preserve historical ledgers under `docs/history/` and keep
the protected pre-compaction snapshot byte-identical.
