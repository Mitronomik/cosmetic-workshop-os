# Deployment

Updated: `2026-08-12`

## Lifecycle

```text
PR #192 — MERGED — D3 MACOS PACKAGE MVP
PR #191 — MERGED — CR-012 / D3 AUTHORIZATION
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
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
C4-III EXACT-HEAD VERIFICATION — PASS
C4-III EXACT-PACKAGE VERIFICATION — PASS
C4-III LIFECYCLE CLOSURE — COMPLETED BY THIS CHANGESET
CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION
D3 — macOS package MVP — IMPLEMENTED
D4 — Update safety — NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE
D5 — Remote install checklist — NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
Product release readiness — NOT CLAIMED
```

## Current topology

The product remains local-first on the MacBook. Ordinary business work uses the local FastAPI backend; Restore control remains launcher-owned on `127.0.0.1:<ephemeral>` under ADR 0018.

PR #188 / C4-II-C introduced no deployment topology change. The lifecycle-closure transition also introduces no service, port, cloud dependency, backend Restore endpoint or mandatory internet. The C4-III partial-verification checkpoint introduced none either, and the C4-III lifecycle closure introduces none — it records already completed external verification results and nothing else.

C4-III was verification/lifecycle work. It does not authorize deployment topology, packaging or updater redesign, and neither does its closure. Exact-package verification required by ADR 0017 must use an authorized product artifact; when that prerequisite was unavailable the verification was reported incomplete (`INCONCLUSIVE — ENVIRONMENT`) rather than changing packaging under C4-III. The artifact was then produced by D3, under its own CR-012 authorization and outside the C4-III slice, and the exact-package verifier `c4-iii-restore-exact-package-v1.2` subsequently passed against the packaged runtime built from `0e1193264dc22979ca48e32a962aba916b6b520e`. Restore is verified and lifecycle-closed on the same topology it always had.

## CR-012 packaged-artifact prerequisite

`CR-012` is ACCEPTED — [`decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](decisions/0019-c4-iii-packaged-artifact-prerequisite.md) — and authorized one bounded successor task outside C4-III: `D3 — macOS package MVP — IMPLEMENTED`.

That task changes **no deployment topology**. The packaged product keeps the same shape it has today — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — and adds no service, no port, no cloud dependency, no backend Restore endpoint, no mandatory internet and no desktop application shell. It only makes the existing runtime distributable as `CosmeticWorkshopOS-mac.zip`.

As implemented, that remains exactly true. The package bundles a self-contained CPython so the end user needs no Python, and serves the production frontend through a standard-library localhost listener on the existing `http://127.0.0.1:5173` origin so the end user needs no Node. The backend is still a separate launcher-owned process on `127.0.0.1:8000`, started through the same `app.launcher_backend_entrypoint` with the same lock/socket handshake. The only new listener is the local frontend one, which replaces the Node development server in packaged mode and is owned by the packaged entrypoint for exactly one launcher run. See [`packaging.md`](packaging.md) for the build.

CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization. Signing, notarization, mandatory DMG, auto-update, update download, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, D4 update safety and D5 remote-install work stay NOT AUTHORIZED — and C4-III closure does not change that.

Safe packaged update flow, installation verification and full release-candidate smoke remain separate future work needing separate authorization. Product release readiness remains NOT CLAIMED.
