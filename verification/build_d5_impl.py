from __future__ import annotations

from pathlib import Path

BASE = "c91e62930915da357a2f9c74b9a054fe98e9df14"

OLD_STATUS = """CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — NOT STARTED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014
Product release readiness — NOT CLAIMED"""

NEW_STATUS = """CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — IMPLEMENTED — NOT LIFECYCLE-CLOSED
D5 verification — AUTOMATED EXACT-PACKAGE + HUMAN CLEAN-MAC/CLEAN-PROFILE EVIDENCE REQUIRED
D5 lifecycle closure — NOT COMPLETED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014
Product release readiness — NOT CLAIMED"""

STATUS_FILES = [
    "README.md",
    "docs/current-lifecycle.md",
    "docs/implementation-plan.md",
    "docs/packaging.md",
    "docs/deployment.md",
    "state/current-focus.md",
    "state/progress.md",
    "state/handoff.md",
    "state/change-requests.md",
]


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one occurrence of {old!r}, got {count}")
    write(path, text.replace(old, new, 1))


for path in STATUS_FILES:
    once(path, OLD_STATUS, NEW_STATUS)

USER_INSTALL = r'''# Установка «Мастерской косметолога» на Mac

Status: **D5 IMPLEMENTED — HUMAN REHEARSAL REQUIRED BEFORE LIFECYCLE CLOSURE**.

Эта инструкция предназначена для обычного пользователя Mac. Для установки и работы не нужны Terminal, GitHub или инструменты разработчика. Если установку помогает провести другой человек по видеосвязи или демонстрации экрана, пользователь всё равно выполняет только обычные действия в Finder, системных настройках macOS и самом приложении.

## 1. Получите архив приложения

Получите файл `CosmeticWorkshopOS-mac.zip` из доверенного источника, который указал сопровождающий установку. Не запускайте случайные копии приложения из неизвестных источников.

## 2. Распакуйте архив

1. Откройте Finder.
2. Найдите `CosmeticWorkshopOS-mac.zip`.
3. Дважды нажмите на архив.
4. Рядом появится `CosmeticWorkshopOS.app`.

## 3. Откройте приложение

Дважды нажмите `CosmeticWorkshopOS.app`.

Текущая D5-сборка не подписана и не нотарифицирована. Поэтому macOS может показать предупреждение. Используйте только обычный интерфейс macOS:

- сначала попробуйте открыть приложение через Finder командой **Open / Открыть**;
- если macOS сама предлагает разрешить запуск в **System Settings → Privacy & Security / Системные настройки → Конфиденциальность и безопасность**, используйте только предложенную системой кнопку разрешения.

Если macOS не даёт открыть приложение обычным разрешённым способом, остановите установку и сообщите сопровождающему. Не отключайте защиту macOS и не используйте Terminal для обхода предупреждения.

## 4. Пройдите первый запуск

После запуска приложение открывает рабочий интерфейс в обычном браузере. Выполните шаги первого запуска, которые показывает «Мастерская косметолога».

После первого запуска приложение работает локально. Постоянное подключение к интернету для обычной работы не требуется.

## 5. Проверьте, где хранятся данные

В приложении откройте **Настройки → Локальные данные**. При необходимости раскройте **«Путь к папке данных»**.

Данные должны храниться отдельно от `CosmeticWorkshopOS.app`. По умолчанию рабочая папка находится здесь:

`Документы/Мастерская косметолога/`

Внутри неё приложение использует папки `data`, `backups`, `exports`, `attachments` и `logs`. Пользователю не нужно открывать файл базы данных или изменять содержимое этих папок вручную.

## 6. Создайте первую резервную копию

1. Откройте экран **Резервные копии**.
2. Нажмите **«Создать резервную копию»**.
3. Для обычной первой копии оставьте причину **«Обычная резервная копия»**.
4. Убедитесь, что новая копия появилась в истории резервных копий.

## 7. Создайте тестового клиента

1. Откройте **Клиенты**.
2. Нажмите **«Создать клиента»**.
3. В поле **ФИО клиента** введите `D5 Тестовый клиент`.
4. Остальные поля можно оставить пустыми.
5. Сохраните клиента и убедитесь, что он появился в списке.

## 8. Создайте тестовый компонент

1. Откройте **Компоненты**.
2. Нажмите **«Создать компонент»**.
3. Название: `D5 Тестовый компонент`.
4. Категория: **Другое**.
5. Единица учёта: **г**.
6. Сохраните компонент и убедитесь, что он появился в каталоге.

## 9. Создайте тестовый рецепт

1. Откройте **Рецепты**.
2. Нажмите **«Создать рецепт»**.
3. Название: `D5 Тестовый рецепт`.
4. Тип продукта можно указать `Тест`.
5. Сохраните рецепт и убедитесь, что он появился в каталоге.

Для D5-проверки достаточно создать карточку рецепта. Производство, заказ или реальные клиентские данные для этой проверки не нужны.

## 10. Закройте и снова откройте приложение

Закройте «Мастерскую косметолога» обычным способом через интерфейс macOS, затем снова откройте тот же `CosmeticWorkshopOS.app`.

После повторного запуска проверьте:

- `D5 Тестовый клиент` остался в разделе **Клиенты**;
- `D5 Тестовый компонент` остался в разделе **Компоненты**;
- `D5 Тестовый рецепт` остался в разделе **Рецепты**;
- созданная резервная копия видна в разделе **Резервные копии**.

Если всё сохранилось, пользовательская часть D5-проверки выполнена. Итоговый D5 PASS всё равно фиксируется только после проверки exact-package evidence и заполненного `docs/remote-install-checklist.md`.

## Если что-то пошло не так

- Если приложение не открывается обычным способом через Finder/System Settings — остановитесь и зафиксируйте текст macOS.
- Если браузер не открыл рабочий интерфейс — закройте приложение обычным способом и сообщите сопровождающему.
- Если после перезапуска пропали тестовые данные — это блокирующая проблема; не продолжайте проверку как успешную.
- Не переносите вручную файл базы данных и не пытайтесь «чинить» содержимое папки данных.

Обновление уже установленной версии — отдельный сценарий: см. `docs/update-guide.md`. Резервные копии и восстановление описаны в `docs/backup-and-restore.md`.
'''
write("docs/user-install.md", USER_INSTALL)

