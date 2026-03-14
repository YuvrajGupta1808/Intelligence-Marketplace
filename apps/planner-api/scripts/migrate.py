from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import text

from app.db.database import engine


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def _exec(conn, stmt: str, is_sqlite: bool) -> None:
    """Execute one SQL statement, working around SQLite limitations."""
    if is_sqlite:
        m = re.match(
            r"ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+(\w+)(.*)",
            stmt,
            re.IGNORECASE | re.DOTALL,
        )
        if m:
            table, column, rest = m.group(1), m.group(2), m.group(3).strip()
            if _column_exists(conn, table, column):
                return
            stmt = f"ALTER TABLE {table} ADD COLUMN {column} {rest}".strip()
    conn.execute(text(stmt))


def main() -> None:
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    is_sqlite = "sqlite" in str(engine.url)
    with engine.begin() as connection:
        for path in sorted(migrations_dir.glob("*.sql")):
            sql = path.read_text()
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    _exec(connection, stmt, is_sqlite)
    print("Migrations applied.")


if __name__ == "__main__":
    main()

