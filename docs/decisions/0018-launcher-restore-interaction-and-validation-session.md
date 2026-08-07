# ADR 0018 — Launcher-owned loopback Restore control plane and validation session

## Status

`ACCEPTED BY CR-011 CHANGESET — NORMATIVE ONLY WHEN PRESENT ON main` — 2026-08-07.

This ADR decides `CR-011 — Launcher Restore interaction and non-destructive validation-session boundary`.

It does **not** authorize C4-II-A runtime implementation. A separate bounded task must authorize C4-II-A after this decision is merged and independently audited.

This ADR does not amend the durable Restore safety semantics accepted by ADR 0016. The twelve durable phases, transition graph, startup recovery matrix, `replacement_intent` rule, destructive launcher ownership, immutable-source rule, mandatory `before_restore` safety copy, and Restore AuditLog boundary remain unchanged.

## Context

PR #171 is merged at:

`76ab59216047222714a32f2793a789b3dc8df19a`

Current implementation evidence:

- `launcher.main` owns application startup;
- `launcher.runtime` starts the ordinary local backend and opens the ordinary system browser through `webbrowser.open(...)`;
- the ordinary browser is the product presentation surface;
- the local backend is the business API, not the owner of destructive Restore;
- the launcher owns Restore lifecycle authority;
- C4-I exposes `execute_restore(...)`, startup recovery, immutable source intake/staging, candidate validation, backend exclusion, replacement and rollback infrastructure;
- C4-I does not expose a public non-destructive candidate-preparation session;
- the browser has no accepted channel for asking the launcher to open a native picker;
- the browser must never become authoritative for an absolute selected-source path.

Existing C4-I primitives already provide the safety semantics candidate preparation must reuse:

- `open_selected_source(...)` validates an absolute local path, refuses unsafe source shapes, checks sidecars, opens one held read-only descriptor and proves identity;
- `HeldSource.revalidate()` re-proves descriptor/path identity;
- `HeldSource.digest()` computes full SHA-256 through the held descriptor;
- `stage_source(...)` copies through that descriptor, performs two digest passes, re-checks sidecars/identity and publishes only a stable candidate;
- `validate_staged_candidate(...)` opens the staged candidate read-only and verifies structural health, migration lineage and workshop identity.

CR-011 exists so C4-II-A cannot invent its command channel, picker technology, security, concurrency, path-privacy or validation-session lifetime in runtime code.

## Decision drivers

The selected architecture must:

1. preserve the ordinary browser as the familiar product UI;
2. keep filesystem authority in the launcher;
3. keep the absolute selected-source path out of browser and ordinary backend state;
4. bind control authority to one exact launcher run;
5. remain local-first without internet;
6. avoid an ordinary FastAPI Restore mutation;
7. avoid a broad desktop-shell redesign merely to open one picker;
8. remain usable by a non-technical packaged user;
9. reuse C4-I intake/staging/validation rather than duplicate it;
10. reject replay, duplicate actions and stale results;
11. keep heartbeat/state/cancel responsive while picker/validation is running;
12. clean bounded temporary authority after cancellation, browser loss, launcher exit and interruption;
13. keep C4-II-A strictly non-destructive.

## Considered alternatives

### Option A — launcher-native pre-start Restore flow

Advantages:

- no browser-to-launcher channel;
- source path naturally remains launcher-only;
- fewer cross-origin concerns.

Rejected because:

- the project has no native application shell/navigation surface;
- a pre-start Restore UI would make ordinary startup less direct;
- it would pull native-shell/packaging architecture into this bounded decision;
- validation/retry/accessibility presentation would be duplicated outside the existing product UI.

### Option B — narrowly authenticated launcher-owned loopback control plane

Advantages:

- preserves the browser-first product model;
- keeps the ordinary FastAPI business API unchanged;
- keeps picker/path/validation authority in the launcher;
- can use Python standard-library HTTP primitives and one macOS system helper without a new application dependency;
- keeps typed validation presentation in the existing UI;
- gives the new authority boundary explicit tests.

