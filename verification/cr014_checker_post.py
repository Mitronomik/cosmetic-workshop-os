from pathlib import Path

p = Path("scripts/check_documentation_lifecycle.py")
t = p.read_text(encoding="utf-8")
old = '''        "docs-AGENTS.md", "current-focus.md", "progress.md", "handoff.md",
        "change-requests.md", "check_documentation_lifecycle.py", "history-README.md",
'''
new = '''        "docs-AGENTS.md", "decisions-AGENTS.md", "current-focus.md", "progress.md", "handoff.md",
        "change-requests.md", "check_documentation_lifecycle.py", "history-README.md",
'''
if t.count(old) != 1:
    raise SystemExit("D5 snapshot expected-name anchor mismatch")
t = t.replace(old, new, 1)
old2 = '    require(DOCS_AGENTS, ("ADR 0020", "docs/domain-model-d4-update-safety.md", "ADR 0021", "documentation + exact-package assisted-install rehearsal"))\n'
new2 = old2 + '    require(P("docs/decisions/AGENTS.md"), ("ADR 0021", "documentation + exact-package assisted-install rehearsal only", "not runtime changes"))\n'
if t.count(old2) != 1:
    raise SystemExit("D5 decisions AGENTS checker anchor mismatch")
t = t.replace(old2, new2, 1)
p.write_text(t, encoding="utf-8")
