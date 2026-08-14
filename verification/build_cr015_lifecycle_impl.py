from __future__ import annotations

from pathlib import Path

BASE = "e040011e54d1bc39461c9c01b6caaa568307c0c0"


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, got {count}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1. Native AppKit application lifecycle owner.
Path("scripts/macos/app_lifecycle.m").write_text(r'''#import <Cocoa/Cocoa.h>
#import <dispatch/dispatch.h>
#import <signal.h>

static NSString * const CWProductName = @"Мастерская косметолога";
static const NSTimeInterval CWShutdownTimeoutSeconds = 20.0;

@interface CWAppDelegate : NSObject <NSApplicationDelegate>
@property(nonatomic, strong) NSTask *runtimeTask;
@property(nonatomic, copy) NSArray<NSString *> *runtimeArguments;
@property(nonatomic) NSInteger frontendPort;
@property(nonatomic) BOOL terminationReplyPending;
@property(nonatomic) dispatch_source_t terminationSignalSource;
@end

@implementation CWAppDelegate

- (instancetype)init {
    self = [super init];
    if (self) {
        NSArray<NSString *> *arguments = [NSProcessInfo processInfo].arguments;
        self.runtimeArguments = arguments.count > 1
            ? [arguments subarrayWithRange:NSMakeRange(1, arguments.count - 1)]
            : @[];
        self.frontendPort = 5173;
        for (NSUInteger index = 0; index + 1 < self.runtimeArguments.count; index++) {
            if ([self.runtimeArguments[index] isEqualToString:@"--frontend-port"]) {
                NSInteger parsed = self.runtimeArguments[index + 1].integerValue;
                if (parsed > 0 && parsed <= 65535) {
                    self.frontendPort = parsed;
                }
            }
        }
    }
    return self;
}

- (void)applicationWillFinishLaunching:(NSNotification *)notification {
    (void)notification;
    [self installApplicationMenu];
    [self installTerminationSignalBridge];
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    (void)notification;
    [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
    [self launchRuntime];
}

- (void)installApplicationMenu {
    NSMenu *menuBar = [[NSMenu alloc] initWithTitle:@""];
    NSMenuItem *applicationItem = [[NSMenuItem alloc] initWithTitle:@"" action:nil keyEquivalent:@""];
    [menuBar addItem:applicationItem];

    NSMenu *applicationMenu = [[NSMenu alloc] initWithTitle:CWProductName];
    NSString *quitTitle = [NSString stringWithFormat:@"Завершить %@", CWProductName];
    NSMenuItem *quitItem = [[NSMenuItem alloc] initWithTitle:quitTitle
                                                     action:@selector(terminate:)
                                              keyEquivalent:@"q"];
    [applicationMenu addItem:quitItem];
    [applicationItem setSubmenu:applicationMenu];
    [NSApp setMainMenu:menuBar];
}

- (void)installTerminationSignalBridge {
    signal(SIGTERM, SIG_IGN);
    dispatch_source_t source = dispatch_source_create(
        DISPATCH_SOURCE_TYPE_SIGNAL, SIGTERM, 0, dispatch_get_main_queue()
    );
    __weak typeof(self) weakSelf = self;
    dispatch_source_set_event_handler(source, ^{
        if (weakSelf != nil) {
            [NSApp terminate:weakSelf];
        }
    });
    dispatch_resume(source);
    self.terminationSignalSource = source;
}

- (NSString *)runtimeHelperPath {
    return [[NSBundle mainBundle].bundlePath
        stringByAppendingPathComponent:@"Contents/MacOS/CosmeticWorkshopOSRuntime"];
}

- (void)launchRuntime {
    NSString *helper = [self runtimeHelperPath];
    if (![[NSFileManager defaultManager] isExecutableFileAtPath:helper]) {
        [self showCriticalAlertWithMessage:
            @"Приложение повреждено или распаковано не полностью. Удалите эту копию, распакуйте архив заново и откройте приложение ещё раз. Ваши данные не изменились."];
        [NSApp terminate:self];
        return;
    }

    NSTask *task = [[NSTask alloc] init];
    task.executableURL = [NSURL fileURLWithPath:helper];
    task.arguments = self.runtimeArguments;
    task.environment = [NSProcessInfo processInfo].environment;

    __weak typeof(self) weakSelf = self;
    task.terminationHandler = ^(NSTask *finishedTask) {
        dispatch_async(dispatch_get_main_queue(), ^{
            [weakSelf runtimeDidTerminate:finishedTask];
        });
    };

    NSError *error = nil;
    if (![task launchAndReturnError:&error]) {
        [self showCriticalAlertWithMessage:
            @"Не удалось запустить локальное приложение. Закройте эту копию и откройте её снова. Ваши данные не изменились."];
        [NSApp terminate:self];
        return;
    }
    self.runtimeTask = task;
}

- (void)runtimeDidTerminate:(NSTask *)task {
    if (task != self.runtimeTask) {
        return;
    }
    self.runtimeTask = nil;
    if (self.terminationReplyPending) {
        self.terminationReplyPending = NO;
        [NSApp replyToApplicationShouldTerminate:YES];
        return;
    }
    // The runtime owns all startup/failure UX. If it ends on its own, the native
    // lifecycle owner must leave too rather than remain as an empty Dock icon.
    [NSApp terminate:self];
}

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)sender {
    (void)sender;
    NSTask *task = self.runtimeTask;
    if (task == nil || !task.running) {
        return NSTerminateNow;
    }
    if (self.terminationReplyPending) {
        return NSTerminateLater;
    }

    self.terminationReplyPending = YES;
    [task terminate]; // SIGTERM -> existing Python packaged graceful-shutdown path.

    __weak typeof(self) weakSelf = self;
    dispatch_after(
        dispatch_time(DISPATCH_TIME_NOW, (int64_t)(CWShutdownTimeoutSeconds * NSEC_PER_SEC)),
        dispatch_get_main_queue(),
        ^{
            typeof(self) strongSelf = weakSelf;
            if (strongSelf == nil || !strongSelf.terminationReplyPending) {
                return;
            }
            NSTask *stillRunning = strongSelf.runtimeTask;
            if (stillRunning != nil && stillRunning.running) {
                [strongSelf showCriticalAlertWithMessage:
                    @"Приложение не успело корректно завершить локальную работу. Оно будет закрыто принудительно. Перед следующим запуском убедитесь, что резервная копия доступна."];
                kill(stillRunning.processIdentifier, SIGKILL);
            }
            strongSelf.terminationReplyPending = NO;
            [NSApp replyToApplicationShouldTerminate:YES];
        }
    );
    return NSTerminateLater;
}

- (BOOL)applicationShouldHandleReopen:(NSApplication *)sender hasVisibleWindows:(BOOL)flag {
    (void)sender;
    (void)flag;
    if (self.runtimeTask != nil && self.runtimeTask.running) {
        NSString *urlString = [NSString stringWithFormat:@"http://127.0.0.1:%ld", (long)self.frontendPort];
        [[NSWorkspace sharedWorkspace] openURL:[NSURL URLWithString:urlString]];
    }
    return YES;
}

- (void)showCriticalAlertWithMessage:(NSString *)message {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.alertStyle = NSAlertStyleCritical;
    alert.messageText = CWProductName;
    alert.informativeText = message;
    [alert addButtonWithTitle:@"Закрыть"];
    [alert runModal];
}

@end

int main(int argc, const char *argv[]) {
    (void)argc;
    (void)argv;
    @autoreleasepool {
        NSApplication *application = [NSApplication sharedApplication];
        [application setActivationPolicy:NSApplicationActivationPolicyRegular];
        CWAppDelegate *delegate = [[CWAppDelegate alloc] init];
        application.delegate = delegate;
        [application run];
    }
    return 0;
}
''', encoding="utf-8")

