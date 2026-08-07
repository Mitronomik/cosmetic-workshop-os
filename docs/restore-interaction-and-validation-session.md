# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-07`

Normative sources:

- `docs/decisions/0016-launcher-assisted-restore.md` — durable Restore safety and twelve-phase state machine;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — C4-I lifecycle closure and decision-only CR-011 gate;
- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md` — selected CR-011 interaction architecture;
- `docs/current-lifecycle.md` — current implementation authorization.

ADR 0018 is newer only for the CR-011 interaction/validation-session topic. It does not amend ADR 0016 safety semantics and does not authorize C4-II-A runtime work.

## Current lifecycle

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

On a CR-011 PR branch the decision becomes project authority only when the changeset is present on `main`.

## Selected interaction architecture

CR-011 selects a **narrowly authenticated launcher-owned loopback control plane**.

```text
ordinary browser / SPA
  ├── business API ──→ ordinary FastAPI backend
  └── Restore control ──→ launcher control plane
                           127.0.0.1:<ephemeral>
                                  ↓
                           action/session coordinator
                             ├── owned picker worker
                             └── validation worker
                                  ↓
                    C4-I intake/staging/validation
```

The control plane is separate from the ordinary backend, is not a generic command server, and has no destructive execute/confirm operation in C4-II-A.

No WebSocket is selected. No new application dependency is authorized.

## Control-plane bind, Host and Origin

Future C4-II-A must enforce:

- bind exactly `127.0.0.1`;
- OS-assigned ephemeral control port;
- no `0.0.0.0`, LAN or remote binding;
- HTTP `Host` equal to the actual `127.0.0.1:<bound-port>` authority;
- one exact allowed Origin derived from the configured local `frontend_url`;
- user-mode Origin must be local HTTP on `127.0.0.1` with the configured frontend port;
- no wildcard CORS;
- no credentialed cookie session;
- only required methods/headers and no broadened preflight response.

A browser page without a valid launcher control session must fail closed with human-readable guidance to open/restart the application normally. It must never fall back to browser upload or an ordinary FastAPI Restore endpoint.

## Bootstrap and exact-run authority

Before opening the browser, launcher creates:

- opaque launcher `run_id`;
- one-use bootstrap token with at least 256 bits of cryptographic entropy;
- control-plane ephemeral port.

Launcher passes control port + bootstrap token in the browser URL **fragment**, never query parameters.

Conceptually:

```text
http://127.0.0.1:5173/#cw-control=<ephemeral-port>:<bootstrap-token>
```

Mandatory bootstrap behavior:

- fragment is not sent to the frontend HTTP server;
- frontend reads it once and exchanges it through `POST /v1/bootstrap`;
- bootstrap is an **atomic compare-and-consume** operation;
- exactly one concurrent exchange may succeed;
- every replay/concurrent loser is refused;
- frontend removes the fragment immediately after success using `history.replaceState(...)` or equivalent;
- bootstrap token is never logged or persisted.

Successful bootstrap returns a second run-scoped session token with at least 256 bits of entropy.

The session token:

- is valid only for the current `run_id`;
- is stored only in browser `sessionStorage`, never `localStorage`;
- is sent in an explicit authorization header, never a URL;
- is bound to exact allowed Origin;
- is invalidated on launcher exit/restart or session expiry;
- is never persisted or logged.

All bootstrap/control responses that contain session or validation state must use `Cache-Control: no-store` and equivalent no-cache behavior where applicable.

## Mandatory control-plane concurrency

A long-running select/picker/validation action must **not** block the only control-plane request loop.

Future C4-II-A must use a `ThreadingHTTPServer`-equivalent concurrent request model or equivalent launcher-owned dispatcher/worker coordination so that while picker/validation is in flight:

- heartbeat remains serviceable;
- `GET /v1/state` remains serviceable;
- `POST /v1/restore/cancel` remains serviceable;
- session timeout can still be enforced;
- an owned picker helper can be terminated after cancellation/session expiry.

Concurrency does not create multiple mutation owners. Explicit launcher-owned synchronization must still permit at most one picker/validation owner for one control session.

## Browser liveness

While a Restore control session is active:

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without authenticated heartbeat or other authenticated control request.

On expiry launcher must atomically:

- invalidate the browser session token;
- invalidate/advance current selection generation;
- terminate owned picker helper if active;
- prevent stale validation result publication;
- clear launcher-private retained source proof/path;
- clean only provably owned validation scratch;
- leave ordinary backend/workshop data unchanged.

Browser reload may recover through current `sessionStorage` token + `GET /v1/state`.

## Narrow control vocabulary

C4-II-A may expose only an equivalent of:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

No arbitrary filesystem, shell, SQL, backend-proxy or generic launcher command endpoint is allowed.

## Replay, duplicate and stale-result protection

Every authenticated non-read command carries a cryptographically random request ID with at least 128 bits of entropy.

Launcher keeps a bounded per-run replay/idempotency ledger:

- same request ID never executes twice;
- duplicate completed request returns/references the same safe result;
- duplicate in-progress request does not create second ownership;
- a new `select` while picker/validation already owns the session is refused as action-in-progress;
- accepted select/cancel/reselect advances a monotonically increasing selection generation;
- result may publish only if its captured generation remains current;
- cancel/reselect invalidates older generation and clears retained proof for that generation before new authority is established;
- stale result is discarded and cannot overwrite current browser state.

## Native macOS picker

Launcher owns picker authority.

Future adapter:

```text
launcher
→ owned short-lived /usr/bin/osascript child
→ macOS Standard Additions `choose file`
→ selected POSIX path returned only to launcher
```

Requirements:

- no `shell=True`;
- no user-controlled text interpolated into executable AppleScript;
- no `System Events` automation of another application;
- typed ordinary cancellation;
- no absolute path returned to browser or ordinary backend;
- filename/type filter is a presentation hint only, never compatibility authority.

No PyObjC, Electron, Tauri, pywebview, tkinter or other new runtime dependency is authorized.

Mac App Store sandbox compatibility is not claimed. A future sandbox packaging decision may replace the adapter while preserving launcher ownership and path privacy unless a later ADR explicitly changes them.

## Mandatory non-destructive validation boundary

Future C4-II-A must implement a launcher-owned service conceptually equivalent to:

```text
prepare_restore_candidate(...)
```

It must:

- never call `execute_restore(...)`;
- create no durable Restore operation;
- enter none of the twelve durable Restore phases;
- create no `before_restore` safety copy;
- replace no working database;
- migrate no working database;
- perform no rollback/startup-recovery mutation;
- write no Restore AuditLog event;
- leave original selected source byte-identical;
- use isolated launcher-owned temporary validation staging outside durable Restore operation workspaces;
- reuse C4-I `open_selected_source(...)`, `HeldSource` identity/revalidation/digest semantics, stable two-pass staging semantics and `validate_staged_candidate(...)` through shared collaborators;
- return typed presentation-safe results only;
- keep raw SQLite errors, stack traces, migration IDs and internal paths in local technical logs only;
- expose only opaque run/session/generation identifiers;
- never claim Restore completed.

If current `stage_source(...)` is too coupled to `RestoreWorkspace`, C4-II-A may make a bounded refactor extracting one shared lower-level staging primitive while preserving all existing C4-I behavior/tests. A second weaker staging algorithm is forbidden.

## Validation scratch ownership

Use a canonical launcher-owned root under current user's system temp area, conceptually:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

Rules:

- root resolved by launcher code only;
- opaque random run/session components;
- no user-provided path component;
- no symlink traversal;
- ownership/version marker sufficient to prove cleanup;
- cleanup refuses paths outside canonical root;
- scratch never appears as a durable Restore operation;
- next-run cleanup removes only recognized/proved owned session directories.

## Typed browser-visible result

Allowed browser facts:

- opaque run/session identity;
- selection generation;
- safe display filename/label;
- state: idle/selecting/validating/accepted/rejected/cancelled/technical_failure;
- current-schema / older-supported-schema compatibility;
- fixed rejection category and safe guidance;
- stale/cancelled state.

Forbidden browser facts:

- absolute source path;
- staged candidate path;
- raw SQL/SQLite text;
- migration IDs;
- stack traces;
- operation-record contents;
- arbitrary database contents.

Displayed filename is never compatibility/authority proof.

## Retained launcher-private proof

After successful validation, temporary staged candidate is deleted.

Launcher may retain, **for the current authenticated control session only**:

- canonical absolute source path, launcher-private;
- C4-I `SourceIdentity` facts;
- full SHA-256 digest captured from held descriptor;
- successful selection generation;
- typed compatibility result.

Browser session token references this state but is not authority.

Retained source proof/path must be cleared on:

- cancel;
- reselection before new generation becomes authoritative;
- validation rejection;
- validation technical failure;
- browser control-session expiry;
- launcher normal exit;
- any transition invalidating the successful generation.

No in-memory proof/token survives launcher crash.

## Future C4-II-B re-proof

Before destructive execution future C4-II-B must:

```text
reopen launcher-private original path through C4-I intake
→ compare descriptor/path SourceIdentity
→ recompute and compare full SHA-256
→ re-check sidecars/self-containment
→ stage again through C4-I semantics
→ validate again
→ only then enter existing C4-I destructive execution boundary
```

Any mismatch invalidates prior validation and returns to source selection. Browser state, filename, extension or token possession cannot bypass re-proof.

## Backend lifecycle

The ordinary backend remains running during:

- native file selection;
- source intake;
- temporary staging;
- candidate validation;
- validation-result presentation.

C4-II-A is non-destructive and operates on source + isolated staged copy. Existing C4-I backend stop/exclusion proof remains a future C4-II-B destructive boundary.

## Cleanup matrix

| Event | Required behavior |
|---|---|
| Picker cancel | invalidate generation; clear retained proof; no durable operation/safety copy; clean owned scratch |
| Reselect | invalidate old generation and clear old proof first; end old ownership; clean scratch; then establish next generation |
| Validation rejection | keep safe rejection category only; clear proof; clean staged scratch |
| Technical failure | technical detail local only; safe browser message; clear proof; clean scratch |
| Browser reload | restore typed state through current run-scoped session |
| Browser/tab close | heartbeat expiry invalidates control authority, clears proof, cancels active picker/validation, cleans owned scratch |
| Launcher normal exit | invalidate tokens/generation, clear proof, terminate picker, clean scratch, stop control plane |
| Launcher crash/machine interruption | no token/proof survives; next run cleans only recognized owned scratch |

Validation scratch must never trigger a Restore phase, startup recovery or working-database mutation.

## Future C4-II-A minimum tests

At minimum prove:

1. loopback-only ephemeral bind;
2. wrong/missing Host or Origin rejected;
3. no wildcard CORS;
4. bootstrap atomic one-use under concurrent exchange attempts;
5. old-run/wrong session token rejected;
6. state/session responses use `Cache-Control: no-store`;
7. heartbeat/state/cancel remain serviceable while picker/validation is in flight;
8. replay does not repeat action;
9. duplicate concurrent select rejected;
10. stale generation cannot publish;
11. cancel/reselect/session-expiry clears retained source proof;
12. browser payload contains no absolute path;
13. picker cancellation typed/non-destructive;
14. valid current and supported older backups accepted;
15. newer/foreign/empty/corrupt/directory/symlink/path-escape inputs rejected;
16. original source remains byte-identical;
17. no durable Restore operation/phase/safety copy/AuditLog event;
18. no working database replacement/migration;
19. backend remains usable during validation;
20. cleanup removes only proved owned scratch;
21. next-run cleanup ignores foreign/unproved paths;
22. browser reload recovers safe state;
23. heartbeat expiry invalidates stale control authority.

## Future exact-head macOS smoke

Smoke must use the real selected architecture:

```text
real launcher run
→ real browser Restore screen
→ real authenticated launcher-control request
→ real /usr/bin/osascript native picker
→ select prepared temporary workshop backup
→ real candidate preparation/validation
→ typed browser result
→ prove heartbeat/state remain responsive while picker/validation is in flight
→ cancel/reselect exercise
→ prove source bytes unchanged
→ prove no durable Restore operation/safety copy/working-DB change
→ prove retained proof clears after cancel/session expiry
→ prove owned processes/control plane/scratch cleaned
```

Injecting a final validation result or bypassing picker/control/session boundary is insufficient.

## Not authorized yet

This profile does not authorize:

- C4-II-A runtime implementation;
- C4-II-B/C4-II-C/C4-III;
- frontend Restore controls;
- launcher control-plane code;
- picker code;
- validation-session code;
- destructive Restore confirmation/execution;
- new dependencies;
- packaging implementation;
- changes to ADR 0016 state-machine/recovery semantics.

A separate post-CR-011 task must explicitly authorize bounded C4-II-A runtime work.