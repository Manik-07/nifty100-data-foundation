import sys
from pathlib import Path

import streamlit as st
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_home_metrics,
    get_sectors,
    get_valuation,
)


st.title("Nifty 100 Analytics")

st.caption(
    "Market overview, financial quality metrics and sector distribution."
)


# ==========================================================
# Sidebar - Year Selector
# ==========================================================

st.sidebar.header("Dashboard Filters")

selected_year = st.sidebar.selectbox(
    "Financial Year",
    options=list(range(2024, 2018, -1)),
    index=0,
)

st.sidebar.caption(
    "All Home screen metrics update based on the selected year."
)


# ==========================================================
# Load Data
# ==========================================================

df = get_home_metrics(selected_year)


if df.empty:

    st.warning(
        f"No financial data is available for {selected_year}."
    )

    st.stop()


# ==========================================================
# Calculate KPIs
# ==========================================================

average_roe = df["return_on_equity_pct"].mean()

median_de = df["debt_to_equity"].median()

median_revenue_cagr = df["revenue_cagr_5yr"].median()

total_companies = df["company_id"].nunique()

debt_free_companies = df.loc[
    df["debt_to_equity"].fillna(999) == 0,
    "company_id",
].nunique()


# ----------------------------------------------------------
# Median P/E
# ----------------------------------------------------------

pe_values = []

for ticker in df["company_id"].dropna().unique():

    valuation = get_valuation(ticker)

    if valuation.empty:
        continue

    year_data = valuation[
        valuation["year"] == selected_year
    ]

    if not year_data.empty:

        pe = year_data.iloc[-1]["pe_ratio"]

        if pe is not None:
            pe_values.append(pe)


if pe_values:
    import pandas as pd
    median_pe = pd.Series(pe_values).median()
else:
    median_pe = None


# ==========================================================
# KPI Section
# ==========================================================

st.subheader(f"Market Snapshot — {selected_year}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Average ROE",
        f"{average_roe:.2f}%"
        if average_roe == average_roe
        else "N/A",
    )

with col2:
    st.metric(
        "Median P/E",
        f"{median_pe:.2f}x"
        if median_pe is not None
        else "N/A",
    )

with col3:
    st.metric(
        "Median D/E",
        f"{median_de:.2f}"
        if median_de == median_de
        else "N/A",
    )


col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        "Total Companies",
        total_companies,
    )

with col5:
    st.metric(
        "Median Revenue CAGR 5Y",
        f"{median_revenue_cagr:.2f}%"
        if median_revenue_cagr == median_revenue_cagr
        else "N/A",
    )

with col6:
    st.metric(
        "Debt-Free Companies",
        debt_free_companies,
    )


st.divider()


# ==========================================================
# Sector Breakdown
# ==========================================================

st.subheader("Sector Breakdown")

sector_df = get_sectors()

sector_counts = (
    sector_df
    .groupby("broad_sector")["company_id"]
    .nunique()
    .reset_index(name="company_count")
)


fig_sector = px.pie(
    sector_counts,
    names="broad_sector",
    values="company_count",
    hole=0.55,
    title="Companies by Broad Sector",
)

fig_sector.update_layout(
    legend_title_text="Sector"
)

st.plotly_chart(
    fig_sector,
    use_container_width=True,
)


# ==========================================================
# Top 5 Quality Companies
# ==========================================================

st.subheader("Top 5 Companies by Composite Quality Score")

top5 = (
    df[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "composite_quality_score",
        ]
    ]
    .dropna(subset=["composite_quality_score"])
    .sort_values(
        "composite_quality_score",
        ascending=False,
    )
    .head(5)
)


top5 = top5.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "broad_sector": "Sector",
        "return_on_equity_pct": "ROE %",
        "debt_to_equity": "D/E",
        "revenue_cagr_5yr": "Revenue CAGR 5Y %",
        "composite_quality_score": "Quality Score",
    }
)


st.dataframe(
    top5,
    use_container_width=True,
    hide_index=True,
)


st.caption(
    f"Showing financial information available for calendar year {selected_year}."
)