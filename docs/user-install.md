# User Install Guide

Status: **DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED**. This is not yet the final remote-install procedure.

1. Скачать архив приложения.
2. Распаковать архив.
3. Открыть приложение.
4. Разрешить запуск в macOS, если нужно.
5. Пройти первый запуск.
6. Создать первый backup.

Планируемая папка данных пользователя:

```text
~/Documents/Мастерская косметолога/
  data/
    cosmetic_workshop.sqlite
  backups/
  exports/
  attachments/
  logs/
```

Примечание: D3/D4 уже дают реальный `CosmeticWorkshopOS.app` внутри ZIP и безопасный update path, но этот install guide ещё не прошёл D5 clean-profile rehearsal. До D5 PASS не трактовать его как release-ready инструкцию. Пользовательский сценарий не должен требовать Terminal/Git/Python/Node/Docker.
