# ADR 0018 — Launcher-owned loopback Restore control plane and validation session

## Status

`ACCEPTED BY CR-011 CHANGESET — NORMATIVE ONLY WHEN PRESENT ON main` — 2026-08-07.

This ADR decides `CR-011 — Launcher Restore interaction and non-destructive validation-session boundary`.

It does **not** authorize C4-II-A runtime implementation. A separate bounded task must authorize C4-II-A after this decision is merged and independently audited.

This ADR does not amend the durable Restore safety semantics accepted by ADR 0016. The twelve durable phases, transition graph, startup recovery matrix, `replacement_intent` rule, launcher ownership of destructive Restore, immutable-source rule, mandatory `before_restore` safety copy, and Restore AuditLog boundary remain unchanged.

## Context

PR #171 is merged at:

`76ab59216047222714a32f2793a789b3dc8df19a`

Current implementation evidence:

- `launcher.main` owns application startup;
- `launcher.runtime` starts the ordinary local backend and opens the ordinary system browser through `webbrowser.open(...)`;
- the ordinary browser is the product presentation surface;
- the local backend is the business API, not the owner of destructive Restore;
- the launcher owns Restore lifecycle authority;
- C4-I exposes `execute_restore(...)`, startup recovery, source intake, immutable-source staging, candidate validation, backend exclusion, replacement and rollback infrastructure;
- C4-I does not expose a public non-destructive validation-session application service;
- the browser has no accepted channel for asking the launcher to open a native picker;
- the browser must never become authoritative for an absolute selected-source path.

Existing C4-I primitives already provide the safety semantics future candidate preparation must reuse:

- `open_selected_source(...)` validates an absolute local path, refuses unsafe source shapes, checks sidecars, opens one held read-only descriptor and proves source identity;
- `HeldSource.revalidate()` re-proves descriptor/path identity;
- `HeldSource.digest()` computes full SHA-256 through the held descriptor;
- `stage_source(...)` copies through that descriptor, performs two digest passes, re-checks sidecars/identity and publishes only a stable candidate;
- `validate_staged_candidate(...)` opens the staged candidate read-only and verifies structural health, migration lineage and workshop identity.

CR-011 exists because C4-II-A must not invent its browser-to-launcher channel, picker technology, security model, path-privacy model, concurrency model or validation-session lifetime inside runtime code.

## Decision drivers

The selected architecture must:

1. preserve the ordinary browser as the familiar product UI;
2. keep filesystem authority in the launcher;
3. keep the absolute selected-source path out of browser and ordinary backend state;
4. bind control authority to one exact local launcher run;
5. remain local-first without internet;
6. avoid an ordinary FastAPI Restore mutation;
7. avoid a broad desktop-shell redesign merely to open one picker;
8. remain usable by a non-technical packaged user;
9. reuse C4-I intake/staging/validation safety rather than duplicate it;
10. reject replay, duplicate actions and stale results;
11. keep heartbeat/cancel responsive while picker/validation is running;
12. have bounded cleanup after cancellation, browser loss, launcher exit and interruption;
13. keep C4-II-A non-destructive.

## Considered alternatives

### Option A — launcher-native pre-start Restore flow

Advantages:

- no browser-to-launcher channel;
- source path naturally remains launcher-only;
- fewer cross-origin concerns.

Rejected because:

- the project has no native application shell/navigation surface;
- a pre-start prompt would make ordinary startup less direct;
- a separate native Restore UI would pull shell/packaging architecture into this bounded decision;
- validation/retry/accessibility presentation would be duplicated outside the ordinary product UI.

### Option B — narrowly authenticated launcher-owned loopback control plane

Advantages:

- preserves the current browser product model;
- keeps the ordinary FastAPI API unchanged;
- keeps picker/path/validation authority in the launcher;
- can use Python standard-library HTTP primitives and a macOS system helper without a new application dependency;
- keeps typed validation presentation in the existing UI;
- gives the new authority boundary explicit tests.

Costs:

- exact-run authentication and Origin enforcement are mandatory;
- bootstrap/session/replay/concurrency state must be owned by the launcher;
- browser refresh/tab-loss behavior must be explicit.

**Selected: Option B.**

## Selected architecture

Use a **launcher-owned loopback Restore control plane** separate from the ordinary FastAPI backend.

The control plane:

- runs inside the launcher process;
- binds only `127.0.0.1`;
- binds an OS-assigned ephemeral port (`port 0` at bind time);
- exists for one launcher run only;
- exposes only a bounded Restore-control vocabulary;
- never exposes an ordinary business API;
- never accepts unauthenticated authority-bearing commands;
- never returns an authoritative source path to the browser;
- remains responsive to heartbeat/state/cancel while picker or validation work is running;
- shuts down before launcher process exit.

No WebSocket is selected. Use small HTTP/JSON request-response traffic.

