# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-09`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

## Current lifecycle

```text
PR #181 — MERGED — B1 AUTHORIZED
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
C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B2 — PLANNED — NOT AUTHORIZED
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

## B1 authorization baseline

PR #181 reviewed head `d2549cd9be2b60c5aee2479050e05a6ad8530c6c` merged as `beae1407af270ad1c800c308ea7907750430eb1d`. Its lifecycle gate closed C4-II-A and authorized only B1; B2/B3 remained not authorized.

## Closed C4-II-A boundary

A1 remains non-destructive candidate preparation and launcher-private retained proof. A2 remains exact-run loopback authentication/liveness/replay authority. A3 remains the launcher-owned native picker/path/process boundary. A4 remains the pathless browser fragment/session/presentation layer under `/backups/restore`.

The closed frontend remains unchanged by B1. `frontend/src/main.ts` must remain blob `ea98a76638bddcb5a92b9ba31941508f8a816d42`.

## B1 current implementation

B1 adds only a launcher-private proof binding seam while preserving the historical base request surface:

```text
RestoreRequest(selected_source=Path)
or
ProofBoundRestoreRequest(
    selected_source=Path,
    expected_source_proof=ExpectedSourceProof(SourceIdentity, SHA-256)
)
→ existing open_selected_source(...)
→ one `HeldSource` descriptor
→ bind_expected_source_proof(held, expected)
   → held.identity == expected identity
   → held.revalidate()
   → held.assert_still_self_contained()
   → held.digest()
   → exact byte-count + SHA-256 equality
   → held.revalidate()
   → held.assert_still_self_contained()
→ same `HeldSource` descriptor
→ existing stage_source(...)
```

For closure/checker wording, `ExpectedSourceProof` is the **optional launcher-private evidence at the existing C4-I intake seam**. That does not make it a field of base `RestoreRequest`: the optional branch is represented by choosing legacy `RestoreRequest` or `ProofBoundRestoreRequest`.

Base `RestoreRequest.__dataclass_fields__` remains selected-source-only. The proof-bound subtype adds only launcher-private non-path evidence; destructive/application-owned paths remain derived from `LauncherLifecycleContext`. Legacy requests without proof preserve current behavior.

The proof gate executes before `_execute_with_source(...)`, therefore before operation-directory creation, the `prepared` record, safety-copy creation or working-database mutation. Any pre-open source rejection after an A1 expectation exists, or any proof mismatch on the held descriptor, maps to fixed `RestoreFailure.SOURCE_CHANGED` guidance telling the user to select and validate the backup again.

`launcher/restore/staging.py` remains byte-identical at baseline blob `3126d5b1e68e764c135739fad71915912481c493`; B1 adds no second intake/staging algorithm. A1 remains byte-identical at `c8734ab60a576ecad53acd961571ddf2c14bdcf4`.

Focused B1 tests must prove exact match success, same `HeldSource` descriptor/fd continuity into staging, different-inode substitution refusal, same-inode/same-size digest drift refusal, late sidecar and symlink refusal, digest byte-count mismatch refusal, no `prepared`/safety copy/working-DB mutation on mismatch, source immutability, safe presentation, base-request compatibility and legacy C4-I behavior.

## Successor gate

B2 and B3 remain **PLANNED — NOT AUTHORIZED**. B1 must pass final exact-head tests, an external isolated smoke runner, independent P0/P1/P2 review, merge, and post-merge lifecycle closure before B2 may be authorized.

C4-II-C and C4-III remain blocked. Product Restore is still **NOT IMPLEMENTED**.
