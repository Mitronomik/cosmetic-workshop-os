# ADR 0018 — Launcher-owned loopback Restore control plane and validation session

## Status

`ACCEPTED BY CR-011 CHANGESET — NORMATIVE ONLY WHEN PRESENT ON main` — 2026-08-07.

This ADR decides `CR-011 — Launcher Restore interaction and non-destructive validation-session boundary`.

It does **not** authorize C4-II-A runtime implementation. A separate bounded task must authorize C4-II-A after this decision is merged and independently audited.

This ADR does not amend the durable Restore safety semantics accepted by ADR 0016. The twelve durable phases, transition graph, startup recovery matrix, `replacement_intent` rule, launcher ownership of destructive Restore, immutable-source rule, mandatory `before_restore` safety copy, and Restore AuditLog boundary remain unchanged.

## Context

PR #171 is merged. Its merge commit is:

`76ab59216047222714a32f2793a789b3dc8df19a`

The current implementation has these relevant facts:

- `launcher.main` owns application startup;
- `launcher.runtime` starts the ordinary local backend and opens the ordinary system browser through `webbrowser.open(...)`;
- the ordinary browser is the product presentation surface;
- the local backend is the business API and is not the owner of destructive Restore;
- the launcher owns Restore lifecycle authority;
- C4-I exposes `execute_restore(...)`, startup recovery, source intake, immutable-source staging, candidate validation, backend exclusion, replacement and rollback infrastructure;
- C4-I does not expose a public non-destructive validation-session application service;
- the browser has no accepted channel for asking the launcher to open a native picker;
- the browser must never become authoritative for an absolute selected-source path.

Existing C4-I primitives already provide the safety semantics future candidate preparation must reuse:

- `open_selected_source(...)` validates an absolute local path, refuses symlinks/directories/unsupported sources, checks sidecars, opens one held read-only descriptor and proves source identity;
- `HeldSource.revalidate()` re-proves descriptor and path identity;
- `HeldSource.digest()` computes a full SHA-256 digest through the held descriptor;
- `stage_source(...)` copies through the held descriptor, performs two digest passes, re-checks sidecars and identity, and publishes only a stable candidate;
- `validate_staged_candidate(...)` opens the staged candidate read-only and verifies structural health, migration lineage and workshop identity.

CR-011 exists because C4-II-A must not invent a browser-to-launcher channel, picker technology, security model, path-privacy model or validation-session lifetime inside runtime code.

## Decision drivers

The selected architecture must:

1. preserve the ordinary browser as the familiar product UI;
2. keep filesystem authority in the launcher;
3. keep the absolute selected-source path out of browser and ordinary backend state;
4. bind any control channel to one exact local launcher run;
5. remain local-first and work without internet;
6. avoid turning Restore into an ordinary FastAPI mutation;
7. avoid introducing a broad desktop-shell rewrite merely to open one picker;
8. keep future packaged use possible without requiring terminal, Git, Python or Node.js from the user;
9. reuse C4-I source-intake/staging/validation safety rather than duplicate it;
10. make stale results, duplicate actions and replay safely rejectable;
11. have bounded cleanup after cancellation, browser loss, launcher exit and interruption;
12. keep C4-II-A non-destructive.

## Considered alternatives

### Option A — launcher-native pre-start Restore flow

The launcher would own both presentation and source selection before the ordinary browser flow.

Advantages:

- no browser-to-launcher control channel;
- source path naturally remains launcher-only;
- fewer cross-origin security concerns.

Rejected because:

- the project does not currently have a native application shell or native navigation surface;
- a pre-start prompt on every launch would make ordinary startup less direct for a non-technical user;
- a separate native Restore application/menu would introduce packaging and shell architecture before packaging itself is complete;
- presenting candidate validation and retry guidance outside the ordinary product UI would duplicate UI concepts and accessibility/error-state work;
- selecting this option would effectively make CR-011 a native-shell redesign rather than a bounded Restore interaction decision.

### Option B — narrowly authenticated launcher-owned loopback control plane

The ordinary browser remains the presentation surface. A separate launcher-owned loopback control boundary accepts only a tiny Restore-control vocabulary for the exact launcher run.

Advantages:

- preserves the current browser product model;
- keeps the ordinary FastAPI business API unchanged;
- keeps picker/path/validation authority in the launcher;
- can be implemented with Python standard-library HTTP primitives and one macOS system helper, with no new application dependency;
- allows typed non-technical validation results to stay in the existing UI;
- is independently testable as a narrow security boundary.

