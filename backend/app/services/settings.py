import json
import unicodedata
from datetime import UTC, datetime

from app.db.config import DatabaseConfig
from app.db.paths import resolve_user_data_paths
from app.models.settings import AppSetting
from app.repositories.settings import SettingsRepository
from app.schemas.settings import (
    AppSettingsInfo,
    LocalDataStatus,
    SettingsCapability,
    SettingsDefinition,
    SettingsDefinitionStatus,
    SettingsGroup,
    SettingsStatusResponse,
    WorkshopProfile,
    WorkshopProfileResponse,
    WorkshopProfileUpdateRequest,
)


PRODUCT_NAME = "Мастерская косметолога"
REPOSITORY_NAME = "cosmetic-workshop-os"


def read_app_settings(config: DatabaseConfig | None = None) -> list[AppSetting]:
    return SettingsRepository(config).list_settings()


class SettingsService:
    """Build read-only settings/status information without side effects."""

    def build_status(self) -> SettingsStatusResponse:
        user_paths = resolve_user_data_paths()
        return SettingsStatusResponse(
            generated_at=datetime.now(UTC).isoformat(),
            app=AppSettingsInfo(
                product_name=PRODUCT_NAME,
                repository_name=REPOSITORY_NAME,
                mode="Локальное приложение",
                local_first=True,
                internet_required=False,
                version=None,
            ),
            local_data=LocalDataStatus(
                user_data_separate_from_code=True,
                user_data_path_available=bool(user_paths.base_dir),
                user_data_path_display=str(user_paths.base_dir),
                backup_before_migration_required=True,
                message="Данные мастерской хранятся отдельно от кода приложения.",
            ),
            capabilities=_capabilities(),
            setting_groups=_setting_groups(),
            editable_settings_available=True,
            message="Профиль мастерской уже можно редактировать. Остальные настройки пока показаны как безопасная карта будущих возможностей.",
            warnings=[],
        )


def get_settings_status() -> SettingsStatusResponse:
    return SettingsService().build_status()


WORKSHOP_PROFILE_KEY = "workshop_profile"
WORKSHOP_PROFILE_DESCRIPTION = "Workshop profile settings: display-only identity fields for Settings and future documents."
PROFILE_LIMITS = {
    "workshop_name": 120,
    "master_name": 120,
    "workshop_contact_text": 500,
    "workshop_note": 500,
}
PROFILE_FIELD_LABELS = {
    "workshop_name": "Название мастерской",
    "master_name": "Имя мастера",
    "workshop_contact_text": "Контактный текст",
    "workshop_note": "Примечание",
}


class WorkshopProfileValidationError(ValueError):
    pass


class WorkshopProfileSettingsService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.repository = SettingsRepository(config)

    def get_profile(self) -> WorkshopProfileResponse:
        setting = self.repository.get_setting(WORKSHOP_PROFILE_KEY)
        profile = WorkshopProfile()
        updated_at = setting.updated_at if setting else None
        if setting and setting.value:
            try:
                profile = WorkshopProfile(**json.loads(setting.value))
            except (json.JSONDecodeError, TypeError, ValueError):
                profile = WorkshopProfile()
        return self._response(profile, updated_at, "Профиль мастерской загружен." if self._is_configured(profile) else "Профиль мастерской пока не заполнен.")

    def update_profile(self, request: WorkshopProfileUpdateRequest) -> WorkshopProfileResponse:
        profile = WorkshopProfile(
            workshop_name=self._clean_value("workshop_name", request.workshop_name),
            master_name=self._clean_value("master_name", request.master_name),
            workshop_contact_text=self._clean_value("workshop_contact_text", request.workshop_contact_text),
            workshop_note=self._clean_value("workshop_note", request.workshop_note),
        )
        self.repository.upsert_setting(
            WORKSHOP_PROFILE_KEY,
            json.dumps(profile.model_dump(), ensure_ascii=False),
            "json",
            WORKSHOP_PROFILE_DESCRIPTION,
        )
        return self.get_profile().model_copy(update={"message": "Профиль мастерской сохранен."})

    def _response(self, profile: WorkshopProfile, updated_at: str | None, message: str) -> WorkshopProfileResponse:
        return WorkshopProfileResponse(profile=profile, is_configured=self._is_configured(profile), updated_at=updated_at, message=message)

    def _is_configured(self, profile: WorkshopProfile) -> bool:
        return any(value.strip() for value in profile.model_dump().values())

    def _clean_value(self, field: str, value: str | None) -> str:
        text = unicodedata.normalize("NFKC", str(value or "")).strip()
        if len(text) > PROFILE_LIMITS[field]:
            raise WorkshopProfileValidationError(f"{PROFILE_FIELD_LABELS[field]} слишком длинное.")
        allowed_controls = {"\n", "\r", "\t"} if field in {"workshop_contact_text", "workshop_note"} else set()
        for char in text:
            if unicodedata.category(char)[0] == "C" and char not in allowed_controls:
                raise WorkshopProfileValidationError("Поле содержит недопустимые символы.")
        return text


