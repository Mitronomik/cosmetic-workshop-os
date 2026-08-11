# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-11`

## Current lifecycle

```text
PR #185 — MERGED — B3 AUTHORIZED
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
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
Product release readiness — NOT CLAIMED
```

## Merged baseline

```text
PR #182 reviewed B1 head — 27726058af4f373ab65225ecf4d1a945f1c53067
PR #182 merge/new main — 5e13b50f1918dacbf8d54066c9156942a9adb895
PR #183 reviewed B2-authorization head — fa922f56c19a2dd33b6307ae0a197d476f91489b
PR #183 merge/new main — 4617b8c436eaa510fd545d863346595e2d808ea7
PR #184 reviewed B2 head — 1ae8bfcdf0f1f1798ce85eac0931925d029379c4
PR #184 merge/new main — 266c50a77e5f353fa77701cb854629a99460667f
PR #185 reviewed B3-authorization head — f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c
PR #185 merge/new main — f6589bdd7c403b6d400e3f5b7a0daea75b14632a
```

## Closed implementation — C4-II-B2

B2 is merged and exact-head verified. Its closed launcher flow remains:

```text
POST /v1/restore/execute
  exact body: request_id + command_seq + generation
→ authenticated/session/replay checks
→ consume exactly-next sequence before business preconditions
→ require current accepted control generation + current retained A1 proof
→ copy launcher-private authority into one RestoreExecutionIntent
→ invalidate retained source authority
→ HTTP returns safe restoring state without running C4-I
→ launcher main runtime consumes intent synchronously
→ ProofBoundRestoreRequest
→ existing execute_restore(..., LauncherLifecycleContext)
→ existing C4-I owns all destructive semantics
→ safe ordinary-backend restart/result handoff
```

Accepted B2 evidence remains: focused B2/runtime 37 PASS; launcher 636; backend 1867; total 2503/2503; frontend Restore 16/16; autonomous anti-hang PASS; corrected external process smoke PASS; independent `P0=0/P1=0/P2=0`; final clean-head PASS.

The accepted B2 production blobs remain closed and are not editable in B3.

## Current implementation changeset — C4-II-B3

B3 implements only the browser confirmation + exact destructive replay seam authorized by merged PR #185.

```text
accepted snapshot
→ explicit native dialog confirmation
→ local dismiss/Escape OR destructive confirm
→ RestoreControlRuntime.execute()
→ capture current accepted generation
→ persist pending execute before HTTP
→ POST /v1/restore/execute
   exact request_id + command_seq + generation
→ ambiguous response preserves exact pending execute
→ retry resends same request_id + command_seq + generation
→ merged B2 owns destructive authority
→ browser polls pathless restoring/final state
```

## Implemented B3 seams

### Contract/parser

- adds exactly `restoring`, `restore_completed`, `restore_failed`, `restore_blocked` to the frontend state union/parser;
- unknown states still fail closed;
- snapshot exact-key validation is unchanged;
- adds action `execute` without adding a new server endpoint;
- replay state remains version `1` for backward compatibility;
- select/cancel pending shape is unchanged;
- execute pending additionally requires positive integer `generation`;
- replay parsing rejects extra keys including attempted filesystem authority;
- one helper builds exact command bodies so execute emits only `request_id`, `command_seq`, `generation`.

### Runtime

- `execute()` obtains generation only from the current parsed `accepted` snapshot;
- execute from any non-accepted state queues/sends nothing;
- pending execute is persisted before awaiting HTTP;
- network ambiguity keeps that pending command intact;
- retry uses the exact same ID/sequence/generation and does not allocate a second sequence;
- a second near-simultaneous execute sees pending and does not send another destructive request;
- `restoring` joins selecting/validating as a polled launcher-control state;
- generic post-bootstrap network copy does not falsely say data was unchanged after destructive work may have started.

### Presentation/entry

- accepted state shows explicit danger action but does not auto-execute;
- native `<dialog>` confirmation uses safe filename only;
- copy explains replacement, temporary unavailability and protective copy;
- safe `Вернуться` receives initial focus; destructive action is separate;
- dismiss/Escape are local and do not call `/v1/restore/cancel`;
- confirmation is generation-bound and is invalidated when runtime view changes;
- `restoring` hides select/cancel/re-confirm and shows no fake percentage/phase;
- final B2 states minimally present safe launcher messages;
- `main.ts` remains unchanged.

## B3 implementation surface

Production:

```text
frontend/src/restore-control-contract.ts
frontend/src/restore-control-runtime.ts
frontend/src/restore-control-presentation.ts
frontend/src/restore-control-entry.ts
```

Focused tests:

```text
frontend/test/restore-control.test.mjs
frontend/test/restore-control-races.test.mjs
```

Lifecycle/status/checker files may change only to record B3 implementation and enforce the authorized scope.

No `launcher/**`, `backend/**`, migration, dependency or package-resource implementation is in B3 scope. `frontend/src/main.ts` and `frontend/src/app-navigation-routes.ts` remain unchanged.

## Forbidden scope

No `/v1/restore/confirm`, no browser filesystem authority, no source path/proof/digest persistence, no launcher/backend Restore change, no second Restore engine, no destructive cancel, no phase/recovery redesign, no Restore AuditLog change, no new dependency, no packaging redesign, no C4-II-C/C4-III authorization.

## Required B3 proof before merge

The current code is **not yet closed** and test success is not implied by this document. The published exact PR head must prove:

1. `git diff --check`;
2. lifecycle checker;
3. frontend build/type-check;
4. focused `test:restore-control` suite;
5. B2 state parser exactness and unknown-state fail-closed behavior;
6. exact execute request body and generation source;
7. explicit confirmation and local dismiss/Escape semantics;
8. ambiguous execute exact replay;
9. reload with pending execute;
10. duplicate execute race produces one destructive request;
11. restoring polling and no cancel/reconfirm/fake progress;
12. final safe state presentation;
13. existing A4 bootstrap/session/select/cancel/replay regression;
14. desktop + narrow-screen `/backups/restore` smoke;
15. keyboard/focus/Escape dialog smoke;
16. clean exact head/worktree;
17. independent `P0=0/P1=0/P2=0` audit.

## Next action

Publish B3 as one bounded Draft PR → run exact-head frontend build/focused tests and lifecycle gate → run desktop/narrow/keyboard browser-control smoke → independent audit → merge only when all evidence is green → separate B3 lifecycle closure before any C4-II-C authorization.