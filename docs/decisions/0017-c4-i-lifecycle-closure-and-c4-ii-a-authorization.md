# ADR — C4-I lifecycle closure and C4-II-A authorization

## Status

`ACCEPTED` — 2026-08-06.

This record closes the lifecycle of merged `C4-I` and authorizes exactly one
next bounded runtime slice: `C4-II-A`.

It does **not** amend `CR-010` or
`docs/decisions/0016-launcher-assisted-restore.md`. The accepted twelve phases,
transition graph, recovery matrix, `replacement_intent` crash rule, launcher
ownership and AuditLog boundary remain unchanged.

Earlier branch-era lifecycle statements that describe PR #170 as open, draft,
unmerged or awaiting another audit are historical for their date and are
superseded by this record. Their product contracts and evidence remain intact in
Git history.

## Verified merge facts

| Item | Verified value |
|---|---|
| Pull request | `#170 — C4-I — Implement launcher-owned Restore safety engine` |
| State | `MERGED` |
| Final independently reviewed and exact-head-tested implementation head | `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8` |
| Merge commit on `main` | `e6997281d2e0268ce54184d988c114bac71c35e2` |
| Relationship | the reviewed head is a parent of the merge commit |
| Additional file changes introduced by merge commit | none |

The accepted exact-head test, audit and smoke evidence belongs to PR #170 and is
not re-executed by this documentation-only lifecycle closure.

## Current lifecycle

