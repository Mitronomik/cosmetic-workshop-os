from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATUS=["README.md","docs/current-lifecycle.md","docs/implementation-plan.md","docs/packaging.md","docs/deployment.md","state/current-focus.md","state/progress.md","state/handoff.md","state/change-requests.md"]
OLD1="D5 — Remote install checklist — BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED"
OLD2="D5 verification — AUTOMATED BLOCKER FIX VERIFIED — FULL D5 PASS NOT YET CLAIMED"
OLD3="PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015"
NEW1="D5 — Remote install checklist — PILOT OPERATOR-ASSISTED PATH AUTHORIZED — FULL D5 PASS NOT CLAIMED"
NEW2="D5 verification — CR-016 FAIL RECORDED; OPERATOR-ASSISTED REHEARSAL NOT STARTED"
NEW3="PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015/CR-016/CR-017"
INSERT_AFTER="D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED"
EXTRA="\nCR-016 — ACCEPTED DECISION — IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL\nCR-017 — ACCEPTED — SINGLE-CLIENT OPERATOR-ASSISTED INSTALL/UPDATE CONTRACT\nD5 pilot deployment — OPERATOR-ASSISTED PATH AUTHORIZED NEXT — NOT IMPLEMENTED"

for rel in STATUS:
    p=ROOT/rel
    t=p.read_text()
    for old,new in ((OLD1,NEW1),(OLD2,NEW2),(OLD3,NEW3)):
        if old not in t: raise SystemExit(f"missing {old} in {rel}")
        t=t.replace(old,new)
    if "CR-017 — ACCEPTED — SINGLE-CLIENT OPERATOR-ASSISTED INSTALL/UPDATE CONTRACT" not in t:
        if INSERT_AFTER not in t: raise SystemExit(f"missing insertion anchor in {rel}")
        t=t.replace(INSERT_AFTER,INSERT_AFTER+EXTRA)
    p.write_text(t)

adr23=ROOT/"docs/decisions/0023-single-client-assisted-install-bootstrap.md"
t=adr23.read_text()
t=t.replace("Status: **ACCEPTED — CR-016 BOUNDED IMPLEMENTATION AUTHORIZED AFTER MERGE**","Status: **ACCEPTED DECISION — IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL; SUPERSEDED FOR PILOT DEPLOYMENT BY ADR 0024**")
if "## Implementation outcome" not in t:
    t += """

## Implementation outcome

CR-016 was implemented on head `0179be9fa1758a47662f86c5a14a7f24341815c5`. Automated macOS run `31959318870` proved only post-execution behavior. The mandatory clean-Mac Finder rehearsal then produced `FAIL — PRODUCT`: Gatekeeper quarantined and blocked the downloaded `.command` before it could execute, so it could not perform its embedded verification or reach its bounded quarantine-removal step. PR #210 was closed without merge.

The self-running downloaded bootstrap is therefore rejected as the pilot installation model. ADR 0024 supersedes only that deployment mechanism. The exact product package, CR-015 lifecycle fix, D4 safety and all application runtime semantics remain unchanged.
"""
adr23.write_text(t)

