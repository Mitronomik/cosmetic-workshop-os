# Restore interaction and validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-09`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control/picker/exact-run browser session; current lifecycle plus the A/B slice plans for implementation status.

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

## Closed A1→A4 architecture

```text
browser SPA /backups/restore
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → A2 action/session coordinator
                           ├── A3 native picker
                           └── A1 validation worker
                         → C4-I intake/staging/validation
```

Browser owns presentation only. Launcher owns loopback control, picker, selected absolute path, candidate proof and all destructive authority.

## Retained A1 proof

A1 retains launcher-private canonical source path, `SourceIdentity`, full SHA-256, selection generation and compatibility for the current active generation. Filename/browser state/session token/history state are never destructive authority.

## Implemented B1 seam — proof binding at C4-I intake

B1 adds no second Restore pipeline and does not widen the historical base request surface. `RestoreRequest` remains the selected-source-only C4-I request. A future trusted launcher coordinator that owns the current retained A1 proof uses `ProofBoundRestoreRequest(RestoreRequest)` with one additional non-path field: `ExpectedSourceProof(SourceIdentity, SHA-256)`.

The engine opens the source once through existing `open_selected_source(...)`. Before `_execute_with_source(...)`, `bind_expected_source_proof(...)` proves against that exact `HeldSource`:

```text
RestoreRequest(selected_source=Path)
or
ProofBoundRestoreRequest(selected_source=Path, expected_source_proof=ExpectedSourceProof(...))
→ held.identity == expected SourceIdentity
→ held.revalidate()
→ held.assert_still_self_contained()
→ held.digest()
→ exact byte count + expected SHA-256
→ held.revalidate()
→ held.assert_still_self_contained()
→ same `HeldSource` descriptor
→ existing stage_source(...)
```

A path-only pre-check followed by a later re-open is forbidden. B1 does not do that: proof binding and staging use the same descriptor/object.

Any failure to reopen a previously accepted source, or any identity/content/self-containment mismatch at the B1 gate, fails before `prepared` with fixed `RestoreFailure.SOURCE_CHANGED` guidance. No path, SQL, migration ID, stack trace or database content enters the safe result.

`launcher/restore/staging.py` remains byte-identical to baseline blob `3126d5b1e68e764c135739fad71915912481c493`; existing source intake/staging semantics are not rewritten. Existing C4-I callers continue to use base `RestoreRequest` and retain current behavior.

The proof subtype carries no database path, backup-directory path, Restore-directory path or lock path. Those destructive/application-owned paths remain derived only from `LauncherLifecycleContext`.

## B1 non-goals

B1 does not authorize or implement:

- browser destructive confirmation;
- a new A2/control HTTP command;
- backend shutdown wiring from browser/session;
- a new user-facing `execute_restore(...)` coordinator;
- safety-copy creation merely to compare proof;
- a new staging/validation algorithm;
- durable phase/recovery changes;
- working-database replacement/migration changes;
- Restore AuditLog changes.

## Future B2/B3

B2 remains blocked until B1 is exact-head verified, merged and lifecycle-closed. B2 must separately define destructive launcher/session coordinator semantics while reusing existing C4-I `execute_restore(...)`; when authorized, that trusted coordinator is the only future owner allowed to construct `ProofBoundRestoreRequest` from the current A1 retained proof.

B3 remains blocked until B2 is merged and closed. It will own explicit destructive browser confirmation; browser state itself will still not be authority.
