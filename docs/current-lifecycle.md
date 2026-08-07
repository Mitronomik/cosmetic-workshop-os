# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-07`

This document is the compact authority for current implementation lifecycle,
authorization and PR sequencing. It does not replace durable product, domain,
API, safety or architecture contracts.

## Authority order

Resolve conflicts by **scope and recency**:

1. `AGENTS.md` and applicable nested `AGENTS.md` files;
2. the newest accepted ADR that explicitly supersedes or amends the exact topic;
3. this file for current lifecycle, authorization and PR sequencing;
4. accepted ADRs for durable product/safety/state-machine/architecture semantics
   that have not been superseded;
5. current normative architecture/profile documents;
6. `docs/c4-ii-a-implementation-slices.md` for the bounded C4-II-A implementation
   sequence when applicable;
7. `docs/implementation-plan.md`;
8. active `state/` files;
9. strategic/large reference documents;
10. `docs/history/` evidence.

For Restore:

- ADR 0016 remains authoritative for the launcher-assisted Restore product and
  safety contract, twelve phases, transition graph, startup recovery matrix,
  `replacement_intent`, destructive launcher ownership, immutable source,
  mandatory `before_restore` safety copy and AuditLog boundary;
- ADR 0017 remains authoritative for PR #170/C4-I lifecycle closure and the rule
  that CR-011 was decision-only rather than runtime implementation;
- ADR 0018 is authoritative for the CR-011 interaction/control/picker/
  validation-session architecture;
- `docs/c4-ii-a-implementation-slices.md` does **not** change ADR 0018; it only
  authorizes and sequences implementation of the accepted architecture;
- no lifecycle document may silently authorize C4-II-B destructive execution.

Historical evidence never authorizes runtime work.

## Current lifecycle

```text
PR #171 — MERGED
PR #172 — MERGED — CR-011 ACCEPTED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED
C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
C4 — ACTIVE
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

On the PR #173 authorization branch, the sliced C4-II-A authorization becomes
normative only after that changeset is present on `main`. PR #173 itself is
strictly documentation/lifecycle work and authorizes no runtime change on its own
branch.

## Verified merge baselines

### C4-I / PR #170

| Item | Value |
|---|---|
| Final independently reviewed head | `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8` |
| Merge commit | `e6997281d2e0268ce54184d988c114bac71c35e2` |

### Project-memory closure / PR #171

| Item | Value |
|---|---|
| Final reviewed head | `4978aa9a7c05117011eae1bc00276d5f98378d9b` |
| Merge commit | `76ab59216047222714a32f2793a789b3dc8df19a` |

### CR-011 / PR #172

| Item | Value |
|---|---|
| Final independently reviewed head | `c51d5baa07e4cd8912b1973649c22b20f581e3d2` |
| Merge commit | `998596560db6780a677bdec363d1fd19db30c1b6` |
| Merged at | `2026-08-07T12:57:28Z` |

PR #172 merge commit — `998596560db6780a677bdec363d1fd19db30c1b6`.
PR #172 changed documentation/state plus the documentation lifecycle checker
only. Its exact-head architecture gate closed with P0=0, P1=0, P2=0.

## Accepted CR-011 architecture

ADR 0018 selects:

```text
ordinary browser presentation
→ exact-run authenticated launcher-owned HTTP control plane on 127.0.0.1:<ephemeral>
→ launcher-owned macOS picker via /usr/bin/osascript
→ launcher-owned non-destructive validation session
→ accepted C4-I intake/staging/validation semantics
```

The architecture preserves path privacy, exact-run browser authentication,
non-destructive candidate validation, ordinary backend availability during
C4-II-A, and mandatory C4-II-B re-proof before destructive execution.

Normative architecture sources:

- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`;
- `docs/restore-interaction-and-validation-session.md`.

## C4-II-A implementation authorization

C4-II-A is authorized only through the bounded plan:

`docs/c4-ii-a-implementation-slices.md`.

Sequence:

```text
A1 validation-session core
→ A2 exact-run launcher control plane
→ A3 native macOS picker integration
→ A4 browser /backups/restore + end-to-end non-destructive flow
```

Only A1 is the immediate successor after PR #173 merges.

