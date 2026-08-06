# Current focus — C4-I closed; C4-II-A authorized

Updated: `2026-08-06`

> This file is the current authoritative short-horizon status. The detailed
> branch-era journal previously stored here remains available in Git history at
> parent commit `e6997281d2e0268ce54184d988c114bac71c35e2`.

## Current lifecycle

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED

C4-I — Launcher-owned restore safety engine
— DONE — MERGED AND EXACT-HEAD VERIFIED
— PR #170
— final reviewed head ac95e2990efa979b3ded6cb48f91ddd0750aa7c8
— merge commit e6997281d2e0268ce54184d988c114bac71c35e2

C4-II-A — Launcher Restore source selection and validation presentation
— AUTHORIZED — NOT IMPLEMENTED

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
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## Verified C4-I closure

PR #170 merged the internal launcher-owned Restore safety engine. The exact
independently reviewed and smoke-tested implementation head was
`ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`; it is a parent of merge commit
`e6997281d2e0268ce54184d988c114bac71c35e2` on `main`. The merge added no
additional file change beyond the reviewed head.

C4-I remains internal infrastructure. It added no user-facing file picker,
validation screen, destructive confirmation, Restore action, completion screen,
FastAPI Restore endpoint, ordinary SPA mutation or Restore AuditLog event.
Therefore user-facing Restore remains `NOT IMPLEMENTED`.

The accepted ADR 0016 contract is unchanged: exactly twelve phases, the same
transition graph, the same recovery matrix, `phase` as the sole authoritative
lifecycle field and the same `replacement_intent` crash rule.

## Current next action

Implement one bounded runtime pull request:

```text
C4-II-A — Launcher Restore source selection and validation presentation
```

### Goal

Allow a non-technical user to select one local SQLite backup through the
launcher/application shell, run the existing C4-I staging and validation
contracts, and understand the selected backup or the reason it cannot be used —
without executing Restore or mutating the working database.

### Authorized scope

- launcher-owned local file selection;
- exactly one local SQLite backup source;
- invocation of the existing C4-I staging and candidate-validation boundaries;
- human-readable selected-backup information that can be established safely;
- human-readable validation progress, success and rejection outcomes;
- fixed non-technical messages with technical detail confined to local logs;
- keyboard-accessible interaction and understandable focus behaviour;
- narrow-viewport behaviour where the launcher/application shell supports it;
- focused tests and an exact-head smoke appropriate to this non-destructive slice.

### Non-goals

- no call to `execute_restore(...)`;
- no `before_restore` safety copy;
- no working-database replacement or migration;
- no rollback or recovery-state mutation;
- no destructive confirmation yet;
- no success, rollback-completed or support-assisted terminal outcome flow;
- no FastAPI Restore endpoint;
- no ordinary SPA-owned Restore mutation;
- no Restore AuditLog event;
- no state-machine, phase, transition or recovery-matrix change;
- no packaging, updater or release-readiness claim;
- no C4-II-B, C4-II-C or C4-III implementation.

### Architecture constraints

The launcher remains the owner of filesystem access, staging and validation.
The frontend/application shell may present typed results but must not parse
SQLite, migration history, raw paths, SQL errors or stack traces, and must not
reimplement validation. Validation failure must never make a destructive action
available. The selected source remains immutable read-only input.

### Required evidence

- existing C4-I tests remain collected and green;
- focused tests cover valid current-schema backup, valid older supported backup,
  corrupt file, foreign SQLite, newer schema, non-file, symlink/path escape and
  source immutability;
- selection cancellation and replacement of a previous selection are safe;
- no working-database byte, Restore operation record, safety copy or AuditLog row
  is created by the presentation flow;
- keyboard and focus behaviour are covered;
- `git diff --check` is clean;
- exact-head smoke uses isolated temporary user data and does not claim full
  Restore or release smoke.

## Explicitly not authorized next

C4-II-B, C4-II-C and C4-III remain planned only. No agent may begin destructive
Restore execution, outcome UX or lifecycle closure from this documentation PR or
from the merged PR #170 branch.
