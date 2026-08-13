from __future__ import annotations

import json
from pathlib import Path
import plistlib
import shutil

import pytest

from scripts.verify_product_version import (
    ProductVersionVerificationError,
    verify_product_version,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def canonical_version(root: Path = REPO_ROOT) -> str:
    return (root / "backend" / "VERSION").read_text(encoding="utf-8").strip()


def fake_app(tmp_path: Path, version: str | None = None) -> Path:
    version = version or canonical_version()
    app = tmp_path / "CosmeticWorkshopOS.app"
    contents = app / "Contents"
    app_root = contents / "Resources" / "app"
    (app_root / "backend").mkdir(parents=True)
    plist = {
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
    }
    (contents / "Info.plist").write_bytes(plistlib.dumps(plist))
    (app_root / "package-runtime.json").write_text(
        json.dumps({"app_version": version}), encoding="utf-8"
    )
    return app


def source_root(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    (root / "backend").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "backend" / "VERSION", root / "backend" / "VERSION")
    shutil.copy2(REPO_ROOT / "backend" / "pyproject.toml", root / "backend" / "pyproject.toml")
    return root


def test_all_package_version_projections_match_one_source(tmp_path):
    root = source_root(tmp_path)
    app = fake_app(tmp_path)

    assert verify_product_version(app, root) == canonical_version(root)


def test_manifest_projection_mismatch_fails_the_build_gate(tmp_path):
    root = source_root(tmp_path)
    app = fake_app(tmp_path)
    manifest = app / "Contents" / "Resources" / "app" / "package-runtime.json"
    manifest.write_text(json.dumps({"app_version": "9.9.9"}), encoding="utf-8")

    with pytest.raises(ProductVersionVerificationError):
        verify_product_version(app, root)


def test_info_plist_projection_mismatch_fails_the_build_gate(tmp_path):
    root = source_root(tmp_path)
    app = fake_app(tmp_path, version="9.9.9")

    with pytest.raises(ProductVersionVerificationError):
        verify_product_version(app, root)


def test_repository_version_source_is_not_allowed_inside_packaged_backend(tmp_path):
    root = source_root(tmp_path)
    app = fake_app(tmp_path)
    copied = app / "Contents" / "Resources" / "app" / "backend" / "VERSION"
    copied.write_text(canonical_version(root) + "\n", encoding="utf-8")

    with pytest.raises(ProductVersionVerificationError):
        verify_product_version(app, root)
