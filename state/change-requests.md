# Change Requests

Updated: `2026-08-06`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger is preserved byte-for-byte at:

`docs/history/change-requests/2026-08-06-pre-compaction.md`

That snapshot contains dated lifecycle wording and detailed evidence that remain
valuable as history but do not override current status. Durable decisions remain
in their ADR and profile documents.

## Current lifecycle

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED
C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

Current lifecycle authority:

- `docs/current-lifecycle.md`;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`;
- `docs/implementation-plan.md`.

## Ledger

| ID | Date | Request | Current status | Durable record / outcome |
|---|---|---|---|---|
| CR-001 | 2026-06-21 | Add Codex project-memory structure | accepted and in use | `docs/codex-project-structure.md`; establishes `AGENTS.md`, durable `docs/`, active `state/`, and bounded PR workflow. |
| CR-002 | 2026-07-26 | Close B4 with Dashboard safe-GET pilot only | accepted and implemented | Dashboard timeout/recovery pilot delivered; expansion to other read routes was deliberately deferred and requires a separate authorization. Historical contract in the preserved implementation plan. |
| CR-003 | 2026-07-26 | Open backend baseline correction gate | accepted and completed | Four deterministic failures were classified and closed through R2, R3, CR-005, and R4; `docs/backend-baseline-failure-triage.md`. |
| CR-004 | 2026-07-26 | Investigate SQLite backup transaction consistency | accepted and implemented | Classified `PRODUCT DEFECT — BACKUP CONSISTENCY`, severity `HIGH`; raw live-file copy replaced by SQLite Online Backup API. `docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md`. |
| CR-005 | 2026-07-27 | Decide backup/export filename reason contract | accepted and implemented | Canonical filename-derived reason grammar implemented by R4 / PR #146; legacy artifacts are not renamed. `docs/backup-and-restore.md`, `docs/export.md`. |
| CR-006 | 2026-07-29 | Decide JSON export create-response confirmation semantics | accepted and implemented | Product defect confirmed and corrected with JSON-export AuditLog coverage in PR #166. `docs/decisions/0014-json-export-create-confirmation-semantics.md`. |
| CR-007 | 2026-07-27 | Decide backend-owned workshop tax-rate setting | accepted and implemented | `default_tax_rate`, Decimal percentage semantics, no silent historical recalculation; PRs #148–#149. `docs/settings.md`. |
| CR-008 | 2026-07-27 | Decide financial estimates and immutable production snapshots | accepted and implemented | C2-I, C2-II, C2-III-A, and C2-III-B completed through PR #157. `docs/decisions/0012-c2-financial-calculation-snapshots.md`. |
| CR-009 | 2026-07-30 | Decide durable file-backed artifact AuditLog semantics | accepted and implemented | Shared bounded ledger and truthful `recorded` / `audit_pending` / `artifact_invalid` semantics implemented through PRs #163, #166, #167, and #168. `docs/decisions/0013-file-backed-artifact-audit-semantics.md`. |
| CR-010 | 2026-08-02 | Decide launcher-assisted Restore semantics | accepted; C4-I implemented; product Restore incomplete | ADR 0016 accepted. Internal C4-I safety engine merged in PR #170; user-facing Restore remains not implemented. `docs/decisions/0016-launcher-assisted-restore.md`. |
| CR-011 | 2026-08-06 | Decide launcher Restore interaction and non-destructive validation-session boundary | **authorized — decision only — not decided** | Only authorized next task. Must select one screen/picker/command-channel/security/process/packaging architecture and define launcher-owned candidate preparation. No runtime implementation is authorized. ADR 0017 and `docs/restore-interaction-and-validation-session.md`. |

## CR-011 decision gate

CR-011 must decide one concrete architecture for:

- where the user-facing C4-II-A screen lives and which process owns it;
- which process opens the native macOS picker;
- how a browser action, if any, reaches the launcher;
- exact-run authentication, origin, token, replay, stale-session, and duplicate
  action protection;
- absolute source-path privacy;
- backend lifecycle during source selection and validation;
- allowed dependencies and packaging consequences;
- cancellation, reselection, launcher exit, interrupted-session cleanup, and
  isolated exact-head smoke;
- one launcher-owned, non-destructive candidate-preparation boundary.

Before CR-011 is accepted, no agent may implement:

- C4-II-A, C4-II-B, C4-II-C, or C4-III;
- a native picker;
- launcher IPC, WebSocket, or loopback control service;
- an ordinary FastAPI Restore endpoint;
- SPA-owned filesystem access;
- browser upload/blob transfer as authoritative Restore source;
- a validation-session Python service;
- Restore packaging changes;
- destructive Restore execution.

## History policy

A detailed accepted decision is never deleted merely because its lifecycle row
can be shortened. When this ledger is compacted again, preserve the complete
previous version under `docs/history/change-requests/` and keep this active file
limited to current status, durable references, open gates, and load-bearing
outcomes.
