from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path.cwd()
BASE = "a8a28672a6fd807cd59342a02a102b8e09128fff"
DEST = ROOT / "docs/history/d5-pre-decision"

FILES = {
    "README.md": "README.md",
    "current-lifecycle.md": "docs/current-lifecycle.md",
    "implementation-plan.md": "docs/implementation-plan.md",
    "packaging.md": "docs/packaging.md",
    "deployment.md": "docs/deployment.md",
    "update-guide.md": "docs/update-guide.md",
    "user-install.md": "docs/user-install.md",
    "remote-install-checklist.md": "docs/remote-install-checklist.md",
    "docs-AGENTS.md": "docs/AGENTS.md",
    "current-focus.md": "state/current-focus.md",
    "progress.md": "state/progress.md",
    "handoff.md": "state/handoff.md",
    "change-requests.md": "state/change-requests.md",
    "check_documentation_lifecycle.py": "scripts/check_documentation_lifecycle.py",
    "history-README.md": "docs/history/README.md",
}

if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != BASE:
    raise SystemExit("CR-014 snapshot builder is not on exact decision base")

DEST.mkdir(parents=True, exist_ok=False)
blobs: dict[str, str] = {}
for out_name, source_name in FILES.items():
    source = ROOT / source_name
    target = DEST / out_name
    shutil.copyfile(source, target)
    blobs[out_name] = subprocess.check_output(["git", "hash-object", str(source)], text=True).strip()

manifest = {
    "source_commit": BASE,
    "purpose": "exact active lifecycle/install/checker surfaces immediately before CR-014 / ADR 0021",
    "files": blobs,
}
(DEST / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
(DEST / "ABOUT.md").write_text(
    "# D5 pre-decision snapshot\n\n"
    f"Exact source commit: `{BASE}`.\n\n"
    "This directory preserves the active lifecycle, install-document skeletons and lifecycle checker immediately before CR-014 / ADR 0021. "
    "The snapshot is historical evidence only; current authority remains `docs/current-lifecycle.md`. "
    "Files are protected by exact Git blob identity through `manifest.json`.\n",
    encoding="utf-8",
)