Costs:

- exact-run authentication and Origin enforcement are mandatory;
- bootstrap/session/replay/concurrency state must be launcher-owned;
- browser refresh/tab-loss behavior must be explicit.

**Selected: Option B.**

## Selected architecture

Use a **launcher-owned loopback Restore control plane** separate from the ordinary FastAPI backend.

The control plane:

- runs inside the launcher process;
- binds only `127.0.0.1`;
- binds an OS-assigned ephemeral port (`port 0` at bind time);
- exists for one launcher run only;
- exposes only the bounded Restore-control vocabulary defined below;
- never exposes an ordinary business API;
- never accepts unauthenticated authority-bearing commands;
- never returns an authoritative source path to the browser;
- remains responsive to heartbeat/state/cancel while picker or validation is running;
- shuts down before launcher process exit.

No WebSocket is selected. The control contract is small HTTP/JSON request-response traffic.

No new runtime dependency is authorized. Future C4-II-A should use Python standard-library HTTP/server primitives unless a later decision explicitly authorizes another dependency.

## Startup and process order

Future user-mode startup order is fixed conceptually as:

```text
acquire launcher lifecycle / instance authority
→ resolve interrupted C4-I Restore recovery gate
→ perform ordinary startup / migrations / backup-before-migration rules
→ start and prove ordinary backend ready
→ bind launcher control plane on 127.0.0.1:<ephemeral>
→ create exact-run bootstrap capability
→ open ordinary browser with bootstrap fragment
→ run browser UI + backend + control plane under the same launcher lifetime
```

If the control plane cannot start safely, ordinary product operation may continue when otherwise safe, but Restore controls must be unavailable and fail closed. The launcher must not invent a different Restore transport as fallback.

## Process topology

```text
macOS user
  ↓
ordinary browser / SPA
  ├── business requests ──→ FastAPI backend on 127.0.0.1
  │
  └── Restore control ────→ launcher-owned control plane
                             127.0.0.1:<ephemeral>
                                      ↓
                             launcher action/session coordinator
                               ├── owned picker worker
                               └── validation worker
                                      ↓
                         C4-I intake / staging / validation

working database remains untouched during C4-II-A
```

## User interaction flow

Future C4-II-A uses the normal browser application UI under a dedicated Restore screen/route.

```text
open application normally
→ browser establishes exact-run launcher control session
→ user opens Restore screen
→ user chooses “Выбрать резервную копию”
→ browser sends authenticated select command
→ launcher opens native macOS picker
→ absolute path returns only to launcher
→ launcher prepares/validates temporary candidate
→ launcher returns typed safe result
→ browser shows accepted/rejected/cancelled state
```

The browser never receives the absolute path and never uploads file bytes as authoritative Restore source.

A page opened without a valid launcher control session must fail closed with human-readable guidance to open/restart the application normally. It must not fall back to browser file upload or an ordinary backend endpoint.

## Native picker ownership

The launcher owns the picker action and filesystem authority.

Selected future macOS adapter:

- owned short-lived child process invoking `/usr/bin/osascript`;
- macOS Standard Additions `choose file` provides the native dialog;
- selected POSIX path returns only to launcher;
- browser/ordinary backend receive no absolute path;
- `shell=True` is forbidden;
- user-controlled text must not be interpolated into executable AppleScript source;
- no `System Events` control of another application;
- picker cancellation maps to typed cancellation, not technical failure.

No new Python package is authorized for the picker.

Filename/type hints are presentation only and never compatibility authority. Full C4-I intake and candidate validation remain authoritative.

### Packaging consequence

Current packaging target is a non-sandboxed local macOS application/package. `/usr/bin/osascript` is a macOS system dependency and is not bundled.

CR-011 does not claim Mac App Store sandbox compatibility. A future App-Store/sandbox decision may replace the picker adapter with an `NSOpenPanel`/security-scoped-access implementation, but must preserve launcher ownership/path privacy unless a later ADR explicitly changes them.

