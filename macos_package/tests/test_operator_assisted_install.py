from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "scripts" / "macos" / "operator_install_update.sh.template"
PACKAGER = ROOT / "scripts" / "package_operator_assisted_macos.sh"
VERIFIER = ROOT / "scripts" / "verify_operator_assisted_package.py"
MAKEFILE = ROOT / "Makefile"
SCRIPT_NAME = "operator_install_update.sh"
INNER_NAME = "CosmeticWorkshopOS-mac.zip"
README_NAME = "OPERATOR-README.txt"
VERSION = "0.1.0"
ARCH = "arm64"


def rendered_operator(inner_bytes: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(inner_bytes).hexdigest()
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("__INNER_SHA256__", digest)
    text = text.replace("__APP_VERSION__", VERSION)
    text = text.replace("__ARCHITECTURE__", ARCH)
    return text, digest


def build_dir(tmp_path: Path) -> tuple[Path, str]:
    inner = b"canonical-product-zip-fixture"
    script_text, digest = rendered_operator(inner)
    directory = tmp_path / "CosmeticWorkshopOS-operator-assisted-0.1.0-arm64"
    directory.mkdir()
    script = directory / SCRIPT_NAME
    script.write_text(script_text, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    (directory / INNER_NAME).write_bytes(inner)
    (directory / README_NAME).write_text(
        f"support-оператор\nGatekeeper\n{VERSION}\n{ARCH}\n{digest}\n", encoding="utf-8"
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


def verifier_args(path: Path, digest: str, *, as_zip: bool = False) -> tuple[str, ...]:
    return (
        "--zip" if as_zip else "--directory",
        str(path),
        "--expected-sha256",
        digest,
        "--expected-version",
        VERSION,
        "--expected-architecture",
        ARCH,
    )


def write_outer_zip(directory: Path, path: Path, *, executable: bool = True) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in directory.iterdir():
            info = zipfile.ZipInfo(f"{directory.name}/{item.name}")
            mode = item.stat().st_mode
            if item.name == SCRIPT_NAME and not executable:
                mode &= ~stat.S_IXUSR
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, item.read_bytes())


def test_operator_template_is_fail_closed_before_quarantine_removal():
    text = TEMPLATE.read_text(encoding="utf-8")
    sha_gate = text.index('[[ "$ACTUAL_SHA256" == "$EXPECTED_SHA256" ]]')
    bundle_gate = text.index('[[ "$BUNDLE_ID" == "$EXPECTED_BUNDLE_ID" ]]')
    version_gate = text.index('[[ "$VERSION" == "$EXPECTED_VERSION" ]]')
    executable_gate = text.index('[[ "$EXECUTABLE_NAME" == "$EXPECTED_EXECUTABLE" ]]')
    arch_gate = text.index('if [[ "$EXPECTED_ARCH" == "arm64" ]]')
    first_xattr = text.index('"$XATTR" -dr com.apple.quarantine "$CANDIDATE_APP"')
    quit_request = text.index('tell application id "ru.cosmetic-workshop-os.app" to quit')
    backup = text.index('PREVIOUS_BACKUP="$BACKUP_DIR/')
    publication = text.index('"$MV" "$TEMP_DEST" "$DEST_APP"')
    assert sha_gate < bundle_gate < version_gate < executable_gate < arch_gate < first_xattr
    assert first_xattr < quit_request < backup < publication
    assert text.count(' -dr com.apple.quarantine ') == 1


def test_operator_template_preserves_security_boundary():
    text = TEMPLATE.read_text(encoding="utf-8").casefold()
    for forbidden in (
        "spctl --master-disable",
        "spctl --global-disable",
        "csrutil disable",
        "sudo ",
        "xattr -cr",
        "/applications/cosmeticworkshopos.app",
        "killall ",
        "pkill ",
    ):
        assert forbidden not in text
    assert 'install_dir="$home/applications"' in text
    assert '"$xattr" -dr com.apple.quarantine "$candidate_app"' in text
    assert 'tell application id "ru.cosmetic-workshop-os.app" to quit' in text


def test_operator_template_does_not_take_database_or_d4_ownership():
    text = TEMPLATE.read_text(encoding="utf-8")
    for forbidden in (
        "cosmetic_workshop.sqlite",
        "schema_migrations",
        "update-journal.json",
        "before_migration",
    ):
        assert forbidden not in text
    assert "D4/recovery guidance" in text


def test_directory_verifier_accepts_matching_operator_bundle(tmp_path):
    directory, digest = build_dir(tmp_path)
    result = run_verifier(*verifier_args(directory, digest))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Operator-assisted package verification: PASS" in result.stdout


def test_directory_verifier_rejects_inner_zip_mismatch(tmp_path):
    directory, digest = build_dir(tmp_path)
    (directory / INNER_NAME).write_bytes(b"tampered")
    result = run_verifier(*verifier_args(directory, digest))
    assert result.returncode == 1
    assert "inner ZIP SHA mismatch" in result.stdout


def test_outer_zip_requires_script_executable_bit(tmp_path):
    directory, digest = build_dir(tmp_path)
    good = tmp_path / "good.zip"
    write_outer_zip(directory, good)
    result = run_verifier(*verifier_args(good, digest, as_zip=True))
    assert result.returncode == 0, result.stdout + result.stderr

    bad = tmp_path / "bad.zip"
    write_outer_zip(directory, bad, executable=False)
    result = run_verifier(*verifier_args(bad, digest, as_zip=True))
    assert result.returncode == 1
    assert "executable bit" in result.stdout


def test_packager_wraps_canonical_package_instead_of_redefining_it():
    text = PACKAGER.read_text(encoding="utf-8")
    assert 'bash "$SCRIPT_DIR/package_macos.sh"' in text
    assert 'INNER_ZIP="$OUTPUT_DIR/CosmeticWorkshopOS-mac.zip"' in text
    assert "shasum -a 256" in text
    assert "operator_install_update.sh.template" in text
    assert "verify_operator_assisted_package.py" in text
    assert "package_single_client_macos.sh" not in text


def test_makefile_exposes_bounded_operator_package_target():
    text = MAKEFILE.read_text(encoding="utf-8")
    assert "package-operator-assisted-macos:" in text
    assert "bash scripts/package_operator_assisted_macos.sh" in text
