#!/usr/bin/env python3
"""Verify a built macOS package's structure and refuse to ship a bad one.

Run automatically at the end of `scripts/package_macos.sh`, so a build that
produced a package containing a user database, a `.git` directory or a missing
frontend fails the build rather than being discovered later. The same checks are
exercised directly by `macos_package/tests/test_macos_package_structure.py`.

This is a structure gate. It proves what the artifact contains; it does not
prove the artifact runs. Live package behaviour is the Level-5 package smoke.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from macos_package.verification import (  # noqa: E402 - path set up above
    APP_BUNDLE_NAME,
    ZIP_NAME,
    verify_package,
)


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--app",
        type=Path,
        default=repo_root / "build" / "package" / APP_BUNDLE_NAME,
        help="Path to the built .app bundle.",
    )
    parser.add_argument(
        "--zip",
        dest="zip_path",
        type=Path,
        default=repo_root / "dist" / ZIP_NAME,
        help="Path to the built ZIP. Skipped when the file does not exist.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Repository the package was built from; enables the "
        "'package does not reference the build checkout' check.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    zip_path = arguments.zip_path if arguments.zip_path and arguments.zip_path.is_file() else None
    result = verify_package(arguments.app, zip_path, source_root=arguments.source_root)
    print(result.report())
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