## Browser bootstrap and exact-run security

### Bind, Host and Origin

- bind address: exactly `127.0.0.1`;
- port: OS-assigned ephemeral port;
- no `0.0.0.0`, LAN or remote binding;
- HTTP `Host` must equal the actual `127.0.0.1:<bound-port>` authority;
- launcher derives one exact allowed Origin from configured `frontend_url`;
- user-mode Origin must be local HTTP on `127.0.0.1` with the configured frontend port;
- a different Host/Origin is refused, never dynamically trusted.

CORS:

- one exact allowed origin only;
- no wildcard origin;
- no credentialed cookie session;
- only required methods/headers;
- preflight must not broaden origin/method/header scope.

### Bootstrap token

Before opening the browser, launcher creates:

- opaque `run_id`;
- cryptographically random bootstrap token with at least 256 bits of entropy;
- control-plane ephemeral port.

Browser launch URL carries control port + one-time bootstrap token in the **URL fragment**, not query parameters.

Conceptually:

```text
http://127.0.0.1:5173/#cw-control=<ephemeral-port>:<one-time-bootstrap-token>
```

Mandatory properties:

- fragment is not sent to the frontend HTTP server;
- frontend reads it once and exchanges it with `POST /v1/bootstrap`;
- bootstrap is an **atomic compare-and-consume** operation;
- exactly one concurrent exchange can create browser session authority;
- every replay/concurrent loser is refused;
- frontend removes the bootstrap fragment immediately after success with `history.replaceState(...)` or equivalent;
- bootstrap token is never logged or durably persisted.

### Run-scoped browser session token

Successful bootstrap returns a second cryptographically random session token with at least 256 bits of entropy.

The session token:

- is valid only for exact launcher `run_id`;
- is stored in browser `sessionStorage`, never `localStorage`;
- is sent in explicit authorization header, never a URL;
- is bound to exact allowed Origin;
- is invalidated on launcher exit/restart or control-session expiry;
- is never persisted by launcher;
- is never logged.

All bootstrap/control responses carrying session or validation state must use `Cache-Control: no-store` and equivalent no-cache behavior where applicable.

## Mandatory concurrency model

A long-running `select` request must **not** execute on the only control-plane request loop.

Future C4-II-A must use a `ThreadingHTTPServer`-equivalent concurrent request model or equivalent launcher-owned dispatcher/worker coordination so that while picker/validation is in flight:

- heartbeat remains serviceable;
- `GET /v1/state` remains serviceable;
- cancel remains serviceable;
- session timeout can still be enforced;
- an owned picker helper can be terminated after cancel/session expiry.

Concurrency is request servicing, not authority multiplication. Explicit synchronization must permit at most one picker/validation owner for one control session.

## Browser liveness

Browser sends authenticated heartbeat while Restore control session is active.

Future C4-II-A must use:

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without authenticated heartbeat or other authenticated control request.

On expiry launcher must atomically:

- invalidate session token;
- invalidate/advance active selection generation;
- terminate owned picker helper if active;
- prevent stale validation result publication;
- clear launcher-private retained source proof/path for that control session;
- clean only provably owned validation scratch;
- leave ordinary backend/workshop data unchanged.

## Narrow control vocabulary

C4-II-A may expose only an equivalent of:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

There is deliberately no destructive execute/confirm command in C4-II-A.

The control plane must not grow arbitrary filesystem, shell, SQL, backend-proxy or generic launcher-command endpoints.

## Replay, duplicate and command ordering

Mutating control commands (`select`, `cancel`, and any equivalent future C4-II-A mutating command) carry both:

- a cryptographically random request ID with at least 128 bits of entropy; and
- a strictly monotonic `command_seq` scoped to the authenticated control session.

The launcher stores bounded command authority state:

- `highest_command_seq`;
- request ID for that sequence;
- safe status/result needed to answer an idempotent retry of that sequence.

Rules:

- first new mutation must be the next expected sequence;
- `command_seq < highest_command_seq` is always stale/replay and is rejected;
- `command_seq == highest_command_seq` is accepted only when request ID matches the recorded request ID, and returns the same in-progress/final safe result without re-execution;
- the same sequence with a different request ID is a conflict and is rejected;
- a skipped/future sequence is rejected rather than silently advancing authority;
- a new `select` while picker/validation already owns the session is refused as `action_in_progress`;
- accepted select/cancel/reselect advances a separate monotonically increasing selection generation;
- a validation result may publish only if its captured generation remains current;
- cancel/reselect invalidates older generation and clears retained proof for it before new source authority is established;
- stale result is discarded and cannot overwrite current browser state.

Heartbeats are authenticated liveness signals, not mutation commands, and do not consume `command_seq`.

This sequence rule prevents replay even after old request-result details are discarded; an old lower sequence can never become new again.

## Non-destructive validation-session ownership

Future C4-II-A must add one launcher-owned boundary conceptually equivalent to:

```text
prepare_restore_candidate(...)
```

Suggested later module responsibilities:

```text
launcher/control_plane.py
launcher/restore/picker_macos.py
launcher/restore/validation_session.py
```

Names are not public API commitments; ownership is.

The validation service must:

- never call `execute_restore(...)`;
- create no durable Restore operation record;
- enter none of twelve durable Restore phases;
- create no `before_restore` safety copy;
- replace no working database;
- migrate no working database;
- perform no rollback/startup-recovery mutation;
- write no Restore AuditLog event;
- leave selected source byte-identical;
- use isolated launcher-owned temporary staging distinct from durable `RestoreWorkspace` operation directories;
- reuse C4-I `open_selected_source(...)`, `HeldSource` identity/digest semantics, stable `stage_source(...)` semantics and `validate_staged_candidate(...)` through shared collaborators rather than weaker copies;
- return typed presentation-safe results only;
- keep raw SQLite errors, migration IDs, internal paths and stack traces in local technical logs only;
- expose only opaque session/run/generation identifiers to browser;
- never claim Restore completed.

If current `stage_source(...)` is too tightly coupled to `RestoreWorkspace`, C4-II-A may make a bounded refactor extracting one shared lower-level staging primitive while preserving all existing C4-I behavior/tests. It must not create a second staging algorithm.

## Validation scratch ownership

Temporary validation staging is not a Restore operation.