def _capabilities() -> list[SettingsCapability]:
    return [
        SettingsCapability(id="backups", title="Резервные копии", status="ready", route="/backups", description="Создание и просмотр локальных резервных копий выполняется в отдельном разделе.", mutates_from_settings=False),
        SettingsCapability(id="exports", title="Экспорт", status="ready", route="/exports", description="Экспорт создает отдельный JSON-снимок только после явного действия в разделе экспорта.", mutates_from_settings=False),
        SettingsCapability(id="imports", title="Импорт", status="ready", route="/imports", description="Импорт работает через черновик, валидацию, предпросмотр и подтверждение.", mutates_from_settings=False),
        SettingsCapability(id="report_documents", title="Документы отчетов", status="ready", route="/report-documents", description="Markdown/PDF-сводки создаются только в разделе документов отчетов.", mutates_from_settings=False),
        SettingsCapability(id="reports", title="Отчеты", status="ready", route="/reports", description="Отчеты читают данные и показывают сводки без изменения склада, заказов и производства.", mutates_from_settings=False),
        SettingsCapability(id="demo_data", title="Демо-данные", status="ready", route="/demo-data", description="Демо-данные устанавливаются и очищаются только через отдельный явный сценарий.", mutates_from_settings=False),
        SettingsCapability(id="help", title="Помощь", status="ready", route="/help", description="Справка объясняет рабочие сценарии и не меняет данные.", mutates_from_settings=False),
        SettingsCapability(id="settings", title="Настройки", status="ready", route="/settings", description="Этот раздел показывает статус настроек и позволяет редактировать только профиль мастерской; расчетные настройки остаются закрыты.", mutates_from_settings=False),
    ]


def _definition(id: str, title: str, status: SettingsDefinitionStatus, description: str, safety_note: str, *, affects_calculations: bool = False, affects_historical_data: bool = False, requires_backend_service: bool = False) -> SettingsDefinition:
    return SettingsDefinition(
        id=id,
        title=title,
        status=status,
        affects_calculations=affects_calculations,
        affects_historical_data=affects_historical_data,
        requires_backend_service=requires_backend_service,
        description=description,
        safety_note=safety_note,
    )


