#!/usr/bin/env bash
#
# Prepare the self-contained Python runtime the packaged backend runs on.
#
# ## Why a real interpreter rather than a frozen binary
#
# The launcher starts the backend as a separate OS process with
# `sys.executable -m app.launcher_backend_entrypoint`, and that entrypoint is
# load-bearing: it takes the backend-liveness lock and binds the configured
# socket *before* any application module is imported, then reports both through
# an inherited one-run pipe. A freezer that turns `sys.executable` into a
# non-Python launcher binary breaks that contract silently — `-m` stops meaning
# what it means, and the handshake the Restore engine depends on to prove a
# backend stopped and restarted goes with it.
#
# So the package carries a genuine, relocatable CPython. The backend keeps being
# started exactly the way it is started from source, and no Restore, launcher or
# backend file has to change to make packaging work.
#
# ## Build-only dependency (ADR 0019)
#
# The runtime is a pinned `python-build-standalone` distribution. It is a
# **build-time** download: it ends up inside the package, so the end user never
# installs Python. Version and source are pinned below, the archive's SHA-256 is
# verified before a single byte of it is used, the transfer is HTTPS, and a
# mismatch aborts the build rather than falling back to anything.
#
# The produced runtime never falls back to a system interpreter: the packaged
# entrypoint refuses to start if the interpreter executing it is not the bundled
# one.
#
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"

# --- pinned build-only runtime ------------------------------------------------
#
# Pinned exactly: one upstream release tag, one CPython version, one checksum per
# architecture. Bumping any of these is a deliberate, reviewable edit.
PBS_RELEASE="20260807"
PYTHON_VERSION="3.12.13"
PBS_BASE_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PBS_RELEASE}"
PBS_SHA256_aarch64="4201588fc5051c2ba988abbe1f033d318965ee378fadf7fb7ef79882ba7be84b"
PBS_SHA256_x86_64="ce9dc826a3215d5deadf6d7ba409a882b8d431192c4c06deb34ff00f93ceb4f5"

BUILD_DIR="${COSMETIC_WORKSHOP_BUILD_DIR:-$REPO_ROOT/build}"
RUNTIME_DIR="$BUILD_DIR/runtime"
# Kept outside the repository so a build never adds untracked weight to the
# working tree, and so repeated builds do not re-download 25 MB each time.
CACHE_DIR="${COSMETIC_WORKSHOP_BUILD_CACHE_DIR:-$HOME/Library/Caches/cosmetic-workshop-os/build}"

log() { printf '[build_backend] %s\n' "$*"; }
fail() { printf '[build_backend] ОШИБКА: %s\n' "$*" >&2; exit 1; }

case "$(uname -m)" in
  arm64|aarch64) PBS_ARCH="aarch64"; EXPECTED_SHA256="$PBS_SHA256_aarch64" ;;
  x86_64)        PBS_ARCH="x86_64";  EXPECTED_SHA256="$PBS_SHA256_x86_64" ;;
  *) fail "неподдерживаемая архитектура $(uname -m). D3 собирает пакет под текущий Mac." ;;
esac

ARCHIVE_NAME="cpython-${PYTHON_VERSION}+${PBS_RELEASE}-${PBS_ARCH}-apple-darwin-install_only.tar.gz"
ARCHIVE_URL="${PBS_BASE_URL}/${ARCHIVE_NAME}"
ARCHIVE_PATH="$CACHE_DIR/$ARCHIVE_NAME"

mkdir -p "$CACHE_DIR" "$BUILD_DIR"

verify_archive() {
  local actual
  actual="$(shasum -a 256 "$ARCHIVE_PATH" | awk '{print $1}')"
  [ "$actual" = "$EXPECTED_SHA256" ]
}

if [ -f "$ARCHIVE_PATH" ] && verify_archive; then
  log "используется проверенная копия из кэша: $ARCHIVE_PATH"
