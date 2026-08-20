from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

CLUSTER_OUTPUT_PATH = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_OUTPUT_PATH = REPORTS_DIR / "elbow_plot.png"


# ============================================================
# CONFIGURATION
# ============================================================

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

N_CLUSTERS = 5
RANDOM_STATE = 42


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """Load financial ratios and sector information from SQLite."""

    with sqlite3.connect(DB_PATH) as conn:

        ratios = pd.read_sql_query(
            """
            SELECT *
            FROM financial_ratios
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

    return ratios, sectors


# ============================================================
# CALCULATE FCF CAGR
# ============================================================

def add_fcf_cagr(df, periods=5):
    """Calculate 5-year FCF CAGR using historical FCF values."""

    result = df.copy()

    result["fcf_year_num"] = pd.to_numeric(
        result["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    result = result.sort_values(
        ["company_id", "fcf_year_num"]
    )

    result["fcf_start"] = (
        result.groupby("company_id")["free_cash_flow_cr"]
        .shift(periods)
    )

    valid = (
        (result["fcf_start"] > 0)
        & (result["free_cash_flow_cr"] > 0)
    )

    result["fcf_cagr_5yr"] = np.nan

    result.loc[valid, "fcf_cagr_5yr"] = (
        (
            result.loc[valid, "free_cash_flow_cr"]
            / result.loc[valid, "fcf_start"]
        )
        ** (1 / periods)
        - 1
    ) * 100

    return result


# ============================================================
# PREPARE LATEST COMPANY DATA
# ============================================================

def prepare_features(ratios, sectors):
    """Prepare one latest-year feature row for each company."""

    ratios = add_fcf_cagr(ratios)

    ratios["year_num"] = pd.to_numeric(
        ratios["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    # Keep only rows with a valid year
    ratios = ratios.dropna(subset=["year_num"]).copy()

    # Latest available year for each company
    ratios = ratios.sort_values(
        ["company_id", "year_num", "id"]
    )

    latest = (
        ratios
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    latest = latest[
        ["company_id"] + FEATURES
    ]

    # Attach sector information
    latest = latest.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
            ]
        ].drop_duplicates("company_id"),
        on="company_id",
        how="left",
    )

    # Convert clustering features to numeric
    for feature in FEATURES:
        latest[feature] = pd.to_numeric(
            latest[feature],
            errors="coerce",
        )

    return latest


# ============================================================
# SECTOR MEDIAN IMPUTATION
# ============================================================

def impute_sector_medians(df):
    """Fill missing feature values using sector medians."""

    result = df.copy()

    for feature in FEATURES:

        sector_median = (
            result
            .groupby("broad_sector")[feature]
            .transform("median")
        )

        result[feature] = result[feature].fillna(
            sector_median
        )

        # Global median fallback if sector median is unavailable
        global_median = result[feature].median()

        result[feature] = result[feature].fillna(
            global_median
        )

    return result


# ============================================================
# ELBOW PLOT
# ============================================================

def generate_elbow_plot(X_scaled):
    """Generate KMeans elbow plot for k=2 through k=10."""

    k_values = range(2, 11)
    inertias = []

    for k in k_values:

        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=10,
        )

        model.fit(X_scaled)

        inertias.append(model.inertia_)

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(figsize=(9, 6))

    plt.plot(
        list(k_values),
        inertias,
        marker="o",
    )

    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")

    plt.xticks(list(k_values))
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        ELBOW_OUTPUT_PATH,
        dpi=150,
    )

    plt.close()

    return dict(zip(k_values, inertias))


# ============================================================
# CLUSTER NAMING
# ============================================================

def assign_cluster_names(cluster_profile):
    """
    Assign reviewed descriptive names to the five KMeans clusters.

    Names were reviewed during Sprint 6 Day 37 using:
    - cluster financial profiles
    - company membership
    - growth characteristics
    - leverage
    - profitability
    - capital efficiency
    """

    return {
        0: "Core Quality Leaders",
        1: "Leveraged Growth / Turnaround",
        2: "High-Quality Compounder",
        3: "High-Efficiency Growth",
        4: "Capital-Efficient Defense Industrials",
    }
# ============================================================
# RUN KMEANS
# ============================================================

def run_clustering(df):
    """Run KMeans clustering and return labels and profiles."""

    X = df[FEATURES].copy()

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    model = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=10,
    )

    cluster_ids = model.fit_predict(X_scaled)

    df = df.copy()

    df["cluster_id"] = cluster_ids

    # Distance from assigned centroid
    distances = model.transform(X_scaled)

    df["distance_from_centroid"] = [
        distances[i, cluster_ids[i]]
        for i in range(len(df))
    ]

    # Cluster profiles using original feature values
    profiles = (
        df
        .groupby("cluster_id")[FEATURES]
        .mean()
    )

    cluster_names = assign_cluster_names(
        profiles
    )

    df["cluster_name"] = df[
        "cluster_id"
    ].map(cluster_names)

    return (
        df,
        profiles,
        model,
        scaler,
    )


# ============================================================
# EXPORT
# ============================================================

def export_results(df):
    """Export cluster labels to CSV."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = df[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].copy()

    output["distance_from_centroid"] = (
        output["distance_from_centroid"].round(6)
    )

    output = output.sort_values(
        ["cluster_id", "company_id"]
    )

    output.to_csv(
        CLUSTER_OUTPUT_PATH,
        index=False,
    )

    return output


# ============================================================
# VALIDATION
# ============================================================

def validate_results(output):
    """Validate that all 92 companies received cluster assignments."""

    if len(output) != 92:
        raise ValueError(
            f"Expected 92 companies, found {len(output)}."
        )

    if output["company_id"].nunique() != 92:
        raise ValueError(
            "Expected 92 unique company IDs."
        )

    if output["cluster_id"].isna().any():
        raise ValueError(
            "Some companies have no cluster assignment."
        )

    cluster_ids = set(
        output["cluster_id"].unique()
    )

    if cluster_ids != {0, 1, 2, 3, 4}:
        raise ValueError(
            f"Expected clusters 0-4, found {cluster_ids}."
        )

    if output["cluster_name"].isna().any():
        raise ValueError(
            "Some companies have no cluster name."
        )

    if output["distance_from_centroid"].isna().any():
        raise ValueError(
            "Some companies have no centroid distance."
        )

    print("Validation PASSED")
    print(f"Companies: {len(output)}")
    print(f"Unique companies: {output['company_id'].nunique()}")
    print(f"Clusters: {sorted(cluster_ids)}")

    print("\nCluster counts:")
    print(
        output["cluster_name"]
        .value_counts()
        .sort_index()
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("SPRINT 6 - DAY 36: KMEANS CLUSTERING")
    print("=" * 70)

    print("\nLoading database...")
    ratios, sectors = load_data()

    print(f"Financial ratio rows: {len(ratios)}")
    print(f"Sector rows: {len(sectors)}")

    print("\nPreparing latest company features...")
    data = prepare_features(
        ratios,
        sectors,
    )

    print(f"Companies prepared: {len(data)}")

    print("\nChecking missing values before imputation:")

    print(
        data[FEATURES]
        .isna()
        .sum()
    )

    print("\nApplying sector median imputation...")

    data = impute_sector_medians(data)

    print("\nMissing values after imputation:")

    print(
        data[FEATURES]
        .isna()
        .sum()
    )

    print("\nScaling features with StandardScaler...")

    X_scaled = StandardScaler().fit_transform(
        data[FEATURES]
    )

    print("\nGenerating elbow plot...")

    inertias = generate_elbow_plot(
        X_scaled
    )

    print("\nElbow inertia values:")

    for k, inertia in inertias.items():
        print(
            f"k={k}: {inertia:.2f}"
        )

    print("\nRunning KMeans with k=5...")

    clustered, profiles, model, scaler = (
        run_clustering(data)
    )

    print("\nCluster profiles:")
    print(
        profiles.round(2)
    )

    print("\nExporting cluster labels...")

    output = export_results(
        clustered
    )

    validate_results(
        output
    )

    print("\nCreated:")
    print(
        CLUSTER_OUTPUT_PATH
    )

    print(
        ELBOW_OUTPUT_PATH
    )

    print("\n" + "=" * 70)
    print("DAY 36 CLUSTERING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()