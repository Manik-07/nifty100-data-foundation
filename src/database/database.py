"""
database.py

Creates the SQLite database from schema.sql
"""

import sqlite3
from pathlib import Path


class DatabaseManager:

    def __init__(self,
                 db_path="db/nifty100.db",
                 schema_path="db/schema.sql"):

        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)

    def create_database(self):

        connection = sqlite3.connect(self.db_path)

        connection.execute("PRAGMA foreign_keys = ON;")

        with open(self.schema_path, "r", encoding="utf-8") as file:
            schema = file.read()

        connection.executescript(schema)

        connection.commit()

        print(f"Database created : {self.db_path}")

        return connection

    def show_tables(self, connection):

        cursor = connection.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name;
        """)

        tables = cursor.fetchall()

        print("\nTables Created")
        print("-" * 40)

        for table in tables:
            print(table[0])

        print("-" * 40)

        cursor.close()


if __name__ == "__main__":

    db = DatabaseManager()

    conn = db.create_database()

    db.show_tables(conn)

    conn.close()