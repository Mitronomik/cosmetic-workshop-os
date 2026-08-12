#!/usr/bin/env python3
"""Guard merged C4-II-C closure and the bounded C4-III verification authorization."""

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

ACTIVE = (README, PLAN, FOCUS, PROGRESS, HANDOFF, CHANGE_REQUESTS)
SUPPORTING = (CURRENT, B_SLICES, PROFILE, DEPLOYMENT, PACKAGING)

CORE = (
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
    "C4-III — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

STALE = (
    "C4-II-C — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-C — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-C — PLANNED — NOT AUTHORIZED",
    "C4-III — PLANNED — NOT AUTHORIZED",
    "C4-III — IN PROGRESS",
    "C4-III — DONE",
    "Restore — IMPLEMENTED",
    "Product release readiness — READY",
)

C4IIC_REVIEWED_HEAD = "1df21915fdcf4a708dc778a0e762d64830b5b880"
C4IIC_MERGE_MAIN = "6294f0044c792ced3ac56d213ea5333e33062f12"

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
    require(CURRENT, CORE + (
        C4IIC_REVIEWED_HEAD,
        C4IIC_MERGE_MAIN,
        "C4-II-C closure baseline",
        "C4-III — Restore end-to-end verification and lifecycle closure",
        "current-schema Restore",
        "supported older-schema Restore",
    ))
    require(B_SLICES, CORE + (
        "CLOSED NORMATIVE IMPLEMENTATION PLAN",
        C4IIC_REVIEWED_HEAD,
        C4IIC_MERGE_MAIN,
        "Closed C4-II-C successor",
    ))
    require(PROFILE, CORE + (
        "Final-state truth",
        "authenticated final B2 snapshot remains authoritative",
        "C4-III authorization",
    ))
    require(PLAN, CORE + (
        "C4-III — Restore end-to-end verification and lifecycle closure",
        "current-schema Restore",
        "supported older-schema Restore",
        "interruption",
        "rollback",
        "repeated launch",
        "source immutability",
        "safety-copy retention",
        "PASS / FAIL PRODUCT / INCONCLUSIVE RUNNER / INCONCLUSIVE ENVIRONMENT",
    ))
    require(DEPLOYMENT, CORE + (
        "no deployment topology change",
        "does not authorize deployment topology, packaging or updater redesign",
    ))
    require(PACKAGING, CORE + (
        "no packaging",
        "does not authorize packaging implementation or redesign",
        "release readiness remains not claimed",
    ))
    for path in ACTIVE + SUPPORTING:
        text = norm(read(path))
        for stale in STALE:
            if norm(stale) in text:
                fail(f"{path.relative_to(ROOT)} retains stale/premature lifecycle phrase: {stale!r}")

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

def check_c4_iii_authorization() -> None:
    require(PLAN, (
        "focused verification tests and test-only harnesses",
        "isolated external exact-head smoke runners",
        "no production behavior change unless separately authorized as a bounded defect fix",
        "If verification reveals a product defect",
    ))
    require(FOCUS, (
        "C4-III Restore end-to-end verification",
        "only authorized next Restore slice",
        "Any product defect requires a separate bounded fix PR",
    ))
    require(HANDOFF, (
        "Authorized handoff",
        "current-schema success",
        "supported older-schema Restore",
        "verified `before_restore` safety-copy retention",
    ))
    require(CHANGE_REQUESTS, (
        "No new Change Request is needed for verification-only",
        "STOP and open a separate decision/change request or bounded defect-fix PR",
    ))

def main() -> int:
    check_lifecycle_docs()
    check_authority_and_history()
    check_closed_boundaries()
    check_c4_iii_authorization()
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
    print("Verified C4-II-C is DONE — MERGED AND EXACT-HEAD VERIFIED.")
    print("Verified final C4-II-C presentation is pinned as a closed production boundary.")
    print("Verified C4-III is AUTHORIZED NEXT — NOT IMPLEMENTED and remains verification/lifecycle only.")
    print("Verified Restore remains NOT IMPLEMENTED and product release readiness is not claimed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
