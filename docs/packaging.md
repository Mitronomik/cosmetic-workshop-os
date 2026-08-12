# Packaging

Updated: `2026-08-12`

## Lifecycle

```text
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
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## C4-II-C closure / C4-III boundary

PR #188 / C4-II-C made no packaging, updater, helper-executable, dependency, port or installation-topology change. Its closure changes documentation/state/checker only. PR #189 and the C4-III partial-verification checkpoint likewise change no packaging surface.

C4-III is authorized for Restore end-to-end verification and lifecycle closure. ADR 0017 includes exact-package verification in that evidence, but this authorization does not authorize packaging implementation or redesign.

If a required packaged verification artifact is not yet available, C4-III must remain incomplete or report an environment/prerequisite gap. It must not hide packaging work inside the Restore verification slice.

## Active packaged-artifact prerequisite gap

That condition is now the live state, not a hypothetical:

```text
C4-III EXACT-PACKAGE VERIFICATION — BLOCKED BY PACKAGED ARTIFACT PREREQUISITE
```

The external C4-III verifier reported `PASS — C4-III EXACT-HEAD VERIFICATION PASSED` on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c`, and `INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE` for the packaged half, leaving `C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE`.

The correct response is to leave C4-III open. Specifically, do **not**:

- implement macOS packaging under C4-III;
- create a `.app`, `.dmg`, ZIP or packaged runtime to satisfy the gate;
- redesign packaging or updater architecture;
- relabel the exact-package result as PASS, FAIL PRODUCT or INCONCLUSIVE RUNNER;
- treat the passing exact-head half as sufficient for lifecycle closure.

macOS packaging, safe packaged update flow, installation verification and full release-candidate smoke remain separate future work needing separate authorization. Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
