"""The package-structure gate: what must be in the artifact, and what must not.

Two halves.

The **deterministic** half builds synthetic bundles and asserts the verifier's
verdict on each — including every negative case, which a real build cannot be
made to produce on purpose. It needs no Mac, no network and no interpreter
download, so the exclusion rules that keep a user database out of a
distributable artifact are checked on every run rather than only after a build.

The **real-artifact** half runs the same verifier against a bundle produced by
`make package-macos` when one is present, and skips loudly when it is not. This
is a structure gate: it proves what an artifact contains, never that it runs.
Live behaviour is the Level-5 package smoke's job.
"""

from __future__ import annotations

from pathlib import Path
import os
import stat
import zipfile

import pytest

from macos_package.verification import (
    APP_BUNDLE_NAME,
    ZIP_NAME,
    verify_package,
)
from packaging_fixtures import build_app_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]


def failures_of(bundle: Path, zip_path: Path | None = None, source_root: Path | None = None):
    result = verify_package(bundle, zip_path, source_root=source_root)
    return {check.name for check in result.failures}


def zip_bundle(bundle: Path, zip_path: Path) -> Path:
    """Archive the bundle preserving the executable bit, as `ditto` would."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle.rglob("*")):
            if not path.is_file():
                continue
            arcname = f"{bundle.name}/{path.relative_to(bundle).as_posix()}"
            info = zipfile.ZipInfo(arcname)
            info.external_attr = (path.stat().st_mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())
    return zip_path


# -- the passing shape -----------------------------------------------------


def test_a_complete_bundle_passes_every_check(tmp_path):
    bundle = build_app_bundle(tmp_path)
    result = verify_package(bundle, source_root=REPO_ROOT)
    assert result.ok, result.report()
    assert {check.name for check in result.checks} >= {
        "app_bundle_exists",
        "info_plist",
        "bundle_executable",
        "bundled_runtime",
        "required_application_files",
        "frontend_production_assets",
        "offline_help_resources",
        "packaged_migrations",
        "package_manifest",
        "no_user_database",
        "no_forbidden_directories",
        "no_developer_or_secret_files",
        "no_source_repository_reference",
    }


def test_a_missing_bundle_fails_immediately(tmp_path):
    assert "app_bundle_exists" in failures_of(tmp_path / "nothing.app")


# -- bundle metadata and entrypoint ----------------------------------------


def test_the_bundle_must_declare_the_human_facing_display_name(tmp_path):
    """The internal artifact name is CosmeticWorkshopOS; the user sees Russian."""
    import plistlib

    bundle = build_app_bundle(tmp_path)
    plist_path = bundle / "Contents" / "Info.plist"
    plist = plistlib.loads(plist_path.read_bytes())
    plist["CFBundleDisplayName"] = "CosmeticWorkshopOS"
    plist_path.write_bytes(plistlib.dumps(plist))
    assert "info_plist" in failures_of(bundle)


def test_a_non_executable_bootstrap_fails(tmp_path):
    """A bundle whose executable bit was lost is a bundle that will not open."""
    bundle = build_app_bundle(tmp_path)
    executable = bundle / "Contents" / "MacOS" / "CosmeticWorkshopOS"
    executable.chmod(executable.stat().st_mode & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH)
    assert "bundle_executable" in failures_of(bundle)


def test_a_missing_bootstrap_fails(tmp_path):
    bundle = build_app_bundle(tmp_path)
    (bundle / "Contents" / "MacOS" / "CosmeticWorkshopOS").unlink()
    assert "bundle_executable" in failures_of(bundle)


# -- self-contained runtime ------------------------------------------------


def test_a_package_without_a_bundled_interpreter_fails(tmp_path):
    """Without this the user would need their own Python — the whole point of D3."""
    bundle = build_app_bundle(tmp_path)
    (bundle / "Contents" / "Resources" / "runtime" / "bin" / "python3.12").unlink()
    assert "bundled_runtime" in failures_of(bundle)


def test_a_bundled_interpreter_without_a_standard_library_fails(tmp_path):
    bundle = build_app_bundle(tmp_path)
    (bundle / "Contents" / "Resources" / "runtime" / "lib" / "python3.12").rmdir()
    assert "bundled_runtime" in failures_of(bundle)


# -- product content -------------------------------------------------------


@pytest.mark.parametrize(
    "relative",
    [
        "launcher/main.py",
        "launcher/runtime.py",
        "launcher/restore/engine.py",
        "launcher/restore/macos_picker.py",
        "backend/app/launcher_backend_entrypoint.py",
        "backend/app/services/backend_liveness.py",
        "macos_package/entrypoint.py",
        "frontend/dist/index.html",
    ],
)
def test_every_required_product_file_is_required(tmp_path, relative):
    bundle = build_app_bundle(tmp_path)
    (bundle / "Contents" / "Resources" / "app" / relative).unlink()
    assert "required_application_files" in failures_of(bundle)


def test_a_frontend_build_without_assets_fails(tmp_path):
    bundle = build_app_bundle(tmp_path)
    for asset in (bundle / "Contents/Resources/app/frontend/dist/assets").iterdir():
        asset.unlink()
    assert "frontend_production_assets" in failures_of(bundle)


def test_offline_help_resources_are_required(tmp_path):
    bundle = build_app_bundle(tmp_path)
    for document in (bundle / "Contents/Resources/app/help").iterdir():
        document.unlink()
    assert "offline_help_resources" in failures_of(bundle)


def test_a_declared_migration_that_is_not_packaged_fails(tmp_path):
    """Otherwise a fresh database breaks on first launch, after the data dir exists."""
    bundle = build_app_bundle(tmp_path)
    (
        bundle / "Contents/Resources/app/backend/app/migrations/versions/0002_ingredients.py"
    ).unlink()
    assert "packaged_migrations" in failures_of(bundle)


def test_the_migration_check_counts_what_the_package_declares(tmp_path):
    bundle = build_app_bundle(tmp_path)
    result = verify_package(bundle)
    migrations = next(check for check in result.checks if check.name == "packaged_migrations")
    assert migrations.ok
    assert "2 migrations packaged" in migrations.detail


def test_a_missing_or_broken_manifest_fails(tmp_path):
    bundle = build_app_bundle(tmp_path)
    manifest = bundle / "Contents/Resources/app/package-runtime.json"
    manifest.write_text("{ broken", encoding="utf-8")
    assert "package_manifest" in failures_of(bundle)
    manifest.unlink()
    assert "package_manifest" in failures_of(bundle)


# -- exclusions ------------------------------------------------------------


@pytest.mark.parametrize(
    "relative",
    [
        "Contents/Resources/app/cosmetic_workshop.sqlite",
        "Contents/Resources/app/data/cosmetic_workshop.sqlite3",
        "Contents/Resources/app/backend/workshop.db",
    ],
)
def test_any_database_inside_the_package_fails(tmp_path, relative):
    """A distributable artifact carrying a workshop's records is a privacy incident."""
    bundle = build_app_bundle(tmp_path)
    target = bundle / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"SQLite format 3\x00")
    assert "no_user_database" in failures_of(bundle)


