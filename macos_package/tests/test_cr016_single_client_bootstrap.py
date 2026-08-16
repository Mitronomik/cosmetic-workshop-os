from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import subprocess
import sys
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "scripts" / "macos" / "single_client_bootstrap.command.template"
PACKAGER = ROOT / "scripts" / "package_single_client_macos.sh"
VERIFIER = ROOT / "scripts" / "verify_single_client_package.py"
COMMAND_NAME = "Установить или обновить Мастерскую.command"
INNER_NAME = "CosmeticWorkshopOS-mac.zip"
README_NAME = "Прочтите меня.txt"
VERSION = "0.1.0"
ARCH = "arm64"


def rendered_command(inner_bytes: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(inner_bytes).hexdigest()
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("__INNER_SHA256__", digest)
    text = text.replace("__APP_VERSION__", VERSION)
    text = text.replace("__ARCHITECTURE__", ARCH)
    return text, digest


def build_distribution_dir(tmp_path: Path) -> tuple[Path, str]:
    inner_bytes = b"exact-product-zip-fixture"
    command_text, digest = rendered_command(inner_bytes)
    directory = tmp_path / "Мастерская косметолога — установка"
    directory.mkdir()
    command = directory / COMMAND_NAME
    command.write_text(command_text, encoding="utf-8")
    command.chmod(command.stat().st_mode | stat.S_IXUSR)
    (directory / INNER_NAME).write_bytes(inner_bytes)
    (directory / README_NAME).write_text(
        f"{COMMAND_NAME}\n{VERSION}\n{ARCH}\n{digest}\n", encoding="utf-8"
    )
    return directory, digest


def run_verifier(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_template_is_fail_closed_before_quarantine_removal():
    text = TEMPLATE.read_text(encoding="utf-8")
    sha_gate = text.index('[[ "$ACTUAL_SHA256" == "$EXPECTED_SHA256" ]]')
    bundle_gate = text.index('[[ "$BUNDLE_ID" == "$EXPECTED_BUNDLE_ID" ]]')
    version_gate = text.index('[[ "$VERSION" == "$EXPECTED_VERSION" ]]')
    executable_gate = text.index('[[ "$EXECUTABLE_NAME" == "$EXPECTED_EXECUTABLE" ]]')
    arch_gate = text.index('if [[ "$EXPECTED_ARCH" == "arm64" ]]')
    first_xattr = text.index('"$XATTR" -dr com.apple.quarantine "$CANDIDATE_APP"')
    running_guard = text.index('"$PGREP" -x CosmeticWorkshopOS')
    backup = text.index('"$DITTO" "$DEST_APP" "$PREVIOUS_BACKUP"')
    replace = text.index('"$MV" "$DEST_APP" "$OLD_HOLD"')
    launch = text.index('"$OPEN" "$DEST_APP"')

    assert sha_gate < bundle_gate < version_gate < executable_gate < arch_gate < first_xattr
    assert first_xattr < running_guard < backup < replace < launch


def test_template_never_globally_weakens_macos_security_or_requires_admin():
    text = TEMPLATE.read_text(encoding="utf-8").casefold()
    for forbidden in (
        "spctl --master-disable",
        "spctl --global-disable",
        "csrutil disable",
        "sudo ",
        "xattr -cr",
        "/applications/cosmeticworkshopos.app",
    ):
        assert forbidden not in text
    assert 'install_dir="$home/applications"' in text
    assert '"$xattr" -dr com.apple.quarantine "$candidate_app"' in text


def test_template_does_not_take_database_or_d4_ownership():
    text = TEMPLATE.read_text(encoding="utf-8")
    for forbidden in (
        "cosmetic_workshop.sqlite",
        "schema_migrations",
        "update-journal.json",
        "before_migration",
    ):
        assert forbidden not in text


def test_directory_verifier_accepts_matching_generated_bootstrap(tmp_path):
    directory, digest = build_distribution_dir(tmp_path)
    result = run_verifier(
        "--directory",
        str(directory),
        "--expected-sha256",
        digest,
        "--expected-version",
        VERSION,
        "--expected-architecture",
        ARCH,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Single-client distribution verification: PASS" in result.stdout


def test_directory_verifier_rejects_inner_zip_mismatch(tmp_path):
    directory, digest = build_distribution_dir(tmp_path)
    (directory / INNER_NAME).write_bytes(b"tampered")
    result = run_verifier(
        "--directory",
        str(directory),
        "--expected-sha256",
        digest,
        "--expected-version",
        VERSION,
        "--expected-architecture",
        ARCH,
    )
    assert result.returncode == 1
    assert "inner ZIP SHA mismatch" in result.stdout


def write_outer_zip(directory: Path, archive_path: Path, *, nfd_names: bool = False, command_executable: bool = True) -> None:
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        root = directory.name
        for path in directory.iterdir():
            root_name = unicodedata.normalize("NFD", root) if nfd_names else root
            file_name = unicodedata.normalize("NFD", path.name) if nfd_names else path.name
            info = zipfile.ZipInfo(f"{root_name}/{file_name}")
            mode = path.stat().st_mode
            if path.name == COMMAND_NAME and not command_executable:
                mode &= ~stat.S_IXUSR
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def test_outer_zip_must_preserve_command_executable_bit(tmp_path):
    directory, digest = build_distribution_dir(tmp_path)
    archive_path = tmp_path / "outer.zip"
    write_outer_zip(directory, archive_path)
    result = run_verifier(
        "--zip",
        str(archive_path),
        "--expected-sha256",
        digest,
        "--expected-version",
        VERSION,
        "--expected-architecture",
        ARCH,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    broken = tmp_path / "outer-no-exec.zip"
    write_outer_zip(directory, broken, command_executable=False)
    result = run_verifier(
        "--zip",
        str(broken),
        "--expected-sha256",
        digest,
        "--expected-version",
        VERSION,
        "--expected-architecture",
        ARCH,
    )
    assert result.returncode == 1
    assert "does not preserve bootstrap executable bit" in result.stdout


def test_outer_zip_accepts_macos_nfd_filename_normalization(tmp_path):
    directory, digest = build_distribution_dir(tmp_path)
    archive_path = tmp_path / "outer-nfd.zip"
    write_outer_zip(directory, archive_path, nfd_names=True)
    result = run_verifier(
        "--zip",
        str(archive_path),
        "--expected-sha256",
        digest,
        "--expected-version",
        VERSION,
        "--expected-architecture",
        ARCH,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_packager_wraps_but_does_not_redefine_canonical_product_package():
    text = PACKAGER.read_text(encoding="utf-8")
    assert 'bash "$SCRIPT_DIR/package_macos.sh"' in text
    assert 'INNER_ZIP="$OUTPUT_DIR/CosmeticWorkshopOS-mac.zip"' in text
    assert "shasum -a 256" in text
    assert "single_client_bootstrap.command.template" in text
    assert "verify_single_client_package.py" in text
    assert "ditto -c -k --sequesterRsrc --keepParent" in text
    assert "codesign" not in text
    assert "notarytool" not in text
