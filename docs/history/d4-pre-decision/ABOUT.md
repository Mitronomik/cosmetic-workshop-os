# D4 pre-decision snapshot

This directory preserves the complete active lifecycle/state surfaces immediately before CR-013 / ADR 0020.

Exact source base:

```text
dc2301f7d4e101ad0fba851325dae9274f02da0c
```

The snapshot files are copied by exact Git blob identity, not rewritten summaries. They remain historical evidence only and do not override the newer active lifecycle or ADR 0020.

The preserved lifecycle checker is especially important: the current checker reads its legacy protected-blob dictionaries and continues verifying every previously protected Restore/history blob before applying the new D4 authorization checks.
