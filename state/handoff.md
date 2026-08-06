# Handoff

Updated: `2026-08-06`

This is the compact current handoff. Historical C4-I implementation and audit
detail is retained in:

`docs/history/c4-i-implementation-and-audit-history.md`

The current lifecycle decision is:

`docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`

## Repository lifecycle

```text
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
PR #170
final reviewed head ac95e2990efa979b3ded6cb48f91ddd0750aa7c8
merge commit e6997281d2e0268ce54184d988c114bac71c35e2

CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED
C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED

Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Next action

Perform one documentation and architecture decision task only:

```text
CR-011 — Decide the launcher Restore interaction and validation-session boundary.
```

No runtime implementation may begin until that decision is accepted.

The decision must select one concrete architecture. It must answer where the UI
lives, which process owns it, which process opens the native picker, how any
browser command reaches the launcher, how the exact local run is authenticated,
whether a source path leaves the launcher, whether the backend stays running,
which dependencies and packaging changes are allowed, how stale sessions and
replay are rejected, and how cleanup and exact-head smoke work.

## Current implementation facts

The launcher currently opens an ordinary system browser through
`webbrowser.open(...)`.

The current public C4-I package exposes destructive execution and startup
recovery. It does not expose a dedicated public non-destructive candidate
preparation session.

Therefore no accepted browser-to-launcher command channel or validation-session
application service exists yet.

## Mandatory future validation-session semantics

The future C4-II-A boundary may be named differently, but must be equivalent to:

```text
prepare_restore_candidate(...)
```

It must be launcher-owned and must:

- reuse C4-I source intake, staging, stability, and candidate validation rules;
- use temporary isolated staging outside the durable Restore operation workspace;
- create no durable Restore operation record and enter no Restore phase;
- call no `execute_restore(...)`;
- create no `before_restore` safety copy;
- mutate no selected source or working database;
- perform no migration, rollback, recovery mutation, or Restore AuditLog write;
- return typed safe presentation results;
- keep raw SQLite, migration, stack-trace, and absolute-path detail in local logs;
- use opaque session identity and stale-selection protection;
- invalidate prior results on cancellation or reselection;
- clean temporary state after cancellation, failure, reselection, and shutdown;
- support bounded cleanup after interrupted validation.

An opaque token is not proof that a source is still valid. C4-II-B must re-prove
source or retained-candidate identity through launcher-owned state and accepted
C4-I rules before destructive execution.

## Prohibited assumptions

Do not add any of the following without an accepted CR-011 decision:

- ordinary FastAPI Restore endpoint;
- generic unauthenticated localhost endpoint;
- wildcard CORS;
- WebSocket or IPC invented in runtime code;
- SPA-owned filesystem access;
- browser upload/blob as the authoritative source;
- `<input type="file">` as a source of an absolute local path;
- pywebview, Electron, Tauri, PyObjC, tkinter, AppleScript, or custom URL scheme;
- hidden packaging changes;
- absolute selected-source path in ordinary browser state;
- terminal workflow for the user.

## Preserved load-bearing C4-I contract

- exactly twelve durable phases;
- `phase` is the sole authoritative lifecycle field;
- accepted transition graph and startup recovery matrix unchanged;
- immutable selected source;
- canonical launcher-owned paths and locks;
- retained backend exclusion around database access;
- exact-child lock-and-socket readiness proof;
- mandatory verified `before_restore` safety copy before replacement;
- conservative `replacement_intent` recovery;
- retryable port refusal never becomes durable Restore state;
- `rolled_back` is failed Restore;
- `recovery_blocked` blocks ordinary startup;
- browser opens into the normal workspace only after durable `completed`;
- no ordinary backend or SPA Restore mutation;
- no Restore AuditLog event.

## Review gate for PR #171

PR #171 must remain draft and unmerged until an independent read-only
documentation and architecture consistency audit confirms that all active
lifecycle documents agree and that C4-II-A is not authorized.