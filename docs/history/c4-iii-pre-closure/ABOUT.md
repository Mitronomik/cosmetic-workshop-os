# C4-III pre-closure snapshots

These files are byte-identical Git blobs from merged main
`0e1193264dc22979ca48e32a962aba916b6b520e`, immediately after PR #192 merged the D3 macOS package MVP and before the C4-III Restore lifecycle closure rewrote the active lifecycle status.

They are historical, non-normative snapshots. Current authority lives in the active files at repository root / `docs/` / `state/`.

The snapshot exists because `docs/AGENTS.md` requires preserving the full prior copy before rewriting active lifecycle documentation. It preserves the exact open-slice wording that was true before the independent exact-package verification result was accepted:

```text
C4-III — IN PROGRESS — EXACT-HEAD VERIFICATION PASSED
C4-III EXACT-PACKAGE VERIFICATION — NOT YET PASSED
C4-III LIFECYCLE CLOSURE — NOT COMPLETED
D3 — macOS package MVP — IMPLEMENTED — C4-III EXACT-PACKAGE VERIFICATION PENDING
Restore — NOT IMPLEMENTED
```

## What this snapshot preserves

- the accepted C4-III **exact-head** PASS on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c`, runner `c4-iii-restore-exact-head-v1`, runner SHA-256 `4c5c09081d2dc1db45ee556777039f4d9802f026d717a194c88c15d6894e5f3a`;
- the recorded exact-package result of that same run, `INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE`, and its `C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE` gate;
- the CR-012 / ADR 0019 authorization of roadmap stage `D3 — macOS package MVP` as the bounded packaged-artifact prerequisite;
- the D3 implementation state as merged by PR #192.

The `INCONCLUSIVE — ENVIRONMENT` classification was **correct at the time** — no packaged artifact existed for the verifier to run against. It is preserved here and in the active profile exactly as recorded. It is not a product failure, not a runner failure, and it is never rewritten as a PASS.

## What happened after this snapshot

The independent external exact-package verifier `c4-iii-restore-exact-package-v1.2` (SHA-256 `2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694`) ran against the packaged runtime built from exact published `main` `0e1193264dc22979ca48e32a962aba916b6b520e` and returned `PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED`. C4-III then closed on the combination of accepted exact-head **and** exact-package evidence.

Two earlier external-runner attempts preceded that accepted run and are preserved truthfully in the active profile as **runner-fault history, never as product defects**:

- an earlier runner version failed before package execution because the external fixture helper had an incorrect `PYTHONPATH`, and was correctly classified `INCONCLUSIVE — RUNNER`;
- `v1.1` produced a textual `FAIL — PRODUCT` during the hard-interruption probe, but inspection proved that verdict was caused by a runner programming error — `UnboundLocalError: cannot access local variable 'x' where it is not associated with a value`. That result is invalid as product evidence and is preserved as historical runner-fault evidence.

Neither attempt is rewritten as a PASS, and neither is counted against the product.

Product release readiness stayed **NOT CLAIMED** through the closure, and `D4` and `D5` stayed **NOT AUTHORIZED**.