(ROOT/"docs/decisions/0024-single-client-operator-assisted-install.md").write_text(r'''# ADR 0024 — Single-client operator-assisted install and update

Status: **ACCEPTED — CR-017 BOUNDED IMPLEMENTATION AUTHORIZED AFTER MERGE**

Decision base: `d2aef241f46be58a1f4c535718f93d15f8209ed8`
Date: `2026-08-16`
Change request: `CR-017 — Single-client operator-assisted install and update`

## Context

CR-016 attempted to preserve a double-click self-service bootstrap while avoiding Developer ID/notarization for one known client. Its implementation passed automated post-execution tests, but the mandatory clean-Mac Finder rehearsal failed before bootstrap execution because Gatekeeper blocked the downloaded `.command` itself. This is a trust-boundary deadlock, not a product-runtime defect.

The project has one known client. There is not yet sufficient business justification to pay for and operationalize Developer ID/notarization solely for this pilot. The product architecture, packaged `.app`, native lifecycle, D4 update safety, Restore and external user-data boundary must remain unchanged.

## Decision

For the current single-client pilot only, installation and later manual package updates use an **operator-assisted support flow**.

A qualified support operator may connect by screen sharing or work directly at the Mac, open Terminal, and run a repository-owned/operator-owned installation script. The client must not type shell commands or understand them. Normal product use after installation remains Finder/Dock/browser/product UI only.

This decision supersedes the failed CR-016 self-running downloaded `.command` mechanism. It does not revive or merge PR #210.

## Mandatory verification-before-quarantine-removal contract

Before quarantine metadata is removed or an installed application is replaced, the operator flow must:

1. identify the exact `CosmeticWorkshopOS-mac.zip` selected for installation;
2. calculate SHA-256 with a macOS system tool;
3. compare it with an immutable expected SHA-256 supplied by the version-specific operator script or explicit trusted invocation argument;
4. stop immediately on mismatch;
5. extract the verified ZIP into a runner-owned staging directory under the current user's filesystem;
6. verify the staged `CosmeticWorkshopOS.app` bundle identifier, product version, `CFBundleExecutable`, executable native main and expected architecture;
7. only after every verification passes, remove `com.apple.quarantine` recursively from that exact verified staged `.app`;
8. never remove quarantine from arbitrary paths or from an unverified downloaded bootstrap.

## Operator and user boundary

The support operator may use Terminal, `shasum`, `plutil`, `file`, `xattr`, `ditto`, `open`, `osascript` and ordinary filesystem commands needed by the bounded script.

The client must not be asked to type or paste Terminal commands. The operator may explain that Terminal is being used only for installation/support.

The operator flow must not use `sudo`, must not request an administrator password, and should install under `~/Applications/CosmeticWorkshopOS.app`.

## Gatekeeper boundary

Gatekeeper remains globally enabled. CR-017 permits only the narrow equivalent of:

```text
xattr -dr com.apple.quarantine <verified-staged-CosmeticWorkshopOS.app>
```

It does not authorize `spctl --master-disable`, SIP changes, Startup Security changes, global quarantine removal, security-policy weakening, MDM bypass or any other system-wide trust change.

## First installation

For first installation, after candidate verification the operator script may remove quarantine from the verified staged app, publish it to `~/Applications/CosmeticWorkshopOS.app`, and launch it with normal macOS application launch semantics.

After launch, the client must be able to use Finder/Dock/browser UI without Terminal. Ordinary macOS Quit and restart remain governed by the closed CR-015 lifecycle implementation.

## Update behavior

The same operator tool may install a later exact package.

Before replacement it must verify the candidate fully. If the application is running, it may request ordinary application Quit through macOS automation and wait for complete shutdown, or fail closed and require the operator to close it normally. It must never force-kill the application as a successful update path.

The previous `.app` package must be retained separately before candidate publication. The tool must not automatically launch that retained package as rollback after the new version starts.

D4 remains the sole authority for schema compatibility, before-migration backup, staged migration, UpdateLog, interruption handling and migration failure. The operator installer must never edit the product database or user-data directory.

## Trust model

The support operator receives the exact expected SHA-256 through a trusted support channel and verifies the selected package before quarantine removal. For the one-client pilot this is sufficient to protect against accidental wrong-package use and transfer corruption.

This is not public code-signing identity. If the application gains additional independent clients or self-service/public distribution becomes economically justified, a new decision must evaluate Developer ID signing/notarization and replace this assisted trust model.

## Implementation scope

CR-017 authorizes only:

- one operator-owned macOS install/update script;
- deterministic tests for its fail-closed ordering and forbidden commands;
- optional packaging/support documentation for the operator;
- exact-package automated rehearsal on isolated data;
- a clean-Mac human operator-assisted rehearsal.

It does not authorize backend/frontend/domain changes, database changes, migrations, Restore changes, D4 changes, a new desktop framework, auto-update/download, cloud infrastructure, signing/notarization, DMG/PKG, App Store, public release hosting, release channels, Phase 12 or product release readiness.

## Human rehearsal contract

A D5 pilot-assisted PASS requires the actual exact package to be installed on the clean test Mac through the operator procedure, followed by client-style product use without Terminal: launch, backup/client/component/recipe smoke, ordinary Quit, restart and persistence verification.

The operator may use Terminal during installation. After installation the client-facing path must not require Terminal.

Success proves only the single-client operator-assisted pilot deployment. It does not prove unsigned self-service distribution or public release readiness.

## Stop conditions

Stop and request another decision if the operator flow requires administrator privileges, global security weakening, database manipulation, remote-control infrastructure, public/multi-client distribution claims, Developer ID/notarization, or changes to the product runtime itself.

## Non-goals

- no self-running downloaded `.command` requirement;
- no global Gatekeeper disable;
- no Developer ID/notarization in this stage;
- no product redesign;
- no backend/frontend/domain/Restore/D4 changes;
- no automatic update downloads;
- no Phase 12;
- no product release readiness claim.
''')

