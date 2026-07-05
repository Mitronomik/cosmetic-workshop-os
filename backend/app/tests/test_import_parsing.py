from io import BytesIO
import zipfile

import pytest

from app.services.imports import MAX_COLUMNS, MAX_ROWS, ImportParseError, UnsupportedImportFileError, parse_import_file


def test_parses_utf8_csv_and_preserves_raw_values():
    result = parse_import_file("ingredients.csv", "name,unit,notes\n Масло ши ,g, важное ".encode(), "ingredients")

    assert result.headers == ["name", "unit", "notes"]
    assert result.rows[0].raw_values == {"name": "Масло ши", "unit": "g", "notes": "важное"}
    assert result.rows[0].normalized_values["name"] == "Масло ши"
    assert result.rows[0].status == "valid"


def test_parses_utf8_bom_semicolon_tab_and_cp1251_csv():
    bom = parse_import_file("ingredients.csv", "\ufeffname;unit\nВода;ml\n".encode("utf-8-sig"), "ingredients")
    tab = parse_import_file("clients.csv", "full_name\tphone\nАнна\t123\n".encode(), "clients")
    cp1251 = parse_import_file("ingredients.csv", "name;unit\nОтдушка;g\n".encode("cp1251"), "ingredients")

    assert bom.rows[0].normalized_values["unit"] == "ml"
    assert tab.rows[0].normalized_values["full_name"] == "Анна"
    assert cp1251.rows[0].normalized_values["name"] == "Отдушка"


def test_rejects_empty_csv():
    with pytest.raises(ImportParseError):
        parse_import_file("ingredients.csv", b"\n\n", "ingredients")


def test_detects_duplicate_headers_and_missing_required_columns():
    result = parse_import_file("ingredients.csv", b"name, Name,notes\nA,B,C\n", "clients")

    codes = [issue.code for issue in result.issues]
    assert "duplicate_header" in codes
    assert "missing_required_column" in codes


def test_enforces_max_rows_and_columns():
    too_many_rows = "name\n" + "\n".join(f"item{i}" for i in range(MAX_ROWS + 1))
    with pytest.raises(ImportParseError):
        parse_import_file("ingredients.csv", too_many_rows.encode(), "ingredients")

    headers = ",".join(f"c{i}" for i in range(MAX_COLUMNS + 1))
    with pytest.raises(ImportParseError):
        parse_import_file("ingredients.csv", f"{headers}\nvalues\n".encode(), "ingredients")


def test_rejects_unsupported_extension():
    with pytest.raises(UnsupportedImportFileError):
        parse_import_file("ingredients.txt", b"name\nA\n", "ingredients")


def test_produces_row_level_validation_issues():
    result = parse_import_file("ingredient_lots.csv", b"ingredient_name,quantity,unit,purchase_date\nOil,12,kg,not-date\n,12.5,g,2026-07-05\n", "ingredient_lots")

    assert result.rows[0].status == "error"
    assert {issue.code for issue in result.rows[0].issues} == {"invalid_unit", "invalid_date"}
    assert result.rows[1].status == "error"
    assert result.rows[1].issues[0].code == "missing_required_value"


def _cell(reference: str, value: str) -> str:
    return f'<c r="{reference}" t="inlineStr"><is><t>{value}</t></is></c>'


def _minimal_xlsx(sheet_rows_xml: str | None = None) -> bytes:
    rows_xml = sheet_rows_xml or f'<row r="1">{_cell("A1", "name")}{_cell("B1", "unit")}</row><row r="2">{_cell("A2", "Вода")}{_cell("B2", "ml")}</row>'
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as zf:
        zf.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        zf.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        zf.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{rows_xml}</sheetData></worksheet>')
    return output.getvalue()


def test_parses_simple_xlsx():
    result = parse_import_file("ingredients.xlsx", _minimal_xlsx(), "ingredients")

    assert result.headers == ["name", "unit"]
    assert result.rows[0].normalized_values == {"name": "Вода", "unit": "ml"}


def test_csv_preserves_real_source_row_numbers_with_blank_lines():
    result = parse_import_file("ingredients.csv", b"name,unit\n\nWater,ml\n\nOil,g\n", "ingredients")

    assert [row.row_number for row in result.rows] == [3, 5]


def test_csv_row_validation_uses_real_source_row_number():
    result = parse_import_file("ingredients.csv", b"name,unit\n\n,kg\n", "ingredients")

    assert result.rows[0].row_number == 3
    assert {issue.row_number for issue in result.rows[0].issues} == {3}


def test_xlsx_preserves_blank_middle_cells():
    content = _minimal_xlsx(
        f'<row r="1">{_cell("A1", "name")}{_cell("B1", "unit")}{_cell("C1", "notes")}</row>'
        f'<row r="2">{_cell("B2", "ml")}{_cell("C2", "comment")}</row>'
    )

    result = parse_import_file("ingredients.xlsx", content, "ingredients")
    row = result.rows[0]

    assert row.normalized_values["name"] == ""
    assert row.normalized_values["unit"] == "ml"
    assert row.normalized_values["notes"] == "comment"
    assert row.status == "error"
    assert {issue.code for issue in row.issues} == {"missing_required_value"}


def test_xlsx_preserves_real_row_numbers():
    content = _minimal_xlsx(
        f'<row r="1">{_cell("A1", "name")}{_cell("B1", "unit")}</row>'
        f'<row r="5">{_cell("A5", "Вода")}{_cell("B5", "ml")}</row>'
    )

    result = parse_import_file("ingredients.xlsx", content, "ingredients")

    assert result.rows[0].row_number == 5