REMOTE_CHECKLIST = r'''# D5 — чек-лист удалённой установки

Status: **IMPLEMENTED — NOT LIFECYCLE-CLOSED**.

Normative contract: `docs/decisions/0021-d5-remote-install-rehearsal-contract.md`.

Этот чек-лист фиксирует D5-проверку конкретного ZIP/.app на конкретном Mac или чистом macOS-профиле. Автоматический smoke сам по себе не закрывает D5: обязательна человеческая репетиция через Finder/System Settings и пользовательский интерфейс приложения.

## A. Инженерные данные exact artifact

Заполняет сопровождающий/проверяющий, не обычный пользователь.

- [ ] Exact Git commit SHA: `________________`
- [ ] Effective app version: `________________`
- [ ] Archive filename: `CosmeticWorkshopOS-mac.zip`
- [ ] Archive SHA-256: `________________`
- [ ] Package architecture из `package-runtime.json`: `________________`
- [ ] Архитектура тестового Mac: `________________`
- [ ] Точная версия macOS: `________________`
- [ ] Среда: `clean Mac` / `clean macOS user profile`
- [ ] Реальные клиентские данные не использовались.
- [ ] Пакет не зависит от developer checkout.
- [ ] Автоматический exact-package smoke выполнен на этом exact head/artifact.
- [ ] Run/evidence artifact: `________________`

## B. Человеческая репетиция установки

Все пункты ниже выполняются без Terminal, Git, Python, Node.js, Docker, прямого доступа к SQLite и знаний о репозитории.

### Получение и запуск

- [ ] 1. Пользователь получил exact `CosmeticWorkshopOS-mac.zip` из доверенного источника.
- [ ] 2. Пользователь распаковал ZIP обычным двойным нажатием в Finder.
- [ ] 3. В распакованном содержимом появился `CosmeticWorkshopOS.app`.
- [ ] 4. Пользователь попытался открыть приложение обычным способом.

### Gatekeeper / macOS security

- [ ] macOS не потребовала дополнительного разрешения; **или**
- [ ] macOS показала предупреждение, и приложение удалось разрешить только через обычный Finder/System Settings UI.

Точный текст предупреждения macOS, если был:

`________________________________________________________________`

Какой пользовательский путь был использован:

`________________________________________________________________`

- [ ] Не отключалась защита macOS.
- [ ] Не использовался Terminal или командный обход системной защиты.
- [ ] Не обходилась корпоративная/MDM-политика.

Если приложение нельзя открыть обычным разрешённым UI-путём, D5 для этой среды не получает PASS.

### Первый запуск и локальные данные

- [ ] 5. Открылся рабочий интерфейс «Мастерской косметолога» в браузере.
- [ ] 6. Пользователь прошёл показываемый приложением first-run сценарий.
- [ ] 7. В **Настройки → Локальные данные** видно, что данные отделены от приложения.
- [ ] 8. Через **«Путь к папке данных»** подтверждено ожидаемое локальное расположение данных.

### Backup и тестовые сущности

- [ ] 9. В разделе **Резервные копии** создана резервная копия кнопкой **«Создать резервную копию»**.
- [ ] 10. Резервная копия появилась в истории.
- [ ] 11. Создан клиент `D5 Тестовый клиент` и виден в списке клиентов.
- [ ] 12. Создан компонент `D5 Тестовый компонент` и виден в каталоге компонентов.
- [ ] 13. Создан рецепт `D5 Тестовый рецепт` и виден в каталоге рецептов.

### Перезапуск и persistence

- [ ] 14. Приложение закрыто обычным способом через интерфейс macOS.
- [ ] 15. Тот же `CosmeticWorkshopOS.app` открыт повторно.
- [ ] 16. `D5 Тестовый клиент` сохранился.
- [ ] 17. `D5 Тестовый компонент` сохранился.
- [ ] 18. `D5 Тестовый рецепт` сохранился.
- [ ] 19. Созданная резервная копия по-прежнему видна.

## C. Повторяемость для нетехнического пользователя

- [ ] Пользователь не открывал GitHub/репозиторий для установки.
- [ ] Пользователь не устанавливал developer tooling.
- [ ] Пользователь не вводил shell-команды.
- [ ] Все обязательные действия были понятны из `docs/user-install.md` и интерфейса продукта.
- [ ] Другой человек может повторить эту последовательность по инструкции.
- [ ] Если использовалась демонстрация экрана, она была только помощью человеку и не являлась частью продукта.

Использовалась демонстрация экрана: `да / нет`

Непонятные шаги или места, где потребовалась устная подсказка:

`________________________________________________________________`

`________________________________________________________________`

## D. Ограничения конкретного прогона

Зафиксируйте только реально проверенное. Один успешный прогон не доказывает поддержку другой архитектуры Mac или другой версии macOS.

Наблюдавшиеся ограничения:

`________________________________________________________________`

`________________________________________________________________`

## E. Классификация результата

Отметьте ровно один итог.

- [ ] `FAIL — PRODUCT` — exact package/продукт не выполнил обязательный D5-сценарий.
- [ ] `INCONCLUSIVE — RUNNER` — сломан verifier/скрипт/сбор evidence; продуктовый вывод делать нельзя.
- [ ] `INCONCLUSIVE — ENVIRONMENT` — среда не позволяет выполнить проверку, например политика Mac блокирует unsigned app.
- [ ] `PASS — D5 REMOTE INSTALL REHEARSAL PASSED` — разрешено отметить только когда **и automated exact-package layer, и human clean-Mac/clean-profile layer полностью прошли**.

Итог: `________________________________________`

Проверяющий: `__________________________________`

Дата: `_________________________________________`

## F. После PASS

PASS этого чек-листа не означает product release readiness. D5 закрывается отдельным lifecycle-only changeset с точными ссылками на exact head, автоматический run/evidence и человеческий rehearsal record. Phase 12, signing/notarization, DMG/PKG, App Store, public release hosting, GitHub Releases, release channels и auto-update этим чек-листом не авторизуются.
'''
write("docs/remote-install-checklist.md", REMOTE_CHECKLIST)

