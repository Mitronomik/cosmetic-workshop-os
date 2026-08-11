# Restore interaction and validation-session profile

Status: **CURRENT — NORMATIVE INTERACTION PROFILE**
Updated: `2026-08-11`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control, native picker and exact-run browser session.

## Current lifecycle

```text
PR #187 — MERGED — C4-II-C AUTHORIZATION BASELINE
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
C4-II-C — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed authority chain through B3

```text
A3/A1 picker + validation
→ B1 source-proof binding
→ B2 authenticated one-shot /v1/restore/execute
→ C4-I sole destructive engine
→ B3 explicit confirmation + exact replay
→ pathless restoring/final state
```

PR #187 merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7` and authorized C4-II-C only.

## C4-II-C implementation changeset

Status: **IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED**.

C4-II-C consumes only existing safe browser-visible launcher state/message and changes presentation only.

### `restore_completed`

Shows successful completion, ordinary work availability and safe back navigation. This is allowed only because merged B2 publishes `restore_completed` after successful Restore truth and proved ordinary-backend readiness.

### `restore_failed`

Shows that the attempt did not complete successfully and that ordinary work is available. It explicitly avoids claiming rollback, unchanged data, restored old data or absence of mutation. It warns against blind new Restore.

### `restore_blocked`

Says ordinary work in the current run is not confirmed safe, suppresses normal-work navigation, and tells the user to restart the app. If the blocked condition repeats after restart, the user is directed to the normal Help area rather than a technical console or destructive retry.

### session/network uncertainty after destructive execute

If execute is pending/ambiguous or the browser loses control-session safety while `restoring`, the result is labelled **unknown**.

The page does not infer success, failure, rollback or unchanged data. It suppresses normal-work navigation. When the exact pending execute still exists and the live session permits it, the existing B3 exact replay is labelled as **repeat only the previous command**, not a new Restore. Otherwise the user is directed to restart normally.

An authenticated final B2 snapshot (`restore_completed`, `restore_failed`, or `restore_blocked`) remains authoritative even if same-tab replay metadata is missing. Missing replay metadata disables further Restore commands; it does not turn an already authenticated final result into unknown state.

### Closed architecture

No new launcher state, endpoint, DTO field, browser filesystem authority, destructive cancel, new destructive sequence, operation ID, durable phase, SQL or traceback. Contract/runtime/entry, launcher/backend, main/navigation and ADRs remain closed.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