Use a canonical launcher-owned scratch root under the current user's system temporary directory, conceptually:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<validation-session-id>/
```

Requirements:

- canonical root resolved by launcher code only;
- launcher creates/uses the private root/session directories with user-only permissions (`0700` or platform-equivalent restrictive permissions);
- opaque random run/session directory names;
- no user-provided path component;
- no symlink traversal;
- owned marker/version metadata sufficient to prove cleanup authority;
- candidate scratch never appears under durable Restore operation directories;
- cleanup refuses paths outside the canonical root;
- interruption cleanup removes only recognized owned session directories.

## Typed presentation result and path privacy

Browser-visible state may contain only safe facts:

- opaque run/session identity;
- selection generation;
- safe display filename/label;
- `idle`, `selecting`, `validating`, `accepted`, `rejected`, `cancelled`, `technical_failure`;
- current-schema / older-supported-schema compatibility;
- fixed rejection category/guidance;
- stale/cancelled state.

It must not contain:

- absolute source path;
- staged candidate path;
- raw SQL/SQLite text;
- migration IDs;
- stack traces;
- operation-record contents;
- arbitrary database contents.

A safe filename is presentation only and never compatibility/authority proof.

## Retained source identity and C4-II-B handoff

After successful C4-II-A validation, the temporary staged candidate is cleaned.

Launcher retains in memory for the **current authenticated control session only**:

- canonical absolute selected-source path, launcher-private;
- C4-I `SourceIdentity` facts captured from the held descriptor;
- full SHA-256 digest captured from the held descriptor;
- successful validation generation;
- typed compatibility result.

None of those facts leave launcher-owned state except safe typed result.

Retained proof must be cleared on:

- cancel;
- reselection before new generation becomes authoritative;
- validation rejection/technical failure;
- browser control-session expiry;
- launcher normal exit;
- any state transition that invalidates the successful generation.

Opaque browser token is a reference only, never authority.

Future C4-II-B must, before destructive Restore:

1. reopen launcher-private original path through accepted C4-I intake;
2. prove reopened descriptor/path identity matches retained identity;
3. recompute/compare full SHA-256;
4. re-check source sidecars/self-containment;
5. stage again through accepted C4-I semantics;
6. validate newly staged candidate again;
7. only then enter existing destructive C4-I execution boundary that creates mandatory safety copy and durable Restore operation.

Any mismatch invalidates prior validation and returns to source selection. Browser state, filename, extension or token possession never bypasses re-proof.

## Backend lifecycle

The **ordinary backend remains running** during:

- file selection;
- source intake;
- temporary staging;
- candidate validation;
- result presentation.

C4-II-A is strictly non-destructive and operates on an isolated source/staged copy. Existing C4-I backend stop/exclusion proof remains the future C4-II-B destructive boundary.

## Cancellation, reselection and cleanup

### Picker cancel

- invalidate/advance generation;
- clear retained source proof;
- no durable Restore operation/safety copy;
- clean owned scratch;
- return typed cancelled state.

### Reselection

- invalidate old generation first;
- clear old retained source proof;
- terminate/finish old picker/validation ownership;
- clean old owned scratch;
- only then establish next generation.

### Validation rejection / technical failure

- retain only safe presentation category;
- technical detail stays local;
- clear retained source proof;
- clean staged scratch;
- source stays byte-identical.

### Browser reload

- `sessionStorage` retains exact-run session token;
- browser calls `GET /v1/state`;
- in-progress generation remains launcher-authoritative.

### Browser/tab close

- no destructive action follows;
- 60-second heartbeat expiry invalidates browser authority;
- clear retained source proof/path;
- cancel active picker/validation ownership;
- clean owned scratch;
- ordinary backend data remains unchanged.

### Launcher normal exit

- invalidate bootstrap/session tokens;
- cancel active generation;
- clear retained source proof/path;
- terminate owned picker helper;
- remove owned validation scratch;
- stop control plane.

### Launcher crash / machine interruption

No token or in-memory source proof survives process loss.

Next launcher start performs bounded cleanup only under canonical validation scratch root and only for paths whose marker/path shape proves ownership.

Validation scratch never becomes a durable Restore operation, phase, recovery trigger or working-database mutation.

## Failure behavior

Control-plane failure is fail-closed for Restore control only.

If the control plane cannot bind/authenticate/validate Host+Origin/parse a command/maintain session invariants:

- no picker/validation authority is granted;
- no destructive Restore begins;
- ordinary backend may continue normal product operation when otherwise safe;
- browser gets fixed human-readable Restore-unavailable guidance;
- technical detail remains local.

## Dependency decision

CR-011 authorizes **no new application dependency**.

Future C4-II-A is expected to use:

- Python standard library for launcher-owned HTTP control boundary;
- `/usr/bin/osascript` with macOS Standard Additions `choose file` for picker;
- existing C4-I code for intake/staging/validation.

If implementation cannot satisfy these boundaries, stop and open a new architecture/change request rather than adding PyObjC, Electron, Tauri, pywebview, tkinter, a WebSocket framework or another dependency by assumption.

## Packaging implications

Future C4-II-A will require the packaged launcher to:

- remain alive for browser/product session;
- own the ephemeral control listener and worker/concurrency lifecycle;
- open browser with one-use bootstrap fragment;
- own short-lived `/usr/bin/osascript` picker helper;
- clean validation proof/scratch/tokens at shutdown.

This ADR does not implement `.app`/`.dmg` packaging and does not authorize a general native shell.

Mac App Store sandboxing is outside the current MVP packaging contract.

## C4-II-A implementation boundary

C4-II-A, when separately authorized, may implement only:

- launcher control-plane bootstrap/session/concurrency boundary described here;
- browser Restore selection/validation presentation;
- launcher-owned macOS picker adapter;
- non-destructive validation-session service;
- shared-safe refactor needed to reuse C4-I staging/validation semantics;
- typed safe results/cancel/reselect state;
- bounded validation scratch/proof cleanup;
- tests and exact-head smoke for this boundary.

C4-II-A must not implement destructive confirmation or call the destructive execution boundary.

## Required future tests and exact-head smoke

Automated C4-II-A tests must prove at least:

1. control plane binds only `127.0.0.1` on ephemeral port;
2. wrong/missing Host or Origin is refused;
3. wildcard CORS is absent;
4. bootstrap token is atomic one-use under concurrent exchange attempts;
5. old-run/invalid session tokens are refused;
6. control responses are `Cache-Control: no-store`;
7. heartbeat/state/cancel remain serviceable while picker/validation is in flight;
8. `command_seq` replay/out-of-order rules prevent re-execution even after older result details are discarded;
9. duplicate current sequence with same request ID is idempotent;
10. duplicate sequence with different request ID is rejected;
11. duplicate concurrent select is refused;
12. stale generation cannot publish;
13. cancel/reselect/session-expiry clears retained source proof;
14. browser payload contains no absolute path;
15. picker cancellation is typed/non-destructive;
16. source remains byte-identical;
17. validation creates no durable Restore operation/phase/safety copy/AuditLog event;
18. working database remains unchanged;
19. backend remains usable during validation;
20. scratch directories use restrictive user-only permissions;
21. scratch cleanup removes only owned paths;
22. next-run cleanup ignores foreign/unproved paths;
23. browser reload recovers safe state;
24. heartbeat expiry invalidates control authority and prevents stale publication.

Exact-head macOS smoke must exercise the **real** boundary:

```text
real launcher run
→ real browser Restore screen
→ real authenticated launcher control request
→ real /usr/bin/osascript native picker
→ select temporary known application backup
→ real launcher candidate preparation/validation
→ typed result delivered to browser
→ keep picker/validation in flight long enough to prove heartbeat/state/cancel responsiveness
→ cancel/reselect scenario
→ verify source bytes unchanged
→ verify no durable Restore operation/safety copy/working-DB change
→ verify retained proof cleared after cancel/session expiry
→ verify control plane/picker/scratch cleanup and no owned process remains
```

Injecting final validation result or bypassing picker/control/session boundary is insufficient.

## Consequences

Positive:

- preserves browser-first UX;
- keeps Restore authority launcher-owned;
- no ordinary backend Restore mutation;
- no new application dependency;
- no absolute path in browser state;
- exact-run local control security, command ordering and concurrency are explicit;
- future implementation scope is bounded/testable;
- C4-I safety primitives remain source of truth.

Costs:

- launcher gains one narrow loopback server, worker coordination and session state in C4-II-A;
- frontend performs one-time exact-run bootstrap;
- control security/concurrency requires dedicated tests;
- browser tab loss intentionally cancels Restore-control authority after timeout;
- App Store sandbox packaging may require a future picker-adapter decision.

## Explicit non-goals

This ADR does not authorize or implement:

- C4-II-A runtime code;
- C4-II-B/C4-II-C/C4-III;
- destructive Restore confirmation;
- changes to twelve-phase state machine;
- ordinary FastAPI Restore endpoint;
- browser upload as Restore authority;
- SPA filesystem authority;
- wildcard CORS;
- generic localhost command server;
- WebSocket/IPC architecture;
- PyObjC/Electron/Tauri/pywebview/tkinter dependency adoption;
- `.app`/`.dmg` packaging implementation;
- App Store sandbox support;
- cloud sync, OCR, roles, multi-user or unrelated features.

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

A separate post-merge task must authorize C4-II-A. This ADR does not authorize implementation merely by existing on a PR branch.