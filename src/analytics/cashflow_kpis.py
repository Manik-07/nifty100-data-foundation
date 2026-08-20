"""
cashflow_kpis.py

Sprint 5 - Day 31
Cash Flow Intelligence Module

Features:
1. CFO Quality Score
2. CFO Quality Label
3. CapEx Intensity
4. CapEx Label
5. Distress Signal
6. Deleveraging Flag
7. FCF CAGR - 5 year
8. FCF Conversion
9. Capital Allocation Pattern

Outputs:
    output/cashflow_intelligence.xlsx
    output/distress_alerts.csv
"""

from pathlib import Path
import sqlite3
import re
import math

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "db" / "nifty100.db"
CAPITAL_ALLOCATION_PATH = ROOT / "output" / "capital_allocation.csv"

OUTPUT_DIR = ROOT / "output"
INTELLIGENCE_PATH = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_PATH = OUTPUT_DIR / "distress_alerts.csv"


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ============================================================
# YEAR HELPERS
# ============================================================

def year_number(year_text):
    """
    Extract numeric year from strings such as:
        Mar 2024
        Dec 2019
        Sep 2023
    """
    if pd.isna(year_text):
        return None

    match = re.search(r"(\d{4})", str(year_text))

    if match:
        return int(match.group(1))

    return None


def year_sort_key(year_text):
    year = year_number(year_text)

    if year is None:
        return 9999

    return year


# ============================================================
# SAFE NUMERIC HELPERS
# ============================================================

