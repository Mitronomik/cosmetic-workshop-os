#!/usr/bin/env bash
#
# DEVELOPER-ONLY exact-head smoke runner for the C4-I Restore safety engine.
#
# This is NOT the product Restore workflow and must never be documented as one.
# `CR-010` forbids a terminal command as the user-facing workflow, and `C4-I`
# exposes no user-facing Restore entry point at all. This script exists so a
# developer can verify the internal engine at one exact published commit.
#
# It refuses to run unless HEAD is exactly the expected published SHA and the
# workspace is clean, and it verifies cleanliness again afterwards. Everything it
# creates lives in one temporary directory that the trap removes; it never
# touches the real user-data directory and never uses real user data.
#
# Usage:
#   scripts/c4_i_restore_smoke.sh <expected-published-head-sha>
#   C4_I_SMOKE_EXPECTED_HEAD=<sha> scripts/c4_i_restore_smoke.sh
#
# Result:
#   PASS           - every scenario held
#   FAIL PRODUCT   - the engine did not behave as the accepted contract requires
#   INCONCLUSIVE   - the smoke could not be run, so it proves nothing

set -euo pipefail

EXIT_PASS=0
EXIT_FAIL_PRODUCT=1
EXIT_INCONCLUSIVE=2

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPOSITORY_ROOT"

SMOKE_ROOT=""
EVIDENCE_FILE=""

cleanup() {
    # Kill anything this run started, then remove every temporary artifact.
    # Runs on success, failure and interruption alike, so no backend child and no
    # temporary directory outlives the smoke.
    if [ -n "${SMOKE_ROOT}" ] && [ -d "${SMOKE_ROOT}" ]; then
        pkill -f "COSMETIC_WORKSHOP_DB_PATH=${SMOKE_ROOT}" 2>/dev/null || true
        rm -rf "${SMOKE_ROOT}"
    fi
}
trap cleanup EXIT INT TERM

say() { printf '%s\n' "$*"; }

say "==============================================================="
say " C4-I Restore safety engine - DEVELOPER-ONLY verification"
say " Not a product workflow. Not a user-facing Restore entry point."
say "==============================================================="

EXPECTED_HEAD="${1:-${C4_I_SMOKE_EXPECTED_HEAD:-}}"
if [ -z "$EXPECTED_HEAD" ]; then
    say "INCONCLUSIVE: no expected published head was given."
    say "  Pass the exact published SHA as the first argument, or set"
    say "  C4_I_SMOKE_EXPECTED_HEAD. This runner will not test an unverified head."
    exit "$EXIT_INCONCLUSIVE"
fi

ACTUAL_HEAD="$(git rev-parse HEAD)"
if [ "$ACTUAL_HEAD" != "$EXPECTED_HEAD" ]; then
    say "INCONCLUSIVE: HEAD is not the expected published head."
    say "  expected: $EXPECTED_HEAD"
    say "  actual:   $ACTUAL_HEAD"
    exit "$EXIT_INCONCLUSIVE"
fi
say "Exact head verified: $ACTUAL_HEAD"

if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
    say "INCONCLUSIVE: the workspace is not clean before the smoke."
    git status --short --untracked-files=all
    exit "$EXIT_INCONCLUSIVE"
fi
say "Workspace clean before the smoke."

SMOKE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/c4i-restore-smoke.XXXXXX")"
EVIDENCE_FILE="${SMOKE_ROOT}/evidence.json"
say "Isolated temporary root: ${SMOKE_ROOT}"
say ""

set +e
env -u COSMETIC_WORKSHOP_DB_PATH -u COSMETIC_WORKSHOP_USER_DATA_DIR \
    python3 "${REPOSITORY_ROOT}/scripts/c4_i_restore_smoke.py" \
    --root "$SMOKE_ROOT" \
    --evidence "$EVIDENCE_FILE" \
    --head "$ACTUAL_HEAD"
DRIVER_STATUS=$?
set -e

say ""
if [ -f "$EVIDENCE_FILE" ]; then
    say "--- evidence -------------------------------------------------"
    cat "$EVIDENCE_FILE"
    say "--------------------------------------------------------------"
fi

if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
    say "INCONCLUSIVE: the smoke left the repository dirty."
    git status --short --untracked-files=all
    exit "$EXIT_INCONCLUSIVE"
fi
say "Workspace clean after the smoke. The tested branch was not modified."

case "$DRIVER_STATUS" in
    0) say "RESULT: PASS" ;;
    1) say "RESULT: FAIL PRODUCT" ;;
    *) say "RESULT: INCONCLUSIVE" ;;
esac
exit "$DRIVER_STATUS"
