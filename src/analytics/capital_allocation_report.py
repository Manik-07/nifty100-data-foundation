"""
capital_allocation_report.py

Sprint 5 - Day 32
Capital Allocation Report

Tasks:
1. Verify capital_allocation.csv coverage
2. Generate latest-year pattern distribution
3. Detect year-over-year capital allocation pattern changes
"""

from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT / "output" / "capital_allocation.csv"

DISTRIBUTION_FILE = (
    ROOT / "output" / "capital_allocation_distribution.csv"
)

CHANGES_FILE = (
    ROOT / "output" / "pattern_changes.csv"
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Capital allocation file not found: {INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

required_columns = [
    "company_id",
    "year",
    "cfo_sign",
    "cfi_sign",
    "cff_sign",
    "pattern_label",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ---------------------------------------------------------
# CLEAN DATA
# ---------------------------------------------------------

df["company_id"] = df["company_id"].astype(str).str.strip()
df["year"] = df["year"].astype(str).str.strip()
df["pattern_label"] = (
    df["pattern_label"]
    .astype(str)
    .str.strip()
)

df = df.sort_values(
    ["company_id", "year"]
).reset_index(drop=True)


# ---------------------------------------------------------
# BASIC VERIFICATION
# ---------------------------------------------------------

company_count = df["company_id"].nunique()
row_count = len(df)
pattern_count = df["pattern_label"].nunique()

expected_patterns = {
    "Reinvestor",
    "Mixed",
    "Growth Funded by Debt",
    "Liquidating Assets",
    "Distress Signal",
    "Unknown",
    "Pre-Revenue",
    "Cash Accumulator",
}

actual_patterns = set(df["pattern_label"].unique())

missing_patterns = expected_patterns - actual_patterns


print("=" * 60)
print("DAY 32 - CAPITAL ALLOCATION REPORT")
print("=" * 60)

print(f"\nInput file           : {INPUT_FILE}")
print(f"Total rows           : {row_count}")
print(f"Companies            : {company_count}")
print(f"Patterns found       : {pattern_count}")

if company_count == 92:
    print("PASS - All 92 companies are present")
else:
    print(
        f"WARNING - Expected 92 companies, found {company_count}"
    )

if missing_patterns:
    print(
        f"WARNING - Missing patterns: {sorted(missing_patterns)}"
    )
else:
    print("PASS - All 8 capital allocation patterns present")


# ---------------------------------------------------------
# COMPANY COVERAGE
# ---------------------------------------------------------

company_year_summary = (
    df.groupby("company_id")
    .agg(
        year_count=("year", "nunique"),
        first_year=("year", "min"),
        last_year=("year", "max"),
    )
    .reset_index()
)

print("\nCOMPANY YEAR COVERAGE")
print("-" * 60)

print(
    company_year_summary["year_count"]
    .describe()
    .to_string()
)

incomplete_companies = company_year_summary[
    company_year_summary["year_count"] < 3
]

if len(incomplete_companies) > 0:
    print(
        "\nCompanies with fewer than 3 years:"
    )
    print(
        incomplete_companies.to_string(index=False)
    )
else:
    print(
        "\nPASS - Every company has at least 3 years"
    )


# ---------------------------------------------------------
# LATEST YEAR PER COMPANY
# ---------------------------------------------------------

latest_rows = (
    df.sort_values(["company_id", "year"])
    .groupby("company_id", as_index=False)
    .tail(1)
    .copy()
)

latest_distribution = (
    latest_rows["pattern_label"]
    .value_counts()
    .rename_axis("pattern_label")
    .reset_index(name="company_count")
)

latest_distribution["percentage"] = (
    latest_distribution["company_count"]
    / company_count
    * 100
).round(2)

latest_distribution = latest_distribution.sort_values(
    "company_count",
    ascending=False
).reset_index(drop=True)


# ---------------------------------------------------------
# SAVE DISTRIBUTION
# ---------------------------------------------------------

latest_distribution.to_csv(
    DISTRIBUTION_FILE,
    index=False
)


print("\nLATEST-YEAR PATTERN DISTRIBUTION")
print("-" * 60)

print(
    latest_distribution.to_string(index=False)
)

print(
    f"\nSaved: {DISTRIBUTION_FILE}"
)


# ---------------------------------------------------------
# YEAR-OVER-YEAR PATTERN CHANGES
# ---------------------------------------------------------

work = df[
    [
        "company_id",
        "year",
        "pattern_label",
    ]
].copy()

work["previous_year"] = (
    work.groupby("company_id")["year"]
    .shift(1)
)

work["previous_pattern"] = (
    work.groupby("company_id")["pattern_label"]
    .shift(1)
)

changes = work[
    work["previous_pattern"].notna()
    & (
        work["pattern_label"]
        != work["previous_pattern"]
    )
].copy()


# ---------------------------------------------------------
# CHANGE REPORT
# ---------------------------------------------------------

changes["change"] = (
    changes["previous_pattern"]
    + " -> "
    + changes["pattern_label"]
)

changes = changes.rename(
    columns={
        "year": "current_year",
        "pattern_label": "current_pattern",
    }
)

changes = changes[
    [
        "company_id",
        "previous_year",
        "current_year",
        "previous_pattern",
        "current_pattern",
        "change",
    ]
]


# ---------------------------------------------------------
# SAVE CHANGES
# ---------------------------------------------------------

changes.to_csv(
    CHANGES_FILE,
    index=False
)


print("\nPATTERN CHANGES")
print("-" * 60)

print(
    f"Total year-over-year changes : {len(changes)}"
)

print(
    f"Companies with changes       : "
    f"{changes['company_id'].nunique()}"
)

print(
    f"\nSaved: {CHANGES_FILE}"
)


# ---------------------------------------------------------
# CHANGE SUMMARY
# ---------------------------------------------------------

if not changes.empty:

    change_summary = (
        changes["change"]
        .value_counts()
        .rename_axis("change")
        .reset_index(name="count")
    )

    print("\nMOST COMMON PATTERN CHANGES")
    print("-" * 60)

    print(
        change_summary.head(20).to_string(index=False)
    )


# ---------------------------------------------------------
# FINAL STATUS
# ---------------------------------------------------------

print("\n" + "=" * 60)

if company_count == 92 and not missing_patterns:
    print("DAY 32 VERIFICATION: PASS")
else:
    print("DAY 32 VERIFICATION: REVIEW REQUIRED")

print("=" * 60)