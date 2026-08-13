#!/usr/bin/env bash
#
# D3 — macOS package MVP. Produce `CosmeticWorkshopOS-mac.zip` containing a
# user-openable `CosmeticWorkshopOS.app`.
#
# The whole build is: build the frontend, prepare a self-contained interpreter,
# copy the existing product into a bundle, and verify what came out. It packages
# the product; it does not modify it. No launcher, backend, Restore or frontend
# source file is touched by this script.
#
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
SCRIPT_DIR="$REPO_ROOT/scripts"

APP_NAME="CosmeticWorkshopOS"
APP_BUNDLE="${APP_NAME}.app"
ZIP_NAME="${APP_NAME}-mac.zip"

BUILD_DIR="${COSMETIC_WORKSHOP_BUILD_DIR:-$REPO_ROOT/build}"
OUTPUT_DIR="${COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR:-$REPO_ROOT/dist}"
STAGE_DIR="$BUILD_DIR/package"
BUNDLE_DIR="$STAGE_DIR/$APP_BUNDLE"

log() { printf '\n[package_macos] %s\n' "$*"; }
fail() { printf '[package_macos] ОШИБКА: %s\n' "$*" >&2; exit 1; }

# D4-A: one editable product-version authority. The package metadata below are
# projections generated from backend/VERSION, never independent literals.
APP_VERSION="$(
  PYTHONPATH="$REPO_ROOT/backend" python3 - <<'PY'
from app.version import read_repository_app_version
print(read_repository_app_version())
PY
)" || fail "не удалось прочитать каноническую версию приложения"

[ "$(uname -s)" = "Darwin" ] || fail "сборка macOS-пакета возможна только на macOS (обнаружено: $(uname -s))."
command -v ditto  >/dev/null 2>&1 || fail "не найден /usr/bin/ditto — требуется macOS."
command -v rsync  >/dev/null 2>&1 || fail "не найден rsync."
command -v shasum >/dev/null 2>&1 || fail "не найден shasum."

BUILD_SUCCEEDED=0
cleanup() {
  if [ "$BUILD_SUCCEEDED" -ne 1 ]; then
    printf '[package_macos] сборка прервана — удаляю незавершённый пакет\n' >&2
    rm -rf "$BUNDLE_DIR"
  fi
}
trap cleanup EXIT

log "1/6 сборка production frontend"
bash "$SCRIPT_DIR/build_frontend.sh"

log "2/6 подготовка self-contained runtime"
bash "$SCRIPT_DIR/build_backend.sh"
RUNTIME_DIR="$BUILD_DIR/runtime"
[ -x "$RUNTIME_DIR/bin/python3.12" ] || fail "self-contained runtime не собран"

log "3/6 сборка $APP_BUNDLE"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR/Contents/MacOS" "$BUNDLE_DIR/Contents/Resources/app"

sed "s/__APP_VERSION__/$APP_VERSION/g" "$SCRIPT_DIR/macos/Info.plist.template" \
  > "$BUNDLE_DIR/Contents/Info.plist"
cp "$SCRIPT_DIR/macos/bundle_bootstrap.sh" "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"
chmod 755 "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"

ditto "$RUNTIME_DIR" "$BUNDLE_DIR/Contents/Resources/runtime"

APP_ROOT="$BUNDLE_DIR/Contents/Resources/app"
COMMON_EXCLUDES=(
  --exclude '.git' --exclude '.git*'
  --exclude '__pycache__' --exclude '*.pyc'
  --exclude '.DS_Store'
  --exclude '.pytest_cache'
  --exclude 'node_modules'
  --exclude '*.sqlite' --exclude '*.sqlite3' --exclude '*.db'
  --exclude '.env' --exclude '.env.*'
  --exclude '*.pem' --exclude '*.key'
)

rsync -a "${COMMON_EXCLUDES[@]}" --exclude 'tests' \
  "$REPO_ROOT/launcher/" "$APP_ROOT/launcher/"
mkdir -p "$APP_ROOT/backend"
rsync -a "${COMMON_EXCLUDES[@]}" --exclude 'tests' \
  "$REPO_ROOT/backend/app/" "$APP_ROOT/backend/app/"
rsync -a "${COMMON_EXCLUDES[@]}" --exclude 'tests' \
  "$REPO_ROOT/macos_package/" "$APP_ROOT/macos_package/"
mkdir -p "$APP_ROOT/frontend"
rsync -a "${COMMON_EXCLUDES[@]}" \
  "$REPO_ROOT/frontend/dist/" "$APP_ROOT/frontend/dist/"
rsync -a "${COMMON_EXCLUDES[@]}" \
  "$REPO_ROOT/help/" "$APP_ROOT/help/"

# The package's self-description. app_version is generated from backend/VERSION;
# the source VERSION file itself is deliberately not copied into the package.
cat > "$APP_ROOT/package-runtime.json" <<JSON
{
  "product": "Мастерская косметолога",
  "artifact": "$APP_BUNDLE",
  "app_version": "$APP_VERSION",
  "python_version": "$("$RUNTIME_DIR/bin/python3.12" -c 'import platform; print(platform.python_version())')",
  "architecture": "$(uname -m)",
  "runtime_root_relative_to_app": "../runtime",
  "requires_system_python": false,
  "requires_node": false
}
JSON

find "$BUNDLE_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$BUNDLE_DIR" -name '.DS_Store' -delete 2>/dev/null || true
xattr -cr "$BUNDLE_DIR" 2>/dev/null || true

log "4/6 создание $ZIP_NAME"
mkdir -p "$OUTPUT_DIR"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME"
rm -f "$ZIP_PATH"
ditto -c -k --keepParent "$BUNDLE_DIR" "$ZIP_PATH"

log "5/6 проверка структуры и версии пакета"
python3 "$SCRIPT_DIR/verify_product_version.py" \
  --app "$BUNDLE_DIR" --source-root "$REPO_ROOT" \
  || fail "проекции версии пакета не совпадают с канонической версией"
python3 "$SCRIPT_DIR/verify_macos_package.py" \
  --app "$BUNDLE_DIR" --zip "$ZIP_PATH" --source-root "$REPO_ROOT" \
  || fail "проверка структуры пакета не пройдена"

log "6/6 готово"
printf '  .app : %s (%s)\n' "$BUNDLE_DIR" "$(du -sh "$BUNDLE_DIR" | awk '{print $1}')"
printf '  zip  : %s (%s)\n' "$ZIP_PATH" "$(du -sh "$ZIP_PATH" | awk '{print $1}')"
printf '  arch : %s\n' "$(uname -m)"
printf '  version: %s\n' "$APP_VERSION"
printf '\nD3 package built. Not signed, not notarized — verification artifact only.\n'

BUILD_SUCCEEDED=1
