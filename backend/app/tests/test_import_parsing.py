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


def _minimal_xlsx() -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as zf:
        zf.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        zf.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        zf.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c t="inlineStr"><is><t>name</t></is></c><c t="inlineStr"><is><t>unit</t></is></c></row><row r="2"><c t="inlineStr"><is><t>Вода</t></is></c><c t="inlineStr"><is><t>ml</t></is></c></row></sheetData></worksheet>')
    return output.getvalue()


def test_parses_simple_xlsx():
    result = parse_import_file("ingredients.xlsx", _minimal_xlsx(), "ingredients")

    assert result.headers == ["name", "unit"]
    assert result.rows[0].normalized_values == {"name": "Вода", "unit": "ml"}
