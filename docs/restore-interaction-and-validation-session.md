# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — CR-011 DECISION GATE**  
Updated: `2026-08-06`

This profile extends the Restore architecture described by:

- `docs/architecture.md`;
- `docs/backup-and-restore.md`;
- `docs/decisions/0016-launcher-assisted-restore.md`;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`.

Where an older branch-era lifecycle statement in `docs/architecture.md` or
`docs/backup-and-restore.md` describes C4-I as unmerged or C4-II as one undivided
slice, the current lifecycle in ADR 0017 and this profile governs. The twelve
phases, transition graph, recovery matrix, immutable-source rule, mandatory
safety copy, launcher ownership, and AuditLog boundary remain governed by ADR
0016 and are not changed here.

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

Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Existing implementation boundary

The launcher currently opens the ordinary system browser through
`webbrowser.open(...)`.

The ordinary browser UI currently has no accepted command channel through which
it can ask the launcher to open a native macOS file picker or begin
launcher-owned source validation.

The public C4-I package currently exposes destructive Restore execution and
startup recovery entry points. It does not expose a dedicated public
non-destructive candidate-preparation session.

These are architecture and security decisions. They are not implementation
details that C4-II-A may choose implicitly.

## CR-011 decision requirements

Before any C4-II runtime work is authorized, CR-011 must select one concrete
architecture and decide:

1. where the user-facing C4-II-A screen lives;
2. which process owns the screen;
3. which process opens the native macOS file picker;
4. how a browser action, if any, reaches the launcher;
5. whether an absolute source path ever leaves launcher-owned state;
6. whether the ordinary backend remains running during selection and validation;
7. how the channel is bound to the exact local launcher run;
8. origin, token, replay, stale-session, and duplicate-action protection;
9. allowed dependencies;
10. required packaging changes and explicitly deferred packaging work;
11. the non-technical packaged user entry path;
12. cancellation, reselection, launcher-exit, and interrupted-session cleanup;
13. isolated exact-head smoke for the selected architecture.

The decision may compare a launcher-native pre-start Restore flow and a narrowly
authenticated launcher-owned loopback control plane. It must choose one; it may
not leave incompatible alternatives equally authorized.

## Prohibited implementation by assumption

Before CR-011 is accepted, the following are not authorized:

- an ordinary FastAPI Restore endpoint;
- SPA-owned filesystem access;
- browser upload or blob transfer as the authoritative Restore source;
- reliance on `<input type="file">` for an absolute local path;
- a generic unauthenticated localhost endpoint;
- wildcard CORS;
- a WebSocket or IPC channel invented only in runtime code;
- pywebview, Electron, Tauri, PyObjC, tkinter, AppleScript, a custom URL scheme,
  or another native-shell technology;
- a dependency not named by the accepted decision;
- packaging changes hidden inside C4-II-A;
- an absolute selected-source path in ordinary browser presentation state;
- a user workflow that falls back to GitHub, Git, Python, Node.js, Docker,
  SQLite tools, or a terminal.

## Mandatory non-destructive application boundary

Future C4-II-A must use one launcher-owned application service conceptually
represented as:

```text
prepare_restore_candidate(...)
```

The exact code name is not fixed by this profile. The semantics are mandatory.

The service must:

- be owned by the launcher/application shell;
- never call `execute_restore(...)`;
- create no durable Restore operation record;
- enter none of the twelve durable Restore phases;
- create no `before_restore` safety copy;
- replace no working database;
- migrate no working database;
- perform no rollback or startup-recovery mutation;
- write no Restore AuditLog event;
- leave the selected source immutable and byte-identical;
- use isolated temporary staging distinct from a durable Restore operation
  workspace;
- reuse the accepted C4-I source intake, sidecar checks, held-descriptor staging,
  stability proof, schema-lineage checks, and candidate-validation rules;
- return typed presentation results;
- map rejection to fixed non-technical user-facing categories;
- keep raw SQLite errors, stack traces, migration IDs, internal absolute paths,
  and verifier details in local technical logs only;
- expose only an opaque validation-session identity outside launcher-owned state;
- use a monotonically changing selection generation or equivalent stale-result
  protection;
- invalidate earlier results on cancellation and reselection;
- reject duplicate ownership/actions;
- clean temporary artifacts after cancellation, reselection, rejection,
  technical failure, and launcher shutdown;
- provide bounded cleanup after an interrupted validation session;
- give the browser no authority over the selected-source path;
- forbid UI compatibility inference from filename or extension;
- never produce a durable result or message equivalent to Restore completion.

## Typed presentation result

The future result may expose only human-safe information that the launcher can
prove, such as:

- an opaque session identifier;
- current selection generation;
- safe display label without an authoritative absolute path;
- validation state;
- current-schema compatibility;
- older-supported-schema compatibility for later execution;
- fixed rejection category;
- fixed user guidance;
- whether the current result is stale or cancelled.

It must not expose raw SQL, migration IDs, operation-record contents, stack
traces, SQLite errors, arbitrary absolute paths, or database contents.

## Session identity is not authority

An opaque validation-session token is only a reference to launcher-owned state.
It is not proof that the original source or retained candidate remains valid.

Future C4-II-B must not trust an old browser result. Before any destructive
execution, it must re-prove either:

- the immutable original selected source; or
- an explicitly retained launcher-owned staged candidate.

The accepted CR-011 architecture must decide which identity is retained and how
it is re-proved. Filename, extension, browser state, and token possession are not
sufficient authority.

## Source, staging, and cleanup ownership

The selected source remains read-only input and must never be renamed, migrated,
deleted, rewritten, checkpointed, or repaired.

Validation staging is temporary and is not a durable Restore operation. It must
use a launcher-owned directory with ownership rules that prevent path escape,
symlink traversal, accidental cleanup of foreign files, and reuse of stale state.

Cancellation or reselection must invalidate the prior generation before a later
result can become current. Cleanup must remove only artifacts whose ownership can
be proved.

After a hard interruption, the next launcher run may perform bounded cleanup of
recognized validation-session scratch state. It must not treat that scratch as a
Restore operation, enter a Restore phase, alter the working database, or infer
that destructive Restore began.

## Backend and browser boundaries

No ordinary FastAPI Restore mutation endpoint is authorized.

If CR-011 later selects a launcher-owned loopback control plane, it must be a
separate local control boundary, not an ordinary business API route. The decision
must define binding address, exact-run token creation and lifetime, allowed
origin, request vocabulary, replay protection, cancellation semantics, process
ownership, shutdown, and tests. A generic localhost endpoint is not acceptable.

The browser is a presentation client only. It may display typed launcher-owned
results and issue only commands authorized by the selected control architecture.
It does not own source paths, SQLite validation, staging, migration analysis,
working-database replacement, locks, safety-copy creation, rollback, or recovery.

## Future C4-II-A minimum tests

The eventual runtime slice must prove at least:

1. cancellation creates no durable Restore operation and changes no data;
2. a valid current-schema application backup is accepted;
3. a valid older supported backup is accepted for later execution;
4. newer, foreign, empty, corrupt, directory, symlink, and path-escape inputs are
   rejected;
5. the original selected source remains byte-identical on every path;
6. no `before_restore` safety copy is created;
7. no working-database replacement or migration occurs;
8. no Restore phase or AuditLog event is written;
9. stale earlier validation cannot overwrite a later selection;
10. cancellation and reselection clean only owned temporary files;
11. launcher shutdown and interrupted validation have bounded cleanup;
12. duplicate actions do not create duplicate authority;
13. the ordinary browser never becomes authoritative for an absolute source path;
14. raw technical details do not reach user-facing presentation;
15. the selected interaction channel is confined to the exact launcher run;
16. exact-head smoke exercises the real picker/control/session boundary rather
    than injecting the final result synthetically.

## Relationship to future execution

C4-II-A remains non-destructive and not authorized until CR-011 is accepted.

C4-II-B remains separately planned. It will own explicit destructive
confirmation, identity re-proof, mandatory `before_restore` safety copy, and the
existing C4-I execution boundary.

C4-II-C remains separately planned for truthful completion, rollback,
retryable-environment, restart-required, and support-assisted outcomes.

C4-III remains the end-to-end package verification and lifecycle closure gate.

None of those slices is authorized by this profile.