Cost:

- requires exact-run authentication, explicit origin handling, replay protection and session cleanup;
- requires a bootstrap handshake between launcher and browser;
- requires careful browser-refresh/tab-loss behavior.

**Selected: Option B.**

## Selected architecture

Use a **launcher-owned loopback Restore control plane** that is separate from the ordinary FastAPI backend.

The control plane:

- runs inside the launcher process;
- binds only to `127.0.0.1`;
- binds an OS-assigned ephemeral port (`port 0` at bind time), not a fixed public port;
- exists only for one launcher run;
- exposes only the bounded Restore-control vocabulary defined below;
- never exposes an ordinary business API;
- never accepts unauthenticated requests;
- never receives or returns an authoritative source path from/to the browser;
- is shut down before launcher process exit.

No WebSocket is selected. The control contract is small HTTP/JSON request-response traffic.

No new runtime dependency is authorized by CR-011. A future C4-II-A implementation should use Python standard-library HTTP/server primitives unless a later decision explicitly authorizes another dependency.

## Process topology

```text
macOS user
  ↓
ordinary browser / SPA
  ├── ordinary business requests ──→ FastAPI backend on 127.0.0.1
  │
  └── Restore control requests ────→ launcher-owned control plane
                                      127.0.0.1:<ephemeral-port>
                                               ↓
                                      launcher validation-session service
                                               ↓
                       launcher-owned /usr/bin/osascript picker helper
                                               ↓
                                      absolute selected path
                                      stays launcher-owned
                                               ↓
                         C4-I intake / staging / validation primitives

working database remains untouched during C4-II-A
```

The ordinary backend and the launcher control plane are separate authorities even though both are loopback services.

## User interaction flow

Future C4-II-A should use the normal application UI, expected under a dedicated Restore screen/route owned by the browser presentation layer.

The flow is:

```text
open application normally
→ browser establishes an exact-run launcher control session
→ user opens Restore screen
→ user chooses “Выбрать резервную копию”
→ browser sends authenticated select command to launcher control plane
→ launcher opens native macOS picker
→ selected absolute path is returned only to launcher
→ launcher prepares and validates a temporary candidate
→ launcher returns typed safe presentation result
→ browser shows accepted/rejected/cancelled state
```

The browser never receives the absolute path and never uploads the file bytes as the authoritative Restore source.

## Native picker ownership

The launcher owns the picker action and all filesystem authority.

The selected future macOS picker adapter is:

- an owned short-lived child process invoking `/usr/bin/osascript`;
- macOS Standard Additions `choose file` provides the native file dialog;
- the script returns the selected file's POSIX path only to the launcher process;
- the browser and ordinary backend receive no absolute path;
- `shell=True` is forbidden;
- user-controlled text must not be interpolated into executable AppleScript source;
- the picker must not use `System Events` or control another application;
- picker cancellation is a typed cancellation, not a technical error.

No new Python package is required or authorized for this picker.

The picker may show a friendly filename/type hint, but filename or extension is never compatibility authority. Full C4-I intake and candidate validation still decides acceptance.

### Packaging consequence

The current packaging target is a non-sandboxed local macOS application/package. `/usr/bin/osascript` is a macOS system dependency and is not bundled.

CR-011 does not claim Mac App Store sandbox compatibility. If a future commercial/App-Store packaging decision requires a sandboxed `NSOpenPanel` or security-scoped file access, that requires a separate packaging decision. Such a later adapter change must preserve the launcher-owned picker/path boundary decided here.

## Browser bootstrap and exact-run security model

### Control-plane bind

- address: exactly `127.0.0.1`;
- port: ephemeral OS-assigned port;
- no `0.0.0.0`, LAN address or remote binding;
- control plane lifetime: one launcher run only.

### Allowed browser origin

The launcher derives one exact allowed origin from the configured `frontend_url` for the current run.

For user-mode C4-II-A, the accepted origin must be local HTTP on `127.0.0.1` with the configured frontend port. A different host/origin must be refused rather than added dynamically.

CORS:

- one exact allowed origin only;
- no wildcard origin;
- no credentialed cookie session;
- only the required methods and headers;
- preflight responses must not broaden the accepted origin/method/header set.

### Bootstrap token

At launcher startup, before opening the browser, the launcher creates:

- one opaque launcher `run_id`;
- one cryptographically random bootstrap token with at least 256 bits of entropy;
- the control-plane ephemeral port.

The browser launch URL carries only the control port and one-time bootstrap token in the **URL fragment**, not query parameters.

