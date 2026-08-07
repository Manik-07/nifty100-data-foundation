from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


# ---------------------------------------------------------
# Project Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"

MARKET_CAP_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "market_cap.xlsx"
)

OUTPUT_DIR = PROJECT_ROOT / "output"

VALUATION_SUMMARY_PATH = (
    OUTPUT_DIR / "valuation_summary.xlsx"
)

VALUATION_FLAGS_PATH = (
    OUTPUT_DIR / "valuation_flags.csv"
)


# ---------------------------------------------------------
# Load Market Cap / Valuation History
# ---------------------------------------------------------

def load_market_cap():
    """
    Load historical valuation data from market_cap.xlsx.
    """

    df = pd.read_excel(MARKET_CAP_PATH)

    numeric_columns = [
        "year",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


# ---------------------------------------------------------
# Load Company / Sector Information
# ---------------------------------------------------------

def load_companies():
    """
    Load company names and broad sectors.
    """

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector AS sector

        FROM companies c

        LEFT JOIN sectors s
            ON c.id = s.company_id

        ORDER BY c.id
    """

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            query,
            conn,
        )

    df = df.drop_duplicates(
        subset=["company_id"],
        keep="last",
    )

    return df


# ---------------------------------------------------------
# Load Latest FCF
# ---------------------------------------------------------

def load_latest_fcf():
    """
    Load the latest available annual Free Cash Flow
    for every company.
    """

    query = """
        WITH ranked_fcf AS (
            SELECT
                company_id,
                year,
                free_cash_flow_cr,

                CAST(
                    SUBSTR(year, -4)
                    AS INTEGER
                ) AS year_number,

                ROW_NUMBER() OVER (
                    PARTITION BY company_id

                    ORDER BY
                        CAST(
                            SUBSTR(year, -4)
                            AS INTEGER
                        ) DESC,
                        id DESC
                ) AS rn

            FROM financial_ratios

            WHERE
                year GLOB '*[0-9][0-9][0-9][0-9]'
                AND free_cash_flow_cr IS NOT NULL
        )

        SELECT
            company_id,
            year AS fcf_year,
            free_cash_flow_cr

        FROM ranked_fcf

        WHERE rn = 1
    """

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            query,
            conn,
        )

    df["free_cash_flow_cr"] = pd.to_numeric(
        df["free_cash_flow_cr"],
        errors="coerce",
    )

    return df


# ---------------------------------------------------------
# Build Valuation Summary
# ---------------------------------------------------------

def build_valuation_summary():
    """
    Calculate valuation metrics and valuation flags
    for all Nifty 100 companies.
    """

    market = load_market_cap()
    companies = load_companies()
    fcf = load_latest_fcf()


    # -----------------------------------------------------
    # Latest valuation year
    # -----------------------------------------------------

    latest_year = int(
        market["year"].max()
    )

    latest = market[
        market["year"] == latest_year
    ].copy()


    # Guarantee one row per company
    latest = latest.drop_duplicates(
        subset=["company_id"],
        keep="last",
    )


    # -----------------------------------------------------
    # 5-Year Median P/E
    # -----------------------------------------------------
    #
    # Latest year = 2024
    # Five-year window = 2020–2024
    # -----------------------------------------------------

    five_year_start = latest_year - 4

    five_year_market = market[
        market["year"].between(
            five_year_start,
            latest_year,
        )
    ].copy()


    median_pe = (
        five_year_market
        .groupby("company_id")["pe_ratio"]
        .median()
        .reset_index()
        .rename(
            columns={
                "pe_ratio": "5yr_median_PE"
            }
        )
    )


    # -----------------------------------------------------
    # Merge Datasets
    # -----------------------------------------------------

    summary = (
        companies
        .merge(
            latest[
                [
                    "company_id",
                    "market_cap_crore",
                    "pe_ratio",
                    "pb_ratio",
                    "ev_ebitda",
                ]
            ],
            on="company_id",
            how="left",
        )
        .merge(
            fcf[
                [
                    "company_id",
                    "free_cash_flow_cr",
                ]
            ],
            on="company_id",
            how="left",
        )
        .merge(
            median_pe,
            on="company_id",
            how="left",
        )
    )


    # -----------------------------------------------------
    # FCF Yield
    # -----------------------------------------------------

    summary["FCF_yield_pct"] = np.where(
        summary["market_cap_crore"] > 0,

        (
            summary["free_cash_flow_cr"]
            / summary["market_cap_crore"]
        )
        * 100,

        np.nan,
    )


    # -----------------------------------------------------
    # Sector Median P/E
    # -----------------------------------------------------

    summary["sector_median_PE"] = (
        summary
        .groupby("sector")["pe_ratio"]
        .transform("median")
    )


    # -----------------------------------------------------
    # P/E vs Sector Median %
    # -----------------------------------------------------

    summary["PE_vs_sector_median_pct"] = np.where(
        summary["sector_median_PE"] > 0,

        (
            (
                summary["pe_ratio"]
                - summary["sector_median_PE"]
            )
            / summary["sector_median_PE"]
        )
        * 100,

        np.nan,
    )


    # -----------------------------------------------------
    # Valuation Flag
    # -----------------------------------------------------

    def valuation_flag(row):

        pe = row["pe_ratio"]
        sector_median = row["sector_median_PE"]

        if pd.isna(pe) or pd.isna(sector_median):
            return "Fair"

        if pe > sector_median * 1.5:
            return "Caution"

        if pe < sector_median * 0.7:
            return "Discount"

        return "Fair"


    summary["flag"] = summary.apply(
        valuation_flag,
        axis=1,
    )


    # -----------------------------------------------------
    # Final Required Columns
    # -----------------------------------------------------

    summary = summary.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        }
    )


    summary = summary[
        [
            "company_id",
            "company_name",
            "sector",
            "P/E",
            "P/B",
            "EV/EBITDA",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag",
        ]
    ]


    # -----------------------------------------------------
    # Round Output
    # -----------------------------------------------------

    numeric_output_columns = [
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
    ]

    summary[
        numeric_output_columns
    ] = summary[
        numeric_output_columns
    ].round(2)


    return summary


# ---------------------------------------------------------
# Export Files
# ---------------------------------------------------------

def export_valuation_files():
    """
    Generate valuation_summary.xlsx and valuation_flags.csv.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    summary = build_valuation_summary()


    # Validate company count
    if len(summary) != 92:

        raise ValueError(
            f"Expected 92 companies, "
            f"but valuation summary contains {len(summary)} rows."
        )


    if summary["company_id"].nunique() != 92:

        raise ValueError(
            "Valuation summary does not contain "
            "92 unique company IDs."
        )


    # -----------------------------------------------------
    # Excel Summary
    # -----------------------------------------------------

    summary.to_excel(
        VALUATION_SUMMARY_PATH,
        index=False,
    )


    # -----------------------------------------------------
    # Caution / Discount Flags
    # -----------------------------------------------------

    flags = summary[
        summary["flag"].isin(
            [
                "Caution",
                "Discount",
            ]
        )
    ].copy()


    flags.to_csv(
        VALUATION_FLAGS_PATH,
        index=False,
    )


    return summary, flags


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    summary, flags = export_valuation_files()

    print("=" * 60)
    print("VALUATION MODULE COMPLETE")
    print("=" * 60)

    print(
        f"Companies processed: {len(summary)}"
    )

    print(
        f"Caution: "
        f"{(summary['flag'] == 'Caution').sum()}"
    )

    print(
        f"Discount: "
        f"{(summary['flag'] == 'Discount').sum()}"
    )

    print(
        f"Fair: "
        f"{(summary['flag'] == 'Fair').sum()}"
    )

    print()

    print(
        f"Created: {VALUATION_SUMMARY_PATH}"
    )

    print(
        f"Created: {VALUATION_FLAGS_PATH}"
    )