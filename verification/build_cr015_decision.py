from __future__ import annotations

from pathlib import Path

BASE = "c91e62930915da357a2f9c74b9a054fe98e9df14"

OLD_STATUS = """CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — NOT STARTED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014
Product release readiness — NOT CLAIMED"""

NEW_STATUS = """CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
Product release readiness — NOT CLAIMED"""

STATUS_FILES = [
    Path("README.md"),
    Path("docs/current-lifecycle.md"),
    Path("docs/implementation-plan.md"),
    Path("docs/packaging.md"),
    Path("docs/deployment.md"),
    Path("state/current-focus.md"),
    Path("state/progress.md"),
    Path("state/handoff.md"),
    Path("state/change-requests.md"),
]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement anchor, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        raise SystemExit(f"{path}: marker already present: {marker}")
    path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


for path in STATUS_FILES:
    replace_once(path, OLD_STATUS, NEW_STATUS)

# The current task must stop authorizing docs-only D5 and authorize exactly the blocker fix.
replace_once(
    Path("state/current-focus.md"),
    """## Current task

**Implement D5 Remote Install Checklist only, under CR-014 / ADR 0021.**

D5 is the only authorized next stage. It is documentation + exact-package assisted-install rehearsal over the existing D3/D4 package, with mandatory clean-Mac/clean-profile human UI evidence before D5 closure. Do not modify backend/frontend/launcher/migrations/package runtime under this authorization. If rehearsal finds a product defect, stop and authorize/fix it separately.

Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12, product release readiness claims or Restore changes.""",
    """## Current task

**Implement only the CR-015 native macOS application lifecycle blocker fix.**

A clean-Mac human D5 rehearsal confirmed that the current packaged `.app` can start and serve the browser UI, but it does not behave as a healthy native macOS application lifecycle owner: the Dock reports the app as not responding, ordinary Quit is not available as a reliable graceful shutdown path, and a subsequent Finder launch cannot be accepted as a verified restart. D5 closure is blocked.

CR-015 authorizes one bounded runtime repair: a minimal native AppKit lifecycle wrapper around the existing packaged bootstrap/launcher. The browser remains the product UI; backend/domain/data ownership does not move into the native wrapper. Do not modify business logic, database semantics, Restore semantics, D4 update semantics, frontend product flows or migrations except where a focused test harness must observe lifecycle behavior.

Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12 or product release readiness claims.""",
)

# Implementation plan: D5 stays blocked; one repair slice becomes authorized.
plan = Path("docs/implementation-plan.md")
replace_once(
    plan,
    """## D5 — Remote install checklist

**AUTHORIZED NEXT — NOT IMPLEMENTED** under CR-014 / ADR 0021.

D5 is documentation + exact-package assisted-install rehearsal only. It must turn the existing install skeletons into a repeatable non-technical Finder/System Settings flow, then prove the roadmap client/component/recipe/restart scenario on a clean Mac or clean macOS user profile with exact artifact/environment evidence. Automated package smoke alone is insufficient for D5 closure; the human UI rehearsal is mandatory.

D5 may not change product runtime behavior. If rehearsal exposes a product defect, stop and authorize/fix that defect separately before closure.""",
    """## D5 — Remote install checklist

**BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL** under CR-014 / ADR 0021.

The D5 documentation/exact-package rehearsal branch reached the mandatory clean-Mac human step and exposed a runtime blocker in the packaged `.app`: the browser UI could be used, but the application did not provide a healthy native macOS lifecycle for ordinary Dock Quit and verified Finder restart. Automated direct-process SIGTERM smoke is not sufficient evidence for that user path.

D5 remains open and may not claim PASS until the blocker is fixed, a fresh exact package is built, automated verification is repeated, and the human clean-Mac/clean-profile rehearsal is repeated on that same artifact.

## D5 blocker — Native macOS application lifecycle

**AUTHORIZED NEXT — NOT IMPLEMENTED** under CR-015 / ADR 0022.

Implement only a minimal native AppKit lifecycle wrapper that owns macOS application responsiveness, ordinary Quit and restart handoff while delegating all product runtime work to the existing packaged bootstrap/launcher. The browser remains the UI. No business logic, database ownership, Restore/update semantics, signing/notarization or release/distribution feature is authorized by this repair.""",
)

