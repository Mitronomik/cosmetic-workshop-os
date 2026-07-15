# Current Focus — prepare Slice A3

Slice A2 structured form validation is DONE and verified in PR #114.

Verified runtime head:

`8eb5d0c2c116c83d4162d10895268375e0bc1e1e`

PR #114 remains open only for final state closure and merge.

Completed A2 scope:

- structured validation for `/clients` create/edit;
- structured validation for `/ingredients` create/edit;
- backend remains the validation source of truth;
- inline errors and form summaries use understandable Russian text;
- focus, caret and original input DOM identity are preserved;
- mutation failures are separated from post-save refresh failures;
- stale request contexts and duplicate submits are guarded;
- frontend validation tests remain dependency-free.

Slice A3 is READY, but no A3 implementation is included in PR #114.

The next task must select one focused A3 validation-migration sub-slice. Do not migrate every remaining form in one PR.
