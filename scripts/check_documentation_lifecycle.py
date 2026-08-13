#!/usr/bin/env python3
"""Guard the closed C4-III Restore lifecycle and the bounds it did not widen.

C4-III is closed. Both required halves of the ADR 0017 evidence surface passed,
independently, against two different exact baselines:

```text
exact-head    PASS   81e8193596709b0c16d0ecad598458b3ea95fd9c
exact-package PASS   0e1193264dc22979ca48e32a962aba916b6b520e
```

Closure follows from the **combination** and from nothing else, so this checker
pins both baselines, both runners and both runner SHA-256s. It also pins the
load-bearing packaged evidence — the real `replacement_intent -> rolled_back`
hard-interruption recovery, source immutability, mandatory `before_restore`
retention, older-schema migration, `recovery_blocked` failing closed, and a run
that left no owned processes or ports — because a closure claim that no longer
carries its evidence is just an assertion.

Two things this checker protects that pull in opposite directions:

1. **The old open state must not survive.** `C4-III — IN PROGRESS`, `EXACT-PACKAGE
   VERIFICATION — NOT YET PASSED`, `LIFECYCLE CLOSURE — NOT COMPLETED`, the D3
   `EXACT-PACKAGE VERIFICATION PENDING` suffix and `Restore — NOT IMPLEMENTED`
   are now false on the active surfaces and are rejected there.
2. **The old history must survive.** The earlier `INCONCLUSIVE — ENVIRONMENT`
   exact-package result was correct when it was produced — no packaged artifact
   existed yet — and it is neither rewritten as a PASS nor reclassified as
   something other than an environment outcome. The same applies to the two
   external runner attempts that preceded acceptance: one `INCONCLUSIVE — RUNNER`
   and one `v1.1` textual `FAIL — PRODUCT` that inspection traced to a runner
   `UnboundLocalError`. Neither is product evidence, and neither is erased.

Those two pull apart cleanly because the superseded phrasings are forbidden on
the **active** surfaces only. ADR 0019 and the dated history keep them, where
they are accurate records rather than claims about now.

Closing C4-III grants nothing downstream. `Restore — IMPLEMENTED` is a
consequence of the lifecycle closure, not of any runtime change, and it is the
end of the Restore programme rather than the start of a release one. Product
release readiness stays NOT CLAIMED; D4, D5, signing, notarization, DMG,
auto-update, App Store, sandbox migration and cloud/sync stay NOT AUTHORIZED —
by CR-012 and by the closure alike. A dedicated guard rejects the specific
overclaim that exact-package verification proves release readiness.
"""

from __future__ import annotations

from hashlib import sha1
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
P = lambda value: ROOT / value

README = P("README.md")
CURRENT = P("docs/current-lifecycle.md")
B_SLICES = P("docs/c4-ii-b-implementation-slices.md")
PROFILE = P("docs/restore-interaction-and-validation-session.md")
PLAN = P("docs/implementation-plan.md")
DEPLOYMENT = P("docs/deployment.md")
PACKAGING = P("docs/packaging.md")
FOCUS = P("state/current-focus.md")
PROGRESS = P("state/progress.md")
HANDOFF = P("state/handoff.md")
CHANGE_REQUESTS = P("state/change-requests.md")
ADR16 = P("docs/decisions/0016-launcher-assisted-restore.md")
ADR17 = P("docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md")
ADR18 = P("docs/decisions/0018-launcher-restore-interaction-and-validation-session.md")
ADR19 = P("docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md")

ACTIVE = (README, PLAN, FOCUS, PROGRESS, HANDOFF, CHANGE_REQUESTS)
SUPPORTING = (CURRENT, B_SLICES, PROFILE, DEPLOYMENT, PACKAGING)

CORE = (
    "PR #192 — MERGED — D3 MACOS PACKAGE MVP",
    "PR #191 — MERGED — CR-012 / D3 AUTHORIZATION",
    "PR #190 — MERGED — C4-III PARTIAL VERIFICATION CHECKPOINT",
    "PR #189 — MERGED — C4-II-C LIFECYCLE CLOSURE AND C4-III AUTHORIZATION",
    "PR #188 — MERGED — C4-II-C EXACT-HEAD VERIFIED",
    "PR #187 — MERGED — C4-II-C AUTHORIZATION BASELINE",
    "PR #186 — MERGED — C4-II-B3 EXACT-HEAD VERIFIED",
    "PR #185 — MERGED — B3 AUTHORIZATION BASELINE",
    "PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED",
    "PR #183 — MERGED — B2 AUTHORIZATION BASELINE",
    "PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-C — DONE — MERGED AND EXACT-HEAD VERIFIED",
    # C4-III closes on both halves. The two PASS lines stay separately labelled
    # so neither can be read as standing in for the other.
    "C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED",
    "C4-III EXACT-HEAD VERIFICATION — PASS",
    "C4-III EXACT-PACKAGE VERIFICATION — PASS",
    "C4-III LIFECYCLE CLOSURE — COMPLETED BY THIS CHANGESET",
    "CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION",
    # Conservative and final. Built, not released.
    "D3 — macOS package MVP — IMPLEMENTED",
    # Closure is not an authorization event for anything downstream.
    "D4 — Update safety — NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE",
    "D5 — Remote install checklist — NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE",
    "Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED",
    "Product release readiness — NOT CLAIMED",
)

