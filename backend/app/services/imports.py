from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO, StringIO
import csv
import json
from pathlib import Path
import re
import sqlite3
import zipfile
from xml.etree import ElementTree

from app.db.config import DatabaseConfig
from app.db.connection import session
from app.domain.clients import ClientDraft
from app.domain.ingredients import IngredientDraft
from app.domain.packaging_items import PackagingItemDraft
from app.domain.recipes import RecipeTemplateDraft
from app.repositories.audit import AuditLogRepository
from app.repositories.clients import ClientRepository
from app.repositories.ingredients import IngredientRepository
from app.repositories.packaging_items import PackagingItemRepository
from app.repositories.recipes import RecipeRepository

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000
MAX_COLUMNS = 100
PREVIEW_LIMIT = 50
SUPPORTED_EXTENSIONS = {"csv", "xlsx"}

TARGETS = {
    "ingredients": {"label": "Компоненты", "required_columns": ["name"], "optional_columns": ["inci_name", "unit", "density", "notes"]},
    "packaging_items": {"label": "Тара", "required_columns": ["name"], "optional_columns": ["category", "unit", "cost", "stock", "minimum_stock", "notes"]},
    "clients": {"label": "Клиенты", "required_columns": ["full_name"], "optional_columns": ["phone", "email", "address", "notes"]},
    "recipe_templates": {"label": "Рецепты", "required_columns": ["name"], "optional_columns": ["product_type", "notes"]},
    "ingredient_lots": {"label": "Партии компонентов", "required_columns": ["ingredient_name", "quantity", "unit"], "optional_columns": ["ingredient_id", "unit_cost", "purchase_date", "expiration_date", "supplier", "lot_number"]},
    "orders": {"label": "Заказы", "required_columns": ["client_name", "product_name", "target_batch_size_value", "target_batch_size_unit"], "optional_columns": ["client_id", "sale_price", "due_date", "notes"]},
}
DECIMAL_FIELDS = {"density", "quantity", "unit_cost", "cost", "stock", "minimum_stock", "sale_price", "target_batch_size_value"}
DATE_FIELDS = {"purchase_date", "expiration_date", "due_date"}
UNIT_FIELDS = {"unit", "target_batch_size_unit"}
UNIT_ALIASES = {"g": "g", "gram": "g", "grams": "g", "г": "g", "ml": "ml", "milliliter": "ml", "milliliters": "ml", "мл": "ml", "pcs": "pcs", "piece": "pcs", "pieces": "pcs", "шт": "pcs"}
VALID_UNITS = set(UNIT_ALIASES)
POSITIVE_DECIMAL_FIELDS = {"density", "quantity", "target_batch_size_value"}
NON_NEGATIVE_DECIMAL_FIELDS = {"stock", "minimum_stock", "cost", "unit_cost", "sale_price"}
ID_FIELDS = {"ingredient_id", "client_id"}
HEADER_ALIASES = {
    "ingredients": {"название": "name", "наименование": "name", "inci": "inci_name", "инци": "inci_name", "плотность": "density", "единица": "unit", "единица_измерения": "unit", "комментарий": "notes", "заметки": "notes"},
    "packaging_items": {"название": "name", "наименование": "name", "тип": "category", "категория": "category", "единица": "unit", "единица_измерения": "unit", "остаток": "stock", "минимальный_остаток": "minimum_stock", "себестоимость": "cost", "стоимость": "cost", "цена": "cost"},
    "clients": {"фио": "full_name", "имя": "full_name", "клиент": "full_name", "телефон": "phone", "почта": "email", "email": "email", "адрес": "address", "комментарий": "notes", "заметки": "notes"},
    "recipe_templates": {"название": "name", "наименование": "name", "тип_продукта": "product_type", "категория": "product_type", "комментарий": "notes", "заметки": "notes"},
    "ingredient_lots": {"компонент": "ingredient_name", "название_компонента": "ingredient_name", "id_компонента": "ingredient_id", "партия": "lot_number", "номер_партии": "lot_number", "количество": "quantity", "единица": "unit", "единица_измерения": "unit", "себестоимость": "unit_cost", "стоимость": "unit_cost", "цена_за_единицу": "unit_cost", "дата_покупки": "purchase_date", "срок_годности": "expiration_date", "поставщик": "supplier"},
    "orders": {"клиент": "client_name", "id_клиента": "client_id", "продукт": "product_name", "название_продукта": "product_name", "размер_партии": "target_batch_size_value", "объем": "target_batch_size_value", "единица": "target_batch_size_unit", "единица_измерения": "target_batch_size_unit", "цена": "sale_price", "дата": "due_date", "плановая_дата": "due_date", "комментарий": "notes", "заметки": "notes"},
}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    row_number: int | None = None
    field: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {"severity": self.severity, "code": self.code, "message": self.message, "row_number": self.row_number, "field": self.field}