# 2. Package the native lifecycle owner and retain the existing shell as a helper.
replace_once(
    "scripts/package_macos.sh",
    "command -v shasum >/dev/null 2>&1 || fail \"не найден shasum.\"",
    "command -v shasum >/dev/null 2>&1 || fail \"не найден shasum.\"\ncommand -v xcrun  >/dev/null 2>&1 || fail \"не найден xcrun — требуется стандартный macOS developer toolchain для сборки native lifecycle wrapper.\"",
)
replace_once(
    "scripts/package_macos.sh",
    '''cp "$SCRIPT_DIR/macos/bundle_bootstrap.sh" "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"\nchmod 755 "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"''',
    '''RUNTIME_HELPER="$BUNDLE_DIR/Contents/MacOS/${APP_NAME}Runtime"\ncp "$SCRIPT_DIR/macos/bundle_bootstrap.sh" "$RUNTIME_HELPER"\nchmod 755 "$RUNTIME_HELPER"\n\n# CR-015 / ADR 0022: the CFBundleExecutable must own a real AppKit event loop so\n# Finder/Dock Quit is a user-visible application lifecycle operation, not an\n# assumption that LaunchServices will signal a shell/Python process for us.\nxcrun --sdk macosx clang \\\n  -fobjc-arc -mmacosx-version-min=12.0 -framework Cocoa \\\n  "$SCRIPT_DIR/macos/app_lifecycle.m" \\\n  -o "$BUNDLE_DIR/Contents/MacOS/$APP_NAME" \\\n  || fail "не удалось собрать native macOS lifecycle wrapper"\nchmod 755 "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"''',
)

