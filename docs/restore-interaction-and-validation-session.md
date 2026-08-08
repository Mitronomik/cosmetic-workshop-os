# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-08`

Normative sources:

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — selected interaction/control/picker/validation architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation plan;
- `docs/current-lifecycle.md` — current lifecycle authorization.

ADR 0018 is unchanged by A3 implementation.

## Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
PR #177 — MERGED — A2 CLOSED / A3 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
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
                         → A2 action/session coordinator
                           ├── A3 launcher-owned native picker
                           └── A1 validation worker
                         → C4-I intake/staging/validation
```

Browser owns presentation only. Launcher owns control, picker, absolute selected
source path, validation-session authority and all future destructive authority.

## A1 validation boundary — CLOSED

A1 remains the only candidate-preparation service. It creates no durable Restore
phase, no `before_restore` safety copy, no working-DB mutation and no Restore
AuditLog. It directly reuses C4-I source intake/staging/validation and retains only
launcher-private source proof.

## A2 exact-run control plane — CLOSED

PR #176 reviewed head `681cb4050bec082db6b637285590e232880af739`
merged as `90a14dd9a11b83bc31a40e1d3fb9523f41772b88`.

A2 remains exact loopback/Host/Origin, atomic one-use bootstrap, run token,
no-store/narrow CORS, 15s heartbeat / 60s expiry, strict command ordering, one
selection/validation worker and generation-gated publication. Cancel/expiry keeps
A1 authority invalid and the stale A2→A1 begin race remains hardened.

## A3 native picker — CURRENT IMPLEMENTATION

PR #177 reviewed head `d767b957cb3debae584709f2bbadafebd8dd6a9e`
merged as `e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263`, authorizing only A3.

### Native picker ownership

`launcher/restore/macos_picker.py` implements the launcher-owned adapter:

- `OSASCRIPT_PATH = Path("/usr/bin/osascript")`;
- fixed `use scripting additions` / `choose file` AppleScript;
- selected `POSIX path` returned only to launcher memory;
- no user-controlled script interpolation;
- `shell=False` and no `System Events`;
- AppleScript error `-128` returns an internal cancellation sentinel and becomes a
  typed ordinary cancel result;
- non-macOS/missing exact helper returns typed unavailable;
- empty/nonzero/non-absolute results become launcher-internal technical failure;
- C4-I/A1 remains file-acceptance authority.

### Picker process lifecycle

The existing A2 selection worker remains the sole long-work owner. The A3 adapter
owns at most one child for that worker and polls the A2 `cancel_event` while the
child is active.

On cancel/expiry/close:

```text
A2 invalidates control/A1 authority immediately
→ cancel_event becomes set
→ A3 terminates owned osascript child
→ waits/reaps
→ kill + reap only if terminate does not quiesce
→ selection worker exits without stale publication
```

No detached or unaccounted picker child is allowed.

### Path privacy

The selected absolute POSIX path is launcher-private. It flows only through the
internal `SourceSelectionResult` into merged A1 candidate preparation and later
launcher-private retained proof. Browser/control request/state, URLs and safe
user-visible failures remain pathless.

### Technical failure boundary

Raw osascript stderr and absolute paths are not serialized. The closed A2 worker
maps adapter exceptions to its fixed safe `selection_failed` presentation.

## A3→A4 browser seam

Production product-browser launch URL remains unchanged through A3.
`open_runtime_browser(...)` does not append `#cw-control`, control port, bootstrap
capability or session token.

A4 remains blocked and owns `/backups/restore`, first production fragment handoff,
immediate fragment removal, `sessionStorage` and real browser E2E UX.

## Launcher runtime ownership

```text
launcher lifecycle / recovery / startup
→ proved ordinary backend
→ A2 exact-run control plane with production A3 adapter injected
→ ordinary product browser URL unchanged
→ select: A2 worker owns A3 picker child
→ launcher-private path enters A1 validation
→ close/quiesce picker/control/A1
→ stop owned backend
→ release launcher lifecycle
```

If picker selection cannot run safely, no browser file input or alternate Restore
transport is invented.

## A3 verification

Current verification assets:

- native picker unit/process tests;
- A2 session cancel/expiry → picker terminate/reap integration tests;
- production runtime adapter-injection test;
- exact-head `scripts/smoke_restore_native_picker.py`.

A3 is not closed until those tests, A2/A1/C4-I/full regressions, exact-head smoke
and independent audit pass on the final published head.

## Future C4-II-B re-proof

Before destructive Restore, separately authorized C4-II-B must reopen/re-prove the
launcher-private original path, compare `SourceIdentity`, recompute SHA-256,
re-check sidecars, re-stage/revalidate, prove backend exclusion, create mandatory
`before_restore` safety copy and only then enter C4-I destructive execution.
Browser state/token/filename is never destructive authority.

## Successor gates

A4 remains blocked until A3 is exact-head verified, merged and lifecycle-closed.
C4-II-B remains separately not authorized.
