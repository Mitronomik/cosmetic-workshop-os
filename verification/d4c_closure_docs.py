from __future__ import annotations

import os
import re
from pathlib import Path

PR_HEAD = os.environ["D4C_VERIFIED_PR_HEAD"]
MERGED_HEAD = os.environ["D4C_MERGED_HEAD"]
PR_RUN = os.environ["D4C_PR_HEAD_RUN"]
MERGED_RUN = os.environ["D4C_MERGED_RUN"]
PR_ARTIFACT = os.environ["D4C_PR_ARTIFACT"]
PR_DIGEST = os.environ["D4C_PR_DIGEST"]
MERGED_ARTIFACT = os.environ["D4C_MERGED_ARTIFACT"]
MERGED_DIGEST = os.environ["D4C_MERGED_DIGEST"]

OLD_D4 = "D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING"
NEW_D4 = "D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT"
OLD_C = "D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING"
NEW_C = "D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED"
OLD_D = "D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED"
NEW_D = "D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED"
STATUS_FILES = (
    "README.md", "docs/current-lifecycle.md", "docs/implementation-plan.md",
    "docs/packaging.md", "docs/deployment.md", "state/current-focus.md",
    "state/progress.md", "state/handoff.md", "state/change-requests.md",
)


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path); text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match for {old!r}, got {text.count(old)}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


for name in STATUS_FILES:
    p = Path(name); text = p.read_text(encoding="utf-8")
    for old, new in ((OLD_D4, NEW_D4), (OLD_C, NEW_C), (OLD_D, NEW_D)):
        if old not in text:
            raise SystemExit(f"{name}: missing lifecycle source {old!r}")
        text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")

# README
replace_once("README.md", "D4-B remains closed. D4-C is implemented in the current branch; exact-head/exact-package verification and lifecycle closure are still pending, and D4-D remains gated.", "D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice; D5 and release readiness remain gated.")
replace_once("README.md", "## D4-B closed baseline / D4-C implementation", "## D4-A/B/C closed baseline / D4-D next")
p = Path("README.md"); text = p.read_text(encoding="utf-8")
pattern = r"## D4-C implementation pending verification\n.*?(?=## Core product invariants)"
replacement = f"""## D4-C closed baseline / D4-D next

D4-C is merged, exact-head/exact-package verified and lifecycle-closed.

- verified PR head: `{PR_HEAD}`; Level-5 run `{PR_RUN}`; artifact `{PR_ARTIFACT}`; digest `{PR_DIGEST}`;
- merged head: `{MERGED_HEAD}`; Level-5 run `{MERGED_RUN}`; artifact `{MERGED_ARTIFACT}`; digest `{MERGED_DIGEST}`;
- verified PR head → merge: `0` changed files;
- redacted Settings update status, fixed packaged update-failure outcomes and closed Restore protections are preserved.

D4-D is authorized next only for exact-package D4 verification and D4 lifecycle closure. D5 and product release readiness remain unauthorized/not claimed.

"""
text2, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1: raise SystemExit("README D4-C section mismatch")
p.write_text(text2, encoding="utf-8")

# Normative lifecycle
p = Path("docs/current-lifecycle.md"); text = p.read_text(encoding="utf-8")
pattern = r"## D4-C implementation truth\n.*?(?=## Closed Restore boundary)"
replacement = f"""## D4-C closure truth

D4-C is **DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED**. Its implementation remains presentation-only over the D4-B startup authority: bounded read-only Settings status, exactly two packaged update-failure outcomes, no browser update authority, no raw update metadata and no protected Restore changes.

## D4-C closure evidence

- verified PR head: `{PR_HEAD}`;
- PR-head Level-5 verifier: run `{PR_RUN}`, artifact `{PR_ARTIFACT}`, digest `{PR_DIGEST}`;
- merged head/current main: `{MERGED_HEAD}`;
- verified PR head → merge compare: `0` changed files;
- merged-head Level-5 verifier: run `{MERGED_RUN}`, artifact `{MERGED_ARTIFACT}`, digest `{MERGED_DIGEST}`;
- both trustworthy exact-package runs ended `PASS — FULL AUTOMATED SMOKE PASSED`.

## D4-D authorization boundary

D4-D alone is **AUTHORIZED NEXT — NOT IMPLEMENTED**. It may perform the final exact-package D4 verification and D4 lifecycle closure required by ADR 0020. It may not introduce new update runtime authority, downloader/checking, D5, signing, notarization, DMG, App Store, release channels/readiness, cloud sync or Restore changes.

"""
text2, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1: raise SystemExit("current-lifecycle D4-C section mismatch")
p.write_text(text2, encoding="utf-8")

