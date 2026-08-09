# C4-II-A implementation authorization and slice plan

Status: **CLOSED NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-09`

This document records the completed `C4-II-A — Launcher Restore source selection and non-destructive validation presentation` sequence. ADR 0018 remains unchanged.

## Merged sequence

```text
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
```

Final A4 evidence:

```text
PR #180 reviewed head — 79c698ed76d478d608a25f4b95499ff519794228
PR #180 merge/new main — e61d4e233c98d3c53e7749fe96ed0ee630610372
```

A4 closed with lifecycle PASS; A4 launcher 15; A3 14; A2 29; A1 17; C4-I 514; full backend+launcher 2470; frontend A4 16; backup regression 25; audit-log regression 92; exact-head cross-layer smoke PASS; desktop/narrow/keyboard/native-picker UI smoke PASS; independent P0=0/P1=0/P2=0.

## Closed A1→A4 contract

A1 owns non-destructive candidate preparation and retains only launcher-private source proof. A2 owns exact-run loopback session/auth/liveness/replay semantics. A3 owns the native macOS picker, absolute path and picker-child lifecycle. A4 owns fragment-only bootstrap, run-scoped browser session state and the pathless `/backups/restore` presentation.

The completed A flow is:

```text
launcher control plane
→ browser #cw-control fragment
→ immediate fragment removal
→ one-use bootstrap
→ sessionStorage descriptors + same-tab history replay metadata
→ /backups/restore
→ A2 select/cancel
→ A3 /usr/bin/osascript picker
→ A1/C4-I non-destructive validation
```

The browser never owns the source path and no A slice exposes destructive confirmation or execution.

## Closed hard boundaries

The A sequence must remain free of browser filesystem authority, query-token transport, `localStorage` token persistence, ordinary FastAPI Restore mutation, generic launcher commands, `execute_restore(...)` calls from browser/control code, durable Restore phases, `before_restore` safety-copy creation, working-database replacement/migration, rollback/recovery mutation and Restore AuditLog.

`frontend/src/main.ts` remains byte-identical at blob `ea98a76638bddcb5a92b9ba31941508f8a816d42`; future Restore work must not use B as an excuse to move the shell into a larger monolith.

## Successor

C4-II-B is now sliced separately in `docs/c4-ii-b-implementation-slices.md`.

Only B1 is authorized. B2/B3 remain not authorized until predecessor merge/exact-head closure gates are complete.