STALE = (
    "C4-II-C — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-C — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-C — PLANNED — NOT AUTHORIZED",
    "C4-III — PLANNED — NOT AUTHORIZED",
    "C4-III — AUTHORIZED NEXT — NOT IMPLEMENTED",
    # D3 is built. Built is neither verified-as-a-release nor released, so every
    # phrasing that upgrades it stays forbidden.
    "D3 — macOS package MVP — DONE",
    "D3 — macOS package MVP — CLOSED",
    "D3 — macOS package MVP — COMPLETE",
    "D3 — macOS package MVP — MERGED",
    "D3 — macOS package MVP — VERIFIED",
    "D3 — macOS package MVP — RELEASE READY",
    "D3 — macOS package MVP — EXACT-PACKAGE VERIFIED",
    "D3 — macOS package MVP — NOTARIZED",
    "D3 — macOS package MVP — SIGNED",
    "D3 — macOS package MVP — APP STORE READY",
    "D3 — macOS package MVP — UNIVERSAL",
    "D3 — DONE",
    "D3 — CLOSED",
    "D3 — COMPLETE",
    "D3 — VERIFIED",
    "D3 — RELEASE READY",
    # The package smoke proves the delivery layer. It is never the C4-III
    # exact-package Restore verifier, and must never be written up as one.
    "D3 package smoke — C4-III EXACT-PACKAGE VERIFICATION PASSED",
    "D3 SMOKE PASS — C4-III EXACT-PACKAGE VERIFICATION",
    "packaged artifact — VERIFIED",
    "packaged artifact — DONE",
    "PACKAGED ARTIFACT — AVAILABLE",
    "CR-012 — DONE",
    "CR-012 — CLOSED",
)

# Phrases that were true before D3 was built and are false now. They stay
# legitimate inside ADR 0019, which records the state at the time of the
# decision, so they are forbidden on the active surfaces only and this tuple is
# never scanned against the ADR or against the dated history journal entries.
SUPERSEDED_BY_D3 = (
    "D3 — macOS package MVP — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-III EXACT-PACKAGE VERIFICATION — BLOCKED BY PACKAGED ARTIFACT PREREQUISITE",
    "No package exists.",
    "no packaged product artifact exists",
    "scripts/package_macos.sh is a placeholder",
)

# Phrases that were true while C4-III was open and are false now that both
# halves have passed. Same rule as SUPERSEDED_BY_D3: forbidden on the active
# surfaces, preserved in ADR 0019 and in `docs/history/c4-iii-pre-closure/`,
# where they record what was accurate at the time rather than what is true now.
SUPERSEDED_BY_CLOSURE = (
    "C4-III — IN PROGRESS",
    "C4-III EXACT-PACKAGE VERIFICATION — NOT YET PASSED",
    "C4-III EXACT-PACKAGE VERIFICATION — BLOCKED",
    "C4-III LIFECYCLE CLOSURE — NOT COMPLETED",
    "C4-III LIFECYCLE CLOSURE — BLOCKED",
    "D3 — macOS package MVP — IMPLEMENTED — C4-III EXACT-PACKAGE VERIFICATION PENDING",
    "EXACT-PACKAGE VERIFICATION PENDING",
    "Restore — NOT IMPLEMENTED",
    "Restore remains NOT IMPLEMENTED",
    "Restore is NOT IMPLEMENTED",
    "Restore stays NOT IMPLEMENTED",
    "C4-III stays open",
    "C4-III must remain open",
    "C4-III cannot close",
)

# CR-012 authorizes roadmap D3 and stops there, and the C4-III closure widens
# nothing either. These phrases would push either one into D4, D5 or the wider
# release programme and are always false.
BROADENING = (
    "CR-012 authorizes signing",
    "CR-012 authorizes notarization",
    "CR-012 authorizes auto-update",
    "CR-012 authorizes App Store",
    "CR-012 authorizes a DMG",
    "CR-012 authorizes D4",
    "CR-012 authorizes D5",
    "CR-012 authorizes release readiness",
    "CR-012 authorizes Electron",
    "CR-012 authorizes Tauri",
    "CR-012 authorizes a desktop shell",
    "CR-012 authorizes a new Restore transport",
    "C4-III closure authorizes D4",
    "C4-III closure authorizes D5",
    "C4-III closure authorizes signing",
    "C4-III closure authorizes notarization",
    "C4-III closure authorizes auto-update",
    "C4-III closure authorizes App Store",
    "C4-III closure authorizes a DMG",
    "C4-III closure authorizes cloud sync",
    "C4-III closure authorizes release",
    "C4-III closure authorizes a new Restore transport",
    "closing C4-III authorizes",
    "D4 — AUTHORIZED BY CR-012",
    "D5 — AUTHORIZED BY CR-012",
    "D4 — AUTHORIZED BY C4-III",
    "D5 — AUTHORIZED BY C4-III",
    "D4 — Update safety — AUTHORIZED",
    "D5 — Remote install checklist — AUTHORIZED",
    "D4 is authorized",
    "D5 is authorized",
    "signing — AUTHORIZED",
    "notarization — AUTHORIZED",
    "auto-update — AUTHORIZED",
    "App Store — AUTHORIZED",
    "mandatory DMG — AUTHORIZED",
    "DMG — AUTHORIZED",
    "sandbox migration — AUTHORIZED",
    "cloud sync — AUTHORIZED",
    "cloud deployment — AUTHORIZED",
    "release-channel infrastructure — AUTHORIZED",
    "release-candidate certification — AUTHORIZED",
    "D4 update-safety implementation — AUTHORIZED",
    "D5 remote-install work — AUTHORIZED",
    "signing is authorized",
    "notarization is authorized",
    "auto-update is authorized",
    "App Store work is authorized",
)

# The exact-package PASS proves packaged Restore behavior. It is not a release
# gate, and the product is not releasable because a verification passed.
RELEASE_OVERCLAIM = (
    "Product release readiness — READY",
    "Product release readiness — CLAIMED",
    "Product release readiness — ACHIEVED",
    "release readiness — READY",
    "is release-ready",
    "now release-ready",
    "release-ready product",
    "release-ready build",
    "release-ready artifact",
    "exact-package verification proves release readiness",
    "exact-package PASS proves release readiness",
    "exact-package verification makes the product release-ready",
    "exact-package verification means the product is releasable",
    "C4-III closure proves release readiness",
    "C4-III closure makes the product release-ready",
    "the product is releasable",
    "release-candidate certification — PASS",
    "full release-candidate smoke — PASS",
)

