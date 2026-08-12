"""Resolve the packaged application's own resources — never a developer checkout.

Every path below is derived from this module's **own location on disk**, so the
same code answers the same question in both places it runs:

```text
source tree      <repo>/macos_package/package_paths.py   → application root <repo>
packaged product .../Resources/app/macos_package/…       → application root .../Resources/app
```

That is deliberately not a fallback. There is no "look for a repository if the
package looks incomplete" branch anywhere in this module, because a packaged
product that quietly starts serving a developer checkout would make every later
exact-package verification meaningless: the artifact under test would not be the
thing running. A package missing its own resources is a refusal
(:func:`missing_package_resources`), never a redirection.

The packaged build additionally writes :data:`PACKAGE_MANIFEST_NAME` next to the
application root. Its presence is what distinguishes "running from the package"
from "running from the source tree", and in the packaged case it lets the
entrypoint insist that the interpreter actually executing us lives **inside the
bundle** rather than being somebody's system Python.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys

# Written by `scripts/package_macos.sh` into the packaged application root. It
# is the package's own self-description: which Python was bundled, for which
# architecture, and where the bundled interpreter lives relative to the root.
PACKAGE_MANIFEST_NAME = "package-runtime.json"

# Relative locations inside the application root. The packaged layout mirrors
# the repository layout exactly, which is what lets `launcher/config.py`'s
# existing `parents[1]` resolution keep working untouched inside the bundle.
LAUNCHER_DIRNAME = "launcher"
BACKEND_DIRNAME = "backend"
FRONTEND_DIRNAME = "frontend"
HELP_DIRNAME = "help"
FRONTEND_DIST_RELATIVE = Path(FRONTEND_DIRNAME) / "dist"


@dataclass(frozen=True)
class PackageLayout:
    """Where the packaged product's parts are, relative to one resolved root."""

    application_root: Path
    manifest: dict | None

    @property
    def is_packaged(self) -> bool:
        """True only when this tree carries the build's own manifest.

        Used to decide *presentation*, not authority: a packaged run shows a
        macOS alert on a fatal startup refusal, a source run prints to the
        terminal a developer can actually see.
        """
        return self.manifest is not None

    @property
    def launcher_dir(self) -> Path:
        return self.application_root / LAUNCHER_DIRNAME

    @property
    def backend_dir(self) -> Path:
        return self.application_root / BACKEND_DIRNAME

    @property
    def backend_app_dir(self) -> Path:
        return self.backend_dir / "app"

    @property
    def frontend_dist_dir(self) -> Path:
        return self.application_root / FRONTEND_DIST_RELATIVE

    @property
    def frontend_index(self) -> Path:
        return self.frontend_dist_dir / "index.html"

    @property
    def help_dir(self) -> Path:
        return self.application_root / HELP_DIRNAME

    @property
    def bundled_runtime_dir(self) -> Path | None:
        """The bundled interpreter's root, as the build recorded it.

        `None` outside a package. Inside one it is resolved from the manifest
        rather than hard-coded here, so the build owns the layout and this
        module only reads it.
        """
        if self.manifest is None:
            return None
        relative = self.manifest.get("runtime_root_relative_to_app")
        if not isinstance(relative, str) or not relative:
            return None
        return (self.application_root / relative).resolve()


def resolve_package_layout(application_root: Path | None = None) -> PackageLayout:
    """Resolve the layout from this module's location, or from an explicit root.

    `application_root` exists for tests and for the structure verifier, which
    both need to point at a tree other than their own. Production callers pass
    nothing and get the tree this module physically lives in.
    """
    root = (application_root or Path(__file__).resolve().parents[1]).resolve()
    return PackageLayout(application_root=root, manifest=read_package_manifest(root))


def read_package_manifest(application_root: Path) -> dict | None:
    """Read the build manifest, or `None` when this is not a packaged tree.

    A manifest that exists but cannot be parsed returns `None` rather than
    raising: the caller's next question is "are the resources there?", and an
    unreadable manifest must not turn into a traceback in front of a user who
    only double-clicked an application.
    """
    manifest_path = application_root / PACKAGE_MANIFEST_NAME
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, OSError):
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def missing_package_resources(layout: PackageLayout) -> list[str]:
    """Name every packaged resource that is required and absent.

    Returned as identifiers rather than paths, and the caller keeps them out of
    the user-facing dialog: a non-technical user gains nothing from a filesystem
    path, and a path can carry a home directory into a screenshot. The list is
    for the terminal/log side and for tests.
    """
    missing: list[str] = []
    if not (layout.launcher_dir / "main.py").is_file():
        missing.append("launcher")
    if not (layout.backend_app_dir / "launcher_backend_entrypoint.py").is_file():
        missing.append("backend")
    if not layout.frontend_index.is_file():
        missing.append("frontend_index")
    if not _has_frontend_assets(layout.frontend_dist_dir):
        missing.append("frontend_assets")
    return missing


def _has_frontend_assets(dist_dir: Path) -> bool:
    """A production build is index.html **plus** its compiled assets.

    Checked separately from `index.html` because a half-copied `dist/` is the
    realistic packaging accident: the page loads, every script 404s, and the
    user sees a blank window with no explanation.
    """
    assets_dir = dist_dir / "assets"
    if not assets_dir.is_dir():
        return False
    return any(assets_dir.glob("*.js")) and any(assets_dir.glob("*.css"))


def bundled_runtime_owns_interpreter(layout: PackageLayout) -> bool:
    """True when the interpreter running us lives inside this package.

    The packaged product exists precisely so the user needs no Python of their
    own. If `sys.executable` resolves outside the bundle, the package is being
    run by some other interpreter — a developer experiment, a broken copy, a
    relocated bundle missing its runtime — and the honest response is to refuse
    rather than to work by accident on one machine and fail on the user's.
    """
    runtime_dir = layout.bundled_runtime_dir
    if runtime_dir is None or not runtime_dir.is_dir():
        return False
    try:
        interpreter = Path(sys.executable).resolve()
    except (OSError, ValueError):
        return False
    return interpreter == runtime_dir or runtime_dir in interpreter.parents
