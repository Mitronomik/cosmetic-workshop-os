from pydantic import BaseModel


class DatabaseStatusResponse(BaseModel):
    status: str
    database: str
    required_tables_present: bool
    migrations_expected: list[str]
    tables: list[str]
