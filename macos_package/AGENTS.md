# macos_package/AGENTS.md

Scope: everything under `macos_package/`.

This package exists for `D3 — macOS package MVP`, authorized by `CR-012` / ADR 0019. It holds only what the **packaged** product needs on top of the existing runtime.

Boundary rules:

- Package the existing product; never reimplement it. The launcher owns Restore, the backend owns business logic, the ordinary browser is the presentation surface.
- Do not duplicate launcher lifecycle, backend supervision or Restore state-machine logic here. Call `launcher.runtime.run_local_runtime` and let it decide.
- Do not add a desktop application framework, a WebView shell, a second product UI, a new Restore transport or a backend Restore endpoint. If packaging appears to require one, STOP and open a new decision.
- The frontend server binds `127.0.0.1` only, serves one fixed production build root, proxies only `/api/*` to the fixed local backend, and adds no CORS headers. It is not a general proxy and must not grow into one.
- Preserve the exact configured local frontend origin. ADR 0018 Restore control-plane Origin/Host checks depend on it.
- Never turn a backend status into a different status. Only `502` (backend unreachable) may be invented.
- No user data, database, backup, export or log may ever live inside the package.
- User-facing packaged failure text comes from the fixed catalogue in `user_alert.py`. Never interpolate paths, exception text or any other composed string into AppleScript.
- Every new production boundary here needs focused tests in `macos_package/tests/`.
