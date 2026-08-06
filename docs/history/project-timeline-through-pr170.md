# Project timeline through PR #170

Status: **HISTORICAL — NON-NORMATIVE**
Updated: `2026-08-06`

This document is a searchable orientation layer for maintainers and agents. It
summarizes why the major implementation windows existed, what they delivered,
which constraints survived, and where deeper evidence lives. It is not a current
authorization document.

## 1. Product and architecture foundation

The project was defined as a local-first working system for a non-technical
cosmetic maker, not as a repository, generic admin panel, or recipe spreadsheet.
The durable architecture established:

- packaged local use on macOS without required internet;
- browser UI over a local API-first backend;
- business rules in backend/domain services rather than only in the frontend;
- SQLite user data stored outside application code and package contents;
- backup before migrations and safe update design;
- versioned recipes and first-class client-specific formulas;
- inventory through lots and movements;
- transactional production and immutable historical production data;
- imports through draft, preview, validation, confirmation, and apply;
- understandable UI for a non-technical user;
- no silent expansion into cloud sync, OCR, full accounting, roles,
  multi-user operation, or advanced analytics in the MVP.

Primary references:

- `AGENTS.md`;
- `docs/product-spec.md`;
- `docs/architecture.md`;
- `docs/domain-model.md`;
- `docs/roadmap.md`.

## 2. Agent-driven project memory

`CR-001` established the project-memory structure:

```text
AGENTS.md  — mandatory operating contract
docs/      — durable product, architecture, domain, and decision records
state/     — current progress, focus, handoff, and change requests
```

The intent was that a new agent could determine the product, constraints,
current phase, completed work, next bounded PR, and required tests without
reconstructing the project from issue and commit archaeology.

Primary references:

- `docs/codex-project-structure.md`;
- `docs/codex-prompting-rules.md`;
- `docs/pr-testing-and-smoke-rules.md`;
- `docs/smoke-script-authoring-rules.md`.

## 3. UI and operational hardening windows

The project completed a broad UI/UX and runtime-truth hardening sequence before
the C1–C4 completion window. The work included:

- shared action states, focus, disabled, danger, and feedback contracts;
- human-readable mutation and refresh failure handling;
- route-level responsive and keyboard verification;
- dashboard and onboarding operational behavior;
- local-artifact presentation that avoids developer paths as primary content;
- evidence-based acceptance or rejection of Hermes audit findings.

### Block B and the safe-GET pilot

Block B closed with a deliberately bounded Dashboard safe-GET timeout and
recovery pilot. The important historical limitation is that the same protection
was **not** automatically expanded to every read route. Alerts, Purchases,
Orders, Reports, Backups, Exports, and Report Documents remained outside that
pilot and require separately authorized work if later needed.

This limitation must not be erased by a broad refactor or interpreted as already
delivered coverage.

Primary historical detail:

- `docs/history/implementation-plan/2026-08-06-pre-compaction.md`;
- PRs through #141;
- `state/change-requests.md` entries `CR-002` and `CR-003`.

## 4. Backend baseline correction gate

After Block B, the full backend suite reproduced four deterministic failures.
The project did not treat all four as production defects automatically. It used
an evidence gate to distinguish test defects from undecided product contracts.

### R3 — purchase-suggestions smoke seeding

- test/setup defect;
- production behavior was not changed;
- API smoke was repaired so the intended no-mutation behavior was genuinely
  exercised.

### R2 — import date-normalization assertion

- test expectation defect;
- the existing normalization contract treated a normalized date as a warning,
  not an invalid date error;
- production import behavior was preserved.

### CR-005 and R4 — backup/export filename reason contract

The remaining two failures exposed an undecided filename grammar rather than an
automatically proven production defect. `CR-005` decided the canonical
filename-derived reason contract; `R4` then implemented and verified it.
Important retained rules include:

- separator runs collapse to one underscore;
- literal hyphens are not allowed in a new reason segment;
- numeric-only values receive `reason_`;
- Unicode alphanumerics are preserved;
- existing artifacts are not renamed or rewritten;
- API reason is canonical filename-derived authority;
- the frontend may localize known slugs but does not reconstruct them.

Primary references:

- `docs/backend-baseline-failure-triage.md`;
- `docs/backup-and-restore.md`;
- `docs/export.md`;
- `state/change-requests.md`;
- PRs #143–#146.

## 5. C1 — backend-owned tax-rate setting

`CR-007` decided the setting contract and `C1-I` implemented it in PR #149.
Load-bearing outcomes:

- canonical setting key `default_tax_rate`;
- percentage semantics, not coefficient semantics;
- `Decimal` and `ROUND_HALF_UP` boundaries;
- missing is unavailable, not fabricated zero;
- configured `0.00` is valid;
- setting changes do not recalculate historical production;
- UI and API expose understandable repair behavior;
- physical production must not be blocked solely by missing financial context.

Primary references:

- `docs/settings.md`;
- `AGENTS.md` financial rules;
- PRs #148–#149.

## 6. C2 — financial estimates and immutable snapshots

