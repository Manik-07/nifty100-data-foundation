"""
populate_ratios.py

Sprint 2 - Day 12

Loads financial statements from SQLite,
merges them,
checks duplicate records before KPI calculation.
"""

import sqlite3
import pandas as pd

from src.analytics.ratios import RatioCalculator
from src.analytics.cagr import CAGRCalculator
from src.analytics.cashflow_kpis import CashFlowKPIs

DATABASE = "db/nifty100.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def load_data():

    conn = get_connection()

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn
    )

    pnl = (
        pd.read_sql(
            "SELECT * FROM profitandloss",
            conn
        )
        .drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )
    )

    balance = (
        pd.read_sql(
            "SELECT * FROM balancesheet",
            conn
        )
        .drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )
    )

    cashflow = (
        pd.read_sql(
            "SELECT * FROM cashflow",
            conn
        )
        .drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )
    )

    conn.close()

    return (
        companies,
        pnl,
        balance,
        cashflow
    )


def merge_financials():

    companies, pnl, balance, cashflow = load_data()

    # Remove surrogate primary keys before merge
    pnl = pnl.drop(columns=["id"])

    balance = balance.drop(columns=["id"])

    cashflow = cashflow.drop(columns=["id"])

    df = (
        pnl
        .merge(
            balance,
            on=["company_id", "year"],
            how="inner"
        )
        .merge(
            cashflow,
            on=["company_id", "year"],
            how="inner"
        )
        .merge(
            companies,
            left_on="company_id",
            right_on="id",
            how="left"
        )
    )

    return df

def calculate_ratios(df):

    output = []

    for _, row in df.iterrows():

        record = {}

        record["company_id"] = row["company_id"]
        record["year"] = row["year"]

        # ----------------------------
        # Profitability Ratios
        # ----------------------------

        record["net_profit_margin_pct"] = (
            RatioCalculator.net_profit_margin(
                row["net_profit"],
                row["sales"]
            )
        )

        record["operating_profit_margin_pct"] = (
            RatioCalculator.operating_profit_margin(
                row["operating_profit"],
                row["sales"]
            )
        )

        record["return_on_equity_pct"] = (
            RatioCalculator.return_on_equity(
                row["net_profit"],
                row["equity_capital"],
                row["reserves"]
            )
        )

        # ----------------------------
        # Leverage
        # ----------------------------

        record["debt_to_equity"] = (
            RatioCalculator.debt_to_equity(
                row["borrowings"],
                row["equity_capital"],
                row["reserves"]
            )
        )

        record["interest_coverage"] = (
            RatioCalculator.interest_coverage(
                row["operating_profit"],
                row["other_income"],
                row["interest"]
            )
        )

        record["asset_turnover"] = (
            RatioCalculator.asset_turnover(
                row["sales"],
                row["total_assets"]
            )
        )

        # ----------------------------
        # Cash Flow KPIs
        # ----------------------------

        fcf = CashFlowKPIs.free_cash_flow(
            row["operating_activity"],
            row["investing_activity"]
        )

        record["free_cash_flow_cr"] = fcf

        capex = CashFlowKPIs.capex_intensity(
            row["investing_activity"],
            row["sales"]
        )

        record["capex_cr"] = (
            capex["value"]
            if capex is not None
            else None
        )

        record["cash_from_operations_cr"] = (
            row["operating_activity"]
        )

        # ----------------------------
        # Other Fields
        # ----------------------------

        record["earnings_per_share"] = row["eps"]

        record["book_value_per_share"] = row["book_value"]

        record["dividend_payout_ratio_pct"] = (
            row["dividend_payout"]
        )

        record["total_debt_cr"] = row["borrowings"]
                # ----------------------------
        # CAGR (Placeholder)
        # ----------------------------

        record["revenue_cagr_5yr"] = None
        record["pat_cagr_5yr"] = None
        record["eps_cagr_5yr"] = None

        # ----------------------------
        # Composite Quality Score
        # ----------------------------

        score = 0

        # ROE
        if (
            record["return_on_equity_pct"] is not None
            and record["return_on_equity_pct"] >= 15
        ):
            score += 25

        # Net Profit Margin
        if (
            record["net_profit_margin_pct"] is not None
            and record["net_profit_margin_pct"] >= 10
        ):
            score += 25

        # Debt to Equity
        if (
            record["debt_to_equity"] is not None
            and record["debt_to_equity"] <= 1
        ):
            score += 25

        # Interest Coverage
        if (
            record["interest_coverage"] is not None
            and record["interest_coverage"] >= 3
        ):
            score += 25

        record["composite_quality_score"] = score

        output.append(record)

    return pd.DataFrame(output)

