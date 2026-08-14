from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from typing import Any
from urllib import error, request

BASE = "c91e62930915da357a2f9c74b9a054fe98e9df14"
HEAD = "da01c1f879cbf3af1efa000252520cd9ef9c38b4"
PR_BRANCH = "docs/d5-remote-install-rehearsal"
ALLOWED_FILES = {
    "README.md",
    "docs/backup-and-restore.md",
    "docs/current-lifecycle.md",
    "docs/deployment.md",
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
FORBIDDEN_PREFIXES = ("backend/", "frontend/", "launcher/", "macos_package/", "migrations/")

ROOT = Path.cwd().resolve()
TEMP = Path(os.environ.get("RUNNER_TEMP", "/tmp")).resolve()
EVIDENCE = Path(os.environ.get("EVIDENCE_DIR", TEMP / "pr205-d5-automated-evidence")).resolve()
BUILD_DIR = Path(os.environ.get("COSMETIC_WORKSHOP_BUILD_DIR", TEMP / "d5-build")).resolve()
DIST_DIR = Path(os.environ.get("COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR", TEMP / "d5-dist")).resolve()
USER_DATA = Path(os.environ.get("COSMETIC_WORKSHOP_USER_DATA_DIR", TEMP / "d5-user-data")).resolve()
APP = BUILD_DIR / "package" / "CosmeticWorkshopOS.app"
ZIP = DIST_DIR / "CosmeticWorkshopOS-mac.zip"
EXECUTABLE = APP / "Contents" / "MacOS" / "CosmeticWorkshopOS"
MANIFEST = APP / "Contents" / "Resources" / "app" / "package-runtime.json"

report: dict[str, Any] = {
    "exact_head": HEAD,
    "exact_base": BASE,
    "result": None,
    "classification": None,
    "checks": {},
    "artifact": {},
    "environment": {},
    "created": {},
    "human_layer": "REQUIRED — NOT EXECUTED BY AUTOMATION",
    "d5_lifecycle_closure": "NOT COMPLETED",
}


class ProductFailure(RuntimeError):
    pass


class RunnerFailure(RuntimeError):
    pass


class EnvironmentFailure(RuntimeError):
    pass


def mark(name: str, value: Any = "success") -> None:
    report["checks"][name] = value


def run(cmd: list[str], *, env: dict[str, str] | None = None, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if check and proc.returncode != 0:
        raise RunnerFailure(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout[-12000:]}")
    return proc


def git(*args: str) -> str:
    return run(["git", *args]).stdout.strip()


def ensure_external(path: Path, *, label: str) -> None:
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise RunnerFailure(f"{label} unexpectedly lives inside repository: {resolved}")
    if APP.exists():
        app_resolved = APP.resolve()
        if resolved == app_resolved or app_resolved in resolved.parents:
            raise RunnerFailure(f"{label} unexpectedly lives inside app package: {resolved}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def api(port: int, method: str, path: str, payload: Any | None = None, *, expected: int = 200, timeout: float = 5.0) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = request.Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ProductFailure(f"{method} {path} returned HTTP {exc.code}, expected {expected}: {body}") from exc
    except (error.URLError, TimeoutError, ConnectionError) as exc:
        raise ProductFailure(f"{method} {path} could not reach packaged backend: {exc}") from exc
    if status != expected:
        raise ProductFailure(f"{method} {path} returned HTTP {status}, expected {expected}: {body}")
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ProductFailure(f"{method} {path} returned non-JSON body: {body[:500]}") from exc


def wait_health(port: int, expected_version: str, process: subprocess.Popen[str], *, timeout: float = 45.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: str | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ProductFailure(f"packaged app exited before health became ready: exit={process.returncode}")
        try:
            payload = api(port, "GET", "/api/health", expected=200, timeout=1.0)
            if payload.get("status") != "ok":
                last = f"health status={payload!r}"
            elif str(payload.get("version")) != expected_version:
                raise ProductFailure(f"health version {payload.get('version')!r} != package version {expected_version!r}")
            else:
                return payload
        except ProductFailure as exc:
            last = str(exc)
        time.sleep(0.25)
    raise ProductFailure(f"packaged backend did not become healthy: {last}")


def wait_frontend(port: int, process: subprocess.Popen[str], *, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ProductFailure(f"packaged app exited before frontend became ready: exit={process.returncode}")
        try:
            with request.urlopen(f"http://127.0.0.1:{port}/", timeout=1.0) as response:
                body = response.read().decode("utf-8", errors="replace")
                if response.status == 200 and ("Мастерская" in body or "root" in body.lower()):
                    return
        except Exception:
            pass
        time.sleep(0.25)
    raise ProductFailure("packaged frontend did not become reachable")


def start_app(frontend_port: int, backend_port: int, log_name: str) -> tuple[subprocess.Popen[str], Any]:
    log_path = EVIDENCE / log_name
    handle = log_path.open("w", encoding="utf-8")
    env = os.environ.copy()
    env["COSMETIC_WORKSHOP_USER_DATA_DIR"] = str(USER_DATA)
    process = subprocess.Popen(
        [str(EXECUTABLE), "--no-browser", "--frontend-port", str(frontend_port), "--backend-port", str(backend_port)],
        cwd=TEMP,
        env=env,
        text=True,
        stdout=handle,
        stderr=subprocess.STDOUT,
    )
    return process, handle


def stop_app(process: subprocess.Popen[str], handle: Any, *, label: str) -> None:
    try:
        if process.poll() is None:
            process.terminate()  # same SIGTERM path the packaged entrypoint documents for Dock/Finder Quit
            try:
                code = process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                raise ProductFailure(f"{label}: packaged app did not stop after SIGTERM")
        else:
            code = int(process.returncode or 0)
        if code != 0:
            raise ProductFailure(f"{label}: packaged app exited with {code}, expected 0")
    finally:
        handle.close()


def assert_port_released(port: int, *, label: str) -> None:
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return
        time.sleep(0.2)
    raise ProductFailure(f"{label}: port {port} remained occupied after packaged app shutdown")


def classify_build_failure(output: str) -> Exception:
    low = output.casefold()
    environment_markers = (
        "could not resolve host",
        "failed to connect",
        "connection timed out",
        "network is unreachable",
        "temporary failure in name resolution",
        "не удалось загрузить runtime по https",
        "connection reset",
        "proxy error",
    )
    if any(marker in low for marker in environment_markers):
        return EnvironmentFailure("package build blocked by runner/network environment")
    return ProductFailure("exact package build failed")


def preflight() -> None:
    if git("rev-parse", "HEAD") != HEAD:
        raise RunnerFailure("verifier is not detached at exact PR head")
    run(["git", "fetch", "origin", "main", PR_BRANCH])
    if git("rev-parse", "origin/main") != BASE:
        raise RunnerFailure("origin/main moved from the exact PR base; verifier refuses ambiguous comparison")
    if git("rev-parse", f"origin/{PR_BRANCH}") != HEAD:
        raise RunnerFailure("PR branch moved from expected exact head")
    if git("status", "--porcelain"):
        raise RunnerFailure("repository is dirty before verification")
    if int(git("rev-list", "--count", f"{BASE}..{HEAD}")) != 1:
        raise RunnerFailure("D5 implementation is not exactly one commit from base")
    changed = set(filter(None, git("diff", "--name-only", f"{BASE}...{HEAD}").splitlines()))
    if changed != ALLOWED_FILES:
        raise RunnerFailure(f"unexpected D5 implementation scope: {sorted(changed)}")
    if any(path.startswith(FORBIDDEN_PREFIXES) for path in changed):
        raise RunnerFailure("runtime implementation leaked into D5 docs-only scope")
    run([sys.executable, "scripts/check_documentation_lifecycle.py"])
    run(["git", "diff", "--check", f"{BASE}...{HEAD}"])
    mark("exact_head_and_scope")
    mark("lifecycle_checker")


def build_package() -> dict[str, Any]:
    ensure_external(BUILD_DIR, label="build dir")
    ensure_external(DIST_DIR, label="dist dir")
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    env = os.environ.copy()
    env["COSMETIC_WORKSHOP_BUILD_DIR"] = str(BUILD_DIR)
    env["COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR"] = str(DIST_DIR)
    env["COSMETIC_WORKSHOP_BUILD_CACHE_DIR"] = str(TEMP / "d5-build-cache")
    proc = run(["bash", "scripts/package_macos.sh"], env=env, check=False, timeout=1200)
    (EVIDENCE / "package-build.log").write_text(proc.stdout, encoding="utf-8")
    if proc.returncode != 0:
        raise classify_build_failure(proc.stdout)
    if not ZIP.is_file() or not APP.is_dir() or not EXECUTABLE.is_file() or not MANIFEST.is_file():
        raise ProductFailure("package build reported success but expected ZIP/.app/runtime manifest is missing")
    run([sys.executable, "scripts/verify_product_version.py", "--app", str(APP), "--source-root", str(ROOT)])
    run([sys.executable, "scripts/verify_macos_package.py", "--app", str(APP), "--zip", str(ZIP), "--source-root", str(ROOT)])
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    archive_digest = sha256(ZIP)
    product = {
        "filename": ZIP.name,
        "sha256": archive_digest,
        "app_version": manifest["app_version"],
        "package_architecture": manifest["architecture"],
        "zip_path": str(ZIP),
        "app_path": str(APP),
    }
    report["artifact"] = product
    report["environment"] = {
        "runner_architecture": run(["uname", "-m"]).stdout.strip(),
        "macos_version": run(["sw_vers", "-productVersion"]).stdout.strip(),
        "clean_environment_kind": "isolated runner temp user-data directory (automated layer only)",
    }
    mark("exact_package_build_and_identity")
    return manifest


def smoke(manifest: dict[str, Any]) -> None:
    shutil.rmtree(USER_DATA, ignore_errors=True)
    USER_DATA.mkdir(parents=True, exist_ok=False)
    ensure_external(USER_DATA, label="isolated user-data")

    frontend_port = free_port()
    backend_port = free_port()
    while backend_port == frontend_port:
        backend_port = free_port()

    first, first_log = start_app(frontend_port, backend_port, "first-start.log")
    first_stopped = False
    try:
        wait_health(backend_port, str(manifest["app_version"]), first)
        wait_frontend(frontend_port, first)
        mark("first_packaged_start")

        status_before = api(backend_port, "GET", "/api/backups/status")
        if not status_before.get("database_exists"):
            raise ProductFailure("fresh packaged startup did not create the working database")

        backup = api(backend_port, "POST", "/api/backups", {"reason": "manual"}, expected=201)
        backup_file = backup["backup"]["filename"]
        backup_path = Path(backup["backup"]["path"]).resolve()
        if not backup_path.is_file():
            raise ProductFailure("backup API returned success but artifact is missing")
        ensure_external(backup_path, label="backup artifact")
        if USER_DATA not in backup_path.parents:
            raise ProductFailure(f"backup escaped isolated user-data directory: {backup_path}")

        client = api(backend_port, "POST", "/api/clients", {"full_name": "D5 Тестовый клиент"}, expected=201)
        ingredient = api(
            backend_port,
            "POST",
            "/api/ingredients",
            {"name": "D5 Тестовый компонент", "category": "other", "default_unit": "g"},
            expected=201,
        )
        recipe = api(
            backend_port,
            "POST",
            "/api/recipe-templates",
            {"name": "D5 Тестовый рецепт", "product_type": "Тест"},
            expected=201,
        )
        version = api(
            backend_port,
            "POST",
            f"/api/recipe-templates/{recipe['id']}/versions",
            {
                "title": "D5 Тестовая версия",
                "target_batch_size_value": "100",
                "target_batch_size_unit": "g",
                "ingredients": [
                    {
                        "ingredient_id": ingredient["id"],
                        "position": 1,
                        "phase": "A",
                        "amount_value": "100",
                        "amount_unit": "percent",
                    }
                ],
            },
            expected=201,
        )
        report["created"] = {
            "backup_filename": backup_file,
            "client_id": client["id"],
            "ingredient_id": ingredient["id"],
            "recipe_template_id": recipe["id"],
            "recipe_version_id": version["version"]["id"],
        }
        mark("backup_client_component_recipe_created")

        stop_app(first, first_log, label="first shutdown")
        first_stopped = True
        assert_port_released(frontend_port, label="first frontend shutdown")
        assert_port_released(backend_port, label="first backend shutdown")
        mark("graceful_packaged_shutdown")
    finally:
        if not first_stopped:
            try:
                stop_app(first, first_log, label="first cleanup shutdown")
            except Exception:
                pass

    second, second_log = start_app(frontend_port, backend_port, "second-start.log")
    second_stopped = False
    try:
        wait_health(backend_port, str(manifest["app_version"]), second)
        wait_frontend(frontend_port, second)
        created = report["created"]

        client = api(backend_port, "GET", f"/api/clients/{created['client_id']}")
        if client.get("full_name") != "D5 Тестовый клиент":
            raise ProductFailure("client did not persist across packaged restart")
        ingredient = api(backend_port, "GET", f"/api/ingredients/{created['ingredient_id']}")
        if ingredient.get("name") != "D5 Тестовый компонент":
            raise ProductFailure("component did not persist across packaged restart")
        recipe = api(backend_port, "GET", f"/api/recipe-templates/{created['recipe_template_id']}")
        if recipe.get("name") != "D5 Тестовый рецепт":
            raise ProductFailure("recipe did not persist across packaged restart")
        detail = api(backend_port, "GET", f"/api/recipe-versions/{created['recipe_version_id']}")
        if detail.get("version", {}).get("id") != created["recipe_version_id"]:
            raise ProductFailure("recipe version did not persist across packaged restart")
        if not detail.get("ingredients") or detail["ingredients"][0].get("ingredient_id") != created["ingredient_id"]:
            raise ProductFailure("recipe version ingredient relation did not persist across restart")

        backups = api(backend_port, "GET", "/api/backups")
        filenames = {item.get("filename") for item in backups.get("backups", [])}
        if created["backup_filename"] not in filenames:
            raise ProductFailure("created backup is not visible after packaged restart")
        status_after = api(backend_port, "GET", "/api/backups/status")
        if not status_after.get("database_exists") or int(status_after.get("backup_count", 0)) < 1:
            raise ProductFailure("backup/database status is not preserved after restart")

        db_path = Path(status_after["database_path"]).resolve()
        if not db_path.is_file():
            raise ProductFailure("working database path reported after restart does not exist")
        ensure_external(db_path, label="working database")
        if USER_DATA not in db_path.parents:
            raise ProductFailure(f"working database escaped isolated user-data directory: {db_path}")
        mark("restart_persistence")
        mark("external_user_data_boundary")

        stop_app(second, second_log, label="second shutdown")
        second_stopped = True
        assert_port_released(frontend_port, label="second frontend shutdown")
        assert_port_released(backend_port, label="second backend shutdown")
        mark("second_graceful_shutdown")
    finally:
        if not second_stopped:
            try:
                stop_app(second, second_log, label="second cleanup shutdown")
            except Exception:
                pass


def postflight() -> None:
    if git("rev-parse", "HEAD") != HEAD:
        raise RunnerFailure("HEAD changed during verification")
    run(["git", "fetch", "origin", PR_BRANCH])
    if git("rev-parse", f"origin/{PR_BRANCH}") != HEAD:
        raise RunnerFailure("PR branch moved during verification")
    if git("status", "--porcelain"):
        raise RunnerFailure(f"repository dirty after verification: {git('status', '--porcelain')}")
    mark("repository_postflight")


def write_report() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "evidence.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# PR #205 D5 automated exact-package verification",
        "",
        f"Exact head: `{HEAD}`",
        f"Exact base: `{BASE}`",
        f"Result: **{report['result']}**",
        f"Classification: `{report['classification']}`",
        "",
        "## Checks",
    ]
    for name, value in report["checks"].items():
        lines.append(f"- {name}: {value}")
    if report.get("artifact"):
        lines.extend([
            "",
            "## Exact package artifact",
            f"- filename: `{report['artifact'].get('filename')}`",
            f"- SHA-256: `{report['artifact'].get('sha256')}`",
            f"- app version: `{report['artifact'].get('app_version')}`",
            f"- package architecture: `{report['artifact'].get('package_architecture')}`",
            f"- runner Mac architecture: `{report['environment'].get('runner_architecture')}`",
            f"- macOS: `{report['environment'].get('macos_version')}`",
        ])
    lines.extend([
        "",
        "## D5 boundary",
        "- Human clean-Mac/clean-profile Finder/System Settings layer: **REQUIRED — NOT EXECUTED BY AUTOMATION**",
        "- D5 lifecycle closure: **NOT COMPLETED**",
        "- Product release readiness: **NOT CLAIMED**",
        "",
    ])
    if report["result"] == "passed":
        lines.extend([
            "PASS — FULL AUTOMATED SMOKE PASSED",
            "",
            "D5 automated exact-package layer: PASS",
            "",
            "This is deliberately **not** `PASS — D5 REMOTE INSTALL REHEARSAL PASSED`; the human layer is still mandatory.",
        ])
    else:
        lines.append(f"{report['classification']}")
    (EVIDENCE / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    try:
        preflight()
        manifest = build_package()
        smoke(manifest)
        postflight()
    except EnvironmentFailure as exc:
        report["result"] = "inconclusive"
        report["classification"] = "INCONCLUSIVE — ENVIRONMENT"
        report["error"] = str(exc)
        write_report()
        print((EVIDENCE / "report.md").read_text(encoding="utf-8"))
        return 2
    except RunnerFailure as exc:
        report["result"] = "inconclusive"
        report["classification"] = "INCONCLUSIVE — RUNNER"
        report["error"] = str(exc)
        write_report()
        print((EVIDENCE / "report.md").read_text(encoding="utf-8"))
        return 3
    except ProductFailure as exc:
        report["result"] = "failed"
        report["classification"] = "FAIL — PRODUCT"
        report["error"] = str(exc)
        write_report()
        print((EVIDENCE / "report.md").read_text(encoding="utf-8"))
        return 1
    except Exception as exc:  # verifier defects must not be misreported as product defects
        report["result"] = "inconclusive"
        report["classification"] = "INCONCLUSIVE — RUNNER"
        report["error"] = f"unexpected verifier exception: {type(exc).__name__}: {exc}"
        write_report()
        print((EVIDENCE / "report.md").read_text(encoding="utf-8"))
        return 3
    else:
        report["result"] = "passed"
        report["classification"] = "PASS — FULL AUTOMATED SMOKE PASSED"
        write_report()
        print((EVIDENCE / "report.md").read_text(encoding="utf-8"))
        return 0
    finally:
        # Preserve exact ZIP/evidence for upload; remove only disposable user-data.
        shutil.rmtree(USER_DATA, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
