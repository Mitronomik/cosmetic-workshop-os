# Операторская установка и обновление одного пилотного клиента

Статус: **CR-017 PILOT SUPPORT PROCEDURE — НЕ ПУБЛИЧНАЯ ДИСТРИБУЦИЯ**

Нормативное решение: `docs/decisions/0024-single-client-operator-assisted-install.md`.

Этот сценарий используется только для одного известного пилотного клиента, пока самостоятельная публичная дистрибуция через Developer ID/notarization экономически не оправдана.

## Граница ответственности

- Клиент не вводит и не вставляет команды в Terminal.
- Команды выполняет support-оператор лично или через согласованный screen sharing.
- Gatekeeper остаётся глобально включённым.
- `sudo`, отключение SIP, `spctl --master-disable` и снижение Security Policy запрещены.
- Operator installer не меняет SQLite, Restore, backups, migration history или user-data directory.
- После публикации новой `.app` дальнейшую совместимость/backup/migration контролирует D4.

## Пакет

Support-оператор получает exact outer ZIP вида:

```text
CosmeticWorkshopOS-operator-assisted-<version>-<arch>.zip
└── CosmeticWorkshopOS-operator-assisted-<version>-<arch>/
    ├── CosmeticWorkshopOS-mac.zip
    ├── operator_install_update.sh
    └── OPERATOR-README.txt
```

`operator_install_update.sh` содержит immutable SHA-256 именно своего companion `CosmeticWorkshopOS-mac.zip`.

## Первая установка

1. Передайте outer ZIP на Mac клиента через согласованный канал.
2. Распакуйте outer ZIP обычным Finder.
3. Откройте Terminal как support-оператор.
4. Перетащите `operator_install_update.sh` из Finder в Terminal после `/bin/zsh ` либо перейдите в папку пакета.
5. Запустите скрипт. Клиент ничего не вводит.
6. Скрипт обязан сначала подтвердить SHA-256, Bundle ID, version, executable и architecture. При любой ошибке установка останавливается до `xattr` и до изменения установленной `.app`.
7. После PASS скрипт точечно снимает `com.apple.quarantine` только с verified staged `CosmeticWorkshopOS.app`.
8. Приложение устанавливается в `~/Applications/CosmeticWorkshopOS.app` и запускается обычным macOS способом.
9. После этого клиент использует только Finder/Dock/browser UI.

## Обновление

1. Передайте новый version-specific operator ZIP.
2. Support-оператор запускает новый `operator_install_update.sh` через Terminal.
3. Candidate полностью проверяется до изменения текущей `.app`.
4. Если приложение запущено, скрипт запрашивает обычный macOS Quit и ждёт полного завершения. Force Kill не считается успешным update path.
5. Текущая `.app` сохраняется в support directory как retained previous package.
6. Verified candidate публикуется на месте установленной `.app` и запускается.
7. D4 самостоятельно решает schema compatibility, before-migration backup, staged migration и UpdateLog.
8. Retained previous `.app` нельзя автоматически запускать как rollback после возможного schema commit.

## Обязательный smoke после установки

На clean Mac/clean profile после операторской установки проверьте:

- приложение запускается без Terminal после установки;
- backup создаётся;
- создаются тестовый клиент, компонент и рецепт;
- Dock → Quit штатно завершает приложение;
- повторный запуск через Finder работает;
- тестовые данные и backup сохранились;
- Terminal больше не нужен для обычной эксплуатации.

Успех этого сценария подтверждает только **single-client operator-assisted pilot deployment**. Он не является доказательством self-service/public distribution readiness.