# Current focus
p=ROOT/"state/current-focus.md"; t=p.read_text()
a=t.index("## Current task")
b=t.index("## Prior CR-015 handoff truth")
t=t[:a]+'''## Current task

**Implement only CR-017 — Single-client operator-assisted install/update after this decision merges.**

CR-016 implementation head `0179be9fa1758a47662f86c5a14a7f24341815c5` and automated run `31959318870` remain historical evidence only. The clean-Mac human rehearsal proved the downloaded `.command` cannot bootstrap itself because Gatekeeper blocks it before execution; PR #210 is closed without merge.

CR-017 authorizes a support-operator Terminal workflow only. The operator verifies exact package SHA-256 and app identity before removing quarantine from the verified staged `.app`. The client never types commands. Gatekeeper stays globally enabled, no `sudo` is permitted, and product database/user-data/D4/Restore/runtime semantics remain untouched.

After the operator-assisted implementation is separately verified, repeat the clean-Mac D5 rehearsal using that operator procedure. Full D5 PASS, Phase 12 and product release readiness remain unclaimed.

'''+t[b:]
p.write_text(t)

# Change request ledger
p=ROOT/"state/change-requests.md"; t=p.read_text()
t=t.replace("Status: **ACCEPTED — BOUNDED IMPLEMENTATION AUTHORIZED AFTER DECISION MERGE**.","Status: **ACCEPTED DECISION — IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL**.",1 if "## CR-016" in t else 0)
if "## CR-017 — Single-client operator-assisted install and update" not in t:
    t += '''

### CR-016 implementation outcome

Implementation head `0179be9fa1758a47662f86c5a14a7f24341815c5` passed automated post-execution run `31959318870`, but the mandatory clean-Mac Finder rehearsal produced `FAIL — PRODUCT`: Gatekeeper blocked the downloaded `.command` before execution. PR #210 was closed without merge. The self-running bootstrap model is rejected.

## CR-017 — Single-client operator-assisted install and update

Status: **ACCEPTED — BOUNDED IMPLEMENTATION AUTHORIZED AFTER DECISION MERGE**.

Durable decision: `docs/decisions/0024-single-client-operator-assisted-install.md`.

CR-017 replaces only the failed CR-016 bootstrap mechanism. A qualified support operator may use Terminal/screen sharing to verify the exact product package, remove quarantine only from the verified staged `.app`, install/update under the current user's application space, and launch it. The client never types commands and Gatekeeper remains globally enabled.

CR-017 does not authorize `sudo`, global Gatekeeper/SIP/security weakening, database/Restore/D4 changes, backend/frontend/domain changes, signing/notarization, public distribution, auto-update/download, Phase 12 or product release readiness. A clean-Mac operator-assisted rehearsal remains mandatory before any pilot PASS claim.
'''
p.write_text(t)

# Current lifecycle authority + truth sections
p=ROOT/"docs/current-lifecycle.md"; t=p.read_text()
anchor="- ADR 0022 is authoritative for the bounded CR-015 native macOS lifecycle blocker fix discovered by that rehearsal."
if "ADR 0023" not in t:
    t=t.replace(anchor,anchor+"\n- ADR 0023 records the rejected CR-016 self-running bootstrap experiment.\n- ADR 0024 is authoritative for the CR-017 single-client operator-assisted install/update pilot path.")
