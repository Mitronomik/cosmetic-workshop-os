MIGRATION_ID = "0018_demo_data_tracking"


def upgrade(connection):
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS demo_data_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            demo_version TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            cleared_at TEXT,
            summary_json TEXT NOT NULL DEFAULT '{}',
            CHECK (length(trim(demo_version)) > 0),
            CHECK (status IN ('active', 'cleared', 'failed'))
        );

        CREATE INDEX IF NOT EXISTS idx_demo_data_sessions_status_created
            ON demo_data_sessions(status, created_at, id);

        CREATE TABLE IF NOT EXISTS demo_data_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            label TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES demo_data_sessions(id),
            UNIQUE(session_id, table_name, record_id),
            CHECK (session_id > 0),
            CHECK (length(trim(table_name)) > 0),
            CHECK (record_id > 0)
        );

        CREATE INDEX IF NOT EXISTS idx_demo_data_records_session_table
            ON demo_data_records(session_id, table_name, record_id);
        CREATE INDEX IF NOT EXISTS idx_demo_data_records_table_record
            ON demo_data_records(table_name, record_id);
        """)
