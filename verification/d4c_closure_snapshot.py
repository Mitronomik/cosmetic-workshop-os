from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

SOURCE = os.environ["D4C_MERGED_HEAD"]
PR_HEAD = os.environ["D4C_VERIFIED_PR_HEAD"]
PR_RUN = os.environ["D4C_PR_HEAD_RUN"]
MERGED_RUN = os.environ["D4C_MERGED_RUN"]
PR_ARTIFACT = os.environ["D4C_PR_ARTIFACT"]
PR_DIGEST = os.environ["D4C_PR_DIGEST"]
MERGED_ARTIFACT = os.environ["D4C_MERGED_ARTIFACT"]
MERGED_DIGEST = os.environ["D4C_MERGED_DIGEST"]

SNAPSHOT = Path("docs/history/d4-c-pre-closure")
FILES = {
    "README.md": "README.md",
    "docs/current-lifecycle.md": "current-lifecycle.md",
    "docs/implementation-plan.md": "implementation-plan.md",
    "docs/packaging.md": "packaging.md",
    "docs/deployment.md": "deployment.md",
    "docs/update-guide.md": "update-guide.md",
    "state/current-focus.md": "current-focus.md",
    "state/progress.md": "progress.md",
    "state/handoff.md": "handoff.md",
    "state/change-requests.md": "change-requests.md",
    "scripts/check_documentation_lifecycle.py": "check_documentation_lifecycle.py",
    "docs/history/README.md": "history-README.md",
}

if SNAPSHOT.exists():
    raise SystemExit("D4-C pre-closure snapshot already exists")
SNAPSHOT.mkdir(parents=True)

blob_map: dict[str, str] = {}
for source, target in FILES.items():
    path = Path(source)
    if not path.is_file():
        raise SystemExit(f"missing snapshot source: {source}")
    shutil.copyfile(path, SNAPSHOT / target)
    blob_map[target] = subprocess.check_output(["git", "hash-object", source], text=True).strip()

manifest = {
    "source_commit": SOURCE,
    "verified_pr_head": PR_HEAD,
    "pr_head_verification_run": PR_RUN,
    "merged_head_verification_run": MERGED_RUN,
    "verified_head_to_merge_changed_files": 0,
    "files": blob_map,
}
(SNAPSHOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

about = f"""# D4-C pre-closure snapshot

This directory preserves exact active lifecycle/state/checker surfaces from merged head `{SOURCE}` immediately before D4-C lifecycle closure and D4-D authorization.

Evidence:

- verified PR head: `{PR_HEAD}`;
- PR-head Level-5 run: `{PR_RUN}`;
- PR-head artifact: `{PR_ARTIFACT}`;
- PR-head digest: `{PR_DIGEST}`;
- merged head: `{SOURCE}`;
- merged-head Level-5 run: `{MERGED_RUN}`;
- merged-head artifact: `{MERGED_ARTIFACT}`;
- merged-head digest: `{MERGED_DIGEST}`;
- verified PR head → merge: `0` changed files.

Every copied file is preserved by exact Git blob identity in `manifest.json`. Historical status text here is evidence only and does not override active lifecycle authority.
"""
(SNAPSHOT / "ABOUT.md").write_text(about, encoding="utf-8")
