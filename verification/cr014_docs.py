from __future__ import annotations

from pathlib import Path

BASE = "a8a28672a6fd807cd59342a02a102b8e09128fff"
ADR21 = "docs/decisions/0021-d5-remote-install-rehearsal-contract.md"

OLD_D5 = "D5 — Remote install checklist — NOT AUTHORIZED BY CR-013"
NEW_D5 = """CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — NOT STARTED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014"""

STATUS_FILES = [
    "README.md",
    "docs/current-lifecycle.md",
    "docs/implementation-plan.md",
    "docs/packaging.md",
    "docs/deployment.md",
    "state/current-focus.md",
    "state/progress.md",
    "state/handoff.md",
    "state/change-requests.md",
]


def once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence of {old!r}, got {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


for path in STATUS_FILES:
    once(path, OLD_D5, NEW_D5)

# README authority and D5 boundary.
once(
    "README.md",
    "D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.",
    "D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.\nD5 decision: `docs/decisions/0021-d5-remote-install-rehearsal-contract.md`.",
)
once(
    "README.md",
    "D4-A, D4-B, D4-C and D4-D are closed. D4 is complete; D5 and product release readiness remain gated.",
    "D4-A, D4-B, D4-C and D4-D are closed. D4 is complete. CR-014 authorizes D5 only as a documentation + exact-package assisted-install rehearsal; Phase 12 and product release readiness remain gated.",
)
once(
    "README.md",
    "D5 is not authorized by CR-013 and product release readiness is not claimed.",
    "CR-014 authorizes D5 as the only next stage. D5 is not implemented or verified yet; signing/notarization/DMG/App Store/public release/auto-update, Phase 12 and product release readiness remain unauthorized or not claimed.",
)
once(
    "README.md",
    "Read `AGENTS.md`, `docs/current-lifecycle.md`, relevant ADRs and the focused product/domain/test docs before changing behavior. D4 is closed; any future update/distribution work requires a new authorized lifecycle step and must not reopen the closed Restore boundary.",
    "Read `AGENTS.md`, `docs/current-lifecycle.md`, relevant ADRs and the focused product/domain/test docs before changing behavior. D4 is closed. D5 work must follow ADR 0021 and remain documentation/rehearsal-only; any release/distribution/runtime expansion requires a separate decision and must not reopen the closed Restore boundary.",
)

# Current lifecycle authority and D5 contract section.
once(
    "docs/current-lifecycle.md",
    "- ADR 0020 is authoritative for D4 Update Safety.",
    "- ADR 0020 is authoritative for D4 Update Safety.\n- ADR 0021 is authoritative for D5 Remote Install Rehearsal once CR-014 is merged.",
)
once(
    "docs/current-lifecycle.md",
    "## Closed Restore boundary",
    """## D5 decision truth

CR-014 / ADR 0021 defines D5 as a **documentation + exact-package assisted-install rehearsal**, not a release/distribution programme and not a runtime feature.

D5 may update the non-technical install/checklist documents and verify one exact packaged artifact on an explicitly recorded clean Mac or clean macOS user profile. A full D5 PASS requires both automated exact-package evidence and a human Finder/System Settings rehearsal. User steps may not require Terminal, Git, Python, Node.js, Docker, direct SQLite access or repository knowledge.

The current package is unsigned and un-notarized. D5 may document only the normal macOS user-interface approval path actually observed during rehearsal; it may not use `xattr`, `spctl`, `sudo`, global Gatekeeper disabling or any other terminal/security bypass. A D5 PASS is bounded to the exact tested artifact, architecture and macOS environment; it does not imply untested Intel/Apple-Silicon/macOS support.

D5 itself authorizes no backend/frontend/launcher/migration/package-runtime change. A product defect discovered during rehearsal blocks D5 closure and requires its own bounded fix. Signing, notarization, DMG/PKG, App Store, public release hosting, GitHub Releases, release channels, auto-update, MDM/remote-management integration, Phase 12 and product release readiness remain outside CR-014.

## Closed Restore boundary""",
)
once(
    "docs/current-lifecycle.md",
    "D4 is closed. D5, auto-update/download, GitHub Releases integration, signing, notarization, DMG, App Store, release channels and release readiness remain unauthorized or not claimed and require separate future authorization.",
    "D4 is closed. D5 alone is authorized next under ADR 0021 for documentation + assisted-install rehearsal. Auto-update/download, GitHub Releases integration, signing, notarization, DMG/PKG, App Store, release channels, Phase 12 and release readiness remain unauthorized or not claimed.",
)

# Implementation plan: add the new decision and the bounded next task.
once(
    "docs/implementation-plan.md",
    "Normative D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.",
    "Normative D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.\nNormative D5 decision: `docs/decisions/0021-d5-remote-install-rehearsal-contract.md`.",
)
once(
    "docs/implementation-plan.md",
    "## D5 and release boundary\n\n`D5 — Remote install checklist` remains **NOT AUTHORIZED BY CR-013**. Product release readiness remains **NOT CLAIMED**. Signing, notarization, DMG, App Store, release channels and auto-download remain out of scope.",
    """## D5 — Remote install checklist

**AUTHORIZED NEXT — NOT IMPLEMENTED** under CR-014 / ADR 0021.

D5 is documentation + exact-package assisted-install rehearsal only. It must turn the existing install skeletons into a repeatable non-technical Finder/System Settings flow, then prove the roadmap client/component/recipe/restart scenario on a clean Mac or clean macOS user profile with exact artifact/environment evidence. Automated package smoke alone is insufficient for D5 closure; the human UI rehearsal is mandatory.

D5 may not change product runtime behavior. If rehearsal exposes a product defect, stop and authorize/fix that defect separately before closure.

## Release boundary

Product release readiness remains **NOT CLAIMED**. Signing, notarization, DMG/PKG, App Store, public release hosting, GitHub Releases, release channels, auto-update/download, MDM/remote-management integration and `PHASE 12 — MVP release preparation` remain out of CR-014 scope.""",
)

# Packaging/deployment boundaries.
once(
    "docs/packaging.md",
    "Status: **CURRENT — D3 IMPLEMENTED; D4 CLOSED AND FINAL EXACT-PACKAGE VERIFIED**",
    "Status: **CURRENT — D3 IMPLEMENTED; D4 CLOSED; D5 DECIDED AND AUTHORIZED NEXT; RELEASE NOT CLAIMED**",
)
once(
    "docs/packaging.md",
    "D4 is closed and final exact-package verified. This closure does not authorize auto-update download, internet update checking, GitHub Releases integration, release channels, installer redesign, signing/notarization, DMG, App Store, sandbox migration, D5 or release readiness.",
    "D4 is closed and final exact-package verified. CR-014 authorizes D5 only to document and rehearse assisted installation of the existing ZIP/.app. It does not authorize package-runtime redesign, auto-update/download, internet update checking, GitHub Releases, release channels, signing/notarization, DMG/PKG, App Store, sandbox migration, Phase 12 or release readiness.",
)
once(
    "docs/deployment.md",
    "D4 is closed with no deployment-topology change: Settings uses the existing local API and packaged failures use the existing package entrypoint. D5 and release/distribution/cloud work remain unauthorized.",
    "D4 is closed with no deployment-topology change. CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal over the same local topology. Release/distribution infrastructure, cloud work and runtime topology changes remain unauthorized.",
)

# Update guide stays D4-owned; only its D5 status/cross-boundary changes.
once(
    "docs/update-guide.md",
    "D4-контракт безопасного ручного обновления реализован и финально exact-package проверен. Этот файл описывает update-safety поведение, но не является заявлением о готовности продукта к релизу или о завершённой удалённой установке: D5 всё ещё не авторизован.",
    "D4-контракт безопасного ручного обновления реализован и финально exact-package проверен. Этот файл описывает update-safety поведение. CR-014 теперь авторизует D5 как отдельную проверку первой удалённой установки, но D5 ещё не реализован/проверен и это по-прежнему не является заявлением о готовности продукта к релизу.",
)

# Mark the existing install skeletons truthfully without implementing D5 yet.
user_install = Path("docs/user-install.md")
user_text = user_install.read_text(encoding="utf-8")
if not user_text.startswith("# User Install Guide\n"):
    raise SystemExit("docs/user-install.md title mismatch")
user_text = user_text.replace(
    "# User Install Guide\n",
    "# User Install Guide\n\nStatus: **DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED**. This is not yet the final remote-install procedure.\n",
    1,
)
old_note = "Примечание: текущая сборка содержит только MVP foundation для launcher/runtime. Это еще не финальный пользовательский `.app`/`.dmg` package. Папка данных создается только явной startup-инициализацией, чтобы обычные проверки состояния не меняли данные скрыто."
new_note = "Примечание: D3/D4 уже дают реальный `CosmeticWorkshopOS.app` внутри ZIP и безопасный update path, но этот install guide ещё не прошёл D5 clean-profile rehearsal. До D5 PASS не трактовать его как release-ready инструкцию. Пользовательский сценарий не должен требовать Terminal/Git/Python/Node/Docker."
if user_text.count(old_note) != 1:
    raise SystemExit("docs/user-install.md stale note mismatch")
user_install.write_text(user_text.replace(old_note, new_note, 1), encoding="utf-8")

remote = Path("docs/remote-install-checklist.md")
remote_text = remote.read_text(encoding="utf-8")
if not remote_text.startswith("# Remote Install Checklist\n"):
    raise SystemExit("remote checklist title mismatch")
remote.write_text(
    remote_text.replace(
        "# Remote Install Checklist\n",
        "# Remote Install Checklist\n\nStatus: **DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED**. ADR 0021 defines the required final checklist and evidence; do not treat the unchecked skeleton below as a completed install certification.\n",
        1,
    ),
    encoding="utf-8",
)

# docs/AGENTS authority.
once(
    "docs/AGENTS.md",
    "- ADR 0020 is the D4 Update Safety authority once CR-013 is merged. For D4-specific conceptual `AppSettings`, `BackupRecord` and `UpdateLog` fields, read `docs/domain-model-d4-update-safety.md` together with `docs/domain-model.md`.",
    "- ADR 0020 is the D4 Update Safety authority once CR-013 is merged. For D4-specific conceptual `AppSettings`, `BackupRecord` and `UpdateLog` fields, read `docs/domain-model-d4-update-safety.md` together with `docs/domain-model.md`.\n- ADR 0021 is the D5 Remote Install Rehearsal authority once CR-014 is merged. D5 is documentation + exact-package assisted-install rehearsal only; it does not authorize runtime, signing/notarization, DMG/PKG, public release, auto-update, Phase 12 or release-readiness work.",
)

# State files.
once(
    "state/current-focus.md",
    "**No further implementation slice is authorized by CR-013.**\n\nD4 is complete and lifecycle-closed. Starting D5 requires a separate authorization decision/change request. Until then, do not implement remote-install work, auto-update/download, signing/notarization/DMG/App Store/release channels, product release readiness claims or Restore changes.",
    """**Implement D5 Remote Install Checklist only, under CR-014 / ADR 0021.**

D5 is the only authorized next stage. It is documentation + exact-package assisted-install rehearsal over the existing D3/D4 package, with mandatory clean-Mac/clean-profile human UI evidence before D5 closure. Do not modify backend/frontend/launcher/migrations/package runtime under this authorization. If rehearsal finds a product defect, stop and authorize/fix it separately.

Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12, product release readiness claims or Restore changes.""",
)
once(
    "state/progress.md",
    "- CR-013 / ADR 0020 is accepted.\n- Product release readiness is not claimed.",
    "- CR-013 / ADR 0020 is accepted and D4 is closed.\n- CR-014 / ADR 0021 is accepted; D5 alone is authorized next.\n- Product release readiness is not claimed.",
)
once(
    "state/progress.md",
    "D5 remains unauthorized by CR-013 and product release readiness remains not claimed.",
    "CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal. D5 is not implemented or verified yet; Phase 12 and product release readiness remain gated.",
)
once(
    "state/handoff.md",
    "- CR-013 / ADR 0020 decides D4 Update Safety.",
    "- CR-013 / ADR 0020 decides D4 Update Safety.\n- CR-014 / ADR 0021 decides D5 Remote Install Rehearsal and authorizes D5 only.",
)
once(
    "state/handoff.md",
    "D4-C remains closed. D4-D final verification passed on exact main `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881` and D4 is lifecycle-closed. No D5, release or Restore work is authorized by this closure.",
    "D4-C remains closed. D4-D final verification passed on exact main `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881` and D4 is lifecycle-closed. CR-014 now authorizes D5 only as documentation + assisted-install rehearsal; release/Phase 12/runtime/Restore expansion remains unauthorized.",
)

# Change request ledger: append CR-014 after CR-013 content.
cr = Path("state/change-requests.md")
cr_text = cr.read_text(encoding="utf-8")
anchor = "D4-A/B/C/D closure is satisfied. D5 remains unauthorized and product release readiness remains not claimed.\n"
if cr_text.count(anchor) != 1:
    raise SystemExit("CR ledger anchor mismatch")
cr_block = f'''D4-A/B/C/D closure is satisfied. CR-013 itself authorizes no D5 work.\n\n## CR-014 — D5 Remote Install Rehearsal contract\n\nStatus: **ACCEPTED — D5 AUTHORIZED NEXT; NOT IMPLEMENTED**.\n\nDurable decision: `{ADR21}`.\n\nCR-014 defines D5 as documentation + exact-package assisted-install rehearsal on a clean Mac or clean macOS user profile. It authorizes no runtime change and no signing/notarization/DMG/PKG/App Store/public release/GitHub Releases/auto-update/release-channel/MDM/Phase-12 work. A full D5 PASS requires both automated exact-package evidence and a human non-technical Finder/System Settings rehearsal.\n\nD5 is the only authorized next stage. Product release readiness remains not claimed.\n'''
cr.write_text(cr_text.replace(anchor, cr_block, 1), encoding="utf-8")

# History index.
once(
    "docs/history/README.md",
    "## Current index\n",
    f"## Current index\n\n- `d5-pre-decision/` — exact active lifecycle/install/checker surfaces from `main` `{BASE}` immediately before CR-014 / ADR 0021.\n",
)
