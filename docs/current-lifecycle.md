# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-11`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

## Current lifecycle

```text
PR #185 — MERGED — B3 AUTHORIZED
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## Merged baseline through B3 authorization

PR #182 reviewed B1 head `27726058af4f373ab65225ecf4d1a945f1c53067` merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`.

PR #183 reviewed B2 authorization head `fa922f56c19a2dd33b6307ae0a197d476f91489b` merged as `4617b8c436eaa510fd545d863346595e2d808ea7`.

PR #184 reviewed B2 implementation head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4` merged as `266c50a77e5f353fa77701cb854629a99460667f`.

PR #185 reviewed B2-closure/B3-authorization head `f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c` merged as `f6589bdd7c403b6d400e3f5b7a0daea75b14632a`.

## Accepted B2 evidence

- focused B2/runtime tests: **37 PASS** in the independent audit;
- launcher regression: **636 PASS**;
- backend regression: **1867 PASS**;
- full backend + launcher: **2503/2503 PASS**;
- frontend Restore regression: **16/16 PASS**;
- anti-hang owner-loop gate: **PASS**, autonomous, no manual `Ctrl+C`;
- corrected external exact-head isolated process smoke: **PASS**;
- independent audit: **P0=0 / P1=0 / P2=0 — AUDIT GATE PASS**;
- final no-change exact-head / clean-worktree gate: **PASS**.

The earlier eight-hour run that required repeated manual `Ctrl+C` remains **INVALID / NOT A PASS**. The first external smoke runner remains **INCONCLUSIVE RUNNER**.

## Closed B2 boundary

```text
browser/session
→ authenticated POST /v1/restore/execute(request_id, command_seq, generation)
→ exactly-next sequence consumed before business preconditions
→ current accepted control generation + current launcher-private retained A1 proof
→ one in-memory RestoreExecutionIntent
→ retained source authority invalidated immediately
→ pathless restoring
→ HTTP returns without C4-I
→ launcher main runtime consumes intent synchronously
→ ProofBoundRestoreRequest from launcher-private authority
→ existing C4-I execute_restore(..., LauncherLifecycleContext)
→ canonical ordinary-backend restart handoff when safe
→ pathless restore_completed / restore_failed / restore_blocked
```

The accepted B2 launcher implementation is a closed boundary. The same control plane survives the destructive interval; browser generation remains a stale-view guard and never source proof.

## B3 implementation changeset

The current B3 changeset implements only the authorized frontend confirmation/replay seam:

```text
accepted browser snapshot
→ explicit human confirmation dialog
→ local dismiss OR destructive confirm
→ frontend creates one pending execute command
   request_id + command_seq + accepted generation
→ pending command is persisted in same-tab history replay state
→ authenticated POST /v1/restore/execute
→ ambiguous transport result keeps exact same request_id + command_seq + generation
→ merged B2 remains the destructive authority boundary
→ browser polls pathless restoring/final launcher state
```

Implemented frontend behavior:

- TypeScript parsing accepts exactly the four merged B2 execution states: `restoring`, `restore_completed`, `restore_failed`, `restore_blocked`;
- unknown control states remain fail-closed;
- pending replay is a discriminated union: select/cancel retain the historical shape, while execute additionally requires `generation`;
- `RestoreControlRuntime.execute()` derives generation only from the current parsed `accepted` snapshot; DOM code cannot supply filesystem authority or its own generation;
- execute request body is centralized and contains exactly `request_id + command_seq + generation`;
- ambiguous execute retry reuses the exact same request ID, command sequence and generation;
- explicit confirmation is local browser presentation; dismiss/Escape sends neither execute nor `/v1/restore/cancel`;
- repeated confirmation is blocked by the already-persisted pending command;
- `restoring` continues launcher-control polling and offers no select/cancel/destructive-cancel action or fake percentage;
- completed/failed/blocked states minimally present only the safe launcher-provided message;
- generic post-execute network guidance no longer falsely promises that working data was unchanged;
- `frontend/src/main.ts` is unchanged; B3 stays inside the focused Restore contract/runtime/presentation/entry modules.

No launcher, ordinary FastAPI backend, migration, dependency or domain behavior changes are included. No `/v1/restore/confirm` endpoint is added. Browser source path/proof/digest authority remains impossible.

## B3 verification gate

B3 is not lifecycle-closed merely because code exists. Before merge it still requires actual exact-head evidence for:

1. `git diff --check` and lifecycle checker;
2. frontend build/type-check;
3. focused Restore control tests covering exact execute schema, confirmation, exact replay, duplicate-submit race and B2 state parsing/presentation;
4. existing A4 bootstrap/session/select/cancel/replay regression;
5. desktop Restore-route smoke;
6. narrow-screen Restore-route smoke;
7. keyboard/focus/Escape confirmation smoke;
8. restoring/error/success/disabled-state review;
9. clean exact head/worktree;
10. independent `P0=0 / P1=0 / P2=0` audit.

Do not record these as PASS until they actually run against the published B3 PR head.

C4-II-C and C4-III remain **PLANNED — NOT AUTHORIZED**. Product Restore remains **NOT IMPLEMENTED** until later lifecycle closure adds the richer truthful result/restart/support experience and end-to-end product gate.