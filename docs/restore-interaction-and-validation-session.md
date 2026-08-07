# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-07`

Normative sources:

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — selected interaction/control/picker/validation architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation plan;
- `docs/current-lifecycle.md` — current lifecycle authorization.

ADR 0018 architecture is unchanged by A1.

## Current lifecycle

```text
PR #173 — MERGED — C4-II-A SLICED AUTHORIZATION
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Selected architecture

```text
browser SPA /backups/restore
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → action/session coordinator
                           ├── /usr/bin/osascript picker worker
                           └── validation worker
                         → C4-I intake/staging/validation
```

Browser owns presentation only. Launcher owns control, picker, absolute selected
source path, validation-session authority and all future destructive authority.
No WebSocket, generic localhost command server, browser filesystem authority or
ordinary FastAPI Restore mutation is selected.

## A1 implemented boundary

The current A1 changeset implements the launcher-owned **non-destructive
validation core only**:

```text
new selection generation
→ private system-temp scratch session
→ C4-I open_selected_source / HeldSource
→ C4-I stable stage_source
→ source digest + identity + sidecar re-proof
→ C4-I validate_staged_candidate read-only
→ source digest + identity + sidecar re-proof again
→ delete staged validation candidate/session scratch
→ if generation remains current, retain launcher-private SourceIdentity + SHA-256
→ return typed presentation-safe result
```

A1 creates no durable Restore operation/phase, no `before_restore` safety copy,
no working-DB mutation/migration, no rollback/recovery mutation and no Restore
AuditLog. It does not call `execute_restore(...)` and does not stop the ordinary
backend merely to validate an isolated copy.

Validation scratch:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

Run/session names are launcher-generated UUID4 values. Directories use `0700` or
platform-equivalent restrictive permissions; ownership/version markers are
required for cleanup. User path components are never used in scratch names.
Unknown directories/files and symlinks are not recursively deleted.

A1 typed result may contain only opaque run/session identity, generation, safe
display filename, state, current/older-supported compatibility and fixed safe
guidance. Absolute source/staged paths, raw SQL/SQLite, migration IDs, stack
traces and database contents are forbidden from presentation state.

Launcher-private retained proof contains source path, C4-I `SourceIdentity`, full
SHA-256, successful generation and compatibility only. It clears on cancel,
reselection, rejection/failure, invalidation or service close.

## Future startup order — A2/A4

ADR 0018 future production order remains:

```text
launcher lifecycle / instance authority
→ interrupted C4-I recovery gate
→ ordinary startup / migrations / backup-before-migration
→ ordinary backend ready
→ control plane bind on 127.0.0.1:<ephemeral>
→ exact-run bootstrap capability
→ browser handoff only once A4 consumer/removal exists
```

A1 does not implement or modify this startup path.

## Future bind / Origin / bootstrap — A2

A2 must enforce exact `127.0.0.1` bind, OS-assigned ephemeral port, exact Host,
exact configured local frontend Origin, no wildcard origin, no credentialed cookie
authority and only required methods/headers.

Bootstrap remains one-use >=256-bit capability transported only in URL fragment,
with atomic compare-and-consume and `Cache-Control: no-store`. Successful
bootstrap returns a second >=256-bit run-scoped token. Browser reload metadata is
`sessionStorage` only and includes non-secret
`control_origin = http://127.0.0.1:<ephemeral-port>` plus run/session identity.

A2 production still has no browser fragment handoff: production browser URL stays
unchanged until A4 supplies the consumer/removal logic.

## Future concurrency / liveness — A2

Mandatory control-plane concurrency remains: picker/validation must never block
the only heartbeat/state/cancel request loop. Worker publication is generation
gated and cleanup waits for **worker quiescence**.

- heartbeat interval: 15 seconds;
- control-session expiry: 60 seconds without authenticated activity.

Expiry invalidates token/generation/proof, prevents stale publication and cleans
owned scratch only after worker quiescence.

Every mutating control command carries request ID with at least 128 bits entropy
and strict monotonic `command_seq`. An authenticated syntactically valid expected
next command consumes its command sequence **before business precondition
evaluation**, so a typed business rejection also consumes the sequence and cannot
become success on delayed replay.

## Future A2→A3 picker seam

A2 has no real picker. Production A2 uses launcher-owned typed
`picker_unavailable` and obtains no source path. Tests may inject a launcher-owned
fake adapter. Browser `path`, `source_path`, upload/blob/file payload or generic
filesystem route is forbidden.

A3 replaces that adapter with launcher-owned:

```text
/usr/bin/osascript
→ macOS Standard Additions `choose file`
→ absolute POSIX path returned only to launcher
```

No `shell=True`, no `System Events`, no user text interpolated into executable
AppleScript and no hidden PyObjC/Electron/Tauri/pywebview/tkinter dependency.

## Future A4 browser screen

A4 owns exact `/backups/restore`, entry from `/backups`, first production browser
bootstrap-fragment handoff, immediate fragment removal, `sessionStorage`, typed
select/cancel/reselect/reload UX and real non-destructive E2E macOS smoke.

A4 still has no destructive execute/confirm command.

## Future C4-II-B re-proof

Before any destructive Restore, separately authorized C4-II-B must:

```text
reopen launcher-private original path through C4-I intake
→ compare SourceIdentity
→ recompute/compare full SHA-256
→ re-check sidecars/self-containment
→ stage again
→ validate again
→ prove backend exclusion
→ create mandatory before_restore safety copy
→ only then enter existing C4-I destructive execution
```

Any mismatch returns to source selection. Browser state/token/filename is never
destructive authority.

## Backend lifecycle

The **ordinary backend remains running** during A1 non-destructive source intake,
staging and validation. Backend exclusion/stop remains a future destructive
C4-II-B/C4-I boundary.

## A1 verification

A1 must prove current/older acceptance, invalid/newer rejection, source and
working-DB safety, no durable Restore/safety-copy/AuditLog mutation, generation
invalidation, owned-only scratch cleanup, existing C4-I regression safety and
exact-head real-service smoke before A1 can be closed.

A2/A3/A4 and C4-II-B remain blocked exactly as recorded in
`docs/current-lifecycle.md`.