else
  # A cached file that fails the checksum is removed rather than reused or
  # trusted: it is either a partial download or something that must not be run.
  rm -f "$ARCHIVE_PATH"
  log "загрузка $ARCHIVE_URL"
  curl --fail --location --proto '=https' --tlsv1.2 --silent --show-error \
    --output "$ARCHIVE_PATH.part" "$ARCHIVE_URL" \
    || fail "не удалось загрузить runtime по HTTPS"
  mv "$ARCHIVE_PATH.part" "$ARCHIVE_PATH"
  verify_archive || {
    # Fail closed. A checksum mismatch is never worked around, and the bad file
    # is not left on disk where a later build could pick it up.
    actual="$(shasum -a 256 "$ARCHIVE_PATH" | awk '{print $1}')"
    rm -f "$ARCHIVE_PATH"
    fail "SHA-256 не совпал: ожидалось $EXPECTED_SHA256, получено $actual"
  }
  log "SHA-256 подтверждён"
fi

log "распаковка runtime в $RUNTIME_DIR"
rm -rf "$RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR"
# The archive contains a single `python/` directory; strip it so the runtime
# root is predictable.
tar -xzf "$ARCHIVE_PATH" -C "$RUNTIME_DIR" --strip-components=1

RUNTIME_PYTHON="$RUNTIME_DIR/bin/python3.12"
[ -x "$RUNTIME_PYTHON" ] || fail "в распакованном runtime нет исполняемого python3.12"

# --- backend runtime dependencies --------------------------------------------
#
# Read out of `backend/pyproject.toml` rather than repeated here, so the packaged
# runtime and the developer environment cannot drift onto different versions of
# FastAPI, Starlette or uvicorn. Test extras are deliberately excluded.
log "чтение зависимостей backend из backend/pyproject.toml"
# Read with a `while` loop rather than `mapfile`: macOS still ships bash 3.2,
# and a build script that only runs under a Homebrew bash is a trap.
BACKEND_DEPENDENCIES=()
while IFS= read -r dependency; do
  [ -n "$dependency" ] && BACKEND_DEPENDENCIES+=("$dependency")
done < <("$RUNTIME_PYTHON" - "$REPO_ROOT/backend/pyproject.toml" <<'PY'
import sys, tomllib
with open(sys.argv[1], "rb") as handle:
    project = tomllib.load(handle)["project"]
for dependency in project["dependencies"]:
    print(dependency)
PY
)
[ "${#BACKEND_DEPENDENCIES[@]}" -gt 0 ] || fail "не удалось прочитать зависимости backend"
log "зависимости: ${BACKEND_DEPENDENCIES[*]}"

# `--only-binary=:all:` fails closed rather than compiling from source against
# whatever toolchain happens to be on the build machine — a packaged product must
# not depend on a developer's local compiler state.
# `--no-compile` keeps `__pycache__` out of the artifact; the bootstrap sets
# PYTHONDONTWRITEBYTECODE so the running app never writes into its own bundle.
log "установка зависимостей backend в упакованный runtime"
"$RUNTIME_PYTHON" -m pip install \
  --disable-pip-version-check --no-input --no-compile --only-binary=:all: \
  "${BACKEND_DEPENDENCIES[@]}" \
  || fail "не удалось установить зависимости backend в упакованный runtime"

# --- prune ---------------------------------------------------------------------
#
# Remove what the product cannot use. The console scripts matter most: pip writes
# them with an absolute shebang pointing at this build directory, so shipping
# them would put a stale build path inside the artifact.
log "очистка runtime"
find "$RUNTIME_DIR/bin" -maxdepth 1 -type f ! -name 'python*' -delete
rm -rf \
  "$RUNTIME_DIR/lib/python3.12/test" \
  "$RUNTIME_DIR/lib/python3.12/idlelib" \
  "$RUNTIME_DIR/lib/python3.12/tkinter" \
  "$RUNTIME_DIR/lib/python3.12/turtledemo" \
  "$RUNTIME_DIR/lib/python3.12/lib2to3" \
  "$RUNTIME_DIR/share"
find "$RUNTIME_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$RUNTIME_DIR" -name '*.pyc' -delete 2>/dev/null || true
find "$RUNTIME_DIR" -name '.DS_Store' -delete 2>/dev/null || true

# The one thing that must still be true after all of the above.
"$RUNTIME_PYTHON" -c 'import fastapi, starlette, uvicorn, sqlite3, ssl; print("runtime OK", fastapi.__version__)' \
  || fail "упакованный runtime не может импортировать backend-зависимости"

log "self-contained runtime готов: $RUNTIME_DIR ($(du -sh "$RUNTIME_DIR" | awk '{print $1}'))"
