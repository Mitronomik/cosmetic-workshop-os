from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path.cwd()
TMP = Path(os.environ["RUNNER_TEMP"])
EXPECTED_HEAD = os.environ["EXPECTED_HEAD"]
EVIDENCE = TMP / "d4-d-final-evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)


def run_logged(command: list[str], log_name: str, *, env: dict[str, str] | None = None) -> None:
    with (EVIDENCE / log_name).open("w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}")


def git_show(ref: str, path: str, target: Path) -> None:
    target.write_bytes(subprocess.check_output(["git", "show", f"{ref}:{path}"]))


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


results: dict[str, object] = {
    "stage": "D4-D",
    "expected_head": EXPECTED_HEAD,
    "status": "running",
    "checks": {},
}
checks = results["checks"]
assert isinstance(checks, dict)

try:
    subprocess.run(
        ["git", "fetch", "origin", "main", "verification/pr200-ba577f11", "verification/pr198-final-dfae8216"],
        check=True,
    )
    assert git_output("rev-parse", "HEAD") == EXPECTED_HEAD
    assert git_output("rev-parse", "origin/main") == EXPECTED_HEAD
    assert git_output("status", "--porcelain") == ""
    subprocess.run(["git", "diff", "--check"], check=True)
    checks["exact_main_preflight"] = "success"

    # Reuse the accepted D4-C Level-5 orchestrator on current main. It owns the
    # full Python regression, lifecycle, frontend, real .app build, D4-C package
    # scenarios, and clean repository postflight.
    pr200_level5 = TMP / "d4d_pr200_level5.py"
    git_show("origin/verification/pr200-ba577f11", "verification/pr200_level5.py", pr200_level5)
    subprocess.run([sys.executable, "-m", "py_compile", str(pr200_level5)], check=True)
    level5_env = os.environ.copy()
    level5_env.update(
        {
            "EXPECTED_BASE": EXPECTED_HEAD,
            "EXPECTED_HEAD": EXPECTED_HEAD,
            "PR_BRANCH": "main",
            "VERIFIER_BRANCH": "verification/pr200-ba577f11",
        }
    )
    run_logged([sys.executable, str(pr200_level5)], "integrated-d4c-level5.log", env=level5_env)
    pr200_results_path = TMP / "pr200-ba577f11-evidence/results.json"
    pr200_results = json.loads(pr200_results_path.read_text(encoding="utf-8"))
    assert pr200_results["status"] == "passed"
    shutil.copy2(pr200_results_path, EVIDENCE / "integrated-d4c-results.json")
    checks["full_regression_lifecycle_frontend_package_d4c"] = "success"

    # The accepted D4-B package smoke expects its historical runner-owned package
    # path. Copy the exact current-main .app built above; this creates no second
    # product build and changes no application bytes.
    source_app = TMP / "pr200-build/package/CosmeticWorkshopOS.app"
    target_app = TMP / "pr198-final-build/package/CosmeticWorkshopOS.app"
    assert source_app.is_dir()
    target_app.parent.mkdir(parents=True, exist_ok=True)
    if target_app.exists():
        shutil.rmtree(target_app)
    shutil.copytree(source_app, target_app, symlinks=True)
    assert target_app.is_dir()
    checks["single_exact_package_reused_for_d4b"] = "success"

    # D4-B package scenarios cover: fresh/current, supported-older migration,
    # verified before_migration backup + UpdateLog, repeat launch, interrupted
    # source (no blind retry), interrupted target reconciliation, and newer-lineage
    # refusal before update metadata/backup/mutation.
    d4b_smoke = TMP / "d4d_d4b_package_smoke.py"
    git_show(
        "origin/verification/pr198-final-dfae8216",
        "verification/pr198_d4b_package_smoke.py",
        d4b_smoke,
    )
    subprocess.run([sys.executable, "-m", "py_compile", str(d4b_smoke)], check=True)
    smoke_env = os.environ.copy()
    smoke_env.update(
        {
            "EXPECTED_HEAD": EXPECTED_HEAD,
            "EVIDENCE_DIR": str(EVIDENCE),
            "PYTHONPATH": f"{ROOT / 'backend'}:{ROOT}",
        }
    )
    run_logged([sys.executable, str(d4b_smoke)], "d4b-exact-package-smoke.log", env=smoke_env)
    checks["d4b_exact_package_update_safety"] = "success"

    # D4 user-data/package topology remains local-first and external to the repo.
    assert TMP not in ROOT.parents and ROOT not in TMP.parents
    assert not source_app.is_relative_to(ROOT)
    for name in (
        "pr198-final-fresh-user-data",
        "pr198-final-older-user-data",
        "pr198-final-interrupted-source",
        "pr198-final-interrupted-target",
        "pr198-final-newer-user-data",
        "pr200-fresh",
        "pr200-older",
        "pr200-precommit-failure",
        "pr200-ambiguous",
    ):
        path = TMP / name
        if path.exists():
            assert not path.is_relative_to(ROOT)
    checks["external_isolated_user_data"] = "success"

    # Final exact-head integrity. The external verifier may leave only files under
    # RUNNER_TEMP; the tested repository must remain byte-clean.
    assert git_output("rev-parse", "HEAD") == EXPECTED_HEAD
    subprocess.run(["git", "diff", "--check"], check=True)
    assert git_output("status", "--porcelain") == ""
    checks["repository_postflight"] = "success"
    results["status"] = "passed"
except Exception as exc:
    results["status"] = "failed"
    results["error"] = repr(exc)

(EVIDENCE / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = [
    "# D4-D final exact-package verification",
    "",
    f"Exact main/head: `{EXPECTED_HEAD}`",
    f"Result: **{results['status']}**",
    "",
]
for key, value in checks.items():
    lines.append(f"- {key}: {value}")
lines.append("")
if results["status"] == "passed":
    lines.extend(
        [
            "D4 manual-update safety is verified across D4-A/B/C package semantics.",
            "PASS — FULL AUTOMATED SMOKE PASSED",
        ]
    )
else:
    lines.extend(["FAIL — D4 FINAL VERIFICATION DID NOT PASS", "Do not close D4."])
report = "\n".join(lines) + "\n"
(EVIDENCE / "D4D_FINAL_REPORT.md").write_text(report, encoding="utf-8")
print(report)
raise SystemExit(0 if results["status"] == "passed" else 1)
