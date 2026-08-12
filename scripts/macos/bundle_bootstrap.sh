#!/bin/bash
#
# Contents/MacOS/CosmeticWorkshopOS — the whole native side of the package.
#
# It resolves the bundle it lives in, checks that the bundled interpreter is
# actually there, and hands over. It is not an application framework: it starts
# no UI, owns no state, supervises nothing and makes no product decision. Every
# decision belongs to `macos_package.entrypoint` and, through it, to the
# existing launcher.
#
# `exec` matters. Replacing this shell with the interpreter means the process
# macOS tracks *is* the Python process, so Quit from the Dock delivers SIGTERM
# straight to it — the entrypoint converts that into the graceful shutdown the
# launcher already implements, and the backend child is stopped properly instead
# of being orphaned by a killed wrapper.
#
set -euo pipefail

HERE="$(cd -- "$(dirname -- "$0")" && pwd -P)"
CONTENTS="$(cd -- "$HERE/.." && pwd -P)"
RESOURCES="$CONTENTS/Resources"
APP_ROOT="$RESOURCES/app"
RUNTIME_PYTHON="$RESOURCES/runtime/bin/python3.12"

# The one failure this script has to report itself: without the interpreter
# there is no Python left to show a message with. The alert text is a constant,
# and both strings reach AppleScript as `argv` values rather than as script
# source, so nothing here is interpolated into executable text.
if [ ! -x "$RUNTIME_PYTHON" ] || [ ! -d "$APP_ROOT" ]; then
  /usr/bin/osascript \
    -e 'on run argv' \
    -e 'display alert (item 1 of argv) message (item 2 of argv) as critical giving up after 120' \
    -e 'end run' \
    -- "Мастерская косметолога" \
    "Приложение повреждено или распаковано не полностью. Удалите эту копию, распакуйте архив заново и откройте приложение ещё раз. Ваши данные не изменились." \
    >/dev/null 2>&1 || true
  exit 11
fi

# The application root is the import root, exactly as the repository root is in
# development, so `launcher/config.py`'s existing `parents[1]` resolution finds
# `backend/` and `frontend/` inside the bundle without any packaging-aware code.
#
# It is set to exactly that and nothing else. An inherited `PYTHONPATH` used to
# be appended, which quietly let whatever happened to be in the launching
# environment take part in resolving this product's modules — the opposite of
# what a self-contained package is for, and a way for a developer checkout to
# shadow packaged code on one machine and not another.
export PYTHONPATH="$APP_ROOT"
# A stray `PYTHONHOME` would point the bundled interpreter at some other
# installation's standard library.
unset PYTHONHOME
# Ignore ~/Library/Python/*/lib/python/site-packages. The package ships the
# dependencies it needs; a user-site copy of one of them must not win.
export PYTHONNOUSERSITE=1
# The app must never write bytecode into its own bundle.
export PYTHONDONTWRITEBYTECODE=1

cd "$APP_ROOT"
exec "$RUNTIME_PYTHON" -m macos_package.entrypoint "$@"
