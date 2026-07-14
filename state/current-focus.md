# Current Focus — Slice A2 structured form validation

Slice A2 is IN PROGRESS — correction under review.

Scope for this correction branch remains limited to PR #114:

- repair `/clients` and `/ingredients` structured validation lifecycle defects;
- preserve focus/caret while clearing stale field errors;
- guard in-flight form context switches;
- separate mutation failures from post-save list refresh failures;
- make parser field-path allow-listing strict;
- keep accessible Russian inline errors and form summaries without duplicate announcements;
- no route expansion beyond Clients and Ingredients.

Slice A3 remains BLOCKED A2 and must not be started in this PR.

A2 must remain IN PROGRESS until the corrected published PR head is reviewed and required smoke evidence is accepted.
