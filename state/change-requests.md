# Change Requests

Updated: `2026-08-08`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger is preserved byte-for-byte at
`docs/history/change-requests/2026-08-06-pre-compaction.md`. Historical evidence
does not override current lifecycle or authorization.

## Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — AUTHORIZED NEXT — NOT IMPLEMENTED
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

PR #173 is not a new architecture/change request. It fixes the implementation
order already selected by CR-011:

```text
A1 — validation-session core
→ A2 — exact-run launcher control plane
→ A3 — native picker integration
→ A4 — browser Restore screen
```

## A1 closure evidence

PR #174 completed A1 at reviewed head
`e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`, merged as
`504e776508c940554b3ee8659a201af21db8303c`, with lifecycle/smoke PASS,
17 A1 tests, 514 C4-I tests, 2415 full tests and audit 0/0/0.

A1 remains the single non-destructive candidate-preparation authority.

## A2 closure evidence

PR #175 authorized A2 from merge
`636645ece744752f6a753ae5a25a05297fd34e10`.

PR #176 completed A2:

```text
reviewed head — 681cb4050bec082db6b637285590e232880af739
merge commit — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
```

Accepted exact-head evidence: lifecycle PASS, stale-A1-authority race 2 passed,
A2 targeted 28 passed, A1 17 passed, C4-I Restore 514 passed, full
backend+launcher 2443 passed, exact-head A2 smoke PASS and independent audit
P0=0 / P1=0 / P2=0.

A2 is **DONE — MERGED AND EXACT-HEAD VERIFIED**.

## A3 lifecycle authorization

This post-A2 closure is not a new CR and does not change ADR 0018.

A3 is now **AUTHORIZED NEXT — NOT IMPLEMENTED**. It may implement only the
launcher-owned native macOS picker already selected by CR-011/ADR 0018:

- `/usr/bin/osascript` + Standard Additions `choose file`;
- fixed script, no user-controlled interpolation;
- no `shell=True`, no `System Events`;
- typed cancellation;
- absolute POSIX path only in launcher memory;
- owned child terminate/wait on cancel/expiry;
- existing A2 source-selection adapter → existing A1 validation;
- no new dependency.

A3 may not add browser path/file authority, `/backups/restore`, production
bootstrap-fragment handoff or destructive Restore authority.

## C4-II-B boundary

C4-II-B remains **PLANNED — NOT AUTHORIZED**. No C4-II-A slice may add
destructive execute/confirm authority, safety-copy creation, working-DB
replacement/migration, rollback/recovery mutation or Restore AuditLog.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger
can shorten their row. Preserve historical ledgers under `docs/history/` and keep
the protected pre-compaction snapshot byte-identical.
