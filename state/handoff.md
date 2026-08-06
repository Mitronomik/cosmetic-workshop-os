# Handoff

Updated: `2026-08-06`

> This is the single current authoritative handoff. The complete pre-closure
> handoff is preserved unchanged at
> `state/history/2026-08-06-c4-i-closure/handoff.md`.

## Repository lifecycle

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

## What merged in PR #170

PR #170 merged the internal launcher-owned Restore safety engine. The final
independently reviewed and exact-head-tested implementation head is
`ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`; merge commit
`e6997281d2e0268ce54184d988c114bac71c35e2` contains it without additional file
changes.

The engine implements the accepted CR-010 / ADR 0016 contract exactly. The
following remain load-bearing and must not be reinterpreted by later slices:

- exactly twelve durable phases;
- `phase` is the sole authoritative lifecycle field;
- unchanged transition graph and startup recovery matrix;
- durable `replacement_intent` before the replacement boundary;
- terminal phases are never reactivated;
- the selected source is immutable read-only input;
- the current database is protected by the canonical maintenance lease or the
  exact owned child lock/handshake boundary whenever it is accessed;
- a busy port is retryable environment evidence, not a verdict on database
  safety;
- Restore is launcher-assisted, not a running FastAPI mutation and not an
  ordinary SPA mutation;
- no Restore AuditLog event is authorized;
- the ordinary browser opens only after durable `completed`.

C4-I has no user-facing entry point. Do not describe it as shipped Restore.

## Next task: C4-II-A only

### Product goal

Give a non-technical user a safe first half of the Restore workflow:

```text
select one local SQLite backup
→ stage and validate through the existing C4-I contracts
→ show understandable backup information or a rejection
```

Nothing destructive happens in this slice.

### Required ownership

- The launcher/application shell owns local file selection.
- C4-I remains the sole owner of staging and candidate validation.
- Presentation consumes typed results and never parses SQLite or migration
  history itself.
- Technical detail remains in local logs.
- The selected file stays byte-identical and is never renamed, migrated,
  deleted or rewritten.

### Authorized user-facing states

- no source selected;
- native selection cancelled;
- selection accepted and validation pending;
- valid current-schema backup;
- valid older supported backup, clearly described as requiring migration during
  a later execution slice;
- invalid/corrupt file;
- foreign SQLite database;
- newer unsupported schema;
- path/type/symlink rejection;
- safe replacement of a previous selection;
- retry after a validation failure.

### Explicit non-goals

- no destructive confirmation;
- no `execute_restore(...)` call;
- no `before_restore` safety copy;
- no working-database replacement or migration;
- no rollback or recovery mutation;
- no completion, rollback-completed or support-assisted terminal screen;
- no FastAPI Restore endpoint;
- no SPA-owned filesystem access or Restore mutation;
- no state-machine or operation-record change;
- no Restore AuditLog event;
- no packaging or updater work;
- no C4-II-B, C4-II-C or C4-III implementation.

### Minimum verification

- focused launcher/service tests for selection and typed presentation mapping;
- real C4-I validation coverage remains collected and green;
- source immutability proved for success and rejection paths;
- no working-database, safety-copy, operation-record or AuditLog mutation;
- cancellation, reselection, stale-result rejection and duplicate-action
  protection;
- keyboard focus and accessible naming;
- desktop and supported narrow-width presentation;
- exact-head smoke with isolated temporary user data;
- no claim of successful Restore or release readiness.

## Later slices — not authorized

`C4-II-B` will own explicit destructive confirmation and execution only after
C4-II-A is reviewed, exact-head verified and merged. `C4-II-C` will own truthful
completion, rollback and support-assisted outcomes only after its predecessor is
closed. `C4-III` remains the isolated end-to-end verification and lifecycle
closure gate.
