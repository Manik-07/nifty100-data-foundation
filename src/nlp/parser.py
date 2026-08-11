import re
import sqlite3
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "analysis.xlsx"
DB_FILE = BASE_DIR / "db" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"

PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURES_FILE = OUTPUT_DIR / "parse_failures.csv"
VALIDATION_FILE = OUTPUT_DIR / "cagr_validation_flags.csv"


# ---------------------------------------------------------
# TARGET FIELDS
# ---------------------------------------------------------

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# ---------------------------------------------------------
# REQUIRED REGEX
# ---------------------------------------------------------

PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*([\d.]+)%"
)


# ---------------------------------------------------------
# RATIO ENGINE MAPPING
# ---------------------------------------------------------

CAGR_MAPPING = {
    "compounded_sales_growth": "revenue_cagr_5yr",
    "compounded_profit_growth": "pat_cagr_5yr",
}


# ---------------------------------------------------------
# PARSER
# ---------------------------------------------------------

def parse_metric(value):
    """
    Parse values such as:

        10 Years: 21%

    Returns:

        (period_years, value_pct)

    If the value does not match the required pattern:

        (None, None)
    """

    if pd.isna(value):
        return None, None

    text = str(value).strip()

    match = PATTERN.search(text)

    if not match:
        return None, None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


# ---------------------------------------------------------
# CAGR CROSS VALIDATION
# ---------------------------------------------------------

def validate_cagr(parsed_df):
    """
    Cross-validate 5-year parsed CAGR values against
    the existing financial_ratios table.

    Divergence:

        abs(parsed - computed)
        ---------------------- x 100
             abs(computed)

    Flag when divergence > 5%.
    """

    validation_records = []

    con = sqlite3.connect(DB_FILE)

    query = """
        SELECT
            company_id,
            revenue_cagr_5yr,
            pat_cagr_5yr
        FROM financial_ratios
        WHERE revenue_cagr_5yr IS NOT NULL
           OR pat_cagr_5yr IS NOT NULL
    """

    ratio_df = pd.read_sql_query(query, con)

    con.close()

    for _, row in parsed_df.iterrows():

        metric = row["metric_type"]
        period = row["period_years"]
        company_id = row["company_id"]
        parsed_value = row["value_pct"]

        # Only compare 5-year CAGR metrics
        if period != 5:
            continue

        if metric not in CAGR_MAPPING:
            continue

        db_column = CAGR_MAPPING[metric]

        matches = ratio_df[
            ratio_df["company_id"] == company_id
        ]

        if matches.empty:
            validation_records.append(
                {
                    "company_id": company_id,
                    "metric_type": metric,
                    "period_years": period,
                    "parsed_value_pct": parsed_value,
                    "computed_value_pct": None,
                    "divergence_pct": None,
                    "flag": "NO_COMPUTED_VALUE",
                }
            )
            continue

        computed_values = matches[db_column].dropna()

        if computed_values.empty:
            validation_records.append(
                {
                    "company_id": company_id,
                    "metric_type": metric,
                    "period_years": period,
                    "parsed_value_pct": parsed_value,
                    "computed_value_pct": None,
                    "divergence_pct": None,
                    "flag": "NO_COMPUTED_VALUE",
                }
            )
            continue

        # Use latest available computed 5-year CAGR
        computed_value = float(computed_values.iloc[-1])

        if computed_value == 0:
            divergence = None
            flag = "ZERO_COMPUTED_VALUE"

        else:
            divergence = (
                abs(parsed_value - computed_value)
                / abs(computed_value)
            ) * 100

            divergence = round(divergence, 2)

            if divergence > 5:
                flag = "MANUAL_REVIEW"
            else:
                flag = "OK"

        validation_records.append(
            {
                "company_id": company_id,
                "metric_type": metric,
                "period_years": period,
                "parsed_value_pct": parsed_value,
                "computed_value_pct": round(computed_value, 2),
                "divergence_pct": divergence,
                "flag": flag,
            }
        )

    validation_df = pd.DataFrame(
        validation_records,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "parsed_value_pct",
            "computed_value_pct",
            "divergence_pct",
            "flag",
        ],
    )

    validation_df.to_csv(
        VALIDATION_FILE,
        index=False
    )

    return validation_df


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 60)
    print("DAY 29 - NLP ANALYSIS TEXT PARSER")
    print("=" * 60)

    # Actual headers are on Excel row 2
    df = pd.read_excel(
        INPUT_FILE,
        header=1
    )

    df = df.dropna(how="all")

    print(f"Input file: {INPUT_FILE}")
    print(f"Input rows: {len(df)}")

    parsed_records = []
    failure_records = []

    for _, row in df.iterrows():

        company_id = row.get("company_id")

        if pd.isna(company_id):
            continue

        company_id = str(company_id).strip()

        for metric in TARGET_FIELDS:

            raw_value = row.get(metric)

            period_years, value_pct = parse_metric(
                raw_value
            )

            if period_years is not None:

                parsed_records.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "period_years": period_years,
                        "value_pct": value_pct,
                    }
                )

            else:

                failure_records.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "raw_value": raw_value,
                        "reason": "Regex pattern did not match",
                    }
                )

    parsed_df = pd.DataFrame(
        parsed_records,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures_df = pd.DataFrame(
        failure_records,
        columns=[
            "company_id",
            "metric_type",
            "raw_value",
            "reason",
        ],
    )

    # Save parsed output
    parsed_df.to_csv(
        PARSED_FILE,
        index=False
    )

    # Save failures
    failures_df.to_csv(
        FAILURES_FILE,
        index=False
    )

    # Cross-validation
    validation_df = validate_cagr(
        parsed_df
    )

    print()
    print("RESULTS")
    print("-" * 60)

    print(
        f"Parsed records      : {len(parsed_df)}"
    )

    print(
        f"Failed records      : {len(failures_df)}"
    )

    print(
        f"Validation records  : {len(validation_df)}"
    )

    if not validation_df.empty:

        manual_review_count = (
            validation_df["flag"]
            .eq("MANUAL_REVIEW")
            .sum()
        )

        ok_count = (
            validation_df["flag"]
            .eq("OK")
            .sum()
        )

        unavailable_count = (
            validation_df["flag"]
            .eq("NO_COMPUTED_VALUE")
            .sum()
        )

        print(
            f"CAGR validation OK  : {ok_count}"
        )

        print(
            f"Manual review       : {manual_review_count}"
        )

        print(
            f"No computed value   : {unavailable_count}"
        )

    print()
    print("OUTPUT FILES")
    print("-" * 60)

    print(PARSED_FILE)
    print(FAILURES_FILE)
    print(VALIDATION_FILE)

    print()
    print("Day 29 parser completed.")


if __name__ == "__main__":
    main()