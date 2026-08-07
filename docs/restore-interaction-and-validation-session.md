# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-07`

Normative sources:

- `docs/decisions/0016-launcher-assisted-restore.md` — durable Restore safety/state machine;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — C4-I lifecycle closure and decision-only CR-011 gate;
- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md` — selected interaction architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation authorization;
- `docs/current-lifecycle.md` — current implementation authorization.

ADR 0018 does not amend ADR 0016. The C4-II-A slice plan does not change ADR
0018 architecture; it only authorizes implementation in bounded sequence.

## Current lifecycle

```text
PR #172 — MERGED — CR-011 ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED
C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

Only A1 is the immediate successor after the PR #173 authorization changeset is
merged to `main`. A2–A4 require their predecessor to merge and pass exact-head
verification first.

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

The browser owns presentation only. Launcher owns control, picker, absolute path,
validation-session authority and all future destructive authority.

No WebSocket, generic localhost command server, browser filesystem authority,
ordinary FastAPI Restore mutation or new application dependency is selected.

## Slice ownership

The accepted architecture is implemented in four separate PRs:

- **A1 — validation-session core**: candidate preparation, C4-I primitive reuse,
  scratch/proof/generation/cancel/cleanup; no HTTP/picker/frontend;
- **A2 — exact-run control plane**: loopback bootstrap/session/security/concurrency/
  replay protocol; no real picker/final UI;
- **A3 — native picker integration**: real `/usr/bin/osascript` picker and
  picker→A1 integration; no final browser workspace;
- **A4 — browser Restore screen**: `/backups/restore`, browser session handling,
  typed UX and real non-destructive end-to-end smoke.

No later slice may start from an unmerged predecessor branch.

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

This full topology belongs to A2–A4. A1 does not alter launcher browser/control
startup.

If the later control plane cannot start safely, normal product use may continue
when otherwise safe, but Restore fails closed and no fallback transport is
allowed.

## Bind, Host, Origin and CORS

A2 must enforce exact `127.0.0.1` bind, ephemeral port, exact `Host`, exact local
frontend Origin, no wildcard CORS, no credentialed cookie session, no LAN/remote
bind, and only required methods/headers.

A `/backups/restore` page without valid launcher session must show safe restart/
open guidance and never fall back to upload or FastAPI Restore.

## Bootstrap, sessionStorage and reload

A2/A4 implement this accepted contract:

- launcher creates `run_id`, one-use bootstrap token with at least 256 bits entropy
  and an ephemeral control port;
- control metadata enters browser only in URL **fragment**;
- bootstrap is an **atomic compare-and-consume** operation;
- exactly one concurrent exchange succeeds;
- fragment is removed immediately after success;
- successful bootstrap returns a second >=256-bit run-scoped token;
- SPA stores `control_origin`, optional opaque `run_id`, and session token only in
  `sessionStorage`;
- token is sent only in authorization header, never `localStorage`, URL or durable
  application state;
- invalid-token/run-mismatch clears stale sessionStorage metadata;
- bootstrap/control responses carrying session or validation state use
  `Cache-Control: no-store`.

## Mandatory control-plane concurrency

A2 must keep heartbeat, state, cancel and timeout serviceable while picker/
validation work is in flight. Use `ThreadingHTTPServer`-equivalent concurrent
servicing or equivalent launcher-owned worker coordination.

At most one picker/validation owner exists per control session.

Cancellation/session expiry invalidates authority immediately. Late worker output
cannot publish. Scratch deletion that could race with a worker waits for **worker
quiescence** / file release.

## Browser liveness

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without authenticated activity.

Expiry invalidates token/generation, terminates owned picker, prevents stale
publication, **clear launcher-private retained source proof/path**, waits for
quiescence, cleans only owned scratch and leaves workshop data unchanged.

## Control vocabulary

A2/A4 may expose only an equivalent of:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

No execute/confirm/destructive command belongs in C4-II-A.

## Replay, duplicate and command ordering

Each mutating control command carries:

- random request ID with at least 128 bits of entropy;
- strictly monotonic `command_seq` per authenticated control session.

Launcher keeps bounded authority state including `highest_command_seq`, request
ID for that sequence, and safe in-progress/final retry result.

Sequence consumption rules:

- Origin/Host/auth/token/JSON/schema/sequence validation happens before
  consumption;
- invalid auth/Origin/Host/format, stale sequence or skipped/future sequence does
  not consume;
- an authenticated, syntactically valid request carrying exactly the expected
  next `command_seq` atomically consumes that sequence before business precondition
  evaluation;
- a typed business rejection such as `action_in_progress` therefore **consumes its
  command sequence** and records its safe result;
- replay of that rejected command later cannot become successful merely because
  conditions changed;
- current-sequence retry works only with the same request ID and returns the same
  recorded safe result without re-execution;
- accepted select/cancel/reselect advances separate selection generation;
- result publishes only if its captured generation remains current;
- heartbeat does not consume `command_seq`.

