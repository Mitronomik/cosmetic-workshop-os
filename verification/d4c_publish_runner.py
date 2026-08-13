from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from textwrap import dedent

EXPECTED_BASE = "20d7190ebd91012a58993bf02934d6f4459332a0"
IMPLEMENTATION_BRANCH = "agent/d4-c-user-update-status-failure-ux"
V3_BRANCH = "maintenance/d4-c-implementation-builder-v3"


def run(*args: str, cwd: str | None = None) -> None:
    subprocess.run(list(args), cwd=cwd, check=True)


def output(*args: str) -> str:
    return subprocess.check_output(list(args), text=True).strip()


if output("git", "rev-parse", "HEAD") != EXPECTED_BASE:
    raise SystemExit("implementation branch is not on the exact D4-C base")
if output("git", "status", "--porcelain"):
    raise SystemExit("implementation branch is not clean")

run("git", "fetch", "origin", V3_BRANCH)
yaml = subprocess.check_output(
    ["git", "show", f"origin/{V3_BRANCH}:.github/workflows/build-d4-c-implementation-v3.yml"],
    text=True,
)
tail = yaml[yaml.index("      - name: Apply Restore-safe bounded D4-C transform\n"):]
match = re.search(r"python3 - <<'PY'\n(?P<body>.*?)^\s+PY\s*$", tail, re.MULTILINE | re.DOTALL)
if not match:
    raise SystemExit("cannot locate the reviewed v3 transform")
exec(compile(dedent(match.group("body")), "<d4-c-v3-transform>", "exec"), {"__name__": "__main__"})

if output("git", "hash-object", "launcher/runtime.py") != "7cca822944a335e03e196be6d9def8817267205e":
    raise SystemExit("protected launcher/runtime.py changed")
if output("git", "hash-object", "frontend/src/main.ts") != "ea98a76638bddcb5a92b9ba31941508f8a816d42":
    raise SystemExit("protected frontend/src/main.ts changed")

run("python", "-m", "pip", "install", "--disable-pip-version-check", "./backend[test]")
env = os.environ.copy()
env["PYTHONPATH"] = f"{Path.cwd() / 'backend'}:{Path.cwd()}"
subprocess.run(
    [
        "python", "-m", "pytest", "-q",
        "backend/app/tests/test_d4_c_update_status.py",
        "backend/app/tests/test_settings.py",
        "backend/app/tests/test_settings_api.py",
        "macos_package/tests/test_d4_c_update_failure_alerts.py",
        "macos_package/tests/test_macos_package_entrypoint.py",
    ],
    check=True,
    env=env,
)
run("npm", "ci", cwd="frontend")
run("npm", "run", "test:settings-update-status", cwd="frontend")
run("npm", "run", "build", cwd="frontend")
run("python", "scripts/check_documentation_lifecycle.py")
run("git", "diff", "--check")

expected = sorted(
    [
        "backend/app/schemas/settings.py",
        "backend/app/services/settings.py",
        "backend/app/services/update_safety.py",
        "backend/app/tests/test_d4_c_update_status.py",
        "frontend/package.json",
        "frontend/src/settings-tax-bindings.ts",
        "frontend/src/settings-update-status.ts",
        "frontend/test/settings-update-status.test.mjs",
        "frontend/tsconfig.test.settings-update-status.json",
        "macos_package/entrypoint.py",
        "macos_package/tests/test_d4_c_update_failure_alerts.py",
        "macos_package/user_alert.py",
    ]
)
actual = sorted(filter(None, subprocess.check_output(["git", "diff", "--name-only"], text=True).splitlines()))
print("=== D4-C ACTUAL SCOPE ===")
print("\n".join(actual))
if actual != expected:
    raise SystemExit(f"D4-C scope mismatch\nexpected={expected!r}\nactual={actual!r}")

run("git", "add", *expected)
run("git", "diff", "--cached", "--check")
run("git", "config", "user.name", "D4-C implementation builder")
run("git", "config", "user.email", "actions@users.noreply.github.com")
run("git", "commit", "-m", "D4-C add user-facing update status and packaged failure UX")
run("git", "push", "origin", f"HEAD:{IMPLEMENTATION_BRANCH}")
