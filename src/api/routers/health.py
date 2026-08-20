import sqlite3
import time
from pathlib import Path

from fastapi import APIRouter


router = APIRouter()

START_TIME = time.monotonic()

ROOT = Path(__file__).resolve().parents[3]
DATABASE = ROOT / "db" / "nifty100.db"


def get_db_connection():
    """Create a SQLite database connection."""
    return sqlite3.connect(DATABASE)


@router.get("/health")
def health_check():
    """Return API health and database row counts."""

    conn = get_db_connection()

    try:
        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        db_row_counts = {}

        for row in tables:
            table_name = row[0]

            count = conn.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]

            db_row_counts[table_name] = count

    finally:
        conn.close()

    return {
        "status": "ok",
        "db_row_counts": db_row_counts,
        "uptime_seconds": round(
            time.monotonic() - START_TIME,
            2,
        ),
        "version": "1.0.0",
    }