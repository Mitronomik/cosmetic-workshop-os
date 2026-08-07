# ADR 0017 — C4-I lifecycle closure and C4-II decision gate

## Status

`ACCEPTED` — 2026-08-06.

This record closes the lifecycle of merged `C4-I` and authorizes one bounded
**decision-only** task: `CR-011 — Launcher Restore interaction and
validation-session boundary`.

It does not authorize C4-II runtime implementation.

It does **not** amend `CR-010` or
[`0016-launcher-assisted-restore.md`](0016-launcher-assisted-restore.md). The
accepted twelve phases, transition graph, startup recovery matrix,
`replacement_intent` crash rule, launcher ownership, immutable source rule,
mandatory safety copy, and AuditLog boundary remain unchanged.

The concise implementation and audit history is retained in
[`docs/history/c4-i-implementation-and-audit-history.md`](../history/c4-i-implementation-and-audit-history.md).
That history is non-normative and must not override this decision or the current
implementation plan.

## Verified C4-I merge facts

| Item | Verified value |
|---|---|
| Pull request | `#170 — C4-I — Implement launcher-owned Restore safety engine` |
| State | `MERGED` |
| Final independently reviewed and exact-head-tested implementation head | `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8` |
| Merge commit on `main` | `e6997281d2e0268ce54184d988c114bac71c35e2` |
| Merged at | `2026-08-03T16:12:23Z` |
| Relationship | reviewed head is a parent of the merge commit |
| Additional file changes introduced by merge commit | none |

The accepted PR #170 tests, audit, and exact-head smoke evidence are historical
evidence. They are not re-executed or relabelled by PR #171.

## Current lifecycle

