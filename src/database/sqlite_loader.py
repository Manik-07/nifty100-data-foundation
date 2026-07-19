"""
sqlite_loader.py

Loads all datasets into SQLite database
and generates load_audit.csv
"""

import sqlite3
import pandas as pd

from src.etl.loader import ExcelLoader


class SQLiteLoader:

    def __init__(self, db_path="db/nifty100.db"):

        self.connection = sqlite3.connect(db_path)

        self.audit = []

    def load_table(self, dataframe, table_name):

        try:

            dataframe.to_sql(
                table_name,
                self.connection,
                if_exists="append",
                index=False
            )

            print(f"✅ Loaded {table_name:<20} Rows : {len(dataframe)}")

            self.audit.append({
                "table": table_name,
                "rows_loaded": len(dataframe),
                "status": "SUCCESS",
                "rejected_rows": 0
            })

        except Exception as e:

            print(f"❌ Failed {table_name}")

            self.audit.append({
                "table": table_name,
                "rows_loaded": 0,
                "status": "FAILED",
                "rejected_rows": len(dataframe),
                "error": str(e)
            })

    def generate_audit(self):

        audit_df = pd.DataFrame(self.audit)

        audit_df.to_csv(
            "data/output/load_audit.csv",
            index=False
        )

        print("\n========================================")
        print("Load Audit Generated")
        print("========================================")
        print(audit_df)

    def close(self):

        self.connection.close()


if __name__ == "__main__":

    loader = ExcelLoader()

    datasets = loader.load_all()

    sqlite_loader = SQLiteLoader()

    tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "prosandcons",
        "sectors",
        "stock_prices"
    ]

    for table in tables:

        sqlite_loader.load_table(
            datasets[table],
            table
        )

    sqlite_loader.generate_audit()

    sqlite_loader.close()

    print("\nDatabase loading completed successfully.")