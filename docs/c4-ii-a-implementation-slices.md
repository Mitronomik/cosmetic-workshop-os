# C4-II-A implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN WHEN PRESENT ON `main`**
Updated: `2026-08-07`

This document authorizes and bounds implementation work for:

`C4-II-A — Launcher Restore source selection and non-destructive validation presentation`.

It does not change the architecture selected by ADR 0018 and does not authorize C4-II-B destructive confirmation/execution.

## Authority

Read together with:

- `docs/current-lifecycle.md` — current authorization and sequencing;
- `docs/decisions/0016-launcher-assisted-restore.md` — durable destructive Restore safety/state-machine contract;
- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md` — selected control/picker/validation-session architecture;
- `docs/restore-interaction-and-validation-session.md` — normative interaction and validation-session profile;
- `docs/pr-testing-and-smoke-rules.md` — PR verification rules.

If this document conflicts with ADR 0016 or ADR 0018 on architecture or safety, the ADR governs. This document may only slice and authorize implementation of the already accepted architecture.

## Merged baseline

PR #172 / CR-011 is merged.

```text
PR #172 reviewed head — c51d5baa07e4cd8912b1973649c22b20f581e3d2
PR #172 merge commit — 998596560db6780a677bdec363d1fd19db30c1b6
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
```

## C4-II-A authorization model

C4-II-A is authorized only as four bounded implementation slices.

```text
C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED
C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

Only A1 may begin immediately after this authorization changeset is merged to `main`. Later slices require the previous slice to be independently reviewed, exact-head tested, merged, and lifecycle state updated before implementation.

Do not create dependent implementation branches from an unmerged prior slice. Each implementation slice starts from updated `main` after its predecessor merges.

## C4-II-A1 — Validation-session core

### Goal

Implement the launcher-owned non-destructive candidate-preparation boundary without browser control-plane or native-picker integration.

Conceptual application boundary:

```text
prepare_restore_candidate(...)
```

### Authorized scope

- launcher-owned validation-session state and ownership;
- isolated validation scratch under system temp with user-only permissions;
- selection generation / stale-result protection inside the validation service;
- cancellation/invalidation semantics needed by the core service;
- typed presentation-safe validation result model;
- retained launcher-private source proof: canonical private source path, C4-I `SourceIdentity`, full SHA-256, successful generation and typed compatibility result;
- bounded cleanup after success, rejection, cancellation, technical failure and recognized interrupted scratch;
- reuse of C4-I source intake, held-descriptor identity/digest, sidecar checks, two-pass stable staging and read-only candidate validation;
- if required, one bounded shared-primitive refactor that preserves existing C4-I behavior and tests rather than duplicating the staging algorithm.

### Explicit non-goals

A1 must not implement HTTP control plane, browser bootstrap/session tokens, `command_seq`, native picker, frontend Restore route/UI, destructive confirmation, `execute_restore(...)`, durable Restore operation/phase creation, `before_restore` safety copy, working-database replacement/migration, rollback/startup-recovery mutation, Restore AuditLog event, new application dependency or packaging implementation.

### Required tests

At minimum prove:

1. valid current-schema source produces typed accepted result;
2. supported older-schema source produces typed accepted-for-later-execution result without migration of original source or working DB;
3. newer/foreign/empty/corrupt/directory/symlink/sidecar/working-DB source classes reject through accepted C4-I rules;
4. source remains byte-identical;
5. no durable Restore operation, phase, safety copy or AuditLog event is created;
6. working database remains unchanged;
7. stale generation cannot publish;
8. cancellation/reselection invalidates prior proof;
9. retained proof clears on invalidating transitions;
10. cleanup removes only provably owned scratch;
11. interruption cleanup never treats validation scratch as a Restore operation;
12. existing C4-I launcher/Restore tests remain green.

### A1 smoke boundary

A1 smoke is launcher/service-level, not browser UI smoke. It must exercise the real candidate-preparation service and real C4-I intake/staging/validation on prepared temporary SQLite sources. Synthetic final-result injection is insufficient.

