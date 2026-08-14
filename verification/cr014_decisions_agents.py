from pathlib import Path

p = Path("docs/decisions/AGENTS.md")
t = p.read_text(encoding="utf-8")
anchor = "- For current C4 lifecycle and runtime authorization, read\n  `docs/current-lifecycle.md` before acting on branch-era status tables in older\n  ADRs.\n"
insert = """- ADR 0019 remains the bounded D3 package authority; package existence is not release readiness.\n- ADR 0020 remains the D4 Update Safety authority; D4 is closed.\n- ADR 0021 is the newer bounded authority for D5 Remote Install Rehearsal once CR-014 merges. It authorizes documentation + exact-package assisted-install rehearsal only, not runtime changes, signing/notarization, DMG/PKG, public release, auto-update, Phase 12 or release readiness.\n- For current lifecycle and runtime authorization, read\n  `docs/current-lifecycle.md` before acting on branch-era status tables in older\n  ADRs.\n"""
if t.count(anchor) != 1:
    raise SystemExit("docs/decisions/AGENTS.md authority anchor mismatch")
p.write_text(t.replace(anchor, insert, 1), encoding="utf-8")
