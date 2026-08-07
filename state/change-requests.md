# Change Requests

Updated: `2026-08-07`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger is preserved byte-for-byte at
`docs/history/change-requests/2026-08-06-pre-compaction.md`. Historical evidence
does not override current lifecycle or authorization.

## Current lifecycle

```text
PR #173 — MERGED — C4-II-A SLICED AUTHORIZATION
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
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

## C4-II-A implementation authorization

PR #173 is **not** a new architecture/change request. It is the separate lifecycle
authorization required by CR-011.

```text
PR #173 reviewed head — 9f5722c5dec695588596d45daa5588092ce7f080
PR #173 merge commit — aaedf2735660fb92eb627f7eeab327437d459b56
```

The accepted sequence remains:

```text
A1 — validation-session core
→ A2 — exact-run launcher control plane
→ A3 — native picker integration
→ A4 — browser Restore screen
```

## Current A1 implementation status

A1 is implemented in the current changeset but is not yet closed. It adds the
launcher-owned non-destructive candidate-preparation service, private validation
scratch, typed results, generation/cancel/reselection semantics, retained
`SourceIdentity` + SHA-256 proof, targeted tests and exact-head service smoke.

It reuses existing C4-I intake/staging/validation and adds no duplicate staging
algorithm.

A1 does **not** add HTTP control, browser bootstrap/session, `command_seq`, native
picker, frontend Restore UI, durable Restore state, safety-copy creation,
working-DB replacement/migration, rollback/recovery or Restore AuditLog.

A1 closure still requires exact-head tests/smoke/audit and merge evidence.

## Successor rule

A2 is not an implicit follow-up from an unmerged A1 branch. It remains blocked
until A1 merges, exact-head verification is accepted and lifecycle/project memory
is updated from `main`.

C4-II-B remains **PLANNED — NOT AUTHORIZED**. No C4-II-A slice may gain
destructive execute/confirm authority.

## History policy

Detailed accepted decisions are never deleted merely because this compact ledger
can shorten their row. Preserve historical ledgers under `docs/history/` and keep
the protected pre-compaction snapshot byte-identical.