# PR #190 recorded a correct INCONCLUSIVE — ENVIRONMENT classification. Neither
# CR-012, nor D3, nor the later exact-package PASS may be written up as though
# the verifier had misclassified that run.
RECLASSIFICATION = (
    "not a missing environment",
    "not an environment issue",
    "not an environment problem",
    "not an environment accident",
    "rather than a missing environment",
    "the recorded INCONCLUSIVE — ENVIRONMENT result was wrong",
    "the earlier INCONCLUSIVE was really a PASS",
    "reclassify the INCONCLUSIVE — ENVIRONMENT result",
)

# The two pre-acceptance runner attempts are runner faults. Recording either as
# a real product failure would invent a defect the product never had.
RUNNER_FAULT_MISCLASSIFICATION = (
    "the v1.1 FAIL — PRODUCT verdict was a real product failure",
    "C4-III exact-package verification found a product defect",
    "the hard-interruption probe found a product defect",
    "a Restore product defect was found",
    "a Restore product defect was fixed",
    "FAIL — PRODUCT — C4-III EXACT-PACKAGE",
)

# What the built package must keep being described as. Each phrase pins a
# property that, if it silently stopped being true, would turn D3 from
# "packaging the product" into "changing it" — the exact drift ADR 0019's stop
# conditions exist to catch.
D3_IMPLEMENTATION = (
    "make package-macos",
    "CosmeticWorkshopOS.app",
    # The self-contained runtime, and the reason it is a real interpreter.
    "python-build-standalone",
    "3.12.13",
    "SHA-256 pinned per architecture",
    "fail closed",
    # The two things the end user must never need.
    "the end user needs no Python",
    "without Node",
    # The preserved process architecture.
    "app.launcher_backend_entrypoint",
    "backend-liveness lock",
    "No protected closed Restore production file was modified",
    # The bounded frontend listener.
    "binds `127.0.0.1` only",
    "adds no CORS headers",
    "only `/api/*`",
    # What stays out.
    "No signing, notarization, DMG, installer, updater or release upload is added",
    # The gate this is not.
    "never that it runs",
)

# The bounded rule that replaced the previously blanket "no packaging
# implementation is authorized" statement.
CR012_BOUNDARY = (
    "CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it",
    "D4, D5 and later release/distribution work remain outside this authorization",
)

C4IIC_REVIEWED_HEAD = "1df21915fdcf4a708dc778a0e762d64830b5b880"
C4IIC_MERGE_MAIN = "6294f0044c792ced3ac56d213ea5333e33062f12"

# Exact merged `main` the external C4-III exact-head verifier ran against.
C4III_VERIFIED_MAIN = "81e8193596709b0c16d0ecad598458b3ea95fd9c"
C4III_RUNNER_SHA256 = "4c5c09081d2dc1db45ee556777039f4d9802f026d717a194c88c15d6894e5f3a"
C4III_RUNNER_VERSION = "c4-iii-restore-exact-head-v1"

# Exact published `main` the packaged runtime was built from, and the accepted
# external exact-package verifier that ran against it.
C4III_PACKAGE_MAIN = "0e1193264dc22979ca48e32a962aba916b6b520e"
C4III_PACKAGE_RUNNER_SHA256 = "2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694"
C4III_PACKAGE_RUNNER_VERSION = "c4-iii-restore-exact-package-v1.2"

C4III_EXACT_HEAD_GATES = (
    "lifecycle PASS",
    "focused_restore_pytest PASS",
    "frontend_npm_ci PASS",
    "frontend_build PASS",
    "frontend_restore_tests PASS",
    "destructive_e2e_current_and_older PASS",
    "PASS — C4-III EXACT-HEAD VERIFICATION PASSED",
)

# The historical outer gates of the exact-head run, preserved verbatim. The
# INCONCLUSIVE — ENVIRONMENT line belongs here permanently: it is the record of
# a run made before any packaged artifact existed.
C4III_OUTER_GATES = (
    "C4III EXACT-HEAD OUTER GATE: PASS",
    "C4III EXACT-PACKAGE OUTER GATE: INCONCLUSIVE — ENVIRONMENT",
    "C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE",
    "INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE",
    "BLOCKED — PACKAGE PREREQUISITE",
)

C4III_EXACT_PACKAGE_GATES = (
    "PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED",
    "PASS — FULL AUTOMATED SMOKE PASSED",
)

# The eight accepted packaged scenarios, reduced to the invariants that make the
# closure meaningful. Losing any of these turns the PASS into an unbacked claim.
C4III_EXACT_PACKAGE_EVIDENCE = (
    # current-schema and older-schema success
    "restore_completed",
    "migration to the current schema succeeded",
    "backend restarted successfully",
    # source immutability, both spellings the scenarios use
    "selected source SHA-256 unchanged",
    "selected source unchanged",
    # mandatory safety copy, retained on success and absent where nothing ran
    "`before_restore` safety copy retained",
    "no `before_restore` safety copy",
    # rejection before any destructive mutation
    "rejected before destructive execution",
    "stale retained source proof rejected",
    "restore_failed",
    # interruption, real crash, rollback. The crash must stay described as a
    # real durable one: a simulated phase would not be evidence.
    "source_staged",
    "aborted",
    "real durable crash phase",
    "replacement_intent",
    "rolled_back",
    "rollback_in_progress",
    # fail-closed refusal
    "replacement_committed",
    "recovery_blocked",
    "packaged exit code `3`",
    "ordinary startup refused",
    # autonomous cleanup
    "owned processes left: none",
    "owned ports still held: none",
)

