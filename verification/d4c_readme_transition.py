from pathlib import Path
CODE = "adfe37a3f68a545635f173c22d4710eacde86e74"
p = Path("README.md")
text = p.read_text(encoding="utf-8")
replacements = [
("D4-B is merged, exact-head/exact-package verified and lifecycle-closed by this closure. D4-C is now the only authorized next slice; D4-D remains gated.", "D4-B remains closed. D4-C is implemented in the current branch; exact-head/exact-package verification and lifecycle closure are still pending, and D4-D remains gated."),
("## D4-B closed baseline / D4-C next", "## D4-B closed baseline / D4-C implementation"),
("- D4-C UI/failure UX was not implemented by D4-B; this closure authorizes it as the next separate slice.", "- D4-C is implemented separately as a read-only human-facing status projection plus bounded packaged failure presentation; D4-B remains the update authority."),
]
for old, new in replacements:
    if text.count(old) != 1: raise SystemExit("README narrative mismatch")
    text = text.replace(old, new, 1)
anchor = "## Core product invariants\n"
block = f"""## D4-C implementation pending verification

Implementation code commit: `{CODE}`.

D4-C adds a redacted read-only Settings update status and exactly two fixed packaged update-failure outcomes. Browser-visible data excludes operation/schema/stage/backup identities, raw failure categories, paths and tracebacks. There is no update command or technical update console. Protected Restore blobs remain unchanged.

D4-D remains unauthorized until D4-C is merged, verified and lifecycle-closed.

"""
if text.count(anchor) != 1: raise SystemExit("README anchor mismatch")
p.write_text(text.replace(anchor, block + anchor, 1), encoding="utf-8")
