# Current focus

PR84 follow-up — Harden demo-data clear dependency guards.

Scope:
- expand demo-data clear guards for all current direct dependency tables;
- add generic alert and purchase suggestion reference guards;
- make status report `can_clear=false` when clear would be unsafe;
- no frontend UI, migrations, automatic install/clear, backup/export automation, production confirmation, or import target expansion.

Next recommended PR: PR85 — Demo data mode UI.