```text
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
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## Why C4-I closure does not mean Restore is implemented

C4-I is internal launcher infrastructure. It implements the accepted durable
Restore state machine and the safety mechanisms needed by a future product flow.
It exposes no product file picker, selected-backup screen, validation screen,
destructive confirmation, execution action, progress screen, terminal outcome
screen, ordinary FastAPI Restore endpoint, ordinary SPA mutation, or supported
terminal workflow for the user.

The current launcher opens the ordinary system browser through
`webbrowser.open(...)`. The ordinary browser page currently has no accepted
command channel through which it can instruct the launcher to open a native
macOS picker or perform launcher-owned validation.

The current public C4-I package exposes destructive Restore execution and startup
recovery entry points. It does not expose a dedicated public non-destructive
candidate-preparation session.

Those are architecture gaps, not details a runtime PR may choose implicitly.
Therefore C4-II-A remains blocked and not authorized.

## Decision: split the remaining product work

The user-facing Restore capability remains divided into bounded slices:

### C4-II-A — source selection and validation presentation

```text
PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
```

Future purpose only:

```text
select one local SQLite backup
→ prepare and validate it through launcher-owned C4-I rules
→ present safe human-readable information or rejection
```

No current workshop data is replaced or migrated in this slice.

### C4-II-B — explicit confirmation and execution

```text
PLANNED — NOT AUTHORIZED
```

Reserved future purpose: re-prove the exact source or retained candidate,
present explicit destructive confirmation, create the mandatory safety copy,
invoke the existing C4-I execution boundary, and manage the restart handoff.

### C4-II-C — result, rollback, and support-assisted UX

```text
PLANNED — NOT AUTHORIZED
```

Reserved future purpose: truthful `completed`, `rolled_back`, retryable
environment, restart-required, and `recovery_blocked` presentation.

### C4-III — end-to-end verification and lifecycle closure

```text
PLANNED — NOT AUTHORIZED
```

Reserved future purpose: exact-package verification of current-schema and
supported older-schema Restore, rejection paths, interruption, rollback,
repeated launch, source immutability, safety-copy retention, and lifecycle
closure.

## CR-011 — authorized decision-only task

CR-011 must select one concrete architecture before any C4-II runtime code is
authorized. It must not leave incompatible options equally permitted, and it
must not hide the choice in implementation code.

The decision must explicitly answer all of the following.

1. Where the user-facing C4-II-A screen lives.
2. Which process owns that screen.
3. Which process physically opens the native macOS file picker.
4. How a browser action, if any, reaches the launcher.
5. Whether an absolute selected-source path is ever exposed outside the launcher.
6. Whether the ordinary backend remains running during source selection and
   candidate validation.
7. How the command channel is limited to the exact local launcher run.
8. Which origin, token, replay, stale-session, and duplicate-action protections
   are mandatory.
9. Which new dependencies are allowed.
10. Which packaging changes are required and which are explicitly deferred.
11. How a non-technical packaged user starts Restore without Git, Python,
    Node.js, Docker, GitHub, or a terminal.
12. How cancellation, reselection, launcher exit, and interrupted validation
    clean up launcher-owned temporary state.
13. How the selected architecture is tested in isolated exact-head smoke.

CR-011 must compare candidate approaches against:

- product clarity for a non-technical user;
- local-only security boundaries;
- path and source-identity privacy;
- replay and stale-result resistance;
- process lifecycle and crash recovery;
- packaging feasibility on macOS;
- dependency cost and maintenance risk;
- exact-head testability;
- compatibility with the accepted C4-I safety engine.

The decision may evaluate, among other explicitly bounded options:

- a launcher-native pre-start Restore flow;
- a narrowly authenticated launcher-owned loopback control plane.

This ADR deliberately does not select an option merely to finish PR #171.

## Not authorized before CR-011 is accepted

No implementation may assume or introduce any of the following before a
separate accepted CR-011 decision authorizes it:

- an ordinary FastAPI Restore endpoint;
- SPA-owned filesystem access;
- browser upload or blob transfer as the authoritative Restore source;
- reliance on `<input type="file">` to provide an absolute local path;
- a generic unauthenticated localhost endpoint;
- wildcard CORS;
- a WebSocket, IPC, or command channel invented only in runtime code;
- pywebview, Electron, Tauri, PyObjC, tkinter, AppleScript, a custom URL scheme,
  or another shell technology;
- packaging changes hidden inside C4-II-A;
- an absolute backup path stored in ordinary browser presentation state;
- a new dependency not named by the accepted decision;
- a fallback terminal workflow for the user.

Implementation by assumption is explicitly rejected.

## Mandatory non-destructive validation-session boundary

Future C4-II-A must use one launcher-owned application boundary conceptually
represented as:

```text
prepare_restore_candidate(...)
```

The exact eventual code name is not decided here. The semantic boundary is
mandatory.

### Required properties

The future service must:

- be owned by the launcher/application shell;
- never call `execute_restore(...)`;
- create no durable Restore operation record;
- enter none of the twelve durable Restore phases;
- create no `before_restore` safety copy;
- replace no working database;
- migrate no working database;
- perform no rollback or startup-recovery mutation;
- write no Restore AuditLog event;
- never mutate, rename, migrate, delete, or rewrite the selected source;
- use isolated temporary staging distinct from a durable Restore operation
  workspace;
- reuse the accepted C4-I source intake, staging, source-stability, and candidate
  validation rules rather than creating a weaker parallel validation flow;
- return typed presentation results;
- map rejection to fixed non-technical categories;
- keep raw SQLite errors, stack traces, migration IDs, internal absolute paths,
  and verifier detail in local technical logs only;
- expose only an opaque validation-session identity outside launcher-owned state;
- use a monotonically changing selection generation or an equivalent mechanism
  that rejects stale results;
- invalidate earlier results on cancellation and reselection;
- protect duplicate actions from creating duplicate ownership;
- clean temporary artifacts after cancellation, reselection, validation failure,
  and launcher shutdown;
- provide bounded cleanup recovery after an interrupted validation session;
- give the browser no authority over the selected-source path;
- forbid UI compatibility inference from filename or extension;
- never publish a durable success claim equivalent to Restore completion.

### Session identity is not validation authority

An opaque validation-session token is only a reference to launcher-owned state.
It is not proof that the original source or staged candidate remains valid.

Future C4-II-B must not trust an old browser result. Before destructive execution,
it must re-prove the selected source or retained-candidate identity through
launcher-owned state and the accepted C4-I safety rules.

The later decision must define whether C4-II-B:

- reopens and revalidates the immutable original source; or
- re-proves an explicitly retained launcher-owned staged candidate.

Either approach must reject stale identity and must not rely on filename, browser
state, or a token alone.

## Presentation boundary

The future presentation layer may consume typed results and display:

- safe source label information;
- validation progress;
- valid-current-schema status;
- valid-older-supported status for later execution;
- fixed rejection categories;
- cancellation and retry guidance.

It must not:

- parse SQLite;
- inspect migration lineage;
- calculate schema compatibility;
- reconstruct validation from a filename or extension;
- show raw SQL, migration IDs, stack traces, internal operation records, or
  absolute developer paths;
- imply that Restore executed;
- show a success message equivalent to «Данные восстановлены»;
- make a destructive action available after rejection.

## Unchanged CR-010 / ADR 0016 invariants

Later decisions and runtime work must preserve all of the following:

- Restore is launcher-assisted;
- the ordinary backend is stopped for destructive replacement;
- the selected source is immutable read-only input;
- Restore is whole-database only;
- complete candidate validation precedes destructive mutation;
- a verified `before_restore` safety copy is mandatory before replacement;
- exactly twelve durable phases exist:
  `prepared`, `source_staged`, `candidate_validated`, `safety_copy_verified`,
  `replacement_intent`, `replacement_committed`, `verification_in_progress`,
  `completed`, `aborted`, `rollback_in_progress`, `rolled_back`, and
  `recovery_blocked`;
- `phase` is the sole authoritative lifecycle field;
- the accepted transition graph and startup recovery matrix are unchanged;
- `replacement_intent` is treated conservatively after interruption;
- terminal records are not reactivated;
- `rolled_back` is failed Restore, never successful Restore;
- `recovery_blocked` never permits ordinary startup;
- the ordinary browser opens only after durable `completed`;
- no ordinary FastAPI Restore mutation is authorized;
- no ordinary SPA-owned filesystem replacement or lock is authorized;
- no Restore AuditLog event is authorized;
- technical detail remains in local logs rather than ordinary user-facing text.

## Consequences

### Positive

- C4-I is closed truthfully and no longer appears as open branch work.
- The reasons behind its safety boundaries remain searchable in the current tree.
- Codex cannot invent a browser-to-launcher command channel in a runtime PR.
- Candidate validation receives an explicit non-destructive application boundary.
- C4-II remains split into independently reviewable pieces.

### Negative and accepted

- No C4-II runtime slice is authorized after PR #171.
- A separate decision PR is required before product UI implementation.
- User-facing Restore remains incomplete.

These costs are accepted because the missing interaction and session boundaries
are security and data-safety decisions, not ordinary implementation details.

## Non-goals of PR #171

No runtime code; no frontend code; no backend code; no launcher code; no test
change; no migration; no dependency change; no native picker; no IPC; no
loopback server; no packaging; no updater; no state-machine change; no
re-execution or relabelling of PR #170 evidence; no product release-readiness
claim.