# ADR 0018 — Launcher-owned loopback Restore control plane and validation session

## Status

`ACCEPTED BY CR-011 CHANGESET — NORMATIVE ONLY WHEN PRESENT ON main` — 2026-08-07.

This ADR decides `CR-011 — Launcher Restore interaction and non-destructive validation-session boundary`.

It does **not** authorize C4-II-A runtime implementation. A separate bounded task must authorize C4-II-A after this decision is merged and independently audited.

ADR 0016 remains authoritative for the twelve durable Restore phases, transition graph, startup recovery matrix, `replacement_intent`, destructive launcher ownership, immutable source, mandatory `before_restore` safety copy, and Restore AuditLog boundary. ADR 0018 does not amend those semantics.

## Context and current implementation evidence

PR #171 is merged at `76ab59216047222714a32f2793a789b3dc8df19a`.

Current facts:

- `launcher.main` owns application startup;
- `launcher.runtime` starts the ordinary local backend and opens the ordinary system browser through `webbrowser.open(...)`;
- the browser is the product presentation surface;
- the FastAPI backend is the business API, not destructive Restore authority;
- the launcher owns Restore lifecycle authority;
- C4-I exposes destructive `execute_restore(...)`, recovery, immutable source intake/staging, candidate validation, backend exclusion, replacement and rollback infrastructure;
- no public non-destructive candidate-preparation session exists;
- no accepted browser-to-launcher picker/control channel exists;
- browser state must never become authoritative for an absolute selected-source path.

Existing C4-I primitives must remain the source of truth:

- `open_selected_source(...)`;
- `HeldSource.revalidate()`;
- `HeldSource.digest()` / full SHA-256;
- stable two-pass `stage_source(...)` semantics;
- `validate_staged_candidate(...)` read-only validation.

## Decision drivers

The solution must preserve browser-first UX, launcher filesystem authority, local-first operation, source-path privacy, exact-run authentication, replay/stale/duplicate resistance, responsive cancel/liveness, bounded cleanup, C4-I safety reuse, and a strictly non-destructive C4-II-A boundary.

## Considered alternatives

### Option A — launcher-native pre-start Restore flow

Advantages: no browser-to-launcher channel and naturally launcher-private path ownership.

Rejected because the product has no native application shell/navigation surface. Introducing a separate native Restore UI now would broaden this bounded decision into a shell/packaging redesign and duplicate validation/retry/accessibility presentation outside the ordinary product UI.

### Option B — narrowly authenticated launcher-owned loopback control plane

Advantages: preserves the existing browser product surface, keeps ordinary FastAPI unchanged, keeps picker/path/validation authority in launcher, requires no new application dependency, and makes the new local authority boundary explicitly testable.

**Selected: Option B.**

## Selected architecture

```text
ordinary browser / SPA
  ├── business API → ordinary FastAPI backend
  └── Restore control → launcher-owned control plane
                         127.0.0.1:<ephemeral>
                                  ↓
                         action/session coordinator
                           ├── owned picker worker
                           └── validation worker
                                  ↓
                       C4-I intake/staging/validation
```

The control plane:

- runs inside the launcher process;
- binds only `127.0.0.1` on an OS-assigned ephemeral port;
- is separate from the ordinary backend;
- exposes only the narrow C4-II-A vocabulary defined below;
- remains responsive to heartbeat/state/cancel while picker/validation runs;
- never returns an authoritative source path to browser;
- shuts down with launcher.

No WebSocket is selected. No new runtime dependency is authorized. Python standard-library HTTP/server primitives are the expected implementation boundary.

## Screen ownership and user entry path

The future C4-II-A screen is a **browser-SPA-owned** nested route:

```text
/backups/restore
```

The normal user entry is an explicit human-readable action from the existing `/backups` workspace, conceptually “Восстановить из резервной копии”.

The route is presentation only. It does not own filesystem paths, SQLite validation, staging or destructive authority.

A page opened without a valid launcher control session must fail closed with guidance to open/restart the application normally. It must not fall back to `<input type="file">`, browser upload or an ordinary FastAPI Restore endpoint.

## Startup and process order

```text
acquire launcher lifecycle / instance authority
→ resolve interrupted C4-I Restore recovery gate
→ ordinary startup / migrations / backup-before-migration
→ start and prove ordinary backend ready
→ bind launcher control plane on 127.0.0.1:<ephemeral>
→ create exact-run bootstrap capability
→ open /backups/restore or ordinary app entry with bootstrap fragment available to SPA
→ keep browser UI + backend + control plane under the same launcher lifetime
```

The ordinary application may open its normal default route first; when the Restore route is entered later it uses the already-established exact-run control session.