# The pre-acceptance runner attempts, preserved as runner faults.
C4III_RUNNER_HISTORY = (
    "INCONCLUSIVE — RUNNER",
    "incorrect fixture `PYTHONPATH`",
    "UnboundLocalError",
    "invalid as product evidence",
)

PINNED_BLOBS = {
    P("launcher/restore/contracts.py"): "1b4adf345b2470e7c50987570e7848012aa15a95",
    P("launcher/restore/engine.py"): "91eb99d14aa3dc70e7d6fb0d63cb03c6af7d255f",
    P("launcher/restore/source_proof.py"): "2339ee118d7ae85f792cb550c5a8ea1cc77f716c",
    P("launcher/restore/staging.py"): "3126d5b1e68e764c135739fad71915912481c493",
    P("launcher/restore/validation_session.py"): "c8734ab60a576ecad53acd961571ddf2c14bdcf4",
    P("launcher/restore/validation_scratch.py"): "6703052865d6e1d05dbfac14ea37fc47409d4da7",
    P("launcher/restore/context.py"): "5795a6bd4339e77d60e27e282ad21d6df0f54364",
    P("launcher/restore/verification.py"): "1c3c25d0b0cf9b1e6ae4cb4931b56b3a9bf29772",
    P("launcher/restore/macos_picker.py"): "2bb2a048bb30866f9bf410da10a76537dbe09cdd",
    P("launcher/restore/browser_handoff.py"): "31aa42da893a551680091f9d7b97b3ef15422251",
    P("launcher/tests/test_restore_source_proof_binding.py"): "256ce4edc86d5060e056466bdeb35fb319269e33",
    P("launcher/restore/control_protocol.py"): "ab7240950d34228e0b81654a6c378c6cb77cb676",
    P("launcher/restore/control_session.py"): "aafa14b0a3ef126caddcb01e8429b5c26d80306c",
    P("launcher/restore/control_plane.py"): "b99a2ef2747cb4880465eb7b37e27cffbab18abc",
    P("launcher/restore/execution_coordinator.py"): "ea059358dd730969ccc8abcaaf6f7d4dfa5b3d51",
    P("launcher/runtime.py"): "7cca822944a335e03e196be6d9def8817267205e",
    P("frontend/src/main.ts"): "ea98a76638bddcb5a92b9ba31941508f8a816d42",
    P("frontend/src/app-navigation-routes.ts"): "cac0f380a6daf70cde21d8f5318c745e442e14e4",
    P("frontend/src/restore-control-contract.ts"): "15c50941998f38d441e1314f7227847bca11e3d0",
    P("frontend/src/restore-control-runtime.ts"): "3861dfd51ab3b146fb082133cf33a9cb24688b5c",
    P("frontend/src/restore-control-entry.ts"): "dfcec88d788d0e46dcc5cc9b53def89efb567ab6",
    P("frontend/src/restore-control-presentation.ts"): "5dc9977fcd258c4366ea9bbfed6f6055acc9749e",
}

