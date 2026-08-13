import subprocess

active = {
    'README.md','docs/current-lifecycle.md','docs/deployment.md','docs/implementation-plan.md',
    'docs/packaging.md','docs/update-guide.md','docs/history/README.md',
    'scripts/check_documentation_lifecycle.py','state/change-requests.md','state/current-focus.md',
    'state/handoff.md','state/progress.md',
}
snapshot_names = {
    'ABOUT.md','manifest.json','README.md','current-lifecycle.md','implementation-plan.md',
    'packaging.md','deployment.md','update-guide.md','current-focus.md','progress.md','handoff.md',
    'change-requests.md','check_documentation_lifecycle.py','history-README.md',
}
expected = active | {f'docs/history/d4-c-pre-closure/{name}' for name in snapshot_names}
tracked = subprocess.check_output(['git','diff','--name-only'], text=True).splitlines()
untracked = subprocess.check_output(['git','ls-files','--others','--exclude-standard'], text=True).splitlines()
actual = set(filter(None, tracked + untracked))
if actual != expected or len(actual) != 26:
    raise SystemExit(f'D4-C closure scope mismatch: missing={sorted(expected-actual)} extra={sorted(actual-expected)} count={len(actual)}')
for path in actual:
    if path.startswith(('backend/','launcher/','frontend/','macos_package/','migrations/')):
        raise SystemExit(f'implementation scope leak: {path}')
