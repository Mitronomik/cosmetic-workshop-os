from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from typing import Any
from urllib import error, request

BASE = "e040011e54d1bc39461c9c01b6caaa568307c0c0"
HEAD = "d7f95141e5f41c7a806c3fafb71e942fe5892dd8"
PR_BRANCH = "fix/d5-native-macos-lifecycle"
BUNDLE_ID = "ru.cosmetic-workshop-os.app"
ALLOWED_FILES = {
    "macos_package/tests/packaging_fixtures.py",
    "macos_package/tests/test_macos_package_structure.py",
    "macos_package/tests/test_native_macos_lifecycle_source.py",
    "macos_package/verification.py",
    "scripts/macos/app_lifecycle.m",
    "scripts/package_macos.sh",
}

ROOT = Path.cwd().resolve()
TEMP = Path(os.environ["RUNNER_TEMP"]).resolve()
EVIDENCE = TEMP / "pr207-native-lifecycle-evidence"
BUILD = TEMP / "pr207-build"
DIST = TEMP / "pr207-dist"
CACHE = TEMP / "pr207-cache"
USER_DATA = TEMP / "pr207-user-data"
APP = BUILD / "package" / "CosmeticWorkshopOS.app"
ZIP = DIST / "CosmeticWorkshopOS-mac.zip"
MANIFEST = APP / "Contents" / "Resources" / "app" / "package-runtime.json"
DB = USER_DATA / "data" / "cosmetic_workshop.sqlite"

EVIDENCE.mkdir(parents=True, exist_ok=True)
report: dict[str, Any] = {
    "exact_base": BASE,
    "exact_head": HEAD,
    "status": "running",
    "classification": None,
    "checks": {},
    "artifact": {},
    "environment": {},
    "created": {},
    "d5_human_rehearsal": "REQUIRED AGAIN AFTER FIX MERGE",
}


class ProductFailure(RuntimeError):
    pass


class RunnerFailure(RuntimeError):
    pass


class EnvironmentFailure(RuntimeError):
    pass


def mark(name: str, value: str = "success") -> None:
    report["checks"][name] = value


def run(cmd: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None,
        check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout[-4000:]}")
    return proc


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def api(port: int, method: str, path: str, payload: Any | None = None,
        expected: int = 200, timeout: float = 4.0) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except OSError as exc:
        raise ProductFailure(f"{method} {path} failed: {exc}") from exc
    if status != expected:
        raise ProductFailure(f"{method} {path}: expected {expected}, got {status}: {body[:1000]}")
    return json.loads(body) if body else None


def wait_health(port: int, version: str, timeout: float = 50.0) -> None:
    deadline = time.monotonic() + timeout
    last = "not attempted"
    while time.monotonic() < deadline:
        try:
            payload = api(port, "GET", "/api/health", expected=200, timeout=1.0)
            if payload.get("status") == "ok" and str(payload.get("version")) == version:
                return
            last = repr(payload)
        except ProductFailure as exc:
            last = str(exc)
        time.sleep(0.25)
    raise ProductFailure(f"packaged backend did not become healthy: {last}")


