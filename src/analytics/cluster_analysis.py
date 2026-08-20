from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "db" / "nifty100.db"

OUTPUT_DIR = ROOT / "output"
REPORTS_DIR = ROOT / "reports"

CLUSTER_LABELS_PATH = OUTPUT_DIR / "cluster_labels.csv"

CLUSTER_PROFILE_PATH = OUTPUT_DIR / "cluster_profiles.csv"
PORTFOLIO_STATS_PATH = OUTPUT_DIR / "portfolio_stats.csv"
OUTLIER_REPORT_PATH = OUTPUT_DIR / "outlier_report.csv"

CORRELATION_PATH = OUTPUT_DIR / "kpi_correlation.csv"
HEATMAP_PATH = REPORTS_DIR / "correlation_heatmap.png"


# ============================================================
# 10 PROJECT KPIs
# ============================================================

KPI_COLUMNS = {
    "ROE": "return_on_equity_pct",
    "ROCE": "return_on_capital_employed_pct",
    "Net Profit Margin": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "PAT CAGR 5yr": "pat_cagr_5yr",
    "Revenue CAGR 5yr": "revenue_cagr_5yr",
    "EPS CAGR 5yr": "eps_cagr_5yr",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
}


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    conn = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql_query(
        """
        SELECT *
        FROM financial_ratios
        """,
        conn,
    )

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            roce_percentage
        FROM companies
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector,
            sub_sector,
            market_cap_category
        FROM sectors
        """,
        conn,
    )

    conn.close()

    companies["return_on_capital_employed_pct"] = (
        pd.to_numeric(
            companies["roce_percentage"],
            errors="coerce",
        )
    )

    companies = companies.drop(
        columns=["roce_percentage"]
    )

    return ratios, companies, sectors


# ============================================================
# LATEST YEAR
# ============================================================

def extract_year(value):

    value = str(value)

    match = pd.Series([value]).str.extract(
        r"(\d{4})"
    )[0].iloc[0]

    if pd.isna(match):
        return np.nan

    return int(match)


def get_latest_data(ratios, companies, sectors):

    df = ratios.copy()

    df["year_num"] = df["year"].apply(
        extract_year
    )

    df = df.dropna(
        subset=["year_num"]
    )

    df["year_num"] = df["year_num"].astype(int)

    df = df.sort_values(
        ["company_id", "year_num", "id"]
    )

    latest = (
        df.groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    # Add ROCE from company master
    latest = latest.merge(
        companies,
        on="company_id",
        how="left",
    )

    # Add sector
    latest = latest.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
                "sub_sector",
                "market_cap_category",
            ]
        ].drop_duplicates(
            "company_id"
        ),
        on="company_id",
        how="left",
    )

    return latest


# ============================================================
# CLEAN NUMERIC KPIs
# ============================================================

def clean_kpis(df):

    result = df.copy()

    for column in KPI_COLUMNS.values():

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    return result


# ============================================================
# CLUSTER PROFILES
# ============================================================

def create_cluster_profiles(df):

    if not CLUSTER_LABELS_PATH.exists():

        raise FileNotFoundError(
            "cluster_labels.csv not found. "
            "Run clustering.py first."
        )

    labels = pd.read_csv(
        CLUSTER_LABELS_PATH
    )

    labels["company_id"] = (
        labels["company_id"]
        .astype(str)
        .str.strip()
    )

    result = df.merge(
        labels[
            [
                "company_id",
                "cluster_id",
                "cluster_name",
                "distance_from_centroid",
            ]
        ],
        on="company_id",
        how="inner",
    )

    profile_rows = []

    for cluster_id, group in result.groupby(
        "cluster_id"
    ):

        for kpi_name, column in KPI_COLUMNS.items():

            values = pd.to_numeric(
                group[column],
                errors="coerce",
            ).dropna()

            if len(values) == 0:
                continue

            profile_rows.append(
                {
                    "cluster_id": cluster_id,
                    "cluster_name": group[
                        "cluster_name"
                    ].iloc[0],
                    "kpi": kpi_name,
                    "mean": values.mean(),
                    "median": values.median(),
                    "company_count": len(group),
                }
            )

    profiles = pd.DataFrame(
        profile_rows
    )

    return result, profiles


# ============================================================
# CLUSTER COMPANY MEMBERSHIP
# ============================================================

def print_cluster_members(result):

    print("\n" + "=" * 70)
    print("CLUSTER MEMBERS")
    print("=" * 70)

    for cluster_id, group in result.groupby(
        "cluster_id"
    ):

        print(
            f"\nCluster {cluster_id}: "
            f"{group['cluster_name'].iloc[0]}"
        )

        print(
            "Companies:",
            ", ".join(
                group["company_id"]
                .astype(str)
                .sort_values()
                .tolist()
            ),
        )


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

def create_portfolio_stats(df):

    rows = []

    for kpi_name, column in KPI_COLUMNS.items():

        values = pd.to_numeric(
            df[column],
            errors="coerce",
        ).dropna()

        if len(values) == 0:
            continue

        rows.append(
            {
                "kpi": kpi_name,
                "p10": values.quantile(0.10),
                "p25": values.quantile(0.25),
                "p50": values.quantile(0.50),
                "p75": values.quantile(0.75),
                "p90": values.quantile(0.90),
                "mean": values.mean(),
                "std": values.std(),
                "count": len(values),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# CORRELATION MATRIX
# ============================================================

def create_correlation_matrix(df):

    correlation_data = pd.DataFrame()

    for kpi_name, column in KPI_COLUMNS.items():

        correlation_data[kpi_name] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    correlation = correlation_data.corr(
        method="pearson"
    )

    return correlation


# ============================================================
# CORRELATION HEATMAP
# ============================================================

def create_heatmap(correlation):

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(12, 10)
    )

    image = plt.imshow(
        correlation.values,
        aspect="auto",
    )

    plt.colorbar(
        image,
        label="Pearson Correlation",
    )

    plt.xticks(
        range(len(correlation.columns)),
        correlation.columns,
        rotation=45,
        ha="right",
    )

    plt.yticks(
        range(len(correlation.index)),
        correlation.index,
    )

    plt.title(
        "Pearson Correlation Heatmap — 10 KPIs"
    )

    # Add values to cells
    for i in range(
        len(correlation.index)
    ):

        for j in range(
            len(correlation.columns)
        ):

            value = correlation.iloc[i, j]

            if pd.notna(value):

                plt.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                )

    plt.tight_layout()

    plt.savefig(
        HEATMAP_PATH,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


# ============================================================
# SECTOR OUTLIER DETECTION
# ============================================================

def create_outlier_report(df):

    rows = []

    for sector, sector_group in df.groupby(
        "broad_sector",
        dropna=False,
    ):

        for kpi_name, column in KPI_COLUMNS.items():

            values = pd.to_numeric(
                sector_group[column],
                errors="coerce",
            )

            mean = values.mean()
            std = values.std()

            # Cannot calculate meaningful Z-score
            # if there is only one value or zero variance.
            if pd.isna(std) or std == 0:
                continue

            z_scores = (
                values - mean
            ) / std

            for index, z_score in z_scores.items():

                if pd.isna(z_score):
                    continue

                if abs(z_score) > 3:

                    rows.append(
                        {
                            "company_id":
                                sector_group.loc[
                                    index,
                                    "company_id",
                                ],
                            "broad_sector":
                                sector,
                            "kpi":
                                kpi_name,
                            "value":
                                values.loc[index],
                            "sector_mean":
                                mean,
                            "sector_std":
                                std,
                            "z_score":
                                z_score,
                            "absolute_z_score":
                                abs(z_score),
                            "outlier":
                                True,
                        }
                    )

    report = pd.DataFrame(
        rows
    )

    if not report.empty:

        report = report.sort_values(
            "absolute_z_score",
            ascending=False,
        )

    return report


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(
    profiles,
    portfolio_stats,
    correlation,
    outliers,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    profiles.to_csv(
        CLUSTER_PROFILE_PATH,
        index=False,
    )

    portfolio_stats.to_csv(
        PORTFOLIO_STATS_PATH,
        index=False,
    )

    correlation.to_csv(
        CORRELATION_PATH
    )

    outliers.to_csv(
        OUTLIER_REPORT_PATH,
        index=False,
    )


# ============================================================
# VALIDATION
# ============================================================

def validate(result, profiles, portfolio_stats):

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(
        f"Companies analysed: "
        f"{result['company_id'].nunique()}"
    )

    print(
        f"Rows analysed: "
        f"{len(result)}"
    )

    print(
        f"Clusters analysed: "
        f"{result['cluster_id'].nunique()}"
    )

    print(
        f"Cluster profile rows: "
        f"{len(profiles)}"
    )

    print(
        f"Portfolio statistics rows: "
        f"{len(portfolio_stats)}"
    )

    if result["company_id"].nunique() != 92:

        raise ValueError(
            "Expected 92 companies."
        )

    if result["cluster_id"].nunique() != 5:

        raise ValueError(
            "Expected 5 clusters."
        )

    if len(portfolio_stats) != 10:

        raise ValueError(
            "Expected statistics for 10 KPIs."
        )

    print("\nValidation PASSED")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SPRINT 6 - DAY 37: CLUSTER PROFILING")
    print("=" * 70)

    print("\nLoading database...")

    ratios, companies, sectors = load_data()

    print(
        f"Financial ratio rows: {len(ratios)}"
    )

    print(
        f"Company master rows: {len(companies)}"
    )

    print(
        f"Sector rows: {len(sectors)}"
    )

    print("\nExtracting latest year...")

    latest = get_latest_data(
        ratios,
        companies,
        sectors,
    )

    print(
        f"Latest company rows: "
        f"{len(latest)}"
    )

    latest = clean_kpis(
        latest
    )

    print("\nCreating cluster profiles...")

    result, profiles = (
        create_cluster_profiles(
            latest
        )
    )

    print_cluster_members(
        result
    )

    print("\nCreating portfolio statistics...")

    portfolio_stats = (
        create_portfolio_stats(
            result
        )
    )

    print("\nPortfolio statistics:")

    print(
        portfolio_stats.round(2).to_string(
            index=False
        )
    )

    print("\nCreating Pearson correlation matrix...")

    correlation = (
        create_correlation_matrix(
            result
        )
    )

    print(
        correlation.round(2).to_string()
    )

    print("\nGenerating correlation heatmap...")

    create_heatmap(
        correlation
    )

    print("\nDetecting sector outliers...")

    outliers = (
        create_outlier_report(
            result
        )
    )

    print(
        f"Outliers detected: "
        f"{len(outliers)}"
    )

    if not outliers.empty:

        print("\nTop outliers:")

        print(
            outliers.head(20).round(2).to_string(
                index=False
            )
        )

    else:

        print(
            "No |Z| > 3 outliers detected."
        )

    print("\nSaving outputs...")

    save_outputs(
        profiles,
        portfolio_stats,
        correlation,
        outliers,
    )

    validate(
        result,
        profiles,
        portfolio_stats,
    )

    print("\nCreated:")

    print(
        CLUSTER_PROFILE_PATH
    )

    print(
        PORTFOLIO_STATS_PATH
    )

    print(
        CORRELATION_PATH
    )

    print(
        OUTLIER_REPORT_PATH
    )

    print(
        HEATMAP_PATH
    )

    print("\n" + "=" * 70)
    print("DAY 37 ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()