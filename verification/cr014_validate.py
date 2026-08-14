from __future__ import annotations

import subprocess
from pathlib import Path

CHECK = ["python3", "scripts/check_documentation_lifecycle.py"]


def must_fail(label: str) -> None:
    result = subprocess.run(CHECK, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if result.returncode == 0:
        raise SystemExit(f"negative CR-014 probe was not caught: {label}")


focus = Path("state/current-focus.md")
good = focus.read_text(encoding="utf-8")
probes = (
    (
        "D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED",
        "D5 — Remote install checklist — IMPLEMENTED",
    ),
    (
        "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014",
        "PHASE 12 — MVP release preparation — AUTHORIZED",
    ),
    ("Product release readiness — NOT CLAIMED", "Product release readiness — READY"),
    ("Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED", "Restore — IN PROGRESS"),
)
for old, new in probes:
    if old not in good:
        raise SystemExit(f"probe source missing: {old}")
    focus.write_text(good.replace(old, new, 1), encoding="utf-8")
    must_fail(new)
    focus.write_text(good, encoding="utf-8")

# Release/distribution authorization must be rejected even if the lifecycle block is unchanged.
focus.write_text(good + "\nsigning — AUTHORIZED\n", encoding="utf-8")
must_fail("signing authorization")
focus.write_text(good, encoding="utf-8")

# The current install skeletons must remain explicitly non-verified until D5 implementation.
remote = Path("docs/remote-install-checklist.md")
remote_good = remote.read_text(encoding="utf-8")
marker = "Status: **DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED**."
if marker not in remote_good:
    raise SystemExit("remote checklist draft marker missing")
remote.write_text(remote_good.replace(marker, "Status: **VERIFIED**.", 1), encoding="utf-8")
must_fail("premature remote checklist verification")
remote.write_text(remote_good, encoding="utf-8")

# The exact pre-decision snapshot is immutable evidence.
history = Path("docs/history/d5-pre-decision/README.md")
history_good = history.read_bytes()
history.write_bytes(history_good + b"\nmutation-probe\n")
must_fail("D5 pre-decision history mutation")
history.write_bytes(history_good)

subprocess.run(CHECK, check=True)
subprocess.run(["git", "diff", "--check"], check=True)
