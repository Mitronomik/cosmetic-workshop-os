"""D3 — macOS package MVP runtime support.

This package contains the small amount of code that only the **packaged**
product needs, kept deliberately outside the closed Restore/launcher boundary:

```text
package_paths     resolve the packaged application's own resources
frontend_server   serve the production frontend build and proxy /api/* — no Node
user_alert        make a packaged startup refusal visible without a terminal
entrypoint        start the frontend server, then the existing launcher
verification      prove a built .app / ZIP contains what it must and nothing else
```

Nothing here owns Restore, the backend child, the database or any business
logic. D3 packages the existing product; it does not reimplement it. The
launcher stays the destructive Restore authority under ADR 0016, the launcher
keeps the ADR 0018 loopback control plane and picker, the backend stays the
API-first localhost-only business authority, and the ordinary system browser
stays the presentation surface.
"""