def add_cagr_columns(df, ratio_df):

    ratio_df["revenue_cagr_5yr"] = None
    ratio_df["pat_cagr_5yr"] = None
    ratio_df["eps_cagr_5yr"] = None

    companies = df["company_id"].unique()

    for company in companies:

        company_df = (
            df[df["company_id"] == company]
            .sort_values("year")
            .reset_index(drop=True)
    )

        print(company, len(company_df))

        for i in range(5, len(company_df)):

            current = company_df.iloc[i]
            previous = company_df.iloc[i - 5]

            revenue = CAGRCalculator.calculate_cagr(
                previous["sales"],
                current["sales"],
                5
            )

            pat = CAGRCalculator.calculate_cagr(
                previous["net_profit"],
                current["net_profit"],
                5
            )

            eps = CAGRCalculator.calculate_cagr(
                previous["eps"],
                current["eps"],
                5
            )

            mask = (
                (ratio_df.company_id == current.company_id)
                &
                (ratio_df.year == current.year)
            )

            ratio_df.loc[
                mask,
                "revenue_cagr_5yr"
            ] = revenue["value"]

            ratio_df.loc[
                mask,
                "pat_cagr_5yr"
            ] = pat["value"]

            ratio_df.loc[
                mask,
                "eps_cagr_5yr"
            ] = eps["value"]

    return ratio_df

def save_financial_ratios(ratio_df):

    conn = get_connection()

    cursor = conn.cursor()

    # Remove existing data
    cursor.execute("DELETE FROM financial_ratios")

    conn.commit()

    ratio_df.to_sql(
        "financial_ratios",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()

    cursor.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    )

    count = cursor.fetchone()[0]

    conn.close()

    print("\n" + "=" * 60)
    print("financial_ratios table populated successfully.")
    print("Rows inserted:", count)
    print("=" * 60)


def check_source_duplicates():

    conn = get_connection()

    tables = [
        "profitandloss",
        "balancesheet",
        "cashflow"
    ]

    print("\n" + "=" * 70)
    print("CHECKING SOURCE TABLES FOR DUPLICATES")
    print("=" * 70)

    for table in tables:

        print(f"\n===== {table.upper()} =====")

        query = f"""
        SELECT
            company_id,
            year,
            COUNT(*) AS duplicate_count
        FROM {table}
        GROUP BY company_id, year
        HAVING COUNT(*) > 1
        """

        duplicates = pd.read_sql(query, conn)

        if duplicates.empty:
            print("No duplicates found.")
        else:
            print(duplicates)

    conn.close()
    """
populate_ratios.py

Sprint 2 - Day 12

Loads financial statements from SQLite,
merges them,
checks duplicate records before KPI calculation.
"""

import sqlite3
import pandas as pd

from src.analytics.ratios import RatioCalculator
from src.analytics.cagr import CAGRCalculator
from src.analytics.cashflow_kpis import CashFlowKPIs

DATABASE = "db/nifty100.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def load_data():

    conn = get_connection()

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn
    )

    pnl = (
        pd.read_sql(
            "SELECT * FROM profitandloss",
            conn
        )
        .drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )
    )

    balance = (
        pd.read_sql(
            "SELECT * FROM balancesheet",
            conn
        )
        .drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )
    )

    cashflow = (
        pd.read_sql(
            "SELECT * FROM cashflow",
            conn
        )
        .drop_duplicates(
            subset=["company_id", "year"],
            keep="first"
        )
    )

    conn.close()

    return (
        companies,
        pnl,
        balance,
        cashflow
    )


def merge_financials():

    companies, pnl, balance, cashflow = load_data()

    # Remove surrogate primary keys before merge
    pnl = pnl.drop(columns=["id"])

    balance = balance.drop(columns=["id"])

    cashflow = cashflow.drop(columns=["id"])

    df = (
        pnl
        .merge(
            balance,
            on=["company_id", "year"],
            how="inner"
        )
        .merge(
            cashflow,
            on=["company_id", "year"],
            how="inner"
        )
        .merge(
            companies,
            left_on="company_id",
            right_on="id",
            how="left"
        )
    )

    return df

