# Packaging

Updated: `2026-08-12`

## Lifecycle

```text
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
C4-III — IN PROGRESS — EXACT-HEAD VERIFICATION PASSED
C4-III EXACT-PACKAGE VERIFICATION — NOT YET PASSED
C4-III LIFECYCLE CLOSURE — NOT COMPLETED
CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION
D3 — macOS package MVP — IMPLEMENTED — C4-III EXACT-PACKAGE VERIFICATION PENDING
D4 — Update safety — NOT AUTHORIZED BY CR-012
D5 — Remote install checklist — NOT AUTHORIZED BY CR-012
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## C4-II-C closure / C4-III boundary

PR #188 / C4-II-C made no packaging, updater, helper-executable, dependency, port or installation-topology change. Its closure changes documentation/state/checker only. PR #189 and the C4-III partial-verification checkpoint likewise change no packaging surface.

C4-III is authorized for Restore end-to-end verification and lifecycle closure. ADR 0017 includes exact-package verification in that evidence, but this authorization does not authorize packaging implementation or redesign.

If a required packaged verification artifact is not yet available, C4-III must remain incomplete or report an environment/prerequisite gap. It must not hide packaging work inside the Restore verification slice.

## Closed packaged-artifact prerequisite gap

The external C4-III verifier reported `PASS — C4-III EXACT-HEAD VERIFICATION PASSED` on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c`, and `INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE` for the packaged half, leaving `C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE`.

That classification stands exactly as recorded. It was an environment prerequisite — not a product failure and not a runner failure — and it is never rewritten as a PASS.

D3 has since built the missing artifact, so the **prerequisite** is closed while the **verification** is not:

```text
C4-III EXACT-PACKAGE VERIFICATION — NOT YET PASSED
```

The artifact now exists and `make package-macos` produces it. What has not happened is the independent external C4-III exact-package verifier running against it and passing. Until that runs, exact-package verification stays unpassed and C4-III lifecycle closure stays incomplete.

C4-III itself stays open and stays out of packaging. Inside the C4-III verification slice, do **not**:

- implement macOS packaging under C4-III;
- create a `.app`, `.dmg`, ZIP or packaged runtime to satisfy the gate;
- redesign packaging or updater architecture;
- relabel the exact-package result as PASS, FAIL PRODUCT or INCONCLUSIVE RUNNER;
- treat the passing exact-head half as sufficient for lifecycle closure.

## CR-012 — D3 macOS package MVP authorization