HISTORY_BLOBS = {
    P("docs/history/implementation-plan/2026-08-06-pre-compaction.md"): "763a720ac7cc30c9eb870c5f24fa23aee75ea054",
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/current-focus.md"): "3fcd869815a7559cc46f278b37ee06eae683dd75",
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/progress.md"): "fcc0479d15cefa1672d01939418b9c37152559d7",
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/handoff.md"): "e47f8872415ada073d5518c5bd24dace20ff5fe4",
    P("docs/history/change-requests/2026-08-06-pre-compaction.md"): "85f284b0a08eba2a2f084672091cc9eedab261dc",
    P("docs/history/c4-ii-b3-pre-closure/README.md"): "5098bb7967d22678cdb2565d9757b672a66e46fb",
    P("docs/history/c4-ii-b3-pre-closure/current-lifecycle.md"): "163e5e12267f1f9fea406d1207b892bb1f12ca7f",
    P("docs/history/c4-ii-b3-pre-closure/c4-ii-b-implementation-slices.md"): "80d463c534f8a3bb8fec7662028378df43615780",
    P("docs/history/c4-ii-b3-pre-closure/deployment.md"): "4ece44f12b6736a03ecc03c6bf93671ccb278f21",
    P("docs/history/c4-ii-b3-pre-closure/implementation-plan.md"): "2e53832ef72e92cbbe0625657932ff536f29ec09",
    P("docs/history/c4-ii-b3-pre-closure/packaging.md"): "6981d45662506b491780479e1de1b9b39ecea45b",
    P("docs/history/c4-ii-b3-pre-closure/restore-interaction-and-validation-session.md"): "9f9933dbab683bc3d9cbc4a680a590665d7b9b02",
    P("docs/history/c4-ii-b3-pre-closure/change-requests.md"): "fb6cd6b452b3bf58384b7ad2d898b985d99ab670",
    P("docs/history/c4-ii-b3-pre-closure/current-focus.md"): "346c3e9c9b1fe1609827748a07d3a2ab46b2cdd2",
    P("docs/history/c4-ii-b3-pre-closure/handoff.md"): "d76d312b22aed6befad9b0cb82584917e2659fcd",
    P("docs/history/c4-ii-b3-pre-closure/progress.md"): "0a918ca9a8db5ba0a813ef6d69b6b7cac2466399",
    P("docs/history/c4-ii-c-pre-implementation/README.md"): "9812ab5f578d404e56b00fe8f15566c6a9efb705",
    P("docs/history/c4-ii-c-pre-implementation/current-lifecycle.md"): "2b07a616dbcef16335d9d16400f07c0734fc824f",
    P("docs/history/c4-ii-c-pre-implementation/c4-ii-b-implementation-slices.md"): "caf8285fc8d22eb5a24151cd4e0a1626c39e49f1",
    P("docs/history/c4-ii-c-pre-implementation/deployment.md"): "fb6c95ef945bbe4bfde57b051a34f7f205072f97",
    P("docs/history/c4-ii-c-pre-implementation/implementation-plan.md"): "d4402b7aece04d51104bc7a8de4295179196d8db",
    P("docs/history/c4-ii-c-pre-implementation/packaging.md"): "bcd241d876f0b24d196a9fd1ecedc3b3fdde83bb",
    P("docs/history/c4-ii-c-pre-implementation/restore-interaction-and-validation-session.md"): "0b98aa58952c09bec235450873945b10481255f7",
    P("docs/history/c4-ii-c-pre-implementation/change-requests.md"): "f6a6e5a13e9eeeaf9750cc301499aef295ff92ab",
    P("docs/history/c4-ii-c-pre-implementation/current-focus.md"): "28b27cbd284c8332c932e9da9489dee3ecbcd5bc",
    P("docs/history/c4-ii-c-pre-implementation/handoff.md"): "e43d3bcdb0c3c51bee8fc068e679f004a8b713c4",
    P("docs/history/c4-ii-c-pre-implementation/progress.md"): "47d6f92b770600de084c543a00495c7ae23f231e",
    P("docs/history/c4-ii-c-pre-closure/README.md"): "122bc86bae0313f5f82ceb5cd8ee402c489ac625",
    P("docs/history/c4-ii-c-pre-closure/current-lifecycle.md"): "460a44b0bad7c6a68c468a847ef2bf56541f96be",
    P("docs/history/c4-ii-c-pre-closure/c4-ii-b-implementation-slices.md"): "de64bc2cc5ddadc4d9b10cb2b9c8d8d8665cc798",
    P("docs/history/c4-ii-c-pre-closure/deployment.md"): "bd1db7af743a687a08336ab415e536e52b171d70",
    P("docs/history/c4-ii-c-pre-closure/implementation-plan.md"): "cf072337fc0ddc0a4b2493113c09b90b8fe44584",
    P("docs/history/c4-ii-c-pre-closure/packaging.md"): "ea635365069d878242fdd26de6c40d93ddbfc4cf",
    P("docs/history/c4-ii-c-pre-closure/restore-interaction-and-validation-session.md"): "3a6335c697ab49b580945a17bea8db092e7b5f59",
    P("docs/history/c4-ii-c-pre-closure/change-requests.md"): "cba10b001ad412279a621d8a3211847978fa63ec",
    P("docs/history/c4-ii-c-pre-closure/current-focus.md"): "ba706cd45ce2a4eb0ef34a30a2d0be86a3347d2e",
    P("docs/history/c4-ii-c-pre-closure/handoff.md"): "e01e06754d0fb5dde4060c4f00e9231636916afc",
    P("docs/history/c4-ii-c-pre-closure/progress.md"): "3075c538566752439c076edaf1c9315750c36542",
    P("docs/history/c4-iii-pre-partial-verification/README.md"): "9603547b782acbc66ff9f933e003c9ae1d9f0bf9",
    P("docs/history/c4-iii-pre-partial-verification/current-lifecycle.md"): "00e359342b8a146dedcbe4e1195255bf03a60658",
    P("docs/history/c4-iii-pre-partial-verification/c4-ii-b-implementation-slices.md"): "cb6849135105c97f84c613ba0a46a0e7e563fe1e",
    P("docs/history/c4-iii-pre-partial-verification/deployment.md"): "937cea437145589437dcb32bbb03ded76dab0bc1",
    P("docs/history/c4-iii-pre-partial-verification/implementation-plan.md"): "64f8cde79984ec670d6fd886a1bbafa13ff9093a",
    P("docs/history/c4-iii-pre-partial-verification/packaging.md"): "d4b016a5c4588f5cf4878817b186d7ccdd5d2120",
    P("docs/history/c4-iii-pre-partial-verification/restore-interaction-and-validation-session.md"): "c47f6886da25de7020ef5f3572e4fa48e1fa7ce8",
    P("docs/history/c4-iii-pre-partial-verification/change-requests.md"): "77df5f27b218b0d58b42b48afd3141ae569d2871",
    P("docs/history/c4-iii-pre-partial-verification/current-focus.md"): "c7932d5aa86fc6946d4dfa48ab58626cbe227963",
    P("docs/history/c4-iii-pre-partial-verification/handoff.md"): "f46c6f02913f326ca62f28b207a465af1d0e5d08",
    P("docs/history/c4-iii-pre-partial-verification/progress.md"): "8ac34a9ef1676039bd0174f30994ae85ee496add",
    # Pre-closure snapshots, byte-identical to published main
    # 0e1193264dc22979ca48e32a962aba916b6b520e.
    P("docs/history/c4-iii-pre-closure/README.md"): "3943271a4b0cb7de301708212438236612ff63a2",
    P("docs/history/c4-iii-pre-closure/current-lifecycle.md"): "870d582d27db1874ec7ed8b8bf00d846c95b2424",
    P("docs/history/c4-iii-pre-closure/c4-ii-b-implementation-slices.md"): "cd6dd3fc72a1a939f73ebeb4ac3f362bd870dbcc",
    P("docs/history/c4-iii-pre-closure/deployment.md"): "b2bebb9e4f614ecf5bec23af5320cf20d68eda8c",
    P("docs/history/c4-iii-pre-closure/implementation-plan.md"): "11102c48ac4afd16603b47aca8b34c99d07d9aff",
    P("docs/history/c4-iii-pre-closure/packaging.md"): "cedb4deeac0059148e1f425882e8e44ad298c50c",
    P("docs/history/c4-iii-pre-closure/restore-interaction-and-validation-session.md"): "3edf50a5d518ddea482dba81d2ee9199febe5fec",
    P("docs/history/c4-iii-pre-closure/change-requests.md"): "d7862c9cc5ce2b695c0d52d7ec807bb98a84ad52",
    P("docs/history/c4-iii-pre-closure/current-focus.md"): "307563a1944780f68ec38c2caa27c05153d27636",
    P("docs/history/c4-iii-pre-closure/handoff.md"): "b64bc5ba6959d633ca2b8c728a4c1743c6f329f8",
    P("docs/history/c4-iii-pre-closure/progress.md"): "85eb9e017056d98a9eb9bab75f9b0faaf21fc751",
}