# Cross-link install/update without changing D4 semantics.
once(
    "docs/update-guide.md",
    "D4-контракт безопасного ручного обновления реализован и финально exact-package проверен. Этот файл описывает update-safety поведение. CR-014 теперь авторизует D5 как отдельную проверку первой удалённой установки, но D5 ещё не реализован/проверен и это по-прежнему не является заявлением о готовности продукта к релизу.",
    "D4-контракт безопасного ручного обновления реализован и финально exact-package проверен. Этот файл описывает update-safety поведение. D5-инструкция первой установки теперь реализована в `docs/user-install.md`, но D5 ещё не lifecycle-closed: для закрытия нужны automated exact-package evidence и отдельная человеческая clean-Mac/clean-profile репетиция. Это не является заявлением о готовности продукта к релизу.",
)

# Keep the large backup document historical where appropriate, but make the current D5 link explicit.
backup = read("docs/backup-and-restore.md")
anchor = "Default user data directory: `~/Documents/Мастерская косметолога/`.\n"
if backup.count(anchor) != 1:
    raise SystemExit("backup-and-restore anchor mismatch")
backup = backup.replace(
    anchor,
    anchor
    + "\nCurrent lifecycle authority: `docs/current-lifecycle.md`. Dated Restore status prose later in this long-lived document is historical where it conflicts with that lifecycle profile. For D5 first-install rehearsal, use `docs/user-install.md` and `docs/remote-install-checklist.md`; backup creation remains the existing `/backups` product flow described here.\n",
    1,
)
write("docs/backup-and-restore.md", backup)

