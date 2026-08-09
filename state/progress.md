# Progress

Updated: `2026-08-09`

## Completed / merged baseline

- C1/C2 completed; C3 completed, merged, exact-head verified and hardened.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- A1/A2/A3/A4 — merged and exact-head verified.
- PR #181 reviewed `d2549cd9be2b60c5aee2479050e05a6ad8530c6c`, merged as `beae1407af270ad1c800c308ea7907750430eb1d`; C4-II-A closed and only B1 authorized.
- Searchable history and five exact pre-compaction snapshots remain protected.

## Current lifecycle

```text
PR #181 — MERGED — B1 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## B1 implementation

B1 adds `ExpectedSourceProof`, fixed `SOURCE_CHANGED` guidance, launcher-private `ProofBoundRestoreRequest(RestoreRequest)` and `bind_expected_source_proof(...)`. Base `RestoreRequest` remains selected-source-only. The proof is checked against the same C4-I `HeldSource` descriptor later staged: identity → revalidate → self-containment → full descriptor SHA-256/byte count → revalidate → self-containment. The gate runs before `_execute_with_source(...)`, therefore before `prepared`, safety copy or working-DB mutation.

`launcher/restore/staging.py` stays byte-identical; legacy requests remain base `RestoreRequest` and preserve current behavior. Focused tests cover exact match, same descriptor continuity, inode/path substitution, same-inode byte drift, sidecars, symlink, short digest, safe message, immutability, base-request compatibility and legacy behavior.

The first full B1 regression attempt on exact head `e0cce48734116e0527463e914fe62517f24850b1` reached **2479 passed / 1 failed**. The single failure was the historical base `RestoreRequest` field-surface contract. B1 was corrected by moving proof evidence into the dedicated subtype instead of weakening that invariant. The corrected exact head still requires re-verification.

## Still blocked

```text
C4-II-B2 — not authorized
C4-II-B3 — not authorized
C4-II-C — not authorized
C4-III — not authorized
```

## Open product obligations

- exact-head verify and merge B1;
- lifecycle-close B1 before deciding B2 destructive coordinator/control semantics;
- later B3 explicit destructive confirmation;
- later C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