If the control plane cannot start safely, ordinary product operation may continue when otherwise safe, but Restore controls remain unavailable. No alternate Restore transport is invented.

## Native picker ownership

Launcher owns the picker and absolute path.

Future adapter:

- owned short-lived `/usr/bin/osascript` child;
- macOS Standard Additions `choose file`;
- selected POSIX path returned only to launcher;
- no `shell=True`;
- no user-controlled text interpolated into executable AppleScript;
- no `System Events` automation;
- cancellation is a typed ordinary cancel result.

No new Python/application dependency is authorized.

Filename/type hints are presentation only; C4-I intake/validation remains acceptance authority.

Mac App Store sandbox compatibility is not claimed. A later sandbox decision may replace the picker adapter while preserving launcher ownership/path privacy unless a later ADR explicitly changes them.

## Bind, Host, Origin and CORS

Future C4-II-A must enforce:

- bind exactly `127.0.0.1`;
- OS-assigned ephemeral port;
- no LAN, `0.0.0.0` or remote bind;
- HTTP `Host` equal to actual `127.0.0.1:<bound-port>`;
- one exact allowed Origin derived from configured local `frontend_url`;
- user-mode Origin must be local HTTP on `127.0.0.1` with configured frontend port;
- no wildcard origin;
- no credentialed cookie session;
- only required methods/headers and no broadened preflight.

## Bootstrap and browser reload state

Before browser open launcher creates:

- opaque `run_id`;
- one-use bootstrap token with at least 256 bits of entropy;
- control-plane ephemeral port.

The launch URL transports control port + bootstrap token only in the **URL fragment**, never query parameters.

Conceptually:

```text
http://127.0.0.1:5173/#cw-control=<ephemeral-port>:<bootstrap-token>
```

Bootstrap rules:

- fragment is not sent to frontend HTTP server;
- frontend exchanges it with `POST /v1/bootstrap`;
- bootstrap is an **atomic compare-and-consume** operation;
- exactly one concurrent exchange succeeds;
- replay/concurrent losers are refused;
- frontend immediately removes the bootstrap fragment with `history.replaceState(...)` or equivalent;
- bootstrap capability is never logged or persisted.

Successful bootstrap returns a second run-scoped token with at least 256 bits of entropy.

For browser reload, SPA stores only these run-scoped control descriptors in `sessionStorage`:

- `control_origin`, exactly `http://127.0.0.1:<ephemeral-port>`;
- opaque `run_id` if needed for presentation/session matching;
- run-scoped session token.

`control_origin` is routing metadata, not authority. Token possession plus exact Origin/Host/run checks is still required.

The session token:

- is never stored in `localStorage`;
- is sent in an explicit authorization header, never URL;
- is bound to exact allowed Origin and current launcher run;
- is invalidated on launcher exit/restart/session expiry;
- is never persisted by launcher or logged.

On explicit invalid-token / run-mismatch response, SPA clears stale `control_origin`, `run_id` and session token from `sessionStorage`. A network failure may show Restore unavailable but must never invent new authority.

All bootstrap/control responses carrying session or validation state use `Cache-Control: no-store` and equivalent no-cache behavior where applicable.

## Mandatory concurrency model

A long-running `select` request must **not** run on the only control request loop.

Use a `ThreadingHTTPServer`-equivalent concurrent request model or equivalent launcher-owned dispatcher/worker coordination so that while picker/validation is in flight:

- heartbeat remains serviceable;
- `GET /v1/state` remains serviceable;
- cancel remains serviceable;
- timeout remains enforceable;
- owned picker helper can be terminated.

Concurrency does not multiply authority. At most one picker/validation owner exists for one control session.

Worker publication is generation-gated. After cancellation/expiry a worker may not publish success even if its underlying I/O returns later.

Cancellation invalidates authority immediately. Cleanup that could race with a still-running worker occurs only after that worker has quiesced/released owned files. Future shared staging may add a cooperative cancellation hook checked at safe chunk boundaries while keeping C4-I callers' behavior unchanged. If a non-interruptible validation substep is still finishing, the UI remains cancelled/stale and no new source authority is established until prior ownership is quiescent.

## Browser liveness

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without authenticated heartbeat or other authenticated control request.

On expiry launcher atomically:

- invalidates session token;
- invalidates/advances selection generation;
- terminates owned picker if active;
- prevents stale result publication;
- clear launcher-private retained source proof/path for that session;
- waits for/coordinates worker quiescence before deleting worker-owned scratch;
- cleans only proved owned validation scratch;
- leaves ordinary backend/workshop data unchanged.

Browser reload uses `sessionStorage` `control_origin` + session token and `GET /v1/state`.

## Narrow control vocabulary

C4-II-A may expose only an equivalent of:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