```text
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

## Why C4-I closure does not mean Restore is implemented

C4-I is internal launcher infrastructure. It implements staging, validation,
durable Restore operation state, safety-copy orchestration, replacement,
rollback, verification and startup recovery boundaries for later use.

It deliberately exposes no user-facing file picker, selected-backup screen,
validation presentation, destructive confirmation, Restore action, progress
screen, completion screen, rollback-completed screen or support-assisted outcome
screen. It adds no running-backend Restore endpoint and no ordinary SPA Restore
mutation. Therefore user-facing Restore remains `NOT IMPLEMENTED`.

## Unchanged CR-010 / ADR 0016 invariants

Later work must preserve all of the following:

- Restore is launcher-assisted;
- the ordinary backend is stopped for destructive replacement;
- the selected source is immutable read-only input;
- Restore is whole-database only;
- staging and candidate validation complete before mutation of the working
  database;
- a verified `before_restore` safety copy is mandatory before replacement;
- exactly twelve phases exist:
  `prepared`, `source_staged`, `candidate_validated`, `safety_copy_verified`,
  `replacement_intent`, `replacement_committed`, `verification_in_progress`,
  `completed`, `aborted`, `rollback_in_progress`, `rolled_back`,
  `recovery_blocked`;
- `phase` is the sole authoritative lifecycle field;
- the transition graph and startup recovery matrix are unchanged;
- `replacement_intent` is durably recorded before the replacement boundary and
  is treated conservatively after interruption;
- terminal records are not reactivated;
- `rolled_back` is failed Restore, never successful Restore;
- `recovery_blocked` never permits ordinary startup;
- the ordinary browser opens only after durable `completed`;
- no Restore AuditLog event is authorized;
- no FastAPI Restore mutation is authorized;
- no SPA-owned filesystem replacement or locking mechanism is authorized;
- technical details remain in local logs rather than ordinary user-facing text.

## Decision: split C4-II before implementation

The user-facing flow is not one bounded reviewable change. It is split into
three sequential runtime slices. Only the first is authorized here.

### C4-II-A — Launcher Restore source selection and validation presentation

```text
AUTHORIZED — NOT IMPLEMENTED
```

#### Goal

Provide the safe non-destructive first half of the Restore workflow:

```text
select one local SQLite backup
→ stage and validate it through existing C4-I contracts
→ show understandable backup information or a rejection
```

No current workshop data is replaced or migrated in this slice.

#### Scope

- launcher-owned native/local file selection;
- selection of exactly one local regular SQLite backup source;
- safe cancellation with no state mutation;
- invocation of existing C4-I source-staging and candidate-validation
  boundaries rather than a second validation implementation;
- human-readable selected-backup information that can be established safely;
- human-readable validation progress;
- success presentation for a valid current-schema backup;
- success presentation for a valid older supported backup, without executing its
  later migration;
- rejection presentation for corrupt, empty, foreign, newer-schema, non-file,
  symlink and path-escape inputs;
- fixed non-technical messages with technical detail confined to local logs;
- safe replacement of a previous selection;
- stale-result rejection when a later selection supersedes earlier validation;
- duplicate-action protection;
- visible keyboard focus, accessible naming and understandable navigation;
- supported narrow-viewport presentation where applicable;
- focused automated tests and exact-head isolated smoke for this non-destructive
  slice.

#### Architecture constraints

- The launcher/application shell owns local file selection.
- C4-I remains the sole owner of staging and candidate validation.
- The presentation layer consumes typed results and performs no SQLite parsing,
  migration-lineage analysis or business validation.
- Raw SQL, migration IDs, internal absolute paths, stack traces and SQLite errors
  are not shown in ordinary UI.
- The selected source remains byte-identical and is never renamed, migrated,
  deleted or rewritten.
- Validation failure must never make a destructive confirmation or execution
  action available.
- A filename or extension is never sufficient validation authority.
- Local-first operation requires no network service or upload.

#### Backend requirements

No ordinary FastAPI Restore endpoint is expected or authorized. Existing
read-only backend helpers may be reused only through the launcher-owned C4-I
boundary. No business repository write, schema change, migration or AuditLog event
is authorized.

#### Frontend/application-shell requirements

- show only human-readable source information that can be proved safely;
- tie validation progress and result ownership to the exact current selection;
- do not reconstruct validation from filenames or file extensions;
- do not calculate or infer schema compatibility;
- distinguish cancellation, validation rejection and technical presentation
  failure;
- never imply that Restore has executed;
- never show a success message equivalent to «Данные восстановлены»;
- do not expose developer paths, raw JSON or repository terminology.

#### Tests

At minimum, prove:

1. selection cancellation creates no operation and changes no data;
2. a valid current-schema application backup is accepted;
3. a valid older supported backup is accepted for later execution;
4. a newer unsupported schema is rejected;
5. a foreign healthy SQLite database is rejected;
6. an empty file is rejected;
7. a corrupt database is rejected;
8. a directory is rejected;
9. a symlink or path escape is rejected;
10. the original selected source remains byte-identical after success and every
    rejection path;
11. validation creates no `before_restore` safety copy;
12. validation does not replace, migrate or otherwise mutate the working
    database;
13. validation does not create a Restore AuditLog row;
14. a later selection supersedes stale results from an earlier selection;
15. duplicate selection/validation actions do not create duplicate ownership;
16. keyboard and focus behaviour is understandable;
17. messages contain no raw SQL, migration IDs, stack trace or unsafe absolute
    path;
18. all existing C4-I node IDs remain collected and green;
19. `git diff --check` is clean;
20. exact-head smoke uses isolated temporary user data and claims neither full
    Restore smoke nor release smoke.

#### Non-goals

- no call to `execute_restore(...)`;
- no explicit destructive confirmation;
- no `before_restore` safety-copy creation;
- no working-database replacement;
- no restored-copy migration;
- no rollback or startup-recovery mutation;
- no completion, rollback-completed or support-assisted terminal result UI;
- no FastAPI Restore endpoint;
- no ordinary SPA mutation;
- no Restore AuditLog event;
- no state-machine, phase, transition or recovery-matrix change;
- no generic file browser or arbitrary filesystem access;
- no cloud source, upload, sync or scheduler;
- no packaging, updater or release-readiness claim;
- no C4-II-B, C4-II-C or C4-III implementation.

### C4-II-B — Explicit confirmation and Restore execution

```text
PLANNED — NOT AUTHORIZED
```

Reserved future scope: presentation of the already validated exact source;
explicit destructive confirmation; truthful explanation that current data will
be replaced, a safety copy will be created, the source remains unchanged and the
application restarts; invocation of the existing C4-I execution boundary;
progress and restart handoff. This slice cannot begin until C4-II-A is reviewed,
exact-head verified, merged and closed.

### C4-II-C — Completion, rollback and support-assisted outcome UX

```text
PLANNED — NOT AUTHORIZED
```

Reserved future scope: truthful `completed`, `rolled_back`, retryable environment,
restart-required and `recovery_blocked` presentation; support-assisted guidance;
keyboard, accessibility and narrow-viewport behaviour. It must never label
`rolled_back` as successful Restore or expose technical recovery details.

### C4-III — Restore end-to-end verification and lifecycle closure

```text
PLANNED — NOT AUTHORIZED
```

Reserved future scope: exact-package current-schema and older-schema Restore;
corrupt/foreign/newer-schema rejection; interruption before and after replacement;
automatic rollback; repeated launch; source immutability; safety-copy retention;
browser-open boundary; lifecycle closure. It is a verification and closure gate,
not a place to hide broad runtime implementation.

## Consequences

**Positive.** The repository no longer treats merged PR #170 as open work. The
next implementation is small, non-destructive and independently reviewable.
Selection and validation presentation can be audited without mixing it with the
first user-triggered database replacement.

**Negative and accepted.** User-facing Restore remains incomplete after C4-II-A.
The user will be able to establish whether a backup is suitable but will not yet
be able to execute Restore. This is intentional sequencing, not a shipped partial
success claim.

## Non-goals of this lifecycle closure

No runtime code; no frontend code; no backend code; no launcher code; no test
change; no migration; no dependency change; no packaging; no updater; no change
to the accepted Restore state machine; no amendment to CR-010; no re-execution or
relabeling of PR #170 evidence; no product release-readiness claim.

## Historical state preservation

The previous long-form `state/current-focus.md`, `state/progress.md` and
`state/handoff.md` remain available in ordinary Git history at the parent of this
closure. They are not duplicated into new archive files, because doing so would
inflate a narrowly scoped documentation PR without adding information or safety.