def calculate_ratios(df):

    output = []

    for _, row in df.iterrows():

        record = {}

        record["company_id"] = row["company_id"]
        record["year"] = row["year"]

        # ----------------------------
        # Profitability Ratios
        # ----------------------------

        record["net_profit_margin_pct"] = (
            RatioCalculator.net_profit_margin(
                row["net_profit"],
                row["sales"]
            )
        )

        record["operating_profit_margin_pct"] = (
            RatioCalculator.operating_profit_margin(
                row["operating_profit"],
                row["sales"]
            )
        )

        record["return_on_equity_pct"] = (
            RatioCalculator.return_on_equity(
                row["net_profit"],
                row["equity_capital"],
                row["reserves"]
            )
        )

        # ----------------------------
        # Leverage
        # ----------------------------

        record["debt_to_equity"] = (
            RatioCalculator.debt_to_equity(
                row["borrowings"],
                row["equity_capital"],
                row["reserves"]
            )
        )

        record["interest_coverage"] = (
            RatioCalculator.interest_coverage(
                row["operating_profit"],
                row["other_income"],
                row["interest"]
            )
        )

        record["asset_turnover"] = (
            RatioCalculator.asset_turnover(
                row["sales"],
                row["total_assets"]
            )
        )

        # ----------------------------
        # Cash Flow KPIs
        # ----------------------------

        fcf = CashFlowKPIs.free_cash_flow(
            row["operating_activity"],
            row["investing_activity"]
        )

        record["free_cash_flow_cr"] = fcf

        capex = CashFlowKPIs.capex_intensity(
            row["investing_activity"],
            row["sales"]
        )

        record["capex_cr"] = (
            capex["value"]
            if capex is not None
            else None
        )

        record["cash_from_operations_cr"] = (
            row["operating_activity"]
        )

        # ----------------------------
        # Other Fields
        # ----------------------------

        record["earnings_per_share"] = row["eps"]

        record["book_value_per_share"] = row["book_value"]

        record["dividend_payout_ratio_pct"] = (
            row["dividend_payout"]
        )

        record["total_debt_cr"] = row["borrowings"]
                # ----------------------------
        # CAGR (Placeholder)
        # ----------------------------

        record["revenue_cagr_5yr"] = None
        record["pat_cagr_5yr"] = None
        record["eps_cagr_5yr"] = None

        # ----------------------------
        # Composite Quality Score
        # ----------------------------

        score = 0

        # ROE
        if (
            record["return_on_equity_pct"] is not None
            and record["return_on_equity_pct"] >= 15
        ):
            score += 25

        # Net Profit Margin
        if (
            record["net_profit_margin_pct"] is not None
            and record["net_profit_margin_pct"] >= 10
        ):
            score += 25

        # Debt to Equity
        if (
            record["debt_to_equity"] is not None
            and record["debt_to_equity"] <= 1
        ):
            score += 25

        # Interest Coverage
        if (
            record["interest_coverage"] is not None
            and record["interest_coverage"] >= 3
        ):
            score += 25

        record["composite_quality_score"] = score

        output.append(record)

    return pd.DataFrame(output)

import re


def extract_year(value):

    match = re.search(r"\d{4}", str(value))

    if match:
        return int(match.group())

    return None


def add_cagr_columns(df, ratio_df):

    ratio_df["revenue_cagr_5yr"] = None
    ratio_df["pat_cagr_5yr"] = None
    ratio_df["eps_cagr_5yr"] = None

    df = df.copy()

    df["year_num"] = df["year"].apply(extract_year)

    df = df[df["year_num"].notna()]

    for company in df["company_id"].unique():

        company_df = (
            df[df["company_id"] == company]
            .sort_values("year_num")
            .reset_index(drop=True)
        )

        year_lookup = {}

        for _, row in company_df.iterrows():
            year_lookup[row["year_num"]] = row

        for _, current in company_df.iterrows():

            previous_year = current["year_num"] - 5

            if previous_year not in year_lookup:
                continue

            previous = year_lookup[previous_year]

            revenue = CAGRCalculator.calculate_cagr(
                previous["sales"],
                current["sales"],
                5
            )

            pat = CAGRCalculator.calculate_cagr(
                previous["net_profit"],
                current["net_profit"],
                5
            )

            eps = CAGRCalculator.calculate_cagr(
                previous["eps"],
                current["eps"],
                5
            )

            mask = (
                (ratio_df["company_id"] == current["company_id"])
                &
                (ratio_df["year"] == current["year"])
            )

            ratio_df.loc[
                mask,
                "revenue_cagr_5yr"
            ] = revenue["value"]

            ratio_df.loc[
                mask,
                "pat_cagr_5yr"
            ] = pat["value"]

            ratio_df.loc[
                mask,
                "eps_cagr_5yr"
            ] = eps["value"]

    return ratio_df

