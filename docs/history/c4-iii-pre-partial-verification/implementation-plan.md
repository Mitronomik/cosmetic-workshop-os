# cosmetic-workshop-os — Active implementation plan

Updated: `2026-08-11`

## Current lifecycle

```text
PR #188 — MERGED — C4-II-C EXACT-HEAD VERIFIED
PR #187 — MERGED — C4-II-C AUTHORIZATION BASELINE
PR #186 — MERGED — C4-II-B3 EXACT-HEAD VERIFIED
PR #185 — MERGED — B3 AUTHORIZATION BASELINE
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-C — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-III — AUTHORIZED NEXT — NOT IMPLEMENTED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed predecessor

PR #188 reviewed exact head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12` at `2026-08-11T17:25:11Z`, closing C4-II-C.

Accepted C4-II-C evidence: lifecycle PASS; frontend install/build PASS; focused Restore **34/34 PASS**; browser smoke v5.4 PASS; fresh independent audit P0=0/P1=0/P2=0; final no-change exact-head gate PASS.

Final C4-II-C production file `frontend/src/restore-control-presentation.ts` is now a closed boundary together with the already-closed contract/runtime/entry/launcher/backend/main/navigation seams.

## Current implementation window

### C4-III — Restore end-to-end verification and lifecycle closure

Status: **AUTHORIZED NEXT — NOT IMPLEMENTED**.

Goal:

```text
merged launcher-assisted Restore chain
→ verify current-schema Restore
→ verify supported older-schema Restore
→ verify rejection + interruption + rollback
→ verify repeated launch / startup recovery
→ prove source immutability + safety-copy retention
→ exact end-to-end evidence
→ lifecycle closure
```

### Allowed scope

- focused verification tests and test-only harnesses;
- isolated external exact-head smoke runners;
- verification/checklist documentation;
- lifecycle/state/checker updates required to record evidence;
- no production behavior change unless separately authorized as a bounded defect fix.

### Required verification

At minimum, C4-III must cover the reserved ADR 0017 verification surface:

1. current-schema successful Restore;
2. supported older-schema Restore through the existing migration/startup rules;
3. invalid/rejected candidate paths before destructive mutation;
4. interruption at safety-critical boundaries and conservative startup recovery;
5. rollback and `restore_failed` truth;
6. `restore_blocked` / recovery-blocked ordinary-startup refusal;
7. repeated launch after completed, failed/rolled-back and blocked outcomes;
8. immutable selected source / B1 proof binding;
9. mandatory verified `before_restore` safety-copy retention;
10. browser path/privacy and one-shot/exact-replay invariants;
11. exact-head or exact-package evidence with autonomous timeouts/cleanup;
12. independent P0/P1/P2 audit and final no-change gate.

Use the project smoke classification exactly: PASS / FAIL PRODUCT / INCONCLUSIVE RUNNER / INCONCLUSIVE ENVIRONMENT. Manual `Ctrl+C` invalidates PASS.

### Architecture constraints

C4-III does not authorize:

- a new Restore engine or second destructive path;
- a new launcher/control/backend endpoint or DTO field;
- browser filesystem/source authority;
- destructive cancel, blind retry or new request sequence;
- durable phase reconstruction in frontend;
- production refactor hidden inside verification;
- packaging or updater redesign;
- C4 lifecycle completion without the required evidence.

If verification reveals a product defect, STOP the verification claim, open a separate bounded defect-fix PR, rerun the affected exact-head checks, then resume C4-III.

Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