if "## CR-017 operator-assisted pilot truth" not in t:
    t += '''

## CR-016 implementation outcome

CR-016's version-specific downloaded `.command` bootstrap was implemented and automated post-execution behavior passed on head `0179be9fa1758a47662f86c5a14a7f24341815c5` in run `31959318870`. The mandatory clean-Mac Finder rehearsal then produced `FAIL — PRODUCT`: Gatekeeper blocked the quarantined `.command` before it could execute. PR #210 was closed without merge. That self-running bootstrap is not an authorized current implementation target.

## CR-017 operator-assisted pilot truth

ADR 0024 authorizes the next bounded D5 pilot action: a qualified support operator may use Terminal/screen sharing to install or update one known client's exact package after mandatory SHA-256 and app-identity verification. Only the verified staged `.app` may have quarantine removed. The client must not type commands. Gatekeeper stays globally enabled; `sudo`, SIP/security weakening, database/Restore/D4 changes and public distribution remain forbidden.

The operator-assisted path is **AUTHORIZED NEXT — NOT IMPLEMENTED**. Full D5 PASS, Phase 12 and product release readiness remain unclaimed.
'''
p.write_text(t)

# Implementation plan add bounded path
p=ROOT/"docs/implementation-plan.md"; t=p.read_text()
if "## CR-017 — Single-client operator-assisted pilot path" not in t:
    t += '''

## CR-017 — Single-client operator-assisted pilot path

**AUTHORIZED NEXT — NOT IMPLEMENTED**.

CR-016's downloaded `.command` model failed the mandatory clean-Mac Finder handoff and is not mergeable. CR-017 replaces only that bootstrap mechanism with a support-operator Terminal workflow for one known client.

Implementation may add one operator-owned install/update script plus focused tests/documentation. It must verify package SHA-256 and staged app identity before quarantine removal, install under the user application directory without `sudo`, preserve the previous app during updates, use ordinary macOS Quit semantics, and leave all database/update safety to D4.

A clean-Mac operator-assisted rehearsal is required before any pilot D5 PASS. Public/self-service distribution, Developer ID/notarization, Phase 12 and release readiness remain outside this stage.
'''
p.write_text(t)

# Supporting docs append concise boundary
for rel in ("README.md","docs/packaging.md","docs/deployment.md","state/progress.md","state/handoff.md"):
    p=ROOT/rel; t=p.read_text()
    if "## CR-017 pilot distribution boundary" not in t:
        t += '''

## CR-017 pilot distribution boundary

The CR-016 self-running downloaded `.command` experiment failed the mandatory human Finder rehearsal because Gatekeeper blocked the bootstrap before execution. CR-017 therefore authorizes only a single-client **operator-assisted** install/update pilot: a qualified support operator may use Terminal to verify the exact package and remove quarantine only from the verified staged `.app`; the client does not type commands. Gatekeeper remains globally enabled. No public/self-service distribution, signing/notarization, Phase 12 or release-readiness claim is created.
'''
    p.write_text(t)

