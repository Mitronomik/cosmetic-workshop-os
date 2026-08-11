# Deployment

Updated: `2026-08-11`

## Lifecycle

```text
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
C4-II-C — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Current topology

The product remains local-first on the MacBook. Ordinary business work uses the local FastAPI backend; Restore control remains launcher-owned on `127.0.0.1:<ephemeral>` with the same exact-run security boundary defined by ADR 0018.

PR #186/B3 introduced no deployment topology change. The B3 closure PR is documentation/state/checker-only.

C4-II-C is authorized as **frontend-only** presentation/wiring over existing launcher states. It must introduce **no deployment topology change**, no new service, no new port, no cloud dependency, no backend Restore endpoint and no mandatory internet.

No new launcher state, no new control endpoint, no browser filesystem authority, no destructive retry and no destructive cancel are authorized.

C4-III remains not authorized. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
