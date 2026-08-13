from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path.cwd()
TMP = Path(os.environ["RUNNER_TEMP"])
EVIDENCE = TMP / "pr200-ba577f11-evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
EXPECTED_HEAD = os.environ["EXPECTED_HEAD"]
EXPECTED_BASE = os.environ["EXPECTED_BASE"]
PR_BRANCH = os.environ["PR_BRANCH"]
VERIFIER_BRANCH = os.environ["VERIFIER_BRANCH"]
checks: dict[str, str] = {}


def run_logged(name: str, commands: list[list[str]], *, cwd: Path = ROOT, env=None) -> bool:
    log_path = EVIDENCE / f"{name}.log"
    ok = True
    with log_path.open("w", encoding="utf-8") as log:
        for command in commands:
            log.write(f"$ {' '.join(command)}\n")
            log.flush()
            result = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
            if result.returncode != 0:
                ok = False
                break
    checks[name] = "success" if ok else "failure"
    return ok


def output(*command: str) -> str:
    return subprocess.check_output(command, text=True).strip()


def preflight() -> bool:
    try:
        subprocess.run(["git", "fetch", "origin", "main", PR_BRANCH, VERIFIER_BRANCH], check=True)
        assert output("git", "rev-parse", "HEAD") == EXPECTED_HEAD
        assert output("git", "rev-parse", f"origin/{PR_BRANCH}") == EXPECTED_HEAD
        assert output("git", "rev-parse", "origin/main") == EXPECTED_BASE
        assert output("git", "status", "--porcelain") == ""
        subprocess.run(["git", "diff", "--check"], check=True)
        assert output("git", "rev-parse", "HEAD:launcher/runtime.py") == "7cca822944a335e03e196be6d9def8817267205e"
        assert output("git", "rev-parse", "HEAD:frontend/src/main.ts") == "ea98a76638bddcb5a92b9ba31941508f8a816d42"
        (EVIDENCE / "actual-head.txt").write_text(EXPECTED_HEAD + "\n", encoding="utf-8")
        changed = output("git", "diff", "--name-only", f"{EXPECTED_BASE}...{EXPECTED_HEAD}")
        (EVIDENCE / "changed-files.txt").write_text(changed + "\n", encoding="utf-8")
        checks["preflight"] = "success"
        return True
    except Exception as exc:
        (EVIDENCE / "preflight.log").write_text(repr(exc) + "\n", encoding="utf-8")
        checks["preflight"] = "failure"
        return False


def load_smoke() -> bool:
    try:
        data = subprocess.check_output(["git", "show", f"origin/{VERIFIER_BRANCH}:verification/pr200_d4c_package_smoke.py"])
        path = TMP / "pr200_d4c_package_smoke.py"
        path.write_bytes(data)
        subprocess.run([sys.executable, "-m", "py_compile", str(path)], check=True)
        assert output("git", "rev-parse", "HEAD") == EXPECTED_HEAD
        assert output("git", "diff", "--name-only") == ""
        checks["smoke_selfcheck"] = "success"
        return True
    except Exception as exc:
        (EVIDENCE / "smoke-selfcheck.log").write_text(repr(exc) + "\n", encoding="utf-8")
        checks["smoke_selfcheck"] = "failure"
        return False


def postflight() -> bool:
    try:
        for path in (ROOT / "frontend/node_modules", ROOT / "frontend/dist", ROOT / "frontend/dist-tests", ROOT / "backend/build"):
            if path.exists():
                shutil.rmtree(path)
        for path in (ROOT / "backend").glob("*.egg-info"):
            if path.is_dir():
                shutil.rmtree(path)
        subprocess.run(["git", "restore", f"--source={EXPECTED_HEAD}", "--worktree", "--", "frontend", "backend"], check=False)
        assert output("git", "rev-parse", "HEAD") == EXPECTED_HEAD
        subprocess.run(["git", "diff", "--check"], check=True)
        status = output("git", "status", "--porcelain")
        (EVIDENCE / "final-git-status.txt").write_text(status + ("\n" if status else ""), encoding="utf-8")
        assert status == ""
        checks["postflight"] = "success"
        return True
    except Exception as exc:
        (EVIDENCE / "postflight.log").write_text(repr(exc) + "\n", encoding="utf-8")
        checks["postflight"] = "failure"
        return False


preflight()
run_logged("dependencies", [[sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "./backend[test]"]])

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT / 'backend'}:{ROOT}"
run_logged("python_regression", [[sys.executable, "-m", "pytest", "backend/app/tests", "launcher/tests", "macos_package/tests", "-q"]], env=env)
run_logged("lifecycle", [[sys.executable, "-m", "py_compile", "scripts/check_documentation_lifecycle.py"], [sys.executable, "scripts/check_documentation_lifecycle.py"]])
run_logged("frontend", [["npm", "ci"], ["npm", "run", "test:settings-update-status"], ["npm", "run", "build"]], cwd=ROOT / "frontend")

package_env = os.environ.copy()
package_env["COSMETIC_WORKSHOP_BUILD_DIR"] = str(TMP / "pr200-build")
package_env["COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR"] = str(TMP / "pr200-dist")
package_ok = run_logged("package", [["bash", "scripts/package_macos.sh"]], env=package_env)
if package_ok:
    executable = TMP / "pr200-build/package/CosmeticWorkshopOS.app/Contents/MacOS/CosmeticWorkshopOS"
    archive = TMP / "pr200-dist/CosmeticWorkshopOS-mac.zip"
    if not (executable.is_file() and os.access(executable, os.X_OK) and archive.is_file()):
        checks["package"] = "failure"

if load_smoke():
    run_logged("exact_package_d4c_smoke", [[sys.executable, str(TMP / "pr200_d4c_package_smoke.py")]], env=env)
else:
    checks["exact_package_d4c_smoke"] = "failure"

postflight()

critical_env = ("preflight", "dependencies", "postflight")
product = ("python_regression", "lifecycle", "frontend", "package", "exact_package_d4c_smoke")
if any(checks.get(k) != "success" for k in critical_env):
    status = "environment_inconclusive"
elif checks.get("smoke_selfcheck") != "success":
    status = "runner_inconclusive"
elif any(checks.get(k) != "success" for k in product):
    status = "product_failed"
else:
    status = "passed"

payload = {"pr": 200, "expected_base": EXPECTED_BASE, "expected_head": EXPECTED_HEAD, "actual_head": output("git", "rev-parse", "HEAD"), "status": status, "checks": checks}
(EVIDENCE / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = ["# PR #200 D4-C exact-head verification", "", f"Expected head: `{EXPECTED_HEAD}`", f"Result: **{status}**", "", "| Check | Outcome |", "|---|---|"]
for key in ("preflight", "dependencies", "python_regression", "lifecycle", "frontend", "package", "smoke_selfcheck", "exact_package_d4c_smoke", "postflight"):
    lines.append(f"| {key} | {checks.get(key, 'missing')} |")
lines.append("")
if status == "passed":
    lines += ["PASS — FULL AUTOMATED SMOKE PASSED", "D4-C exact published head is verification-complete; lifecycle closure remains separate."]
elif status == "product_failed":
    lines += ["FAIL — PRODUCT REGRESSION CONFIRMED", "Do not merge."]
else:
    lines += ["INCONCLUSIVE — SMOKE EVIDENCE IS NOT RELIABLE", "Do not merge based on this run."]
report = "\n".join(lines) + "\n"
(EVIDENCE / "PR200_SMOKE_REPORT.md").write_text(report, encoding="utf-8")
summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a", encoding="utf-8") as f: f.write(report)
print(report)
raise SystemExit(0 if status == "passed" else 1)
