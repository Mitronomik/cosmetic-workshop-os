from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

ROOT = Path.cwd()
TMP = Path(os.environ["RUNNER_TEMP"])
EVIDENCE = TMP / "pr201-be733a8e-evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
EXPECTED_BASE = os.environ["EXPECTED_BASE"]
EXPECTED_HEAD = os.environ["EXPECTED_HEAD"]
PR_BRANCH = os.environ["PR_BRANCH"]


def out(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def run_checker(*, quiet: bool = False) -> int:
    kwargs = {}
    if quiet:
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.STDOUT}
    return subprocess.run(["python3", "scripts/check_documentation_lifecycle.py"], **kwargs).returncode


def must_fail(label: str) -> None:
    if run_checker(quiet=True) == 0:
        raise AssertionError(f"negative lifecycle probe was not caught: {label}")


def restore(path: Path, content: str | bytes) -> None:
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


checks: dict[str, str] = {}
try:
    subprocess.run(["git", "fetch", "origin", "main", PR_BRANCH], check=True)
    assert out("git", "rev-parse", "HEAD") == EXPECTED_HEAD
    assert out("git", "rev-parse", "origin/main") == EXPECTED_BASE
    assert out("git", "rev-parse", f"origin/{PR_BRANCH}") == EXPECTED_HEAD
    assert out("git", "status", "--porcelain") == ""
    subprocess.run(["git", "diff", "--check"], check=True)
    checks["exact_head"] = "success"

    expected_active = {
        "README.md", "docs/current-lifecycle.md", "docs/deployment.md",
        "docs/implementation-plan.md", "docs/packaging.md", "docs/update-guide.md",
        "docs/history/README.md", "scripts/check_documentation_lifecycle.py",
        "state/change-requests.md", "state/current-focus.md", "state/handoff.md",
        "state/progress.md",
    }
    snapshot_names = {
        "ABOUT.md", "manifest.json", "README.md", "current-lifecycle.md",
        "implementation-plan.md", "packaging.md", "deployment.md", "update-guide.md",
        "current-focus.md", "progress.md", "handoff.md", "change-requests.md",
        "check_documentation_lifecycle.py", "history-README.md",
    }
    expected_files = expected_active | {
        f"docs/history/d4-c-pre-closure/{name}" for name in snapshot_names
    }
    actual_files = set(filter(None, out("git", "diff", "--name-only", f"{EXPECTED_BASE}...{EXPECTED_HEAD}").splitlines()))
    assert actual_files == expected_files
    assert len(actual_files) == 26
    for path in actual_files:
        assert not path.startswith(("backend/", "launcher/", "frontend/", "macos_package/", "migrations/"))
    checks["scope"] = "success"

    assert run_checker() == 0
    checks["lifecycle"] = "success"

    manifest = json.loads(Path("docs/history/d4-c-pre-closure/manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_commit"] == EXPECTED_BASE
    assert manifest["verified_pr_head"] == "ba577f1151e041c11019525862d9bb76eeb1404e"
    assert manifest["pr_head_verification_run"] == "31747841343"
    assert manifest["merged_head_verification_run"] == "31749503618"
    assert manifest["verified_head_to_merge_changed_files"] == 0
    checks["snapshot_evidence"] = "success"

    focus = Path("state/current-focus.md")
    focus_good = focus.read_text(encoding="utf-8")
    for old, new, label in (
        (
            "D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED",
            "D4-D — Exact-package update verification and D4 lifecycle closure — IMPLEMENTED",
            "D4-D premature implementation",
        ),
        (
            "D5 — Remote install checklist — NOT AUTHORIZED BY CR-013",
            "D5 — Remote install checklist — AUTHORIZED",
            "D5 authorization",
        ),
        ("Product release readiness — NOT CLAIMED", "Product release readiness — READY", "release readiness"),
        (
            "Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED",
            "Restore — IN PROGRESS",
            "Restore reopen",
        ),
        (
            "D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",
            "D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING",
            "D4-C reversion",
        ),
    ):
        assert old in focus_good
        focus.write_text(focus_good.replace(old, new, 1), encoding="utf-8")
        must_fail(label)
        restore(focus, focus_good)

    history = Path("docs/history/d4-c-pre-closure/README.md")
    history_good = history.read_bytes()
    history.write_bytes(history_good + b"\nverification-mutation\n")
    must_fail("D4-C history mutation")
    restore(history, history_good)

    runtime = Path("backend/app/services/update_safety.py")
    runtime_good = runtime.read_text(encoding="utf-8")
    assert "error.committed" in runtime_good
    runtime.write_text(runtime_good.replace("error.committed", "error.was_committed", 1), encoding="utf-8")
    must_fail("D4-C runtime seam mutation")
    restore(runtime, runtime_good)

    frontend = Path("frontend/src/settings-update-status.ts")
    frontend_good = frontend.read_text(encoding="utf-8")
    assert "fetch('/api/settings/status')" in frontend_good
    frontend.write_text(frontend_good.replace("fetch('/api/settings/status')", "fetch('/api/settings/status-broken')", 1), encoding="utf-8")
    must_fail("D4-C frontend seam mutation")
    restore(frontend, frontend_good)

    plan = Path("docs/implementation-plan.md")
    plan_good = plan.read_text(encoding="utf-8")
    assert "**AUTHORIZED NEXT — NOT IMPLEMENTED**." in plan_good
    plan.write_text(plan_good.replace("**AUTHORIZED NEXT — NOT IMPLEMENTED**.", "**PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED**.", 1), encoding="utf-8")
    must_fail("stale D4-D narrative")
    restore(plan, plan_good)

    current = Path("docs/current-lifecycle.md")
    current_good = current.read_text(encoding="utf-8")
    closed = "D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice."
    stale = "D4-A and D4-B remain closed. D4-C is implemented in the current branch; exact-head/exact-package verification and lifecycle closure remain pending, and D4-D remains unauthorized."
    assert closed in current_good
    current.write_text(current_good.replace(closed, stale, 1), encoding="utf-8")
    must_fail("stale D4-C narrative")
    restore(current, current_good)
    checks["negative_probes"] = "success"

    assert run_checker() == 0
    subprocess.run(["git", "diff", "--check"], check=True)
    assert out("git", "rev-parse", "HEAD") == EXPECTED_HEAD
    assert out("git", "status", "--porcelain") == ""
    checks["postflight"] = "success"
    status = "passed"
except Exception as exc:
    checks.setdefault("failure", repr(exc))
    status = "failed"

payload = {
    "pr": 201,
    "expected_base": EXPECTED_BASE,
    "expected_head": EXPECTED_HEAD,
    "actual_head": out("git", "rev-parse", "HEAD"),
    "status": status,
    "checks": checks,
}
(EVIDENCE / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = [
    "# PR #201 D4-C lifecycle closure verification", "",
    f"Expected head: `{EXPECTED_HEAD}`", f"Result: **{status}**", "",
]
for key, value in checks.items():
    lines.append(f"- {key}: {value}")
lines.append("")
if status == "passed":
    lines.append("PASS — D4-C LIFECYCLE CLOSURE VERIFIED")
else:
    lines.append("FAIL — DO NOT MERGE")
report = "\n".join(lines) + "\n"
(EVIDENCE / "PR201_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")
print(report)
raise SystemExit(0 if status == "passed" else 1)