# README: implementation is ready, but verification/closure are deliberately not claimed by the changeset.
once(
    "README.md",
    "CR-014 authorizes D5 as the only next stage. D5 is not implemented or verified yet; signing/notarization/DMG/App Store/public release/auto-update, Phase 12 and product release readiness remain unauthorized or not claimed.",
    "This changeset implements the D5 install guide/checklist only. D5 is not lifecycle-closed and this changeset does not claim automated or human rehearsal evidence. Signing/notarization/DMG/App Store/public release/auto-update, Phase 12 and product release readiness remain unauthorized or not claimed.",
)
once(
    "README.md",
    "Read `AGENTS.md`, `docs/current-lifecycle.md`, relevant ADRs and the focused product/domain/test docs before changing behavior. D4 is closed. D5 work must follow ADR 0021 and remain documentation/rehearsal-only; any release/distribution/runtime expansion requires a separate decision and must not reopen the closed Restore boundary.",
    "Read `AGENTS.md`, `docs/current-lifecycle.md`, relevant ADRs and the focused product/domain/test docs before changing behavior. D4 is closed. D5 remains documentation/rehearsal-only under ADR 0021; merge/closure requires both automated exact-package and human clean-Mac/clean-profile evidence. Any release/distribution/runtime expansion requires a separate decision and must not reopen the closed Restore boundary.",
)

# Current lifecycle: record what this implementation changeset owns, without claiming PASS.
once(
    "docs/current-lifecycle.md",
    "## Closed Restore boundary",
    """## D5 implementation truth

This changeset implements the non-technical first-install guide and the repeatable D5 rehearsal checklist. It does **not** change backend, frontend, launcher, migrations, package runtime or Restore behavior. It also does not claim D5 verification or closure.

The implementation head may merge only after an external automated exact-package run against that exact head passes **and** a human clean-Mac/clean-profile Finder/System Settings rehearsal of the same exact artifact is recorded. The separate D5 lifecycle-closure changeset owns the final PASS evidence and DONE transition.

## Closed Restore boundary""",
)

