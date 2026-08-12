# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-11`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

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

macOS packaging, safe packaged update flow, installation verification and full release-candidate smoke remain incomplete.

## Merged baseline through C4-II-C authorization

- PR #186 reviewed B3 head `316358c65a851b46090121c7a6bc877b980176ba`, merged as `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`.
- PR #187 reviewed B3-closure/C4-II-C-authorization head `48e245811af706bb666620c6dda8033ff200967a`, merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7` at `2026-08-11T11:54:33Z`.

B3 remains closed on accepted exact-head evidence: frontend build PASS, focused Restore 30/30 PASS, browser smoke v4 PASS, final independent audit P0=0/P1=0/P2=0, final no-change gate PASS. The earlier P1=1 audit remains historical evidence and was corrected before merge.

## Closed authority chain through B3

```text
A3/A1 source selection + validation
→ B1 source-proof binding
→ B2 authenticated one-shot execute authority
→ C4-I sole destructive engine
→ B3 explicit browser confirmation + exact replay
→ pathless restoring/final launcher state
```

Closed seams remain byte-identical unless separately authorized: launcher/backend Restore authority, contract/runtime, `main.ts`, app navigation, ADR 0016 and ADR 0018.

## C4-II-C implementation changeset

C4-II-C is present in the current changeset but is **NOT YET CLOSED**.

Authorized production surface used:

```text
frontend/src/restore-control-presentation.ts
```

No `restore-control-entry.ts` change is needed.

### Truthful final states

- `restore_completed`: presents successful completion and ordinary navigation only within merged B2 backend-ready semantics.
- `restore_failed`: presents safe failure truth and ordinary availability without claiming rollback, unchanged data, restored old data or absence of mutation.
- `restore_blocked`: clearly says ordinary work is not safely available in this run, removes normal-work navigation and gives restart/help guidance.
- destructive-result session/network uncertainty remains unknown. It does not become success, failure, rollback or unchanged-data truth.

### Interaction rules

- normal-work `back` navigation is suppressed while `restoring`, while execute is pending/uncertain, and for `restore_blocked`;
- completed/failed states may return to backups because merged B2 proves ordinary backend readiness for those final states;
- an ambiguous pending execute may expose only the existing exact replay of the **same** command, with explicit wording that it is not a new Restore;
- no destructive confirm/cancel/reselection is exposed in final states.

### Closed architecture

No new launcher state, control endpoint, DTO field, browser filesystem authority, operation ID, durable phase, backend Restore endpoint, destructive cancel, automatic retry or new destructive request sequence is added.

`frontend/src/restore-control-contract.ts`, `frontend/src/restore-control-runtime.ts`, `frontend/src/restore-control-entry.ts`, launcher/backend, `main.ts`, navigation, migrations, dependencies, packaging resources and ADRs remain closed.

## Verification still required

Implementation presence does not imply PASS. The published PR head must still run:

1. `git diff --check`;
2. lifecycle checker;
3. frontend `npm ci`;
4. frontend build/type-check;
5. focused Restore suite — expected **34 tests** if no later test is added;
6. desktop + narrow browser smoke;
7. final-state truthfulness smoke for completed/failed/blocked/uncertainty;
8. keyboard/focus regression;
9. exact changed-path/closed-blob review;
10. clean head/worktree;
11. independent P0/P1/P2 audit.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
