from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import stat
import sys
import zipfile

SCRIPT_NAME = "operator_install_update.sh"
INNER_NAME = "CosmeticWorkshopOS-mac.zip"
README_NAME = "OPERATOR-README.txt"


def fail(message: str) -> None:
    print(f"Operator-assisted package verification: FAIL — {message}")
    raise SystemExit(1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_script(text: str, *, digest: str, version: str, arch: str) -> None:
    required = (
        f'EXPECTED_SHA256="{digest}"',
        f'EXPECTED_VERSION="{version}"',
        f'EXPECTED_ARCH="{arch}"',
        'EXPECTED_BUNDLE_ID="ru.cosmetic-workshop-os.app"',
        'INSTALL_DIR="$HOME/Applications"',
        '"$XATTR" -dr com.apple.quarantine "$CANDIDATE_APP"',
        'tell application id "ru.cosmetic-workshop-os.app" to quit',
        'previous-apps',
        'D4',
    )
    for needle in required:
        if needle not in text:
            fail(f"operator script missing required contract: {needle}")

    for unresolved in ("__INNER_SHA256__", "__APP_VERSION__", "__ARCHITECTURE__"):
        if unresolved in text:
            fail(f"operator script contains unresolved placeholder {unresolved}")

    lowered = text.casefold()
    forbidden = (
        "spctl --master-disable",
        "spctl --global-disable",
        "csrutil disable",
        "sudo ",
        "xattr -cr",
        "/applications/cosmeticworkshopos.app",
        "schema_migrations",
        "update-journal.json",
        "before_migration",
        "cosmetic_workshop.sqlite",
        "killall ",
        "pkill ",
    )
    for needle in forbidden:
        if needle in lowered:
            fail(f"operator script contains forbidden behavior: {needle}")

    sha_gate = text.index('[[ "$ACTUAL_SHA256" == "$EXPECTED_SHA256" ]]')
    bundle_gate = text.index('[[ "$BUNDLE_ID" == "$EXPECTED_BUNDLE_ID" ]]')
    version_gate = text.index('[[ "$VERSION" == "$EXPECTED_VERSION" ]]')
    executable_gate = text.index('[[ "$EXECUTABLE_NAME" == "$EXPECTED_EXECUTABLE" ]]')
    arch_gate = text.index('if [[ "$EXPECTED_ARCH" == "arm64" ]]')
    first_xattr = text.index('"$XATTR" -dr com.apple.quarantine "$CANDIDATE_APP"')
    quit_request = text.index('tell application id "ru.cosmetic-workshop-os.app" to quit')
    previous_backup = text.index('PREVIOUS_BACKUP="$BACKUP_DIR/')
    publication = text.index('"$MV" "$TEMP_DEST" "$DEST_APP"')

    if not (sha_gate < bundle_gate < version_gate < executable_gate < arch_gate < first_xattr):
        fail("quarantine removal is not strictly below all package identity gates")
    if not (first_xattr < quit_request < previous_backup < publication):
        fail("replacement ordering is not verify → quarantine → normal Quit → retain previous → publish")

    if text.count(' -dr com.apple.quarantine ') != 1:
        fail("operator script must contain exactly one recursive quarantine-removal command")


def verify_payload(
    *, script_bytes: bytes, inner_bytes: bytes, readme_bytes: bytes, script_mode: int | None,
    digest: str, version: str, arch: str,
) -> None:
    actual = sha256_bytes(inner_bytes)
    if actual != digest:
        fail(f"inner ZIP SHA mismatch: expected {digest}, got {actual}")
    try:
        text = script_bytes.decode("utf-8")
        readme = readme_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"support text is not UTF-8: {exc}")
    verify_script(text, digest=digest, version=version, arch=arch)
    for needle in (version, arch, digest, "support-оператор", "Gatekeeper"):
        if needle not in readme:
            fail(f"operator README missing {needle!r}")
    if script_mode is not None and not (script_mode & stat.S_IXUSR):
        fail("operator script executable bit was not preserved")


def verify_directory(path: Path, *, digest: str, version: str, arch: str) -> None:
    if not path.is_dir():
        fail(f"directory not found: {path}")
    names = {item.name for item in path.iterdir() if not item.name.startswith("._")}
    expected = {SCRIPT_NAME, INNER_NAME, README_NAME}
    if names != expected:
        fail(f"operator directory must contain exactly {sorted(expected)}, got {sorted(names)}")
    script = path / SCRIPT_NAME
    verify_payload(
        script_bytes=script.read_bytes(),
        inner_bytes=(path / INNER_NAME).read_bytes(),
        readme_bytes=(path / README_NAME).read_bytes(),
        script_mode=script.stat().st_mode,
        digest=digest,
        version=version,
        arch=arch,
    )


def verify_zip(path: Path, *, digest: str, version: str, arch: str) -> None:
    if not path.is_file():
        fail(f"ZIP not found: {path}")
    with zipfile.ZipFile(path) as archive:
        infos = [
            info for info in archive.infolist()
            if not info.is_dir() and not info.filename.startswith("__MACOSX/") and "/._" not in info.filename
        ]
        by_basename: dict[str, list[zipfile.ZipInfo]] = {}
        for info in infos:
            by_basename.setdefault(Path(info.filename).name, []).append(info)
        for name in (SCRIPT_NAME, INNER_NAME, README_NAME):
            if len(by_basename.get(name, [])) != 1:
                fail(f"outer ZIP must contain exactly one real {name}")
        allowed = {SCRIPT_NAME, INNER_NAME, README_NAME}
        unexpected = sorted(Path(info.filename).name for info in infos if Path(info.filename).name not in allowed)
        if unexpected:
            fail(f"outer ZIP contains unexpected real files: {unexpected}")
        script_info = by_basename[SCRIPT_NAME][0]
        mode = (script_info.external_attr >> 16) & 0xFFFF
        verify_payload(
            script_bytes=archive.read(script_info),
            inner_bytes=archive.read(by_basename[INNER_NAME][0]),
            readme_bytes=archive.read(by_basename[README_NAME][0]),
            script_mode=mode,
            digest=digest,
            version=version,
            arch=arch,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--directory", type=Path)
    group.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-architecture", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    digest = args.expected_sha256.lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        fail("expected SHA-256 is not a 64-character lowercase hex digest")
    if args.directory:
        verify_directory(args.directory, digest=digest, version=args.expected_version, arch=args.expected_architecture)
    else:
        verify_zip(args.zip_path, digest=digest, version=args.expected_version, arch=args.expected_architecture)
    print("Operator-assisted package verification: PASS")


if __name__ == "__main__":
    main()
