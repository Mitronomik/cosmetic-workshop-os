# Handoff

Updated: `2026-08-09`

Current lifecycle authority: `docs/current-lifecycle.md`. Accepted Restore decisions: ADR 0016 and ADR 0018. Closed A plan: `docs/c4-ii-a-implementation-slices.md`. Current B plan: `docs/c4-ii-b-implementation-slices.md`.

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

## Authorization baseline — PR #181

```text
reviewed head — d2549cd9be2b60c5aee2479050e05a6ad8530c6c
merge/new main — beae1407af270ad1c800c308ea7907750430eb1d
```

## Current B1 implementation

```text
A1 retained SourceIdentity + SHA-256
→ ProofBoundRestoreRequest(
     selected_source=Path,
     expected_source_proof=ExpectedSourceProof(...)
   )
→ existing C4-I open_selected_source(...)
→ HeldSource H
→ bind_expected_source_proof(H, expected)
→ identity + revalidate + self-containment
→ full H.digest() + exact byte count
→ revalidate + self-containment again
→ exact same H
→ unchanged C4-I stage_source(..., H)
```

Base `RestoreRequest` remains selected-source-only for all historical C4-I callers. The proof subtype contains no additional filesystem path and grants no authority by itself.

Mismatch stops before `_execute_with_source(...)`, so there is no `prepared`, safety copy or working-database mutation. It returns fixed `SOURCE_CHANGED` guidance. `launcher/restore/staging.py` stays byte-identical to baseline.

Focused B1 tests are in `launcher/tests/test_restore_source_proof_binding.py`. PR-specific exact-head smoke must be external to the tested branch and use isolated data.

## Not B1

- browser confirmation/button;
- new control HTTP command;
- user-facing destructive coordinator;
- duplicate staging/validation engine;
- durable phase vocabulary changes;
- safety-copy/replacement/recovery redesign;
- Restore AuditLog changes.

## Successor gate

B2/B3 are not authorized. B1 must be exact-head verified, externally smoked, independently audited, merged and lifecycle-closed before B2 may be authorized.
