from __future__ import annotations

import json
from pathlib import Path

from app.version import read_repository_app_version

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_runtime_version_surfaces_do_not_embed_the_current_version_literal():
    canonical = read_repository_app_version()
    for relative in (
        "backend/app/main.py",
        "backend/app/api/health.py",
        "macos_package/tests/packaging_fixtures.py",
    ):
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert f'"{canonical}"' not in source
        assert f"'{canonical}'" not in source


def test_private_frontend_npm_metadata_has_no_independent_product_version():
    package = json.loads((REPO_ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((REPO_ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))

    assert package["private"] is True
    assert "version" not in package
    assert "version" not in lock
    assert "version" not in lock["packages"][""]


def test_historical_database_seed_is_not_reinterpreted_as_runtime_authority():
    migration = (
        REPO_ROOT / "backend" / "app" / "migrations" / "versions" / "0001_infrastructure.py"
    ).read_text(encoding="utf-8")

    # ADR 0020 explicitly leaves this historical seed in place. D4-A removes
    # active runtime/build authorities; it does not rewrite historical user data.
    assert '"app.version"' in migration
