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

On a CR-011 PR branch the decision becomes project authority only when present on `main`.

## Selected interaction architecture

CR-011 selects a **narrowly authenticated launcher-owned loopback control plane**.

```text
ordinary browser / SPA
  ├── business API ──→ ordinary FastAPI backend
  └── Restore control ──→ launcher control plane
                           127.0.0.1:<ephemeral>
                                  ↓
                           action/session coordinator
                             ├── picker worker
                             └── validation worker
                                  ↓
                    C4-I intake/staging/validation
```

The control plane is separate from the ordinary backend, is not a generic local command server, and has no destructive execute/confirm operation in C4-II-A.

No WebSocket is selected. No new application dependency is authorized.

## Startup order

Future user-mode startup order is:

```text
acquire launcher lifecycle / instance authority
→ resolve interrupted C4-I Restore recovery gate
→ ordinary startup / migrations / backup-before-migration
→ start and prove ordinary backend ready
→ bind launcher control plane on 127.0.0.1:<ephemeral>
→ create exact-run bootstrap capability
→ open ordinary browser with bootstrap fragment
→ keep browser UI + backend + control plane under one launcher lifetime
```

If the control plane cannot start safely, normal product use may continue when otherwise safe, but Restore controls fail closed and no fallback transport is invented.

## Bind, Host and Origin

Future C4-II-A must enforce:

- bind exactly `127.0.0.1`;
- OS-assigned ephemeral control port;
- no `0.0.0.0`, LAN or remote binding;
- HTTP `Host` equal to actual `127.0.0.1:<bound-port>`;
- one exact allowed Origin derived from configured local `frontend_url`;
- user-mode Origin is local HTTP on `127.0.0.1` with configured frontend port;
- no wildcard CORS;
- no credentialed cookie session;
- only required methods/headers and no broadened preflight.

A page without a valid launcher session fails closed with human-readable guidance to open/restart the application normally; no browser-upload or FastAPI Restore fallback is allowed.

## Bootstrap and exact-run authority

Before opening the browser, launcher creates:

- opaque `run_id`;
- one-use bootstrap token with at least 256 bits of cryptographic entropy;
- control-plane ephemeral port.

Control port + bootstrap token enter the browser in the URL **fragment**, never query parameters.

Conceptually:

```text
http://127.0.0.1:5173/#cw-control=<ephemeral-port>:<bootstrap-token>
```

Mandatory behavior:

- fragment is not sent to frontend HTTP server;
- frontend exchanges it through `POST /v1/bootstrap`;
- bootstrap is an **atomic compare-and-consume** operation;
- exactly one concurrent exchange succeeds;
- replay/concurrent losers are refused;
- frontend immediately removes the fragment with `history.replaceState(...)` or equivalent;
- bootstrap capability is never logged or persisted.

Successful bootstrap returns a second run-scoped token with at least 256 bits of entropy.

The session token:

- is valid only for exact `run_id`;
- is stored only in browser `sessionStorage`, never `localStorage`;
- is sent in explicit authorization header, never URL;
- is bound to exact allowed Origin;
- is invalidated on launcher exit/restart/session expiry;
- is never persisted or logged.

All bootstrap/control responses containing session or validation state use `Cache-Control: no-store` and equivalent no-cache behavior where applicable.

## Mandatory control-plane concurrency

A long-running select/picker/validation action must **not** block the only control request loop.

Future C4-II-A must use a `ThreadingHTTPServer`-equivalent concurrent request model or equivalent launcher-owned dispatcher/worker coordination so that while picker/validation is in flight:

- heartbeat remains serviceable;
- `GET /v1/state` remains serviceable;
- cancel remains serviceable;
- session timeout remains enforceable;
- owned picker helper can be terminated after cancel/session expiry.

Concurrency never creates multiple authority owners. Explicit synchronization permits at most one picker/validation owner per control session.

## Browser liveness

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without authenticated heartbeat or other authenticated control request.

On expiry launcher atomically:

