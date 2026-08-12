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
#   CosmeticWorkshopOS.app/
#     Contents/
#       Info.plist
#       MacOS/CosmeticWorkshopOS          bootstrap → bundled python → entrypoint
#       Resources/
#         runtime/                        pinned relocatable CPython + backend deps
#         app/
#           launcher/                     unchanged
#           backend/app/                  unchanged, minus tests
#           frontend/dist/                production build
#           macos_package/                packaging runtime support
#           help/                         offline help
#           package-runtime.json          the build's self-description
#
# Explicitly NOT done here, and not authorized by CR-012: signing, notarization,
# DMG, installer, updater, release upload.
#
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
SCRIPT_DIR="$REPO_ROOT/scripts"

APP_NAME="CosmeticWorkshopOS"
APP_BUNDLE="${APP_NAME}.app"
ZIP_NAME="${APP_NAME}-mac.zip"
APP_VERSION="0.1.0"

BUILD_DIR="${COSMETIC_WORKSHOP_BUILD_DIR:-$REPO_ROOT/build}"
OUTPUT_DIR="${COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR:-$REPO_ROOT/dist}"
STAGE_DIR="$BUILD_DIR/package"
BUNDLE_DIR="$STAGE_DIR/$APP_BUNDLE"

log() { printf '\n[package_macos] %s\n' "$*"; }
fail() { printf '[package_macos] ОШИБКА: %s\n' "$*" >&2; exit 1; }

# --- refuse anywhere but macOS ------------------------------------------------
[ "$(uname -s)" = "Darwin" ] || fail "сборка macOS-пакета возможна только на macOS (обнаружено: $(uname -s))."
command -v ditto  >/dev/null 2>&1 || fail "не найден /usr/bin/ditto — требуется macOS."
command -v rsync  >/dev/null 2>&1 || fail "не найден rsync."
command -v shasum >/dev/null 2>&1 || fail "не найден shasum."

# --- clean up a failed build --------------------------------------------------
# A half-assembled bundle must never be left behind: it looks like a product and
# would fail in confusing ways if anybody opened it.
BUILD_SUCCEEDED=0
cleanup() {
  if [ "$BUILD_SUCCEEDED" -ne 1 ]; then
    printf '[package_macos] сборка прервана — удаляю незавершённый пакет\n' >&2
    rm -rf "$BUNDLE_DIR"
  fi
}
trap cleanup EXIT

# --- 1. production frontend ---------------------------------------------------
log "1/6 сборка production frontend"
bash "$SCRIPT_DIR/build_frontend.sh"

# --- 2. self-contained runtime ------------------------------------------------
log "2/6 подготовка self-contained runtime"
bash "$SCRIPT_DIR/build_backend.sh"
RUNTIME_DIR="$BUILD_DIR/runtime"
[ -x "$RUNTIME_DIR/bin/python3.12" ] || fail "self-contained runtime не собран"

# --- 3. assemble the bundle ---------------------------------------------------
log "3/6 сборка $APP_BUNDLE"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR/Contents/MacOS" "$BUNDLE_DIR/Contents/Resources/app"

sed "s/__APP_VERSION__/$APP_VERSION/g" "$SCRIPT_DIR/macos/Info.plist.template" \
  > "$BUNDLE_DIR/Contents/Info.plist"
cp "$SCRIPT_DIR/macos/bundle_bootstrap.sh" "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"
chmod 755 "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"

# `ditto` rather than `cp -R`, so the interpreter's symlinks, permissions and
# framework layout survive the copy intact.
ditto "$RUNTIME_DIR" "$BUNDLE_DIR/Contents/Resources/runtime"

APP_ROOT="$BUNDLE_DIR/Contents/Resources/app"

# Every exclusion below is a thing that must never be distributed: developer
# state, real user data, test suites, VCS metadata, editor droppings. The copy
# is an allowlist of directories plus a denylist of contents, rather than a
# whole-tree copy with a few holes punched in it.
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

# The package's self-description. Its presence is what tells the entrypoint it
# is running packaged rather than from a checkout, and it records which runtime
# and architecture this artifact was built for. It carries no path from the
# build machine.
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

# Belt and braces: anything the excludes missed dies here rather than shipping.
find "$BUNDLE_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$BUNDLE_DIR" -name '.DS_Store' -delete 2>/dev/null || true

# Strip extended attributes — quarantine flags and provenance markers picked up
# from the downloaded runtime. Left in place they have to be carried through the
# archive as AppleDouble sidecars, which is what produces a parallel `__MACOSX`
# tree full of `._` files. Nothing the product needs lives in an xattr.
xattr -cr "$BUNDLE_DIR" 2>/dev/null || true

# --- 4. archive ---------------------------------------------------------------
log "4/6 создание $ZIP_NAME"
mkdir -p "$OUTPUT_DIR"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME"
rm -f "$ZIP_PATH"
# `ditto -c -k --keepParent` is the macOS-native archiver: it preserves symlinks
# and the executable bit, which `zip` alone does not reliably do for a bundle.
# `--sequesterRsrc` is deliberately not used: it would add a parallel `__MACOSX`
# tree, and the xattrs it exists to preserve were just stripped above.
ditto -c -k --keepParent "$BUNDLE_DIR" "$ZIP_PATH"

# --- 5. verify ----------------------------------------------------------------
log "5/6 проверка структуры пакета"
python3 "$SCRIPT_DIR/verify_macos_package.py" \
  --app "$BUNDLE_DIR" --zip "$ZIP_PATH" --source-root "$REPO_ROOT" \
  || fail "проверка структуры пакета не пройдена"

# --- 6. report ----------------------------------------------------------------
log "6/6 готово"
printf '  .app : %s (%s)\n' "$BUNDLE_DIR" "$(du -sh "$BUNDLE_DIR" | awk '{print $1}')"
printf '  zip  : %s (%s)\n' "$ZIP_PATH" "$(du -sh "$ZIP_PATH" | awk '{print $1}')"
printf '  arch : %s\n' "$(uname -m)"
printf '\nD3 package built. Not signed, not notarized — verification artifact only.\n'

BUILD_SUCCEEDED=1
