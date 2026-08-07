import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import get_companies, get_trend_data


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("📈 Trend Analysis")

st.caption(
    "Analyse up to three financial metrics over the latest "
    "10 available annual periods."
)


# ---------------------------------------------------------
# Load Companies
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.warning("No company data is available.")
    st.stop()


# ---------------------------------------------------------
# Company Search
# ---------------------------------------------------------

companies["search_label"] = (
    companies["company_name"].astype(str)
    + " ("
    + companies["company_id"].astype(str)
    + ")"
)

company_options = companies["search_label"].tolist()


selected_label = st.selectbox(
    "Search Company / Ticker",
    company_options,
    index=0,
)


selected_company = companies[
    companies["search_label"] == selected_label
].iloc[0]


ticker = selected_company["company_id"]
company_name = selected_company["company_name"]


# ---------------------------------------------------------
# Load Trend Data
# ---------------------------------------------------------

df = get_trend_data(ticker)

if df.empty:
    st.warning(
        f"No historical trend data is available for {company_name}."
    )
    st.stop()


# ---------------------------------------------------------
# Remove TTM / Non-Annual Rows
# ---------------------------------------------------------

df["year_number"] = pd.to_numeric(
    df["year"].astype(str).str.extract(r"(\d{4})$")[0],
    errors="coerce",
)

df = df.dropna(subset=["year_number"]).copy()

df["year_number"] = df["year_number"].astype(int)

df = df.sort_values("year_number")


# ---------------------------------------------------------
# Keep Latest 10 Years
# ---------------------------------------------------------

if len(df) > 10:
    df = df.tail(10).copy()


if len(df) < 10:
    st.info(
        f"Data available for {len(df)} annual periods. "
        "The chart uses all available historical data."
    )


# ---------------------------------------------------------
# Metric Definitions
# ---------------------------------------------------------

METRICS = {
    "Revenue (₹ Cr)": "sales",
    "Operating Profit (₹ Cr)": "operating_profit",
    "Net Profit (₹ Cr)": "net_profit",
    "EPS": "eps",
    "ROE (%)": "return_on_equity_pct",
    "OPM (%)": "operating_profit_margin_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "Debt / Equity": "debt_to_equity",
    "Free Cash Flow (₹ Cr)": "free_cash_flow_cr",
    "Interest Coverage": "interest_coverage",
}


# ---------------------------------------------------------
# Metric Selection
# ---------------------------------------------------------

selected_metrics = st.multiselect(
    "Select Metrics — Maximum 3",
    options=list(METRICS.keys()),
    default=[
        "Revenue (₹ Cr)",
        "Net Profit (₹ Cr)",
    ],
    max_selections=3,
)


if not selected_metrics:
    st.info("Select at least one metric to display the trend chart.")
    st.stop()


# ---------------------------------------------------------
# Company Information
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Ticker",
        ticker,
    )

with col2:
    st.metric(
        "Company",
        company_name,
    )

with col3:
    st.metric(
        "Periods Available",
        len(df),
    )


st.divider()


# ---------------------------------------------------------
# Trend Chart
# ---------------------------------------------------------

st.subheader(
    f"{company_name} — Financial Trends"
)

fig = go.Figure()


for metric_name in selected_metrics:

    column = METRICS[metric_name]

    metric_df = df[
        ["year", "year_number", column]
    ].copy()

    metric_df[column] = pd.to_numeric(
        metric_df[column],
        errors="coerce",
    )

    metric_df = metric_df.dropna(
        subset=[column]
    )

    if metric_df.empty:
        continue


    # -----------------------------------------------------
    # YoY Percentage Change
    # -----------------------------------------------------

    metric_df["yoy_change"] = (
        metric_df[column].pct_change() * 100
    )


    # Annotation text
    annotation_text = []

    for value in metric_df["yoy_change"]:

        if pd.isna(value):
            annotation_text.append("")

        else:
            annotation_text.append(
                f"{value:+.1f}%"
            )


    # -----------------------------------------------------
    # Add Metric Trace
    # -----------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=metric_df["year"],
            y=metric_df[column],
            mode="lines+markers+text",
            name=metric_name,
            text=annotation_text,
            textposition="top center",
            hovertemplate=(
                "<b>%{x}</b><br>"
                + metric_name
                + ": %{y:,.2f}<br>"
                + "YoY: %{text}"
                + "<extra></extra>"
            ),
        )
    )


# ---------------------------------------------------------
# Chart Layout
# ---------------------------------------------------------

fig.update_layout(
    height=600,
    xaxis_title="Financial Year",
    yaxis_title="Metric Value",
    hovermode="x unified",
    legend_title="Metrics",
    margin=dict(
        l=40,
        r=40,
        t=50,
        b=40,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


st.caption(
    "Percentage labels show year-over-year change from the "
    "previous available annual period."
)


# ---------------------------------------------------------
# Historical Data Table
# ---------------------------------------------------------

st.divider()

st.subheader("Historical Data")


table_columns = [
    "year",
]

rename_columns = {
    "year": "Year",
}


for metric_name in selected_metrics:

    column = METRICS[metric_name]

    if column in df.columns:
        table_columns.append(column)
        rename_columns[column] = metric_name


table_df = df[
    table_columns
].copy()


table_df = table_df.rename(
    columns=rename_columns
)


st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
)