- invalidates browser token;
- invalidates/advances selection generation;
- terminates owned picker helper if active;
- prevents stale result publication;
- clear launcher-private retained source proof/path for that control session;
- cleans only proved owned validation scratch;
- leaves ordinary backend/workshop data unchanged.

Browser reload may recover via current `sessionStorage` token + `GET /v1/state`.

## Narrow control vocabulary

C4-II-A may expose only an equivalent of:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

No destructive execute/confirm endpoint belongs in C4-II-A. No arbitrary filesystem, shell, SQL, proxy or generic launcher endpoint is allowed.

## Replay, duplicate and command ordering

Each mutating control command carries:

- cryptographically random request ID with at least 128 bits of entropy;
- strictly monotonic `command_seq` scoped to the authenticated control session.

Launcher keeps bounded command state: highest accepted sequence, its request ID and safe in-progress/final result needed for retry.

Rules:

- next new mutation must use exactly the next sequence;
- lower sequence is permanently stale/replay and rejected;
- current sequence retries only when request ID matches, and do not re-execute;
- current sequence with a different request ID is rejected as conflict;
- skipped/future sequence is rejected;
- new select while picker/validation owns the session is action-in-progress;
- accepted select/cancel/reselect advances separate selection generation;
- result publishes only when captured generation remains current;
- cancel/reselect invalidates old generation and clears its retained proof before new source authority;
- stale results cannot overwrite browser state.

Heartbeat is an authenticated liveness signal and does not consume `command_seq`.

## Native macOS picker

Launcher owns picker authority.

```text
launcher
→ owned short-lived /usr/bin/osascript child
→ macOS Standard Additions `choose file`
→ POSIX selected path returned only to launcher
```

Requirements:

- no `shell=True`;
- no user-controlled text interpolated into AppleScript source;
- no `System Events` automation;
- typed cancellation;
- no absolute path returned to browser/ordinary backend;
- filename/type filter is presentation hint only.

No PyObjC, Electron, Tauri, pywebview, tkinter or other new runtime dependency is authorized.

Mac App Store sandbox compatibility is not claimed. A future sandbox decision may replace the adapter while preserving launcher ownership/path privacy unless a later ADR changes them.

## Mandatory non-destructive validation boundary

Future C4-II-A implements one launcher-owned service conceptually equivalent to:

```text
prepare_restore_candidate(...)
```

It must:

- never call `execute_restore(...)`;
- create no durable Restore operation;
- enter none of twelve durable Restore phases;
- create no `before_restore` safety copy;
- replace/migrate no working database;
- perform no rollback/startup-recovery mutation;
- write no Restore AuditLog event;
- leave original selected source byte-identical;
- use isolated temporary validation staging outside durable Restore operation workspaces;
- reuse C4-I `open_selected_source(...)`, `HeldSource` identity/revalidation/digest, stable two-pass staging and `validate_staged_candidate(...)` through shared collaborators;
- return typed presentation-safe results only;
- keep raw SQLite errors, stack traces, migration IDs/internal paths in local technical logs only;
- expose only opaque run/session/generation identifiers;
- never claim Restore completed.

If `stage_source(...)` is too coupled to `RestoreWorkspace`, C4-II-A may extract one shared lower-level staging primitive while preserving all existing C4-I behavior/tests. A second weaker staging algorithm is forbidden.

## Validation scratch

Canonical launcher-owned root under current user's system temp area, conceptually:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

Rules:

- root resolved by launcher only;
- root/session directories created/used with user-only permissions (`0700` or platform-equivalent restrictive permissions);
- opaque random run/session path components;
- no user-provided path component;
- no symlink traversal;
- ownership/version marker sufficient to prove cleanup;
- cleanup refuses paths outside canonical root;
- scratch is never a durable Restore operation;
- next-run cleanup removes only recognized/proved owned session directories.

## Typed browser-visible result

Allowed:

- opaque run/session identity;
- selection generation;
- safe display filename/label;
- state: idle/selecting/validating/accepted/rejected/cancelled/technical_failure;
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

## Retained launcher-private proof

After successful validation, delete temporary staged candidate.

