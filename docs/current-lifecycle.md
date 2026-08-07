# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-07`

This document is the single compact authority for current implementation
lifecycle statements while older large documents are being incrementally
synchronized. It does not replace their product, domain, API, safety, or
architecture contracts.

## Authority order

Authority is evaluated by **scope and recency**, not by treating every accepted
ADR as globally newer than every lifecycle document.

When lifecycle or authorization wording conflicts, use this order:

1. `AGENTS.md` and applicable nested `AGENTS.md` files;
2. the newest accepted ADR that explicitly supersedes or amends an older
   decision for the exact topic in conflict;
3. this current lifecycle profile for current implementation status,
   authorization, and PR sequencing;
4. accepted ADRs for their durable product, safety, state-machine, and
   architecture decisions when those decisions have not been superseded;
5. current normative architecture/profile documents;
6. `docs/implementation-plan.md`;
7. active `state/` files;
8. strategic or large reference documents;
9. `docs/history/` evidence.

For Restore specifically:

- ADR 0016 remains authoritative for the accepted launcher-assisted Restore
  product and safety contract;
- ADR 0017 is the newer accepted lifecycle-closure decision and supersedes only
  dated C4 implementation-status / authorization wording in ADR 0016;
- ADR 0017 does **not** amend the twelve phases, transition graph, startup
  recovery matrix, `replacement_intent` rule, launcher ownership, immutable
  source rule, mandatory safety copy, or AuditLog boundary accepted by ADR 0016.

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

## PR #171 closure gate

While PR #171 is still open and unmerged, the current action is **not CR-011**.
The only permitted work on the PR #171 branch is to close PR #171 itself:

```text
finish the independent documentation/architecture audit
→ correct every finding
→ run the required documentation checks in a real checkout
→ repeat the exact-head read-only gate
→ merge PR #171
```

Do not start CR-011 from the unmerged PR #171 branch.
Do not create a dependent CR-011 branch from the PR #171 head.

## Only authorized successor after PR #171 merges

After PR #171 is merged, update local `main` and create a new branch from that
merged `main`. Only then begin:

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

The following documents retain valuable product, safety, architecture, and
historical context but contain dated branch-era C4 lifecycle/status wording:

- `docs/decisions/0016-launcher-assisted-restore.md`;
- `docs/architecture.md`;
- `docs/roadmap.md`;
- `docs/backup-and-restore.md`.

Within those files, statements equivalent to any of the following are
**historical and superseded by ADR 0017 and this lifecycle profile**:

```text
C4-I — IMPLEMENTED ON PR BRANCH — NOT MERGED
C4-I — IMPLEMENTED ON PR BRANCH — SIXTH CORRECTION APPLIED — NOT MERGED
C4 implementation — NOT STARTED
C4-I — AUTHORIZED — NOT IMPLEMENTED
C4-I is implemented on a pull-request branch and not merged
```

For ADR 0016 this supersession applies **only** to dated implementation lifecycle
and authorization labels. Its accepted Restore product, safety, state-machine,
and recovery semantics remain authoritative unless a later accepted ADR changes
them explicitly.

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

Historical commands are not automatically safe operational instructions. For
read-only Git archaeology, use the safe guidance in `docs/history/README.md` and
`docs/history/AGENTS.md`.

## Documentation consistency check

Run from the repository root:

```bash
python3 scripts/check_documentation_lifecycle.py
```

The check must verify:

- current lifecycle markers across compact active control files;
- explicit PR #171 → merged `main` → CR-011 sequencing;
- CR-011 ledger state;
- preserved history paths and expected Git blob identities;
- explicit supersession of dated C4 lifecycle wording, including ADR 0016;
- absence of unsafe `git restore --source=` guidance from maintained historical
  guidance files.

## Maintenance rule

A future lifecycle change must update, in the same documentation PR:

- this file;
- `README.md`;
- `docs/implementation-plan.md`;
- `state/current-focus.md`;
- `state/progress.md`;
- `state/handoff.md`;
- `state/change-requests.md` when a CR changes;
- every active status surface whose current-status section would otherwise
  contradict the new lifecycle, or this explicit supersession map until that
  focused synchronization is completed.

Do not delete searchable historical records merely because Git can recover an
old commit.