# 3. Structure verifier: native main executable + isolated runtime helper.
replace_once(
    "macos_package/verification.py",
    'BUNDLE_EXECUTABLE_NAME = "CosmeticWorkshopOS"\nBUNDLE_DISPLAY_NAME',
    'BUNDLE_EXECUTABLE_NAME = "CosmeticWorkshopOS"\nBUNDLE_RUNTIME_HELPER_NAME = "CosmeticWorkshopOSRuntime"\nBUNDLE_DISPLAY_NAME',
)
replace_once(
    "macos_package/verification.py",
    '''    checks.append(_check_bundle_executable(contents / "MacOS" / BUNDLE_EXECUTABLE_NAME))\n    checks.append(\n        _check_bootstrap_interpreter_isolation(contents / "MacOS" / BUNDLE_EXECUTABLE_NAME)\n    )''',
    '''    native_executable = contents / "MacOS" / BUNDLE_EXECUTABLE_NAME\n    runtime_helper = contents / "MacOS" / BUNDLE_RUNTIME_HELPER_NAME\n    checks.append(_check_bundle_executable(native_executable))\n    checks.append(_check_native_lifecycle_executable(native_executable))\n    checks.append(_check_runtime_helper(runtime_helper))\n    checks.append(_check_bootstrap_interpreter_isolation(runtime_helper))''',
)
replace_once(
    "macos_package/verification.py",
    '''    return Check("bundle_executable", True)\n\n\ndef _check_bootstrap_interpreter_isolation''',
    '''    return Check("bundle_executable", True)\n\n\nMACHO_MAGICS = {\n    b"\\xfe\\xed\\xfa\\xce", b"\\xce\\xfa\\xed\\xfe",\n    b"\\xfe\\xed\\xfa\\xcf", b"\\xcf\\xfa\\xed\\xfe",\n    b"\\xca\\xfe\\xba\\xbe", b"\\xbe\\xba\\xfe\\xca",\n    b"\\xca\\xfe\\xba\\xbf", b"\\xbf\\xba\\xfe\\xca",\n}\n\n\ndef _check_native_lifecycle_executable(executable_path: Path) -> Check:\n    if not executable_path.is_file():\n        return Check("native_lifecycle_executable", False, "native lifecycle executable is missing")\n    try:\n        magic = executable_path.read_bytes()[:4]\n    except OSError as exc:\n        return Check("native_lifecycle_executable", False, f"native executable is unreadable: {exc}")\n    if magic not in MACHO_MAGICS:\n        return Check(\n            "native_lifecycle_executable", False,\n            "CFBundleExecutable is not a Mach-O native application lifecycle binary",\n        )\n    return Check("native_lifecycle_executable", True)\n\n\ndef _check_runtime_helper(helper_path: Path) -> Check:\n    if not helper_path.is_file():\n        return Check("bundle_runtime_helper", False, "CosmeticWorkshopOSRuntime is missing")\n    if not helper_path.stat().st_mode & stat.S_IXUSR:\n        return Check("bundle_runtime_helper", False, "runtime helper is not executable")\n    if not helper_path.read_bytes().startswith(b"#!"):\n        return Check("bundle_runtime_helper", False, "runtime helper is not the expected script")\n    return Check("bundle_runtime_helper", True)\n\n\ndef _check_bootstrap_interpreter_isolation''',
)
replace_once(
    "macos_package/verification.py",
    '''    candidates = [contents / "Info.plist", contents / "MacOS" / BUNDLE_EXECUTABLE_NAME]''',
    '''    candidates = [\n        contents / "Info.plist",\n        contents / "MacOS" / BUNDLE_EXECUTABLE_NAME,\n        contents / "MacOS" / BUNDLE_RUNTIME_HELPER_NAME,\n    ]''',
)

