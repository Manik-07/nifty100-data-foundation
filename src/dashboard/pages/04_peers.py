import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import get_peer_metrics


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("👥 Peer Comparison")

st.caption(
    "Compare a company against its peer group using "
    "profitability, growth, leverage and valuation metrics."
)


# ---------------------------------------------------------
# Peer Groups
# ---------------------------------------------------------

PEER_GROUPS = [
    "Automobiles",
    "Consumer Finance",
    "FMCG",
    "IT Services",
    "Life Insurance",
    "Oil & Gas",
    "Pharmaceuticals",
    "Power & Utilities",
    "Private Banks",
    "Public Sector Banks",
    "Steel",
]


# ---------------------------------------------------------
# Peer Group Selection
# ---------------------------------------------------------

selected_group = st.selectbox(
    "Select Peer Group",
    PEER_GROUPS,
)


# ---------------------------------------------------------
# Load Peer Data
# ---------------------------------------------------------

df = get_peer_metrics(selected_group)

if df.empty:
    st.warning("No peer data is available for this group.")
    st.stop()


# ---------------------------------------------------------
# Numeric Conversion
# ---------------------------------------------------------

metric_columns = [
    "roe",
    "opm",
    "debt_to_equity",
    "revenue_cagr",
    "pat_cagr",
    "icr",
    "pe",
    "dividend_yield",
]

for column in metric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )


# ---------------------------------------------------------
# Benchmark Company
# ---------------------------------------------------------

benchmark_rows = df[
    pd.to_numeric(
        df["is_benchmark"],
        errors="coerce",
    ).fillna(0) == 1
]

if not benchmark_rows.empty:
    default_company = benchmark_rows.iloc[0]["company_name"]
else:
    default_company = df.iloc[0]["company_name"]


company_names = df["company_name"].tolist()

default_index = (
    company_names.index(default_company)
    if default_company in company_names
    else 0
)


# ---------------------------------------------------------
# Company Selection
# ---------------------------------------------------------

selected_company = st.selectbox(
    "Benchmark Company",
    company_names,
    index=default_index,
)

selected_row = df[
    df["company_name"] == selected_company
].iloc[0]


# ---------------------------------------------------------
# Basic Information
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Selected Company",
        selected_row["company_id"],
    )

with col2:
    st.metric(
        "Peer Group",
        selected_group,
    )

with col3:
    st.metric(
        "Companies in Group",
        len(df),
    )


st.divider()


# ---------------------------------------------------------
# Radar Chart Metrics
# ---------------------------------------------------------

radar_metrics = {
    "ROE": "roe",
    "OPM": "opm",
    "Revenue CAGR": "revenue_cagr",
    "PAT CAGR": "pat_cagr",
    "Interest Coverage": "icr",
    "Dividend Yield": "dividend_yield",
    "P/E": "pe",
    "Debt/Equity": "debt_to_equity",
}


# ---------------------------------------------------------
# Normalisation
# ---------------------------------------------------------
#
# Radar charts need comparable scales because, for example,
# ICR may be 80 while D/E may only be 0.1.
#
# Higher = better for most metrics.
# Lower = better for P/E and Debt/Equity.
# ---------------------------------------------------------

normalized = pd.DataFrame(index=df.index)

lower_is_better = [
    "pe",
    "debt_to_equity",
]

for column in radar_metrics.values():

    series = df[column].copy()

    min_value = series.min(skipna=True)
    max_value = series.max(skipna=True)

    if pd.isna(min_value) or pd.isna(max_value):
        normalized[column] = 0

    elif max_value == min_value:
        normalized[column] = 50

    else:
        normalized[column] = (
            (series - min_value)
            / (max_value - min_value)
            * 100
        )

        if column in lower_is_better:
            normalized[column] = (
                100 - normalized[column]
            )


normalized = normalized.fillna(0)


# ---------------------------------------------------------
# Selected Company Scores
# ---------------------------------------------------------

