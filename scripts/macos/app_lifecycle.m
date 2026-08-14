#import <Cocoa/Cocoa.h>
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
