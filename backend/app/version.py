"""Canonical D4-A application-version identity.

The repository owns exactly one editable version source: ``backend/VERSION``.
A packaged product does not carry that source file; its effective runtime version
comes from the build-generated ``package-runtime.json`` projection instead.

Version strings are metadata only. This module validates their syntax and never
orders or compares versions for schema compatibility; migration lineage owns that
question.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

VERSION_FILENAME = "VERSION"
PACKAGE_MANIFEST_NAME = "package-runtime.json"
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class AppVersionError(RuntimeError):
    """The application version authority or packaged projection is unusable."""


def validate_app_version(value: object) -> str:
    if not isinstance(value, str):
        raise AppVersionError("Application version must be a string.")
    candidate = value.strip()
    if candidate != value or not VERSION_PATTERN.fullmatch(candidate):
        raise AppVersionError("Application version must use canonical major.minor.patch syntax.")
    return candidate


def default_repository_version_path() -> Path:
    return Path(__file__).resolve().parents[1] / VERSION_FILENAME


def default_package_manifest_path() -> Path:
    return Path(__file__).resolve().parents[2] / PACKAGE_MANIFEST_NAME


def read_repository_app_version(path: Path | None = None) -> str:
    version_path = Path(path) if path is not None else default_repository_version_path()
    try:
        raw = version_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AppVersionError("Canonical repository application version is unavailable.") from exc
    value = raw[:-1] if raw.endswith("\n") else raw
    if "\n" in value or "\r" in value:
        raise AppVersionError("Canonical repository application version has unexpected content.")
    return validate_app_version(value)


def read_packaged_app_version(path: Path | None = None) -> str:
    manifest_path = Path(path) if path is not None else default_package_manifest_path()
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AppVersionError("Packaged application version projection is unavailable.") from exc
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AppVersionError("Packaged application version projection is unreadable.") from exc
    if not isinstance(manifest, dict):
        raise AppVersionError("Packaged application version projection has an invalid shape.")
    return validate_app_version(manifest.get("app_version"))


def resolve_effective_app_version(
    *,
    repository_version_path: Path | None = None,
    package_manifest_path: Path | None = None,
) -> str:
    """Resolve the one effective runtime version without inventing a fallback.

    Presence of the package manifest selects packaged authority. If that manifest
    exists but is malformed, startup fails closed instead of falling back to a
    repository version that a built artifact must not depend on.
    """
    manifest_path = (
        Path(package_manifest_path)
        if package_manifest_path is not None
        else default_package_manifest_path()
    )
    if manifest_path.is_file():
        return read_packaged_app_version(manifest_path)

    version_path = (
        Path(repository_version_path)
        if repository_version_path is not None
        else default_repository_version_path()
    )
    return read_repository_app_version(version_path)
