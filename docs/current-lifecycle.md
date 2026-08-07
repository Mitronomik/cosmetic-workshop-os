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
6. `docs/implementation-plan.md`;
7. active `state/` files;
8. strategic/large reference documents;
9. `docs/history/` evidence.

For Restore:

- ADR 0016 remains authoritative for the launcher-assisted Restore product and
  safety contract, twelve phases, transition graph, startup recovery matrix,
  `replacement_intent`, destructive launcher ownership, immutable source,
  mandatory `before_restore` safety copy and AuditLog boundary;
- ADR 0017 closes C4-I lifecycle and supersedes only dated C4 implementation
  status/authorization wording in ADR 0016;
- ADR 0018 is newer for the exact CR-011 interaction/validation-session topic and
  supersedes ADR 0017 only where ADR 0017 says CR-011 is still undecided or that
  C4-II-A is still blocked by the undecided CR-011 gate;
- ADR 0017 remains authoritative for PR #170/C4-I lifecycle closure and for the
  rule that CR-011 was decision-only rather than runtime authorization;
- ADR 0018 decides the interaction architecture: a narrowly authenticated
  launcher-owned loopback control plane, launcher-owned macOS picker, exact-run
  browser session and non-destructive validation-session boundary;
- ADR 0018 does not amend ADR 0016 safety semantics and does not authorize
  C4-II-A runtime work by itself.

Historical evidence never authorizes runtime work.

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
C4 — ACTIVE
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

On a CR-011 pull-request branch, ADR 0018 is the decided changeset but becomes
normative only when that changeset is present on `main`. No successor runtime
work may be based on the unmerged decision branch.

## Verified merge baselines

### C4-I / PR #170

| Item | Value |
|---|---|
| Final independently reviewed head | `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8` |
| Merge commit | `e6997281d2e0268ce54184d988c114bac71c35e2` |
| Merged at | `2026-08-03T16:12:23Z` |

### Project-memory closure / PR #171

| Item | Value |
|---|---|
| Final reviewed head | `4978aa9a7c05117011eae1bc00276d5f98378d9b` |
| Merge commit | `76ab59216047222714a32f2793a789b3dc8df19a` |
| Merged at | `2026-08-07T11:23:42Z` |

PR #171 preserved searchable project memory, exact historical snapshots and the
CR-011 decision gate. It changed no runtime path.

## CR-011 decision

ADR 0018 selects one architecture:

```text
ordinary browser presentation
→ authenticated launcher-owned HTTP control plane on 127.0.0.1:<ephemeral>
→ launcher-owned macOS picker
→ launcher-owned non-destructive validation session
→ existing C4-I intake/staging/validation semantics
```

Key constraints:

- control plane is separate from the ordinary FastAPI business API;
- no WebSocket or generic localhost command server;
- one exact frontend Origin; no wildcard CORS;
- one-use bootstrap capability enters through URL fragment, then is removed;
- run-scoped browser token is session-only and never durable;
- absolute selected-source path remains launcher-private;
- native picker is an owned `/usr/bin/osascript` child using Standard Additions
  `choose file`; no new application dependency is authorized;
- ordinary backend remains running during non-destructive C4-II-A validation;
- validation must reuse C4-I source intake, held-descriptor stability proof,
  staging and candidate validation;
- successful validation retains launcher-private source identity + SHA-256 proof,
  not a browser authority token;
- future C4-II-B must reopen, re-prove, restage and revalidate before destructive
  execution;
- temporary validation scratch is not a Restore operation and may never enter a
  durable Restore phase.

Normative decision:

- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.

Normative profile:

- `docs/restore-interaction-and-validation-session.md`.

## Current task and successor gate

The current CR-011 changeset is documentation/architecture only.

Before it may merge:

```text
finish documentation synchronization
→ run git diff --check
→ run scripts/check_documentation_lifecycle.py
→ run any repository-defined docs/link checker
→ verify no backend/frontend/launcher runtime path changed
→ perform a fresh independent exact-head architecture audit
→ resolve every P0/P1/P2 finding
→ merge the CR-011 decision PR
```

