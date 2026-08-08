# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-08`

Historical pre-compaction plan remains byte-identical under `docs/history/`.

## Merged baseline

```text
PR #176 / A2 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
PR #177 / A3 authorization merge — e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263
PR #178 reviewed A3 head — b0de148032d9b3d2f9912298897f8649c9b1692b
PR #178 / A3 merge — 9d95b0c39c4abd05d5a574c6cd8574b8e457f36b
```

## Current lifecycle

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

## A3 closure

A3 final evidence is accepted: targeted A3 14, A2 28, A1 17, C4-I 514, full backend+launcher 2457, exact-head native-picker smoke PASS, lifecycle PASS, clean exact head and independent P0=0 / P1=0 / P2=0.

Closed A3 production contract remains exact `/usr/bin/osascript`, fixed Standard Additions `choose file`, `shell=False`, no `System Events`, typed error `-128` cancel, launcher-private absolute POSIX path and owned terminate/reap + kill/reap fallback.

## Current implementation window — C4-II-A4

Goal: complete only the browser presentation and exact-run bootstrap/session UX for the already-merged A1/A2/A3 non-destructive chain.

### Authorized implementation scope

- canonical nested route `/backups/restore`;
- human-readable entry from `/backups`;
- first production launcher browser handoff via URL fragment only: `#cw-control=<ephemeral-port>:<bootstrap-token>`;
- bootstrap fragment consumed at SPA startup and exchanged once through existing `POST /v1/bootstrap`;
- immediate `history.replaceState(...)` removal of bootstrap material;
- `sessionStorage` only for `control_origin`, optional opaque `run_id`, and run-scoped session token;
- never persist session token to `localStorage`;
- exact launcher control origin + explicit authorization header;
- reload recovery through `GET /v1/state`;
- invalid-token/run-mismatch clears stale descriptors;
- heartbeat at 15 seconds while run-scoped session is active;
- existing A2 select/cancel/reselect with random request IDs and strict monotonic `command_seq`;
- presentation-safe states for selecting, validating, accepted, rejected, cancelled, expired and technical-unavailable cases;
- nontechnical open/restart guidance when no valid launcher session exists;
- non-destructive E2E through A2 → A3 → A1/C4-I.

### Mandatory seams

Browser never owns filesystem authority: no `path`, `source_path`, file bytes, upload/blob, bookmark/handle or `<input type="file">` fallback.

Bootstrap/session capability never goes in query params, backend API payloads, logs or persistent storage.

Ordinary FastAPI remains business API only. Launcher control plane remains the Restore interaction authority.

A4 remains non-destructive: no execute/confirm command, no `execute_restore(...)`, no durable Restore phase, no `before_restore`, no DB replacement/migration, no rollback/recovery mutation and no Restore AuditLog.

## Required A4 tests

1. nested route resolution for `/backups/restore` and entry from `/backups`;
2. exact fragment grammar and rejection of malformed bootstrap descriptors;
3. fragment removal immediately after bootstrap attempt;
4. no query transport and no bootstrap persistence;
5. sessionStorage contract and no localStorage token;
6. authenticated control client uses exact `control_origin` and Authorization header;
7. reload state recovery and invalid-token/run-mismatch cleanup;
8. heartbeat startup/cleanup around active launcher session;
9. monotonic `command_seq` and >=128-bit request IDs at frontend client seam;
10. select/cancel/reselect typed UI;
11. pathless DTO/presentation under internal path/stderr failures;
12. missing session fail-closed guidance with no browser file fallback;
13. production launcher URL uses fragment only;
14. A3/A2/A1/C4-I regressions remain green;
15. exact-head real non-destructive browser smoke.

## Exact-head gate

Final A4 head must pass diff/lifecycle checks, targeted frontend/session tests, relevant launcher regressions, full backend+launcher/frontend baseline as applicable, exact-head browser smoke, clean status/head and independent P0=0 / P1=0 / P2=0 audit.

## Forbidden scope

Do not add C4-II-B destructive execution, backend Restore mutation endpoint, WebSocket/generic launcher command server, browser filesystem fallback, new unrelated dependency, packaging implementation, cloud sync, OCR, roles/multiuser or advanced analytics.

## Current next action

```text
merge A3 closure / A4 authorization
→ start A4 from updated main
→ implement only browser bootstrap/session/route UX
→ exact-head tests + real non-destructive E2E smoke
→ independent audit
→ merge only at P0=0 / P1=0 / P2=0
```