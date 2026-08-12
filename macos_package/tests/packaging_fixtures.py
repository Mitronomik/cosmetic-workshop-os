"""Shared fixtures for the D3 packaging tests.

The frontend-build and app-bundle builders here construct the *shape* of a real
artifact without needing a Mac, a network or a 25 MB interpreter download. That
is what lets the structure verifier be tested deterministically on any machine —
including the negative cases, which a real build cannot produce on purpose.
"""

from __future__ import annotations

from pathlib import Path
import plistlib
import socket
import stat
import time
import json


def free_loopback_port() -> int:
    """Take a port the OS says is free, then release it.

    Inherently racy, and deliberately so: the tests need a port nothing else is
    expected to hold, not a reservation. The server under test performs the
    authoritative bind.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def wait_until_serving(port: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return True
        except OSError:
            time.sleep(0.02)
    return False


def build_frontend_dist(root: Path) -> Path:
    """A minimal but structurally faithful production frontend build."""
    dist = root / "frontend" / "dist"
    (dist / "assets").mkdir(parents=True, exist_ok=True)
    (dist / "brand").mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(
        "<!doctype html><html lang=\"ru\"><head><title>Мастерская косметолога</title>"
        "</head><body><div id=\"root\"></div></body></html>",
        encoding="utf-8",
    )
    (dist / "assets" / "main.js").write_text("export const marker = 'main-js';\n", encoding="utf-8")
    (dist / "assets" / "styles.css").write_text(":root { --marker: 1; }\n", encoding="utf-8")
    (dist / "brand" / "mch-logo.png").write_bytes(b"\x89PNG\r\n\x1a\n fake")
    return dist


REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_TEMPLATE = REPO_ROOT / "scripts" / "macos" / "bundle_bootstrap.sh"


def bootstrap_template_source() -> str:
    return BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")


MIGRATIONS_MODULE_SOURCE = '''\
MIGRATION_MODULES = [
    "app.migrations.versions.0001_infrastructure",
    "app.migrations.versions.0002_ingredients",
]
'''


def build_app_bundle(root: Path, *, name: str = "CosmeticWorkshopOS.app") -> Path:
    """A complete, passing `.app` skeleton the negative tests then break."""
    bundle = root / name
    contents = bundle / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    application = resources / "app"
    macos.mkdir(parents=True, exist_ok=True)

    contents.joinpath("Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleName": "CosmeticWorkshopOS",
                "CFBundleDisplayName": "Мастерская косметолога",
                "CFBundleIdentifier": "ru.cosmetic-workshop-os.app",
                "CFBundleExecutable": "CosmeticWorkshopOS",
                "CFBundlePackageType": "APPL",
                "CFBundleShortVersionString": "0.1.0",
            }
        )
    )
    # The real template, not a stub. The structure gate inspects the bootstrap
    # that is actually inside a bundle, so the fixture has to carry the same
    # script the build installs — otherwise these tests would validate a
    # placeholder while the shipped script drifted.
    executable = macos / "CosmeticWorkshopOS"
    executable.write_text(bootstrap_template_source(), encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    runtime_bin = resources / "runtime" / "bin"
    runtime_bin.mkdir(parents=True, exist_ok=True)
    interpreter = runtime_bin / "python3.12"
    interpreter.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    interpreter.chmod(interpreter.stat().st_mode | stat.S_IXUSR)
    (resources / "runtime" / "lib" / "python3.12").mkdir(parents=True, exist_ok=True)

    for relative in (
        "launcher/main.py",
        "launcher/config.py",
        "launcher/runtime.py",
        "launcher/restore/engine.py",
        "launcher/restore/control_plane.py",
        "launcher/restore/macos_picker.py",
        "backend/app/main.py",
        "backend/app/launcher_backend_entrypoint.py",
        "backend/app/services/startup.py",
        "backend/app/services/backend_liveness.py",
        "backend/app/migrations/versions/0001_infrastructure.py",
        "backend/app/migrations/versions/0002_ingredients.py",
        "macos_package/entrypoint.py",
        "macos_package/frontend_server.py",
    ):
        target = application / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# packaged module\n", encoding="utf-8")

    migrations = application / "backend" / "app" / "db" / "migrations.py"
    migrations.parent.mkdir(parents=True, exist_ok=True)
    migrations.write_text(MIGRATIONS_MODULE_SOURCE, encoding="utf-8")

    build_frontend_dist(application)

    help_dir = application / "help"
    help_dir.mkdir(parents=True, exist_ok=True)
    (help_dir / "how-to-create-order.md").write_text("# Как создать заказ\n", encoding="utf-8")

    (application / "package-runtime.json").write_text(
        json.dumps(
            {
                "product": "Мастерская косметолога",
                "artifact": name,
                "app_version": "0.1.0",
                "python_version": "3.12.13",
                "architecture": "arm64",
                "runtime_root_relative_to_app": "../runtime",
                "requires_system_python": False,
                "requires_node": False,
            }
        ),
        encoding="utf-8",
    )
    return bundle