def save_financial_ratios(ratio_df):

    conn = get_connection()

    cursor = conn.cursor()

    # Remove existing data
    cursor.execute("DELETE FROM financial_ratios")

    conn.commit()

    ratio_df.to_sql(
        "financial_ratios",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()

    cursor.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    )

    count = cursor.fetchone()[0]

    conn.close()

    print("\n" + "=" * 60)
    print("financial_ratios table populated successfully.")
    print("Rows inserted:", count)
    print("=" * 60)


def generate_capital_allocation(df):

    output = []

    for _, row in df.iterrows():

        pattern = CashFlowKPIs.capital_allocation_pattern(
            row["operating_activity"],
            row["investing_activity"],
            row["financing_activity"]
        )

        output.append({
            "company_id": row["company_id"],
            "year": row["year"],
            "cfo_sign": "+" if row["operating_activity"] >= 0 else "-",
            "cfi_sign": "+" if row["investing_activity"] >= 0 else "-",
            "cff_sign": "+" if row["financing_activity"] >= 0 else "-",
            "pattern_label": pattern
        })

    allocation_df = pd.DataFrame(output)

    allocation_df.to_csv(
        "output/capital_allocation.csv",
        index=False
    )

    print("\ncapital_allocation.csv generated.")
def generate_edge_case_log(df, ratio_df):

    import os

    os.makedirs("output", exist_ok=True)

    with open("output/ratio_edge_cases.log", "w") as log:

        log.write("Financial Ratio Edge Cases\n")
        log.write("=" * 60 + "\n\n")

        for _, ratio in ratio_df.iterrows():

            source = df[
                (df["company_id"] == ratio["company_id"])
                &
                (df["year"] == ratio["year"])
            ]

            if source.empty:
                continue

            source = source.iloc[0]

            # --------------------------
            # ROE Comparison
            # --------------------------
            if (
                ratio["return_on_equity_pct"] is not None
                and pd.notna(source["roe_percentage"])
            ):

                diff = abs(
                    ratio["return_on_equity_pct"]
                    - source["roe_percentage"]
                )

                if diff > 5:

                    log.write(
                        f"{ratio['company_id']} {ratio['year']} | "
                        f"ROE Difference = {diff:.2f}%\n"
                    )

            # --------------------------
            # ROCE Comparison
            # --------------------------

            roce = RatioCalculator.return_on_capital_employed(
                source["operating_profit"],
                source["equity_capital"],
                source["reserves"],
                source["borrowings"]
            )

            if (
                roce is not None
                and pd.notna(source["roce_percentage"])
            ):

                diff = abs(
                    roce - source["roce_percentage"]
                )

                if diff > 5:

                    log.write(
                        f"{ratio['company_id']} {ratio['year']} | "
                        f"ROCE Difference = {diff:.2f}%\n"
                    )

    print("\nratio_edge_cases.log generated.")

if __name__ == "__main__":

    print("=" * 60)
    print("Running Financial Ratio Engine")
    print("=" * 60)

    # Merge all financial data
    df = merge_financials()

    print(f"Merged rows : {len(df)}")

    # Calculate all ratios
    ratio_df = calculate_ratios(df)

    # Add CAGR columns
    ratio_df = add_cagr_columns(df, ratio_df)

    print(f"Calculated rows : {len(ratio_df)}")

    # Save into SQLite
    save_financial_ratios(ratio_df)

    # Generate CSV
    generate_capital_allocation(df)

    # Generate Edge Case Log
    generate_edge_case_log(df, ratio_df)

    print("\nPreview\n")
    print(ratio_df.head())