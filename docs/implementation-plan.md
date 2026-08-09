# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-09`

## Current lifecycle

```text
PR #181 — MERGED — B1 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Merged baseline

```text
PR #181 reviewed B1-authorization head — d2549cd9be2b60c5aee2479050e05a6ad8530c6c
PR #181 merge/new main — beae1407af270ad1c800c308ea7907750430eb1d
```

## Current implementation window — C4-II-B1

B1 is implemented as a narrow launcher-private gate while retaining the closed C4-I base request surface:

```text
RestoreRequest(selected_source=Path)
or
ProofBoundRestoreRequest(
    selected_source=Path,
    expected_source_proof=ExpectedSourceProof(SourceIdentity, SHA-256)
)
→ existing open_selected_source(...)
→ HeldSource H
→ bind_expected_source_proof(H, expected)
→ H.identity equality
→ H.revalidate()
→ H.assert_still_self_contained()
→ H.digest()
→ exact byte count + SHA-256 equality
→ H.revalidate() + self-containment again
→ same H
→ existing _execute_with_source(...)
→ unchanged stage_source(..., H)
```

A mismatch stops before `_execute_with_source(...)`, hence before `prepared`, `before_restore` and any working-database mutation. A fixed `SOURCE_CHANGED` message contains no path, SQL, migration ID, stack trace or database content.

## Mandatory B1 seams

- Base `RestoreRequest` remains selected-source-only; the historical C4-I type-level security invariant stays true.
- `ProofBoundRestoreRequest` is launcher-private and adds only `ExpectedSourceProof`, never another path.
- C4-I remains the only Restore engine.
- `launcher/restore/staging.py` remains byte-identical to baseline; no duplicate staging/validation algorithm exists.
- The proof check and staging use the same `HeldSource` object/fd.
- Existing C4-I calls using base `RestoreRequest` keep current behavior.
- B1 adds no browser route/button and no A2 control endpoint.
- B2/B3 remain not authorized.

## Required B1 proof before merge

1. focused B1 pytest contract passes;
2. base `RestoreRequest` remains selected-source-only;
3. matching identity+digest continues through existing C4-I;
4. different inode, same-inode changed bytes, late sidecar, symlink and short digest are refused;
5. mismatch creates no durable record, safety copy or working-DB change;
6. selected source stays unchanged;
7. legacy C4-I regression remains green;
8. A1/A2/A3/A4 closed-boundary regressions remain green;
9. full backend+launcher regression remains green;
10. exact published head is smoke-tested with an external isolated runner under the project smoke-runner contract;
11. worktree/head remain clean and exact;
12. independent P0=0/P1=0/P2=0 audit.

## Forbidden scope

No B2/B3 runtime wiring, browser destructive confirmation, new control command, FastAPI Restore mutation, second Restore engine, phase/recovery redesign, packaging redesign, cloud sync, OCR, roles/multiuser or advanced analytics.

## Next action

Publish B1 Draft PR → exact-head local tests → external isolated smoke → independent audit → merge only after all evidence is green → separate post-merge lifecycle closure before any B2 authorization.
