# ADR 0022 — Native macOS application lifecycle blocker fix

Status: **ACCEPTED — IMPLEMENTED AND EXACT-PACKAGE VERIFIED**
Decision base: `c91e62930915da357a2f9c74b9a054fe98e9df14`
Date: `2026-08-14`

## Context

CR-014 / ADR 0021 requires D5 to include a real non-technical clean-Mac or clean-profile rehearsal. That human rehearsal reached successful Gatekeeper approval, first packaged start and normal browser work, then exposed a blocker at application shutdown/restart.

Observed user-level behavior:

- the packaged app could be opened through the normal macOS security UI;
- the browser UI opened and ordinary D5 data actions could be completed;
- the `.app` did not present a healthy responsive macOS application lifecycle for normal Dock Quit;
- macOS reported the application as not responding;
- closing Safari/browser did not own or complete local runtime shutdown;
- a subsequent Finder launch could not be accepted as a verified restart.

This is `FAIL — PRODUCT` for the D5 human layer. D5 must not be closed on the earlier automated smoke.

## Why the previous automated smoke was insufficient

The package currently declares an `APPL` bundle, but `CFBundleExecutable` is a shell bootstrap which `exec`s the bundled Python `macos_package.entrypoint`. The Python runtime correctly owns frontend/backend startup and graceful SIGTERM handling, but it is not an AppKit application event-loop owner.

The earlier automated D5 package smoke called `process.terminate()` directly and verified the Python SIGTERM path. That proves graceful process shutdown when a signal is injected. It does **not** prove that a human can use the normal macOS application lifecycle through Finder/Dock and receive the same result.

## Decision

Introduce one minimal native macOS AppKit lifecycle executable as the bundle's `CFBundleExecutable`.

Its only responsibilities are:

1. register and remain responsive as a normal macOS application;
2. launch the existing self-contained packaged bootstrap/runtime as a child process;
3. forward package verification arguments to that child unchanged;
4. keep the existing browser UI as the product UI;
5. translate ordinary macOS Quit into graceful child termination and wait asynchronously for completion without blocking the AppKit event loop;
6. exit only after the child runtime has ended, or report a bounded shutdown problem without silently pretending success;
7. allow a later normal Finder launch to start a fresh runtime;
8. on an ordinary reopen request while already running, reopen/foreground the local browser workspace rather than starting a second backend runtime.

The native wrapper owns no business logic, domain service, database transaction, migration, backup, Restore or update-safety decision.

## Bounded implementation choice

For this fix, the native lifecycle executable may be a small Objective-C/AppKit program compiled at package-build time with the macOS developer toolchain. The shipped user package must still require no compiler, Python, Node.js, Terminal or developer tooling from the end user.

The existing shell bootstrap remains the self-contained runtime helper and continues to pin `PYTHONPATH`, clear `PYTHONHOME`, disable the user site, disable bytecode writes and execute the bundled Python interpreter. The native wrapper must not reimplement those isolation rules.

## Ownership after the fix

```text
Finder / Dock / macOS application lifecycle
→ native AppKit lifecycle wrapper
→ existing packaged bootstrap helper
→ bundled Python macos_package.entrypoint
→ existing launcher.runtime
→ local frontend + backend
→ external user-data directory
```

The browser remains a presentation surface. Closing a browser tab/window is not defined as application shutdown. The application itself remains visible/controllable through the macOS application lifecycle until the user quits it.

## Quit contract

A successful ordinary Quit must:

- be initiated through the macOS application lifecycle (Dock/menu/system application termination), not only by an external test signal;
- keep the native application responsive while the child shuts down;
- request the existing child runtime's graceful termination path;
- let the launcher stop the backend and release its workspace/liveness resources;
- release the frontend/backend ports;
- leave the user database and already committed data intact;
- leave no orphan packaged runtime/backend process.

If graceful child shutdown does not complete within the bounded wrapper timeout, the wrapper must not silently claim a clean Quit. The user must receive a fixed non-technical failure message and the D5 lifecycle test must fail.

## Restart contract

After successful ordinary Quit, opening the same `.app` again through Finder/LaunchServices must:

- start one fresh native application instance;
- start one fresh packaged runtime;
- open the browser workspace normally;
- read the same external user-data directory;
- preserve the D5 synthetic client/component/recipe and backup created before Quit.

Opening an already-running `.app` must not create a second backend writer. A reopen request should surface the existing local workspace.

## Build/package constraints

- user data remain outside the `.app`;
- the packaged Python runtime remains bundled and self-contained;
- no system Python or Node runtime is introduced;
- no Electron, Tauri or new desktop UI framework;
- no signing/notarization requirement is introduced by this decision;
- package architecture remains the current-build architecture contract unless separately changed;
- existing product-version projections remain authoritative.

## Test contract

The implementation PR must include focused tests plus a real macOS exact-package verification.

Required automated evidence:

1. structural verifier proves the bundle contains a native executable plus the isolated packaged runtime helper;
2. existing Python/package regression remains green;
3. exact `.app` is launched through normal macOS LaunchServices, not only by directly executing the child Python process;
4. the test observes frontend/backend readiness against isolated external user data;
5. application-level Quit is requested through the macOS application lifecycle (for example an application Quit Apple event), not merely `SIGTERM` injected into the child;
6. wrapper remains responsive and the runtime/backend exit cleanly;
7. ports are released and no orphan runtime remains;
8. the same `.app` is launched again through LaunchServices and persisted synthetic data remain available;
9. repository postflight is clean.

Automated PASS still does not close D5. After the fix is merged, D5 requires a fresh exact-package build and a fresh human clean-Mac/clean-profile rehearsal on that same artifact.

## Stop conditions

Stop and do not merge the blocker fix if any of the following is required:

- moving business/domain/data logic into the native wrapper;
- changing database/Restore/D4 update semantics to make Quit work;
- requiring Terminal commands from the user;
- introducing Electron/Tauri or another desktop application framework;
- requiring signing/notarization merely to make lifecycle logic function;
- weakening the external user-data or single-writer safety boundary.

## Non-goals

CR-015 does not authorize:

- signing or notarization;
- DMG/PKG creation;
- App Store distribution;
- GitHub Releases/public hosting;
- auto-update/download or release channels;
- MDM/remote-management;
- cloud sync;
- Phase 12;
- product release readiness;
- frontend redesign;
- Restore or D4 update-safety redesign.

## Implementation and verification closure

The bounded blocker fix is implemented and merged. Verified implementation head `d7f95141e5f41c7a806c3fafb71e942fe5892dd8` merged as `c38940349a80d345f3e833b61e4bf4e5e761c0eb` with `0` changed files. External exact-package run `31780899805` passed full regression and the required LaunchServices → application-level Quit → complete cleanup → LaunchServices restart → persistence path. Exact tested ZIP SHA-256: `85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6`.

The implementation preserves the decision boundary: native AppKit owns only application lifecycle; the existing bootstrap/Python launcher/backend own product runtime and data. Timeout behavior fails closed by cancelling Quit rather than force-killing the runtime owner.

## Authorization boundary

CR-015 authorizes no further runtime slice after this closure. The next action is the fresh D5 human clean-Mac/clean-profile rehearsal on the fixed exact package. D5 itself remains open and no downstream release stage becomes authorized by this implementation closure.