current = Path("docs/current-lifecycle.md")
replace_once(
    current,
    "- ADR 0021 is authoritative for D5 Remote Install Rehearsal once CR-014 is merged.",
    "- ADR 0021 is authoritative for D5 Remote Install Rehearsal.\n- ADR 0022 is authoritative for the bounded CR-015 native macOS lifecycle blocker fix discovered by that rehearsal.",
)
append_once(
    current,
    "## D5 blocker truth",
    """## D5 blocker truth

The mandatory human D5 rehearsal on a clean Mac produced a product-level stop condition after successful first launch and normal Gatekeeper approval: the packaged app did not expose a healthy native macOS application lifecycle. The Dock reported the application as not responding; closing the browser did not own or complete application shutdown; and a subsequent Finder launch could not be accepted as a valid restart. This is classified `FAIL — PRODUCT` for the D5 human layer, not a runner failure.

Current code explains the boundary: `CFBundleExecutable` points to a shell bootstrap which `exec`s the bundled Python entrypoint. That Python process owns the local frontend/backend launcher but does not itself run an AppKit application event loop. The previous automated D5 smoke sent SIGTERM directly to that process and therefore did not prove the user-level Dock Quit contract.

CR-015 / ADR 0022 authorizes one bounded repair: make a minimal native AppKit executable the `.app` lifecycle owner; have it launch the existing self-contained bootstrap/runtime as a child; translate ordinary macOS Quit into graceful child termination; remain responsive while shutdown completes; and allow a clean subsequent Finder launch. The native wrapper owns no business/domain/data logic. Browser UI, backend API, launcher, Restore, D4 update safety and external user-data semantics remain authoritative and unchanged.

D5 closure remains blocked until a fresh exact package containing the fix passes both automated package verification and the mandatory clean-Mac/clean-profile human rehearsal. `PHASE 12` and product release readiness remain unauthorized/not claimed.""",
)

append_once(
    Path("docs/packaging.md"),
    "## CR-015 native macOS lifecycle blocker",
    """## CR-015 native macOS lifecycle blocker

The first clean-Mac D5 human rehearsal exposed that the current shell/Python `CFBundleExecutable` does not provide a healthy native macOS Dock/Quit lifecycle even though the local browser product runtime itself starts. CR-015 / ADR 0022 authorizes a minimal AppKit lifecycle executable around the existing packaged bootstrap only. This is a product-lifecycle repair, not signing/notarization, DMG/PKG, App Store packaging or a new desktop UI framework.""",
)

append_once(
    Path("docs/deployment.md"),
    "## CR-015 lifecycle repair boundary",
    """## CR-015 lifecycle repair boundary

CR-015 changes no deployment topology: the application remains local-first, the browser remains the UI, and user data remain external to the `.app`. The only authorized runtime change is the native macOS application lifecycle wrapper required for responsive Dock Quit and repeat launch. No cloud, remote management or release-channel work is authorized.""",
)

append_once(
    Path("state/change-requests.md"),
    "## CR-015 — Native macOS application lifecycle blocker fix",
    """## CR-015 — Native macOS application lifecycle blocker fix

Status: **ACCEPTED — BOUNDED FIX AUTHORIZED NEXT**.

Durable decision: `docs/decisions/0022-native-macos-application-lifecycle.md`.

The mandatory D5 human rehearsal confirmed a product blocker: first launch and browser workflows worked, but the `.app` did not provide a healthy responsive native macOS lifecycle for ordinary Dock Quit and verified Finder restart. CR-015 authorizes only a minimal native AppKit lifecycle owner around the existing packaged bootstrap/launcher. It does not authorize business-logic changes, frontend redesign, database or migration changes, Restore/D4 semantic changes, signing, notarization, DMG/PKG, App Store, auto-update, public release hosting, MDM, Phase 12 or product release readiness.""",
)

append_once(
    Path("state/progress.md"),
    "## CR-015 blocker decision",
    """## CR-015 blocker decision

The clean-Mac D5 human rehearsal exposed `FAIL — PRODUCT` at ordinary application shutdown/restart. CR-015 / ADR 0022 authorizes the bounded native AppKit lifecycle repair next. D5 remains blocked and no release-readiness claim is permitted.""",
)

append_once(
    Path("state/handoff.md"),
    "## CR-015 handoff",
    """## CR-015 handoff

Next implementation work is only the native macOS application lifecycle blocker fix from ADR 0022. Preserve the existing browser UI, Python packaged entrypoint, launcher/backend ownership, external user-data boundary, Restore and D4 update semantics. Required acceptance proof includes a real packaged `.app` launched through LaunchServices, responsive application-level Quit (not direct SIGTERM as the sole proof), released ports/processes, repeat Finder launch and persistence, followed by a fresh human clean-Mac D5 rehearsal.""",
)

adr = Path("docs/decisions/0022-native-macos-application-lifecycle.md")
adr.write_text("""# ADR 0022 — Native macOS application lifecycle blocker fix

Status: **ACCEPTED — CR-015 BOUNDED FIX AUTHORIZED NEXT**  
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

The native wrapper owns **no** business logic, domain service, database transaction, migration, backup, Restore or update-safety decision.

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

## Authorization boundary

Only the **D5 blocker fix — Native macOS application lifecycle** is authorized next by CR-015. D5 remains blocked until the fix is merged and the complete fresh automated + human rehearsal is repeated. No downstream release stage becomes authorized merely because this decision is accepted.
""", encoding="utf-8")