## C4-II-A2 — Exact-run launcher control plane

### Entry gate

A1 must be merged and exact-head verified first.

### Goal

Implement the launcher-owned loopback control/session boundary without native picker or final browser Restore UI.

### Authorized scope

- bind exactly `127.0.0.1` on OS-assigned ephemeral port;
- exact Host and configured local frontend Origin validation;
- no wildcard CORS / no credentialed cookie authority;
- one-use >=256-bit bootstrap capability;
- atomic bootstrap compare-and-consume;
- >=256-bit run-scoped session token;
- `Cache-Control: no-store` for sensitive control/session responses;
- heartbeat and 60-second authenticated inactivity expiry;
- concurrent servicing while long-running work is owned elsewhere;
- strict mutating command protocol with >=128-bit request ID and monotonic `command_seq`;
- sequence consumption before business precondition evaluation;
- idempotent current-sequence retry and permanent stale-sequence rejection;
- selection-generation integration with A1;
- safe typed state endpoint;
- cancellation/invalidation plumbing into A1;
- launcher startup/shutdown ownership of the control plane;
- a launcher-owned source-selection port/interface (`PickerPort`-equivalent) used by the select coordinator.

### Mandatory A2-to-A3 seam

A2 has **no real picker yet**. Therefore production A2 must use a launcher-owned unavailable picker adapter that returns a fixed typed `picker_unavailable` result and never obtains a source path.

Tests may inject a fake launcher-owned picker adapter to exercise coordinator/security behavior, but that test adapter is not production authority and must not create a production endpoint for supplying paths.

The browser may never provide the source path, file bytes or a filesystem handle to make A2 tests/implementation work. No temporary query/body field such as `path`, `source_path`, upload/blob or test-only production route is allowed.

A2 may start/stop the control plane under launcher ownership, but **the production browser launch URL remains unchanged until A4**. A2 must not append the bootstrap capability to `open_runtime_browser(...)` or equivalent user-facing browser navigation yet. This prevents a sensitive bootstrap fragment from remaining visible before the frontend consumer/removal logic exists.

A2 exact-head tests/smoke may exercise bootstrap and control requests through a direct local authenticated HTTP harness. Ordinary product UI must still expose no Restore control path after A2 alone.

### Explicit non-goals

A2 must not implement real native picker, production browser bootstrap-fragment handoff, final `/backups/restore` UI, destructive execute/confirm command, ordinary FastAPI Restore endpoint, generic filesystem/shell/SQL/launcher command surface, WebSocket, new dependency unless separately authorized, or C4-II-B.

### Required tests

At minimum prove loopback-only bind, exact Host/Origin, bootstrap atomicity, old-run/token rejection, no-store behavior, heartbeat/expiry, concurrent state/cancel servicing, command ordering, non-replayable typed rejection, idempotent retry, generation gating, cleanup/invalidation, typed `picker_unavailable`, rejection/absence of browser-provided source path authority, unchanged ordinary browser launch URL, and absence of any destructive command.

## C4-II-A3 — Native macOS picker integration

### Entry gate

A2 must be merged and exact-head verified first.

### Goal

Replace the A2 unavailable source-selection adapter with the real launcher-owned native file picker and connect it to A1 candidate preparation.

### Authorized scope

- owned short-lived `/usr/bin/osascript` child;
- Standard Additions `choose file`;
- no `shell=True`;
- no `System Events`;
- no user-controlled text interpolated into executable AppleScript;
- typed picker cancellation;
- absolute POSIX path returned only to launcher memory;
- picker worker ownership/termination;
- select command → real picker adapter → A1 candidate preparation;
- cancel/session-expiry invalidation while picker/validation work is in flight;
- worker-quiescence cleanup and stale-result blocking.

A3 replaces the A2 `picker_unavailable` production adapter; it must not add any browser-supplied path fallback.

The production browser launch URL still remains unchanged in A3. Exact-head smoke may use a direct authenticated local control-plane client to invoke the real picker. The user-facing fragment handoff and frontend consumer are A4 scope.

### Explicit non-goals

