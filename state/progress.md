# Progress

Updated: `2026-08-11`

## Current lifecycle

```text
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
C4-II-C — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## 2026-08-11 — C4-II-B3 closed / C4-II-C authorized

PR #187 reviewed head `48e245811af706bb666620c6dda8033ff200967a` merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7`. C4-II-B remains DONE and C4-II-C became the only authorized next implementation slice.

## 2026-08-11 — C4-II-C implementation changeset

Implemented frontend-only truthful final-state UX in `restore-control-presentation.ts`:

- completed provides successful completion and safe ordinary navigation;
- failed avoids rollback/unchanged-data overclaims;
- blocked removes normal-work navigation and gives restart/help guidance;
- post-execute connection/session uncertainty remains unknown and suppresses normal navigation;
- ambiguous execute retry is explicitly the same previous command, not a new Restore.

Focused tests extend `restore-control-races.test.mjs`; expected focused Restore count is 34 before any later additions.

No launcher/backend/contract/runtime/entry/main/navigation/dependency/ADR changes are part of this slice.

Exact-head build/tests/smoke/audit are still required. C4-III remains blocked. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