# Update lifecycle checker to recognize the new bounded authorization.
checker = Path("scripts/check_documentation_lifecycle.py")
text = checker.read_text(encoding="utf-8")
text = text.replace(
    'ADR21 = P("docs/decisions/0021-d5-remote-install-rehearsal-contract.md")',
    'ADR21 = P("docs/decisions/0021-d5-remote-install-rehearsal-contract.md")\nADR22 = P("docs/decisions/0022-native-macos-application-lifecycle.md")',
    1,
)
old_tuple = '''D5_STATUS = (\n    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",\n    "D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED",\n    "D5 verification — NOT STARTED",\n    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014",\n    "Product release readiness — NOT CLAIMED",\n)'''
new_tuple = '''D5_STATUS = (\n    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",\n    "D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL",\n    "CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX",\n    "D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED",\n    "D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL",\n    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015",\n    "Product release readiness — NOT CLAIMED",\n)'''
if text.count(old_tuple) != 1:
    raise SystemExit("checker D5_STATUS anchor mismatch")
text = text.replace(old_tuple, new_tuple, 1)
text = text.replace(
    'require(CURRENT, ("ADR 0020", "ADR 0021", "D4-A closure truth", "D4-B closure truth", "D4-C closure truth", "D4-D closure truth", "D4 closure truth", "D5 decision truth", D4D_VERIFIED_HEAD, D4D_FINAL_RUN, "Restore remains closed"))',
    'require(CURRENT, ("ADR 0020", "ADR 0021", "ADR 0022", "D4-A closure truth", "D4-B closure truth", "D4-C closure truth", "D4-D closure truth", "D4 closure truth", "D5 decision truth", "D5 blocker truth", D4D_VERIFIED_HEAD, D4D_FINAL_RUN, "Restore remains closed"))',
    1,
)
text = text.replace(
    'require(PLAN, ("Normative D4 decision", "Normative D5 decision", "D4-A", "D4-B", "D4-C", "D4-D", "## D5 — Remote install checklist", "**AUTHORIZED NEXT — NOT IMPLEMENTED**"))',
    'require(PLAN, ("Normative D4 decision", "Normative D5 decision", "D4-A", "D4-B", "D4-C", "D4-D", "## D5 — Remote install checklist", "BLOCKED — PRODUCT DEFECT CONFIRMED", "## D5 blocker — Native macOS application lifecycle", "AUTHORIZED NEXT — NOT IMPLEMENTED"))',
    1,
)
text = text.replace(
    'require(FOCUS, ("Implement D5 Remote Install Checklist only", "documentation + exact-package assisted-install rehearsal", "Do not modify backend/frontend/launcher/migrations/package runtime"))',
    'require(FOCUS, ("Implement only the CR-015 native macOS application lifecycle blocker fix", "minimal native AppKit lifecycle wrapper", "Do not modify business logic, database semantics, Restore semantics, D4 update semantics"))',
    1,
)
anchor = '''def check_domain_clarification() -> None:\n'''
check22 = '''def check_adr22() -> None:\n    require(ADR22, (\n        "ADR 0022 — Native macOS application lifecycle blocker fix",\n        "Status: **ACCEPTED — CR-015 BOUNDED FIX AUTHORIZED NEXT**",\n        "Decision base: `c91e62930915da357a2f9c74b9a054fe98e9df14`",\n        "FAIL — PRODUCT",\n        "AppKit",\n        "ordinary macOS Quit",\n        "LaunchServices",\n        "existing packaged bootstrap",\n        "browser remains",\n        "no business logic",\n        "Objective-C",\n        "no Electron",\n        "fresh human clean-Mac/clean-profile rehearsal",\n        "Only the **D5 blocker fix — Native macOS application lifecycle** is authorized next",\n    ))\n    forbid(ADR22, (\n        "Product release readiness — READY",\n        "signing — AUTHORIZED",\n        "notarization — AUTHORIZED",\n        "DMG — AUTHORIZED",\n        "App Store — AUTHORIZED",\n        "auto-update — AUTHORIZED",\n        "PHASE 12 — MVP release preparation — AUTHORIZED",\n    ))\n\n\n'''
if text.count(anchor) != 1:
    raise SystemExit("checker check_domain_clarification anchor mismatch")
text = text.replace(anchor, check22 + anchor, 1)
text = text.replace("    check_adr21()\n    check_domain_clarification()", "    check_adr21()\n    check_adr22()\n    check_domain_clarification()", 1)
text = text.replace(
    'print("Verified CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal.")\n    print("Verified D5 is not implemented/verified and Phase 12/product release readiness remain gated.")',
    'print("Verified CR-014 D5 human rehearsal is blocked by a confirmed product lifecycle defect.")\n    print("Verified CR-015 authorizes only the native macOS application lifecycle blocker fix.")\n    print("Verified D5 closure, Phase 12 and product release readiness remain gated.")',
    1,
)
checker.write_text(text, encoding="utf-8")

print("CR-015 decision changes prepared from", BASE)
