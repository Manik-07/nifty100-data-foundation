import os
import re
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ==========================================================
# CONFIGURATION
# ==========================================================

DB_PATH = "db/nifty100.db"
OUTPUT_DIR = "reports/radar_charts"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ==========================================================
# CREATE OUTPUT DIRECTORY
# ==========================================================

def create_output_directory():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


# ==========================================================
# LOAD FINANCIAL DATA + ROCE
# ==========================================================

def load_data():

    conn = get_connection()

    ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn
    )

    companies = pd.read_sql(
        """
        SELECT
            id AS company_id,
            roce_percentage
        FROM companies
        """,
        conn
    )

    conn.close()

    # Rename ROCE column
    companies = companies.rename(
        columns={
            "roce_percentage":
                "return_on_capital_employed_pct"
        }
    )

    # Clean IDs before merge
    ratios["company_id"] = (
        ratios["company_id"]
        .astype(str)
        .str.strip()
    )

    companies["company_id"] = (
        companies["company_id"]
        .astype(str)
        .str.strip()
    )

    # Merge ROCE into financial ratios
    ratios = ratios.merge(
        companies,
        on="company_id",
        how="left"
    )

    return ratios


# ==========================================================
# LOAD PEER GROUPS
# ==========================================================

def load_peer_groups():

    conn = get_connection()

    peer_df = pd.read_sql(
        "SELECT * FROM peer_groups",
        conn
    )

    conn.close()

    peer_df["company_id"] = (
        peer_df["company_id"]
        .astype(str)
        .str.strip()
    )

    peer_df["peer_group_name"] = (
        peer_df["peer_group_name"]
        .astype(str)
        .str.strip()
    )

    peer_df["is_benchmark"] = pd.to_numeric(
        peer_df["is_benchmark"],
        errors="coerce"
    ).fillna(0).astype(int)

    return peer_df[
        [
            "company_id",
            "peer_group_name",
            "is_benchmark"
        ]
    ]


# ==========================================================
# EXTRACT YEAR
# ==========================================================

def extract_year(value):

    match = re.search(
        r"\d{4}",
        str(value)
    )

    if match:
        return int(match.group())

    return None


# ==========================================================
# GET LATEST COMPANY DATA
# ==========================================================

def get_latest_company_data(df):

    df = df.copy()

    df["year_num"] = (
        df["year"]
        .apply(extract_year)
    )

    df = df[
        df["year_num"].notna()
    ]

    latest = (
        df
        .sort_values(
            [
                "company_id",
                "year_num"
            ]
        )
        .groupby(
            "company_id",
            as_index=False
        )
        .tail(1)
        .reset_index(drop=True)
    )

    return latest


# ==========================================================
# NORMALIZE RADAR METRICS
#
# P10/P90 winsorisation
# Then scale metrics to 0-100.
#
# D/E is inverse because lower leverage is better.
# ==========================================================

def normalize_radar_metrics(df):

    df = df.copy()

    metrics = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "composite_quality_score"
    ]

    for metric in metrics:

        if metric not in df.columns:

            print(
                f"WARNING: Missing radar metric: {metric}"
            )

            df[f"{metric}_score"] = 50.0

            continue

        values = pd.to_numeric(
            df[metric],
            errors="coerce"
        )

        # ----------------------------------------------
        # Missing values
        # ----------------------------------------------

        median = values.median()

        if pd.isna(median):
            median = 0

        values = values.fillna(
            median
        )

        # ----------------------------------------------
        # P10 / P90 Winsorisation
        # ----------------------------------------------

        lower = values.quantile(
            0.10
        )

        upper = values.quantile(
            0.90
        )

        values = values.clip(
            lower,
            upper
        )

        # ----------------------------------------------
        # Scale to 0-100
        # ----------------------------------------------

        if (
            pd.notna(lower)
            and pd.notna(upper)
            and upper != lower
        ):

            normalized = (
                (
                    values - lower
                )
                /
                (
                    upper - lower
                )
            ) * 100

        else:

            normalized = pd.Series(
                50.0,
                index=df.index,
                dtype=float
            )

        # ----------------------------------------------
        # Lower D/E is better
        # ----------------------------------------------

        if metric == "debt_to_equity":

            normalized = (
                100 - normalized
            )

        df[
            f"{metric}_score"
        ] = normalized.clip(
            0,
            100
        ).round(2)

    return df


# ==========================================================
# RADAR SCORE COLUMNS
# ==========================================================

def get_score_columns():

    return [
        "return_on_equity_pct_score",
        "return_on_capital_employed_pct_score",
        "net_profit_margin_pct_score",
        "debt_to_equity_score",
        "free_cash_flow_cr_score",
        "pat_cagr_5yr_score",
        "revenue_cagr_5yr_score",
        "composite_quality_score_score"
    ]


# ==========================================================
# RADAR LABELS
# ==========================================================

def get_radar_labels():

    return [
        "ROE",
        "ROCE",
        "Net Profit\nMargin",
        "Debt / Equity",
        "Free Cash\nFlow",
        "PAT CAGR\n5Y",
        "Revenue CAGR\n5Y",
        "Composite\nScore"
    ]


