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


def _codes(issues):
    return [issue.code for issue in issues]


def _all_codes(result):
    return [issue.code for issue in result.issues] + [issue.code for row in result.rows for issue in row.issues]


def test_header_alias_decimal_unit_date_email_id_and_readiness_contract():
    result = parse_import_file("lots.csv", "Компонент;Количество;Единица;Дата_покупки;id_компонента\nВода;100,5;г;05.07.2026;1\n".encode(), "ingredient_lots")

    assert result.headers == ["ingredient_name", "quantity", "unit", "purchase_date", "ingredient_id"]
    row = result.rows[0]
    assert row.raw_values["Количество"] == "100,5"
    assert row.normalized_values["quantity"] == "100.5"
    assert row.normalized_values["unit"] == "g"
    assert row.normalized_values["purchase_date"] == "2026-07-05"
    assert row.status == "warning"
    assert {"header_alias_used", "decimal_comma_normalized", "unit_alias_normalized", "date_format_normalized"} <= set(_all_codes(result))


def test_client_alias_and_invalid_email_warning():
    result = parse_import_file("clients.csv", "ФИО,email\nАнна,not-email\n".encode(), "clients")

    assert result.headers == ["full_name", "email"]
    assert result.rows[0].normalized_values["full_name"] == "Анна"
    assert "header_alias_used" in _codes(result.issues)
    assert result.rows[0].status == "warning"
    assert result.rows[0].issues[0].code == "invalid_email"


def test_ambiguous_decimal_and_positive_negative_rules_block_rows():
    ambiguous = parse_import_file("lots.csv", b"ingredient_name,quantity,unit\nOil,1.000,5,g\n", "ingredient_lots")
    # CSV comma splits this value; explicit semicolon keeps the ambiguous value intact.
    ambiguous = parse_import_file("lots.csv", "ingredient_name;quantity;unit\nOil;1.000,5;g\n".encode(), "ingredient_lots")
    assert ambiguous.rows[0].status == "error"
    assert "ambiguous_decimal" in _codes(ambiguous.rows[0].issues)

    zero_quantity = parse_import_file("lots.csv", b"ingredient_name,quantity,unit\nOil,0,g\n", "ingredient_lots")
    assert "invalid_positive_decimal" in _codes(zero_quantity.rows[0].issues)

    negative_price = parse_import_file("packaging.csv", b"name,cost\nJar,-1\n", "packaging_items")
    assert "invalid_non_negative_decimal" in _codes(negative_price.rows[0].issues)

    zero_price = parse_import_file("packaging.csv", b"name,cost\nJar,0\n", "packaging_items")
    assert zero_price.rows[0].status == "valid"


def test_unknown_unit_and_invalid_id_are_blocking():
    unit = parse_import_file("lots.csv", b"ingredient_name,quantity,unit\nOil,1,kg\n", "ingredient_lots")
    assert "invalid_unit" in _codes(unit.rows[0].issues)

    bad_id = parse_import_file("orders.csv", b"client_name,product_name,target_batch_size_value,target_batch_size_unit,client_id\nAnna,Cream,10,g,0\n", "orders")
    assert "invalid_id" in _codes(bad_id.rows[0].issues)