# Implementation plan
replace_once("docs/implementation-plan.md", "D4-A and D4-B remain closed. D4-C is implemented in the current branch and awaits exact-head/exact-package verification and lifecycle closure.", "D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice.")
replace_once("docs/implementation-plan.md", "D4-B closure remains satisfied. D4-C is implemented separately and remains verification-pending.", "D4-B closure remains satisfied. D4-C is also merged, verified and lifecycle-closed.")
p = Path("docs/implementation-plan.md"); text = p.read_text(encoding="utf-8")
pattern = r"### D4-C — User-facing update status and packaged failure UX\n\n.*?(?=### D4-D — Exact-package update verification and lifecycle closure)"
replacement = f"""### D4-C — User-facing update status and packaged failure UX

**DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED**.

Verified PR head `{PR_HEAD}` and merged head `{MERGED_HEAD}` are content-identical. Level-5 runs `{PR_RUN}` and `{MERGED_RUN}` passed the full regression, lifecycle, frontend, real package and exact-package D4-C smoke.

"""
text2, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count != 1: raise SystemExit("implementation-plan D4-C section mismatch")
p.write_text(text2, encoding="utf-8")

# Supporting docs
replace_once("docs/packaging.md", "Status: **CURRENT — D3 IMPLEMENTED; D4-A/B CLOSED; D4-C IMPLEMENTED, VERIFICATION PENDING**", "Status: **CURRENT — D3 IMPLEMENTED; D4-A/B/C CLOSED; D4-D AUTHORIZED NEXT**")
replace_once("docs/packaging.md", "D4-B closure authorizes D4-C only. It does not authorize auto-update download, internet update checking, GitHub Releases integration, release channels, installer redesign, signing/notarization, DMG, App Store, sandbox migration, D5 or release readiness.", "D4-C closure authorizes D4-D only. It does not authorize auto-update download, internet update checking, GitHub Releases integration, release channels, installer redesign, signing/notarization, DMG, App Store, sandbox migration, D5 or release readiness.")
replace_once("docs/deployment.md", "D4-C adds no deployment topology: Settings uses the existing local API and packaged failures use the existing package entrypoint. D4-D and D5 remain unauthorized; no release/distribution or cloud work is authorized.", "Closed D4-C adds no deployment topology: Settings uses the existing local API and packaged failures use the existing package entrypoint. D4-D alone is authorized next; D5 and release/distribution/cloud work remain unauthorized.")
replace_once("docs/update-guide.md", "Статус: **D4-A и D4-B закрыты; D4-C реализован, но exact-head/exact-package проверка и lifecycle closure ещё не завершены**.", "Статус: **D4-A, D4-B и D4-C закрыты и проверены; D4-D авторизован следующим только для финальной exact-package проверки D4 и lifecycle closure**.")
replace_once("docs/update-guide.md", "Этот файл пока **не является инструкцией о готовом обновлении продукта**. D4-A и D4-B закрыты; D4-C уже реализует понятный read-only статус и фиксированные packaged failure-сообщения, но его exact-head/exact-package проверка и lifecycle closure ещё не завершены. D4-D остаётся неавторизован.", "Этот файл пока **не является инструкцией о готовом обновлении продукта**. D4-A, D4-B и D4-C закрыты и exact-package проверены. D4-D теперь авторизован только для финальной проверки полного D4-контракта и lifecycle closure; готовность продукта к релизу всё ещё не заявлена.")

