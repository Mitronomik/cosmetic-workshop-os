# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-06`

This document is the single compact authority for current implementation
lifecycle statements while older large documents are being incrementally
synchronized. It does not replace their product, domain, API, or architecture
contracts.

## Authority order

When lifecycle or authorization wording conflicts, use this order:

1. `AGENTS.md` and applicable nested `AGENTS.md` files;
2. accepted ADRs;
3. this current lifecycle profile;
4. current normative architecture/profile documents;
5. `docs/implementation-plan.md`;
6. active `state/` files;
7. strategic or large reference documents;
8. `docs/history/` evidence.

Historical evidence never authorizes runtime work.

## Current lifecycle

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED

CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED

CR-011 — Launcher Restore interaction and validation-session boundary
— AUTHORIZED — DECISION ONLY — NOT DECIDED

C4-II-A — Launcher Restore source selection and validation presentation
— PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED

C4-II-B — Explicit confirmation and Restore execution
— PLANNED — NOT AUTHORIZED

C4-II-C — Completion, rollback and support-assisted outcome UX
— PLANNED — NOT AUTHORIZED

C4-III — Restore end-to-end verification and lifecycle closure
— PLANNED — NOT AUTHORIZED

C4 — ACTIVE
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## Verified C4-I merge facts

| Item | Value |
|---|---|
| Pull request | `#170 — C4-I — Implement launcher-owned Restore safety engine` |
| Final independently reviewed and exact-head-tested head | `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8` |
| Merge commit on `main` | `e6997281d2e0268ce54184d988c114bac71c35e2` |
| Merged at | `2026-08-03T16:12:23Z` |
| Additional file changes introduced by merge commit | none |

C4-I is internal launcher infrastructure. It does not provide the product file
picker, validation screen, destructive confirmation, Restore execution UX,
terminal outcome UX, ordinary FastAPI Restore endpoint, or ordinary SPA Restore
mutation.

## Only authorized next task

```text
CR-011 — Decide the launcher Restore interaction and validation-session boundary.
Decision-only. No runtime implementation is authorized.
```

CR-011 must choose one concrete architecture for:

- screen location and owning process;
- native macOS picker ownership;
- any browser-to-launcher command path;
- exact-run authentication, origin, replay, stale-session, and duplicate-action
  protection;
- absolute-path privacy;
- backend lifecycle during selection and validation;
- dependencies and packaging consequences;
- cancellation, reselection, shutdown, interrupted-session cleanup, and
  exact-head smoke;
- the launcher-owned non-destructive candidate-preparation boundary.

Current normative C4 references:

- `docs/decisions/0016-launcher-assisted-restore.md`;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`;
- `docs/restore-interaction-and-validation-session.md`;
- `docs/implementation-plan.md`.

## Superseded lifecycle locations

The following large documents retain valuable product and architecture content,
but contain dated branch-era C4 status paragraphs written before PR #170 merged:

- `docs/architecture.md`;
- `docs/roadmap.md`;
- `docs/backup-and-restore.md`.

Within those files, statements equivalent to any of the following are
**historical and superseded**:

```text
C4-I — IMPLEMENTED ON PR BRANCH — NOT MERGED
C4 implementation — NOT STARTED
C4-I — AUTHORIZED — NOT IMPLEMENTED
C4-I is implemented on a pull-request branch and not merged
```

Their product contracts, safety rules, accepted decisions, detailed C4-I engine
description, and historical evidence remain valuable and are not revoked.
Only their lifecycle labels are superseded by this document, ADR 0017, and the
active implementation plan.

No agent may use a superseded status sentence to reopen C4-I, repeat PR #170,
or authorize C4-II runtime work.

## Project history

Searchable history is retained in the current repository tree:

- `docs/history/README.md`;
- `docs/history/project-timeline-through-pr170.md`;
- `docs/history/c4-i-implementation-and-audit-history.md`;
- `docs/history/implementation-plan/2026-08-06-pre-compaction.md`;
- `docs/history/state-snapshots/2026-08-06-c4-i-closure/`;
- `docs/history/change-requests/2026-08-06-pre-compaction.md`.

These files are non-normative evidence. They preserve the reasons, audit rounds,
known limitations, exact test evidence, slice contracts, and branch-era state
without polluting the active short-horizon documents.

## Documentation consistency check

Run from the repository root:

```bash
python3 scripts/check_documentation_lifecycle.py
```

The check verifies the current lifecycle markers, CR-011 ledger entry, preserved
history paths, and absence of stale C4-I status phrases from compact active
control documents. Large legacy documents are permitted to retain dated status
prose only because they are explicitly listed in this profile.

## Maintenance rule

A future lifecycle change must update, in the same documentation PR:

- this file;
- `README.md`;
- `docs/implementation-plan.md`;
- `state/current-focus.md`;
- `state/progress.md`;
- `state/handoff.md`;
- `state/change-requests.md` when a CR changes;
- every large active document whose current-status section would otherwise
  contradict the new lifecycle, or this explicit supersession map until that
  focused synchronization is completed.

Do not delete searchable historical records merely because Git can recover an
old commit.