For current authenticated control session only, launcher may retain:

- canonical absolute source path, launcher-private;
- C4-I `SourceIdentity`;
- full SHA-256 from held descriptor;
- successful selection generation;
- typed compatibility result.

Browser token references this state but is not authority.

Retained proof/path is cleared on:

- cancel;
- reselection before next generation becomes authoritative;
- validation rejection/technical failure;
- browser control-session expiry;
- launcher normal exit;
- any transition invalidating successful generation.

No token/proof survives launcher crash.

## Future C4-II-B re-proof

Before destructive execution future C4-II-B must:

```text
reopen launcher-private original path through C4-I intake
→ compare descriptor/path SourceIdentity
→ recompute and compare full SHA-256
→ re-check sidecars/self-containment
→ stage again through C4-I semantics
→ validate again
→ only then enter existing C4-I destructive execution
```

Any mismatch invalidates prior validation and returns to source selection. Browser state, filename, extension or token possession cannot bypass re-proof.

## Backend lifecycle

The **ordinary backend remains running** during file selection, source intake, temporary staging, candidate validation and result presentation.

C4-II-A is non-destructive and operates on selected source + isolated staged copy. Existing C4-I backend stop/exclusion proof remains the future C4-II-B destructive boundary.

## Cleanup matrix

| Event | Required behavior |
|---|---|
| Picker cancel | invalidate generation, clear proof, no durable operation/safety copy, clean owned scratch |
| Reselect | invalidate generation and clear proof first, end old ownership, clean scratch, then next generation |
| Rejection/technical failure | safe browser category, technical detail local, clear proof, clean scratch |
| Browser reload | recover typed state through current run-scoped session |
| Browser/tab close | heartbeat expiry invalidates control authority, clears proof, cancels active picker/validation, cleans scratch |
| Launcher normal exit | invalidate tokens/generation, clear proof, terminate picker, clean scratch, stop control plane |
| Launcher crash/interruption | no token/proof survives; next run cleans only recognized owned scratch |

Validation scratch never triggers a Restore phase, startup recovery or working-database mutation.

## Future C4-II-A minimum tests

At minimum prove:

1. loopback-only ephemeral bind;
2. wrong/missing Host or Origin rejected;
3. no wildcard CORS;
4. atomic bootstrap one-use under concurrent attempts;
5. old-run/wrong session token rejected;
6. state/session responses use `Cache-Control: no-store`;
7. heartbeat/state/cancel remain serviceable while picker/validation is in flight;
8. `command_seq` prevents replay/out-of-order re-execution after old result detail is discarded;
9. same current sequence + same request ID is idempotent;
10. same sequence + different request ID rejected;
11. duplicate concurrent select rejected;
12. stale generation cannot publish;
13. cancel/reselect/session-expiry clears retained proof;
14. browser payload contains no absolute path;
15. picker cancellation typed/non-destructive;
16. valid current/supported older backup accepted;
17. newer/foreign/empty/corrupt/directory/symlink/path-escape rejected;
18. source remains byte-identical;
19. no durable Restore operation/phase/safety copy/AuditLog event;
20. no working DB replacement/migration;
21. backend usable during validation;
22. scratch uses restrictive user-only permissions;
23. cleanup removes only proved owned scratch;
24. next-run cleanup ignores foreign/unproved paths;
25. browser reload recovers safe state;
26. heartbeat expiry invalidates stale authority.

## Future exact-head macOS smoke

```text
real launcher run
→ real browser Restore screen
→ real authenticated launcher-control request
→ real /usr/bin/osascript picker
→ select prepared temporary workshop backup
→ real candidate preparation/validation
→ typed browser result
→ prove heartbeat/state/cancel responsiveness while picker/validation is in flight
→ cancel/reselect exercise
→ prove source bytes unchanged
→ prove no durable Restore operation/safety copy/working-DB change
→ prove retained proof cleared after cancel/session expiry
→ prove owned processes/control plane/scratch cleaned
```

Injecting the final result or bypassing picker/control/session boundary is insufficient.

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