`CR-008` split financial completion into bounded slices.

### C2-I — readiness estimates

PR #151 added backend-owned tax, margin, and margin-percent estimates to the
existing production-readiness flow without a parallel endpoint or frontend
arithmetic.

### C2-II — transactional snapshots

PR #152 persisted immutable tax context and financial values in the production
transaction. Historical batches remain snapshot-backed and are never silently
recalculated from current settings.

### C2-III-A — presentation

PR #154 exposed order and production-batch financial results without moving
calculations into the frontend.

### C2-III-B — reports

PR #157 made reports and generated report documents read persisted snapshots
rather than applying the current tax setting retroactively.

Retained concerns include exact timestamp normalization, required-but-nullable
confirmation context, stale-context rejection, warning-code stability, negative
margin support, and no duplicate API aliases.

Primary references:

- `docs/decisions/0012-c2-financial-calculation-snapshots.md`;
- `docs/reports.md`;
- `docs/api.md`;
- PRs #150–#157.

## 7. C3 — AuditLog workspace and file-backed artifact semantics

### C3-I and C3-II-A

PR #159 delivered the read-only AuditLog workspace. PR #161 added atomic
workshop-profile coverage while preserving safe backend-owned display summaries
and avoiding raw sensitive metadata.

### CR-009 and C3-II-B1

`CR-009` decided durable partial-success semantics for file-backed artifacts.
PR #163 implemented the bounded ledger and report-document AuditLog coverage.
A verified artifact remains authoritative even if AuditLog persistence is
pending; this is not reported as total creation failure.

### CR-006 and C3-II-B2

`CR-006` confirmed a JSON-export create-response contract defect. PR #166 fixed
that response boundary and added JSON-export AuditLog coverage without a second
ledger or migration.

### CR-004 and C3-II-B3

`CR-004` proved that raw copying a live SQLite main file was unsafe: it could
omit committed WAL data, include mixed rollback-journal transaction state, or
produce corruption while integrity checks appeared reassuring. The accepted
replacement was the SQLite Online Backup API with bounded busy behavior.

PR #167 applied the safe backup engine and durable artifact-audit semantics to
manual backups.

### Artifact-finalization hardening

PR #168 separated three outcomes for report documents and JSON exports:

- `recorded`;
- `audit_pending`;
- `artifact_invalid`.

Only verified artifacts may be returned as created. Verification failure is not
mislabelled as merely pending AuditLog persistence.

Primary references:

- `docs/audit-log.md`;
- `docs/decisions/0013-file-backed-artifact-audit-semantics.md`;
- `docs/decisions/0014-json-export-create-confirmation-semantics.md`;
- `docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md`;
- `docs/backend-baseline-failure-triage.md`;
- PRs #159–#168.

## 8. C4 product decision

`CR-010` accepted launcher-assisted Restore:

- not a running FastAPI mutation;
- not an ordinary SPA filesystem mutation;
- whole-database Restore only;
- immutable selected source;
- complete staged validation before destructive mutation;
- verified `before_restore` safety copy;
- launcher-owned shutdown, replacement, verification, rollback, and startup
  recovery;
- no terminal requirement for the product user;
- no Restore AuditLog event without a separate decision.

Primary references:

- `docs/decisions/0016-launcher-assisted-restore.md`;
- `docs/backup-and-restore.md`.

## 9. C4-I implementation and six audit rounds

PR #170 implemented the launcher-owned Restore safety engine and merged at
`e6997281d2e0268ce54184d988c114bac71c35e2` from final reviewed head
`ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`.

Six independent audit rounds found and closed twenty-four findings:

```text
5 + 5 + 7 + 3 + 2 + 2 = 24
```

The detailed sequence is preserved in:

- `docs/history/c4-i-implementation-and-audit-history.md`.

The final engine preserved the accepted twelve-phase vocabulary, transition
graph, startup recovery matrix, `replacement_intent` crash rule, immutable
source, mandatory safety copy, backend exclusion, exact-child lock/socket proof,
retryable port collision handling, and no-FastAPI/no-SPA Restore boundary.

C4-I was internal infrastructure. It did not implement the user-facing Restore
flow.

## 10. Open obligations after PR #170

At the PR #170 merge baseline:

- user-facing Restore was not implemented;
- native file selection and interaction architecture were undecided;
- no public non-destructive validation-session service existed;
- macOS packaging was incomplete;
- safe packaged update flow was incomplete;
- installation verification was incomplete;
- full release-candidate smoke was incomplete;
- product release readiness was not claimed.

PR #171 later established that the next step must be a decision gate for the
launcher interaction and non-destructive validation-session boundary rather
than an implementation-by-assumption PR.

## 11. Evidence and deeper reconstruction

For complete pre-compaction project memory, read the exact snapshots under:

- `docs/history/implementation-plan/`;
- `docs/history/state-snapshots/`.

For code truth, inspect the relevant merged PR, final reviewed head, merge
commit, tests, and current implementation. Historical documentation explains
intent and evidence but never overrides current accepted decisions.
