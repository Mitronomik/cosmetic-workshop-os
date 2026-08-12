# Packaging

Updated: `2026-08-11`

## Lifecycle

```text
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
C4-III — AUTHORIZED NEXT — NOT IMPLEMENTED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## C4-II-C closure / C4-III boundary

PR #188 / C4-II-C made no packaging, updater, helper-executable, dependency, port or installation-topology change. Its closure changes documentation/state/checker only.

C4-III is authorized for Restore end-to-end verification and lifecycle closure. ADR 0017 includes exact-package verification in that evidence, but this authorization does not authorize packaging implementation or redesign.

If a required packaged verification artifact is not yet available, C4-III must remain incomplete or report an environment/prerequisite gap. It must not hide packaging work inside the Restore verification slice.

macOS packaging, safe packaged update flow, installation verification and full release-candidate smoke remain separate future work. Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
