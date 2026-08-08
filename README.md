# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The product goal is a
packaged application a non-technical user can run without GitHub, Git, Python,
Node.js, Docker or a terminal.

## Current product status

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

PR #176 reviewed A2 head `681cb4050bec082db6b637285590e232880af739`
merged as `90a14dd9a11b83bc31a40e1d3fb9523f41772b88` after 2 race,
28 A2, 17 A1, 514 C4-I, 2443 full tests, smoke and audit 0/0/0.

PR #177 reviewed closure head `d767b957cb3debae584709f2bbadafebd8dd6a9e`
merged as `e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263`, closing A2 and
authorizing only A3.

## Closed A1/A2 boundary

A1 remains the single non-destructive candidate-preparation authority. A2 remains
the exact-run launcher control/session authority with exact loopback/Host/Origin,
atomic bootstrap, run token, no-store/narrow CORS, 15s/60s liveness, strict
`command_seq`, one worker, responsive heartbeat/state/cancel and stale-proof
hardening.

## Current A3 implementation boundary

The current changeset implements only the launcher-owned native macOS picker:

```text
/usr/bin/osascript
→ fixed Standard Additions choose file
→ typed user cancel / owned child terminate+reap
→ absolute POSIX path only in launcher memory
→ existing A2 SourceSelectionAdapter seam
→ existing A1 candidate preparation
```

`launcher/restore/macos_picker.py` uses exact `/usr/bin/osascript`,
`use scripting additions`, `choose file`, `shell=False`, no `System Events`, no
user-controlled AppleScript interpolation, and an error `-128` sentinel for typed
Cancel. Cancel/expiry terminates the owned child with kill fallback and waits for
reaping. Production runtime injects this adapter; the closed A2 unavailable
default remains for direct/test construction.

A3 does not decide whether the selected file is valid. A1/C4-I remains acceptance
authority. Browser/control state remains pathless.

A3 **does not** authorize `/backups/restore`, production `#cw-control` handoff or
any destructive Restore behavior. A4 and C4-II-B remain closed.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — launcher control/picker/session architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 plan;
- `docs/current-lifecycle.md` — current implementation authorization/status.

C4-II-B destructive confirmation/execution remains **NOT AUTHORIZED**.

## C4-II-A sequence

```text
A1 — validation-session core                     ← DONE / merged
→ A2 — exact-run launcher control plane          ← DONE / merged
→ A3 — native macOS picker integration           ← current changeset / not closed
→ A4 — browser /backups/restore + E2E UX         ← blocked
```

## Current authority map

1. [`docs/current-lifecycle.md`](docs/current-lifecycle.md)
2. applicable accepted ADR
3. [`docs/c4-ii-a-implementation-slices.md`](docs/c4-ii-a-implementation-slices.md)
4. [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)
5. [`docs/implementation-plan.md`](docs/implementation-plan.md)
6. active [`state/`](state/) files

Searchable history remains under [`docs/history/`](docs/history/README.md). The
five protected pre-compaction snapshots must remain byte-identical.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package,
API-first business architecture, safe historical data, recipe versions,
first-class client recipes, lot/movement inventory, transactional production,
safe import preview/confirmation, backup-before-migration and a human-readable
non-technical UI.

Restore additionally preserves launcher ownership of filesystem/destructive
authority, immutable selected source, no browser absolute-path authority and no
destructive action before separately authorized C4-II-B.