Do not implement C4-II-A on this branch.

After the CR-011 decision is merged to `main`, prepare a **separate bounded
lifecycle/implementation task** to authorize C4-II-A. ADR 0018 itself does not
authorize runtime implementation.

## C4-II-A remains not authorized

No agent may yet implement:

- Restore frontend controls or route behavior;
- launcher control-plane runtime code;
- native picker runtime code;
- `prepare_restore_candidate(...)` runtime service;
- validation scratch cleanup runtime code;
- C4-II-B destructive confirmation/execution;
- C4-II-C result UX;
- C4-III end-to-end closure;
- a new dependency or packaging implementation for Restore.

The next task must explicitly authorize a bounded C4-II-A implementation scope.

## Superseded lifecycle locations

These files retain valuable durable context but contain older lifecycle/status
wording that is superseded only for the bounded topic described here:

- `docs/decisions/0016-launcher-assisted-restore.md` — old C4-I branch status
  only; durable Restore safety/state-machine semantics remain authoritative;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — old
  `CR-011 NOT DECIDED` / `C4-II-A BLOCKED BY CR-011` status only; C4-I closure and
  decision-only gate semantics remain authoritative;
- `docs/architecture.md` — dated C4 implementation status only;
- `docs/roadmap.md` — dated C4 implementation status only;
- `docs/backup-and-restore.md` — dated C4 implementation status only.

Statements equivalent to these are historical/superseded as current lifecycle:

```text
C4-I — IMPLEMENTED ON PR BRANCH — NOT MERGED
C4-I — IMPLEMENTED ON PR BRANCH — SIXTH CORRECTION APPLIED — NOT MERGED
C4 implementation — NOT STARTED
C4-I — AUTHORIZED — NOT IMPLEMENTED
C4-I is implemented on a pull-request branch and not merged
CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED
C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
```

ADR 0016 supersession remains bounded to lifecycle metadata only. Its durable
Restore safety/state-machine contract remains authoritative.

ADR 0017 supersession is likewise bounded: ADR 0018 replaces only the undecided
CR-011 interaction-gate status and selected interaction architecture. ADR 0017's
C4-I closure facts and its prohibition on implicit runtime implementation remain
valid.

## Project history

Searchable history remains in the repository tree:

- `docs/history/README.md`;
- `docs/history/project-timeline-through-pr170.md`;
- `docs/history/c4-i-implementation-and-audit-history.md`;
- `docs/history/implementation-plan/2026-08-06-pre-compaction.md`;
- `docs/history/state-snapshots/2026-08-06-c4-i-closure/`;
- `docs/history/change-requests/2026-08-06-pre-compaction.md`.

These records are non-normative evidence. Exact pre-compaction snapshots must
remain byte-identical.

Historical commands are not automatically safe operational instructions. Use the
read-only archaeology guidance in `docs/history/README.md` and
`docs/history/AGENTS.md`.

## Documentation consistency check

Run from repository root:

```bash
python3 scripts/check_documentation_lifecycle.py
```

The checker must verify at least:

- post-PR-171 / CR-011 lifecycle markers across compact active files;
- ADR 0016 / 0017 / 0018 scope-and-recency authority;
- explicit bounded supersession of ADR 0017's pre-decision CR-011 status;
- ADR 0018 selected architecture markers;
- C4-II-A remains not authorized;
- required history paths and five exact historical Git blob identities;
- no stale pre-merge PR #171 action remains in compact active files;
- no unsafe executable historical `git restore --source=<old-commit>` guidance.

## Maintenance rule

A future lifecycle change must update, in the same bounded PR:

- this file;
- `README.md`;
- `docs/implementation-plan.md`;
- `state/current-focus.md`;
- `state/progress.md`;
- `state/handoff.md`;
- `state/change-requests.md` when a CR changes;
- every active status surface that would otherwise contradict the new lifecycle,
  or an explicit bounded supersession map.

Do not delete searchable historical records merely because Git can recover an
old commit.