# Checker transforms
p=ROOT/"scripts/check_documentation_lifecycle.py"; t=p.read_text()
t=t.replace('ADR22 = P("docs/decisions/0022-native-macos-application-lifecycle.md")','ADR22 = P("docs/decisions/0022-native-macos-application-lifecycle.md")\nADR23 = P("docs/decisions/0023-single-client-assisted-install-bootstrap.md")\nADR24 = P("docs/decisions/0024-single-client-operator-assisted-install.md")')
old='''D5_STATUS = (\n    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",\n    "D5 — Remote install checklist — BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED",\n    "CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX",\n    "D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",\n    "D5 verification — AUTOMATED BLOCKER FIX VERIFIED — FULL D5 PASS NOT YET CLAIMED",\n    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015",\n    "Product release readiness — NOT CLAIMED",\n)'''
new='''D5_STATUS = (\n    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",\n    "D5 — Remote install checklist — PILOT OPERATOR-ASSISTED PATH AUTHORIZED — FULL D5 PASS NOT CLAIMED",\n    "CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX",\n    "D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",\n    "CR-016 — ACCEPTED DECISION — IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL",\n    "CR-017 — ACCEPTED — SINGLE-CLIENT OPERATOR-ASSISTED INSTALL/UPDATE CONTRACT",\n    "D5 pilot deployment — OPERATOR-ASSISTED PATH AUTHORIZED NEXT — NOT IMPLEMENTED",\n    "D5 verification — CR-016 FAIL RECORDED; OPERATOR-ASSISTED REHEARSAL NOT STARTED",\n    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015/CR-016/CR-017",\n    "Product release readiness — NOT CLAIMED",\n)'''
if old not in t: raise SystemExit("checker D5_STATUS anchor missing")
t=t.replace(old,new)
t=t.replace('"D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL",','"D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL",\n    "D5 — Remote install checklist — BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED",\n    "D5 verification — AUTOMATED BLOCKER FIX VERIFIED — FULL D5 PASS NOT YET CLAIMED",\n    "Implement only CR-016 — Single-client assisted install and update bootstrap",')
t=t.replace('require(CURRENT, ("ADR 0020", "ADR 0021", "ADR 0022",','require(CURRENT, ("ADR 0020", "ADR 0021", "ADR 0022", "ADR 0023", "ADR 0024",')
t=t.replace('"CR-015 closure truth", CR015_VERIFIED_HEAD','"CR-015 closure truth", "CR-016 implementation outcome", "CR-017 operator-assisted pilot truth", CR015_VERIFIED_HEAD')
t=t.replace('"BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED", "## D5 blocker','"PILOT OPERATOR-ASSISTED PATH AUTHORIZED — FULL D5 PASS NOT CLAIMED", "## D5 blocker')
t=t.replace('require(FOCUS, ("Repeat the D5 human clean-Mac/clean-profile rehearsal on the fixed exact package", CR015_VERIFIED_HEAD, CR015_MERGED_HEAD, CR015_VERIFY_RUN, CR015_PACKAGE_SHA256, "No new runtime implementation slice is authorized now"))','require(FOCUS, ("Implement only CR-017", "support operator", "client never types commands", "Gatekeeper", "operator-assisted rehearsal", CR015_VERIFIED_HEAD, CR015_MERGED_HEAD, CR015_VERIFY_RUN, CR015_PACKAGE_SHA256))')
insert='''\n\ndef check_adr23_and_adr24() -> None:\n    require(ADR23, (\n        "IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL",\n        "0179be9fa1758a47662f86c5a14a7f24341815c5",\n        "31959318870",\n        "PR #210 was closed without merge",\n        "ADR 0024 supersedes only that deployment mechanism",\n    ))\n    require(ADR24, (\n        "ADR 0024 — Single-client operator-assisted install and update",\n        "CR-017 — Single-client operator-assisted install and update",\n        "support operator",\n        "client must not type",\n        "SHA-256",\n        "xattr -dr com.apple.quarantine <verified-staged-CosmeticWorkshopOS.app>",\n        "Gatekeeper remains globally enabled",\n        "must not use `sudo`",\n        "~/Applications/CosmeticWorkshopOS.app",\n        "D4 remains the sole authority",\n        "clean-Mac human operator-assisted rehearsal",\n        "does not prove unsigned self-service distribution",\n    ))\n    forbid(ADR24, (\n        "Product release readiness — READY",\n        "signing — AUTHORIZED",\n        "notarization — AUTHORIZED",\n        "PHASE 12 — MVP release preparation — AUTHORIZED",\n    ))\n'''
marker='\ndef check_cr015_implementation_closure() -> None:'
if marker not in t: raise SystemExit("checker insert marker missing")
t=t.replace(marker,insert+marker)
t=t.replace('    check_adr22()\n    check_cr015_implementation_closure()','    check_adr22()\n    check_adr23_and_adr24()\n    check_cr015_implementation_closure()')
t=t.replace('print("Verified D5 still requires a fresh human clean-Mac/clean-profile rehearsal on the fixed exact package.")','print("Verified CR-016 self-running bootstrap implementation failed the human Finder handoff and is not current.")\n    print("Verified CR-017 operator-assisted single-client path is authorized next and not yet implemented.")')
p.write_text(t)

print("CR-017 decision transform complete")