No new runtime dependency is authorized. Future C4-II-A should use Python standard-library HTTP/server primitives unless a later decision explicitly authorizes another dependency.

### Mandatory concurrency model

A long-running `select` request must **not** execute on the only control-plane request loop.

Future C4-II-A must use either `ThreadingHTTPServer`-equivalent concurrent request servicing or an equivalent launcher-owned dispatcher/worker model so that:

- heartbeat remains serviceable while native picker is open;
- `GET state` remains serviceable during validation;
- cancel can invalidate generation and terminate an owned picker helper while select is in flight;
- session timeout can be enforced without waiting for select/validation to return;
- one action still has single launcher-owned mutation authority through explicit synchronization.

Concurrency is for request servicing only; it must not permit two picker/validation owners for one session.

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

The ordinary backend and launcher control plane are separate authorities even though both are loopback services.

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

If the page was opened without a valid launcher control session, Restore controls must fail closed with human-readable guidance to open/restart the application normally; they must not fall back to browser file upload or an ordinary backend endpoint.

## Native picker ownership

The launcher owns the picker action and filesystem authority.

Selected future macOS adapter:

- owned short-lived child process invoking `/usr/bin/osascript`;
- macOS Standard Additions `choose file` provides the native file dialog;
- selected POSIX path returns only to launcher;
- browser/ordinary backend receive no absolute path;
- `shell=True` is forbidden;
- user-controlled text must not be interpolated into executable AppleScript source;
- no `System Events` control of another application;
- picker cancellation maps to typed cancellation, not technical failure.

No new Python package is authorized for this picker.

Filename/type hints may improve presentation but are never compatibility authority. C4-I intake and candidate validation remain authoritative.

### Packaging consequence

Current packaging target is a non-sandboxed local macOS application/package. `/usr/bin/osascript` is a macOS system dependency and is not bundled.

CR-011 does not claim Mac App Store sandbox compatibility. A future App-Store/sandbox decision may replace the picker adapter with an `NSOpenPanel`/security-scoped-access implementation, but must preserve launcher ownership/path privacy unless a later ADR explicitly changes them.

## Browser bootstrap and exact-run security model

### Bind and Host

- address: exactly `127.0.0.1`;
- port: OS-assigned ephemeral port;
- no `0.0.0.0`, LAN or remote binding;
- HTTP `Host` must match the actual `127.0.0.1:<bound-port>` authority;
- control-plane lifetime: one launcher run only.

### Allowed browser Origin

The launcher derives one exact allowed Origin from the configured `frontend_url` for the current run.

For user-mode C4-II-A, accepted Origin must be local HTTP on `127.0.0.1` with the configured frontend port. A different host/origin is refused rather than added dynamically.

CORS:

- one exact allowed origin only;
- no wildcard origin;
- no credentialed cookie session;
- only required methods/headers;
- preflight must not broaden origin/method/header scope.

### Bootstrap token

Before opening the browser, launcher creates:

- opaque launcher `run_id`;
- cryptographically random bootstrap token with at least 256 bits of entropy;
- control-plane ephemeral port.

Browser launch URL carries only control port + one-time bootstrap token in the **URL fragment**, not query parameters.

Conceptual example:

```text
http://127.0.0.1:5173/#cw-control=<ephemeral-port>:<one-time-bootstrap-token>
```

Mandatory properties:

- fragment is not sent to frontend HTTP server;
- frontend reads it once;
- frontend exchanges it with control plane;
- bootstrap consume is **atomic compare-and-consume**: exactly one successful exchange can create browser session authority even under concurrent requests;
- every concurrent/replayed bootstrap after the winning consume is refused;
- frontend removes bootstrap fragment immediately after success using `history.replaceState(...)` or equivalent;
- bootstrap token is never logged or stored in `localStorage`, application data or durable files.

### Run-scoped browser session token

Successful bootstrap returns a second cryptographically random session token with at least 256 bits of entropy.

The session token:

- is valid only for exact launcher `run_id`;
- is stored in browser `sessionStorage`, never `localStorage`;
- is sent in explicit authorization header, never URL;
- is bound to exact allowed Origin;
- is invalidated on launcher exit/restart;
- is invalidated on control-session expiry;
- is never persisted by launcher;
- is never logged.

A token from an earlier run is always invalid.

All bootstrap/control responses carrying session or validation state must use `Cache-Control: no-store` (and equivalent no-cache behavior where applicable).

### Browser liveness

Browser sends authenticated heartbeat while Restore control session is active.

Future C4-II-A must use:

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without authenticated heartbeat or other authenticated control request.

On expiry launcher must atomically:

- invalidate session token;
- invalidate/advance active selection generation;
- terminate owned picker helper if active;
- prevent old validation result from becoming current;
- clear launcher-private retained source proof/path for that control session;
- clean only provably owned validation scratch.

