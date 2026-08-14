from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts" / "macos" / "app_lifecycle.m"
PACKAGE_SCRIPT = ROOT / "scripts" / "package_macos.sh"


def test_native_lifecycle_source_owns_appkit_quit_without_product_logic():
    text = SOURCE.read_text(encoding="utf-8")
    assert "<NSApplicationDelegate>" in text
    assert "applicationShouldTerminate:" in text
    assert "NSTerminateLater" in text
    assert "replyToApplicationShouldTerminate:YES" in text
    assert "[task terminate]" in text
    assert "applicationShouldHandleReopen:" in text
    assert "NSWorkspace" in text
    assert "CosmeticWorkshopOSRuntime" in text
    assert "NSApplicationActivationPolicyRegular" in text
    assert "DISPATCH_SOURCE_TYPE_SIGNAL" in text
    forbidden = ("sqlite", "recipe", "inventory", "restore", "migration", "update_safety")
    lowered = text.lower()
    for token in forbidden:
        assert token not in lowered


def test_native_lifecycle_timeout_fails_closed_instead_of_orphaning_backend():
    text = SOURCE.read_text(encoding="utf-8")
    assert "CWShutdownTimeoutSeconds" in text
    assert "replyToApplicationShouldTerminate:NO" in text
    assert "осталось открытым" in text
    assert "SIGKILL" not in text
    assert "kill(" not in text


def test_package_script_compiles_native_main_and_keeps_runtime_helper():
    text = PACKAGE_SCRIPT.read_text(encoding="utf-8")
    assert "xcrun --sdk macosx clang" in text
    assert "-framework Cocoa" in text
    assert "app_lifecycle.m" in text
    assert 'RUNTIME_HELPER="$BUNDLE_DIR/Contents/MacOS/${APP_NAME}Runtime"' in text
    assert 'bundle_bootstrap.sh" "$RUNTIME_HELPER"' in text
