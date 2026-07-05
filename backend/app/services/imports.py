from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
from datetime import date
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

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000
MAX_COLUMNS = 100
PREVIEW_LIMIT = 50
SUPPORTED_EXTENSIONS = {"csv", "xlsx"}

TARGETS = {
    "ingredients": {"label": "Компоненты", "required_columns": ["name"], "optional_columns": ["inci_name", "unit", "density", "notes"]},
    "packaging_items": {"label": "Тара", "required_columns": ["name"], "optional_columns": ["category", "unit", "cost", "stock", "minimum_stock"]},
    "clients": {"label": "Клиенты", "required_columns": ["full_name"], "optional_columns": ["phone", "email", "address", "notes"]},
    "recipe_templates": {"label": "Рецепты", "required_columns": ["name"], "optional_columns": ["product_type", "notes"]},
    "ingredient_lots": {"label": "Партии компонентов", "required_columns": ["ingredient_name", "quantity", "unit"], "optional_columns": ["ingredient_id", "unit_cost", "purchase_date", "expiration_date", "supplier", "lot_number"]},
    "orders": {"label": "Заказы", "required_columns": ["client_name", "product_name", "target_batch_size_value", "target_batch_size_unit"], "optional_columns": ["client_id", "sale_price", "due_date", "notes"]},
}
DECIMAL_FIELDS = {"density", "quantity", "unit_cost", "cost", "stock", "minimum_stock", "sale_price", "target_batch_size_value"}
DATE_FIELDS = {"purchase_date", "expiration_date", "due_date"}
UNIT_FIELDS = {"unit", "target_batch_size_unit"}
VALID_UNITS = {"g", "ml", "pcs", "gram", "grams", "milliliter", "milliliters", "piece", "pieces", "г", "мл", "шт"}


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


def normalize_header(value: str) -> str:
    normalized = re.sub(r"\s+", "_", value.strip().lower())
    return normalized


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

    normalized_headers = [normalize_header(header) for header in headers]
    issues: list[ValidationIssue] = []
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
            value = normalized[field].strip()
            if value and not re.fullmatch(r"[-+]?\d+(\.\d+)?", value):
                row_issues.append(_issue("error", "invalid_decimal", f"В строке {row_number} в поле “{field}” нужно число с точкой в качестве десятичного разделителя.", row_number, field))
        for field in DATE_FIELDS & normalized.keys():
            value = normalized[field].strip()
            if value:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    row_issues.append(_issue("error", "invalid_date", f"В строке {row_number} в поле “{field}” нужна дата в формате YYYY-MM-DD.", row_number, field))
        for field in UNIT_FIELDS & normalized.keys():
            value = normalized[field].strip().lower()
            if value and value not in VALID_UNITS:
                row_issues.append(_issue("error", "invalid_unit", f"В строке {row_number} в поле “{field}” указана неизвестная единица измерения.", row_number, field))
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
    return {"id": row["id"], "source_id": row["source_id"], "target_type": row["target_type"], "status": row["status"], "row_count": row["row_count"], "valid_row_count": row["valid_row_count"], "invalid_row_count": row["invalid_row_count"], "warning_count": row["warning_count"], "error_count": row["error_count"], "headers": json.loads(row["headers_json"]), "summary": json.loads(row["summary_json"]), "created_at": row["created_at"], "updated_at": row["updated_at"]}


def create_import_draft(upload: UploadedFileData, target_type: str, config: DatabaseConfig | None = None) -> dict[str, object]:
    result = parse_import_file(upload.filename, upload.content, target_type)
    row_errors = sum(1 for row in result.rows if row.status == "error")
    warning_count = sum(1 for row in result.rows for issue in row.issues if issue.severity == "warning") + sum(1 for issue in result.issues if issue.severity == "warning")
    error_count = sum(1 for row in result.rows for issue in row.issues if issue.severity == "error") + sum(1 for issue in result.issues if issue.severity == "error")
    valid_count = sum(1 for row in result.rows if row.status == "valid")
    summary = {"message": "Данные ещё не внесены в систему.", "global_issues": [issue.to_dict() for issue in result.issues]}
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
