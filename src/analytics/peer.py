import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"


# ==========================================================
# REQUIRED 10 PEER METRICS
# ==========================================================

METRICS = {
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


def get_connection():
    return sqlite3.connect(DB_PATH)


# ==========================================================
# LOAD DATA
# ==========================================================

def load_data():

    conn = get_connection()

    ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn
    )

    peer_groups = pd.read_sql(
        "SELECT * FROM peer_groups",
        conn
    )

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn
    )

    conn.close()

    return ratios, peer_groups, companies


# ==========================================================
# GET LATEST FINANCIAL YEAR
# ==========================================================

def extract_year(value):

    year = pd.Series(
        [str(value)]
    ).str.extract(
        r"(\d{4})"
    )[0].iloc[0]

    if pd.isna(year):
        return None

    return int(year)


def get_latest_ratios(ratios):

    df = ratios.copy()

    df["year_num"] = (
        df["year"].apply(extract_year)
    )

    df = (
        df.sort_values(
            ["company_id", "year_num"]
        )
        .groupby("company_id")
        .tail(1)
        .reset_index(drop=True)
    )

    return df


# ==========================================================
# ADD ROCE
# ROCE currently comes from companies table
# ==========================================================

def add_roce(latest, companies):

    roce = companies[
        [
            "id",
            "roce_percentage"
        ]
    ].copy()

    roce = roce.rename(
        columns={
            "id": "company_id",
            "roce_percentage":
                "return_on_capital_employed_pct"
        }
    )

    latest = latest.merge(
        roce,
        on="company_id",
        how="left"
    )

    return latest


# ==========================================================
# MERGE WITH PEER GROUPS
# ==========================================================

def prepare_peer_data(
    latest,
    peer_groups
):

    peer_groups = peer_groups.copy()

    peer_groups["company_id"] = (
        peer_groups["company_id"]
        .astype(str)
        .str.strip()
    )

    latest["company_id"] = (
        latest["company_id"]
        .astype(str)
        .str.strip()
    )

    peer_data = peer_groups[
        [
            "company_id",
            "peer_group_name",
            "is_benchmark"
        ]
    ].merge(
        latest,
        on="company_id",
        how="left"
    )

    return peer_data


# ==========================================================
# SQL-STYLE PERCENT_RANK
# ==========================================================

def percent_rank(series, inverse=False):

    values = pd.to_numeric(
        series,
        errors="coerce"
    )

    result = pd.Series(
        index=series.index,
        dtype="float64"
    )

    valid = values.notna()
    count = valid.sum()

    if count == 0:
        return result

    if count == 1:
        result.loc[valid] = 1.0
        return result

    ranks = values[valid].rank(
        method="min",
        ascending=True
    )

    percentile = (
        (ranks - 1)
        / (count - 1)
    )

    # Lower D/E = better percentile
    if inverse:
        percentile = 1 - percentile

    result.loc[valid] = percentile

    return result


# ==========================================================
# CALCULATE ALL 10 PEER PERCENTILES
# ==========================================================

def calculate_peer_percentiles(
    peer_data
):

    rows = []

    for peer_group_name, group in (
        peer_data.groupby("peer_group_name")
    ):

        group = group.copy()

        print(
            f"\nProcessing {peer_group_name}: "
            f"{len(group)} companies"
        )

        for metric_name, column in METRICS.items():

            if column not in group.columns:

                print(
                    f"WARNING: {column} missing"
                )

                continue

            inverse = (
                column == "debt_to_equity"
            )

            percentiles = percent_rank(
                group[column],
                inverse=inverse
            )

            for index, row in group.iterrows():

                rows.append(
                    {
                        "company_id":
                            row["company_id"],

                        "peer_group_name":
                            peer_group_name,

                        "metric":
                            metric_name,

                        "value":
                            row[column],

                        "percentile_rank":
                            percentiles.loc[index],

                        "year":
                            row["year"],
                    }
                )

    return pd.DataFrame(rows)


# ==========================================================
# SAVE TO SQLITE
# ==========================================================

def save_to_database(df):

    conn = get_connection()

    df.to_sql(
        "peer_percentiles",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print(
        "\nSaved to table: peer_percentiles"
    )


# ==========================================================
# COMPANY LOOKUP
# ==========================================================

def get_peer_group(company_id):

    conn = get_connection()

    peer_groups = pd.read_sql(
        "SELECT * FROM peer_groups",
        conn
    )

    conn.close()

    match = peer_groups[
        peer_groups["company_id"]
        .astype(str)
        .str.strip()
        == str(company_id).strip()
    ]

    if match.empty:
        return "No peer group assigned"

    return match.iloc[0][
        "peer_group_name"
    ]


# ==========================================================
# VALIDATION
# ==========================================================

def validate_results(df):

    print("\n" + "=" * 60)
    print("DAY 18 VALIDATION")
    print("=" * 60)

    print(
        "Peer groups:",
        df["peer_group_name"].nunique()
    )

    print(
        "Companies:",
        df["company_id"].nunique()
    )

    print(
        "Metrics:",
        df["metric"].nunique()
    )

    print(
        "Rows:",
        len(df)
    )

    print(
        "Percentile minimum:",
        df["percentile_rank"].min()
    )

    print(
        "Percentile maximum:",
        df["percentile_rank"].max()
    )

    # ----------------------------------------------
    # IT SERVICES ROE CHECK
    # ----------------------------------------------

    check = df[
        (
            df["peer_group_name"]
            == "IT Services"
        )
        &
        (
            df["metric"] == "ROE"
        )
    ].sort_values(
        "percentile_rank",
        ascending=False
    )

    print("\nIT SERVICES — ROE")
    print("-" * 60)

    print(
        check[
            [
                "company_id",
                "value",
                "percentile_rank"
            ]
        ].to_string(index=False)
    )

    # ----------------------------------------------
    # FMCG ROE CHECK
    # ----------------------------------------------

    check = df[
        (
            df["peer_group_name"]
            == "FMCG"
        )
        &
        (
            df["metric"] == "ROE"
        )
    ].sort_values(
        "percentile_rank",
        ascending=False
    )

    print("\nFMCG — ROE")
    print("-" * 60)

    print(
        check[
            [
                "company_id",
                "value",
                "percentile_rank"
            ]
        ].to_string(index=False)
    )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("DAY 18 - PEER PERCENTILE ENGINE")
    print("=" * 60)

    ratios, peer_groups, companies = (
        load_data()
    )

    print(
        "\nFinancial ratio rows:",
        len(ratios)
    )

    print(
        "Peer group assignments:",
        len(peer_groups)
    )

    print(
        "Peer groups:",
        peer_groups[
            "peer_group_name"
        ].nunique()
    )

    # Latest record only
    latest = get_latest_ratios(
        ratios
    )

    print(
        "Latest companies:",
        latest[
            "company_id"
        ].nunique()
    )

    # Add ROCE
    latest = add_roce(
        latest,
        companies
    )

    # Keep assigned peer companies
    peer_data = prepare_peer_data(
        latest,
        peer_groups
    )

    print(
        "Companies assigned to peers:",
        peer_data[
            "company_id"
        ].nunique()
    )

    # Calculate rankings
    percentiles = (
        calculate_peer_percentiles(
            peer_data
        )
    )

    # Save database
    save_to_database(
        percentiles
    )

    # Validation
    validate_results(
        percentiles
    )

    print("\n" + "=" * 60)
    print("DAY 18 COMPLETE")
    print("=" * 60)