ERRORS: list[str] = []

def fail(message: str) -> None:
    ERRORS.append(message)

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")
        return ""

def norm(value: str) -> str:
    return " ".join(value.split()).casefold()

def require(path: Path, markers: tuple[str, ...]) -> None:
    text = norm(read(path))
    for marker in markers:
        if norm(marker) not in text:
            fail(f"{path.relative_to(ROOT)} is missing marker: {marker!r}")

def forbid(path: Path, markers: tuple[str, ...]) -> None:
    text = norm(read(path))
    for marker in markers:
        if norm(marker) in text:
            fail(f"{path.relative_to(ROOT)} contains forbidden marker: {marker!r}")

def blob(path: Path) -> str:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        fail(f"missing pinned file: {path.relative_to(ROOT)}")
        return ""
    return sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def check_lifecycle_docs() -> None:
    for path in ACTIVE:
        require(path, CORE)
    # Superseded phrasing is rejected on the active surfaces only. ADR 0019 and
    # the dated history keep it, because there it is an accurate record of the
    # state at the time rather than a claim about the state now.
    for path in ACTIVE + SUPPORTING:
        forbid(path, SUPERSEDED_BY_D3)
        forbid(path, SUPERSEDED_BY_CLOSURE)
    require(CURRENT, CORE + C4III_EXACT_HEAD_GATES + C4III_OUTER_GATES
            + C4III_EXACT_PACKAGE_GATES + C4III_EXACT_PACKAGE_EVIDENCE
            + C4III_RUNNER_HISTORY + CR012_BOUNDARY + (
        C4IIC_REVIEWED_HEAD,
        C4IIC_MERGE_MAIN,
        C4III_VERIFIED_MAIN,
        C4III_RUNNER_SHA256,
        C4III_RUNNER_VERSION,
        C4III_PACKAGE_MAIN,
        C4III_PACKAGE_RUNNER_SHA256,
        C4III_PACKAGE_RUNNER_VERSION,
        "C4-II-C closure baseline",
        "C4-III exact-head verification baseline",
        "C4-III exact-package verification baseline",
        "C4-III lifecycle closure",
        "C4-III — Restore end-to-end verification and lifecycle closure",
        "current-schema Restore",
        "supported older-schema Restore",
        # the historical classification, preserved rather than reinterpreted
        "not a product failure",
        "not a runner failure",
        "not rewritten and not reclassified",
        # closure follows from the combination and from nothing else
        "only their combination closes the slice",
        "as a consequence of this lifecycle closure",
        "return code: 0",
        "CR-012 — accepted D3 macOS package MVP authorization",
        "D3 — implemented",
        "D3 did not run C4-III exact-package verification",
        "D3 did not by itself advance C4-III lifecycle closure",
        "The D3 Level-5 package smoke proves the package/runtime delivery layer",
        # the verifier stays outside the product repository
        "not committed to this repository",
    ))
    require(B_SLICES, CORE + (
        "CLOSED NORMATIVE IMPLEMENTATION PLAN",
        C4IIC_REVIEWED_HEAD,
        C4IIC_MERGE_MAIN,
        "Closed C4-II-C successor",
        C4III_VERIFIED_MAIN,
        C4III_PACKAGE_MAIN,
    ))
    require(PROFILE, CORE + (
        "Final-state truth",
        "authenticated final B2 snapshot remains authoritative",
        "C4-III authorization",
        C4III_PACKAGE_MAIN,
        C4III_PACKAGE_RUNNER_VERSION,
        "replacement_intent -> rolled_back",
    ))
    require(PLAN, CORE + C4III_EXACT_PACKAGE_GATES + (
        "C4-III — Restore end-to-end verification and lifecycle closure",
        "current-schema Restore",
        "supported older-schema Restore",
        "interruption",
        "rollback",
        "repeated launch",
        "source immutability",
        "safety-copy retention",
        "PASS / FAIL PRODUCT / INCONCLUSIVE RUNNER / INCONCLUSIVE ENVIRONMENT",
        C4III_VERIFIED_MAIN,
        C4III_RUNNER_SHA256,
        C4III_RUNNER_VERSION,
        C4III_PACKAGE_MAIN,
        C4III_PACKAGE_RUNNER_SHA256,
        C4III_PACKAGE_RUNNER_VERSION,
        "Recorded verification progress",
        "Both required halves are satisfied",
        "C4-III closes only on their combination",
    ))
    require(DEPLOYMENT, CORE + CR012_BOUNDARY + (
        "no deployment topology change",
        "does not authorize deployment topology, packaging or updater redesign",
        "when that prerequisite was unavailable",
        "changes **no deployment topology**",
        "no desktop application shell",
        # The packaged product adds exactly one listener and no new topology.
        "The only new listener is the local frontend one",
        # closure changed no topology either
        C4III_PACKAGE_MAIN,
        "Restore is verified and lifecycle-closed on the same topology it always had",
    ))
    require(PACKAGING, CORE + CR012_BOUNDARY + D3_IMPLEMENTATION
            + C4III_EXACT_PACKAGE_GATES + (
        "no packaging",
        "does not authorize packaging implementation or redesign",
        "release readiness remains not claimed",
        "Closed packaged-artifact prerequisite gap",
        "implement macOS packaging under C4-III",
        "relabel the exact-package result as PASS",
        "CR-012 — D3 macOS package MVP authorization",
        "0019-c4-iii-packaged-artifact-prerequisite.md",
        "CosmeticWorkshopOS-mac.zip",
        "No new desktop application shell is authorized",
        "never a real user database",
        "verification prerequisite and is never product release readiness",
        C4III_PACKAGE_MAIN,
        C4III_PACKAGE_RUNNER_SHA256,
        C4III_PACKAGE_RUNNER_VERSION,
        "never against a source-tree fallback",
        "It is not evidence of release readiness",
    ))
    for path in ACTIVE + SUPPORTING + (ADR19,):
        text = norm(read(path))
        for stale in STALE:
            if norm(stale) in text:
                fail(f"{path.relative_to(ROOT)} retains stale/premature lifecycle phrase: {stale!r}")
        for broadening in BROADENING:
            if norm(broadening) in text:
                fail(f"{path.relative_to(ROOT)} broadens CR-012 or the C4-III closure beyond its bounded scope: {broadening!r}")
        for overclaim in RELEASE_OVERCLAIM:
            if norm(overclaim) in text:
                fail(f"{path.relative_to(ROOT)} claims release readiness that no evidence supports: {overclaim!r}")
        for reclassification in RECLASSIFICATION:
            if norm(reclassification) in text:
                fail(
                    f"{path.relative_to(ROOT)} reclassifies the recorded "
                    f"INCONCLUSIVE — ENVIRONMENT verification result: {reclassification!r}"
                )
        for misclassification in RUNNER_FAULT_MISCLASSIFICATION:
            if norm(misclassification) in text:
                fail(
                    f"{path.relative_to(ROOT)} records a runner fault as a product "
                    f"defect: {misclassification!r}"
                )