@dataclass(frozen=True)
class ParsedRow:
    row_number: int
    raw_values: dict[str, str]
    normalized_values: dict[str, str]
    issues: list[ValidationIssue]

    @property
    def status(self) -> str:
        if any(issue.severity == "error" for issue in self.issues):
            return "error"
        if self.issues:
            return "warning"
        return "valid"


@dataclass(frozen=True)
class ParseResult:
    headers: list[str]
    rows: list[ParsedRow]
    issues: list[ValidationIssue]


@dataclass(frozen=True)
class UploadedFileData:
    filename: str
    content_type: str
    content: bytes


class ImportServiceError(RuntimeError):
    status_code = 400


class UnsupportedImportFileError(ImportServiceError):
    message = "Поддерживаются только CSV и XLSX файлы."


class ImportFileTooLargeError(ImportServiceError):
    message = "Файл слишком большой для черновика импорта."


class ImportParseError(ImportServiceError):
    message = "Не удалось прочитать файл. Проверьте формат CSV/XLSX и попробуйте снова."


class ImportApplyConflictError(ImportServiceError):
    status_code = 409

    def __init__(self, message: str = "Черновик нельзя применить.", issues: list[dict[str, object]] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.issues = issues or []

    @property
    def detail(self) -> dict[str, object]:
        return {"message": self.message, "issues": self.issues}


def normalize_header(value: str) -> str:
    normalized = re.sub(r"\s+", "_", value.strip().lower())
    return normalized



def apply_header_alias(header: str, target_type: str) -> str:
    return HEADER_ALIASES.get(target_type, {}).get(header, header)


def _normalize_decimal_value(value: str, row_number: int, field: str) -> tuple[str, ValidationIssue | None]:
    text = value.strip()
    if not text:
        return text, None
    if "," in text and "." in text:
        return text, _issue("error", "ambiguous_decimal", f"В строке {row_number} в поле “{field}” неоднозначное число «{text}». Уберите разделители тысяч и используйте 100.5 или 100,5.", row_number, field)
    if re.search(r"\d\s+\d", text):
        return text, _issue("error", "ambiguous_decimal", f"В строке {row_number} в поле “{field}” неоднозначное число «{text}». Уберите пробелы-разделители тысяч.", row_number, field)
    if "," in text:
        if re.fullmatch(r"[-+]?\d+,\d+", text):
            normalized = text.replace(",", ".")
            return normalized, _issue("warning", "decimal_comma_normalized", f"В строке {row_number} значение «{text}» будет прочитано как {normalized}.", row_number, field)
        return text, _issue("error", "ambiguous_decimal", f"В строке {row_number} в поле “{field}” неоднозначное число «{text}». Используйте 100.5 или 100,5 без разделителей тысяч.", row_number, field)
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", text):
        return text, None
    return text, _issue("error", "invalid_decimal", f"В строке {row_number} в поле “{field}” нужно число, например 30 или 30,5.", row_number, field)


def _normalize_date_value(value: str, row_number: int, field: str) -> tuple[str, ValidationIssue | None]:
    text = value.strip()
    if not text:
        return text, None
    try:
        date.fromisoformat(text)
        return text, None
    except ValueError:
        pass
    match = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", text)
    if match:
        normalized = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
        try:
            date.fromisoformat(normalized)
            return normalized, _issue("warning", "date_format_normalized", f"В строке {row_number} дата «{text}» будет прочитана как {normalized}.", row_number, field)
        except ValueError:
            pass
    return text, _issue("error", "invalid_date", f"В строке {row_number} в поле “{field}” нужна дата в формате YYYY-MM-DD, например 2026-07-05.", row_number, field)


def _readiness(status: str, row_count: int, valid_count: int, invalid_count: int, issues: list[dict[str, object]], warning_count: int, error_count: int) -> dict[str, object]:
    if status == "applied":
        return {"can_apply": False, "status": "applied", "blocking_error_count": error_count, "warning_count": warning_count, "valid_row_count": valid_count, "invalid_row_count": invalid_count, "blocking_reasons": ["Черновик уже применён."], "warnings": [], "next_action": "Данные уже внесены в систему. Повторное применение недоступно."}
    if status == "cancelled":
        return {"can_apply": False, "status": "cancelled", "blocking_error_count": error_count, "warning_count": warning_count, "valid_row_count": valid_count, "invalid_row_count": invalid_count, "blocking_reasons": ["Черновик отменён."], "warnings": [], "next_action": "Создайте новый черновик, если файл нужно проверить заново."}
    if status == "failed":
        return {"can_apply": False, "status": "failed", "blocking_error_count": error_count, "warning_count": warning_count, "valid_row_count": valid_count, "invalid_row_count": invalid_count, "blocking_reasons": ["Черновик не удалось разобрать."], "warnings": [], "next_action": "Исправьте файл и создайте новый черновик."}
    warnings = []
    codes = {str(i.get("code")) for i in issues if i.get("severity") in {"warning", "info"}}
    if "unknown_column" in codes: warnings.append("Есть неизвестные столбцы, которые не будут применены.")
    if any(c in codes for c in {"header_alias_used", "decimal_comma_normalized", "unit_alias_normalized", "date_format_normalized"}): warnings.append("Есть нормализации значений или заголовков — проверьте предпросмотр.")
    if error_count or row_count == 0:
        reasons = []
        if row_count == 0: reasons.append("В черновике нет строк данных.")
        if error_count: reasons.append("Исправьте ошибки в строках или заголовках перед применением.")
        return {"can_apply": False, "status": "blocked", "blocking_error_count": error_count, "warning_count": warning_count, "valid_row_count": valid_count, "invalid_row_count": invalid_count, "blocking_reasons": reasons, "warnings": warnings, "next_action": "Исправьте файл и создайте новый черновик."}
    ready_status = "ready_with_warnings" if warning_count else "ready"
    return {"can_apply": True, "status": ready_status, "blocking_error_count": 0, "warning_count": warning_count, "valid_row_count": valid_count, "invalid_row_count": invalid_count, "blocking_reasons": [], "warnings": warnings, "next_action": "Проверьте предупреждения. Кнопки применения пока нет — она будет добавлена отдельным PR." if warning_count else "Черновик готов для будущего шага применения. Кнопки применения пока нет."}


def _issue_counts(issues: list[dict[str, object]]) -> tuple[dict[str, int], dict[str, int]]:
    by_code: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for issue in issues:
        by_code[str(issue.get("code"))] = by_code.get(str(issue.get("code")), 0) + 1
        by_severity[str(issue.get("severity"))] = by_severity.get(str(issue.get("severity")), 0) + 1
    return by_code, by_severity

def _issue(severity: str, code: str, message: str, row_number: int | None = None, field: str | None = None) -> ValidationIssue:
    return ValidationIssue(severity=severity, code=code, message=message, row_number=row_number, field=field)


def _file_extension(filename: str) -> str:
    return Path(filename or "").suffix.lower().lstrip(".")


def _decode_csv(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ImportParseError(ImportParseError.message)


def _sniff_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.excel


def _parse_csv(content: bytes) -> tuple[list[str], list[tuple[int, list[str]]], int]:
    text = _decode_csv(content)
    if not text.strip():
        raise ImportParseError("Файл пустой или не содержит строк с данными.")
    reader = csv.reader(StringIO(text), dialect=_sniff_dialect(text[:4096]))
    all_rows = [[cell.strip() for cell in row] for row in reader]
    non_empty = [(idx + 1, row) for idx, row in enumerate(all_rows) if any(cell.strip() for cell in row)]
    if not non_empty:
        raise ImportParseError("Файл пустой или не содержит строк с данными.")
    header_source_row, headers = non_empty[0]
    data_rows = [(row_number, row) for row_number, row in non_empty[1:]]
    return headers, data_rows, header_source_row


def _xlsx_cell_text(cell: ElementTree.Element, shared_strings: list[str], ns: dict[str, str]) -> str:
    cell_type = cell.attrib.get("t")
    value_node = cell.find("main:v", ns)
    inline_node = cell.find("main:is/main:t", ns)
    if inline_node is not None and inline_node.text is not None:
        return inline_node.text.strip()
    if value_node is None or value_node.text is None:
        return ""
    value = value_node.text
    if cell_type == "s":
        try:
            return shared_strings[int(value)].strip()
        except (ValueError, IndexError):
            return value.strip()
    return value.strip()


def _xlsx_column_index(cell_reference: str) -> int:
    letters = ""
    for character in cell_reference:
        if character.isalpha():
            letters += character.upper()
        else:
            break
    if not letters:
        return 0
    index = 0
    for character in letters:
        index = index * 26 + (ord(character) - ord("A") + 1)
    return index - 1


def _xlsx_row_values(row: ElementTree.Element, shared_strings: list[str], ns: dict[str, str]) -> list[str]:
    values_by_index: dict[int, str] = {}
    next_index = 0
    for cell in row.findall("main:c", ns):
        reference = cell.attrib.get("r", "")
        column_index = _xlsx_column_index(reference) if reference else next_index
        values_by_index[column_index] = _xlsx_cell_text(cell, shared_strings, ns).strip()
        next_index = max(next_index, column_index + 1)
    if not values_by_index:
        return []
    width = max(values_by_index) + 1
    return [values_by_index.get(index, "") for index in range(width)]


def _parse_xlsx(content: bytes) -> tuple[list[str], list[tuple[int, list[str]]], int]:
    try:
        archive = zipfile.ZipFile(BytesIO(content))
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships", "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships"}
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", ns):
                shared_strings.append("".join(node.text or "" for node in item.findall(".//main:t", ns)))
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        sheet = next((s for s in workbook.findall("main:sheets/main:sheet", ns) if s.attrib.get("state", "visible") == "visible"), None)
        if sheet is None:
            raise ImportParseError("Файл пустой или не содержит строк с данными.")
        rel_id = sheet.attrib.get(f"{{{ns['rel']}}}id")
        rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels:
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib.get("Target")
                break
        if target is None:
            raise ImportParseError(ImportParseError.message)
        sheet_path = "xl/" + target.lstrip("/")
        root = ElementTree.fromstring(archive.read(sheet_path))
        rows: list[tuple[int, list[str]]] = []
        fallback_row_number = 1
        for row in root.findall(".//main:sheetData/main:row", ns):
            try:
                row_number = int(row.attrib.get("r", fallback_row_number))
            except ValueError:
                row_number = fallback_row_number
            values = _xlsx_row_values(row, shared_strings, ns)
            if any(values):
                rows.append((row_number, values))
            fallback_row_number = row_number + 1
        if not rows:
            raise ImportParseError("Файл пустой или не содержит строк с данными.")
        header_row_number, headers = rows[0]
        return headers, rows[1:], header_row_number
    except ImportParseError:
        raise
    except Exception as exc:
        raise ImportParseError(ImportParseError.message) from exc


def _pad_row(row: Sequence[str], width: int) -> list[str]:
    return (list(row) + [""] * width)[:width]


def parse_import_file(filename: str, content: bytes, target_type: str) -> ParseResult:
    if target_type not in TARGETS:
        raise ImportServiceError("Неизвестный тип импорта.")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ImportFileTooLargeError(ImportFileTooLargeError.message)
    extension = _file_extension(filename)
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedImportFileError(UnsupportedImportFileError.message)
    headers, data_rows, header_row_number = _parse_csv(content) if extension == "csv" else _parse_xlsx(content)
    if not headers or not any(header.strip() for header in headers):
        raise ImportParseError("Файл не содержит строку заголовков.")
    if len(headers) > MAX_COLUMNS:
        raise ImportParseError(f"В файле больше {MAX_COLUMNS} столбцов.")
    if len(data_rows) > MAX_ROWS:
        raise ImportParseError(f"В файле больше {MAX_ROWS} строк данных.")

    raw_normalized_headers = [normalize_header(header) for header in headers]
    normalized_headers = [apply_header_alias(header, target_type) for header in raw_normalized_headers]
    issues: list[ValidationIssue] = []
    for raw_header, normalized_header, original_header in zip(raw_normalized_headers, normalized_headers, headers):
        if raw_header and raw_header != normalized_header:
            issues.append(_issue("info", "header_alias_used", f"Столбец «{original_header.strip()}» распознан как {normalized_header}.", header_row_number, normalized_header))
    seen: set[str] = set()
    for header in normalized_headers:
        if not header:
            issues.append(_issue("error", "missing_header", "Найден пустой заголовок столбца.", header_row_number))
        elif header in seen:
            issues.append(_issue("error", "duplicate_header", f"Заголовок повторяется: {header}", header_row_number, header))
        seen.add(header)
    target = TARGETS[target_type]
    for required in target["required_columns"]:
        if required not in normalized_headers:
            issues.append(_issue("error", "missing_required_column", f"Не найден обязательный столбец: {required}", None, required))
    allowed = set(target["required_columns"]) | set(target["optional_columns"])
    for header in normalized_headers:
        if header and header not in allowed:
            issues.append(_issue("warning", "unknown_column", f"Неизвестный столбец будет показан в черновике: {header}", None, header))

    parsed_rows: list[ParsedRow] = []
    for row_number, row in data_rows:
        values = _pad_row(row, len(normalized_headers))
        raw = {headers[i].strip(): values[i] for i in range(len(normalized_headers))}
        normalized = {normalized_headers[i]: values[i] for i in range(len(normalized_headers)) if normalized_headers[i]}
        row_issues: list[ValidationIssue] = []
        for required in target["required_columns"]:
            if required in normalized and not normalized[required].strip():
                row_issues.append(_issue("error", "missing_required_value", f"В строке {row_number} не заполнено обязательное поле: {required}", row_number, required))
        for field in DECIMAL_FIELDS & normalized.keys():
            normalized_value, issue = _normalize_decimal_value(normalized[field], row_number, field)
            normalized[field] = normalized_value
            if issue:
                row_issues.append(issue)
                if issue.severity == "error":
                    continue
            if normalized_value:
                number = Decimal(normalized_value)
                if field in POSITIVE_DECIMAL_FIELDS and number <= 0:
                    row_issues.append(_issue("error", "invalid_positive_decimal", f"В строке {row_number} поле “{field}” должно быть больше нуля.", row_number, field))
                if field in NON_NEGATIVE_DECIMAL_FIELDS and number < 0:
                    row_issues.append(_issue("error", "invalid_non_negative_decimal", f"В строке {row_number} поле “{field}” не может быть отрицательным.", row_number, field))
        for field in DATE_FIELDS & normalized.keys():
            normalized_value, issue = _normalize_date_value(normalized[field], row_number, field)
            normalized[field] = normalized_value
            if issue:
                row_issues.append(issue)
        for field in UNIT_FIELDS & normalized.keys():
            raw_unit = normalized[field].strip()
            value = raw_unit.lower()
            if value:
                canonical = UNIT_ALIASES.get(value)
                if canonical is None:
                    row_issues.append(_issue("error", "invalid_unit", f"В строке {row_number} в поле “{field}” указана неизвестная единица измерения. Используйте g, ml или pcs.", row_number, field))
                else:
                    normalized[field] = canonical
                    if canonical != raw_unit:
                        row_issues.append(_issue("info", "unit_alias_normalized", f"В строке {row_number} единица «{raw_unit}» будет прочитана как {canonical}.", row_number, field))
        for field in ID_FIELDS & normalized.keys():
            value = normalized[field].strip()
            if value and not re.fullmatch(r"[1-9]\d*", value):
                row_issues.append(_issue("error", "invalid_id", f"В строке {row_number} поле “{field}” должно быть положительным целым числом.", row_number, field))
        if target_type == "clients" and normalized.get("email", "").strip():
            email = normalized["email"].strip()
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                row_issues.append(_issue("warning", "invalid_email", f"В строке {row_number} email «{email}» выглядит некорректно. Проверьте адрес перед будущим применением.", row_number, "email"))
        parsed_rows.append(ParsedRow(row_number=row_number, raw_values=raw, normalized_values=normalized, issues=row_issues))
    return ParseResult(headers=normalized_headers, rows=parsed_rows, issues=issues)


def target_definitions() -> list[dict[str, object]]:
    return [{"type": key, **value} for key, value in TARGETS.items()]


def _json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _row_to_response(row: sqlite3.Row) -> dict[str, object]:
    return {"id": row["id"], "row_number": row["row_number"], "raw_values": json.loads(row["raw_values_json"]), "normalized_values": json.loads(row["normalized_values_json"]), "issues": json.loads(row["issues_json"]), "status": row["status"], "created_at": row["created_at"]}


def _source_to_response(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "original_filename": row["original_filename"],
        "content_type": row["content_type"],
        "file_extension": row["file_extension"],
        "file_size_bytes": row["file_size_bytes"],
        "target_type": row["target_type"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _draft_to_response(row: sqlite3.Row) -> dict[str, object]:
    summary = json.loads(row["summary_json"])
    global_issues = summary.get("global_issues", []) if isinstance(summary, dict) else []
    readiness = summary.get("readiness") if isinstance(summary, dict) else None
    if row["status"] in {"cancelled", "failed", "applied"} or not isinstance(readiness, dict):
        readiness = _readiness(row["status"], row["row_count"], row["valid_row_count"], row["invalid_row_count"], global_issues, row["warning_count"], row["error_count"])
        if isinstance(summary, dict):
            summary["readiness"] = readiness
    return {"id": row["id"], "source_id": row["source_id"], "target_type": row["target_type"], "status": row["status"], "row_count": row["row_count"], "valid_row_count": row["valid_row_count"], "invalid_row_count": row["invalid_row_count"], "warning_count": row["warning_count"], "error_count": row["error_count"], "headers": json.loads(row["headers_json"]), "summary": summary, "apply_readiness": readiness, "created_at": row["created_at"], "updated_at": row["updated_at"]}


def create_import_draft(upload: UploadedFileData, target_type: str, config: DatabaseConfig | None = None) -> dict[str, object]:
    result = parse_import_file(upload.filename, upload.content, target_type)
    row_errors = sum(1 for row in result.rows if row.status == "error")
    all_issue_dicts = [issue.to_dict() for issue in result.issues] + [issue.to_dict() for row in result.rows for issue in row.issues]
    warning_count = sum(1 for issue in all_issue_dicts if issue["severity"] in {"warning", "info"})
    error_count = sum(1 for issue in all_issue_dicts if issue["severity"] == "error")
    valid_count = sum(1 for row in result.rows if row.status == "valid")
    by_code, by_severity = _issue_counts(all_issue_dicts)
    readiness = _readiness("draft", len(result.rows), valid_count, row_errors, all_issue_dicts, warning_count, error_count)
    summary = {"message": "Данные ещё не внесены в систему.", "global_issues": [issue.to_dict() for issue in result.issues], "readiness": readiness, "issue_counts_by_code": by_code, "issue_counts_by_severity": by_severity}
    with session(config) as connection:
        source_id = connection.execute(
            """
            INSERT INTO import_sources (original_filename, content_type, file_extension, file_size_bytes, content_hash, target_type, status)
            VALUES (?, ?, ?, ?, ?, ?, 'parsed')
            """,
            (upload.filename, upload.content_type, _file_extension(upload.filename), len(upload.content), sha256(upload.content).hexdigest(), target_type),
        ).lastrowid
        draft_id = connection.execute(
            """
            INSERT INTO import_drafts (source_id, target_type, status, row_count, valid_row_count, invalid_row_count, warning_count, error_count, headers_json, summary_json)
            VALUES (?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)
            """,
            (source_id, target_type, len(result.rows), valid_count, row_errors, warning_count, error_count, _json(result.headers), _json(summary)),
        ).lastrowid
        for row in result.rows:
            connection.execute(
                """
                INSERT INTO import_draft_rows (draft_id, row_number, raw_values_json, normalized_values_json, issues_json, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (draft_id, row.row_number, _json(row.raw_values), _json(row.normalized_values), _json([issue.to_dict() for issue in row.issues]), row.status),
            )
        draft = connection.execute("SELECT * FROM import_drafts WHERE id = ?", (draft_id,)).fetchone()
        preview = connection.execute("SELECT * FROM import_draft_rows WHERE draft_id = ? ORDER BY row_number, id LIMIT ?", (draft_id, PREVIEW_LIMIT)).fetchall()
    return {"draft": _draft_to_response(draft), "preview_rows": [_row_to_response(row) for row in preview], "issues": [issue.to_dict() for issue in result.issues], "message": "Черновик импорта создан. Данные ещё не внесены в систему."}


def list_import_drafts(status: str | None = None, target_type: str | None = None, limit: int = 50, offset: int = 0, config: DatabaseConfig | None = None) -> dict[str, object]:
    clauses, params = [], []
    if status:
        clauses.append("status = ?"); params.append(status)
    if target_type:
        clauses.append("target_type = ?"); params.append(target_type)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    limit = max(1, min(limit, 100)); offset = max(0, offset)
    with session(config) as connection:
        rows = connection.execute(f"SELECT * FROM import_drafts{where} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?", (*params, limit, offset)).fetchall()
    return {"drafts": [_draft_to_response(row) for row in rows], "limit": limit, "offset": offset}


def get_import_draft(draft_id: int, limit: int = 50, offset: int = 0, config: DatabaseConfig | None = None) -> dict[str, object] | None:
    limit = max(1, min(limit, 100)); offset = max(0, offset)
    with session(config) as connection:
        draft = connection.execute("SELECT * FROM import_drafts WHERE id = ?", (draft_id,)).fetchone()
        if draft is None:
            return None
        source = connection.execute("SELECT * FROM import_sources WHERE id = ?", (draft["source_id"],)).fetchone()
        rows = connection.execute("SELECT * FROM import_draft_rows WHERE draft_id = ? ORDER BY row_number, id LIMIT ? OFFSET ?", (draft_id, limit, offset)).fetchall()
    source_response = _source_to_response(source)
    return {"draft": _draft_to_response(draft), "source": source_response, "preview_rows": [_row_to_response(row) for row in rows], "issues": json.loads(draft["summary_json"]).get("global_issues", []), "limit": limit, "offset": offset}


def cancel_import_draft(draft_id: int, config: DatabaseConfig | None = None) -> dict[str, object] | None:
    with session(config) as connection:
        draft = connection.execute("SELECT * FROM import_drafts WHERE id = ?", (draft_id,)).fetchone()
        if draft is None:
            return None
        connection.execute("UPDATE import_drafts SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (draft_id,))
        connection.execute("UPDATE import_sources SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (draft["source_id"],))
        updated = connection.execute("SELECT * FROM import_drafts WHERE id = ?", (draft_id,)).fetchone()
    return {"draft": _draft_to_response(updated), "message": "Черновик импорта отменён. Рабочие данные не изменены."}

APPLY_SUPPORTED_TARGETS = {"ingredients", "clients", "recipe_templates", "packaging_items"}


def _norm_key(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _conflict(code: str, message: str, row_number: int | None = None, field: str | None = None) -> dict[str, object]:
    return {"severity": "error", "code": code, "message": message, "row_number": row_number, "field": field}


def _draft_rows(connection: sqlite3.Connection, draft_id: int) -> list[dict[str, object]]:
    rows = connection.execute("SELECT * FROM import_draft_rows WHERE draft_id = ? ORDER BY row_number, id", (draft_id,)).fetchall()
    return [{"row_number": row["row_number"], "values": json.loads(row["normalized_values_json"]), "status": row["status"]} for row in rows]


def _check_duplicates(values: list[tuple[int, str]], *, field: str, label: str) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    seen: dict[str, int] = {}
    for row_number, value in values:
        key = _norm_key(value)
        if not key:
            continue
        if key in seen:
            issues.append(_conflict("duplicate_domain_record", f"Повтор в черновике: {label} «{value}» уже указан в строке {seen[key]}.", row_number, field))
        else:
            seen[key] = row_number
    return issues


def _preflight_apply(connection: sqlite3.Connection, target_type: str, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if target_type == "ingredients":
        names = [(int(r["row_number"]), str(r["values"].get("name", ""))) for r in rows]
        issues += _check_duplicates(names, field="name", label="компонент")
        existing = {_norm_key(row["name"]): row["name"] for row in connection.execute("SELECT name FROM ingredients").fetchall()}
        for row_number, name in names:
            if _norm_key(name) in existing:
                issues.append(_conflict("duplicate_domain_record", f"Компонент с названием «{name}» уже существует.", row_number, "name"))
    elif target_type == "clients":
        fields = [("email", "email"), ("phone", "телефон"), ("full_name", "клиент")]
        for field, label in fields:
            issues += _check_duplicates([(int(r["row_number"]), str(r["values"].get(field, ""))) for r in rows], field=field, label=label)
        existing_email = {_norm_key(row["email"]): row["email"] for row in connection.execute("SELECT email FROM clients WHERE trim(email) <> ''").fetchall()}
        existing_phone = {_norm_key(row["phone"]): row["phone"] for row in connection.execute("SELECT phone FROM clients WHERE trim(phone) <> ''").fetchall()}
        existing_name = {_norm_key(row["full_name"]): row["full_name"] for row in connection.execute("SELECT full_name FROM clients").fetchall()}
        for r in rows:
            row_number = int(r["row_number"]); values = r["values"]
            email = str(values.get("email", "")); phone = str(values.get("phone", "")); name = str(values.get("full_name", ""))
            if _norm_key(email) and _norm_key(email) in existing_email:
                issues.append(_conflict("duplicate_domain_record", f"Клиент с email «{email}» уже существует.", row_number, "email"))
            if _norm_key(phone) and _norm_key(phone) in existing_phone:
                issues.append(_conflict("duplicate_domain_record", f"Клиент с телефоном «{phone}» уже существует.", row_number, "phone"))
            if _norm_key(name) in existing_name:
                issues.append(_conflict("duplicate_domain_record", f"Клиент «{name}» уже существует.", row_number, "full_name"))
    elif target_type == "recipe_templates":
        names = [(int(r["row_number"]), str(r["values"].get("name", ""))) for r in rows]
        issues += _check_duplicates(names, field="name", label="рецепт")
        existing = {_norm_key(row["name"]): row["name"] for row in connection.execute("SELECT name FROM recipe_templates").fetchall()}
        for row_number, name in names:
            if _norm_key(name) in existing:
                issues.append(_conflict("duplicate_domain_record", f"Шаблон рецепта с названием «{name}» уже существует.", row_number, "name"))
    elif target_type == "packaging_items":
        names = [(int(r["row_number"]), str(r["values"].get("name", ""))) for r in rows]
        issues += _check_duplicates(names, field="name", label="тара")
        existing = {_norm_key(row["name"]): row["name"] for row in connection.execute("SELECT name FROM packaging_items").fetchall()}
        for r in rows:
            row_number = int(r["row_number"]); values = r["values"]; name = str(values.get("name", ""))
            if _norm_key(name) in existing:
                issues.append(_conflict("duplicate_domain_record", f"Тара с названием «{name}» уже существует.", row_number, "name"))
            if str(values.get("stock", "")).strip():
                issues.append(_conflict("apply_unsupported_field", "Поле “stock” нельзя применять для тары в PR80: остатки должны вноситься движениями склада.", row_number, "stock"))
            if str(values.get("minimum_stock", "")).strip():
                issues.append(_conflict("apply_unsupported_field", "Поле “minimum_stock” пока не поддерживается моделью тары для применения импорта.", row_number, "minimum_stock"))
    return issues


def _create_from_import(connection: sqlite3.Connection, target_type: str, row: dict[str, object], config: DatabaseConfig | None) -> dict[str, object]:
    values = row["values"]
    row_number = int(row["row_number"])
    if target_type == "ingredients":
        draft = IngredientDraft.create(name=values.get("name", ""), category="other", default_unit=values.get("unit") or "g", density_g_per_ml=values.get("density") or None, notes=values.get("notes", ""), inci_name=values.get("inci_name", ""))
        record = IngredientRepository(config).create(draft, connection=connection)
        return {"target_type": target_type, "row_number": row_number, "record_id": record.id, "label": record.name}
    if target_type == "clients":
        draft = ClientDraft.create(full_name=values.get("full_name", ""), phone=values.get("phone", ""), email=values.get("email", ""), address=values.get("address", ""), notes=values.get("notes", ""))
        record = ClientRepository(config).create(draft, connection=connection)
        return {"target_type": target_type, "row_number": row_number, "record_id": record.id, "label": record.full_name}
    if target_type == "recipe_templates":
        draft = RecipeTemplateDraft.create(name=values.get("name", ""), product_type=values.get("product_type", ""), notes=values.get("notes", ""))
        record = RecipeRepository(config).create_template(draft, connection=connection)
        return {"target_type": target_type, "row_number": row_number, "record_id": record.id, "label": record.name}
    if target_type == "packaging_items":
        draft = PackagingItemDraft.create(name=values.get("name", ""), kind=values.get("category") or "other", unit=values.get("unit") or "pcs", unit_cost=values.get("cost") or None, notes=values.get("notes", ""))
        record = PackagingItemRepository(config).create(draft, connection=connection)
        return {"target_type": target_type, "row_number": row_number, "record_id": record.id, "label": record.name}
    raise ImportApplyConflictError(issues=[_conflict("apply_target_not_supported", f"Тип импорта {target_type} пока нельзя применить.")])


def apply_import_draft(draft_id: int, *, confirm_apply: bool, backup_acknowledged: bool, allow_warnings: bool = False, config: DatabaseConfig | None = None) -> dict[str, object] | None:
    if not confirm_apply:
        raise ImportApplyConflictError(issues=[_conflict("apply_confirmation_required", "Перед применением нужно явно подтвердить импорт.")])
    if not backup_acknowledged:
        raise ImportApplyConflictError(issues=[_conflict("backup_acknowledgement_required", "Перед применением подтвердите, что резервная копия создана или не требуется.")])
    with session(config) as connection:
        draft = connection.execute("SELECT * FROM import_drafts WHERE id = ?", (draft_id,)).fetchone()
        if draft is None:
            return None
        if draft["status"] == "cancelled":
            raise ImportApplyConflictError(issues=[_conflict("draft_cancelled", "Отменённый черновик нельзя применить.")])
        if draft["status"] == "failed":
            raise ImportApplyConflictError(issues=[_conflict("draft_failed", "Неуспешный черновик нельзя применить.")])
        if draft["status"] == "applied":
            raise ImportApplyConflictError(issues=[_conflict("draft_already_applied", "Черновик уже применён.")])
        target_type = draft["target_type"]
        summary = json.loads(draft["summary_json"])
        readiness = _draft_to_response(draft)["apply_readiness"]
        if readiness["status"] == "blocked" or not readiness["can_apply"]:
            raise ImportApplyConflictError(issues=[_conflict("draft_not_ready", "Черновик содержит ошибки и не готов к применению.")])
        if readiness["status"] == "ready_with_warnings" and not allow_warnings:
            raise ImportApplyConflictError(issues=[_conflict("warnings_not_allowed", "В черновике есть предупреждения. Для применения передайте allow_warnings=true.")])
        if target_type not in APPLY_SUPPORTED_TARGETS:
            raise ImportApplyConflictError(issues=[_conflict("apply_target_not_supported", f"Тип импорта {target_type} пока нельзя применить в PR80.")])
        rows = _draft_rows(connection, draft_id)
        issues = _preflight_apply(connection, target_type, rows)
        if issues:
            raise ImportApplyConflictError(issues=issues)
        created_records = [_create_from_import(connection, target_type, row, config) for row in rows]
        applied_at = datetime.now(timezone.utc).isoformat()
        warning_messages = list(readiness.get("warnings") or [])
        apply_result = {"draft_id": draft_id, "target_type": target_type, "applied_at": applied_at, "applied_row_count": len(rows), "created_count": len(created_records), "created_records": created_records, "warnings": warning_messages}
        summary["apply_result"] = apply_result
        summary["message"] = "Черновик импорта применён. Данные внесены в систему."
        connection.execute("UPDATE import_drafts SET status = 'applied', summary_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (_json(summary), draft_id))
        connection.execute("UPDATE import_sources SET status = 'applied', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (draft["source_id"],))
        AuditLogRepository(config).create_log(action="import_draft_applied", entity_type="ImportDraft", entity_id=str(draft_id), summary="Import draft applied", metadata={"target_type": target_type, "applied_row_count": len(rows), "created_count": len(created_records)}, connection=connection)
        updated = connection.execute("SELECT * FROM import_drafts WHERE id = ?", (draft_id,)).fetchone()
    return {"draft": _draft_to_response(updated), "apply_result": apply_result, "message": "Черновик импорта применён. Данные внесены в систему."}