selected_index = selected_row.name

company_scores = [
    normalized.loc[selected_index, column]
    for column in radar_metrics.values()
]


# ---------------------------------------------------------
# Peer Average Scores
# ---------------------------------------------------------

peer_average_scores = [
    normalized[column].mean()
    for column in radar_metrics.values()
]


categories = list(radar_metrics.keys())


# Close radar polygon
radar_categories = categories + [categories[0]]

company_scores_closed = (
    company_scores + [company_scores[0]]
)

peer_scores_closed = (
    peer_average_scores
    + [peer_average_scores[0]]
)


# ---------------------------------------------------------
# Radar Chart
# ---------------------------------------------------------

st.subheader(
    f"{selected_company} vs {selected_group} Average"
)

fig = go.Figure()


fig.add_trace(
    go.Scatterpolar(
        r=company_scores_closed,
        theta=radar_categories,
        fill="toself",
        name=selected_company,
    )
)


fig.add_trace(
    go.Scatterpolar(
        r=peer_scores_closed,
        theta=radar_categories,
        fill="toself",
        name="Peer Group Average",
    )
)


fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100],
        )
    ),
    showlegend=True,
    height=600,
    margin=dict(
        l=60,
        r=60,
        t=60,
        b=60,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


st.caption(
    "Radar scores are normalised from 0–100 within the selected "
    "peer group. Higher scores indicate relatively stronger values. "
    "P/E and Debt/Equity are inverted because lower values are preferred."
)


# ---------------------------------------------------------
# Peer KPI Comparison Table
# ---------------------------------------------------------

st.divider()

st.subheader("Peer KPI Comparison")


comparison_df = df[
    [
        "company_id",
        "company_name",
        "is_benchmark",
        "roe",
        "opm",
        "revenue_cagr",
        "pat_cagr",
        "debt_to_equity",
        "icr",
        "pe",
        "dividend_yield",
    ]
].copy()


comparison_df["Company"] = comparison_df.apply(
    lambda row: (
        f"⭐ {row['company_name']}"
        if row["company_name"] == selected_company
        else row["company_name"]
    ),
    axis=1,
)


comparison_df = comparison_df[
    [
        "company_id",
        "Company",
        "roe",
        "opm",
        "revenue_cagr",
        "pat_cagr",
        "debt_to_equity",
        "icr",
        "pe",
        "dividend_yield",
    ]
]


comparison_df = comparison_df.rename(
    columns={
        "company_id": "Ticker",
        "roe": "ROE %",
        "opm": "OPM %",
        "revenue_cagr": "Revenue CAGR %",
        "pat_cagr": "PAT CAGR %",
        "debt_to_equity": "D/E",
        "icr": "ICR",
        "pe": "P/E",
        "dividend_yield": "Dividend Yield %",
    }
)


# ---------------------------------------------------------
# Highlight Selected Company
# ---------------------------------------------------------

def highlight_selected(row):
    if row["Company"].startswith("⭐"):
        return [
            "font-weight: bold; background-color: rgba(255, 215, 0, 0.18)"
        ] * len(row)

    return [""] * len(row)


styled_df = comparison_df.style.apply(
    highlight_selected,
    axis=1,
)


st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# Peer Average Table
# ---------------------------------------------------------

st.subheader("Peer Group Average")

average_data = {
    "ROE %": df["roe"].mean(),
    "OPM %": df["opm"].mean(),
    "Revenue CAGR %": df["revenue_cagr"].mean(),
    "PAT CAGR %": df["pat_cagr"].mean(),
    "D/E": df["debt_to_equity"].mean(),
    "ICR": df["icr"].mean(),
    "P/E": df["pe"].mean(),
    "Dividend Yield %": df["dividend_yield"].mean(),
}

average_df = pd.DataFrame(
    [average_data]
).round(2)

st.dataframe(
    average_df,
    use_container_width=True,
    hide_index=True,
)