from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path.cwd()
EXPECTED_BASE = os.environ["EXPECTED_BASE"]
EXPECTED_HEAD = os.environ["EXPECTED_HEAD"]
PR_BRANCH = os.environ["PR_BRANCH"]
EVIDENCE = Path(os.environ["EVIDENCE_DIR"])
EVIDENCE.mkdir(parents=True, exist_ok=True)

ACTIVE = {
    "README.md",
    "docs/AGENTS.md",
    "docs/current-lifecycle.md",
    "docs/decisions/0021-d5-remote-install-rehearsal-contract.md",
    "docs/decisions/AGENTS.md",
    "docs/deployment.md",
    "docs/history/README.md",
    "docs/implementation-plan.md",
    "docs/packaging.md",
    "docs/remote-install-checklist.md",
    "docs/update-guide.md",
    "docs/user-install.md",
    "scripts/check_documentation_lifecycle.py",
    "state/change-requests.md",
    "state/current-focus.md",
    "state/handoff.md",
    "state/progress.md",
}
SNAPSHOT = {
    "ABOUT.md", "manifest.json", "README.md", "current-lifecycle.md",
    "implementation-plan.md", "packaging.md", "deployment.md", "update-guide.md",
    "user-install.md", "remote-install-checklist.md", "docs-AGENTS.md",
    "decisions-AGENTS.md", "current-focus.md", "progress.md", "handoff.md",
    "change-requests.md", "check_documentation_lifecycle.py", "history-README.md",
}
EXPECTED_FILES = ACTIVE | {f"docs/history/d5-pre-decision/{name}" for name in SNAPSHOT}


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, check=True, **kwargs)


def must_fail(label: str) -> None:
    proc = subprocess.run(
        ["python3", "scripts/check_documentation_lifecycle.py"],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode == 0:
        raise SystemExit(f"negative probe not caught: {label}")


run(["git", "fetch", "origin", "main", PR_BRANCH])
head = run(["git", "rev-parse", "HEAD"], capture_output=True).stdout.strip()
main = run(["git", "rev-parse", "origin/main"], capture_output=True).stdout.strip()
branch = run(["git", "rev-parse", f"origin/{PR_BRANCH}"], capture_output=True).stdout.strip()
if head != EXPECTED_HEAD or branch != EXPECTED_HEAD or main != EXPECTED_BASE:
    raise SystemExit(f"exact identity mismatch: head={head} branch={branch} main={main}")

changed = set(run(["git", "diff", "--name-only", EXPECTED_BASE, EXPECTED_HEAD], capture_output=True).stdout.splitlines())
if changed != EXPECTED_FILES or len(changed) != 35:
    raise SystemExit(f"scope mismatch missing={sorted(EXPECTED_FILES-changed)} extra={sorted(changed-EXPECTED_FILES)} count={len(changed)}")
for path in changed:
    if path.startswith(("backend/", "frontend/", "launcher/", "macos_package/", "migrations/")):
        raise SystemExit(f"runtime scope leak: {path}")

run(["python3", "-m", "py_compile", "scripts/check_documentation_lifecycle.py"])
run(["python3", "scripts/check_documentation_lifecycle.py"])
run(["git", "diff", "--check", EXPECTED_BASE, EXPECTED_HEAD])

adr = Path("docs/decisions/0021-d5-remote-install-rehearsal-contract.md").read_text(encoding="utf-8")
required = (
    "documentation + exact-package assisted-install rehearsal stage",
    "clean Mac or clean macOS user profile",
    "PASS — D5 REMOTE INSTALL REHEARSAL PASSED",
    "INCONCLUSIVE — RUNNER",
    "INCONCLUSIVE — ENVIRONMENT",
    "Finder",
    "System Settings",
    "xattr",
    "spctl",
    "Signing and notarization are not silently authorized",
    "A D5 PASS is bounded to the exact tested artifact and environment evidence",
    "Only D5 is authorized next",
)
for phrase in required:
    if phrase.casefold() not in adr.casefold():
        raise SystemExit(f"ADR 0021 missing: {phrase}")

manifest_path = Path("docs/history/d5-pre-decision/manifest.json")
payload = json.loads(manifest_path.read_text(encoding="utf-8"))
if payload.get("source_commit") != EXPECTED_BASE:
    raise SystemExit("D5 pre-decision source commit mismatch")
for name, expected_blob in payload["files"].items():
    actual = run(["git", "hash-object", f"docs/history/d5-pre-decision/{name}"], capture_output=True).stdout.strip()
    if actual != expected_blob:
        raise SystemExit(f"snapshot blob mismatch: {name}")

# Lifecycle/release/Restore negative probes.
focus = Path("state/current-focus.md")
focus_good = focus.read_text(encoding="utf-8")
for old, new in (
    ("D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED", "D5 — Remote install checklist — DONE"),
    ("D5 verification — NOT STARTED", "D5 verification — PASSED"),
    ("PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014", "PHASE 12 — MVP release preparation — AUTHORIZED"),
    ("Product release readiness — NOT CLAIMED", "Product release readiness — READY"),
    ("Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED", "Restore — IN PROGRESS"),
):
    if old not in focus_good:
        raise SystemExit(f"negative probe source missing: {old}")
    focus.write_text(focus_good.replace(old, new, 1), encoding="utf-8")
    must_fail(new)
    focus.write_text(focus_good, encoding="utf-8")

focus.write_text(focus_good + "\nsigning — AUTHORIZED\n", encoding="utf-8")
must_fail("signing")
focus.write_text(focus_good, encoding="utf-8")

remote = Path("docs/remote-install-checklist.md")
remote_good = remote.read_text(encoding="utf-8")
marker = "DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED"
if marker not in remote_good:
    raise SystemExit("remote draft marker missing")
remote.write_text(remote_good.replace(marker, "VERIFIED", 1), encoding="utf-8")
must_fail("premature checklist verified")
remote.write_text(remote_good, encoding="utf-8")

history = Path("docs/history/d5-pre-decision/README.md")
history_good = history.read_bytes()
history.write_bytes(history_good + b"\nmutation-probe\n")
must_fail("snapshot mutation")
history.write_bytes(history_good)

run(["python3", "scripts/check_documentation_lifecycle.py"])
if run(["git", "status", "--porcelain"], capture_output=True).stdout.strip():
    raise SystemExit("repository postflight dirty")

report = f"""# PR #204 CR-014 D5 decision verification

Exact head: `{EXPECTED_HEAD}`
Result: **passed**

- exact_head: success
- decision_scope_35_files: success
- lifecycle_checker: success
- d5_predecision_snapshot: success
- adr0021_contract: success
- negative_probes: success
- runtime_scope_leak: none
- postflight: success

PASS — CR-014 D5 DECISION VERIFIED
"""
(EVIDENCE / "report.md").write_text(report, encoding="utf-8")
(EVIDENCE / "summary.json").write_text(json.dumps({
    "expected_base": EXPECTED_BASE,
    "expected_head": EXPECTED_HEAD,
    "changed_files": len(changed),
    "status": "passed",
}, indent=2) + "\n", encoding="utf-8")
print(report)
