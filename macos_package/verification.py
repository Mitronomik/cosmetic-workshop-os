"""Prove a built `.app` / ZIP contains what it must — and nothing it must not.

Two questions, and the second matters at least as much as the first:

```text
is everything the product needs actually in there?
is anything that must never ship in there too?
```

The second is why this exists as a gate rather than as a checklist. The
realistic packaging accident is not a forgotten file — that fails loudly on
first launch. It is a `cp -R` that swept up the developer's `.local/`
database, a `node_modules/`, a `.git/`, or the `backups/` directory of a real
workshop. None of those stops the application from starting, so nothing else
would ever notice, and the artifact gets distributed with somebody's client
records inside it.

Everything here is a pure filesystem/zip inspection with no imports from the
product, no subprocesses and no network, so it is deterministic and runs
identically against a real build and against the synthetic fixtures the tests
construct. It is a structure gate, not a substitute for live package smoke: it
proves what the artifact contains, never that it runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import plistlib
import re
import stat
import zipfile

APP_BUNDLE_NAME = "CosmeticWorkshopOS.app"
ZIP_NAME = "CosmeticWorkshopOS-mac.zip"
BUNDLE_EXECUTABLE_NAME = "CosmeticWorkshopOS"
BUNDLE_DISPLAY_NAME = "Мастерская косметолога"
PACKAGE_MANIFEST_NAME = "package-runtime.json"

# A user database, a real backup or an exported dataset inside a distributable
# artifact is a privacy incident, not a packaging defect. Matched by suffix
# anywhere in the bundle.
FORBIDDEN_SUFFIXES = (".sqlite", ".sqlite3", ".db")

# Directory names that must not appear anywhere in the artifact, including
# inside the bundled interpreter. Every name here is one that a correctly built
# Python distribution never contains.
FORBIDDEN_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        ".local",
        "dist-tests",
    }
)

# Directory names forbidden only under the packaged **application** root.
#
# `backups`, `exports`, `attachments` and `logs` are the user-data directories
# the backend creates *outside* the package, so finding one here means real user
# data was copied in.
#
# `tests` and `venv` are scoped rather than banned outright because a genuine
# CPython distribution contains both legitimately: third-party libraries ship
# their own test packages, and `venv` is a standard-library module. Failing a
# build on those would be a false alarm, and a gate that cries wolf is a gate
# people learn to bypass.
FORBIDDEN_APPLICATION_DIRECTORY_NAMES = frozenset(
    {"tests", "venv", "backups", "exports", "attachments", "logs"}
)

# Never legitimate anywhere in a built artifact, interpreter included.
FORBIDDEN_FILE_PATTERNS = (
    re.compile(r"^\.git.*$"),
    re.compile(r"^\.DS_Store$"),
)

# Credential-shaped files, checked only under the packaged **application** root.
#
# This is where a stray developer file would actually arrive: the application
# root is assembled by copying from the working tree, so an `.env` or a private
# key left lying around is a real risk there. The bundled interpreter is built
# from a checksum-verified upstream archive plus wheels from PyPI and never
# receives anything from the working tree — and it legitimately carries CA trust
# stores such as `pip/_vendor/certifi/cacert.pem`, which are not secrets.
FORBIDDEN_APPLICATION_FILE_PATTERNS = (
    re.compile(r"^\.env(\..+)?$"),
    re.compile(r"^\.netrc$"),
    re.compile(r"^id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$"),
    re.compile(r".*\.(pem|key|p12|pfx|keystore)$"),
    re.compile(r"^credentials(\..+)?$"),
)

# Required product material, relative to `Contents/Resources/app`.
REQUIRED_APPLICATION_FILES = (
    "launcher/main.py",
    "launcher/config.py",
    "launcher/runtime.py",
    "launcher/restore/engine.py",
    "launcher/restore/control_plane.py",
    "launcher/restore/macos_picker.py",
    "backend/app/main.py",
    "backend/app/launcher_backend_entrypoint.py",
    "backend/app/db/migrations.py",
    "backend/app/services/startup.py",
    "backend/app/services/backend_liveness.py",
    "macos_package/entrypoint.py",
    "macos_package/frontend_server.py",
    "frontend/dist/index.html",
    PACKAGE_MANIFEST_NAME,
)


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class PackageVerificationResult:
    app_path: Path
    zip_path: Path | None = None
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [check for check in self.checks if not check.ok]

    def report(self) -> str:
        lines = [f"{'PASS' if check.ok else 'FAIL'}  {check.name}" for check in self.checks]
        for check in self.failures:
            lines.append(f"  - {check.name}: {check.detail}")
        lines.append(
            "Package structure verification: "
            + ("PASS" if self.ok else f"FAIL ({len(self.failures)} failing checks)")
        )
        return "\n".join(lines)


def verify_package(
    app_path: Path, zip_path: Path | None = None, *, source_root: Path | None = None
) -> PackageVerificationResult:
    """Run every structural check against one built artifact.

    `source_root` is the repository the artifact was built from. When supplied,
    the packaged text files are searched for that absolute path: a package that
    still names the checkout it came from is a package that may be depending on
    it, and the exact-package verification this artifact exists for would then
    be testing the wrong thing.
    """
    result = PackageVerificationResult(app_path=app_path, zip_path=zip_path)
    checks = result.checks

    if not app_path.is_dir():
        checks.append(Check("app_bundle_exists", False, f"no app bundle at {app_path}"))
        return result
    checks.append(Check("app_bundle_exists", True))

    contents = app_path / "Contents"
    resources = contents / "Resources"
    application_root = resources / "app"

    checks.append(_check_info_plist(contents / "Info.plist"))
    checks.append(_check_bundle_executable(contents / "MacOS" / BUNDLE_EXECUTABLE_NAME))
    checks.append(_check_bundled_runtime(resources / "runtime"))
    checks.extend(_check_required_files(application_root))
    checks.append(_check_frontend_assets(application_root / "frontend" / "dist"))
    checks.append(_check_help_resources(application_root / "help"))
    checks.append(_check_packaged_migrations(application_root))
    checks.append(_check_manifest(application_root / PACKAGE_MANIFEST_NAME))
    checks.extend(_check_no_forbidden_content(app_path))
    checks.append(_check_no_source_root_reference(application_root, contents, source_root))

    if zip_path is not None:
        checks.extend(_check_zip(zip_path))

    return result


# -- bundle metadata and runtime -----------------------------------------


def _check_info_plist(plist_path: Path) -> Check:
    if not plist_path.is_file():
        return Check("info_plist", False, "Contents/Info.plist is missing")
    try:
        plist = plistlib.loads(plist_path.read_bytes())
    except Exception as exc:  # noqa: BLE001 - any parse failure is the same verdict
        return Check("info_plist", False, f"Info.plist is unreadable: {exc!r}")
    if plist.get("CFBundleExecutable") != BUNDLE_EXECUTABLE_NAME:
        return Check(
            "info_plist",
            False,
            f"CFBundleExecutable is {plist.get('CFBundleExecutable')!r}, "
            f"expected {BUNDLE_EXECUTABLE_NAME!r}",
        )
    if plist.get("CFBundleDisplayName") != BUNDLE_DISPLAY_NAME:
        return Check(
            "info_plist",
            False,
            "CFBundleDisplayName must carry the human-facing product name",
        )
    if plist.get("CFBundlePackageType") != "APPL":
        return Check("info_plist", False, "CFBundlePackageType must be APPL")
    return Check("info_plist", True)


def _check_bundle_executable(executable_path: Path) -> Check:
    if not executable_path.is_file():
        return Check(
            "bundle_executable",
            False,
            f"Contents/MacOS/{BUNDLE_EXECUTABLE_NAME} is missing",
        )
    mode = executable_path.stat().st_mode
    if not mode & stat.S_IXUSR:
        return Check(
            "bundle_executable", False, "the bundle executable is not marked executable"
        )
    return Check("bundle_executable", True)


def _check_bundled_runtime(runtime_dir: Path) -> Check:
    """A self-contained interpreter must be present and runnable in place.

    Presence is checked structurally, not by execution: this module must stay a
    pure inspection, and running the bundled binary is the live smoke's job.
    """
    if not runtime_dir.is_dir():
        return Check("bundled_runtime", False, "Contents/Resources/runtime is missing")
    binaries = [
        candidate
        for candidate in (runtime_dir / "bin").glob("python3*")
        if candidate.is_file() and candidate.stat().st_mode & stat.S_IXUSR
    ]
    if not binaries:
        return Check(
            "bundled_runtime",
            False,
            "no executable python3 interpreter under Contents/Resources/runtime/bin",
        )
    if not any((runtime_dir / "lib").glob("python3*")):
        return Check(
            "bundled_runtime", False, "the bundled runtime has no standard library"
        )
    return Check("bundled_runtime", True)


def _check_required_files(application_root: Path) -> list[Check]:
    missing = [
        relative
        for relative in REQUIRED_APPLICATION_FILES
        if not (application_root / relative).is_file()
    ]
    if missing:
        return [Check("required_application_files", False, f"missing: {', '.join(missing)}")]
    return [Check("required_application_files", True)]


def _check_frontend_assets(dist_dir: Path) -> Check:
    assets = dist_dir / "assets"
    if not assets.is_dir():
        return Check("frontend_production_assets", False, "frontend/dist/assets is missing")
    scripts = list(assets.glob("*.js"))
    styles = list(assets.glob("*.css"))
    if not scripts or not styles:
        return Check(
            "frontend_production_assets",
            False,
            f"production build incomplete: {len(scripts)} js, {len(styles)} css",
        )
    return Check("frontend_production_assets", True)


def _check_help_resources(help_dir: Path) -> Check:
    if not help_dir.is_dir():
        return Check("offline_help_resources", False, "help/ is missing from the package")
    documents = [
        candidate
        for candidate in help_dir.glob("*.md")
        if candidate.name != "AGENTS.md" and candidate.stat().st_size > 0
    ]
    if not documents:
        return Check("offline_help_resources", False, "help/ contains no help documents")
    return Check("offline_help_resources", True)


def _check_packaged_migrations(application_root: Path) -> Check:
    """Every migration the packaged backend declares must be packaged with it.

    The list is read out of the packaged `migrations.py` itself rather than
    imported from the repository, so the check compares the artifact against its
    own declaration. A package whose migration registry names a module it does
    not carry would fail at first launch on a fresh database — after the user
    data directory had already been created.
    """
    registry = application_root / "backend" / "app" / "db" / "migrations.py"
    if not registry.is_file():
        return Check("packaged_migrations", False, "backend/app/db/migrations.py is missing")
    module_names = re.findall(
        r'"(app\.migrations\.versions\.[0-9A-Za-z_]+)"', registry.read_text(encoding="utf-8")
    )
    if not module_names:
        return Check("packaged_migrations", False, "no migration modules are declared")
    missing = [
        name
        for name in module_names
        if not (application_root / "backend" / Path(*name.split("."))).with_suffix(".py").is_file()
    ]
    if missing:
        return Check("packaged_migrations", False, f"missing migration modules: {missing}")
    return Check("packaged_migrations", True, f"{len(module_names)} migrations packaged")


def _check_manifest(manifest_path: Path) -> Check:
    if not manifest_path.is_file():
        return Check("package_manifest", False, f"{PACKAGE_MANIFEST_NAME} is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return Check("package_manifest", False, f"unparseable manifest: {exc}")
    required_keys = ("python_version", "architecture", "runtime_root_relative_to_app")
    missing = [key for key in required_keys if not manifest.get(key)]
    if missing:
        return Check("package_manifest", False, f"manifest is missing keys: {missing}")
    return Check(
        "package_manifest",
        True,
        f"python {manifest['python_version']} / {manifest['architecture']}",
    )


# -- exclusions -----------------------------------------------------------


def _check_no_forbidden_content(app_path: Path) -> list[Check]:
    """Walk the whole bundle once, collecting every kind of violation.

    One walk rather than several, and every violation kind reported from it, so
    a build that has two problems is not fixed one launch at a time.
    """
    databases: list[str] = []
    directories: list[str] = []
    developer_files: list[str] = []
    application_prefix = "Contents/Resources/app/"

    for path in app_path.rglob("*"):
        relative = path.relative_to(app_path).as_posix()
        if path.is_dir():
            if path.name in FORBIDDEN_DIRECTORY_NAMES:
                directories.append(relative)
            elif (
                relative.startswith(application_prefix)
                and path.name in FORBIDDEN_APPLICATION_DIRECTORY_NAMES
            ):
                directories.append(relative)
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            databases.append(relative)
        if any(pattern.match(path.name) for pattern in FORBIDDEN_FILE_PATTERNS):
            developer_files.append(relative)
        elif relative.startswith(application_prefix) and any(
            pattern.match(path.name) for pattern in FORBIDDEN_APPLICATION_FILE_PATTERNS
        ):
            developer_files.append(relative)

    return [
        Check(
            "no_user_database",
            not databases,
            f"database-like files in the package: {databases[:10]}",
        ),
        Check(
            "no_forbidden_directories",
            not directories,
            f"forbidden directories in the package: {directories[:10]}",
        ),
        Check(
            "no_developer_or_secret_files",
            not developer_files,
            f"developer/secret-looking files in the package: {developer_files[:10]}",
        ),
    ]


def _check_no_source_root_reference(
    application_root: Path, contents: Path, source_root: Path | None
) -> Check:
    """The package must not name the checkout it was built from.

    Skipped, and reported as skipped, when no source root is supplied — a check
    that silently passes because it had nothing to compare against is worse than
    no check at all.
    """
    if source_root is None:
        return Check("no_source_repository_reference", True, "skipped: no source root supplied")
    needle = str(source_root.resolve())
    offenders: list[str] = []
    candidates = [contents / "Info.plist", contents / "MacOS" / BUNDLE_EXECUTABLE_NAME]
    candidates.extend(
        path
        for path in application_root.rglob("*")
        if path.is_file() and path.suffix in (".py", ".json", ".html", ".js", ".css", ".plist", ".sh")
    )
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if needle in text:
            offenders.append(str(path))
    if offenders:
        return Check(
            "no_source_repository_reference",
            False,
            f"packaged files reference the build checkout: {offenders[:5]}",
        )
    return Check("no_source_repository_reference", True)


# -- zip ------------------------------------------------------------------


def _check_zip(zip_path: Path) -> list[Check]:
    if not zip_path.is_file():
        return [Check("zip_exists", False, f"no archive at {zip_path}")]
    checks = [Check("zip_exists", True)]
    try:
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            executable_entry = f"{APP_BUNDLE_NAME}/Contents/MacOS/{BUNDLE_EXECUTABLE_NAME}"
            checks.append(
                Check(
                    "zip_contains_app_bundle",
                    any(name.startswith(f"{APP_BUNDLE_NAME}/") for name in names),
                    f"{APP_BUNDLE_NAME}/ is not the archive root entry",
                )
            )
            info = next((item for item in archive.infolist() if item.filename == executable_entry), None)
            checks.append(
                Check(
                    "zip_executable_bit_preserved",
                    info is not None and bool((info.external_attr >> 16) & stat.S_IXUSR),
                    "the app executable loses its executable bit through the archive",
                )
            )
            application_prefix = f"{APP_BUNDLE_NAME}/Contents/Resources/app/"
            offenders = [
                name
                for name in names
                if Path(name).suffix.lower() in FORBIDDEN_SUFFIXES
                or any(part in FORBIDDEN_DIRECTORY_NAMES for part in Path(name).parts[:-1])
                or any(pattern.match(Path(name).name) for pattern in FORBIDDEN_FILE_PATTERNS)
                or (
                    name.startswith(application_prefix)
                    and (
                        any(
                            part in FORBIDDEN_APPLICATION_DIRECTORY_NAMES
                            for part in Path(name).parts[:-1]
                        )
                        or any(
                            pattern.match(Path(name).name)
                            for pattern in FORBIDDEN_APPLICATION_FILE_PATTERNS
                        )
                    )
                )
            ]
            checks.append(
                Check(
                    "zip_excludes_forbidden_content",
                    not offenders,
                    f"forbidden archive entries: {offenders[:10]}",
                )
            )
    except zipfile.BadZipFile as exc:
        checks.append(Check("zip_readable", False, f"unreadable archive: {exc}"))
    return checks
