"""
validator.py

Sprint 1 – Day 3

Implemented Rules
-----------------
DQ-01 : Primary Key Uniqueness
DQ-02 : Composite Key Uniqueness
DQ-03 : Foreign Key Integrity
DQ-04 : Balance Sheet Validation
DQ-05 : Operating Profit Validation
"""

import pandas as pd


class DataValidator:

    def __init__(self):
        self.failures = []

    # ----------------------------------------------------
    # DQ-01 : Primary Key
    # ----------------------------------------------------

    def check_primary_key(self, df, table_name, pk_column):

        duplicates = df[df.duplicated(subset=[pk_column], keep=False)]

        if duplicates.empty:
            print(f"✅ {table_name}: Primary Key check passed.")
        else:
            print(f"❌ {table_name}: Duplicate Primary Keys found.")

            for _, row in duplicates.iterrows():

                self.failures.append({
                    "rule": "DQ-01",
                    "table": table_name,
                    "severity": "CRITICAL",
                    "column": pk_column,
                    "value": row[pk_column],
                    "message": "Duplicate Primary Key"
                })

    # ----------------------------------------------------
    # DQ-02 : Composite Key
    # ----------------------------------------------------

    def check_composite_key(self, df, table_name, columns):

        duplicates = df[df.duplicated(subset=columns, keep=False)]

        if duplicates.empty:
            print(f"✅ {table_name}: Composite Key check passed.")
        else:
            print(f"❌ {table_name}: Duplicate Composite Keys found.")

            for _, row in duplicates.iterrows():

                self.failures.append({
                    "rule": "DQ-02",
                    "table": table_name,
                    "severity": "CRITICAL",
                    "column": ", ".join(columns),
                    "value": " | ".join(str(row[col]) for col in columns),
                    "message": "Duplicate Composite Key"
                })

    # ----------------------------------------------------
    # DQ-03 : Foreign Key
    # ----------------------------------------------------

    def check_foreign_key(
        self,
        child_df,
        parent_df,
        child_column,
        parent_column,
        table_name
    ):

        parent_keys = set(parent_df[parent_column])

        invalid = child_df[
            ~child_df[child_column].isin(parent_keys)
        ]

        if invalid.empty:
            print(f"✅ {table_name}: Foreign Key check passed.")
        else:
            print(f"❌ {table_name}: Foreign Key violations found.")

            for _, row in invalid.iterrows():

                self.failures.append({
                    "rule": "DQ-03",
                    "table": table_name,
                    "severity": "CRITICAL",
                    "column": child_column,
                    "value": row[child_column],
                    "message": "Foreign Key not found"
                })

    # ----------------------------------------------------
    # DQ-04 : Balance Sheet Check
    # ----------------------------------------------------

    def check_balance_sheet(self, df):

        tolerance = 0.01

        for _, row in df.iterrows():

            assets = row["total_assets"]
            liabilities = row["total_liabilities"]

            if pd.isna(assets) or pd.isna(liabilities):
                continue

            if assets == 0:
                continue

            difference = abs(assets - liabilities) / assets

            if difference > tolerance:

                self.failures.append({
                    "rule": "DQ-04",
                    "table": "balancesheet",
                    "severity": "WARNING",
                    "column": "total_assets,total_liabilities",
                    "value": f"{assets} | {liabilities}",
                    "message": "Balance Sheet does not balance"
                })

        print("✅ DQ-04 Balance Sheet Check Completed")

    # ----------------------------------------------------
    # DQ-05 : Operating Profit Check
    # ----------------------------------------------------

    def check_operating_profit(self, df):

        tolerance = 1.0

        for _, row in df.iterrows():

            if (
                pd.isna(row["sales"]) or
                pd.isna(row["expenses"]) or
                pd.isna(row["operating_profit"])
            ):
                continue

            expected = row["sales"] - row["expenses"]
            actual = row["operating_profit"]

            if abs(expected - actual) > tolerance:

                self.failures.append({
                    "rule": "DQ-05",
                    "table": "profitandloss",
                    "severity": "WARNING",
                    "column": "operating_profit",
                    "value": actual,
                    "message": "Operating Profit mismatch"
                })

        print("✅ DQ-05 Operating Profit Check Completed")
        
           # ----------------------------------------------------
    # DQ-06 : Positive Sales
    # ----------------------------------------------------

    def check_positive_sales(self, df):

        for _, row in df.iterrows():

            if pd.isna(row["sales"]):
                continue

            if row["sales"] <= 0:

                self.failures.append({
                    "rule": "DQ-06",
                    "table": "profitandloss",
                    "severity": "CRITICAL",
                    "column": "sales",
                    "value": row["sales"],
                    "message": "Sales must be greater than zero"
                })

        print("✅ DQ-06 Positive Sales Check Completed")

    # ----------------------------------------------------
    # Save Validation Report
    # ----------------------------------------------------

    def save_failures(
        self,
        output_file="data/output/validation_failures.csv"
    ):

        if not self.failures:
            print("\n✅ No validation failures found.")
            return

        failures_df = pd.DataFrame(self.failures)

        failures_df.to_csv(output_file, index=False)

        print("\n========================================")
        print("Validation Report Generated")
        print("========================================")
        print(f"Failures : {len(failures_df)}")
        print(f"Saved To : {output_file}")