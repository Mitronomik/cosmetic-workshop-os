#!/usr/bin/env bash
# Build the bounded CR-016 one-client assisted-install distribution.
#
# This script deliberately leaves `scripts/package_macos.sh` and its canonical
# `CosmeticWorkshopOS-mac.zip` contract unchanged. It wraps that already-verified
# product artifact with a version-specific `.command` bootstrap whose embedded
# SHA-256 is generated only after the inner ZIP exists.
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
SCRIPT_DIR="$REPO_ROOT/scripts"
BUILD_DIR="${COSMETIC_WORKSHOP_BUILD_DIR:-$REPO_ROOT/build}"
OUTPUT_DIR="${COSMETIC_WORKSHOP_PACKAGE_OUTPUT_DIR:-$REPO_ROOT/dist}"
SINGLE_CLIENT_OUTPUT_DIR="${COSMETIC_WORKSHOP_SINGLE_CLIENT_OUTPUT_DIR:-$OUTPUT_DIR}"
INNER_ZIP="$OUTPUT_DIR/CosmeticWorkshopOS-mac.zip"
APP_BUNDLE="$BUILD_DIR/package/CosmeticWorkshopOS.app"
MANIFEST="$APP_BUNDLE/Contents/Resources/app/package-runtime.json"
TEMPLATE="$SCRIPT_DIR/macos/single_client_bootstrap.command.template"
STAGE_PARENT="$BUILD_DIR/single-client-distribution"
STAGE_DIR="$STAGE_PARENT/Мастерская косметолога — установка"
COMMAND_NAME="Установить или обновить Мастерскую.command"

log() { printf '\n[package_single_client] %s\n' "$*"; }
fail() { printf '[package_single_client] ОШИБКА: %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = "Darwin" ] || fail "сборка single-client пакета возможна только на macOS"
command -v ditto >/dev/null 2>&1 || fail "не найден ditto"
command -v shasum >/dev/null 2>&1 || fail "не найден shasum"
command -v python3 >/dev/null 2>&1 || fail "не найден python3 для build-time генерации bootstrap"
[ -f "$TEMPLATE" ] || fail "не найден bootstrap template"

mkdir -p "$SINGLE_CLIENT_OUTPUT_DIR"

log "1/5 собираю канонический exact product package"
bash "$SCRIPT_DIR/package_macos.sh"
[ -f "$INNER_ZIP" ] || fail "канонический CosmeticWorkshopOS-mac.zip не создан"
[ -d "$APP_BUNDLE" ] || fail "канонический .app bundle не создан"
[ -f "$MANIFEST" ] || fail "package-runtime.json не создан"

read -r APP_VERSION PACKAGE_ARCH < <(
  python3 - "$MANIFEST" <<'PY'
from pathlib import Path
import json
import sys
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload["app_version"], payload["architecture"])
PY
)
[ -n "$APP_VERSION" ] || fail "пустая версия пакета"
[ -n "$PACKAGE_ARCH" ] || fail "пустая архитектура пакета"
INNER_SHA256="$(shasum -a 256 "$INNER_ZIP" | awk '{print $1}')"
[[ "$INNER_SHA256" =~ ^[0-9a-f]{64}$ ]] || fail "не удалось получить SHA-256 канонического ZIP"

OUTER_ZIP="$SINGLE_CLIENT_OUTPUT_DIR/CosmeticWorkshopOS-single-client-${APP_VERSION}-${PACKAGE_ARCH}.zip"

log "2/5 создаю version-specific bootstrap"
rm -rf "$STAGE_PARENT"
mkdir -p "$STAGE_DIR"
cp "$INNER_ZIP" "$STAGE_DIR/CosmeticWorkshopOS-mac.zip"

python3 - "$TEMPLATE" "$STAGE_DIR/$COMMAND_NAME" "$INNER_SHA256" "$APP_VERSION" "$PACKAGE_ARCH" <<'PY'
from pathlib import Path
import sys
source, target, digest, version, arch = sys.argv[1:]
text = Path(source).read_text(encoding="utf-8")
replacements = {
    "__INNER_SHA256__": digest,
    "__APP_VERSION__": version,
    "__ARCHITECTURE__": arch,
}
for needle, value in replacements.items():
    if text.count(needle) != 1:
        raise SystemExit(f"template placeholder {needle!r} count is {text.count(needle)}")
    text = text.replace(needle, value)
if "__INNER_" in text or "__APP_VERSION__" in text or "__ARCHITECTURE__" in text:
    raise SystemExit("unresolved bootstrap placeholder")
Path(target).write_text(text, encoding="utf-8")
PY
chmod 755 "$STAGE_DIR/$COMMAND_NAME"

cat > "$STAGE_DIR/Прочтите меня.txt" <<EOF
Мастерская косметолога — установка / обновление

1. Не перемещайте файлы внутри этой папки по отдельности.
2. Дважды нажмите «$COMMAND_NAME».
3. Terminal откроется автоматически. Вводить команды не нужно.
4. Установка продолжится только после автоматической проверки exact SHA-256 пакета.
5. Gatekeeper не отключается глобально; bootstrap работает только с проверенной копией Мастерской косметолога.

Версия: $APP_VERSION
Архитектура: $PACKAGE_ARCH
SHA-256 внутреннего CosmeticWorkshopOS-mac.zip:
$INNER_SHA256
EOF

log "3/5 проверяю подготовленную папку"
python3 "$SCRIPT_DIR/verify_single_client_package.py" \
  --directory "$STAGE_DIR" \
  --expected-sha256 "$INNER_SHA256" \
  --expected-version "$APP_VERSION" \
  --expected-architecture "$PACKAGE_ARCH"

log "4/5 создаю outer ZIP"
rm -f "$OUTER_ZIP"
ditto -c -k --sequesterRsrc --keepParent "$STAGE_DIR" "$OUTER_ZIP"

log "5/5 проверяю final outer ZIP"
python3 "$SCRIPT_DIR/verify_single_client_package.py" \
  --zip "$OUTER_ZIP" \
  --expected-sha256 "$INNER_SHA256" \
  --expected-version "$APP_VERSION" \
  --expected-architecture "$PACKAGE_ARCH"

printf '\nSingle-client package built.\n'
printf '  outer zip : %s\n' "$OUTER_ZIP"
printf '  inner zip : %s\n' "$INNER_ZIP"
printf '  inner sha : %s\n' "$INNER_SHA256"
printf '  version   : %s\n' "$APP_VERSION"
printf '  arch      : %s\n' "$PACKAGE_ARCH"
printf '\nCR-016 pilot artifact only — unsigned/unnotarized, not public release readiness.\n'