A3 must not implement final browser Restore workspace, production browser bootstrap-fragment handoff, destructive confirmation/execution, browser-owned absolute path, browser file upload as Restore authority, PyObjC/Electron/Tauri/pywebview/tkinter dependency, App Store sandbox redesign or packaging implementation.

### Required tests and macOS smoke

Automated tests must cover picker result mapping, cancellation, child lifecycle, path privacy, in-flight cancel/expiry and late-worker rejection.

Exact-head macOS smoke must invoke the real `/usr/bin/osascript` picker boundary through launcher-owned code and reach real A1 candidate preparation. Mocking the final picker result is not a sufficient smoke gate.

## C4-II-A4 — Browser Restore screen and end-to-end non-destructive flow

### Entry gate

A3 must be merged and exact-head verified first.

### Goal

Deliver the user-facing source-selection and validation presentation while remaining strictly non-destructive.

### Authorized scope

- exact browser-SPA route `/backups/restore`;
- human-readable entry action from `/backups`;
- production launcher browser handoff that appends the one-use bootstrap capability in the URL fragment only after the A4 frontend consumer exists;
- bootstrap URL-fragment consumption and immediate removal;
- `sessionStorage` run-scoped token and non-secret `control_origin` reload metadata;
- fail-closed invalid/missing launcher-session presentation;
- select/cancel/reselect controls;
- selecting/validating/accepted/rejected/cancelled/technical-failure states;
- fixed non-technical user guidance;
- no absolute path, raw SQLite, migration IDs, stack traces or internal paths in browser state;
- integration with real A2 control plane, A3 picker and A1 validation core;
- final C4-II-A exact-head end-to-end macOS smoke.

### Explicit non-goals

A4 must not implement destructive Restore confirmation that can execute Restore, `execute_restore(...)` control command, safety-copy creation, backend stop/replacement/migration, rollback/recovery UX owned by C4-II-C, C4-II-B/C4-II-C/C4-III or packaging completion.

### Required end-to-end smoke

At exact head, exercise:

```text
real launcher run
→ real browser /backups/restore
→ real exact-run bootstrap/control session
→ real /usr/bin/osascript picker
→ real A1 candidate preparation
→ typed browser result
→ cancel/reselect and browser reload
→ prove source unchanged
→ prove no durable Restore operation/phase/safety copy/AuditLog/working-DB mutation
→ prove owned control/picker/worker/scratch cleanup
```

Synthetic bypass of control, picker or validation boundary is insufficient.

## Cross-slice architecture constraints

Every A1–A4 implementation must preserve:

- ADR 0016 twelve-phase destructive Restore state machine unchanged;
- ADR 0018 selected launcher-owned loopback/picker/session architecture;
- browser remains presentation, never absolute-path authority;
- browser may never provide a source path or file payload as a substitute for the launcher-owned picker boundary;
- ordinary FastAPI remains business API, not Restore mutation authority;
- C4-II-A remains strictly non-destructive;
- source remains byte-identical;
- no second weaker staging/validation implementation;
- ordinary backend may remain running throughout C4-II-A validation;
- no destructive authority is added until separately authorized C4-II-B;
- no hidden packaging/dependency decision;
- no hidden production-only test bypass or generic path-injection endpoint;
- local-first operation without required internet;
- non-technical user workflow.

## PR discipline

Each implementation slice must be a separate small PR.

For every A1–A4 PR require Scope, Non-goals, Architecture constraints, Backend requirements, Frontend requirements, Tests, Acceptance criteria, exact changed-path review, independent exact-head review, PR-specific smoke appropriate to the slice, and P0=0/P1=0/P2=0 before merge.

Do not let a later slice start from an unmerged predecessor branch. Do not silently broaden a slice to absorb the next one.

## After C4-II-A4

C4-II-A is not complete until A4 is merged and its exact-head end-to-end smoke passes.

Even then C4-II-B remains separately not authorized until lifecycle/project memory is updated by a new bounded authorization task.

Restore remains `NOT IMPLEMENTED` until destructive confirmation/execution and outcome handling are completed through later authorized slices.