Ordinary backend/product state is not mutated by timeout.

## Narrow control vocabulary

C4-II-A may expose only an equivalent of:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

Names may vary but scope may not.

There is deliberately no execute/confirm/destructive Restore command in C4-II-A.

The control plane must not grow arbitrary filesystem, shell, SQL, backend-proxy or generic launcher-command endpoints.

## Replay, duplicate and stale-result protection

Every authenticated non-read command carries a random request ID with at least 128 bits of entropy.

Launcher maintains a bounded per-run idempotency/replay ledger.

Rules:

- same request ID never executes an action twice;
- duplicate completed request returns/references same safe result, not repeated action;
- duplicate in-progress request reports same in-progress ownership;
- new `select` while picker/validation owns session is refused as `action_in_progress`;
- accepted select/cancel/reselect advances monotonically increasing selection generation;
- result can publish only if captured generation is still current;
- cancel/reselect invalidates older generation **and clears any retained source proof for that generation before** new authority is established;
- stale result is discarded and cannot overwrite current browser-visible state.

## Validation-session ownership

Future C4-II-A must add one launcher-owned non-destructive boundary conceptually equivalent to:

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
- reuse C4-I `open_selected_source(...)`, `HeldSource` identity/digest semantics, `stage_source(...)` semantics and `validate_staged_candidate(...)` through shared collaborators rather than weaker copies;
- return typed presentation-safe results only;
- keep raw SQLite errors, migration IDs, internal paths and stack traces in local technical logs only;
- expose only opaque session/run/generation identifiers to browser;
- never claim Restore completed.

If current `stage_source(...)` is too coupled to `RestoreWorkspace`, C4-II-A may make a bounded refactor extracting one shared lower-level staging primitive while preserving all C4-I behavior/tests. It must not create a second staging algorithm.

## Validation scratch ownership

Temporary validation staging is not a Restore operation.