There is no destructive execute/confirm command in C4-II-A. No arbitrary filesystem, shell, SQL, backend-proxy or generic launcher command endpoint is allowed.

## Replay, duplicate and command ordering

Each mutating control command carries:

- cryptographically random request ID with at least 128 bits of entropy;
- strictly monotonic `command_seq` scoped to the authenticated control session.

Launcher retains bounded command authority state:

- `highest_command_seq`;
- request ID for that sequence;
- safe in-progress/final result needed for idempotent retry.

Rules:

- next new mutation must use exactly next sequence;
- `command_seq < highest_command_seq` is permanently stale/replay and rejected;
- `command_seq == highest_command_seq` retries only with the same request ID and never re-executes;
- same sequence + different request ID is conflict/rejected;
- skipped/future sequence is rejected;
- new select while picker/validation owns session is `action_in_progress`;
- accepted select/cancel/reselect advances separate selection generation;
- validation result publishes only if captured generation remains current;
- cancel/reselect clears proof for invalidated generation before new source authority;
- stale results cannot overwrite current browser state.

Heartbeats do not consume `command_seq`.

## Non-destructive validation-session boundary

Future C4-II-A must add one launcher-owned service conceptually equivalent to:

```text
prepare_restore_candidate(...)
```

It must:

- never call `execute_restore(...)`;
- create no durable Restore operation record;
- enter none of twelve durable Restore phases;
- create no `before_restore` safety copy;
- replace/migrate no working database;
- perform no rollback/startup-recovery mutation;
- write no Restore AuditLog event;
- leave selected source byte-identical;
- use isolated launcher-owned temporary staging distinct from durable Restore workspaces;
- reuse C4-I `open_selected_source(...)`, `HeldSource` identity/digest, stable `stage_source(...)` semantics and `validate_staged_candidate(...)` through shared collaborators;
- return typed presentation-safe results only;
- keep raw SQLite errors, migration IDs, internal paths and stack traces in local technical logs only;
- expose only opaque session/run/generation identifiers to browser;
- never claim Restore completed.

If `stage_source(...)` is too coupled to `RestoreWorkspace`, C4-II-A may extract one shared lower-level staging primitive while preserving all existing C4-I behavior/tests. A second weaker staging algorithm is forbidden.

## Validation scratch ownership

Conceptual root:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

Requirements:

- canonical root resolved by launcher only;
- private root/session directories use user-only permissions (`0700` or platform-equivalent restrictive permissions);
- opaque random run/session components;
- no user-provided path component;
- no symlink traversal;
- owned marker/version metadata sufficient to prove cleanup authority;
- scratch never appears under durable Restore operation directories;
- cleanup refuses paths outside canonical root;
- interrupted next-run cleanup removes only recognized owned session directories.

## Typed browser result and path privacy

Allowed browser state:

- opaque run/session identity;
- selection generation;
- safe display filename/label;
- idle/selecting/validating/accepted/rejected/cancelled/technical_failure;
- current-schema / older-supported-schema compatibility;
- fixed rejection category/guidance;
- stale/cancelled state.

Forbidden:

- absolute source path;
- staged candidate path;
- raw SQL/SQLite text;
- migration IDs;
- stack traces;
- operation-record contents;
- arbitrary database contents.

Displayed filename is never compatibility/authority proof.

## Retained launcher-private proof and C4-II-B handoff

After successful validation, temporary staged candidate is deleted.

For the current authenticated control session only, launcher may retain:

- canonical absolute source path, launcher-private;
- C4-I `SourceIdentity`;
- full SHA-256 from held descriptor;
- successful selection generation;
- typed compatibility result.

Browser token is reference only, not authority.

Retained proof/path clears on cancel, reselection before new authority, validation rejection/technical failure, control-session expiry, launcher normal exit, or any transition invalidating the successful generation. No token/proof survives launcher crash.

Future C4-II-B must before destructive Restore:

```text
reopen launcher-private original path through C4-I intake
→ compare descriptor/path SourceIdentity
→ recompute and compare full SHA-256
→ re-check sidecars/self-containment
→ stage again through C4-I semantics
→ validate again
→ only then enter existing C4-I destructive execution
```

Any mismatch returns to source selection. Browser state, filename, extension or token possession cannot bypass re-proof.

## Backend lifecycle

The **ordinary backend remains running** during file selection, source intake, temporary staging, candidate validation and result presentation.

C4-II-A is non-destructive and operates on source + isolated staged copy. Existing C4-I backend stop/exclusion proof remains a future C4-II-B destructive boundary.

## Cleanup behavior