@pytest.mark.parametrize(
    "relative",
    [
        "Contents/Resources/app/.git",
        "Contents/Resources/app/frontend/node_modules",
        "Contents/Resources/app/backend/__pycache__",
        "Contents/Resources/app/backups",
        "Contents/Resources/app/exports",
        "Contents/Resources/app/attachments",
        "Contents/Resources/app/logs",
        "Contents/Resources/app/backend/app/tests",
        "Contents/Resources/app/.local",
    ],
)
def test_forbidden_directories_fail(tmp_path, relative):
    bundle = build_app_bundle(tmp_path)
    (bundle / relative).mkdir(parents=True, exist_ok=True)
    assert "no_forbidden_directories" in failures_of(bundle)


@pytest.mark.parametrize(
    "relative",
    [
        # A library shipping its own test package.
        "Contents/Resources/runtime/lib/python3.12/site-packages/anyio/tests",
        # CPython's standard-library `venv` module — not a developer virtualenv.
        "Contents/Resources/runtime/lib/python3.12/venv",
    ],
)
def test_legitimate_interpreter_directories_are_not_flagged(tmp_path, relative):
    """These names are banned under the application root, not inside the runtime.

    A real CPython distribution contains both, so failing a build over one would
    be a false alarm — and a gate that cries wolf is a gate people learn to
    bypass. The same names remain forbidden under the application root, where
    they could only have come from the working tree.
    """
    bundle = build_app_bundle(tmp_path)
    (bundle / relative).mkdir(parents=True, exist_ok=True)
    assert "no_forbidden_directories" not in failures_of(bundle)


def test_a_vendored_ca_bundle_in_the_runtime_is_not_mistaken_for_a_secret(tmp_path):
    """`pip/_vendor/certifi/cacert.pem` is a public trust store, not a private key."""
    bundle = build_app_bundle(tmp_path)
    cacert = (
        bundle
        / "Contents/Resources/runtime/lib/python3.12/site-packages/pip/_vendor/certifi/cacert.pem"
    )
    cacert.parent.mkdir(parents=True, exist_ok=True)
    cacert.write_text("-----BEGIN CERTIFICATE-----\n", encoding="utf-8")
    assert "no_developer_or_secret_files" not in failures_of(bundle)


