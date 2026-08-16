#!/usr/bin/env bash
# Build the bounded CR-017 one-client operator-assisted support distribution.
# The canonical CosmeticWorkshopOS-mac.zip remains the product artifact; this
# wrapper adds a version-specific operator script with the exact inner SHA.
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
SCRIPT_DIR="$REPO_ROOT/scripts"
BUILD_DIR="${COSMETIC_WORKSHOP_BUILD_DIR:-$REPO_ROOT/build}"
OUTPUT_DIR="${COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR:-$REPO_ROOT/dist}"
OPERATOR_OUTPUT_DIR="${COSMETIC_WORKSHOP_OPERATOR_OUTPUT_DIR:-$OUTPUT_DIR}"
INNER_ZIP="$OUTPUT_DIR/CosmeticWorkshopOS-mac.zip"
APP_BUNDLE="$BUILD_DIR/package/CosmeticWorkshopOS.app"
MANIFEST="$APP_BUNDLE/Contents/Resources/app/package-runtime.json"
TEMPLATE="$SCRIPT_DIR/macos/operator_install_update.sh.template"
STAGE_PARENT="$BUILD_DIR/operator-assisted-distribution"

log() { printf '\n[package_operator_assisted] %s\n' "$*"; }
fail() { printf '[package_operator_assisted] ERROR: %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = "Darwin" ] || fail "operator-assisted distribution can only be built on macOS"
command -v ditto >/dev/null 2>&1 || fail "ditto not found"
command -v shasum >/dev/null 2>&1 || fail "shasum not found"
command -v python3 >/dev/null 2>&1 || fail "python3 not found"
[ -f "$TEMPLATE" ] || fail "operator template not found"

mkdir -p "$OPERATOR_OUTPUT_DIR"

log "1/5 build canonical exact product package"
bash "$SCRIPT_DIR/package_macos.sh"
[ -f "$INNER_ZIP" ] || fail "canonical CosmeticWorkshopOS-mac.zip was not created"
[ -d "$APP_BUNDLE" ] || fail "canonical .app was not created"
[ -f "$MANIFEST" ] || fail "package-runtime.json was not created"

read -r APP_VERSION PACKAGE_ARCH < <(
  python3 - "$MANIFEST" <<'PY'
from pathlib import Path
import json
import sys
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload["app_version"], payload["architecture"])
PY
)
[ -n "$APP_VERSION" ] || fail "empty package version"
[ -n "$PACKAGE_ARCH" ] || fail "empty package architecture"
INNER_SHA256="$(shasum -a 256 "$INNER_ZIP" | awk '{print $1}')"
[[ "$INNER_SHA256" =~ ^[0-9a-f]{64}$ ]] || fail "could not calculate canonical ZIP SHA-256"

DIST_NAME="CosmeticWorkshopOS-operator-assisted-${APP_VERSION}-${PACKAGE_ARCH}"
STAGE_DIR="$STAGE_PARENT/$DIST_NAME"
OUTER_ZIP="$OPERATOR_OUTPUT_DIR/${DIST_NAME}.zip"
OPERATOR_SCRIPT="$STAGE_DIR/operator_install_update.sh"

log "2/5 render version-specific operator tool"
rm -rf "$STAGE_PARENT"
mkdir -p "$STAGE_DIR"
cp "$INNER_ZIP" "$STAGE_DIR/CosmeticWorkshopOS-mac.zip"

python3 - "$TEMPLATE" "$OPERATOR_SCRIPT" "$INNER_SHA256" "$APP_VERSION" "$PACKAGE_ARCH" <<'PY'
from pathlib import Path
import sys
source, target, digest, version, arch = sys.argv[1:]
text = Path(source).read_text(encoding="utf-8")
for needle, value in {
    "__INNER_SHA256__": digest,
    "__APP_VERSION__": version,
    "__ARCHITECTURE__": arch,
}.items():
    if text.count(needle) != 1:
        raise SystemExit(f"template placeholder {needle!r} count is {text.count(needle)}")
    text = text.replace(needle, value)
if "__INNER_" in text or "__APP_VERSION__" in text or "__ARCHITECTURE__" in text:
    raise SystemExit("unresolved operator template placeholder")
Path(target).write_text(text, encoding="utf-8")
PY
chmod 755 "$OPERATOR_SCRIPT"

cat > "$STAGE_DIR/OPERATOR-README.txt" <<EOF
Мастерская косметолога — операторская установка / обновление

Этот пакет предназначен только для support-оператора одного пилотного клиента.
Клиент не должен вводить команды в Terminal.

Порядок:
1. Распакуйте этот ZIP целиком.
2. Откройте Terminal как support-оператор.
3. Перейдите в распакованную папку или перетащите operator_install_update.sh в окно Terminal.
4. Запустите: /bin/zsh operator_install_update.sh
5. Скрипт сначала проверит exact SHA-256 и bundle identity и только после этого точечно снимет quarantine с verified staged .app.
6. Gatekeeper глобально не отключается. sudo не используется.

Версия: ${APP_VERSION}
Архитектура: ${PACKAGE_ARCH}
SHA-256 canonical CosmeticWorkshopOS-mac.zip:
${INNER_SHA256}

Публичная/self-service дистрибуция этим пакетом не заявляется.
EOF

log "3/5 verify prepared operator directory"
python3 "$SCRIPT_DIR/verify_operator_assisted_package.py" \
  --directory "$STAGE_DIR" \
  --expected-sha256 "$INNER_SHA256" \
  --expected-version "$APP_VERSION" \
  --expected-architecture "$PACKAGE_ARCH"

log "4/5 create outer operator ZIP"
rm -f "$OUTER_ZIP"
ditto -c -k --sequesterRsrc --keepParent "$STAGE_DIR" "$OUTER_ZIP"

log "5/5 verify final operator ZIP"
python3 "$SCRIPT_DIR/verify_operator_assisted_package.py" \
  --zip "$OUTER_ZIP" \
  --expected-sha256 "$INNER_SHA256" \
  --expected-version "$APP_VERSION" \
  --expected-architecture "$PACKAGE_ARCH"

printf '\nOperator-assisted support package built.\n'
printf '  outer zip : %s\n' "$OUTER_ZIP"
printf '  inner zip : %s\n' "$INNER_ZIP"
printf '  inner sha : %s\n' "$INNER_SHA256"
printf '  version   : %s\n' "$APP_VERSION"
printf '  arch      : %s\n' "$PACKAGE_ARCH"
printf '\nCR-017 one-client operator-assisted pilot only — not public release readiness.\n'
