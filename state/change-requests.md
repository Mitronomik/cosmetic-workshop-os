# Change Requests

Updated: `2026-08-07`
Status: **CURRENT COMPACT LEDGER**

The complete pre-compaction ledger is preserved byte-for-byte at:

`docs/history/change-requests/2026-08-06-pre-compaction.md`

That snapshot is historical evidence and does not override current lifecycle or
authorization.

## Current lifecycle

```text
PR #171 — MERGED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — DECIDED — ADR 0018 ACCEPTED — NORMATIVE ON MAIN
C4-II-A — PLANNED — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

Current authority:

- `docs/current-lifecycle.md`;
- newest accepted ADR for the exact topic;
- `docs/implementation-plan.md`.

On a CR-011 PR branch, ADR 0018 becomes normative project authority only after
the changeset is merged to `main`.

## Ledger

| ID | Date | Request | Current status | Durable record / outcome |
|---|---|---|---|---|
| CR-001 | 2026-06-21 | Add Codex project-memory structure | accepted and in use | `docs/codex-project-structure.md`; establishes `AGENTS.md`, durable `docs/`, active `state/`, and bounded PR workflow. |
| CR-002 | 2026-07-26 | Close B4 with Dashboard safe-GET pilot only | accepted and implemented | Dashboard timeout/recovery pilot delivered; expansion to other read routes was deliberately deferred and requires separate authorization. Historical contract in preserved implementation plan. |
| CR-003 | 2026-07-26 | Open backend baseline correction gate | accepted and completed | Four deterministic failures classified/closed through R2, R3, CR-005 and R4; `docs/backend-baseline-failure-triage.md`. |
| CR-004 | 2026-07-26 | Investigate SQLite backup transaction consistency | accepted and implemented | `PRODUCT DEFECT — BACKUP CONSISTENCY`, severity HIGH; raw live-file copy replaced by SQLite Online Backup API. ADR 0015. |
| CR-005 | 2026-07-27 | Decide backup/export filename reason contract | accepted and implemented | Canonical filename-derived reason grammar implemented by R4 / PR #146; legacy artifacts not renamed. `docs/backup-and-restore.md`, `docs/export.md`. |
| CR-006 | 2026-07-29 | Decide JSON export create-response confirmation semantics | accepted and implemented | Product defect corrected with JSON-export AuditLog coverage in PR #166. ADR 0014. |
| CR-007 | 2026-07-27 | Decide backend-owned workshop tax-rate setting | accepted and implemented | `default_tax_rate`, Decimal semantics, no silent historical recalculation; PRs #148–#149. `docs/settings.md`. |
| CR-008 | 2026-07-27 | Decide financial estimates and immutable production snapshots | accepted and implemented | C2-I, C2-II, C2-III-A and C2-III-B completed through PR #157. ADR 0012. |
| CR-009 | 2026-07-30 | Decide durable file-backed artifact AuditLog semantics | accepted and implemented | Shared bounded ledger and truthful artifact-audit semantics implemented through PRs #163/#166/#167/#168. ADR 0013. |
| CR-010 | 2026-08-02 | Decide launcher-assisted Restore semantics | accepted; C4-I implemented; product Restore incomplete | ADR 0016 accepted. Internal C4-I safety engine merged in PR #170; user-facing Restore remains not implemented. |
| CR-011 | 2026-08-06 | Decide launcher Restore interaction and non-destructive validation-session boundary | **decided — ADR 0018 accepted in changeset; normative on main only** | Selected launcher-owned authenticated loopback control plane + launcher-owned `/usr/bin/osascript` picker + exact-run browser session + launcher-owned non-destructive validation service. C4-II-A remains not authorized. `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`. |

## CR-011 accepted architecture

When ADR 0018 is present on `main`, CR-011 is closed as a decision.

Selected:

```text
ordinary browser presentation
→ authenticated launcher-owned HTTP control plane
  127.0.0.1:<ephemeral>
→ launcher-owned /usr/bin/osascript native picker
→ launcher-owned non-destructive validation session
→ existing C4-I intake/staging/validation semantics
```

Key outcomes:

- ordinary FastAPI backend is not the Restore control plane;
- no WebSocket and no generic localhost command server;
- no new application dependency;
- exact local frontend Origin; no wildcard CORS;
- one-use bootstrap capability + run-scoped browser session token;
- absolute selected-source path remains launcher-private;
- ordinary backend remains running during non-destructive candidate validation;
- C4-II-A must reuse C4-I source intake, held-descriptor stability proof,
  staging and candidate validation;
- temporary validation candidate is deleted after validation;
- launcher retains source identity + SHA-256 proof in memory only;
- future C4-II-B must reopen/re-prove, restage and revalidate before destructive
  execution.

## Current gate

The CR-011 changeset itself must remain documentation/architecture only.

Before merge:

```text
git diff --check
python3 scripts/check_documentation_lifecycle.py
docs/link checker if repository defines one
verify no backend/frontend/launcher runtime path changed
fresh independent exact-head architecture audit
P0=0, P1=0, P2=0
```

## Successor rule

CR-011 decision acceptance does **not** authorize C4-II-A runtime work.

After CR-011 merges:

1. update `main`;
2. create a fresh branch from merged `main`;
3. prepare a separate bounded lifecycle/implementation task that explicitly
   authorizes C4-II-A;
4. keep C4-II-B/C4-II-C/C4-III not authorized.

## History policy

Detailed accepted decisions are never deleted merely because the compact ledger
can shorten their row. Preserve complete older ledgers under
`docs/history/change-requests/` before future compaction.