def _setting_groups() -> list[SettingsGroup]:
    return [
        SettingsGroup(id="safe_mvp_candidates", title="Безопасные кандидаты для MVP", description="Настройки, которые можно добавить позже без влияния на расчеты и историю, если у них появятся backend-владелец, валидация и тесты.", items=[
            _definition("workshop_name", "Название мастерской", "editable_now", "Отображаемое название в интерфейсе и документах.", "Можно делать редактируемым только как отображаемый профиль, без изменения исторических записей."),
            _definition("master_name", "Имя мастера", "editable_now", "Имя для будущих документов и подсказок.", "Должно применяться к новым документам или отображению, не переписывая историю."),
            _definition("workshop_contact_text", "Контакты мастерской", "editable_now", "Короткий текст с телефоном, адресом или способом связи.", "Не должен попадать в расчеты или складские операции."),
            _definition("workshop_note", "Краткое описание / примечание", "editable_now", "Короткое описание мастерской для будущего отображения.", "Не влияет на расчеты, склад или исторические записи."),
            _definition("default_report_document_format", "Формат документа отчета по умолчанию", "safe_mvp_candidate", "Будущий выбор Markdown или PDF при создании отчетного документа.", "Создание файла всё равно должно оставаться явным действием пользователя."),
            _definition("backup_reminder_hint", "Подсказка о резервных копиях", "safe_mvp_candidate", "Будущая пользовательская подсказка о том, когда напоминать про backup.", "Не должна автоматически создавать файлы или блокировать работу."),
            _definition("hide_demo_hints_after_onboarding", "Скрывать подсказки про демо после онбординга", "safe_mvp_candidate", "Будущий UI-флаг для уменьшения подсказок после знакомства с приложением.", "Не должен устанавливать или очищать демо-данные."),
        ]),
        SettingsGroup(id="calculation_sensitive_candidates", title="Кандидаты, влияющие на расчеты", description="Эти настройки нельзя добавлять как простые поля: нужны backend-правила, снапшоты и тесты исторической безопасности.", items=[
            _definition("currency_display", "Отображение валюты", "requires_backend_rules", "Будущий символ/подпись валюты для денежных значений.", "Нужно определить, это только отображение или часть денежных правил.", affects_calculations=True, affects_historical_data=True, requires_backend_service=True),
            _definition("default_tax_rate", "Налоговая ставка по умолчанию", "requires_backend_rules", "Будущая ставка для новых расчетов заказов и производств.", "Должна применяться к будущим расчетам через backend и не менять старые production batch.", affects_calculations=True, affects_historical_data=True, requires_backend_service=True),
            _definition("target_margin", "Целевая маржа", "requires_backend_rules", "Будущая подсказка для планирования цены и прибыльности.", "Нельзя пересчитывать исторические цены без явного решения.", affects_calculations=True, affects_historical_data=True, requires_backend_service=True),
            _definition("default_low_stock_threshold", "Порог низкого остатка по умолчанию", "requires_backend_rules", "Будущий дефолт для новых компонентов или тары.", "Генерация алертов и закупок должна оставаться backend-логикой.", affects_calculations=False, affects_historical_data=False, requires_backend_service=True),
            _definition("expiry_warning_days", "Дней до предупреждения о сроке годности", "requires_backend_rules", "Будущий дефолт для предупреждений о скором истечении срока.", "Влияние на алерты и закупки должно быть протестировано на backend.", affects_calculations=False, affects_historical_data=False, requires_backend_service=True),
            _definition("default_measurement_units", "Единицы измерения по умолчанию", "requires_backend_rules", "Будущие единицы для новых форм и черновиков.", "Нельзя подменять граммы в рецептурных расчетах и ml→g предупреждениях.", affects_calculations=True, affects_historical_data=True, requires_backend_service=True),
        ]),
        SettingsGroup(id="v2_v3_only", title="Только V2/V3", description="Крупные возможности после MVP, требующие отдельных продуктовых и архитектурных решений.", items=[
            _definition("document_templates", "Редактор шаблонов документов", "v2_or_later", "Шаблоны коммерческих документов и отчетов.", "Требует отдельной модели шаблонов и защиты от поломки документов."),
            _definition("labels", "Этикетки", "v2_or_later", "Печать и макеты этикеток.", "Нужны отдельные правила данных, размеров и предупреждений."),
            _definition("certificates", "Сертификаты", "v2_or_later", "Документы сертификации и вложения.", "Не должно имитировать юридическую сертификацию без процесса."),
            _definition("docx_export", "DOCX export", "v2_or_later", "Экспорт документов в DOCX.", "Требует отдельного генератора и тестов файлов."),
            _definition("email_sending", "Отправка email", "v2_or_later", "Будущая отправка документов клиентам или мастеру.", "Не должно становиться обязательной интернет-зависимостью MVP."),
            _definition("external_integrations", "Внешние интеграции", "v2_or_later", "Интеграции с магазинами, складами или сервисами.", "Нужны отдельные настройки безопасности и отказоустойчивости."),
            _definition("cloud_sync", "Облачная синхронизация", "v2_or_later", "Будущая синхронизация между устройствами.", "MVP остается локальным и не требует интернета."),
        ]),
        SettingsGroup(id="not_mvp", title="Не планируется для MVP", description="Функции, которые не входят в текущий MVP и не должны появляться через Settings без явного нового scope.", items=[
            _definition("roles_multi_user", "Роли и мультипользовательский доступ", "not_mvp", "Права доступа, аккаунты и совместная работа.", "Нужна отдельная модель безопасности, не в MVP."),
            _definition("full_accounting", "Полная бухгалтерия", "not_mvp", "Акты, счета, налоговая отчетность и полноценный учет.", "Приложение не должно притворяться бухгалтерской системой."),
            _definition("advanced_analytics", "Продвинутая аналитика", "not_mvp", "Сложные прогнозы, графики и аналитические панели.", "Только после стабилизации базовых отчетов."),
            _definition("template_marketplace", "Маркетплейс шаблонов", "not_mvp", "Каталог внешних шаблонов рецептов или документов.", "Не входит в локальный MVP и может создать внешние зависимости."),
        ]),
    ]