def check_authority_and_history() -> None:
    require(ADR16, ("before_restore", "replacement_intent", "recovery_blocked", "selected source", "immutable"))
    require(ADR17, ("C4-III — end-to-end verification and lifecycle closure", "current-schema", "older-schema", "source immutability", "safety-copy retention"))
    require(ADR18, ("127.0.0.1", "/backups/restore", "sessionStorage", "command_seq", "compare descriptor/path SourceIdentity", "recompute and compare full SHA-256"))
    for path, expected in HISTORY_BLOBS.items():
        actual = blob(path)
        if actual and actual != expected:
            fail(f"protected history blob changed: {path.relative_to(ROOT)} expected {expected}, got {actual}")

def check_closed_boundaries() -> None:
    for path, expected in PINNED_BLOBS.items():
        actual = blob(path)
        if actual and actual != expected:
            fail(f"closed Restore boundary changed: {path.relative_to(ROOT)} expected {expected}, got {actual}")

def check_c4_iii_closure() -> None:
    require(PLAN, (
        "focused verification tests and test-only harnesses",
        "isolated external exact-head smoke runners",
        "no production behavior change unless separately authorized as a bounded defect fix",
        "No verification attempt revealed a product defect",
    ))
    require(FOCUS, C4III_EXACT_HEAD_GATES + C4III_EXACT_PACKAGE_GATES
            + C4III_EXACT_PACKAGE_EVIDENCE + C4III_RUNNER_HISTORY + (
        "C4-III Restore lifecycle closed",
        "Closure condition",
        C4III_VERIFIED_MAIN,
        C4III_RUNNER_VERSION,
        C4III_PACKAGE_MAIN,
        C4III_PACKAGE_RUNNER_SHA256,
        C4III_PACKAGE_RUNNER_VERSION,
        "packaging was not built inside C4-III",
        "Completed task — D3 macOS package MVP",
        "C4-III closes on the combination",
        "Exact-head evidence alone was never sufficient",
        "as a consequence of this closure only",
    ))
    require(HANDOFF, (
        "Authorized handoff",
        "current-schema success",
        "supported older-schema Restore",
        "`before_restore` safety copy retained",
        C4III_VERIFIED_MAIN,
        C4III_RUNNER_SHA256,
        C4III_RUNNER_VERSION,
        C4III_PACKAGE_MAIN,
        C4III_PACKAGE_RUNNER_SHA256,
        C4III_PACKAGE_RUNNER_VERSION,
        "PASS — C4-III EXACT-HEAD VERIFICATION PASSED",
        "PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED",
        "PASS — FULL AUTOMATED SMOKE PASSED",
        "INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE",
        "BLOCKED — PACKAGE PREREQUISITE",
        "packaging was never implemented inside C4-III to clear it",
        "Completed task — D3 macOS package MVP",
        "never reported as C4-III exact-package verification",
        "never counted as product defects",
        "closed by this changeset on the combination of both accepted halves",
        "inherits a **closed** Restore lifecycle",
        "Do not read this closure as a release gate",
        "owned processes left: none",
        "owned ports still held: none",
    ))
    require(PROGRESS, C4III_EXACT_PACKAGE_GATES + C4III_EXACT_PACKAGE_EVIDENCE
            + C4III_RUNNER_HISTORY + (
        C4III_PACKAGE_MAIN,
        C4III_PACKAGE_RUNNER_SHA256,
        C4III_PACKAGE_RUNNER_VERSION,
        "C4-III exact-package verification PASSED, Restore lifecycle closed",
        "Runner history is preserved truthfully and is not counted against the product",
        "is not rewritten, reclassified or upgraded by this closure",
        "documentation, state and lifecycle-checker only",
        "docs/history/c4-iii-pre-closure/",
    ))
    require(CHANGE_REQUESTS, CR012_BOUNDARY + (
        "No new Change Request is needed for verification-only",
        "STOP and open a separate decision/change request or bounded defect-fix PR",
        "Building the packaged artifact was **not** C4-III work",
        "CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification",
        "Status: **ACCEPTED**",
        "0019-c4-iii-packaged-artifact-prerequisite.md",
        C4III_PACKAGE_MAIN,
        C4III_PACKAGE_RUNNER_SHA256,
        C4III_PACKAGE_RUNNER_VERSION,
        "That closure authorizes no further stage",
    ))

