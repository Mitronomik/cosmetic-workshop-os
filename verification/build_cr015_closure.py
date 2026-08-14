from __future__ import annotations

from pathlib import Path

SOURCE = "c38940349a80d345f3e833b61e4bf4e5e761c0eb"
VERIFIED_HEAD = "d7f95141e5f41c7a806c3fafb71e942fe5892dd8"
VERIFY_RUN = "31780899805"
PACKAGE_SHA = "85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6"

OLD_STATUS = """CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
Product release readiness — NOT CLAIMED"""

NEW_STATUS = """CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D5 verification — AUTOMATED BLOCKER FIX VERIFIED — FULL D5 PASS NOT YET CLAIMED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
Product release readiness — NOT CLAIMED"""

STATUS_FILES = [
    Path("README.md"), Path("docs/current-lifecycle.md"), Path("docs/implementation-plan.md"),
    Path("docs/packaging.md"), Path("docs/deployment.md"), Path("state/current-focus.md"),
    Path("state/progress.md"), Path("state/handoff.md"), Path("state/change-requests.md"),
]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: replacement anchor count {count} for {old[:90]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        raise SystemExit(f"{path}: marker already exists: {marker}")
    path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


for path in STATUS_FILES:
    replace_once(path, OLD_STATUS, NEW_STATUS)

replace_once(
    Path("state/current-focus.md"),
    """## Current task

**Implement only the CR-015 native macOS application lifecycle blocker fix.**

A clean-Mac human D5 rehearsal confirmed that the current packaged `.app` can start and serve the browser UI, but it does not behave as a healthy native macOS application lifecycle owner: the Dock reports the app as not responding, ordinary Quit is not available as a reliable graceful shutdown path, and a subsequent Finder launch cannot be accepted as a verified restart. D5 closure is blocked.

CR-015 authorizes one bounded runtime repair: a minimal native AppKit lifecycle wrapper around the existing packaged bootstrap/launcher. The browser remains the product UI; backend/domain/data ownership does not move into the native wrapper. Do not modify business logic, database semantics, Restore semantics, D4 update semantics, frontend product flows or migrations except where a focused test harness must observe lifecycle behavior.

Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12 or product release readiness claims.""",
    f"""## Current task

**Repeat the D5 human clean-Mac/clean-profile rehearsal on the fixed exact package.**

CR-015 is implemented and verified. Runtime implementation head `{VERIFIED_HEAD}` merged content-identically as `{SOURCE}` (`0` changed files from verified head to merge). External exact-package run `{VERIFY_RUN}` proved LaunchServices start, macOS application-level Quit, complete packaged runtime/backend cleanup, released ports, LaunchServices restart and persistence using exact ZIP SHA-256 `{PACKAGE_SHA}`.

No new runtime implementation slice is authorized now. Use the fixed exact package for the mandatory human D5 rehearsal. If the ordinary Finder/Dock/Quit/restart path fails again, stop and classify the new observation before changing code. If it passes, D5 still needs its documentation/checklist evidence and lifecycle closure; do not silently claim release readiness.

Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12 or product release readiness claims.""",
)

plan = Path("docs/implementation-plan.md")
replace_once(
    plan,
    """## D5 — Remote install checklist

**BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL** under CR-014 / ADR 0021.

The D5 documentation/exact-package rehearsal branch reached the mandatory clean-Mac human step and exposed a runtime blocker in the packaged `.app`: the browser UI could be used, but the application did not provide a healthy native macOS lifecycle for ordinary Dock Quit and verified Finder restart. Automated direct-process SIGTERM smoke is not sufficient evidence for that user path.

D5 remains open and may not claim PASS until the blocker is fixed, a fresh exact package is built, automated verification is repeated, and the human clean-Mac/clean-profile rehearsal is repeated on that same artifact.

## D5 blocker — Native macOS application lifecycle

**AUTHORIZED NEXT — NOT IMPLEMENTED** under CR-015 / ADR 0022.

Implement only a minimal native AppKit lifecycle wrapper that owns macOS application responsiveness, ordinary Quit and restart handoff while delegating all product runtime work to the existing packaged bootstrap/launcher. The browser remains the UI. No business logic, database ownership, Restore/update semantics, signing/notarization or release/distribution feature is authorized by this repair.""",
    f"""## D5 — Remote install checklist

**BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED** under CR-014 / ADR 0021.

The first clean-Mac rehearsal correctly exposed the native application lifecycle product defect. CR-015 has now repaired that blocker, but the earlier human failure is not converted into a PASS retroactively. D5 remains open until a fresh clean-Mac/clean-profile rehearsal runs the fixed exact package and the D5 documentation/checklist evidence is completed.

## D5 blocker — Native macOS application lifecycle

**DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED** under CR-015 / ADR 0022.

Verified implementation head `{VERIFIED_HEAD}` merged as `{SOURCE}` with `0` changed files. External run `{VERIFY_RUN}` passed the full Python regression (`2692 passed, 1 skipped`) and a real macOS exact-package lifecycle path: LaunchServices first start → synthetic backup/client/component/recipe → application Quit Apple event → no packaged processes/occupied ports → LaunchServices restart → persistence → second application-level Quit. Exact tested ZIP SHA-256: `{PACKAGE_SHA}`.

The native AppKit executable owns only macOS application lifecycle; the existing packaged helper/Python launcher remains the runtime owner. No business logic, database, Restore or D4 update semantics moved into native code. A shutdown timeout fails closed by cancelling Quit rather than killing the runtime owner and risking an orphan backend.""",
)

current = Path("docs/current-lifecycle.md")
append_once(
    current,
    "## CR-015 closure truth",
    f"""## CR-015 closure truth

CR-015 native macOS application lifecycle blocker fix is **DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED**.

Evidence:

- verified implementation head: `{VERIFIED_HEAD}`;
- merge commit/current implementation merge: `{SOURCE}`;
- verified head → merge: `0` changed files;
- external macOS exact-package run: `{VERIFY_RUN}`;
- full Python regression: `2692 passed, 1 skipped`;
- exact ZIP SHA-256: `{PACKAGE_SHA}`;
- evidence artifact: `9211850165`, digest `sha256:ee76ad8dd1bd404c577f2ce730471e5c73114939cd2d3ba119366b3d6f40aec2`;
- package artifact: `9211850871`, wrapper digest `sha256:3076e886ef1c17c247df5e1911273a87c23b325840f19810fe4da0e2fa94e888`;
- application-level Quit proof used a macOS Quit Apple event after LaunchServices start; direct child SIGTERM was not accepted as the proof.

D5 itself is **not** complete. The fixed exact package still requires the mandatory fresh human clean-Mac/clean-profile rehearsal and final D5 evidence. Phase 12 and product release readiness remain unauthorized/not claimed.""",
)

append_once(
    Path("docs/packaging.md"),
    "## CR-015 implementation closure",
    f"""## CR-015 implementation closure

The native lifecycle repair is merged and exact-package verified. `CosmeticWorkshopOS.app` now has a Mach-O/AppKit `CFBundleExecutable`, while `CosmeticWorkshopOSRuntime` retains the existing self-contained shell/Python isolation path. Verified head `{VERIFIED_HEAD}`, merge `{SOURCE}`, run `{VERIFY_RUN}`, exact ZIP SHA-256 `{PACKAGE_SHA}`. This closes only the lifecycle blocker; signing/notarization and release distribution remain out of scope.""",
)

append_once(
    Path("docs/deployment.md"),
    "## CR-015 closure deployment truth",
    """## CR-015 closure deployment truth

The merged native lifecycle repair changes no deployment topology. The browser remains the product UI, the backend remains local, and user data remain external to the `.app`. The fixed package now participates correctly in the macOS application lifecycle for ordinary Quit/restart. D5 still requires a fresh human clean-Mac rehearsal; no remote-management or release topology is authorized.""",
)

# Durable state evidence.
append_once(
    Path("state/progress.md"),
    "## CR-015 implementation closure",
    f"""## CR-015 implementation closure

CR-015 blocker fix is merged and verified. Verified head `{VERIFIED_HEAD}` → merge `{SOURCE}` changed `0` files. Run `{VERIFY_RUN}` passed `2692 passed, 1 skipped`, native package identity, LaunchServices start, application-level Quit/cleanup, restart persistence and second Quit. Exact ZIP SHA-256 `{PACKAGE_SHA}`. D5 full PASS remains unclaimed pending fresh human rehearsal.""",
)
append_once(
    Path("state/handoff.md"),
    "## CR-015 closure handoff",
    f"""## CR-015 closure handoff

Do not implement more runtime work now. The next action is the mandatory D5 human clean-Mac/clean-profile rehearsal using the fixed exact package verified by run `{VERIFY_RUN}` (ZIP SHA-256 `{PACKAGE_SHA}`). Ordinary Quit must be performed through the macOS application lifecycle; closing the browser is not application shutdown. On success, complete D5 documentation/checklist evidence and lifecycle closure separately. On failure, stop and classify before changing code.""",
)

cr = Path("state/change-requests.md")
replace_once(cr, "Status: **ACCEPTED — BOUNDED FIX AUTHORIZED NEXT**.", "Status: **ACCEPTED — IMPLEMENTED AND EXACT-PACKAGE VERIFIED**.")
append_once(
    cr,
    "### CR-015 implementation evidence",
    f"""### CR-015 implementation evidence

Implemented by verified head `{VERIFIED_HEAD}`, merged as `{SOURCE}` with `0` changed files. External exact-package run `{VERIFY_RUN}` passed the complete application-level Quit/restart blocker matrix; exact ZIP SHA-256 `{PACKAGE_SHA}`. CR-015 is closed as an implementation blocker fix. D5 itself remains open for fresh human rehearsal and final evidence.""",
)

adr = Path("docs/decisions/0022-native-macos-application-lifecycle.md")
replace_once(adr, "Status: **ACCEPTED — CR-015 BOUNDED FIX AUTHORIZED NEXT**", "Status: **ACCEPTED — IMPLEMENTED AND EXACT-PACKAGE VERIFIED**")
replace_once(
    adr,
    """## Authorization boundary

Only the **D5 blocker fix — Native macOS application lifecycle** is authorized next by CR-015. D5 remains blocked until the fix is merged and the complete fresh automated + human rehearsal is repeated. No downstream release stage becomes authorized merely because this decision is accepted.""",
    f"""## Implementation and verification closure

The bounded blocker fix is implemented and merged. Verified implementation head `{VERIFIED_HEAD}` merged as `{SOURCE}` with `0` changed files. External exact-package run `{VERIFY_RUN}` passed full regression and the required LaunchServices → application-level Quit → complete cleanup → LaunchServices restart → persistence path. Exact tested ZIP SHA-256: `{PACKAGE_SHA}`.

The implementation preserves the decision boundary: native AppKit owns only application lifecycle; the existing bootstrap/Python launcher/backend own product runtime and data. Timeout behavior fails closed by cancelling Quit rather than force-killing the runtime owner.

## Authorization boundary

CR-015 authorizes no further runtime slice after this closure. The next action is the fresh D5 human clean-Mac/clean-profile rehearsal on the fixed exact package. D5 itself remains open and no downstream release stage becomes authorized by this implementation closure.""",
)

# Checker: transition truth + pin the merged blocker implementation.
checker = Path("scripts/check_documentation_lifecycle.py")
text = checker.read_text(encoding="utf-8")
old_tuple = '''D5_STATUS = (\n    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",\n    "D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL",\n    "CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX",\n    "D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED",\n    "D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL",\n    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015",\n    "Product release readiness — NOT CLAIMED",\n)'''
new_tuple = '''D5_STATUS = (\n    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",\n    "D5 — Remote install checklist — BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED",\n    "CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX",\n    "D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",\n    "D5 verification — AUTOMATED BLOCKER FIX VERIFIED — FULL D5 PASS NOT YET CLAIMED",\n    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015",\n    "Product release readiness — NOT CLAIMED",\n)'''
if text.count(old_tuple) != 1:
    raise SystemExit("checker D5_STATUS anchor mismatch")
text = text.replace(old_tuple, new_tuple, 1)

constant_anchor = 'LEGACY_CHECKER_SHA = "0d637269f802796098d5e6e911ad4d6a325ba990"\n'
constants = f'''LEGACY_CHECKER_SHA = "0d637269f802796098d5e6e911ad4d6a325ba990"\nCR015_VERIFIED_HEAD = "{VERIFIED_HEAD}"\nCR015_MERGED_HEAD = "{SOURCE}"\nCR015_VERIFY_RUN = "{VERIFY_RUN}"\nCR015_PACKAGE_SHA256 = "{PACKAGE_SHA}"\nCR015_APP_LIFECYCLE_BLOB = "0ec3ff6941227cd84e8eaf16bd4ea7a6b2281834"\nCR015_PACKAGE_SCRIPT_BLOB = "fdf8f01cc16db43320e5621a4a1f8a895ce65c56"\nCR015_PACKAGE_VERIFIER_BLOB = "19bd0bcd04ca98c39fed1c8dad9c50a3b142cc47"\n'''
if text.count(constant_anchor) != 1:
    raise SystemExit("checker constant anchor mismatch")
text = text.replace(constant_anchor, constants, 1)

text = text.replace(
    'require(CURRENT, ("ADR 0020", "ADR 0021", "ADR 0022", "D4-A closure truth", "D4-B closure truth", "D4-C closure truth", "D4-D closure truth", "D4 closure truth", "D5 decision truth", "D5 blocker truth", D4D_VERIFIED_HEAD, D4D_FINAL_RUN, "Restore remains closed"))',
    'require(CURRENT, ("ADR 0020", "ADR 0021", "ADR 0022", "D4-A closure truth", "D4-B closure truth", "D4-C closure truth", "D4-D closure truth", "D4 closure truth", "D5 decision truth", "D5 blocker truth", "CR-015 closure truth", CR015_VERIFIED_HEAD, CR015_MERGED_HEAD, CR015_VERIFY_RUN, CR015_PACKAGE_SHA256, "Restore remains closed"))',
    1,
)
text = text.replace(
    'require(PLAN, ("Normative D4 decision", "Normative D5 decision", "D4-A", "D4-B", "D4-C", "D4-D", "## D5 — Remote install checklist", "BLOCKED — PRODUCT DEFECT CONFIRMED", "## D5 blocker — Native macOS application lifecycle", "AUTHORIZED NEXT — NOT IMPLEMENTED"))',
    'require(PLAN, ("Normative D4 decision", "Normative D5 decision", "D4-A", "D4-B", "D4-C", "D4-D", "## D5 — Remote install checklist", "BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED", "## D5 blocker — Native macOS application lifecycle", "DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED", CR015_VERIFY_RUN, CR015_PACKAGE_SHA256))',
    1,
)
text = text.replace(
    'require(FOCUS, ("Implement only the CR-015 native macOS application lifecycle blocker fix", "minimal native AppKit lifecycle wrapper", "Do not modify business logic, database semantics, Restore semantics, D4 update semantics"))',
    'require(FOCUS, ("Repeat the D5 human clean-Mac/clean-profile rehearsal on the fixed exact package", CR015_VERIFIED_HEAD, CR015_MERGED_HEAD, CR015_VERIFY_RUN, CR015_PACKAGE_SHA256, "No new runtime implementation slice is authorized now"))',
    1,
)
text = text.replace(
    '"Status: **ACCEPTED — CR-015 BOUNDED FIX AUTHORIZED NEXT**",',
    '"Status: **ACCEPTED — IMPLEMENTED AND EXACT-PACKAGE VERIFIED**",',
    1,
)
text = text.replace(
    '"Only the **D5 blocker fix — Native macOS application lifecycle** is authorized next",',
    '"CR-015 authorizes no further runtime slice after this closure",\n        CR015_VERIFIED_HEAD, CR015_MERGED_HEAD, CR015_VERIFY_RUN, CR015_PACKAGE_SHA256,',
    1,
)

func_anchor = 'def check_domain_clarification() -> None:\n'
closure_func = '''def check_cr015_implementation_closure() -> None:\n    verify_blob(P("scripts/macos/app_lifecycle.m"), CR015_APP_LIFECYCLE_BLOB, "CR-015 native lifecycle source")\n    verify_blob(P("scripts/package_macos.sh"), CR015_PACKAGE_SCRIPT_BLOB, "CR-015 package builder")\n    verify_blob(P("macos_package/verification.py"), CR015_PACKAGE_VERIFIER_BLOB, "CR-015 package verifier")\n    require(P("scripts/macos/app_lifecycle.m"), (\n        "<NSApplicationDelegate>", "applicationShouldTerminate:", "NSTerminateLater",\n        "replyToApplicationShouldTerminate:NO", "CosmeticWorkshopOSRuntime",\n        "applicationShouldHandleReopen:",\n    ))\n    require(P("scripts/package_macos.sh"), ("xcrun --sdk macosx clang", "-framework Cocoa", "CosmeticWorkshopOSRuntime"))\n\n\n'''
if text.count(func_anchor) != 1:
    raise SystemExit("checker closure function anchor mismatch")
text = text.replace(func_anchor, closure_func + func_anchor, 1)
text = text.replace(
    '    check_adr22()\n    check_domain_clarification()',
    '    check_adr22()\n    check_cr015_implementation_closure()\n    check_domain_clarification()',
    1,
)
text = text.replace(
    '    print("Verified CR-014 D5 human rehearsal is blocked by a confirmed product lifecycle defect.")\n    print("Verified CR-015 authorizes only the native macOS application lifecycle blocker fix.")\n    print("Verified D5 closure, Phase 12 and product release readiness remain gated.")',
    '    print("Verified CR-015 native macOS lifecycle blocker fix is merged and exact-package verified.")\n    print("Verified D5 still requires a fresh human clean-Mac/clean-profile rehearsal on the fixed exact package.")\n    print("Verified D5 closure, Phase 12 and product release readiness remain gated.")',
    1,
)
# Active status surfaces must not regress to the superseded blocker state.
forbidden_anchor = '    "D5 — Remote install checklist — IMPLEMENTED",\n'
extra_forbidden = '    "D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL",\n    "D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED",\n    "D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL",\n'
if text.count(forbidden_anchor) != 1:
    raise SystemExit("checker forbidden anchor mismatch")
text = text.replace(forbidden_anchor, extra_forbidden + forbidden_anchor, 1)
checker.write_text(text, encoding="utf-8")

# Normalize accidental trailing whitespace before diff checks.
for path in STATUS_FILES + [plan, current, cr, adr, checker]:
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")

print("CR-015 lifecycle closure prepared from", SOURCE)
