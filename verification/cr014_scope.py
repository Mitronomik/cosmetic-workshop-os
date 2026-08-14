import subprocess

active = {
    "README.md",
    "docs/AGENTS.md",
    "docs/decisions/AGENTS.md",
    "docs/decisions/0021-d5-remote-install-rehearsal-contract.md",
    "docs/current-lifecycle.md",
    "docs/deployment.md",
    "docs/history/README.md",
    "docs/implementation-plan.md",
    "docs/packaging.md",
    "docs/remote-install-checklist.md",
    "docs/update-guide.md",
    "docs/user-install.md",
    "scripts/check_documentation_lifecycle.py",
    "state/change-requests.md",
    "state/current-focus.md",
    "state/handoff.md",
    "state/progress.md",
}
snapshot_names = {
    "ABOUT.md",
    "manifest.json",
    "README.md",
    "current-lifecycle.md",
    "implementation-plan.md",
    "packaging.md",
    "deployment.md",
    "update-guide.md",
    "user-install.md",
    "remote-install-checklist.md",
    "docs-AGENTS.md",
    "decisions-AGENTS.md",
    "current-focus.md",
    "progress.md",
    "handoff.md",
    "change-requests.md",
    "check_documentation_lifecycle.py",
    "history-README.md",
}
expected = active | {f"docs/history/d5-pre-decision/{name}" for name in snapshot_names}
tracked = subprocess.check_output(["git", "diff", "--name-only"], text=True).splitlines()
untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
actual = set(filter(None, tracked + untracked))
if actual != expected or len(actual) != 35:
    raise SystemExit(
        f"CR-014 scope mismatch: missing={sorted(expected-actual)} extra={sorted(actual-expected)} count={len(actual)}"
    )
for path in actual:
    if path.startswith(("backend/", "frontend/", "launcher/", "macos_package/", "migrations/")):
        raise SystemExit(f"runtime scope leak: {path}")
