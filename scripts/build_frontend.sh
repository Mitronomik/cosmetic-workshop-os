#!/usr/bin/env bash
#
# Build the production frontend from the checked-out source.
#
# This runs the repository's own build command and changes nothing about how the
# frontend behaves. Node and npm are needed **here**, at build time, and only
# here: the packaged product serves the resulting static files through
# `macos_package/frontend_server.py`, so the end user never needs Node.
#
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
FRONTEND_DIR="$REPO_ROOT/frontend"
DIST_DIR="$FRONTEND_DIR/dist"

log() { printf '[build_frontend] %s\n' "$*"; }
fail() { printf '[build_frontend] ОШИБКА: %s\n' "$*" >&2; exit 1; }

command -v npm >/dev/null 2>&1 || fail "npm не найден. Установите Node.js, чтобы собрать frontend."
[ -f "$FRONTEND_DIR/package.json" ] || fail "не найден $FRONTEND_DIR/package.json"

cd "$FRONTEND_DIR"

# `npm ci` is the reproducible install and is what the existing verification
# gates use. A lockfile that has drifted from package.json is a real problem the
# developer must see, so it is not silently downgraded to `npm install`.
if [ -f package-lock.json ]; then
  log "npm ci"
  npm ci
else
  log "package-lock.json отсутствует — npm install"
  npm install
fi

log "npm run build"
npm run build

# Prove the build produced a usable product, not just a zero exit code. A dist/
# with an index and no assets renders as a blank page, which is exactly the
# failure that must not reach the package.
[ -f "$DIST_DIR/index.html" ] || fail "сборка не создала $DIST_DIR/index.html"
compgen -G "$DIST_DIR/assets/*.js" >/dev/null || fail "в сборке нет JS-ресурсов"
compgen -G "$DIST_DIR/assets/*.css" >/dev/null || fail "в сборке нет CSS-ресурсов"

log "production frontend готов: $DIST_DIR"