# 4. Synthetic package fixture mirrors native-main + helper topology.
replace_once(
    "macos_package/tests/packaging_fixtures.py",
    '''    # The real template, not a stub. The structure gate inspects the bootstrap\n    # that is actually inside a bundle, so the fixture has to carry the same\n    # script the build installs — otherwise these tests would validate a\n    # placeholder while the shipped script drifted.\n    executable = macos / "CosmeticWorkshopOS"\n    executable.write_text(bootstrap_template_source(), encoding="utf-8")\n    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)''',
    '''    # CR-015 topology: a native Mach-O is the CFBundleExecutable and the real\n    # isolation bootstrap remains a separate executable runtime helper. The\n    # synthetic native file only needs a valid Mach-O magic for pure structure\n    # inspection; live execution is covered by exact-package macOS smoke.\n    executable = macos / "CosmeticWorkshopOS"\n    executable.write_bytes(b"\\xcf\\xfa\\xed\\xfe" + b"synthetic-native-lifecycle")\n    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)\n    runtime_helper = macos / "CosmeticWorkshopOSRuntime"\n    runtime_helper.write_text(bootstrap_template_source(), encoding="utf-8")\n    runtime_helper.chmod(runtime_helper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)''',
)

# 5. Adapt deterministic structure tests to the split executable/helper contract.
test_path = Path("macos_package/tests/test_macos_package_structure.py")
test_text = test_path.read_text(encoding="utf-8")
test_text = test_text.replace(
    '        "bundle_executable",\n        "bundled_runtime",',
    '        "bundle_executable",\n        "native_lifecycle_executable",\n        "bundle_runtime_helper",\n        "bootstrap_interpreter_isolation",\n        "bundled_runtime",',
    1,
)
test_text = test_text.replace("def test_a_non_executable_bootstrap_fails", "def test_a_non_executable_native_lifecycle_fails", 1)
test_text = test_text.replace("def test_a_missing_bootstrap_fails", "def test_a_missing_native_lifecycle_fails", 1)
marker = "# -- packaged interpreter isolation ----------------------------------------"
if test_text.count(marker) != 1:
    raise SystemExit("test isolation marker mismatch")
head, tail = test_text.split(marker, 1)
next_marker = "# -- self-contained runtime ------------------------------------------------"
if tail.count(next_marker) != 1:
    raise SystemExit("test runtime marker mismatch")
isolation, rest = tail.split(next_marker, 1)
isolation = isolation.replace("Contents/MacOS/CosmeticWorkshopOS", "Contents/MacOS/CosmeticWorkshopOSRuntime")
insert = '''\n\ndef test_the_main_executable_must_be_native_macho(tmp_path):\n    bundle = build_app_bundle(tmp_path)\n    executable = bundle / "Contents/MacOS/CosmeticWorkshopOS"\n    executable.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")\n    assert "native_lifecycle_executable" in failures_of(bundle)\n\n\ndef test_the_runtime_helper_is_required(tmp_path):\n    bundle = build_app_bundle(tmp_path)\n    helper = bundle / "Contents/MacOS/CosmeticWorkshopOSRuntime"\n    helper.unlink()\n    failures = failures_of(bundle)\n    assert "bundle_runtime_helper" in failures\n    assert "bootstrap_interpreter_isolation" in failures\n\n'''
test_text = head + insert + marker + isolation + next_marker + rest
test_path.write_text(test_text, encoding="utf-8")

# 6. Focused source-level contract catches accidental removal of AppKit ownership.
Path("macos_package/tests/test_native_macos_lifecycle_source.py").write_text(r'''from pathlib import Path

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


def test_package_script_compiles_native_main_and_keeps_runtime_helper():
    text = PACKAGE_SCRIPT.read_text(encoding="utf-8")
    assert "xcrun --sdk macosx clang" in text
    assert "-framework Cocoa" in text
    assert "app_lifecycle.m" in text
    assert 'RUNTIME_HELPER="$BUNDLE_DIR/Contents/MacOS/${APP_NAME}Runtime"' in text
    assert 'bundle_bootstrap.sh" "$RUNTIME_HELPER"' in text
''', encoding="utf-8")

print("CR-015 lifecycle implementation prepared from", BASE)