# Current focus becomes D4-D only.
Path("state/current-focus.md").write_text(f"""# Current focus

Updated: `2026-08-14`

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
{NEW_D4}
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
{NEW_C}
{NEW_D}
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## Current task

**Execute D4-D only, in a separate bounded PR.**

D4-D owns final exact-package verification of the complete D4 manual-update safety contract and D4 lifecycle closure. It must not create a downloader/updater, new update authority, technical admin UI, release/distribution work or Restore changes.

## D4-C accepted evidence

- verified PR head: `{PR_HEAD}`; run `{PR_RUN}`; artifact `{PR_ARTIFACT}`;
- merged head/current main: `{MERGED_HEAD}`; run `{MERGED_RUN}`; artifact `{MERGED_ARTIFACT}`;
- verified-head → merge compare: `0` changed files;
- both Level-5 reports ended `PASS — FULL AUTOMATED SMOKE PASSED`.

## Do not start

- D5;
- auto-update/download or internet update checking;
- signing/notarization/DMG/App Store/release channels;
- product release readiness claims;
- Restore changes.
""", encoding="utf-8")

# State narrative
replace_once("state/progress.md", "D4-B remains closed. D4-C implementation code commit `adfe37a3f68a545635f173c22d4710eacde86e74` adds the redacted Settings status, read-only Settings presentation and two fixed packaged update-failure outcomes. Focused Python tests, frontend tests/build and lifecycle integrity passed before publication.\n\nExact published-head/package verification and lifecycle closure are still required. D4-D, D5 and release readiness remain gated.", f"D4-B remains closed. D4-C is now merged, exact-head/exact-package verified and lifecycle-closed. Verified PR head `{PR_HEAD}` and merged head `{MERGED_HEAD}` are content-identical; Level-5 runs `{PR_RUN}` and `{MERGED_RUN}` both passed.\n\nD4-D alone is authorized next. D5 and release readiness remain gated.")
replace_once("state/handoff.md", "- D4-C is IMPLEMENTED — exact-head/exact-package verification and lifecycle closure pending.", "- D4-C is DONE — merged, exact-head/exact-package verified and lifecycle-closed.\n- D4-D is AUTHORIZED NEXT — not implemented.")
replace_once("state/handoff.md", "## D4-C implementation handoff", "## D4-C closed handoff / D4-D next")
replace_once("state/handoff.md", "D4-C code is implemented at `adfe37a3f68a545635f173c22d4710eacde86e74` through the existing Settings binding and packaged entrypoint seams. Protected `launcher/runtime.py` and `frontend/src/main.ts` remain unchanged. Verify this branch exactly; do not widen into D4-D, release work or Restore.", f"D4-C is closed on verified PR head `{PR_HEAD}` and merged head `{MERGED_HEAD}` with Level-5 runs `{PR_RUN}` / `{MERGED_RUN}` and a `0`-file head→merge compare. D4-D may now perform only final exact-package D4 verification and lifecycle closure; do not widen into D5, release work or Restore.")
replace_once("state/change-requests.md", "Status: **ACCEPTED — D4-A/B CLOSED; D4-C IMPLEMENTED, VERIFICATION PENDING**.", "Status: **ACCEPTED — D4-A/B/C CLOSED; D4-D AUTHORIZED NEXT**.")
replace_once("state/change-requests.md", "D4-A and D4-B are closed. D4-C implementation code commit `adfe37a3f68a545635f173c22d4710eacde86e74` adds only the bounded read-only status and packaged failure UX authorized by CR-013. D4-C is not yet exact-head/exact-package verified or lifecycle-closed; D4-D remains unauthorized.", f"D4-A, D4-B and D4-C are closed. D4-C verified PR head `{PR_HEAD}` and merged head `{MERGED_HEAD}` passed Level-5 exact-package verification and are content-identical. D4-D alone is authorized next.")
replace_once("state/change-requests.md", "D4-A and D4-B closure remain satisfied. D4-C is implementation-complete in the current branch; only D4-C verification and lifecycle closure are authorized next. D4-D is not authorized.", "D4-A/B/C closure remains satisfied. D4-D only is authorized next; D5 and release readiness remain unauthorized/not claimed.")

# History index
index = Path("docs/history/README.md")
text = index.read_text(encoding="utf-8")
anchor = "## Current index\n\n"
entry = f"- `d4-c-pre-closure/` — exact active lifecycle/state/checker surfaces from merged head `{MERGED_HEAD}` immediately before D4-C closure and D4-D authorization.\n"
if text.count(anchor) != 1: raise SystemExit("history index anchor mismatch")
index.write_text(text.replace(anchor, anchor + entry, 1), encoding="utf-8")
