# Restore interaction and validation-session profile

Status: **CURRENT — NORMATIVE INTERACTION PROFILE**
Updated: `2026-08-11`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control, native picker and exact-run browser session.

## Current lifecycle

```text
PR #186 — MERGED — C4-II-B3 EXACT-HEAD VERIFIED
PR #185 — MERGED — B3 AUTHORIZATION BASELINE
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-C — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed authority chain through B3

```text
A3 native picker / A1 validation
→ launcher-private retained source proof
→ B1 exact source-proof binding into C4-I
→ B2 authenticated one-shot /v1/restore/execute
→ C4-I destructive engine on launcher main runtime
→ B3 explicit browser confirmation + exact replay
→ pathless restoring/final launcher states
```

B3 final reviewed head `316358c65a851b46090121c7a6bc877b980176ba`, merged as `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`.

B3 preserves exact `request_id + command_seq + generation`; pending execute persists before HTTP; ambiguous retry reuses the same values; double submit emits at most one execute; dismiss/Escape are local; no browser path/proof/digest authority exists; no `/v1/restore/confirm` exists.

The final B3 browser states are:

```text
restoring
restore_completed
restore_failed
restore_blocked
```

## C4-II-C — Truthful Restore completion/recovery/restart/support UX

Status: **AUTHORIZED NEXT — NOT IMPLEMENTED**.

C4-II-C is **frontend-only** and consumes only the existing safe launcher state/message contract.

### `restore_completed`

May show clear successful completion and safe ordinary navigation only because merged B2 defines this state after successful Restore truth plus proved ordinary-backend readiness. No technical paths/phases.

### `restore_failed`

Must show only safe launcher-provided truth. It must not infer rollback, unchanged data, restored old data or absence of mutation. No blind **destructive retry**.

### `restore_blocked`

Must clearly state that ordinary work cannot safely continue in the current run. Provide restart/recovery/support guidance. Do not offer normal app navigation as known-safe and do not offer destructive retry.

### session/network uncertainty

If browser connectivity or authentication is lost after destructive execute may have started, preserve **session/network uncertainty**. Do not infer success, failure, unchanged data or rollback completion. Provide safe reconnect/restart guidance instead.

### Closed architecture

No new launcher state. No new control endpoint. No browser filesystem authority. No destructive cancel. No destructive retry. No operation ID/durable phase/SQL/traceback in browser. `launcher/**`, `backend/**`, `frontend/src/restore-control-contract.ts`, `frontend/src/restore-control-runtime.ts`, `frontend/src/main.ts` and app navigation remain closed.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