Use canonical launcher-owned scratch root under current user's system temp area, conceptually:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<validation-session-id>/
```

Requirements:

- canonical root resolved by launcher only;
- opaque random run/session directory names;
- no user-provided path component;
- no symlink traversal;
- owned marker/version metadata sufficient to prove cleanup authority;
- candidate scratch never appears under durable Restore operation directories;
- cleanup refuses paths outside canonical root;
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

After successful C4-II-A validation, temporary staged candidate is cleaned.

Launcher retains in memory for the **current authenticated control session only**:

- canonical absolute selected-source path, launcher-private;
- C4-I `SourceIdentity` facts captured from held descriptor;
- full SHA-256 digest captured from held descriptor;
- successful validation generation;
- typed compatibility result.

None of those facts leave launcher-owned state except safe typed result.

The retained proof must be cleared on:

- cancel;
- reselection before new generation becomes authoritative;
- validation rejection/technical failure;
- browser control-session expiry;
- launcher normal exit;
- any state transition that invalidates the successful generation.

Opaque browser session/token is reference only, not authority.

Future C4-II-B must, before destructive Restore:

1. reopen launcher-private original path through accepted C4-I intake;
2. prove reopened descriptor/path identity matches retained identity;
3. recompute/compare full SHA-256;
4. re-check sidecars/self-containment;
5. stage again through accepted C4-I semantics;
6. validate new staged candidate again;
7. only then enter existing destructive C4-I execution boundary that creates mandatory safety copy and durable Restore operation.

Any mismatch invalidates prior validation and returns to source selection. Browser state, filename, extension or token possession never bypasses re-proof.

## Backend lifecycle

The ordinary backend remains running during:

- file selection;
- source intake;
- temporary staging;
- candidate validation;
- result presentation.

Reason:

- C4-II-A is strictly non-destructive;
- validation operates on isolated staged copy;
- no working database replacement/migration occurs;
- destructive backend-stop proof/maintenance lease is unnecessary for candidate validation;
- stopping backend would unnecessarily interrupt product UI and blur validation vs execution.

Future C4-II-B remains responsible for existing C4-I backend exclusion/stop proof before destructive work.

## Cancellation, reselection and cleanup

### Picker cancel

- invalidate/advance generation;
- clear retained source proof for invalidated generation;
- no durable Restore operation/safety copy;
- clean owned scratch;
- return typed cancelled state.

### Reselection

- invalidate old generation first;
- clear old retained source proof;
- terminate/finish old picker/validation ownership;
- clean old owned scratch;
- only then establish next generation.

### Validation rejection

- retain safe rejection category only;
- clear source proof;
- remove staged scratch;
- source remains byte-identical.

### Technical failure

- raw detail local only;
- browser receives fixed safe failure category;
- clear source proof;
- remove owned scratch.

### Browser reload

- `sessionStorage` retains exact-run session token;
- browser calls `GET /v1/state` and restores typed launcher state;
- in-progress generation remains authoritative in launcher memory.

### Browser/tab close

- no destructive action follows;
- heartbeat expiry after 60 seconds invalidates browser authority;
- clear retained source proof/path;
- cancel picker/validation ownership;
- clean owned scratch;
- ordinary backend data unchanged.

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

Validation scratch never becomes durable Restore operation, phase, recovery trigger or working-DB mutation.

## Failure behavior

Control-plane failure is fail-closed for Restore control only.

If control plane cannot bind/authenticate/validate Host+Origin/parse command/maintain session invariants:

- no picker/validation authority is granted;
- no destructive Restore work begins;
- ordinary backend may continue normal product operation when safe;
- browser gets fixed human-readable Restore-unavailable guidance;
- technical detail remains local.

## Dependency decision

CR-011 authorizes **no new application dependency**.

Future C4-II-A is expected to use:

- Python standard library for launcher-owned HTTP control boundary;
- `/usr/bin/osascript` with macOS Standard Additions `choose file` for picker;
- existing C4-I project code for intake/staging/validation.

If implementation cannot satisfy the decision within those boundaries, stop and open a new architecture/change request rather than adding PyObjC, Electron, Tauri, pywebview, tkinter, WebSocket frameworks or another dependency by assumption.

## Packaging implications

Future C4-II-A will require packaged launcher to:

- remain alive for browser/product session;
- own ephemeral control listener and worker/concurrency lifecycle;
- open browser with one-use bootstrap fragment;
- own short-lived `/usr/bin/osascript` picker helper;
- clean validation proof/scratch/tokens at shutdown.

This ADR does not implement `.app`/`.dmg` packaging and does not authorize general native shell.

Mac App Store sandboxing is outside current MVP packaging contract.

## C4-II-A implementation boundary

C4-II-A, when separately authorized, may implement only:

- launcher control-plane bootstrap/session + concurrency boundary described here;
- browser Restore selection/validation presentation;
- launcher-owned macOS picker adapter;
- non-destructive validation-session service;
- shared-safe refactor needed to reuse C4-I staging/validation semantics;
- typed safe results/cancel/reselect state;
- bounded validation scratch/proof cleanup;
- tests and exact-head smoke for this boundary.

C4-II-A must not implement destructive confirmation or call destructive execution boundary.

## Required future tests and exact-head smoke

Automated C4-II-A tests must prove at least:

1. control plane binds only `127.0.0.1` on ephemeral port;
2. wrong/missing Host or Origin is refused;
3. wildcard CORS is absent;
4. bootstrap token is atomic one-use even under concurrent exchange attempts;
5. old-run/invalid session tokens are refused;
6. control responses are `no-store`;
7. heartbeat/state/cancel remain serviceable while picker/validation action is in flight;
8. request replay never repeats picker/validation action;
9. duplicate concurrent select is refused;
10. stale generation cannot publish;
11. cancel/reselect/session-expiry clears retained source proof;
12. browser payload contains no absolute path;
13. picker cancellation is typed/non-destructive;
14. source remains byte-identical;
15. validation creates no durable Restore operation/phase/safety copy/AuditLog event;
16. working database remains unchanged;
17. backend remains usable during validation;
18. scratch cleanup removes only owned paths;
19. next-run cleanup ignores foreign/unproved paths;
20. browser reload recovers safe state;
21. heartbeat expiry invalidates control authority and prevents stale publication.

Exact-head macOS smoke must exercise the **real** boundary:

```text
real launcher run
→ real browser Restore screen
→ real authenticated launcher control request
→ real /usr/bin/osascript native picker
→ select temporary known application backup
→ real launcher candidate preparation/validation
→ typed result delivered to browser
→ keep picker/validation in flight long enough to prove heartbeat/state responsiveness
→ cancel/reselect scenario
→ verify source bytes unchanged
→ verify no durable Restore operation/safety copy/working-DB change
→ verify retained proof cleared after cancel/session expiry
→ verify control plane/picker/scratch cleanup and no owned process remains
```

Human selection of prepared temporary backup in real native dialog is acceptable. Injecting final validation result or bypassing picker/control/session boundary is insufficient.

## Consequences

Positive:

- preserves browser-first UX;
- keeps Restore authority launcher-owned;
- no ordinary backend Restore mutation;
- no new application dependency;
- no absolute path in browser state;
- exact-run local control security/concurrency are explicit;
- future implementation scope is bounded/testable;
- C4-I safety primitives remain source of truth.

Costs:

- launcher gains one narrow loopback server, worker coordination and session state in C4-II-A;
- frontend performs one-time exact-run bootstrap;
- security/concurrency boundary requires dedicated tests;
- browser tab loss intentionally cancels Restore-control authority after timeout;
- App Store sandbox packaging may require future picker-adapter decision.

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