def safe_float(value):
    if value is None:
        return None

    try:
        value = float(value)

        if math.isnan(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def safe_divide(numerator, denominator):
    numerator = safe_float(numerator)
    denominator = safe_float(denominator)

    if numerator is None or denominator is None:
        return None

    if denominator == 0:
        return None

    return numerator / denominator


# ============================================================
# CAGR
# ============================================================

def calculate_cagr(start_value, end_value, years=5):
    """
    CAGR is only meaningful when both start and end values
    are positive.

    Returns percentage.
    """

    start_value = safe_float(start_value)
    end_value = safe_float(end_value)

    if start_value is None or end_value is None:
        return None

    if years <= 0:
        return None

    if start_value <= 0 or end_value <= 0:
        return None

    try:
        return round(
            ((end_value / start_value) ** (1 / years) - 1) * 100,
            2
        )
    except (ValueError, ZeroDivisionError):
        return None


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    con = get_connection()

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name
        FROM companies
        ORDER BY id
        """,
        con
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector AS sector
        FROM sectors
        """,
        con
    )

    profit_loss = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales,
            net_profit
        FROM profitandloss
        """,
        con
    )

    cashflow = pd.read_sql_query(
        """
        SELECT
            id,
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
        """,
        con
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            free_cash_flow_cr,
            capex_cr,
            cash_from_operations_cr,
            total_debt_cr
        FROM financial_ratios
        """,
        con
    )

    balancesheet = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            borrowings
        FROM balancesheet
        """,
        con
    )

    con.close()

    return (
        companies,
        sectors,
        profit_loss,
        cashflow,
        ratios,
        balancesheet,
    )


# ============================================================
# DEDUPLICATE CASH FLOW
# ============================================================

def select_best_cashflow_rows(cashflow, ratios):
    """
    The source cashflow table contains duplicate company/year
    combinations.

    We use cash_from_operations_cr from financial_ratios as
    the reference to select the cashflow row whose CFO is
    closest to the Ratio Engine CFO.

    For rows without a matching Ratio Engine value, choose
    the row with the largest absolute net cash flow.
    """

    cashflow = cashflow.copy()
    ratios = ratios.copy()

    cashflow["year_num"] = cashflow["year"].apply(year_number)
    ratios["year_num"] = ratios["year"].apply(year_number)

    ratios_reference = ratios[
        ["company_id", "year_num", "cash_from_operations_cr"]
    ].copy()

    ratios_reference = ratios_reference.drop_duplicates(
        subset=["company_id", "year_num"],
        keep="last"
    )

    cashflow = cashflow.merge(
        ratios_reference,
        on=["company_id", "year_num"],
        how="left"
    )

    cashflow["cfo_difference"] = (
        cashflow["operating_activity"]
        - cashflow["cash_from_operations_cr"]
    ).abs()

    cashflow["net_cash_abs"] = cashflow["net_cash_flow"].abs()

    selected_rows = []

    for (company_id, year_num), group in cashflow.groupby(
        ["company_id", "year_num"],
        dropna=False
    ):

        group = group.copy()

        reference_exists = group["cash_from_operations_cr"].notna().any()

        if reference_exists:
            group = group.sort_values(
                ["cfo_difference", "id"],
                ascending=[True, True]
            )
        else:
            group = group.sort_values(
                ["net_cash_abs", "id"],
                ascending=[False, True]
            )

        selected_rows.append(group.iloc[0])

    result = pd.DataFrame(selected_rows)

    columns = [
        "company_id",
        "year",
        "year_num",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]

    return result[columns].copy()


# ============================================================
# DEDUPLICATE P&L
# ============================================================

def deduplicate_profit_loss(profit_loss):
    """
    Keep one P&L row per company/year.

    Prefer the row with the largest absolute sales because
    source files can contain duplicate/partial rows.
    """

    df = profit_loss.copy()

    df["year_num"] = df["year"].apply(year_number)

    df["sales_abs"] = df["sales"].abs()

    df = df.sort_values(
        ["company_id", "year_num", "sales_abs"],
        ascending=[True, True, False]
    )

    df = df.drop_duplicates(
        subset=["company_id", "year_num"],
        keep="first"
    )

    return df[
        [
            "company_id",
            "year",
            "year_num",
            "sales",
            "net_profit",
        ]
    ].copy()


# ============================================================
# DEDUPLICATE BALANCE SHEET
# ============================================================

def deduplicate_balance_sheet(balancesheet):
    """
    Keep one borrowing value per company/year.
    """

    df = balancesheet.copy()

    df["year_num"] = df["year"].apply(year_number)

    df["borrowings_abs"] = df["borrowings"].abs()

    df = df.sort_values(
        ["company_id", "year_num", "borrowings_abs"],
        ascending=[True, True, False]
    )

    df = df.drop_duplicates(
        subset=["company_id", "year_num"],
        keep="first"
    )

    return df[
        [
            "company_id",
            "year",
            "year_num",
            "borrowings",
        ]
    ].copy()


# ============================================================
# CFO QUALITY
# ============================================================

def calculate_cfo_quality(company_id, cashflow_df, pnl_df):
    """
    CFO Quality Score:
        CFO / PAT

    Average over latest 5 available years.

    Labels:
        > 1.0      High Quality
        0.5 - 1.0  Moderate
        < 0.5      Accrual Risk
    """

    merged = cashflow_df.merge(
        pnl_df[
            [
                "company_id",
                "year_num",
                "net_profit",
            ]
        ],
        on=["company_id", "year_num"],
        how="inner"
    )

    merged = merged.sort_values("year_num", ascending=False)

    ratios = []

    for _, row in merged.iterrows():

        cfo = safe_float(row["operating_activity"])
        pat = safe_float(row["net_profit"])

        if cfo is None or pat is None:
            continue

        if pat <= 0:
            continue

        ratio = safe_divide(cfo, pat)

        if ratio is not None and math.isfinite(ratio):
            ratios.append(ratio)

    ratios = ratios[:5]

    if not ratios:
        return None, "Insufficient Data"

    score = sum(ratios) / len(ratios)

    score = round(score, 2)

    if score > 1.0:
        label = "High Quality"
    elif score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return score, label


# ============================================================
# CAPEX INTENSITY
# ============================================================

def calculate_capex_intensity(
    latest_cashflow,
    latest_pnl
):
    """
    CapEx Intensity:
        ABS(investing_activity) / sales * 100
    """

    if latest_cashflow is None or latest_pnl is None:
        return None, "Insufficient Data"

    investing = safe_float(
        latest_cashflow["investing_activity"]
    )

    sales = safe_float(
        latest_pnl["sales"]
    )

    if investing is None or sales is None:
        return None, "Insufficient Data"

    if sales <= 0:
        return None, "Insufficient Data"

    intensity = abs(investing) / sales * 100

    intensity = round(intensity, 2)

    if intensity < 3:
        label = "Asset Light"
    elif intensity <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


# ============================================================
# FCF CAGR
# ============================================================

def calculate_fcf_cagr(company_cashflow):
    """
    FCF = CFO + CFI

    Calculate CAGR using latest year and approximately
    five years earlier.

    CAGR is returned only if both FCF values are positive.
    """

    df = company_cashflow.sort_values("year_num")

    df["fcf"] = (
        df["operating_activity"].fillna(0)
        + df["investing_activity"].fillna(0)
    )

    df = df.dropna(subset=["year_num"])

    if len(df) < 2:
        return None

    latest = df.iloc[-1]

    target_year = latest["year_num"] - 5

    candidates = df[
        df["year_num"] <= target_year
    ]

    if candidates.empty:
        return None

    start = candidates.iloc[-1]

    actual_years = latest["year_num"] - start["year_num"]

    if actual_years <= 0:
        return None

    return calculate_cagr(
        start["fcf"],
        latest["fcf"],
        actual_years
    )


# ============================================================
# FCF CONVERSION
# ============================================================

def calculate_fcf_conversion(
    latest_cashflow,
    latest_pnl
):
    """
    FCF Conversion:
        FCF / PAT * 100

    FCF = CFO + CFI
    """

    if latest_cashflow is None or latest_pnl is None:
        return None

    cfo = safe_float(
        latest_cashflow["operating_activity"]
    )

    cfi = safe_float(
        latest_cashflow["investing_activity"]
    )

    pat = safe_float(
        latest_pnl["net_profit"]
    )

    if cfo is None or cfi is None or pat is None:
        return None

    if pat == 0:
        return None

    fcf = cfo + cfi

    return round((fcf / pat) * 100, 2)


# ============================================================
# DISTRESS FLAG
# ============================================================

def calculate_distress_flag(latest_cashflow):
    """
    Distress Signal:

        CFO < 0 AND CFF > 0
    """

    if latest_cashflow is None:
        return False

    cfo = safe_float(
        latest_cashflow["operating_activity"]
    )

    cff = safe_float(
        latest_cashflow["financing_activity"]
    )

    if cfo is None or cff is None:
        return False

    return cfo < 0 and cff > 0


# ============================================================
# DELEVERAGING FLAG
# ============================================================

def calculate_deleveraging_flag(
    company_cashflow,
    company_balance_sheet
):
    """
    Deleveraging:

        CFF < 0
        AND borrowings declining year-over-year
    """

    if company_cashflow.empty:
        return False

    if company_balance_sheet.empty:
        return False

    latest_cf = company_cashflow.sort_values(
        "year_num"
    ).iloc[-1]

    latest_year = latest_cf["year_num"]

    cff = safe_float(
        latest_cf["financing_activity"]
    )

    if cff is None or cff >= 0:
        return False

    bs = company_balance_sheet.sort_values(
        "year_num"
    )

    current = bs[
        bs["year_num"] == latest_year
    ]

    previous = bs[
        bs["year_num"] < latest_year
    ]

    if current.empty or previous.empty:
        return False

    current_borrowings = safe_float(
        current.iloc[-1]["borrowings"]
    )

    previous_borrowings = safe_float(
        previous.iloc[-1]["borrowings"]
    )

    if current_borrowings is None or previous_borrowings is None:
        return False

    return current_borrowings < previous_borrowings


# ============================================================
# CAPITAL ALLOCATION
# ============================================================

def load_capital_allocation():
    if not CAPITAL_ALLOCATION_PATH.exists():
        return pd.DataFrame(
            columns=[
                "company_id",
                "year",
                "pattern_label"
            ]
        )

    df = pd.read_csv(CAPITAL_ALLOCATION_PATH)

    df["year_num"] = df["year"].apply(year_number)

    return df


def get_latest_capital_allocation(
    company_id,
    capital_allocation
):
    df = capital_allocation[
        capital_allocation["company_id"] == company_id
    ].copy()

    if df.empty:
        return "Unknown"

    df = df.sort_values("year_num")

    return str(
        df.iloc[-1]["pattern_label"]
    )


# ============================================================
# BUILD INTELLIGENCE
# ============================================================

def build_intelligence():

    (
        companies,
        sectors,
        profit_loss,
        cashflow,
        ratios,
        balancesheet,
    ) = load_data()

    print()
    print("DAY 31 - CASH FLOW INTELLIGENCE")
    print("=" * 60)

    print(f"Companies loaded       : {len(companies)}")
    print(
        f"Cashflow companies     : "
        f"{cashflow['company_id'].nunique()}"
    )
    print(
        f"Ratio companies        : "
        f"{ratios['company_id'].nunique()}"
    )

    # --------------------------------------------------------
    # Clean source tables
    # --------------------------------------------------------

    cashflow_clean = select_best_cashflow_rows(
        cashflow,
        ratios
    )

    pnl_clean = deduplicate_profit_loss(
        profit_loss
    )

    bs_clean = deduplicate_balance_sheet(
        balancesheet
    )

    capital_allocation = load_capital_allocation()

    # --------------------------------------------------------
    # Sector mapping
    # --------------------------------------------------------

    sector_map = (
        sectors
        .drop_duplicates("company_id")
        .set_index("company_id")["sector"]
        .to_dict()
    )

    results = []
    distress_rows = []

    # --------------------------------------------------------
    # Process only the 92 companies in companies table
    # --------------------------------------------------------

    for _, company in companies.iterrows():

        company_id = company["company_id"]

        company_cf = cashflow_clean[
            cashflow_clean["company_id"] == company_id
        ].copy()

        company_pnl = pnl_clean[
            pnl_clean["company_id"] == company_id
        ].copy()

        company_bs = bs_clean[
            bs_clean["company_id"] == company_id
        ].copy()

        if company_cf.empty:
            print(
                f"WARNING: No cashflow data for {company_id}"
            )

            results.append({
                "company_id": company_id,
                "sector": sector_map.get(
                    company_id,
                    "Unknown"
                ),
                "cfo_quality_score": None,
                "cfo_quality_label": "Insufficient Data",
                "capex_intensity_pct": None,
                "capex_label": "Insufficient Data",
                "fcf_cagr_5yr": None,
                "fcf_conversion_pct": None,
                "distress_flag": False,
                "deleveraging_flag": False,
                "capital_allocation_label": get_latest_capital_allocation(
                    company_id,
                    capital_allocation
                ),
            })

            continue

        company_cf = company_cf.sort_values(
            "year_num"
        )

        company_pnl = company_pnl.sort_values(
            "year_num"
        )

        latest_cf = company_cf.iloc[-1]

        latest_year = latest_cf["year_num"]

        pnl_latest = company_pnl[
            company_pnl["year_num"] == latest_year
        ]

        if pnl_latest.empty:
            # fallback to latest available P&L year
            latest_pnl = (
                company_pnl.iloc[-1]
                if not company_pnl.empty
                else None
            )
        else:
            latest_pnl = pnl_latest.iloc[-1]

        # ----------------------------------------------------
        # CFO QUALITY
        # ----------------------------------------------------

        cfo_score, cfo_label = calculate_cfo_quality(
            company_id,
            company_cf,
            company_pnl
        )

        # ----------------------------------------------------
        # CAPEX INTENSITY
        # ----------------------------------------------------

        capex_intensity, capex_label = (
            calculate_capex_intensity(
                latest_cf,
                latest_pnl
            )
        )

        # ----------------------------------------------------
        # FCF CAGR
        # ----------------------------------------------------

        fcf_cagr = calculate_fcf_cagr(
            company_cf
        )

        # ----------------------------------------------------
        # FCF CONVERSION
        # ----------------------------------------------------

        fcf_conversion = calculate_fcf_conversion(
            latest_cf,
            latest_pnl
        )

        # ----------------------------------------------------
        # DISTRESS
        # ----------------------------------------------------

        distress_flag = calculate_distress_flag(
            latest_cf
        )

        # ----------------------------------------------------
        # DELEVERAGING
        # ----------------------------------------------------

        deleveraging_flag = calculate_deleveraging_flag(
            company_cf,
            company_bs
        )

        # ----------------------------------------------------
        # CAPITAL ALLOCATION
        # ----------------------------------------------------

        capital_allocation_label = (
            get_latest_capital_allocation(
                company_id,
                capital_allocation
            )
        )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        result = {
            "company_id": company_id,
            "sector": sector_map.get(
                company_id,
                "Unknown"
            ),
            "cfo_quality_score": cfo_score,
            "cfo_quality_label": cfo_label,
            "capex_intensity_pct": capex_intensity,
            "capex_label": capex_label,
            "fcf_cagr_5yr": fcf_cagr,
            "fcf_conversion_pct": fcf_conversion,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": capital_allocation_label,
        }

        results.append(result)

        # ----------------------------------------------------
        # DISTRESS ALERT
        # ----------------------------------------------------

        if distress_flag:

            distress_rows.append({
                "company_id": company_id,
                "sector": sector_map.get(
                    company_id,
                    "Unknown"
                ),
                "year": latest_cf["year"],
                "cfo_cr": latest_cf[
                    "operating_activity"
                ],
                "cff_cr": latest_cf[
                    "financing_activity"
                ],
                "latest_net_profit_cr": (
                    latest_pnl["net_profit"]
                    if latest_pnl is not None
                    else None
                ),
            })

    # ========================================================
    # DATAFRAMES
    # ========================================================

    intelligence = pd.DataFrame(results)

    distress = pd.DataFrame(
        distress_rows,
        columns=[
            "company_id",
            "sector",
            "year",
            "cfo_cr",
            "cff_cr",
            "latest_net_profit_cr",
        ]
    )

    # ========================================================
    # SORT
    # ========================================================

    intelligence = intelligence.sort_values(
        "company_id"
    ).reset_index(drop=True)

    distress = distress.sort_values(
        "company_id"
    ).reset_index(drop=True)

    # ========================================================
    # OUTPUT DIRECTORY
    # ========================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # WRITE EXCEL
    # ========================================================

    with pd.ExcelWriter(
        INTELLIGENCE_PATH,
        engine="openpyxl"
    ) as writer:

        intelligence.to_excel(
            writer,
            sheet_name="cashflow_intelligence",
            index=False
        )

        # Useful summary sheet
        summary = pd.DataFrame({
            "metric": [
                "Total companies",
                "High Quality CFO",
                "Moderate CFO",
                "Accrual Risk CFO",
                "Asset Light",
                "Moderate CapEx",
                "Capital Intensive",
                "Distress Signals",
                "Deleveraging Companies",
            ],
            "count": [
                len(intelligence),

                (
                    intelligence[
                        "cfo_quality_label"
                    ] == "High Quality"
                ).sum(),

                (
                    intelligence[
                        "cfo_quality_label"
                    ] == "Moderate"
                ).sum(),

                (
                    intelligence[
                        "cfo_quality_label"
                    ] == "Accrual Risk"
                ).sum(),

                (
                    intelligence[
                        "capex_label"
                    ] == "Asset Light"
                ).sum(),

                (
                    intelligence[
                        "capex_label"
                    ] == "Moderate"
                ).sum(),

                (
                    intelligence[
                        "capex_label"
                    ] == "Capital Intensive"
                ).sum(),

                intelligence[
                    "distress_flag"
                ].sum(),

                intelligence[
                    "deleveraging_flag"
                ].sum(),
            ]
        })

        summary.to_excel(
            writer,
            sheet_name="summary",
            index=False
        )

    # ========================================================
    # WRITE DISTRESS CSV
    # ========================================================

    distress.to_csv(
        DISTRESS_PATH,
        index=False
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    print()
    print("RESULTS")
    print("=" * 60)

    print(
        f"Companies processed    : "
        f"{len(intelligence)}"
    )

    print(
        f"Expected companies     : 92"
    )

    print(
        f"Distress signals       : "
        f"{intelligence['distress_flag'].sum()}"
    )

    print(
        f"Deleveraging companies : "
        f"{intelligence['deleveraging_flag'].sum()}"
    )

    print()
    print("CFO QUALITY")
    print(
        intelligence[
            "cfo_quality_label"
        ].value_counts(dropna=False)
    )

    print()
    print("CAPEX LABEL")
    print(
        intelligence[
            "capex_label"
        ].value_counts(dropna=False)
    )

    print()
    print("OUTPUT FILES")
    print(
        f"{INTELLIGENCE_PATH}"
    )
    print(
        f"{DISTRESS_PATH}"
    )

    # ========================================================
    # FINAL CHECK
    # ========================================================

    if len(intelligence) == 92:
        print()
        print(
            "PASS - cashflow_intelligence.xlsx "
            "contains 92 companies."
        )
    else:
        print()
        print(
            "WARNING - Expected 92 companies but "
            f"generated {len(intelligence)}."
        )

    print()
    print("Day 31 cash flow intelligence completed.")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_intelligence()
    
# ============================================================
# TEST / API COMPATIBILITY CLASS
# ============================================================

class CashFlowKPIs:

    @staticmethod
    def free_cash_flow(cfo, cfi):
        """
        Free Cash Flow = CFO + CFI
        """
        if cfo is None or cfi is None:
            return None

        return cfo + cfi

    @staticmethod
    def cfo_quality_score(cfo, pat):
        """
        CFO Quality based on CFO / PAT.

        > 1.0  -> High Quality
        >= 0.5 -> Moderate
        < 0.5  -> Accrual Risk
        """
        if pat is None or pat == 0:
            return None

        if cfo is None:
            return None

        ratio = cfo / pat

        if ratio > 1.0:
            return "High Quality"
        elif ratio >= 0.5:
            return "Moderate"
        else:
            return "Accrual Risk"

    @staticmethod
    def capex_intensity(capex, sales):
        """
        CapEx Intensity = ABS(CapEx) / Sales * 100
        """
        if capex is None or sales is None:
            return None

        if sales <= 0:
            return None

        intensity = abs(capex) / sales * 100

        if intensity < 3:
            label = "Asset Light"
        elif intensity <= 8:
            label = "Moderate"
        else:
            label = "Capital Intensive"

        return {
            "value": round(intensity, 2),
            "label": label,
        }

    @staticmethod
    def fcf_conversion(fcf, pat):
        """
        FCF Conversion = FCF / PAT * 100
        """
        if fcf is None or pat is None:
            return None

        if pat == 0:
            return None

        return round((fcf / pat) * 100, 2)

    @staticmethod
    def capital_allocation_pattern(cfo, cfi, cff):
        """
        Classify capital allocation pattern.
        """

        if cfo is None or cfi is None or cff is None:
            return "Unknown"

        # Operating cash flow is negative while financing
        # cash flow is positive -> distress
        if cfo < 0 and cff > 0:
            return "Distress Signal"

        # Positive CFO + negative investing cash flow
        # indicates reinvestment.
        if cfo > 0 and cfi < 0:
            return "Reinvestor"

        # Positive CFO + positive investing cash flow
        # indicates cash accumulation.
        if cfo > 0 and cfi >= 0 and cff >= 0:
            return "Cash Accumulator"

        return "Other"