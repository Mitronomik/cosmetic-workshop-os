# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-08`

Normative sources:

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — selected interaction/control/picker/validation architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation plan;
- `docs/current-lifecycle.md` — current lifecycle authorization.

ADR 0018 architecture is unchanged by A1 closure or A2 authorization.

## Current lifecycle

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

A2 implementation begins only after this post-A1 lifecycle closure is merged to
`main`.

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

## A1 merged validation boundary

PR #174 merged exact-head verified A1 at
`e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5` as
`504e776508c940554b3ee8659a201af21db8303c`.

A1 implements only:

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

Validation scratch remains:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

Default scratch ancestry is canonicalized from system temp and app-owned path
components refuse symlink traversal. Run/session names are UUID4, directories are
user-only, and cleanup requires ownership/version proof.

A1 creates no durable Restore operation/phase, no `before_restore` safety copy,
no working-DB mutation/migration, no rollback/recovery mutation and no Restore
AuditLog. It does not call `execute_restore(...)` and does not stop the ordinary
backend merely to validate an isolated copy.

## A2 exact-run control plane — authorized next

A2 owns the local control/session protocol only.

### Bind and request authority

- exact `127.0.0.1` bind;
- OS-assigned ephemeral port;
- exact Host validation;
- exact configured local frontend Origin where required;
- no wildcard CORS;
- no credentialed cookie authority;
- only bounded control methods/headers;
- `Cache-Control: no-store` for control/session state.

### Bootstrap and session

- one-use bootstrap capability with >=256 bits entropy;
- atomic compare-and-consume under concurrent attempts;
- separate >=256-bit run-scoped session token;
- no durable/reusable token;
- 15-second heartbeat;
- control-session expiry after 60 seconds without authenticated activity.

Expiry invalidates session authority, A1 generation and retained proof. Scratch
cleanup waits for the owning worker to quiesce.

### Concurrency

The HTTP servicing loop must remain responsive while long selection/validation
work is in flight. Heartbeat/state/cancel cannot wait for the long worker to
finish.

### Request ordering

Every mutating command carries a request ID with >=128 bits entropy and strict
monotonic `command_seq`.

Auth/Host/Origin/syntax-invalid requests do not consume sequence. Once an
authenticated syntactically valid expected-next command is accepted, its sequence
is atomically consumed **before business precondition evaluation**. A typed
business rejection therefore cannot become success on later replay.

Same current sequence + same request ID may return cached idempotent result. Same
sequence + different request ID, stale sequence or future sequence fails closed.

## A2→A3 source-selection seam

A2 has no real picker. Production A2 uses a launcher-owned source-selection
adapter returning typed `picker_unavailable` and obtains **no source path**.

Tests may inject a launcher-owned fake adapter directly. Browser/control request
must never contain `path`, `source_path`, upload/blob/file bytes, bookmark/handle
or equivalent filesystem authority. No test-only HTTP bypass and no generic
filesystem/shell/SQL route.

A3 later replaces `picker_unavailable` with launcher-owned:

```text
/usr/bin/osascript
→ macOS Standard Additions `choose file`
→ absolute POSIX path returned only to launcher memory
```

No `shell=True`, no `System Events`, no user text interpolated into executable
AppleScript and no hidden PyObjC/Electron/Tauri/pywebview/tkinter dependency.

## A2→A4 browser seam

The production product-browser launch URL remains unchanged during A2 and A3.
A2 does not append the bootstrap fragment to actual browser navigation.

A4 owns exact `/backups/restore`, entry from `/backups`, first production browser
bootstrap-fragment handoff, immediate fragment removal, `sessionStorage` token,
non-secret `control_origin`, typed UX and real non-destructive E2E macOS smoke.

A2 exact-head smoke uses a direct authenticated local HTTP harness instead.

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

The ordinary backend remains running during non-destructive A1 validation and A2
control/session work. Backend exclusion/stop remains a future destructive
C4-II-B/C4-I boundary.

## Successor gates

A3 remains blocked until A2 is exact-head verified, merged and lifecycle-closed.
A4 remains blocked by A3. C4-II-B remains separately not authorized.