# ==========================================================
# CALCULATE PEER GROUP AVERAGES
# ==========================================================

def calculate_peer_averages(df):

    score_columns = (
        get_score_columns()
    )

    peer_averages = (
        df[
            df[
                "peer_group_name"
            ].notna()
        ]
        .groupby(
            "peer_group_name"
        )[score_columns]
        .mean()
        .reset_index()
    )

    return peer_averages

# ==========================================================
# STANDALONE CHART FOR COMPANIES WITHOUT PEER GROUP
# ==========================================================

def generate_standalone_chart(
    row,
    overall_average
):

    # Composite Score is used as the single metric
    metric_column = "composite_quality_score_score"
    metric_label = "Composite Quality Score"

    company_value = row[metric_column]
    nifty_average = overall_average[metric_column]

    if pd.isna(company_value):
        company_value = 50.0

    if pd.isna(nifty_average):
        nifty_average = 50.0

    labels = [
        row["company_id"],
        "Nifty 100 Average"
    ]

    values = [
        float(company_value),
        float(nifty_average)
    ]

    fig, ax = plt.subplots(
        figsize=(7, 6)
    )

    bars = ax.bar(
        labels,
        values
    )

    ax.set_ylim(0, 100)

    ax.set_ylabel(
        "Normalized Score (0-100)"
    )

    ax.set_title(
        f'{row["company_id"]} - {metric_label}\n'
        f'Nifty 100 Comparison | {row["year"]}',
        fontsize=13
    )

    # Add values above bars
    for bar, value in zip(
        bars,
        values
    ):

        ax.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{value:.1f}",
            ha="center",
            fontsize=10
        )

    output_file = os.path.join(
        OUTPUT_DIR,
        f'{row["company_id"]}_radar.png'
    )

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    return output_file


# ==========================================================
# GENERATE RADAR CHART
# ==========================================================

