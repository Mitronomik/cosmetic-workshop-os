# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-11`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

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

macOS packaging, safe packaged update flow, installation verification and full release-candidate smoke remain incomplete.

## Merged baseline through B3 closure

- PR #182 reviewed B1 head `27726058af4f373ab65225ecf4d1a945f1c53067`, merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`.
- PR #183 reviewed B2 authorization head `fa922f56c19a2dd33b6307ae0a197d476f91489b`, merged as `4617b8c436eaa510fd545d863346595e2d808ea7`.
- PR #184 reviewed B2 head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4`, merged as `266c50a77e5f353fa77701cb854629a99460667f`.
- PR #185 reviewed B3 authorization head `f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c`, merged as `f6589bdd7c403b6d400e3f5b7a0daea75b14632a`.
- PR #186 reviewed B3 head `316358c65a851b46090121c7a6bc877b980176ba`, merged as `b9ca2bd77d5f2be0ba406e9669c18f74e1955725` at `2026-08-11T11:14:15Z`.

## Accepted B3 evidence

Final exact-head evidence on `316358c65a851b46090121c7a6bc877b980176ba`:

- `git diff --check` — **PASS**;
- documentation lifecycle checker — **PASS**;
- frontend `npm ci` — **PASS**, 0 vulnerabilities;
- frontend build — **PASS**;
- focused Restore control suite — **30/30 PASS**;
- regression `pending execute presentation never claims Restore has not started` — **PASS**;
- external browser smoke v4 — **PASS**, runner SHA-256 `5103a50f578d624345323731e2eb910cc4e4d756b33bb7b430b03eb4af239b62`;
- browser smoke observed `execute_calls=1`, `cancel_calls=0`, Chrome exit 0;
- final exact-head/worktree no-change gate — **PASS**.

Audit history is preserved truthfully. Earlier head `de827c5789f165949d0dbcd4fbbda4f5d368d71f` had **P0 = 0 / P1 = 1 / P2 = 0 — AUDIT GATE FAIL** because `accepted + pending execute` could falsely claim that working data was unchanged and Restore had not started. That P1 was corrected before merge. The final reviewed head was independently re-audited: **P0 = 0 / P1 = 0 / P2 = 0 — AUDIT GATE PASS**, merge recommendation YES.

## Closed B3 contract

```text
accepted candidate
→ explicit native dialog
→ local dismiss/Escape OR explicit confirm
→ runtime obtains current accepted generation
→ pending execute persisted before network I/O
→ POST /v1/restore/execute
   exact request_id + command_seq + generation
→ ambiguous retry preserves same request ID, command sequence and generation
→ merged B2 remains destructive authority
→ browser polls pathless restoring/final state
```

Closed guarantees:

- parser accepts exactly `restoring`, `restore_completed`, `restore_failed`, `restore_blocked` in addition to closed A4 states and still fails closed on unknown state;
- generation comes only from the current parsed `accepted` snapshot;
- select/cancel replay remains backward-safe;
- execute replay stores the exact positive generation;
- pending execute is persisted before HTTP and blocks duplicate destructive requests;
- dismiss/Escape are local;
- safe confirmation action receives initial focus;
- `restoring` exposes no select/cancel/reconfirm/destructive cancel/fake progress;
- pending execute presentation does not claim data is unchanged or Restore has not started;
- final browser states remain pathless and technical-detail-free.

## C4-II-C authorization

**C4-II-C — Truthful Restore completion/recovery/restart/support UX** is **AUTHORIZED NEXT — NOT IMPLEMENTED**.

Conceptually:

```text
merged B3
→ restoring
→ launcher-owned final state:
   restore_completed
   restore_failed
   restore_blocked
→ truthful human-readable final result
→ safe next action
→ restart/recovery/support guidance where appropriate
```

C4-II-C is **frontend-only**. Primary expected surface is `frontend/src/restore-control-presentation.ts`; `frontend/src/restore-control-entry.ts` is allowed only for bounded navigation/focus/help/restart affordance wiring.

Closed seams must remain byte-identical unless a separate architecture/lifecycle decision explicitly reopens them: `launcher/**`, `backend/**`, `frontend/src/restore-control-contract.ts`, `frontend/src/restore-control-runtime.ts`, `frontend/src/main.ts`, `frontend/src/app-navigation-routes.ts`, migrations, dependencies, package resources, ADR 0016 and ADR 0018.

Hard prohibitions: **no new launcher state**, **no new control endpoint**, **no browser filesystem authority**, **no destructive retry**, **no destructive cancel**, no automatic retry, no operation ID/durable phase in browser, no backend Restore ownership and no packaging redesign.

### Final-state truthfulness

- `restore_completed`: may present success and safe ordinary navigation only to the extent merged B2 semantics prove ordinary backend readiness.
- `restore_failed`: must not infer rollback, unchanged working data, restored old data or absence of mutation unless launcher-safe truth explicitly says so; do not encourage blind destructive retry.
- `restore_blocked`: must say ordinary work cannot safely continue in the current run; provide restart/recovery/support guidance and do not offer normal app navigation or destructive retry as if safe.
- **session/network uncertainty** after destructive execution may have begun must never be converted into success, failure, unchanged-data or rollback claims.

C4-III remains not authorized. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