def wait_frontend(port: int, timeout: float = 25.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with request.urlopen(f"http://127.0.0.1:{port}/", timeout=1.0) as response:
                body = response.read().decode("utf-8", errors="replace")
                if response.status == 200 and "Мастерская" in body:
                    return
        except OSError:
            pass
        time.sleep(0.25)
    raise ProductFailure("packaged frontend did not become reachable")


def app_processes() -> list[str]:
    prefix = str(APP)
    proc = run(["ps", "-axo", "pid=,command="], check=True)
    return [line.strip() for line in proc.stdout.splitlines() if prefix in line]


def wait_no_app_processes(timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not app_processes():
            return
        time.sleep(0.25)
    raise ProductFailure("application-level Quit left packaged app/runtime/backend processes alive: " + repr(app_processes()))


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def wait_ports_free(ports: tuple[int, ...], timeout: float = 12.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(port_is_free(port) for port in ports):
            return
        time.sleep(0.2)
    raise ProductFailure(f"ports were not released after application Quit: {ports}")


def classify_external_failure(output: str, context: str) -> Exception:
    low = output.casefold()
    network = (
        "could not resolve host", "failed to connect", "connection timed out",
        "network is unreachable", "temporary failure in name resolution",
        "не удалось загрузить runtime по https", "connection reset", "proxy error",
        "npm error code eai_again", "npm error code enetunreach",
    )
    if any(token in low for token in network):
        return EnvironmentFailure(f"{context} blocked by network/runner environment")
    return ProductFailure(f"{context} failed")


def cleanup_repo() -> None:
    for path in (ROOT / "backend" / "build", ROOT / "frontend" / "node_modules",
                 ROOT / "frontend" / "dist", ROOT / "frontend" / "dist-tests"):
        if path.exists():
            shutil.rmtree(path)
    for path in (ROOT / "backend").glob("*.egg-info"):
        if path.is_dir():
            shutil.rmtree(path)
    subprocess.run(["git", "restore", f"--source={HEAD}", "--worktree", "--", "backend", "frontend"], cwd=ROOT)


def preflight() -> None:
    run(["git", "fetch", "origin", "main", PR_BRANCH])
    if git("rev-parse", "HEAD") != HEAD:
        raise RunnerFailure("checkout is not detached at exact PR head")
    if git("rev-parse", "origin/main") != BASE:
        raise RunnerFailure("main moved from exact PR base")
    if git("rev-parse", f"origin/{PR_BRANCH}") != HEAD:
        raise RunnerFailure("PR branch moved from exact expected head")
    if git("status", "--porcelain"):
        raise RunnerFailure("repository dirty before verification")
    if int(git("rev-list", "--count", f"{BASE}..{HEAD}")) != 3:
        raise RunnerFailure("unexpected implementation commit count")
    changed = set(filter(None, git("diff", "--name-only", f"{BASE}...{HEAD}").splitlines()))
    if changed != ALLOWED_FILES:
        raise RunnerFailure(f"unexpected implementation scope: {sorted(changed)}")
    run(["git", "diff", "--check", f"{BASE}...{HEAD}"])
    mark("exact_head_and_scope")


def regression() -> None:
    install = run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "./backend[test]"], check=False, timeout=300)
    (EVIDENCE / "dependencies.log").write_text(install.stdout, encoding="utf-8")
    if install.returncode != 0:
        raise classify_external_failure(install.stdout, "dependency installation")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'backend'}:{ROOT}"
    tests = run([sys.executable, "-m", "pytest", "backend/app/tests", "launcher/tests", "macos_package/tests", "-q"], env=env, check=False, timeout=900)
    (EVIDENCE / "python-regression.log").write_text(tests.stdout, encoding="utf-8")
    if tests.returncode != 0:
        raise ProductFailure("Python regression failed")
    lifecycle = run([sys.executable, "scripts/check_documentation_lifecycle.py"], check=False)
    (EVIDENCE / "lifecycle.log").write_text(lifecycle.stdout, encoding="utf-8")
    if lifecycle.returncode != 0:
        raise ProductFailure("documentation lifecycle checker failed")
    mark("full_python_regression")
    mark("lifecycle_checker")


def build_package() -> dict[str, Any]:
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.rmtree(CACHE, ignore_errors=True)
    env = os.environ.copy()
    env.update({
        "COSMETIC_WORKSHOP_BUILD_DIR": str(BUILD),
        "COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR": str(DIST),
        "COSMETIC_WORKSHOP_BUILD_CACHE_DIR": str(CACHE),
    })
    proc = run(["bash", "scripts/package_macos.sh"], env=env, check=False, timeout=1200)
    (EVIDENCE / "package-build.log").write_text(proc.stdout, encoding="utf-8")
    if proc.returncode != 0:
        raise classify_external_failure(proc.stdout, "exact package build")
    if not APP.is_dir() or not ZIP.is_file() or not MANIFEST.is_file():
        raise ProductFailure("package build succeeded without expected app/zip/manifest")
    native = APP / "Contents" / "MacOS" / "CosmeticWorkshopOS"
    helper = APP / "Contents" / "MacOS" / "CosmeticWorkshopOSRuntime"
    if not native.is_file() or not helper.is_file():
        raise ProductFailure("native executable/runtime helper missing")
    file_info = run(["file", str(native)]).stdout
    if "Mach-O" not in file_info:
        raise ProductFailure("CFBundleExecutable is not Mach-O")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    artifact = {
        "filename": ZIP.name,
        "sha256": sha256(ZIP),
        "app_version": manifest["app_version"],
        "package_architecture": manifest["architecture"],
        "native_file": file_info.strip(),
    }
    report["artifact"] = artifact
    mark("exact_package_build_and_native_identity")
    return artifact