## Native macOS picker

A3 implements the launcher-owned adapter:

```text
/usr/bin/osascript
→ macOS Standard Additions `choose file`
→ POSIX selected path returned only to launcher
```

No `shell=True`, no `System Events`, no user data interpolated into executable
AppleScript, typed cancellation, no absolute path to browser/backend.

No PyObjC/Electron/Tauri/pywebview/tkinter dependency is authorized. App Store
sandbox compatibility remains a separate future packaging decision.

## Mandatory non-destructive boundary — A1

A1 implements one launcher-owned application service conceptually equivalent to:

```text
prepare_restore_candidate(...)
```

It must never call `execute_restore(...)`, create a durable Restore operation,
enter any durable phase, create `before_restore` safety copy, replace/migrate
working DB, perform rollback/recovery mutation or write Restore AuditLog.

It must leave source byte-identical and reuse C4-I `open_selected_source(...)`,
`HeldSource` identity/revalidation/digest, stable two-pass staging and
`validate_staged_candidate(...)` through shared collaborators.

If `stage_source(...)` is coupled to `RestoreWorkspace`, A1 may extract one shared
lower-level primitive preserving C4-I behavior/tests. A second weaker algorithm
is forbidden.

## Validation scratch — A1

Conceptual root:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

Root/session dirs use `0700` or platform-equivalent restrictive user-only
permissions. No user path components, no symlink traversal, cleanup only inside
canonical root after ownership proof, and scratch never becomes durable Restore
state.

## Typed result and path privacy

A1 defines typed presentation-safe result data. A4 presents it.

Allowed browser-visible facts: opaque run/session, generation, safe filename
label, typed lifecycle/compatibility and fixed safe guidance.

Forbidden: absolute source/staged path, raw SQL/SQLite, migration IDs, stack
traces, operation record or arbitrary DB contents.

Filename is presentation only.

## Retained launcher-private proof — A1

After successful validation staged candidate is deleted. For the current valid
selection/control context launcher may retain only:

- launcher-private canonical source path;
- C4-I `SourceIdentity`;
- full SHA-256;
- successful generation;
- typed compatibility.

Proof/path clears on cancel, reselection, rejection/failure, session expiry,
launcher exit or any invalidating transition. No proof survives crash. Browser
token is reference only.

## Future C4-II-B re-proof

C4-II-B remains not authorized. When later authorized, it must:

```text
reopen launcher-private path through C4-I intake
→ compare SourceIdentity
→ recompute/compare SHA-256
→ re-check sidecars/self-containment
→ stage again
→ validate again
→ prove backend exclusion
→ create mandatory before_restore safety copy
→ only then enter existing C4-I destructive execution
```

Any mismatch returns to source selection.

## Backend lifecycle

The **ordinary backend remains running** during C4-II-A picker, intake, staging,
candidate validation and result presentation. C4-II-A is non-destructive; C4-I
backend exclusion remains a future C4-II-B destructive authority boundary.

## Cleanup matrix

| Event | Required behavior |
|---|---|
| Picker cancel | invalidate generation/proof immediately; terminate picker; clean scratch after quiescence |
| Reselect | invalidate old generation/proof; quiesce owner; clean scratch; then next generation |
| Rejection/failure | safe browser category; detail local; clear proof; clean scratch |
| Reload | use sessionStorage `control_origin` + token + `GET /v1/state` |
| Tab close | heartbeat expiry invalidates authority/proof, cancels owner, then cleans scratch |
| Launcher exit | invalidate tokens/generation/proof, terminate picker, quiesce workers, clean scratch, stop control plane |
| Crash/interruption | no token/proof survives; next run cleans only recognized owned scratch |

## Slice verification

A1 exact-head smoke must exercise real candidate preparation and C4-I source
intake/staging/validation without browser/picker mocks replacing the core result.

A2 tests must prove control security, concurrency, command ordering and no
destructive command.

A3 exact-head macOS smoke must invoke the real `/usr/bin/osascript` picker and
reach real A1 candidate preparation.

A4 exact-head end-to-end smoke must exercise:

```text
real launcher
→ real browser /backups/restore
→ real authenticated control request
→ real /usr/bin/osascript picker
→ real candidate preparation/validation
→ typed result
→ heartbeat/state/cancel while work is in flight
→ rejected/retried command ordering and cancel/reselect
→ prove source unchanged and no durable/destructive mutation
→ prove proof/workers/control-plane/picker/scratch cleanup
```

Synthetic bypass is insufficient.

## Authorization boundary

C4-II-A runtime is authorized **only** according to
`docs/c4-ii-a-implementation-slices.md`.

A1 is the only immediate runtime successor after PR #173 merges. A2/A3/A4 remain
gated by predecessor merge + exact-head review.

C4-II-B/C4-II-C/C4-III, destructive execution, new dependencies, packaging
implementation and ADR 0016 state-machine changes remain not authorized.