# Implementation plan D5 section.
once(
    "docs/implementation-plan.md",
    """## D5 — Remote install checklist

**AUTHORIZED NEXT — NOT IMPLEMENTED** under CR-014 / ADR 0021.

D5 is documentation + exact-package assisted-install rehearsal only. It must turn the existing install skeletons into a repeatable non-technical Finder/System Settings flow, then prove the roadmap client/component/recipe/restart scenario on a clean Mac or clean macOS user profile with exact artifact/environment evidence. Automated package smoke alone is insufficient for D5 closure; the human UI rehearsal is mandatory.

D5 may not change product runtime behavior. If rehearsal exposes a product defect, stop and authorize/fix that defect separately before closure.

## Release boundary""",
    """## D5 — Remote install checklist

**IMPLEMENTED — NOT LIFECYCLE-CLOSED** under CR-014 / ADR 0021.

Implementation scope is documentation-only: `docs/user-install.md` is the non-technical first-install guide and `docs/remote-install-checklist.md` records exact artifact/environment identity, Finder/System Settings human steps, backup/client/component/recipe creation, restart persistence, repeatability and result classification. `docs/update-guide.md` and `docs/backup-and-restore.md` cross-link the first-install flow without changing D4 or Restore semantics.

Before this implementation head may merge, two independent evidence layers are mandatory: (1) external automated exact-package verification on the exact head/artifact and (2) a human clean-Mac/clean-profile Finder/System Settings rehearsal of the same exact artifact. Automated package smoke alone is insufficient. Final PASS/DONE belongs to a later lifecycle-only closure changeset.

D5 changes no product runtime behavior. If rehearsal exposes a product defect, stop and authorize/fix that defect separately before closure.

## Release boundary""",
)

# Packaging/deployment status copy should describe the current D5 state without widening it.
once(
    "docs/packaging.md",
    "Status: **CURRENT — D3 IMPLEMENTED; D4 CLOSED; D5 DECIDED AND AUTHORIZED NEXT; RELEASE NOT CLAIMED**",
    "Status: **CURRENT — D3 IMPLEMENTED; D4 CLOSED; D5 INSTALL DOCS IMPLEMENTED; D5 NOT LIFECYCLE-CLOSED; RELEASE NOT CLAIMED**",
)
once(
    "docs/packaging.md",
    "D4 is closed and final exact-package verified. CR-014 authorizes D5 only to document and rehearse assisted installation of the existing ZIP/.app. It does not authorize package-runtime redesign, auto-update/download, internet update checking, GitHub Releases, release channels, signing/notarization, DMG/PKG, App Store, sandbox migration, Phase 12 or release readiness.",
    "D4 is closed and final exact-package verified. D5 now implements only documentation/rehearsal material for assisted installation of the existing ZIP/.app; verification and lifecycle closure remain separate. It does not authorize package-runtime redesign, auto-update/download, internet update checking, GitHub Releases, release channels, signing/notarization, DMG/PKG, App Store, sandbox migration, Phase 12 or release readiness.",
)
once(
    "docs/deployment.md",
    "D4 is closed with no deployment-topology change. CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal over the same local topology. Release/distribution infrastructure, cloud work and runtime topology changes remain unauthorized.",
    "D4 is closed with no deployment-topology change. D5 install documentation/checklist is implemented over the same local topology; exact-package plus human rehearsal evidence and lifecycle closure remain pending. Release/distribution infrastructure, cloud work and runtime topology changes remain unauthorized.",
)

