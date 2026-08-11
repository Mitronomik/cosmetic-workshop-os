# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-09`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

## Current lifecycle

```text
PR #183 — MERGED — B2 AUTHORIZED
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
C4-II-B2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## Merged authorization baseline

PR #182 reviewed head `27726058af4f373ab65225ecf4d1a945f1c53067` merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`, closing B1.

PR #183 final reviewed authorization head `fa922f56c19a2dd33b6307ae0a197d476f91489b` merged as `4617b8c436eaa510fd545d863346595e2d808ea7`, authorizing B2 only.

B1 accepted evidence remains: documentation lifecycle PASS; focused proof binding 10/10; Restore privacy 10/10; full backend+launcher 2480/2480; external exact-head A1-source-substitution smoke PASS; clean exact head/worktree; independent `P0=0 / P1=0 / P2=0`.

## Closed A1→B1 boundary

```text
A1 validates and retains launcher-private source path + SourceIdentity + SHA-256
→ B1 ProofBoundRestoreRequest carries non-path ExpectedSourceProof
→ C4-I opens source once
→ B1 re-proves same HeldSource identity/self-containment/full digest
→ same HeldSource enters unchanged C4-I staging
```

Browser filename/session/generation are never source proof. Base `RestoreRequest` remains selected-source-only. The proof subtype contains no target path. C4-I remains the only destructive Restore engine.

## B2 implementation changeset

The authorized B2 coordinator is implemented in the current changeset but is **not yet lifecycle-closed**.

Implemented flow:

```text
POST /v1/restore/execute(request_id, command_seq, generation)
→ exact-run Host/Origin/auth/schema/replay checks
→ exactly-next sequence consumed before business preconditions
→ accepted control generation checked
→ current launcher-private A1 retained proof copied into one RestoreExecutionIntent
→ retained source authority invalidated immediately
→ pathless state = restoring
→ HTTP returns without executing C4-I
→ main launcher runtime loop takes the intent
→ ProofBoundRestoreRequest from launcher-private path + ExpectedSourceProof
→ existing C4-I execute_restore(..., LauncherLifecycleContext)
→ existing C4-I owns backend stop/exclusion + destructive Restore semantics
→ main launcher runtime performs ordinary-backend restart handoff when safe
→ pathless restore_completed / restore_failed / restore_blocked result
```

The same `RestoreControlPlane` instance remains alive on the same ephemeral port while C4-I intentionally stops the ordinary backend and while restart is attempted. Heartbeat/state stay serviceable. Valid select/cancel/second-execute commands during `restoring` consume their sequence and return `restore_in_progress` without cancelling or duplicating destructive work.

Browser/session expiry after execution acceptance invalidates browser authentication and any stale candidate authority but does not cancel C4-I or overwrite launcher-owned `restoring`/final result state.

Control selection generation and A1 retained-proof generation remain separate domains. Browser `generation` is compared only with the accepted control snapshot generation; source authority comes only from the current launcher-private retained proof.

If C4-I allows normal startup, the main runtime releases the retained maintenance lease only immediately before the exact `BackendProcessOwner.start(...)` against canonical `context.database_path`. Only a child that proves the canonical liveness lock and listening socket permits `restore_completed` or `restore_failed` publication. Restart failure does not reinterpret or roll back C4-I truth and returns to safe maintenance exclusion before publishing `restore_blocked`.

No frontend source, ordinary FastAPI backend, migration, dependency, packaging resource, C4-I/B1 engine or A1 validation implementation is changed by B2.

## Successor gate

B2 is not closed merely because the code exists. Before merge it still requires focused/regression exact-head testing, external isolated process smoke, clean exact head/worktree and independent `P0=0 / P1=0 / P2=0` audit.

After merge, a separate lifecycle-closure change is required before any B3 authorization.

B3 remains **PLANNED — NOT AUTHORIZED**. C4-II-C and C4-III remain blocked. Product Restore is still **NOT IMPLEMENTED**.