def test_a_private_key_under_the_application_root_is_still_flagged(tmp_path):
    """Scoping the credential patterns must not disarm them where they matter."""
    bundle = build_app_bundle(tmp_path)
    (bundle / "Contents/Resources/app/backend/server.pem").write_text("x", encoding="utf-8")
    assert "no_developer_or_secret_files" in failures_of(bundle)


def test_vcs_and_finder_droppings_are_forbidden_everywhere(tmp_path):
    """These are never legitimate, in the application root or the interpreter."""
    bundle = build_app_bundle(tmp_path)
    (bundle / "Contents/Resources/runtime/.DS_Store").write_text("x", encoding="utf-8")
    assert "no_developer_or_secret_files" in failures_of(bundle)


@pytest.mark.parametrize(
    "name",
    [".env", ".env.local", "id_rsa", "server.pem", "signing.key", ".netrc", ".DS_Store"],
)
def test_developer_and_secret_looking_files_fail(tmp_path, name):
    bundle = build_app_bundle(tmp_path)
    (bundle / "Contents" / "Resources" / "app" / name).write_text("x", encoding="utf-8")
    assert "no_developer_or_secret_files" in failures_of(bundle)


# -- independence from the build checkout ----------------------------------


def test_a_package_naming_its_build_checkout_fails(tmp_path):
    """The artifact must not depend on — or even mention — the repository."""
    bundle = build_app_bundle(tmp_path)
    source_root = tmp_path / "checkout"
    source_root.mkdir()
    (bundle / "Contents/Resources/app/launcher/config.py").write_text(
        f'PROJECT_ROOT = "{source_root.resolve()}"\n', encoding="utf-8"
    )
    assert "no_source_repository_reference" in failures_of(bundle, source_root=source_root)


def test_the_source_reference_check_reports_itself_as_skipped_when_unusable(tmp_path):
    """A check that silently passes with nothing to compare is worse than none."""
    bundle = build_app_bundle(tmp_path)
    result = verify_package(bundle)
    check = next(c for c in result.checks if c.name == "no_source_repository_reference")
    assert check.ok and "skipped" in check.detail


# -- the archive -----------------------------------------------------------


def test_the_zip_carries_the_app_bundle_with_its_executable_bit(tmp_path):
    bundle = build_app_bundle(tmp_path)
    archive = zip_bundle(bundle, tmp_path / ZIP_NAME)
    result = verify_package(bundle, archive, source_root=REPO_ROOT)
    assert result.ok, result.report()


def test_a_missing_zip_fails(tmp_path):
    bundle = build_app_bundle(tmp_path)
    assert "zip_exists" in failures_of(bundle, tmp_path / "absent.zip")


def test_a_zip_carrying_a_database_fails(tmp_path):
    bundle = build_app_bundle(tmp_path)
    database = bundle / "Contents" / "Resources" / "app" / "leaked.sqlite"
    database.write_bytes(b"SQLite format 3\x00")
    archive = zip_bundle(bundle, tmp_path / ZIP_NAME)
    database.unlink()  # clean on disk, still poisoned in the archive
    assert "zip_excludes_forbidden_content" in failures_of(bundle, archive)


def test_a_zip_that_lost_the_executable_bit_fails(tmp_path):
    """`zip` alone does not reliably preserve it; the build uses `ditto` for this."""
    bundle = build_app_bundle(tmp_path)
    archive = tmp_path / ZIP_NAME
    with zipfile.ZipFile(archive, "w") as handle:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                handle.writestr(
                    f"{bundle.name}/{path.relative_to(bundle).as_posix()}", path.read_bytes()
                )
    assert "zip_executable_bit_preserved" in failures_of(bundle, archive)


# -- the real build, when one exists ---------------------------------------


def _built_artifacts() -> tuple[Path, Path | None] | None:
    build_dir = Path(os.environ.get("COSMETIC_WORKSHOP_BUILD_DIR", REPO_ROOT / "build"))
    output_dir = Path(
        os.environ.get("COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR", REPO_ROOT / "dist")
    )
    bundle = build_dir / "package" / APP_BUNDLE_NAME
    if not bundle.is_dir():
        return None
    archive = output_dir / ZIP_NAME
    return bundle, (archive if archive.is_file() else None)


def test_a_real_built_package_passes_the_same_gate():
    artifacts = _built_artifacts()
    if artifacts is None:
        pytest.skip("no built package present — run `make package-macos` first")
    bundle, archive = artifacts
    result = verify_package(bundle, archive, source_root=REPO_ROOT)
    assert result.ok, result.report()