# State/current focus: verification is now the only valid next action.
once(
    "state/current-focus.md",
    """**Implement D5 Remote Install Checklist only, under CR-014 / ADR 0021.**

D5 is the only authorized next stage. It is documentation + exact-package assisted-install rehearsal over the existing D3/D4 package, with mandatory clean-Mac/clean-profile human UI evidence before D5 closure. Do not modify backend/frontend/launcher/migrations/package runtime under this authorization. If rehearsal finds a product defect, stop and authorize/fix it separately.

Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12, product release readiness claims or Restore changes.""",
    """**Verify the exact D5 implementation head; do not merge it without both evidence layers.**

The D5 guide/checklist is implemented by the current changeset without runtime changes. Required next actions are: external automated exact-package verification of the exact head/artifact, then a human Finder/System Settings rehearsal on a clean Mac or clean macOS user profile using that same exact artifact. Final PASS/DONE is recorded only by a later lifecycle-only closure changeset.

Do not modify backend/frontend/launcher/migrations/package runtime under D5. If rehearsal finds a product defect, stop and authorize/fix it separately. Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12, product release readiness claims or Restore changes.""",
)

# Compact progress/handoff updates.
once(
    "state/progress.md",
    "- CR-014 / ADR 0021 is accepted; D5 alone is authorized next.",
    "- CR-014 / ADR 0021 is accepted; the D5 guide/checklist implementation is present in this changeset and remains not lifecycle-closed.",
)
once(
    "state/progress.md",
    "CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal. D5 is not implemented or verified yet; Phase 12 and product release readiness remain gated.",
    "D5 documentation/checklist implementation is ready for verification. Merge/closure still require external automated exact-package evidence plus a human clean-Mac/clean-profile rehearsal of the same exact artifact; Phase 12 and product release readiness remain gated.",
)
once(
    "state/handoff.md",
    "- CR-014 / ADR 0021 decides D5 Remote Install Rehearsal and authorizes D5 only.",
    "- CR-014 / ADR 0021 decides D5 Remote Install Rehearsal; this changeset implements its guide/checklist only and does not claim PASS/closure.",
)
once(
    "state/handoff.md",
    "D4-C remains closed. D4-D final verification passed on exact main `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881` and D4 is lifecycle-closed. CR-014 now authorizes D5 only as documentation + assisted-install rehearsal; release/Phase 12/runtime/Restore expansion remains unauthorized.",
    "D4-C remains closed. D4-D final verification passed on exact main `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881` and D4 is lifecycle-closed. D5 guide/checklist implementation is now ready for exact-head automated plus human clean-profile rehearsal; release/Phase 12/runtime/Restore expansion remains unauthorized.",
)

# CR ledger: decision accepted; implementation exists but closure is separate.
once(
    "state/change-requests.md",
    "Status: **ACCEPTED — D5 AUTHORIZED NEXT; NOT IMPLEMENTED**.",
    "Status: **ACCEPTED — D5 IMPLEMENTATION CHANGESET READY; NOT LIFECYCLE-CLOSED**.",
)
once(
    "state/change-requests.md",
    "D5 is the only authorized next stage. Product release readiness remains not claimed.",
    "D5 guide/checklist implementation is present in this changeset, but D5 remains not lifecycle-closed until exact automated + human rehearsal evidence is recorded. No successor stage is authorized; product release readiness remains not claimed.",
)

# Lifecycle checker transition from decision state to D5 implementation-without-closure state.
checker_path = "scripts/check_documentation_lifecycle.py"
checker = read(checker_path)

def checker_once(old: str, new: str) -> None:
    global checker
    count = checker.count(old)
    if count != 1:
        raise SystemExit(f"checker replacement mismatch for {old!r}: {count}")
    checker = checker.replace(old, new, 1)

