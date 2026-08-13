#!/usr/bin/env python3
"""Verify every D4-A application-version projection against one source truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import plistlib
import sys
import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.version import AppVersionError, read_repository_app_version, validate_app_version  # noqa: E402


class ProductVersionVerificationError(RuntimeError):
    pass


def verify_product_version(app_path: Path, source_root: Path) -> str:
    source_root = Path(source_root).resolve()
    app_path = Path(app_path).resolve()
    try:
        canonical = read_repository_app_version(source_root / "backend" / "VERSION")
    except AppVersionError as exc:
        raise ProductVersionVerificationError(str(exc)) from exc

    pyproject_path = source_root / "backend" / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as handle:
            pyproject = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ProductVersionVerificationError("backend/pyproject.toml is unreadable") from exc
    project = pyproject.get("project", {})
    if "version" in project:
        raise ProductVersionVerificationError("backend pyproject still has an independent version literal")
    if "version" not in project.get("dynamic", []):
        raise ProductVersionVerificationError("backend pyproject does not declare dynamic version projection")
    version_projection = (
        pyproject.get("tool", {})
        .get("setuptools", {})
        .get("dynamic", {})
        .get("version", {})
        .get("file")
    )
    if version_projection != ["VERSION"]:
        raise ProductVersionVerificationError("backend pyproject version is not projected from VERSION")

    contents = app_path / "Contents"
    plist_path = contents / "Info.plist"
    manifest_path = contents / "Resources" / "app" / "package-runtime.json"
    packaged_source_path = contents / "Resources" / "app" / "backend" / "VERSION"
    if packaged_source_path.exists():
        raise ProductVersionVerificationError("editable repository VERSION source was copied into the package")

    try:
        plist = plistlib.loads(plist_path.read_bytes())
    except Exception as exc:  # noqa: BLE001 - any parse failure is one verdict
        raise ProductVersionVerificationError("Info.plist is unreadable") from exc
    short_version = plist.get("CFBundleShortVersionString")
    bundle_version = plist.get("CFBundleVersion")
    try:
        short_version = validate_app_version(short_version)
        bundle_version = validate_app_version(bundle_version)
    except AppVersionError as exc:
        raise ProductVersionVerificationError("Info.plist version projection is invalid") from exc
    if short_version != canonical or bundle_version != canonical:
        raise ProductVersionVerificationError("Info.plist version projection does not match backend/VERSION")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductVersionVerificationError("package-runtime.json is unreadable") from exc
    if not isinstance(manifest, dict):
        raise ProductVersionVerificationError("package-runtime.json has an invalid shape")
    try:
        packaged_version = validate_app_version(manifest.get("app_version"))
    except AppVersionError as exc:
        raise ProductVersionVerificationError("package-runtime.json app_version is invalid") from exc
    if packaged_version != canonical:
        raise ProductVersionVerificationError("package-runtime.json app_version does not match backend/VERSION")

    return canonical


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        version = verify_product_version(arguments.app, arguments.source_root)
    except ProductVersionVerificationError as exc:
        print(f"Product version verification: FAIL — {exc}", file=sys.stderr)
        return 1
    print(f"Product version verification: PASS — {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