A2–A4 are not independently authorized to start early. Each requires its
predecessor to be independently reviewed, exact-head tested, merged, and current
lifecycle/project memory updated before a fresh branch is created from `main`.

## Current task — PR #173 authorization gate

PR #173 must remain documentation/lifecycle only.

Required sequence:

```text
record PR #172 merge
→ authorize only the sliced C4-II-A plan
→ make A1 the only immediate runtime successor
→ synchronize active state/status surfaces
→ run git diff --check
→ run scripts/check_documentation_lifecycle.py
→ verify docs/state/checker-only diff
→ fresh independent exact-head authorization audit
→ resolve every P0/P1/P2 finding
→ merge PR #173
```

Do not implement A1 on the unmerged PR #173 branch.
Do not create A1 from the PR #173 head before merge.

After PR #173 merges:

1. update `main`;
2. create a fresh A1 implementation branch from merged `main`;
3. implement only `C4-II-A1 — Validation-session core`;
4. keep A2/A3/A4 gated and C4-II-B not authorized.

## C4-II-A1 immediate authorized scope

A1 may implement only the launcher-owned non-destructive validation-session core:

- `prepare_restore_candidate(...)`-equivalent application boundary;
- shared-safe reuse/refactor of C4-I intake/staging/validation primitives;
- isolated user-only validation scratch;
- generation/stale/cancel/invalidation semantics;
- typed presentation-safe result model;
- launcher-private retained `SourceIdentity` + SHA-256 proof;
- bounded owned-only cleanup;
- tests and launcher/service-level exact-head smoke.

A1 must not implement control-plane HTTP, browser bootstrap/session tokens,
`command_seq`, native picker, frontend Restore UI, destructive confirmation,
`execute_restore(...)`, safety-copy creation, working-DB replacement/migration,
rollback/recovery mutation, Restore AuditLog, packaging or new dependencies.

## C4-II-B remains not authorized

No A1–A4 slice may add destructive authority.

C4-II-B remains responsible for later explicit confirmation and mandatory source
identity/digest re-proof, re-staging/revalidation, backend exclusion, safety-copy
creation and entry into the existing C4-I destructive execution boundary.

## Bounded supersession map

These older documents remain authoritative for durable architecture/safety
semantics but may contain pre-PR-173 lifecycle labels. Only those bounded status
labels are superseded by this file and the slice plan:

- `docs/decisions/0016-launcher-assisted-restore.md` — dated C4-I status only;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — dated
  CR-011 decision-gate status only;
- `docs/architecture.md` — dated C4 lifecycle status only;
- `docs/roadmap.md` — dated C4 lifecycle status only;
- `docs/backup-and-restore.md` — dated C4 lifecycle status only.

ADR 0018 remains authoritative for the selected interaction architecture. Its
statement that ADR 0018 itself does not authorize runtime remains true: runtime
authorization comes from this separate PR #173 lifecycle changeset and
`docs/c4-ii-a-implementation-slices.md`.

## Superseded lifecycle wording

Older accepted documents may still state that C4-II-A is `PLANNED — NOT
AUTHORIZED`. Those labels describe the pre-PR-173 lifecycle and do not override
this file once PR #173 is merged.

The architecture/safety semantics in those documents remain authoritative. Only
the bounded lifecycle/authorization wording is superseded by this profile and
`docs/c4-ii-a-implementation-slices.md`.

## Project history

Searchable history remains under `docs/history/` and is non-normative evidence.
The five protected pre-compaction snapshots remain byte-identical and must not be
edited.

## Documentation consistency check

Run from repository root:

```bash
python3 scripts/check_documentation_lifecycle.py
```

The checker must verify at least:

- PR #172 merged baseline;
- CR-011 accepted / ADR 0018 authority;
- sliced C4-II-A authorization;
- A1 is the only immediate implementation successor;
- A2/A3/A4 predecessor gates;
- C4-II-B remains not authorized;
- required A1 non-destructive boundaries;
- required history paths and five exact historical Git blob identities;
- no stale PR #171/#172 decision-branch action remains in compact active files;
- no unsafe executable historical `git restore --source=<old-commit>` guidance.

## Maintenance rule

A future lifecycle transition must update, in the same bounded PR, this file,
README, implementation plan, active state files, relevant compact ledger/status
surfaces and the documentation checker. Do not delete searchable history merely
because Git can recover an older commit.
