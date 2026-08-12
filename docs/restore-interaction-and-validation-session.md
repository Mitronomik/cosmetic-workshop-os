# Restore interaction and validation-session profile

Status: **CURRENT — NORMATIVE INTERACTION PROFILE**
Updated: `2026-08-12`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control, native picker and exact-run browser session; ADR 0017 for the C4 split and C4-III verification/closure purpose.

## Current lifecycle

```text
PR #190 — MERGED — C4-III PARTIAL VERIFICATION CHECKPOINT
PR #189 — MERGED — C4-II-C LIFECYCLE CLOSURE AND C4-III AUTHORIZATION
PR #188 — MERGED — C4-II-C EXACT-HEAD VERIFIED
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
C4-II-C — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-III — IN PROGRESS — EXACT-HEAD VERIFICATION PASSED
C4-III EXACT-PACKAGE VERIFICATION — BLOCKED BY PACKAGED ARTIFACT PREREQUISITE
C4-III LIFECYCLE CLOSURE — NOT COMPLETED
CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION
D3 — macOS package MVP — AUTHORIZED NEXT — NOT IMPLEMENTED
D4 — Update safety — NOT AUTHORIZED BY CR-012
D5 — Remote install checklist — NOT AUTHORIZED BY CR-012
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed authority chain through C4-II-C

```text
A3/A1 picker + validation
→ B1 source-proof binding
→ B2 authenticated one-shot /v1/restore/execute
→ C4-I sole destructive engine
→ B3 explicit confirmation + exact replay
→ pathless restoring/final state
→ C4-II-C truthful final/recovery/support UX
```

PR #188 reviewed `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12`. C4-II-C is closed on accepted exact-head evidence.

### Final-state truth

- `restore_completed`: authoritative successful completion + ordinary work availability.
- `restore_failed`: authoritative unsuccessful Restore result + ordinary work availability, without rollback/unchanged-data inference.
- `restore_blocked`: authoritative restart/help-only state; ordinary work is not confirmed safe.
- pending/`restoring` uncertainty without a final launcher result remains unknown.
- true invalidation with cleared session/snapshot remains unknown + restart-only.
- an authenticated final B2 snapshot remains authoritative after same-tab replay loss; replay loss blocks further Restore commands only.
- ambiguous execute replay is the exact same pending command, never a new destructive request.

### Closed architecture

No source path, proof, operation ID, database path, backup path, lock path, SQL, traceback or durable phase is browser authority. No `/v1/restore/confirm` exists. Launcher/backend/contract/runtime/entry/main/navigation/ADRs and the final C4-II-C presentation are closed.

## C4-III authorization

C4-III — **Restore end-to-end verification and lifecycle closure** — is **IN PROGRESS — EXACT-HEAD VERIFICATION PASSED**.

C4-III must verify the already-merged interaction contract across success, supported older-schema, rejection, interruption, rollback, repeated launch, source immutability and safety-copy retention. It may extend tests/smoke evidence, but does not authorize new presentation semantics, command authority, endpoints or filesystem ownership.

Any discovered product defect requires a separate bounded fix before verification can claim PASS.

External exact-head verification of this interaction profile PASSED on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c`; no product defect was reported and this profile is unchanged. Exact-package verification of the same profile is still `INCONCLUSIVE — ENVIRONMENT` because no packaged artifact exists, so `C4-III LIFECYCLE CLOSURE — NOT COMPLETED`.

Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