`CR-012` is **ACCEPTED**. The normative decision is [`decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](decisions/0019-c4-iii-packaged-artifact-prerequisite.md).

The exact-package verifier correctly reported `INCONCLUSIVE — ENVIRONMENT` because the required packaged artifact was unavailable. Separately, no packaging implementation had yet been authorized to produce that artifact. CR-012 closes only that authorization gap. It does not reclassify or amend the previously recorded verification result.

It authorizes the existing roadmap stage as the one bounded successor implementation task, outside C4-III:

```text
D3 — macOS package MVP — IMPLEMENTED — C4-III EXACT-PACKAGE VERIFICATION PENDING

Current purpose:
produce the packaged product artifact required for
C4-III exact-package verification.
```

`D3 — macOS package MVP` is the roadmap's own stage. CR-012 authorizes it rather than introducing a parallel packaging phase, and D3's roadmap scope, tests and non-goals stay authoritative.

That task packages the existing architecture and changes no product topology:

```text
macOS packaged product
→ existing local launcher
→ local backend on 127.0.0.1
→ built frontend
→ ordinary system browser / SPA
→ external user-data directory
```

Intended delivery shape is `CosmeticWorkshopOS-mac.zip` containing a self-contained, user-openable macOS product artifact — preferably a simple `CosmeticWorkshopOS.app` if that shape is reachable without changing the topology. The packaged user must not need Git, Python, Node.js, npm, Docker, GitHub, Codex, a terminal or manual shell commands. The package carries the launcher, a bundled backend runtime, the production frontend build, migrations, required configuration/resources and required offline help — and never a real user database, real backups, exports, attachments, logs, credentials, secrets or repository working data. User data stays outside the package and survives replacement and restart.

**No new desktop application shell is authorized.** Electron, Tauri, pywebview, a PyObjC shell, a second native product UI, a WebView replacement for the browser UI, a new Restore transport and a new backend Restore endpoint all remain unauthorized. ADR 0016 and ADR 0018 Restore ownership and security semantics are unchanged.

The bounded rule replaces the older blanket statement: **CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization.** Still NOT AUTHORIZED by CR-012: signing, notarization, mandatory DMG, installer redesign, auto-update, update download mechanism, GitHub Releases redesign, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, multi-user infrastructure, full release-candidate certification, general remote-install automation beyond testing this artifact, D4 update safety and D5 remote-install work. None of these belong to D3.

A future implementation PR may add a build-only packaging dependency or tool only under the six ADR 0019 conditions, and must STOP for a new decision if the artifact contract turns out to require a persistent runtime framework, desktop shell, sandbox model or Restore architecture change.

Producing the artifact is a verification prerequisite and is never product release readiness. Safe packaged update flow, installation verification and full release-candidate smoke remain separate future work needing separate authorization. Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.

## D3 implementation — how the package is built

D3 is implemented. The build is three scripts and one command.

```bash
make package-macos
```

It refuses on any non-Darwin host, and produces:

```text
build/package/CosmeticWorkshopOS.app
dist/CosmeticWorkshopOS-mac.zip
```

Both are build products. Neither is committed; `/build/` and `/dist/` are ignored.

### Package layout

```text
CosmeticWorkshopOS.app/
  Contents/
    Info.plist                        minimal bundle metadata, unsigned
    MacOS/CosmeticWorkshopOS          bootstrap → bundled python → entrypoint
    Resources/
      runtime/                        self-contained CPython + backend deps
      app/
        launcher/                     unchanged
        backend/app/                  unchanged, minus tests
        frontend/dist/                production build
        macos_package/                packaging runtime support
        help/                         offline help
        package-runtime.json          the build's self-description
```

The application root mirrors the repository layout, so `launcher/config.py`'s existing `parents[1]` path resolution finds `backend/` and `frontend/` inside the bundle with no packaging-aware code in the launcher.

### Self-contained runtime

A real, relocatable CPython is bundled rather than a frozen binary. The launcher starts the backend as a separate process with `sys.executable -m app.launcher_backend_entrypoint`, and that entrypoint acquires the backend-liveness lock and binds the configured socket before importing any application module. A freezer that turned `sys.executable` into a non-Python binary would silently break the `-m` contract and the inherited `pass_fds` handshake the Restore engine relies on. Keeping a genuine interpreter means the packaged backend starts exactly as it does from source.

Build-only dependency, under the six ADR 0019 conditions:

| | |
|---|---|
| Source | `astral-sh/python-build-standalone`, release `20260807` |
| Runtime | CPython `3.12.13`, `*-apple-darwin-install_only` |
| Transport | HTTPS only (`curl --proto '=https' --tlsv1.2`) |
| Integrity | SHA-256 pinned per architecture, verified before use, **fail closed** |
| Cache | outside the repository, under `~/Library/Caches/cosmetic-workshop-os/build` |
| End user | the end user needs no Python; the package refuses to run on a foreign interpreter |

Backend dependencies are read from `backend/pyproject.toml` rather than repeated in the build script, and installed wheels-only so a build never silently compiles against a developer's local toolchain. The resulting package runs offline.

D3 builds for the architecture of the building Mac and records it in `package-runtime.json`. Universal binaries are out of scope.

### Production frontend without Node

`macos_package/frontend_server.py` is a standard-library localhost server that serves `frontend/dist`, falls back to `index.html` for SPA routes, and proxies only `/api/*` to the local backend. It binds `127.0.0.1` only, adds no CORS headers, rejects path traversal, and holds no business logic. It preserves the exact configured local frontend origin `http://127.0.0.1:5173`, which the ADR 0018 Restore control plane checks as an exact `Origin`/`Host`.

It is not a general proxy: the target is fixed loopback, and no request can influence where a proxied request goes. Backend statuses pass through unchanged — only `502` (backend unreachable) is ever invented, because a synthesized success would let the SPA report a write that never happened.

### What D3 did not change

No protected closed Restore production file was modified. Launcher lifetime ownership, launcher/backend process separation, the backend-liveness lock, socket ownership, the inherited one-run handshake, the Restore control plane, the macOS picker, source immutability, the safety copy, the Restore state machine and rollback/recovery are all untouched. The packaged entrypoint calls `launcher.runtime.run_local_runtime` and adds no second supervisor.

No signing, notarization, DMG, installer, updater or release upload is added.

### Verification

`scripts/verify_macos_package.py` runs automatically at the end of every build and fails it on a bad artifact. It proves bundle structure, an executable entrypoint, the bundled interpreter, backend modules, every declared migration, the production frontend, offline help — and the exclusions: no database, no backups/exports/attachments/logs, no `.git`, no `node_modules`, no secret-looking files, and no reference to the build checkout.

This is a **structure** gate. It proves what the artifact contains, never that it runs. Live behaviour is the Level-5 external package smoke, which remains a separate merge gate, and the C4-III exact-package Restore verifier remains separate again.
