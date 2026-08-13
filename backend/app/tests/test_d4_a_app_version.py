from __future__ import annotations

import json
from pathlib import Path
import re
import tomllib

import pytest

from app.services.runtime_identity import get_runtime_settings_status
from app.version import (
    AppVersionError,
    read_repository_app_version,
    resolve_effective_app_version,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_repository_version_is_a_canonical_identity_token():
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", read_repository_app_version())


def test_source_runtime_resolves_the_repository_version(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    missing_manifest = tmp_path / "package-runtime.json"

    assert resolve_effective_app_version(
        repository_version_path=version_file,
        package_manifest_path=missing_manifest,
    ) == "1.2.3"


def test_packaged_runtime_resolves_the_manifest_projection(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    manifest = tmp_path / "package-runtime.json"
    manifest.write_text(json.dumps({"app_version": "2.3.4"}), encoding="utf-8")

    assert resolve_effective_app_version(
        repository_version_path=version_file,
        package_manifest_path=manifest,
    ) == "2.3.4"


def test_present_but_invalid_package_manifest_never_falls_back_to_source(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    manifest = tmp_path / "package-runtime.json"
    manifest.write_text("not json", encoding="utf-8")

    with pytest.raises(AppVersionError):
        resolve_effective_app_version(
            repository_version_path=version_file,
            package_manifest_path=manifest,
        )


@pytest.mark.parametrize("value", ["", " 1.2.3", "1.2", "1.2.3-beta", "v1.2.3"])
def test_noncanonical_version_syntax_is_rejected(tmp_path, value):
    version_file = tmp_path / "VERSION"
    version_file.write_text(value + "\n", encoding="utf-8")

    with pytest.raises(AppVersionError):
        read_repository_app_version(version_file)


def test_backend_pyproject_projects_version_from_the_canonical_file():
    with (REPO_ROOT / "backend" / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    assert "version" not in pyproject["project"]
    assert "version" in pyproject["project"]["dynamic"]
    assert pyproject["tool"]["setuptools"]["dynamic"]["version"]["file"] == ["VERSION"]


def test_settings_status_exposes_the_same_effective_runtime_version():
    status = get_runtime_settings_status()

    assert status.app.version == resolve_effective_app_version()