def check_cr012_authorization() -> None:
    """CR-012 authorizes roadmap D3 and nothing wider, and reclassifies nothing."""
    require(ADR19, CR012_BOUNDARY + (
        "ADR 0019 — D3 macOS package MVP as the C4-III exact-package prerequisite",
        "`ACCEPTED`",
        "CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification",
        "D3 — macOS package MVP\n— AUTHORIZED NEXT — NOT IMPLEMENTED",
        "produce the packaged product artifact required for\nC4-III exact-package verification",
        "already defined in [`docs/roadmap.md`]",
        "does not invent a new packaging stage, does not redefine D3",
        "It contains no packaging implementation",
        "No packaged artifact exists",
        # the recorded verification result is preserved, not reinterpreted
        "The exact-package verifier correctly reported",
        "It does not reclassify or amend the previously recorded verification result",
        # preserved topology and Restore architecture
        "macOS packaged product",
        "existing local launcher",
        "local backend on 127.0.0.1",
        "built frontend",
        "ordinary system browser / SPA",
        "external user-data directory",
        "ADR 0016 remains authoritative",
        "ADR 0018 remains authoritative",
        # artifact contract
        "CosmeticWorkshopOS-mac.zip",
        "CosmeticWorkshopOS.app",
        "must not need Git, Python, Node.js, npm, Docker, GitHub, Codex, a terminal",
        "a real user database",
        "User data remains **outside** the application/package directory",
        # rejected shells / transports
        "Electron",
        "Tauri",
        "pywebview",
        "PyObjC application shell",
        "a second native product UI",
        "a WebView-based replacement for the existing browser UI",
        "a new Restore transport",
        "a new backend Restore endpoint",
        # release programme stays out
        "signing — NOT AUTHORIZED",
        "notarization — NOT AUTHORIZED",
        "mandatory DMG — NOT AUTHORIZED",
        "auto-update — NOT AUTHORIZED",
        "App Store — NOT AUTHORIZED",
        "sandbox migration — NOT AUTHORIZED",
        "D4 — Update safety — NOT AUTHORIZED BY CR-012",
        "D5 — Remote install checklist — NOT AUTHORIZED BY CR-012",
        "the roadmap's own D3 non-goals",
        # testability + stop conditions
        "Exact-package testability contract",
        "never against a source-tree fallback",
        "mandatory `before_restore` safety-copy semantics remain intact",
        "Stop conditions",
        "must **STOP** and require a new decision",
    ))
    # The bounded successor task is built, and `IMPLEMENTED` is its final status
    # on every active surface. It is never inflated beyond a built package.
    for path in ACTIVE + (CURRENT, DEPLOYMENT, PACKAGING):
        require(path, ("D3 — macOS package MVP — IMPLEMENTED",))
    # The old blanket claim is now globally false and must not be reinstated.
    for path in ACTIVE + SUPPORTING:
        forbid(path, ("no packaging implementation is authorized",))

def main() -> int:
    check_lifecycle_docs()
    check_authority_and_history()
    check_closed_boundaries()
    check_c4_iii_closure()
    check_cr012_authorization()
    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1
    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(ACTIVE)} compact active files.")
    print(f"Verified {len(HISTORY_BLOBS)} exact protected history Git blob identities.")
    print(f"Verified {len(PINNED_BLOBS)} exact closed B1/C4-I/B2/B3/C4-II-C/shell Git blob identities.")
    print("Verified PR #188 merged / C4-II-C exact-head closure baseline.")
    print("Verified PR #189 merged and C4-II-C is DONE — MERGED AND EXACT-HEAD VERIFIED.")
    print("Verified final C4-II-C presentation is pinned as a closed production boundary.")
    print("Verified C4-III is DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED, and that it")
    print("  closes only on the combination of both accepted independent halves.")
    print(f"Verified recorded C4-III exact-head baseline {C4III_VERIFIED_MAIN} / runner {C4III_RUNNER_VERSION}.")
    print(f"Verified recorded C4-III exact-package baseline {C4III_PACKAGE_MAIN} /")
    print(f"  runner {C4III_PACKAGE_RUNNER_VERSION} / SHA-256 {C4III_PACKAGE_RUNNER_SHA256}.")
    print("Verified the accepted exact-package evidence is carried, not merely asserted:")
    print("  current-schema and older-schema Restore, pre-mutation rejection, source immutability,")
    print("  mandatory before_restore retention, a real replacement_intent -> rolled_back recovery,")
    print("  interrupted rollback, recovery_blocked failing closed with packaged exit code 3,")
    print("  and zero owned processes or ports left behind.")
    print("Verified the earlier INCONCLUSIVE — ENVIRONMENT classification is preserved, not")
    print("  reinterpreted, and that the two pre-acceptance runner faults are preserved as")
    print("  runner faults rather than as product defects.")
    print("Verified CR-012 is ACCEPTED and ADR 0019 records the bounded D3 authorization.")
    print("Verified roadmap D3 — macOS package MVP is labelled IMPLEMENTED on every active")
    print("  surface, with no parallel stage, and never upgraded to DONE, CLOSED, VERIFIED,")
    print("  signed, notarized, App Store ready or release-ready.")
    print("Verified the built package is described as packaging the product, not changing it:")
    print("  bundled interpreter, unchanged launcher-managed backend entrypoint and liveness lock,")
    print("  loopback-only frontend listener, and no signing/notarization/DMG/updater work.")
    print("Verified neither CR-012 nor the C4-III closure authorizes D4, D5, signing,")
    print("  notarization, DMG, auto-update, App Store, sandbox migration, cloud sync or any")
    print("  desktop application shell.")
    print("Verified Restore is IMPLEMENTED only as a consequence of C4-III lifecycle closure,")
    print("  and that product release readiness is still not claimed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
