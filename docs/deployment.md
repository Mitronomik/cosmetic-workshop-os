# Deployment

Updated: `2026-08-12`

## Lifecycle

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

## Current topology

The product remains local-first on the MacBook. Ordinary business work uses the local FastAPI backend; Restore control remains launcher-owned on `127.0.0.1:<ephemeral>` under ADR 0018.

PR #188 / C4-II-C introduced no deployment topology change. The lifecycle-closure transition also introduces no service, port, cloud dependency, backend Restore endpoint or mandatory internet. The C4-III partial-verification checkpoint introduces none either — it records an already completed external verification result and nothing else.

C4-III is verification/lifecycle work. It does not authorize deployment topology, packaging or updater redesign. Exact-package verification required by ADR 0017 must use an authorized product artifact; that prerequisite is currently unavailable, so the verification is reported incomplete (`INCONCLUSIVE — ENVIRONMENT`) rather than changing packaging under C4-III.

## CR-012 packaged-artifact prerequisite

`CR-012` is ACCEPTED — [`decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](decisions/0019-c4-iii-packaged-artifact-prerequisite.md) — and authorizes one bounded successor task outside C4-III: `D3 — macOS package MVP — AUTHORIZED NEXT — NOT IMPLEMENTED`.

That task changes **no deployment topology**. The packaged product keeps the same shape it has today — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — and adds no service, no port, no cloud dependency, no backend Restore endpoint, no mandatory internet and no desktop application shell. It only makes the existing runtime distributable as `CosmeticWorkshopOS-mac.zip`.

CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization. Signing, notarization, mandatory DMG, auto-update, update download, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, D4 update safety and D5 remote-install work stay NOT AUTHORIZED.

Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