Conceptual example:

```text
http://127.0.0.1:5173/#cw-control=<ephemeral-port>:<one-time-bootstrap-token>
```

The exact serialization may change, but these properties are mandatory:

- the fragment is not sent in the HTTP request to the frontend server;
- the frontend reads it once;
- the frontend exchanges it with the control plane;
- the launcher invalidates the bootstrap token after the first successful exchange;
- the frontend immediately removes the bootstrap fragment from the visible URL with `history.replaceState(...)` or equivalent;
- the bootstrap token is never written to logs, localStorage, application data or durable files.

### Run-scoped browser session token

A successful bootstrap returns a second cryptographically random session token, also at least 256 bits.

The session token:

- is valid only for the exact launcher `run_id`;
- is kept in browser `sessionStorage`, never `localStorage`;
- is sent in an explicit authorization header, not in URLs;
- is bound to the exact allowed Origin;
- is invalidated on launcher exit/restart;
- is invalidated when the browser control session times out;
- is never persisted by the launcher;
- is never logged.

A token from an earlier launcher run is always invalid.

### Browser liveness

The browser sends an authenticated heartbeat while a Restore control session is active.

Future C4-II-A should use:

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without an authenticated heartbeat or other authenticated control request.

On expiry the launcher:

- invalidates the browser control session token;
- increments/invalidate the active selection generation;
- terminates an owned picker helper if one is still active;
- prevents an old validation result from becoming current;
- cleans only provably owned validation scratch state.

Ordinary backend/product state is not mutated by this timeout.

## Narrow control vocabulary

C4-II-A may expose only these conceptual operations:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

Names may be adjusted during implementation, but equivalent scope is mandatory.

There is deliberately **no** execute/confirm/destructive Restore command in C4-II-A.

The control plane must not grow generic filesystem, shell, SQL, backend proxy or arbitrary launcher command endpoints.

## Replay, duplicate-action and stale-result protection

Every authenticated non-read control request carries a cryptographically strong request ID.

The launcher maintains a bounded per-run idempotency/replay ledger.

Rules:

- the same request ID never executes an action twice;
- a duplicate completed request returns/references the same safe result rather than repeating the picker or validation;
- a duplicate still in progress reports the same in-progress ownership, not a second operation;
- a new `select` while a picker/validation action already owns the session is refused as `action_in_progress`;
- accepted select/cancel/reselect actions advance a monotonically increasing selection generation;
- validation results may become current only if their captured generation still equals the active generation;
- cancellation or reselection invalidates every older generation before cleanup begins;
- a response from a stale generation is discarded and cannot overwrite the current browser-visible result.

## Validation-session ownership

Future C4-II-A must add one launcher-owned non-destructive application boundary conceptually equivalent to:

```text
prepare_restore_candidate(...)
```

Suggested module responsibility boundaries for later implementation are:

```text
launcher/control_plane.py
launcher/restore/picker_macos.py
launcher/restore/validation_session.py
```

The names are not a public API commitment. Ownership is the commitment.

The validation-session service must:

- never call `execute_restore(...)`;
- create no durable Restore operation record;
- enter none of the twelve Restore phases;
- create no `before_restore` safety copy;
- replace no working database;
- migrate no working database;
- perform no rollback or startup-recovery mutation;
- write no Restore AuditLog event;
- leave the selected source byte-identical;
- use isolated launcher-owned temporary validation staging distinct from `RestoreWorkspace` durable operation directories;
- reuse C4-I `open_selected_source(...)`, `HeldSource` identity/digest semantics, `stage_source(...)` semantics and `validate_staged_candidate(...)` rules through shared collaborators rather than implementing weaker copies;
- return typed presentation-safe results only;
- keep raw SQLite errors, migration IDs, internal absolute paths and stack traces in local technical logs only;
- expose only opaque session/run/generation identifiers to the browser;
- never claim that Restore completed.

If current C4-I `stage_source(...)` is too tightly coupled to `RestoreWorkspace`, C4-II-A may perform a bounded refactor that extracts a shared lower-level staging primitive while preserving all existing C4-I behavior and tests. It must not create a second staging algorithm.

## Validation scratch ownership

Temporary validation staging is not a Restore operation.