def set_launch_environment() -> None:
    shutil.rmtree(USER_DATA, ignore_errors=True)
    proc = run(["launchctl", "setenv", "COSMETIC_WORKSHOP_USER_DATA_DIR", str(USER_DATA)], check=False)
    if proc.returncode != 0:
        raise EnvironmentFailure("launchctl could not set isolated user-data environment")
    mark("isolated_launchservices_environment")


def unset_launch_environment() -> None:
    subprocess.run(["launchctl", "unsetenv", "COSMETIC_WORKSHOP_USER_DATA_DIR"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def launch_via_launchservices(frontend_port: int, backend_port: int, version: str) -> None:
    if app_processes():
        raise RunnerFailure("packaged app processes already exist before LaunchServices start")
    proc = run([
        "open", str(APP), "--args", "--no-browser",
        "--frontend-port", str(frontend_port), "--backend-port", str(backend_port),
    ], check=False)
    if proc.returncode != 0:
        raise ProductFailure(f"LaunchServices open failed: {proc.stdout}")
    wait_health(backend_port, version)
    wait_frontend(frontend_port)
    processes = app_processes()
    (EVIDENCE / "running-processes.txt").write_text("\n".join(processes) + "\n", encoding="utf-8")
    if len(processes) < 2:
        raise ProductFailure(f"expected native app plus packaged runtime/backend processes, got {processes}")
    if not DB.is_file():
        raise ProductFailure("LaunchServices app did not create DB in isolated external user-data directory")


def application_quit() -> None:
    proc = run(["osascript", "-e", f'tell application id "{BUNDLE_ID}" to quit'], check=False, timeout=15)
    (EVIDENCE / "application-quit.log").write_text(proc.stdout, encoding="utf-8")
    if proc.returncode != 0:
        raise ProductFailure(f"standard application Quit Apple event failed: {proc.stdout}")


def create_synthetic_data(backend_port: int) -> dict[str, Any]:
    backup = api(backend_port, "POST", "/api/backups", {"reason": "manual"}, expected=201)
    client = api(backend_port, "POST", "/api/clients", {
        "full_name": "D5 Lifecycle Test Client", "phone": "", "email": "", "address": "",
        "birthday": None, "skin_notes": "", "allergy_notes": "", "preference_notes": "",
        "contraindication_notes": "", "notes": "",
    }, expected=201)
    ingredient = api(backend_port, "POST", "/api/ingredients", {
        "name": "D5 Lifecycle Test Component", "category": "other", "default_unit": "g",
        "density_g_per_ml": None, "notes": "", "inci_name": "", "supplier_hint": "",
        "allergen_note": "", "usage_note": "",
    }, expected=201)
    recipe = api(backend_port, "POST", "/api/recipe-templates", {
        "name": "D5 Lifecycle Test Recipe", "product_type": "Test", "description": "", "notes": "",
    }, expected=201)
    created = {
        "backup_filename": backup["backup"]["filename"],
        "client_id": client["id"],
        "ingredient_id": ingredient["id"],
        "recipe_template_id": recipe["id"],
    }
    report["created"] = created
    return created


def verify_persistence(backend_port: int, created: dict[str, Any]) -> None:
    client = api(backend_port, "GET", f"/api/clients/{created['client_id']}")
    ingredient = api(backend_port, "GET", f"/api/ingredients/{created['ingredient_id']}")
    recipe = api(backend_port, "GET", f"/api/recipe-templates/{created['recipe_template_id']}")
    backups = api(backend_port, "GET", "/api/backups")
    if client["full_name"] != "D5 Lifecycle Test Client":
        raise ProductFailure("client missing after application-level Quit/restart")
    if ingredient["name"] != "D5 Lifecycle Test Component":
        raise ProductFailure("component missing after application-level Quit/restart")
    if recipe["name"] != "D5 Lifecycle Test Recipe":
        raise ProductFailure("recipe missing after application-level Quit/restart")
    if created["backup_filename"] not in {item["filename"] for item in backups["backups"]}:
        raise ProductFailure("backup missing after application-level Quit/restart")


def emergency_cleanup() -> None:
    # Evidence classification happens before this cleanup. These are only runner
    # hygiene fallbacks and never count as a successful product Quit.
    try:
        subprocess.run(["osascript", "-e", f'tell application id "{BUNDLE_ID}" to quit'], timeout=5,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    time.sleep(1)
    for line in app_processes():
        try:
            pid = int(line.split(None, 1)[0])
            os.kill(pid, 15)
        except Exception:
            pass


def main() -> int:
    frontend_port = free_port()
    backend_port = free_port()
    while backend_port == frontend_port:
        backend_port = free_port()
    report["environment"] = {
        "platform": run(["sw_vers", "-productVersion"]).stdout.strip(),
        "architecture": run(["uname", "-m"]).stdout.strip(),
        "frontend_port": frontend_port,
        "backend_port": backend_port,
    }
    product_conclusion_reached = False
    try:
        preflight()
        regression()
        artifact = build_package()
        cleanup_repo()
        if git("status", "--porcelain"):
            raise RunnerFailure("repository dirty after regression/package cleanup before lifecycle smoke")
        set_launch_environment()

        launch_via_launchservices(frontend_port, backend_port, artifact["app_version"])
        mark("launchservices_first_start")
        created = create_synthetic_data(backend_port)
        mark("synthetic_backup_client_component_recipe")

        application_quit()
        wait_no_app_processes()
        wait_ports_free((frontend_port, backend_port))
        mark("application_level_quit_and_cleanup")

        launch_via_launchservices(frontend_port, backend_port, artifact["app_version"])
        mark("launchservices_restart")
        verify_persistence(backend_port, created)
        mark("restart_persistence")

        application_quit()
        wait_no_app_processes()
        wait_ports_free((frontend_port, backend_port))
        mark("second_application_level_quit")

        if not DB.is_file() or not str(DB).startswith(str(USER_DATA)) or str(USER_DATA).startswith(str(ROOT)):
            raise ProductFailure("external user-data boundary is not preserved")
        mark("external_user_data_boundary")

        cleanup_repo()
        if git("rev-parse", "HEAD") != HEAD or git("status", "--porcelain"):
            raise RunnerFailure("repository postflight is not exact-head clean")
        mark("repository_postflight")
        report["status"] = "passed"
        report["classification"] = "PASS — FULL AUTOMATED SMOKE PASSED"
        product_conclusion_reached = True
    except RunnerFailure as exc:
        report["status"] = "inconclusive"
        report["classification"] = "INCONCLUSIVE — RUNNER"
        report["error"] = str(exc)
    except EnvironmentFailure as exc:
        report["status"] = "inconclusive"
        report["classification"] = "INCONCLUSIVE — ENVIRONMENT"
        report["error"] = str(exc)
    except ProductFailure as exc:
        report["status"] = "failed"
        report["classification"] = "FAIL — PRODUCT"
        report["error"] = str(exc)
        product_conclusion_reached = True
    except Exception as exc:
        report["status"] = "inconclusive"
        report["classification"] = "INCONCLUSIVE — RUNNER"
        report["error"] = repr(exc)
    finally:
        emergency_cleanup()
        unset_launch_environment()
        cleanup_repo()
        (EVIDENCE / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# PR #207 CR-015 native macOS lifecycle exact-package verification", "",
        f"Exact head: `{HEAD}`", f"Result: **{report['status']}**",
        f"Classification: `{report['classification']}`", "", "## Checks",
    ]
    for key, value in report["checks"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Artifact"])
    for key, value in report["artifact"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "", "## Boundary",
        "- Quit proof used macOS application Apple event after LaunchServices start; direct child SIGTERM was not accepted as the proof.",
        "- D5 human clean-Mac rehearsal must be repeated on the fixed exact package after merge.",
        "- Product release readiness remains NOT CLAIMED.", "",
        str(report["classification"]),
    ])
    report_text = "\n".join(lines) + "\n"
    (EVIDENCE / "PR207_NATIVE_LIFECYCLE_REPORT.md").write_text(report_text, encoding="utf-8")
    print(report_text)
    if report["status"] == "passed":
        return 0
    # Inconclusive and product failure both fail the workflow; classification in
    # evidence determines the next action.
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
