# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-07`

Normative sources:

- `docs/decisions/0016-launcher-assisted-restore.md` — durable Restore safety/state machine;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — C4-I lifecycle closure and decision-only CR-011 gate;
- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md` — selected interaction architecture;
- `docs/current-lifecycle.md` — current implementation authorization.

ADR 0018 is newer only for the CR-011 interaction/validation-session topic. It does not amend ADR 0016 and does not authorize C4-II-A runtime work.

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

## Selected architecture and screen

```text
browser SPA /backups/restore
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → action/session coordinator
                           ├── /usr/bin/osascript picker worker
                           └── validation worker
                         → C4-I intake/staging/validation
```

The screen is browser-owned presentation at exact future route `/backups/restore`, entered through a human-readable action from `/backups`.

No WebSocket, generic localhost command server, browser file authority, ordinary FastAPI Restore mutation or new application dependency is selected.

## Startup order

```text
launcher lifecycle/instance authority
→ interrupted C4-I recovery gate
→ ordinary startup/migrations/backup-before-migration
→ ordinary backend ready proof
→ control plane bind on 127.0.0.1:<ephemeral>
→ exact-run bootstrap capability
→ browser open
→ browser + backend + control plane live under launcher lifetime
```

If the control plane is unavailable, normal product use may continue when otherwise safe, but Restore fails closed. No fallback transport is allowed.

## Bind, Host, Origin and CORS

Future C4-II-A requires:

- exact `127.0.0.1` bind;
- OS-assigned ephemeral port;
- exact `Host: 127.0.0.1:<bound-port>`;
- exact allowed local frontend Origin from configured `frontend_url`;
- no wildcard CORS;
- no credentialed cookie session;
- no LAN/remote binding;
- only required methods/headers.

A `/backups/restore` page without valid launcher session shows human-safe restart/open guidance and does not fall back to upload/FastAPI Restore.

## Bootstrap, sessionStorage and reload

Launcher creates `run_id`, one-use bootstrap token with at least 256 bits entropy and ephemeral control port before browser open.

Control metadata enters browser only in URL **fragment**:

```text
#cw-control=<ephemeral-port>:<bootstrap-token>
```

Bootstrap must be an **atomic compare-and-consume**: exactly one concurrent exchange succeeds; all replay/concurrent losers fail. The fragment is removed immediately after success and never persisted/logged.

Successful bootstrap returns a second >=256-bit run-scoped session token.

For reload the SPA stores in `sessionStorage` only:

- `control_origin = http://127.0.0.1:<ephemeral-port>`;
- opaque `run_id` if needed for session matching;
- run-scoped session token.

`control_origin` is non-secret routing metadata, not authority. The token is sent only in an authorization header and is never `localStorage`/URL/durable state.

On invalid-token/run-mismatch response, SPA clears stale `control_origin`, `run_id` and token from `sessionStorage`.

All bootstrap/control responses carrying session or validation state use `Cache-Control: no-store`.

## Mandatory control-plane concurrency

Long-running picker/validation must not block the only control request loop.

Use `ThreadingHTTPServer`-equivalent concurrent request servicing or equivalent launcher dispatcher/worker coordination so heartbeat, state, cancel and timeout remain active while select is in flight.

At most one picker/validation owner exists per control session.

Cancellation/session-expiry invalidates authority immediately. A late worker result cannot publish because publication is generation-gated. Cleanup that could race with a worker waits for worker quiescence/file release. A shared staging refactor may add cooperative cancellation checks at safe chunk boundaries while preserving existing C4-I caller behavior.

## Browser liveness

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without authenticated activity.

Expiry atomically invalidates token/generation, terminates owned picker if active, blocks stale publication, **clear launcher-private retained source proof/path**, coordinates worker quiescence, cleans only owned scratch and leaves workshop data unchanged.

## Control vocabulary

Only an equivalent of:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

No execute/confirm/destructive operation belongs in C4-II-A.

## Replay and command ordering

Each mutating command carries:

- random request ID with at least 128 bits of entropy;
- strictly monotonic `command_seq` per authenticated session.

Launcher keeps bounded state including `highest_command_seq`, request ID for that sequence and safe in-progress/final retry result.

Rules:

- next new mutation must use exact next sequence;
- lower sequence is permanently stale/replay;
- current sequence retries only with same request ID and never re-executes;
- current sequence + different request ID is rejected;
- skipped/future sequence is rejected;
- active select owns the session; second select is `action_in_progress`;
- accepted select/cancel/reselect advances separate selection generation;
- result publishes only if captured generation remains current;
- cancel/reselect clears old proof before new source authority;
- heartbeat does not consume `command_seq`.

## Native macOS picker

Launcher-owned adapter:

```text
/usr/bin/osascript
→ macOS Standard Additions `choose file`
→ selected POSIX path returned only to launcher
```