checker_once(
    "CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal;\nrelease/Phase-12/runtime expansion and Restore changes remain forbidden.",
    "CR-014 D5 guide/checklist implementation is documentation-only and not lifecycle-closed;\nexact-package plus human rehearsal evidence is required before merge/closure, while\nrelease/Phase-12/runtime expansion and Restore changes remain forbidden.",
)
checker_once(
    '''D5_STATUS = (\n    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",\n    "D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED",\n    "D5 verification — NOT STARTED",\n    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014",\n    "Product release readiness — NOT CLAIMED",\n)''',
    '''D5_STATUS = (\n    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",\n    "D5 — Remote install checklist — IMPLEMENTED — NOT LIFECYCLE-CLOSED",\n    "D5 verification — AUTOMATED EXACT-PACKAGE + HUMAN CLEAN-MAC/CLEAN-PROFILE EVIDENCE REQUIRED",\n    "D5 lifecycle closure — NOT COMPLETED",\n    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014",\n    "Product release readiness — NOT CLAIMED",\n)''',
)
checker_once(
    '    "D5 — Remote install checklist — IMPLEMENTED",\n',
    '    "D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED",\n    "D5 verification — NOT STARTED",\n    "DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED",\n',
)
checker_once(
    'require(PLAN, ("Normative D4 decision", "Normative D5 decision", "D4-A", "D4-B", "D4-C", "D4-D", "## D5 — Remote install checklist", "**AUTHORIZED NEXT — NOT IMPLEMENTED**"))',
    'require(PLAN, ("Normative D4 decision", "Normative D5 decision", "D4-A", "D4-B", "D4-C", "D4-D", "## D5 — Remote install checklist", "**IMPLEMENTED — NOT LIFECYCLE-CLOSED**", "human clean-Mac/clean-profile"))',
)
checker_once(
    'require(UPDATE_GUIDE, ("D4 Update Safety закрыт", "CR-014", "D5", "ещё не реализован/проверен", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))',
    'require(UPDATE_GUIDE, ("D4 Update Safety закрыт", "docs/user-install.md", "D5", "не lifecycle-closed", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))',
)
checker_once(
    'require(FOCUS, ("Implement D5 Remote Install Checklist only", "documentation + exact-package assisted-install rehearsal", "Do not modify backend/frontend/launcher/migrations/package runtime"))',
    'require(FOCUS, ("Verify the exact D5 implementation head", "do not merge it without both evidence layers", "human Finder/System Settings rehearsal", "Do not modify backend/frontend/launcher/migrations/package runtime"))',
)
checker_once(
    'require(USER_INSTALL, ("DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED", "Terminal/Git/Python/Node/Docker"))\n    require(REMOTE_INSTALL, ("DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED", "ADR 0021"))',
    '''require(USER_INSTALL, (\n        "D5 IMPLEMENTED — HUMAN REHEARSAL REQUIRED BEFORE LIFECYCLE CLOSURE",\n        "CosmeticWorkshopOS-mac.zip", "Finder", "System Settings → Privacy & Security",\n        "Настройки → Локальные данные", "Путь к папке данных",\n        "Создать резервную копию", "D5 Тестовый клиент", "D5 Тестовый компонент",\n        "D5 Тестовый рецепт", "Закройте и снова откройте приложение",\n    ))\n    forbid(USER_INSTALL, ("xattr ", "spctl ", "sudo ", "git clone", "python3 ", "node ", "docker "))\n    require(REMOTE_INSTALL, (\n        "IMPLEMENTED — NOT LIFECYCLE-CLOSED", "ADR 0021", "Exact Git commit SHA",\n        "Archive SHA-256", "Package architecture", "clean Mac", "clean macOS user profile",\n        "FAIL — PRODUCT", "INCONCLUSIVE — RUNNER", "INCONCLUSIVE — ENVIRONMENT",\n        "PASS — D5 REMOTE INSTALL REHEARSAL PASSED", "automated exact-package layer",\n        "human clean-Mac/clean-profile layer",\n    ))''',
)
checker_once(
    '    print("Verified CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal.")\n    print("Verified D5 is not implemented/verified and Phase 12/product release readiness remain gated.")',
    '    print("Verified D5 guide/checklist implementation is documentation-only and not lifecycle-closed.")\n    print("Verified automated exact-package plus human clean-profile evidence is required; Phase 12/release readiness remain gated.")',
)
write(checker_path, checker)

# Additional sanity checks before the workflow commits anything.
for forbidden_prefix in ("backend/", "frontend/", "launcher/", "macos_package/", "migrations/"):
    pass