def generate_radar_chart(
    row,
    peer_averages,
    overall_average
):

    labels = get_radar_labels()

    score_columns = (
        get_score_columns()
    )

    # ----------------------------------------------
    # Company values
    # ----------------------------------------------

    company_values = []

    for column in score_columns:

        value = row[column]

        if pd.isna(value):
            value = 50.0

        company_values.append(
            float(value)
        )

    # ----------------------------------------------
    # Comparison values
    # ----------------------------------------------

    peer_group = row.get(
        "peer_group_name"
    )

    if pd.notna(peer_group):

        peer_match = (
            peer_averages[
                peer_averages[
                    "peer_group_name"
                ]
                == peer_group
            ]
        )

        if not peer_match.empty:

            comparison_values = (
                peer_match
                .iloc[0][score_columns]
                .astype(float)
                .tolist()
            )

            comparison_label = (
                f"{peer_group} Average"
            )

        else:

            comparison_values = (
                overall_average[
                    score_columns
                ]
                .astype(float)
                .tolist()
            )

            comparison_label = (
                "Nifty 100 Average"
            )

    else:

        comparison_values = (
            overall_average[
                score_columns
            ]
            .astype(float)
            .tolist()
        )

        comparison_label = (
            "Nifty 100 Average"
        )

    # ----------------------------------------------
    # Close polygons
    # ----------------------------------------------

    company_values = (
        company_values
        + company_values[:1]
    )

    comparison_values = (
        comparison_values
        + comparison_values[:1]
    )

    # ----------------------------------------------
    # Angles
    # ----------------------------------------------

    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False
    ).tolist()

    angles = (
        angles
        + angles[:1]
    )

    # ----------------------------------------------
    # Create polar chart
    # ----------------------------------------------

    fig, ax = plt.subplots(
        figsize=(9, 9),
        subplot_kw={
            "polar": True
        }
    )

    # ----------------------------------------------
    # Company polygon
    # ----------------------------------------------

    ax.plot(
        angles,
        company_values,
        linewidth=2,
        label=row["company_id"]
    )

    ax.fill(
        angles,
        company_values,
        alpha=0.20
    )

    # ----------------------------------------------
    # Peer/Nifty comparison
    # ----------------------------------------------

    ax.plot(
        angles,
        comparison_values,
        linewidth=2,
        linestyle="--",
        label=comparison_label
    )

    # ----------------------------------------------
    # Axis labels
    # ----------------------------------------------

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        labels,
        fontsize=9
    )

    ax.set_ylim(
        0,
        100
    )

    ax.set_yticks(
        [
            20,
            40,
            60,
            80,
            100
        ]
    )

    ax.set_yticklabels(
        [
            "20",
            "40",
            "60",
            "80",
            "100"
        ],
        fontsize=8
    )

    # ----------------------------------------------
    # Title
    # ----------------------------------------------

    if pd.notna(peer_group):

        title = (
            f'{row["company_id"]} Radar Chart\n'
            f'{peer_group} | {row["year"]}'
        )

    else:

        title = (
            f'{row["company_id"]} Radar Chart\n'
            f'Nifty 100 Comparison | {row["year"]}'
        )

    ax.set_title(
        title,
        fontsize=14,
        pad=30
    )

    # ----------------------------------------------
    # Legend
    # ----------------------------------------------

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(
            1.35,
            1.15
        )
    )

    # ----------------------------------------------
    # Save
    # ----------------------------------------------

    output_file = os.path.join(
        OUTPUT_DIR,
        f'{row["company_id"]}_radar.png'
    )

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    return output_file


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("DAY 19 - RADAR CHART ENGINE")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Output directory
    # --------------------------------------------------

    create_output_directory()

    # --------------------------------------------------
    # 2. Load financial data
    # --------------------------------------------------

    ratios = load_data()

    print(
        "\nFinancial ratio rows:",
        len(ratios)
    )

    print(
        "Companies:",
        ratios[
            "company_id"
        ].nunique()
    )

    # --------------------------------------------------
    # 3. Latest record
    # --------------------------------------------------

    latest = (
        get_latest_company_data(
            ratios
        )
    )

    print(
        "\nLatest company records:",
        len(latest)
    )

    # --------------------------------------------------
    # 4. Check ROCE
    # --------------------------------------------------

    print(
        "Companies with ROCE:",
        latest[
            "return_on_capital_employed_pct"
        ].notna().sum()
    )

    # --------------------------------------------------
    # 5. Normalize 8 radar metrics
    # --------------------------------------------------

    latest = (
        normalize_radar_metrics(
            latest
        )
    )

    print(
        "\nRadar metrics normalized."
    )

    print(
        latest[
            [
                "company_id",
                "return_on_equity_pct_score",
                "return_on_capital_employed_pct_score",
                "net_profit_margin_pct_score",
                "debt_to_equity_score",
                "free_cash_flow_cr_score",
                "pat_cagr_5yr_score",
                "revenue_cagr_5yr_score",
                "composite_quality_score_score"
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------
    # 6. Load peer groups
    # --------------------------------------------------

    peer_groups = (
        load_peer_groups()
    )

    print(
        "\nPeer group assignments:",
        len(peer_groups)
    )

    print(
        "Unique peer groups:",
        peer_groups[
            "peer_group_name"
        ].nunique()
    )

    # --------------------------------------------------
    # 7. Merge peer groups
    # --------------------------------------------------

    latest = latest.merge(
        peer_groups,
        on="company_id",
        how="left"
    )

    assigned = (
        latest[
            "peer_group_name"
        ].notna().sum()
    )

    unassigned = (
        latest[
            "peer_group_name"
        ].isna().sum()
    )

    print(
        "\nCompanies with peer groups:",
        assigned
    )

    print(
        "Companies without peer groups:",
        unassigned
    )

    print(
        "Unique mapped peer groups:",
        latest[
            "peer_group_name"
        ].nunique()
    )

    # --------------------------------------------------
    # 8. Peer group averages
    # --------------------------------------------------

    peer_averages = (
        calculate_peer_averages(
            latest
        )
    )

    print(
        "\nPeer groups calculated:",
        len(peer_averages)
    )

    # --------------------------------------------------
    # 9. Overall Nifty 100 average
    # --------------------------------------------------

    score_columns = (
        get_score_columns()
    )

    overall_average = (
        latest[
            score_columns
        ]
        .mean()
    )

    # --------------------------------------------------
    # 10. Generate charts
    # --------------------------------------------------

    print(
        "\nGenerating radar charts..."
    )

    generated_count = 0
    failed_companies = []

    for _, company_row in latest.iterrows():

        try:

            # Company belongs to one of the 11 peer groups
            if pd.notna(
                company_row["peer_group_name"]
            ):

                generate_radar_chart(
                    company_row,
                    peer_averages,
                    overall_average
                )

            # No peer group assigned
            else:

                generate_standalone_chart(
                    company_row,
                    overall_average
                )

            generated_count += 1

        except Exception as error:

            failed_companies.append(
                company_row["company_id"]
            )

            print(
                "FAILED:",
                company_row["company_id"],
                "-",
                error
            )

    # --------------------------------------------------
    # 11. FINAL VALIDATION
    # --------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "DAY 19 VALIDATION"
    )

    print(
        "=" * 60
    )

    print(
        "Companies:",
        latest[
            "company_id"
        ].nunique()
    )

    print(
        "Peer groups:",
        latest[
            "peer_group_name"
        ].nunique()
    )

    print(
        "Companies with peer group:",
        assigned
    )

    print(
        "Companies without peer group:",
        unassigned
    )

    print(
        "Radar metrics:",
        len(score_columns)
    )

    print(
        "Charts generated:",
        generated_count
    )

    print(
        "Failed charts:",
        len(failed_companies)
    )

    if failed_companies:

        print(
            "Failed companies:",
            failed_companies
        )

    print(
        "Output directory:",
        OUTPUT_DIR
    )

    print(
        "\n" + "=" * 60
    )

    if (
        generated_count
        == latest[
            "company_id"
        ].nunique()
    ):

        print(
            "DAY 19 RADAR GENERATION SUCCESSFUL"
        )

    else:

        print(
            "DAY 19 COMPLETED WITH ERRORS"
        )

    print(
        "=" * 60
    )