No `shell=True`, no `System Events`, no user data interpolated into executable AppleScript, typed cancellation, no absolute path to browser/backend.

No PyObjC/Electron/Tauri/pywebview/tkinter dependency is authorized. Mac App Store sandbox compatibility remains a separate future packaging decision.

## Mandatory non-destructive boundary

Future C4-II-A uses one launcher-owned service conceptually:

```text
prepare_restore_candidate(...)
```

It must never call `execute_restore(...)`, create a durable Restore operation, enter any of twelve phases, create `before_restore` safety copy, replace/migrate working DB, perform rollback/recovery mutation or write Restore AuditLog.

It must leave source byte-identical and reuse C4-I `open_selected_source(...)`, `HeldSource` identity/revalidation/digest, stable two-pass staging and `validate_staged_candidate(...)` through shared collaborators.

If `stage_source(...)` is coupled to `RestoreWorkspace`, C4-II-A may extract one shared lower-level primitive while preserving C4-I behavior/tests. A second weaker algorithm is forbidden.

## Validation scratch

Conceptual root:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

Root/session directories use `0700` or platform-equivalent restrictive user-only permissions. No user-provided path components, no symlink traversal, cleanup only within canonical launcher root after ownership proof, and scratch never becomes durable Restore state.

## Typed browser state and path privacy

Allowed: opaque run/session, generation, safe filename label, idle/selecting/validating/accepted/rejected/cancelled/technical_failure, typed compatibility and fixed safe guidance.

Forbidden: absolute source/staged paths, raw SQLite/SQL, migration IDs, stack traces, operation records, arbitrary DB contents.

Filename is presentation only.

## Retained launcher-private proof

After successful validation the staged candidate is deleted. For the current authenticated control session launcher may retain only:

- launcher-private canonical source path;
- C4-I `SourceIdentity`;
- full SHA-256;
- successful generation;
- typed compatibility.

Proof/path clears on cancel, reselection, rejection/failure, session expiry, launcher exit or any invalidating transition. No proof survives launcher crash.

Browser token references this state but is not authority.

## Future C4-II-B re-proof

```text
reopen launcher-private original path through C4-I intake
→ compare SourceIdentity
→ recompute/compare full SHA-256
→ re-check sidecars/self-containment
→ stage again
→ validate again
→ only then enter existing C4-I destructive execution
```

Any mismatch returns to selection.

## Backend lifecycle

The **ordinary backend remains running** during picker, source intake, temporary staging, candidate validation and result presentation. C4-II-A is non-destructive; C4-I backend exclusion remains future C4-II-B destructive authority.

## Cleanup matrix

| Event | Required behavior |
|---|---|
| Picker cancel | invalidate generation/proof immediately; terminate picker; clean scratch after quiescence |
| Reselect | invalidate old generation/proof; quiesce owner; clean scratch; then next generation |
| Rejection/failure | safe browser category; detail local; clear proof; clean scratch |
| Reload | recover through sessionStorage `control_origin` + token + `GET /v1/state` |
| Tab close | heartbeat expiry invalidates authority/proof, cancels owner, then cleans scratch |
| Launcher exit | invalidate tokens/generation/proof, terminate picker, quiesce workers, clean scratch, stop control plane |
| Crash/interruption | no token/proof survives; next run cleans only recognized owned scratch |

## Future C4-II-A tests

Must prove at least: loopback/Host/Origin/CORS, atomic bootstrap, stale-run clearing of sessionStorage metadata, `no-store`, concurrent heartbeat/state/cancel during in-flight picker/validation, worker-quiescence cleanup, `command_seq` replay/order rules, duplicate select, stale generation, retained-proof clearing, no browser absolute path, real picker cancel, accepted/rejected backup classes, source byte identity, no Restore operation/phase/safety copy/AuditLog/working-DB mutation, backend usability, `0700` scratch, owned-only cleanup, next-run cleanup, and `/backups/restore` fail-closed behavior without launcher session.

## Future exact-head macOS smoke

```text
real launcher
→ real browser /backups/restore
→ real authenticated control request
→ real /usr/bin/osascript picker
→ real candidate preparation/validation
→ typed browser result
→ prove heartbeat/state/cancel responsive while work is in flight
→ cancel/reselect
→ prove source unchanged and no durable/destructive mutation
→ prove proof/workers/control-plane/picker/scratch cleanup
```

Synthetic bypass is insufficient.

## Not authorized yet

C4-II-A runtime implementation, C4-II-B/C4-II-C/C4-III, frontend Restore code, launcher control/picker/validation code, destructive execution, new dependencies, packaging implementation and ADR 0016 state-machine changes remain not authorized.

A separate post-CR-011 task must explicitly authorize bounded C4-II-A runtime work.