Use one canonical launcher-owned scratch root under the current user's system temporary directory, conceptually:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<validation-session-id>/
```

Requirements:

- canonical root resolved by launcher code only;
- random opaque run/session directory names;
- no user-provided path component in scratch paths;
- no symlink traversal;
- owned marker/version metadata sufficient to prove cleanup ownership;
- candidate scratch never appears under durable Restore operation directories;
- cleanup refuses paths outside the canonical scratch root;
- interruption cleanup only removes recognized owned session directories.

## Typed presentation result and path privacy

Browser-visible state may contain only safe facts such as:

- opaque run/session identity;
- selection generation;
- safe display filename/label;
- `idle`, `selecting`, `validating`, `accepted`, `rejected`, `cancelled`, `technical_failure`;
- current-schema compatibility;
- older-supported-schema compatibility;
- fixed rejection category;
- fixed user guidance;
- stale/cancelled state.

It must not contain:

- absolute source path;
- staged candidate path;
- raw SQL/SQLite text;
- migration IDs;
- stack traces;
- operation-record contents;
- arbitrary database contents.

A safe filename is presentation only and is never proof of compatibility or authority.

## Retained source identity and C4-II-B handoff

After successful C4-II-A validation, the temporary staged candidate is cleaned.

The launcher retains only in-memory validation authority for the current launcher run:

- canonical absolute selected-source path, launcher-private;
- C4-I `SourceIdentity` facts captured from the held descriptor;
- a full SHA-256 digest captured from the held descriptor;
- the successful validation generation;
- typed compatibility result.

None of those facts leave launcher-owned state except the safe typed compatibility result.

The opaque browser validation-session token is a reference only. It is not authority.

Future C4-II-B must, before destructive Restore:

1. reopen the launcher-private original path through the accepted C4-I source-intake boundary;
2. prove the reopened descriptor/path identity matches the retained identity;
3. recompute and compare the full SHA-256 digest;
4. re-check source sidecars/self-containment;
5. stage again through the accepted C4-I staging semantics;
6. validate the newly staged candidate again;
7. only then enter the existing destructive C4-I execution boundary that creates the mandatory safety copy and durable Restore operation.

Any mismatch invalidates the old validation session and returns to source selection. Browser state, filename, extension or token possession can never bypass this re-proof.

## Backend lifecycle

The ordinary backend remains running during C4-II-A:

- file selection;
- source intake;
- temporary staging;
- candidate validation;
- presentation of validation result.

Reason:

- C4-II-A is strictly non-destructive;
- candidate validation operates on an isolated staged copy;
- it does not replace/migrate the working database;
- it does not require the destructive backend-stop proof or maintenance lease used by C4-I execution;
- stopping the backend during simple source selection would unnecessarily interrupt the product UI and blur the boundary between validation and execution.

Future C4-II-B remains responsible for the existing C4-I backend exclusion/stop proof before destructive work.

## Cancellation, reselection and cleanup

### Picker cancel

- no durable Restore operation;
- no safety copy;
- generation advances to cancelled state;
- no old result may publish afterward;
- owned scratch is removed;
- user receives a normal cancelled state.

### Reselection

- invalidate the previous generation first;
- terminate/finish ownership of the previous picker/validation action;
- clean previous owned scratch;
- then begin the next generation.

### Validation rejection

- retain only the safe rejection category needed for presentation;
- remove staged scratch;
- source remains byte-identical.

### Technical validation failure

- raw detail goes only to local technical logs;
- browser receives a fixed safe failure category/guidance;
- owned scratch is removed.

### Browser reload

- `sessionStorage` retains the exact-run session token;
- browser calls `GET /v1/state` and restores typed launcher-owned state;
- an in-progress generation remains authoritative in launcher memory.

### Browser/tab close

- no destructive action follows from tab close;
- missing heartbeat expires the browser control session after 60 seconds;
- any picker/validation ownership is cancelled and owned scratch is cleaned;
- ordinary backend data is unchanged.

### Launcher normal exit

- invalidate all bootstrap/session tokens;
- advance/cancel any active generation;
- terminate the owned picker helper if necessary;
- remove owned validation scratch;
- shut down the control plane.

### Launcher crash / machine interruption

No token survives process loss.

On the next launcher start, before creating a new validation session, perform bounded cleanup only under the canonical validation scratch root and only for directories whose owned marker/path shape can be proved.

Validation scratch must never be interpreted as a durable Restore operation, must never trigger a Restore phase, and must never cause working-database mutation.

## Failure behavior

Control-plane failure is fail-closed for Restore control only.

If the control plane cannot bind, authenticate, validate origin, parse a command or maintain its session invariants:

- no picker/validation authority is granted;
- no destructive Restore work begins;
- the ordinary backend may continue normal product operation when safe;
- browser receives only a fixed human-readable Restore-unavailable message;
- technical detail remains local.

## Dependency decision

CR-011 authorizes **no new application dependency**.

Future C4-II-A is expected to use:

- Python standard library for the launcher-owned HTTP control boundary;
- `/usr/bin/osascript` with macOS Standard Additions `choose file` for the picker;
- existing project/C4-I code for intake, staging and validation.

If implementation cannot satisfy the decision with those boundaries, stop and open a new architecture/change request rather than adding PyObjC, Electron, Tauri, pywebview, tkinter, WebSocket frameworks or another dependency by assumption.

## Packaging implications

C4-II-A will eventually require the packaged launcher to:

- keep the launcher process alive for the browser/product session;
- own the ephemeral control-plane listener;
- open the browser with the one-time bootstrap fragment;
- own the short-lived `/usr/bin/osascript` picker helper;
- clean validation scratch and tokens at shutdown.

This ADR does not implement `.app`/`.dmg` packaging and does not authorize a general native shell.

Mac App Store sandboxing is explicitly outside the current MVP packaging contract.

## C4-II-A implementation boundary

C4-II-A, when separately authorized, may implement only:

- launcher control-plane bootstrap/session infrastructure described here;
- the dedicated browser Restore selection/validation presentation;
- the launcher-owned macOS picker adapter;
- non-destructive validation-session service;
- shared-safe refactor needed to reuse C4-I staging/validation semantics;
- typed safe results and cancellation/reselection state;
- bounded validation scratch cleanup;
- tests and exact-head smoke for that boundary.

C4-II-A must not implement destructive confirmation or call the destructive execution boundary.

## Required future tests and exact-head smoke

C4-II-A must include automated tests proving at least:

1. control plane binds only `127.0.0.1` on an ephemeral port;
2. wrong/missing Origin is refused;
3. bootstrap token is one-use and run-scoped;
4. old-run and invalid session tokens are refused;
5. wildcard CORS is absent;
6. request replay does not repeat picker/validation action;
7. duplicate concurrent select is refused;
8. stale generation result cannot publish;
9. browser-visible payload contains no absolute path;
10. picker cancellation is typed and non-destructive;
11. source remains byte-identical;
12. validation creates no durable Restore operation, phase, safety copy or AuditLog event;
13. working database remains unchanged;
14. backend remains usable during validation;
15. validation scratch cleanup removes only owned paths;
16. next-run cleanup ignores foreign/unproved paths;
17. browser reload recovers safe state through the same exact-run session;
18. heartbeat expiry invalidates control authority and prevents stale publication.

Exact-head macOS smoke must exercise the **real** boundary:

```text
real launcher run
→ real browser Restore screen
→ real launcher control request
→ real /usr/bin/osascript native picker
→ select a temporary known application backup
→ real launcher candidate preparation and validation
→ typed result delivered to browser
→ cancel/reselect scenario
→ verify source bytes unchanged
→ verify no durable Restore operation/safety copy/working-DB change
→ verify launcher/control-plane cleanup and no owned process remains
```

The smoke may require a human to choose the prepared temporary backup in the real native dialog. Injecting a final validation result or bypassing the picker/control/session boundary is not sufficient.

## Consequences

Positive:

- preserves browser-first product UX;
- keeps Restore authority launcher-owned;
- no ordinary backend Restore mutation;
- no new dependency;
- no absolute source path in browser state;
- exact-run local control security is explicit;
- future implementation scope is bounded and testable;
- C4-I safety primitives remain the source of truth.

Costs:

- launcher gains one narrow loopback server and session state in C4-II-A;
- frontend must perform a one-time exact-run bootstrap;
- control channel requires dedicated security tests;
- browser tab loss intentionally cancels Restore-control authority after a short timeout;
- App Store sandbox packaging may require a future picker-adapter decision.

## Explicit non-goals

This ADR does not authorize or implement:

- C4-II-A runtime code;
- C4-II-B/C4-II-C/C4-III;
- destructive Restore confirmation;
- changes to the twelve-phase state machine;
- an ordinary FastAPI Restore endpoint;
- browser upload as Restore source authority;
- SPA filesystem authority;
- wildcard CORS;
- a generic localhost command server;
- WebSocket/IPC architecture;
- PyObjC/Electron/Tauri/pywebview/tkinter dependency adoption;
- `.app`/`.dmg` packaging implementation;
- App Store sandbox support;
- cloud sync, OCR, roles, multi-user work or unrelated product features.

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