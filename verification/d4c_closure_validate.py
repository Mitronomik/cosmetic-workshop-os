from __future__ import annotations

import subprocess
from pathlib import Path


def must_fail(label: str) -> None:
    result = subprocess.run(
        ["python3", "scripts/check_documentation_lifecycle.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    if result.returncode == 0:
        raise SystemExit(f"negative closure probe was not caught: {label}")


focus = Path("state/current-focus.md")
good = focus.read_text(encoding="utf-8")
for old, new in (
    (
        "D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED",
        "D4-D — Exact-package update verification and D4 lifecycle closure — IMPLEMENTED",
    ),
    ("D5 — Remote install checklist — NOT AUTHORIZED BY CR-013", "D5 — Remote install checklist — AUTHORIZED"),
    ("Product release readiness — NOT CLAIMED", "Product release readiness — READY"),
    ("Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED", "Restore — IN PROGRESS"),
    (
        "D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",
        "D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING",
    ),
):
    if old not in good:
        raise SystemExit(f"probe source missing: {old}")
    focus.write_text(good.replace(old, new, 1), encoding="utf-8")
    must_fail(new)
    focus.write_text(good, encoding="utf-8")

history = Path("docs/history/d4-c-pre-closure/README.md")
raw_bytes = history.read_bytes()
history.write_bytes(raw_bytes + b"\nmutation-probe\n")
must_fail("D4-C history mutation")
history.write_bytes(raw_bytes)

runtime = Path("backend/app/services/update_safety.py")
raw = runtime.read_text(encoding="utf-8")
if "error.committed" not in raw:
    raise SystemExit("runtime probe anchor missing")
runtime.write_text(raw.replace("error.committed", "error.committeD", 1), encoding="utf-8")
must_fail("D4-C runtime seam mutation")
runtime.write_text(raw, encoding="utf-8")

frontend = Path("frontend/src/settings-update-status.ts")
raw = frontend.read_text(encoding="utf-8")
if "fetch('/api/settings/status')" not in raw:
    raise SystemExit("frontend probe anchor missing")
frontend.write_text(raw.replace("fetch('/api/settings/status')", "fetch('/api/settings/status-broken')", 1), encoding="utf-8")
must_fail("D4-C frontend status seam mutation")
frontend.write_text(raw, encoding="utf-8")

subprocess.run(["python3", "scripts/check_documentation_lifecycle.py"], check=True)
subprocess.run(["git", "diff", "--check"], check=True)