| Event | Required behavior |
|---|---|
| Picker cancel | invalidate generation/proof immediately; terminate picker; clean scratch after owner quiescence |
| Reselect | invalidate old generation/proof first; quiesce old owner; clean scratch; then new generation |
| Rejection/technical failure | safe browser category; technical detail local; clear proof; clean scratch |
| Browser reload | use sessionStorage `control_origin` + token to recover typed launcher state |
| Browser/tab close | heartbeat expiry invalidates authority/proof, cancels active ownership, then cleans scratch |
| Launcher normal exit | invalidate tokens/generation/proof, terminate picker, quiesce workers, clean scratch, stop control plane |
| Launcher crash/interruption | no token/proof survives; next run cleans only recognized owned scratch |

Validation scratch never triggers Restore phase, startup recovery or working-database mutation.

## Dependency and packaging decision

CR-011 authorizes **no new application dependency**.

Expected future C4-II-A primitives:

- Python standard library for control plane;
- `/usr/bin/osascript` + Standard Additions `choose file`;
- existing C4-I code for source intake/staging/validation.

If those boundaries cannot satisfy implementation, stop and open a new architecture/change request rather than adding PyObjC, Electron, Tauri, pywebview, tkinter, WebSocket framework or another dependency by assumption.

This ADR does not implement `.app`/`.dmg` packaging or App Store sandbox support.

## C4-II-A implementation boundary

When separately authorized, C4-II-A may implement only:

- exact-run launcher control-plane bootstrap/session/concurrency;
- SPA `/backups/restore` selection/validation presentation;
- launcher-owned macOS picker adapter;
- non-destructive validation-session service;
- shared-safe refactor needed to reuse C4-I staging/validation;
- typed state, command ordering, cancel/reselect/stale protection;
- validation scratch/proof cleanup;
- automated tests and real-boundary exact-head smoke.

It must not implement destructive confirmation/execution.

## Required future tests

At minimum prove:

1. loopback-only ephemeral bind;
2. wrong/missing Host or Origin rejected;
3. no wildcard CORS;
4. atomic bootstrap one-use under concurrent attempts;
5. old-run/wrong session token rejected;
6. `control_origin` + token reload works and stale run clears sessionStorage metadata;
7. state/session responses use `Cache-Control: no-store`;
8. heartbeat/state/cancel remain serviceable while picker/validation is in flight;
9. cancellation prevents late worker publication and cleanup waits for worker quiescence;
10. `command_seq` rejects replay/out-of-order after older result detail is discarded;
11. same current sequence + same request ID is idempotent;
12. same sequence + different request ID rejected;
13. duplicate concurrent select rejected;
14. stale generation cannot publish;
15. cancel/reselect/session-expiry clears retained proof;
16. browser payload contains no absolute path;
17. picker cancellation typed/non-destructive;
18. source remains byte-identical;
19. no durable Restore operation/phase/safety copy/AuditLog event;
20. no working DB replacement/migration;
21. backend usable during validation;
22. scratch uses restrictive user-only permissions;
23. cleanup removes only proved owned scratch;
24. next-run cleanup ignores foreign/unproved paths;
25. exact `/backups/restore` screen fails closed when launcher session unavailable.

## Required future exact-head macOS smoke

```text
real launcher run
→ real browser /backups/restore screen
→ real authenticated launcher-control request
→ real /usr/bin/osascript native picker
→ select prepared temporary workshop backup
→ real candidate preparation/validation
→ typed browser result
→ prove heartbeat/state/cancel responsiveness while picker/validation is in flight
→ cancel/reselect exercise
→ prove source bytes unchanged
→ prove no durable Restore operation/safety copy/working-DB change
→ prove retained proof cleared after cancel/session expiry
→ prove owned workers/control plane/picker/scratch cleaned
```

Injecting final result or bypassing picker/control/session boundary is insufficient.

## Consequences

Positive: preserves browser-first UX and launcher authority, adds no new dependency, keeps path private, gives exact security/concurrency/order contracts, and reuses C4-I safety.

Cost: launcher gains a narrow loopback server, worker coordination and session state; frontend gains exact-run bootstrap/session handling; App Store sandbox packaging may require a later picker-adapter decision.

## Explicit non-goals

This ADR does not authorize or implement C4-II-A runtime code, C4-II-B/C4-II-C/C4-III, destructive confirmation, state-machine changes, ordinary FastAPI Restore endpoint, browser upload authority, SPA filesystem authority, wildcard CORS, generic localhost command server, WebSocket/IPC architecture, new native-shell dependencies, packaging implementation, cloud/OCR/roles/multi-user work.

## Lifecycle consequence

When this ADR is present on `main`:

```text
PR #171 — MERGED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — DECIDED — ADR 0018 ACCEPTED — NORMATIVE ON MAIN
C4-II-A — PLANNED — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

A separate post-merge task must authorize C4-II-A.