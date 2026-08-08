# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

Local-first working system for a cosmetic workshop. The product must remain usable by a non-technical user without GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #178 reviewed head `b0de148032d9b3d2f9912298897f8649c9b1692b` merged as `9d95b0c39c4abd05d5a574c6cd8574b8e457f36b` after A3 14, A2 28, A1 17, C4-I 514, full 2457, native-picker smoke PASS, lifecycle PASS and independent P0=0 / P1=0 / P2=0 audit.

## Closed Restore interaction foundation

A1: launcher-owned non-destructive candidate preparation and C4-I validation reuse.

A2: exact-run authenticated loopback control/session boundary on `127.0.0.1:<ephemeral>` with exact Host/Origin, one-use bootstrap, run token, heartbeat/expiry and replay-safe commands.

A3: launcher-owned native macOS picker:

```text
/usr/bin/osascript
→ fixed Standard Additions choose file
→ typed cancel / owned child quiescence
→ launcher-private absolute POSIX path
→ A2 coordinator
→ A1/C4-I validation
```

Browser/control state remains pathless and no destructive Restore authority exists in A1–A3.

## Authorized A4 boundary

A4 is the only authorized next runtime slice:

```text
launcher bootstrap fragment
→ SPA consumes + removes fragment
→ run-scoped sessionStorage descriptors
→ /backups/restore presentation
→ A2 control
→ A3 picker
→ A1/C4-I non-destructive validation
```

A4 may add `/backups/restore`, the entry from `/backups`, production `#cw-control=<port>:<bootstrap>` fragment handoff, `POST /v1/bootstrap`, `history.replaceState(...)`, run-scoped `sessionStorage`, reload/state/heartbeat/select/cancel/reselect UX.

A4 may **not** add browser path/file authority, query-token transport, localStorage token persistence, FastAPI Restore mutation, destructive confirmation/execute, safety copy, DB replacement/migration, rollback/recovery mutation or Restore AuditLog.

C4-II-B destructive Restore remains **NOT AUTHORIZED**.

## Authority map

1. `docs/current-lifecycle.md`
2. accepted ADR for the exact topic
3. `docs/c4-ii-a-implementation-slices.md`
4. `docs/restore-interaction-and-validation-session.md`
5. `docs/implementation-plan.md`
6. active `state/`

Protected history under `docs/history/` remains byte-identical.