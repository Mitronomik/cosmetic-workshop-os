from __future__ import annotations

import argparse

from launcher.config import build_runtime_config
from launcher.runtime import RuntimeLaunchError, run_local_runtime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local runtime launcher for Мастерская косметолога.")
    parser.add_argument("--host", default="127.0.0.1", help="Backend host; must remain 127.0.0.1.")
    parser.add_argument("--backend-port", type=int, default=8000, help="Local backend port.")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:5173", help="URL to open in browser.")
    parser.add_argument("--mode", choices=["development", "user"], default="user", help="Startup mode.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = build_runtime_config(
            host=args.host,
            backend_port=args.backend_port,
            frontend_url=args.frontend_url,
            mode=args.mode,
            open_browser=not args.no_browser,
        )
        return run_local_runtime(config)
    except (RuntimeLaunchError, ValueError) as exc:
        print(f"Не удалось запустить приложение: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
