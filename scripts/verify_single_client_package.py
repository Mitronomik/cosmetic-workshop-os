#!/usr/bin/env python3
"""Fail-closed structural verifier for the CR-016 one-client outer ZIP.

This verifier deliberately does not execute the downloaded `.command`. Its job is
artifact identity and security-order inspection. Real Finder → Terminal handoff
remains a mandatory human clean-Mac rehearsal.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import stat
import unicodedata
import zipfile

COMMAND_NAME = "Установить или обновить Мастерскую.command"
INNER_ZIP_NAME = "CosmeticWorkshopOS-mac.zip"
README_NAME = "Прочтите меня.txt"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_basename(value: str) -> str:
    """Normalize a decoded ZIP basename for extension/exact-ASCII comparison."""
    return unicodedata.normalize("NFC", PurePosixPath(value).name)


def is_appledouble(info: zipfile.ZipInfo) -> bool:
    """Ignore only metadata sidecars created by macOS `ditto --sequesterRsrc`."""
    parts = PurePosixPath(info.filename).parts
    base = normalized_basename(info.filename)
    return "__MACOSX" in parts or base.startswith("._")


def verify_command(
    text: str, *, expected_sha256: str, expected_version: str, expected_arch: str
) -> list[str]:
    errors: list[str] = []
    required = (
        "#!/bin/zsh",
        f'EXPECTED_SHA256="{expected_sha256}"',
        f'EXPECTED_VERSION="{expected_version}"',
        f'EXPECTED_ARCH="{expected_arch}"',
        'EXPECTED_BUNDLE_ID="ru.cosmetic-workshop-os.app"',
        'INSTALL_DIR="$HOME/Applications"',
        "ACTUAL_SHA256=",
        '[[ "$ACTUAL_SHA256" == "$EXPECTED_SHA256" ]]',
        'CANDIDATE_APP="$STAGE_DIR/CosmeticWorkshopOS.app"',
        "Print :CFBundleIdentifier",
        "Print :CFBundleShortVersionString",
        "Print :CFBundleExecutable",
        '"$PGREP" -x CosmeticWorkshopOS',
        '"$DITTO" "$DEST_APP" "$PREVIOUS_BACKUP"',
        '"$XATTR" -dr com.apple.quarantine "$CANDIDATE_APP"',
        '"$XATTR" -dr com.apple.quarantine "$DEST_APP"',
        '"$OPEN" "$DEST_APP"',
    )
    for needle in required:
        if needle not in text:
            errors.append(f"bootstrap missing required contract: {needle}")

    forbidden = (
        "spctl --master-disable",
        "spctl --global-disable",
        "csrutil disable",
        "sudo ",
        "sudo\t",
        "xattr -cr",
        "xattr -c ",
        "/Applications/CosmeticWorkshopOS.app",
        "curl ",
        "wget ",
        "git clone",
    )
    lowered = text.casefold()
    for needle in forbidden:
        if needle.casefold() in lowered:
            errors.append(f"bootstrap contains forbidden operation: {needle}")

    for placeholder in ("__INNER_SHA256__", "__APP_VERSION__", "__ARCHITECTURE__"):
        if placeholder in text:
            errors.append(f"bootstrap contains unresolved placeholder: {placeholder}")

    checkpoints = {
        "sha_compare": '[[ "$ACTUAL_SHA256" == "$EXPECTED_SHA256" ]]',
        "bundle_id_compare": '[[ "$BUNDLE_ID" == "$EXPECTED_BUNDLE_ID" ]]',
        "version_compare": '[[ "$VERSION" == "$EXPECTED_VERSION" ]]',
        "executable_compare": '[[ "$EXECUTABLE_NAME" == "$EXPECTED_EXECUTABLE" ]]',
        "architecture_gate": 'if [[ "$EXPECTED_ARCH" == "arm64" ]]',
        "first_xattr": '"$XATTR" -dr com.apple.quarantine "$CANDIDATE_APP"',
        "running_guard": '"$PGREP" -x CosmeticWorkshopOS',
        "prepare_destination": 'TEMP_DEST="$INSTALL_DIR/.CosmeticWorkshopOS.installing.$$.app"',
        "backup": '"$DITTO" "$DEST_APP" "$PREVIOUS_BACKUP"',
        "replace": '"$MV" "$DEST_APP" "$OLD_HOLD"',
        "launch": '"$OPEN" "$DEST_APP"',
    }
    positions: dict[str, int] = {}
    for name, needle in checkpoints.items():
        position = text.find(needle)
        if position < 0:
            errors.append(f"bootstrap ordering checkpoint missing: {name}")
        positions[name] = position

    first_gate_names = (
        "sha_compare",
        "bundle_id_compare",
        "version_compare",
        "executable_compare",
        "architecture_gate",
        "first_xattr",
    )
    if all(positions[name] >= 0 for name in first_gate_names):
        if not (
            positions["sha_compare"]
            < positions["bundle_id_compare"]
            < positions["version_compare"]
            < positions["executable_compare"]
            < positions["architecture_gate"]
            < positions["first_xattr"]
        ):
            errors.append(
                "quarantine removal is not ordered after all candidate verification gates"
            )

    publication_names = (
        "first_xattr",
        "running_guard",
        "prepare_destination",
        "backup",
        "replace",
        "launch",
    )
    if all(positions[name] >= 0 for name in publication_names):
        if not (
            positions["first_xattr"]
            < positions["running_guard"]
            < positions["prepare_destination"]
            < positions["backup"]
            < positions["replace"]
            < positions["launch"]
        ):
            errors.append(
                "update publication order does not preserve verify → guard → stage → backup → replace → launch"
            )

    for needle in (
        "cosmetic_workshop.sqlite",
        "schema_migrations",
        "update-journal.json",
        "before_migration",
    ):
        if needle in text:
            errors.append(f"bootstrap reaches into product data/update semantics: {needle}")

    return errors


def verify_readme(
    text: str, *, expected_sha256: str, expected_version: str, expected_arch: str
) -> list[str]:
    errors: list[str] = []
    for token in (expected_sha256, expected_version, expected_arch, COMMAND_NAME):
        if token not in text:
            errors.append(f"readme missing release identity token: {token}")
    return errors


def verify_directory(
    directory: Path, *, expected_sha256: str, expected_version: str, expected_arch: str
) -> list[str]:
    errors: list[str] = []
    command = directory / COMMAND_NAME
    inner_zip = directory / INNER_ZIP_NAME
    readme = directory / README_NAME
    for path in (command, inner_zip, readme):
        if not path.is_file():
            errors.append(f"missing distribution file: {path.name}")
    if errors:
        return errors

    if not command.stat().st_mode & stat.S_IXUSR:
        errors.append("bootstrap .command is not executable")
    actual = hashlib.sha256(inner_zip.read_bytes()).hexdigest()
    if actual != expected_sha256:
        errors.append(f"inner ZIP SHA mismatch: {actual}")
    errors.extend(
        verify_command(
            command.read_text(encoding="utf-8"),
            expected_sha256=expected_sha256,
            expected_version=expected_version,
            expected_arch=expected_arch,
        )
    )
    errors.extend(
        verify_readme(
            readme.read_text(encoding="utf-8"),
            expected_sha256=expected_sha256,
            expected_version=expected_version,
            expected_arch=expected_arch,
        )
    )
    return errors


def verify_zip(
    path: Path, *, expected_sha256: str, expected_version: str, expected_arch: str
) -> list[str]:
    """Verify the outer ZIP without trusting localized filename decoding.

    `ditto` can store localized filenames in a way Python's generic ZIP decoder
    renders differently from Finder. Filename spelling is therefore an UX
    property, not the release-identity boundary. The outer archive must carry:
    exactly one real `.command`, exactly one canonical ASCII inner product ZIP,
    and exactly one real `.txt` readme. AppleDouble sidecars are ignored. The
    command *contents* remain the security boundary and are fully verified.
    """
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            real_infos = [
                info
                for info in archive.infolist()
                if not info.is_dir() and not is_appledouble(info)
            ]
            command_infos = [
                info
                for info in real_infos
                if normalized_basename(info.filename).casefold().endswith(".command")
            ]
            inner_infos = [
                info
                for info in real_infos
                if normalized_basename(info.filename) == INNER_ZIP_NAME
            ]
            readme_infos = [
                info
                for info in real_infos
                if normalized_basename(info.filename).casefold().endswith(".txt")
            ]

            if len(command_infos) != 1:
                errors.append(
                    f"outer ZIP must contain exactly one real .command bootstrap; got {len(command_infos)}"
                )
            if len(inner_infos) != 1:
                errors.append(
                    f"outer ZIP must contain exactly one {INNER_ZIP_NAME}; got {len(inner_infos)}"
                )
            if len(readme_infos) != 1:
                errors.append(
                    f"outer ZIP must contain exactly one real .txt readme; got {len(readme_infos)}"
                )

            recognized_ids = {
                id(info)
                for info in command_infos + inner_infos + readme_infos
            }
            unexpected = [
                info.filename for info in real_infos if id(info) not in recognized_ids
            ]
            if unexpected:
                errors.append(f"outer ZIP contains unexpected real files: {unexpected[:10]}")

            if errors:
                decoded = [repr(info.filename) for info in real_infos[:20]]
                errors.append(f"decoded real outer ZIP entries: {decoded}")
                return errors

            command_info = command_infos[0]
            inner_info = inner_infos[0]
            readme_info = readme_infos[0]

            command_mode = command_info.external_attr >> 16
            if not command_mode & stat.S_IXUSR:
                errors.append("outer ZIP does not preserve bootstrap executable bit")

            inner_bytes = archive.read(inner_info)
            actual = sha256_bytes(inner_bytes)
            if actual != expected_sha256:
                errors.append(f"outer ZIP inner product SHA mismatch: {actual}")

            command_text = archive.read(command_info).decode("utf-8")
            errors.extend(
                verify_command(
                    command_text,
                    expected_sha256=expected_sha256,
                    expected_version=expected_version,
                    expected_arch=expected_arch,
                )
            )
            readme_text = archive.read(readme_info).decode("utf-8")
            errors.extend(
                verify_readme(
                    readme_text,
                    expected_sha256=expected_sha256,
                    expected_version=expected_version,
                    expected_arch=expected_arch,
                )
            )
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError) as exc:
        errors.append(f"outer ZIP unreadable: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--directory", type=Path)
    source.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-architecture", required=True)
    args = parser.parse_args()

    if len(args.expected_sha256) != 64 or any(
        ch not in "0123456789abcdef" for ch in args.expected_sha256
    ):
        print("Single-client distribution verification: FAIL")
        print("- expected SHA-256 is not a lowercase 64-hex digest")
        return 2

    kwargs = dict(
        expected_sha256=args.expected_sha256,
        expected_version=args.expected_version,
        expected_arch=args.expected_architecture,
    )
    if args.directory is not None:
        errors = verify_directory(args.directory, **kwargs)
    else:
        errors = verify_zip(args.zip_path, **kwargs)

    if errors:
        print("Single-client distribution verification: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Single-client distribution verification: PASS")
    print(f"version={args.expected_version}")
    print(f"architecture={args.expected_architecture}")
    print(f"inner_sha256={args.expected_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
